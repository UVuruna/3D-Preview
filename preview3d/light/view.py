"""Preview3DLightWidget — the QPainter-drawn viewer.

Same scene specs, same part paths, same method names as the web-backed
`Preview3DWidget`, so a host can swap one for the other. What it does NOT do is
load glTF/GLB files, shade with real materials, or run in a browser — see
RENDERERS.md for the full comparison and how to choose.
"""

import logging
import math
import time

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from .. import switcher as switcher_ops
from ..directions import parse_direction
from ..resources import load_shared_spec
from . import model_view
from . import scene as scene_ops
from .animation import ANIMATION_DEFAULTS, NO_ANIMATION, Timeline
from .camera import (
    CAMERA_DEFAULTS,
    FREE_VIEW,
    MIN_DISTANCE,
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
        animation_changed(dict): {scene, label, playing, time, duration,
            progress, speed, frame, frames, loop} — likewise.
    """

    camera_changed = Signal(dict)
    animation_changed = Signal(dict)

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

        # Model state. A model is CONTENT, so showing anything else drops it —
        # the same rule a loaded scene follows, and for the same reason: a view
        # or a switcher position addresses parts of specific content.
        self._model: dict | None = None
        self._model_view: str | None = None
        self._switcher = dict(switcher_ops.DEFAULT_STATE)
        self._orientation: str | None = None

        # Animation. The timeline drives flat parameters only (see animation.py);
        # the two baselines are the framing it moves relative to, so one scene
        # descriptor plays correctly on content of any size.
        self._timeline: Timeline | None = None
        self._base_distance = 1.0
        self._base_height = 1.0
        self._last_tick = 0.0
        self._clock = QTimer(self)
        self._clock.setInterval(round(1000 / int(ANIMATION_DEFAULTS["fps"])))
        self._clock.timeout.connect(self._on_clock)

        self._apply_background()

    # ---- Content -----------------------------------------------------------

    def show_scene(self, spec: dict) -> None:
        """Show a parametric primitive — the same spec the web renderer takes."""
        root = Node(name="content")
        root.add(build_primitive(spec))
        self._mount(root)

    def _mount(self, root: Node) -> None:
        """Take a freshly built content root as the thing on screen."""
        self._root = root
        self._content_version += 1
        # New content is not the model's, and it is not turned: both are state
        # about content that no longer exists.
        self._model = None
        self._model_view = None
        self._orientation = None
        # A scene is written against the parts of specific content, so new
        # content invalidates it — keeping it would mean driving paths that need
        # not exist any more, and raising from inside show_scene() rather than
        # where the host could do anything about it. Load content first, scene
        # second (SCENES.md).
        had_scene = self._timeline is not None
        self._timeline = None
        self._sync_clock()
        self._rebuild_grid()
        self.reset_view()
        if had_scene:
            self._emit_animation()

    def show_axes(self, arms: list[dict] | None = None, arm_length: float = 1.0) -> None:
        spec: dict = {"type": "axes", "armLength": arm_length}
        if arms is not None:
            spec["arms"] = arms
        self.show_scene(spec)

    def show_model(self, model: dict, view: str | None = None) -> None:
        """Show a MODEL — axes, seats and views as data (MODELS.md).

        See model_view.py for the model half; this only mounts what it returns.
        """
        checked, root = model_view.build_model_content(model)
        self._mount(root)
        self._model = checked
        self._apply_switcher(force=True)
        self.set_model_view(view or checked["views"][0]["name"])

    def set_model_view(self, name: str) -> None:
        """One of the model's views — which families speak, and from where."""
        model_view.require_model(self._model, "set_model_view")
        opacities, camera = model_view.view_settings(self._model, name)
        for path, alpha in opacities.items():
            scene_ops.set_part_opacity(self._root, path, alpha)
        self._model_view = name
        if camera:
            self.snap_to(camera)
        else:
            self._changed()

    def model_views(self) -> list[dict]:
        """The model's views as {name, label} — what a host builds buttons from."""
        model_view.require_model(self._model, "model_views")
        return model_view.model_view_list(self._model)

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

    def set_orbit(self, azimuth: float, elevation: float) -> None:
        """Look from an absolute direction, in degrees, at the same distance."""
        self._camera.set_orbit(azimuth, elevation)
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

    def snap_to(self, direction) -> None:
        """Look down an arbitrary direction — a token or a vector — and re-frame.

        The seven presets cannot express the four body diagonals a cube is
        actually read along, which is the whole reason a model's view carries a
        camera direction instead of a preset name.
        """
        self._view_name = FREE_VIEW
        self._fit(parse_direction(direction))

    def camera_state(self) -> dict:
        state = self._camera.state()
        state.update({
            "view": self._view_name,
            "grid": self._grid_enabled,
            "gridStep": self._grid_step,
            "background": self._background,
            "contentVersion": self._content_version,
            "orientation": self._orientation,
            "modelView": self._model_view,
        })
        return state

    # ---- Orientation -------------------------------------------------------

    def set_orientation(self, identifier: str | None) -> None:
        """Snap the content to one of the cube's 24 orientations (or `None`).

        The table is computed, not stored (orientations.py). Deliberately does
        NOT re-frame: a cube keeps its silhouette as it turns, and re-fitting on
        every step would make a stepped clock jitter for no gain.
        """
        if identifier == self._orientation:
            return
        self._orientation = identifier
        self._root.basis = model_view.orientation_basis(identifier)
        self._rebuild_grid()
        self._changed()

    def step_orientation(self, step: int) -> None:
        """The next orientation in the enumeration order — the auto-advance step."""
        self.set_orientation(orientations.step_orientation(self._orientation or "", step))

    # ---- Switcher ----------------------------------------------------------

    def set_switcher(self, register: str | None = None, reading: str | None = None) -> None:
        """Which vocabulary speaks, and which readings are lit — see switcher.py."""
        state = switcher_ops.normalise(self._switcher, register, reading)
        model_view.check_register(self._model, state["register"])
        if state == self._switcher:
            return
        self._switcher = state
        self._apply_switcher(force=True)
        self._changed()

    def switcher_state(self, callback=None) -> dict:
        """The current switcher position. Same both-shapes contract as `list_parts`."""
        state = dict(self._switcher)
        if callback is not None:
            callback(state)
        return state

    def _apply_switcher(self, force: bool = False) -> None:
        for operation, path, value in switcher_ops.operations(
            scene_ops.collect_parts(self._root), self._switcher
        ):
            if operation == "visible":
                scene_ops.set_part_visible(self._root, path, value)
            else:
                scene_ops.show_only(self._root, path, value)
        if force:
            self.update()

    # ---- Appearance --------------------------------------------------------

    def set_background(self, color: str) -> None:
        self._background = color
        self._apply_background()
        self._changed()

    def set_grid(self, enabled: bool) -> None:
        self._grid_enabled = enabled
        self._rebuild_grid()
        self._changed()

    # ---- Animation ---------------------------------------------------------
    # A scene is a DESCRIPTOR — keyframes over flat parameters, see SCENES.md.
    # It is loaded paused at t = 0 with that first instant already applied, so
    # a host can show the opening pose without playing anything. With no scene
    # loaded every transport call is a documented no-op.

    def set_animation(self, descriptor: dict | None) -> None:
        self._timeline = Timeline(descriptor) if descriptor else None
        self._sync_clock()
        if self._timeline is not None:
            self._reframe_animation()
        self._emit_animation()

    def play_animation(self) -> None:
        self._with_timeline(Timeline.play)

    def pause_animation(self) -> None:
        self._with_timeline(Timeline.pause)

    def toggle_animation(self) -> None:
        self._with_timeline(Timeline.toggle)

    def stop_animation(self) -> None:
        """Back to the first frame, paused."""
        self._with_timeline(Timeline.stop)

    def seek_animation(self, progress: float) -> None:
        """progress is 0..1 — the scrub slider."""
        self._with_timeline(lambda timeline: timeline.seek(progress))

    def step_frame(self, delta: int) -> None:
        """One frame at a time; +1 forward, -1 back. Pauses playback."""
        self._with_timeline(lambda timeline: timeline.step_frame(delta))

    def set_speed(self, speed: float) -> None:
        self._with_timeline(lambda timeline: timeline.set_speed(speed))

    def jump_to_end(self) -> None:
        """INSTANT mode — the end state without the flight."""
        self._with_timeline(Timeline.jump_to_end)

    def animation_state(self, callback=None) -> dict:
        """Return the playback state — and also pass it to `callback` if given.

        Same both-shapes contract as `list_parts`: the web-backed widget can
        only answer asynchronously, so host code written against it uses a
        callback, and supporting both is what keeps the two interchangeable.
        """
        state = self._timeline.state() if self._timeline is not None else dict(NO_ANIMATION)
        if callback is not None:
            callback(state)
        return state

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
        # A loaded scene owns the camera outright, so it always re-frames.
        if self._timeline is not None:
            self._reframe_animation()
        elif self._user_framed:
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

    # ---- Animation internals -----------------------------------------------

    def _emit_animation(self) -> None:
        self.animation_changed.emit(self.animation_state())

    def _on_clock(self) -> None:
        now = time.perf_counter()
        elapsed, self._last_tick = now - self._last_tick, now
        if not self._timeline.tick(elapsed):
            return
        self._apply_timeline()
        self._changed()
        self._emit_animation()
        if not self._timeline.playing:
            self._clock.stop()      # the scene ended on its own

    # Every transport command lands the same way: change the clock, apply the
    # new instant, report it.
    def _with_timeline(self, action) -> None:
        if self._timeline is None:
            return
        action(self._timeline)
        self._sync_clock()
        self._apply_timeline()
        self._changed()
        self._emit_animation()

    def _sync_clock(self) -> None:
        """The timer runs only while a scene plays — a paused viewer is idle."""
        if self._timeline is not None and self._timeline.playing:
            if not self._clock.isActive():
                self._last_tick = time.perf_counter()
                self._clock.start()
        else:
            self._clock.stop()

    def _reframe_animation(self) -> None:
        """Frame the content as the presets would, and remember that framing.

        The timeline's `camera.dolly` is a factor OF this baseline, which is
        what lets one scene descriptor play correctly on a 1-unit cube and on a
        100-unit model alike. Both baselines come from ONE quantity on purpose:
        deriving the orthographic height from its own silhouette fit instead
        would make a scene that switches projection mid-flight jump in size.
        """
        self.reset_view()
        self._base_distance = max(self._camera.distance, MIN_DISTANCE)
        self._base_height = 2 * math.tan(math.radians(self._camera.fov / 2)) * self._base_distance
        self._apply_timeline()
        self._changed()

    def _apply_timeline(self) -> None:
        azimuth = elevation = dolly = None
        for entry in self._timeline.values():
            channel, path, value = entry["channel"], entry["path"], entry["value"]
            if channel == "camera.azimuth":
                azimuth = value
            elif channel == "camera.elevation":
                elevation = value
            elif channel == "camera.dolly":
                dolly = value
            elif channel == "camera.projection":
                self._camera.set_projection(value)
            elif channel == "part.opacity":
                scene_ops.set_part_opacity(self._root, path, value)
            elif channel == "part.visible":
                scene_ops.set_part_visible(self._root, path, value)
            elif channel == "group.show":
                scene_ops.show_only(self._root, path, value)
            elif channel == "grid":
                if value != self._grid_enabled:
                    self.set_grid(value)
            elif channel == "switcher.register":
                self.set_switcher(register=value)
            elif channel == "switcher.reading":
                self.set_switcher(reading=value)
            elif channel == "content.orientation":
                self.set_orientation(value)
            else:
                raise ValueError(f"Preview3DLightWidget cannot apply channel {channel!r}")

        # A scene with no camera tracks leaves the camera to the user.
        if azimuth is not None or elevation is not None or dolly is not None:
            self._place_camera(azimuth, elevation, dolly)
        self.update()

    def _place_camera(self, azimuth, elevation, dolly) -> None:
        camera = self._camera
        zoom = 1.0 if dolly is None else dolly
        camera.set_orbit(camera.azimuth if azimuth is None else azimuth,
                         camera.elevation if elevation is None else elevation)
        # Apparent size is distance under perspective and frustum height under
        # orthographic — the same split zoom_by() makes, so dolly means one
        # thing in both projections and in both renderers.
        camera.distance = (self._base_distance if camera.projection == ORTHOGRAPHIC
                           else self._base_distance / zoom)
        camera.ortho_height = self._base_height / zoom
        self._view_name = FREE_VIEW      # the scene is looking, not a preset
