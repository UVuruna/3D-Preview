"""Preview3DLightWidget — the QPainter-drawn viewer.

Same scene specs, same part paths, same method names as the web-backed
`Preview3DWidget`, so a host can swap one for the other. What it does NOT do is
load glTF/GLB files, shade with real materials, or run in a browser — see
RENDERERS.md for the full comparison and how to choose.
"""

import logging

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from ..resources import load_shared_spec
from . import scene as scene_ops
from .camera import (
    CAMERA_DEFAULTS,
    FREE_VIEW,
    ORTHOGRAPHIC,
    PERSPECTIVE,
    VIEW_ORDER,
    Camera,
    step_view,
    view_direction,
)
from .primitives import build_primitive
from .renderer import build_grid, content_points, paint_scene
from .scene import Node

logger = logging.getLogger(__name__)

_SPEC = load_shared_spec()
DEFAULT_BACKGROUND = "#16161F"
VIEWS = tuple(VIEW_ORDER)
PROJECTIONS = (PERSPECTIVE, ORTHOGRAPHIC)


class Preview3DLightWidget(QWidget):
    """Dependency-light 3D preview: no browser engine, no GPU, no model files.

    Signals:
        camera_changed(dict): {azimuth, elevation, distance, view, projection,
            grid, gridStep, background, contentVersion} — the same payload the
            web-backed widget emits, so a host's readout code works with either.
    """

    camera_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAutoFillBackground(True)

        self._root = Node(name="content")
        self._camera = Camera()
        self._view_name = str(CAMERA_DEFAULTS["defaultView"])
        self._background = DEFAULT_BACKGROUND
        self._grid_enabled = False
        self._grid_segments = None
        self._grid_step = 0.0
        self._content_version = 0
        self._user_framed = False
        self._drag_origin: QPoint | None = None
        self._drag_button = Qt.MouseButton.NoButton

        self._apply_background()

    # ---- Content -----------------------------------------------------------

    def show_scene(self, spec: dict) -> None:
        """Show a parametric primitive — the same spec the web renderer takes."""
        self._root = Node(name="content")
        self._root.add(build_primitive(spec))
        self._content_version += 1
        self._rebuild_grid()
        self.reset_view()

    def show_axes(self, arms: list[dict] | None = None, arm_length: float = 1.0) -> None:
        spec: dict = {"type": "axes", "armLength": arm_length}
        if arms is not None:
            spec["arms"] = arms
        self.show_scene(spec)

    def load_model(self, path) -> None:
        """Not available in the LIGHT renderer — use the web-backed widget.

        Refusing loudly beats a blank view: a host that needs file loading has
        chosen the wrong renderer, and should learn that at the call (Rule #1).
        """
        raise NotImplementedError(
            "The LIGHT renderer draws parametric scenes only; glTF/GLB loading "
            "needs Preview3DWidget (the web-backed one). See RENDERERS.md."
        )

    # ---- Parts -------------------------------------------------------------

    def list_parts(self, callback=None):
        """Return the part list — and also pass it to `callback` if given.

        The web-backed widget can only answer asynchronously, so host code
        written against it uses a callback; here the answer is immediate.
        Supporting both shapes is what makes the two widgets interchangeable.
        """
        parts = scene_ops.collect_parts(self._root)
        if callback is not None:
            callback(parts)
        return parts

    def set_part_visible(self, path: str, visible: bool) -> None:
        scene_ops.set_part_visible(self._root, path, visible)
        self.update()

    def set_part_opacity(self, path: str, alpha: float) -> None:
        scene_ops.set_part_opacity(self._root, path, alpha)
        self.update()

    def show_only(self, group_path: str, child_name: str) -> None:
        scene_ops.show_only(self._root, group_path, child_name)
        self.update()

    def remove_part(self, path: str) -> None:
        scene_ops.remove_part(self._root, path)
        self._rebuild_grid()
        self.update()

    # ---- Camera ------------------------------------------------------------

    def set_view(self, name: str) -> None:
        self._view_name = name
        self._fit(view_direction(name))

    def step_view(self, step: int) -> None:
        self.set_view(step_view(self._view_name, step))

    def set_projection(self, kind: str) -> None:
        self._camera.set_projection(kind)
        self._changed()

    def orbit_by(self, azimuth: float, elevation: float) -> None:
        self._camera.orbit_by(azimuth, elevation)
        self._mark_user_framed()
        self._changed()

    def pan_by(self, dx: float, dy: float) -> None:
        self._camera.pan_by(dx, dy)
        self._mark_user_framed()
        self._changed()

    def zoom_by(self, factor: float) -> None:
        self._camera.zoom_by(factor)
        self._user_framed = True     # a zoom keeps the direction, so not FREE
        self._changed()

    def reset_view(self) -> None:
        name = self._view_name if self._view_name in VIEWS else str(CAMERA_DEFAULTS["defaultView"])
        self._view_name = name
        self._fit(view_direction(name))

    def camera_state(self) -> dict:
        state = self._camera.state()
        state.update({
            "view": self._view_name,
            "grid": self._grid_enabled,
            "gridStep": self._grid_step,
            "background": self._background,
            "contentVersion": self._content_version,
        })
        return state

    # ---- Appearance --------------------------------------------------------

    def set_background(self, color: str) -> None:
        self._background = color
        self._apply_background()
        self._changed()

    def set_grid(self, enabled: bool) -> None:
        self._grid_enabled = enabled
        self._rebuild_grid()
        self._changed()

    # ---- Qt events ---------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._background != "transparent":
            painter.fillRect(self.rect(), QColor(self._background))
        paint_scene(painter, self._root, self._camera, self.width(), self.height(),
                    self._grid_segments)
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._camera.aspect = self.width() / max(1, self.height())
        # Framing is aspect-dependent, so a narrower widget clips content that
        # used to fit — but once the view is the user's, a resize leaves it be.
        if self._user_framed:
            self.update()
        else:
            self._fit(None)

    def mousePressEvent(self, event):
        self._drag_origin = event.position().toPoint()
        self._drag_button = event.button()
        self.setFocus()

    def mouseMoveEvent(self, event):
        if self._drag_origin is None:
            return
        current = event.position().toPoint()
        dx = current.x() - self._drag_origin.x()
        dy = current.y() - self._drag_origin.y()
        self._drag_origin = current
        if self._drag_button == Qt.MouseButton.RightButton:
            self.pan_by(-dx / max(1, self.width()), dy / max(1, self.height()))
        else:
            self.orbit_by(-dx * 0.4, dy * 0.4)

    def mouseReleaseEvent(self, event):
        self._drag_origin = None
        self._drag_button = Qt.MouseButton.NoButton

    def wheelEvent(self, event):
        steps = event.angleDelta().y() / 120.0
        if steps:
            self.zoom_by(float(CAMERA_DEFAULTS["zoomStep"]) ** steps)

    def keyPressEvent(self, event):
        orbit = float(CAMERA_DEFAULTS["orbitStep"])
        pan = float(CAMERA_DEFAULTS["panStep"])
        shift = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
        key = event.key()

        if key == Qt.Key.Key_Left:
            self.step_view(-1) if shift else (self.pan_by(pan, 0) if ctrl else self.orbit_by(-orbit, 0))
        elif key == Qt.Key.Key_Right:
            self.step_view(1) if shift else (self.pan_by(-pan, 0) if ctrl else self.orbit_by(orbit, 0))
        elif key == Qt.Key.Key_Up:
            self.set_view("top") if shift else (self.pan_by(0, pan) if ctrl else self.orbit_by(0, orbit))
        elif key == Qt.Key.Key_Down:
            self.set_view("bottom") if shift else (self.pan_by(0, -pan) if ctrl else self.orbit_by(0, -orbit))
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_by(float(CAMERA_DEFAULTS["zoomStep"]))
        elif key == Qt.Key.Key_Minus:
            self.zoom_by(1 / float(CAMERA_DEFAULTS["zoomStep"]))
        elif key == Qt.Key.Key_P:
            self.set_projection(ORTHOGRAPHIC if self._camera.projection == PERSPECTIVE else PERSPECTIVE)
        elif key == Qt.Key.Key_G:
            self.set_grid(not self._grid_enabled)
        elif key == Qt.Key.Key_R:
            self.reset_view()
        else:
            super().keyPressEvent(event)

    # ---- Internals ---------------------------------------------------------

    def _fit(self, direction) -> None:
        self._camera.aspect = self.width() / max(1, self.height())
        self._camera.fit(content_points(self._root), direction)
        self._user_framed = False
        self._changed()

    def _mark_user_framed(self) -> None:
        self._user_framed = True
        self._view_name = FREE_VIEW

    def _rebuild_grid(self) -> None:
        if not self._grid_enabled:
            self._grid_segments, self._grid_step = None, 0.0
            return
        self._grid_segments, self._grid_step = build_grid(content_points(self._root))

    def _apply_background(self) -> None:
        transparent = self._background == "transparent"
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, transparent)
        self.setAutoFillBackground(not transparent)
        palette = self.palette()
        palette.setColor(self.backgroundRole(),
                         QColor(0, 0, 0, 0) if transparent else QColor(self._background))
        self.setPalette(palette)

    def _changed(self) -> None:
        self.update()
        self.camera_changed.emit(self.camera_state())
