"""Preview3DWidget — PySide6 wrapper around the 3D Preview web core.

Loads the bundled host page (web/index.html + preview3d.min.js) into a
QWebEngineView and mirrors the JS Viewer API as Python methods. Calls made
before the page finishes loading are queued and flushed on load; camera
movement travels the other way over a Qt web channel.
"""

import base64
import json
import logging
from pathlib import Path

from PySide6.QtCore import QFile, QIODevice, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

logger = logging.getLogger(__name__)

# The web bundle lives in exactly one of two places:
# installed wheel → preview3d/web/ (force-included by pyproject.toml);
# repo checkout   → ../web/ next to this package.
_WEB_LOCATIONS = (
    Path(__file__).parent / "web",
    Path(__file__).parent.parent / "web",
)

# Ships with QtWebChannel; importing the module registers the resource.
_WEB_CHANNEL_SCRIPT = ":/qtwebchannel/qwebchannel.js"

VIEWS = ("iso", "front", "right", "back", "left", "top", "bottom")
PROJECTIONS = ("perspective", "orthographic")


def _host_page() -> Path:
    for root in _WEB_LOCATIONS:
        page = root / "index.html"
        if page.exists():
            return page
    raise FileNotFoundError(
        f"3D Preview web bundle not found in {[str(p) for p in _WEB_LOCATIONS]} — "
        "run `npm run build` in the project root first."
    )


def _web_channel_source() -> str:
    """Read qwebchannel.js out of the Qt resource system.

    Injecting the source is deliberate: a local file:// page cannot reliably
    fetch a qrc:// script, and the bundled host page must work identically
    from disk and from a wheel.
    """
    file = QFile(_WEB_CHANNEL_SCRIPT)
    if not file.open(QIODevice.OpenModeFlag.ReadOnly):
        raise RuntimeError(f"Cannot read {_WEB_CHANNEL_SCRIPT} — is PySide6-QtWebChannel installed?")
    try:
        return file.readAll().data().decode("utf-8")
    finally:
        file.close()


class _Bridge(QObject):
    """The object JS calls into. One slot per message the page can send."""

    cameraReported = Signal(dict)

    @Slot("QVariantMap")
    def reportCamera(self, state: dict) -> None:  # noqa: N802 — JS-facing name
        self.cameraReported.emit(state)


class _ConsolePage(QWebEnginePage):
    """Forwards the JS console into Python logging — JS errors stay visible (Rule #1)."""

    _LEVELS = {
        QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: logging.INFO,
        QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: logging.WARNING,
        QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: logging.ERROR,
    }

    def javaScriptConsoleMessage(self, level, message, line, source):
        logger.log(self._LEVELS[level], "JS console: %s (%s:%d)", message, source, line)


class Preview3DWidget(QWebEngineView):
    """Embeddable 3D preview: parametric primitives, GLB models, orbit controls.

    Signals:
        camera_changed(dict): {azimuth, elevation, distance, view, projection,
            grid, gridStep} — azimuth/elevation in degrees. Emitted while the
            camera moves, rate-limited by the viewer.
    """

    camera_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        page = _ConsolePage(self)
        self.setPage(page)

        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        script = QWebEngineScript()
        script.setName("qwebchannel")
        script.setSourceCode(_web_channel_source())
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        page.scripts().insert(script)

        self._bridge = _Bridge(self)
        self._bridge.cameraReported.connect(self.camera_changed)
        self._channel = QWebChannel(self)
        self._channel.registerObject("bridge", self._bridge)
        page.setWebChannel(self._channel)

        self._ready = False
        self._pending: list[tuple[str, object]] = []
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl.fromLocalFile(str(_host_page())))

    # ---- Content -----------------------------------------------------------

    def show_scene(self, spec: dict) -> None:
        """Show a parametric primitive, e.g. {"type": "axes", ...} — see primitives.md."""
        self._run(f"viewer.show({json.dumps(spec)})")

    def show_axes(self, arms: list[dict] | None = None, arm_length: float = 1.0) -> None:
        """Axes gizmo: up to 6 arms, each {"axis": "+x".."-z", "color": hex, "label": str | list}."""
        spec: dict = {"type": "axes", "armLength": arm_length}
        if arms is not None:
            spec["arms"] = arms
        self.show_scene(spec)

    def load_model(self, path: str | Path) -> None:
        """Load a local glTF/GLB file (bytes are handed to JS — file:// fetch is blocked)."""
        data = base64.b64encode(Path(path).read_bytes()).decode("ascii")
        self._run(f"viewer.loadModelData('{data}')")

    # ---- Parts -------------------------------------------------------------

    def list_parts(self, callback) -> None:
        """Asynchronously deliver the part list to `callback` — see MODELS.md.

        Each entry: {path, name, type, depth, drawable, visible, opacity}.
        """
        self._run_json("viewer.listParts()", callback)

    def set_part_visible(self, path: str, visible: bool) -> None:
        self._run(f"viewer.setPartVisible({json.dumps(path)}, {json.dumps(visible)})")

    def set_part_opacity(self, path: str, alpha: float) -> None:
        self._run(f"viewer.setPartOpacity({json.dumps(path)}, {alpha})")

    def show_only(self, group_path: str, child_name: str) -> None:
        """Show one child of a switch group and hide its siblings."""
        self._run(f"viewer.showOnly({json.dumps(group_path)}, {json.dumps(child_name)})")

    def remove_part(self, path: str) -> None:
        """Detach and free a part for good — use set_part_visible() for toggling."""
        self._run(f"viewer.removePart({json.dumps(path)})")

    # ---- Camera ------------------------------------------------------------

    def set_view(self, name: str) -> None:
        """One of VIEWS."""
        self._run(f"viewer.setView({json.dumps(name)})")

    def step_view(self, step: int) -> None:
        """Cycle the view presets; +1 forward, -1 back."""
        self._run(f"viewer.stepView({int(step)})")

    def set_projection(self, kind: str) -> None:
        """'perspective' or 'orthographic' — the latter is what makes a cube seen
        down its body diagonal a geometrically exact hexagon."""
        self._run(f"viewer.setProjection({json.dumps(kind)})")

    def orbit_by(self, azimuth: float, elevation: float) -> None:
        """Move around the content by degrees; the point looked at stays put."""
        self._run(f"viewer.orbitBy({azimuth}, {elevation})")

    def pan_by(self, dx: float, dy: float) -> None:
        """Slide the view; steps are fractions of the visible height."""
        self._run(f"viewer.panBy({dx}, {dy})")

    def zoom_by(self, factor: float) -> None:
        """factor > 1 zooms in."""
        self._run(f"viewer.zoomBy({factor})")

    def reset_view(self) -> None:
        self._run("viewer.resetView()")

    # ---- Appearance --------------------------------------------------------

    def set_background(self, color: str) -> None:
        """CSS hex color, or 'transparent' for a see-through widget."""
        if color == "transparent":
            self.page().setBackgroundColor(QColor(0, 0, 0, 0))
        self._run(f"viewer.setBackground({json.dumps(color)})")

    def set_grid(self, enabled: bool) -> None:
        """Toggle the reference grid; its cell size is reported by camera_changed."""
        self._run(f"viewer.setGrid({json.dumps(enabled)})")

    # ---- Internals ---------------------------------------------------------

    def _run(self, code: str) -> None:
        self._dispatch(code, None)

    def _run_json(self, expression: str, callback) -> None:
        """Evaluate `expression` and hand the decoded result to `callback`.

        The result crosses as a JSON STRING on purpose: QtWebEngine's direct
        value conversion does not survive JS arrays — an array of three strings
        arrives in Python as an empty string, silently. Numbers and strings
        convert fine, so stringify/loads is the reliable path for any
        structured result.
        """

        def decode(raw):
            callback(json.loads(raw))

        self._dispatch(f"JSON.stringify({expression})", decode)

    def _dispatch(self, code: str, callback) -> None:
        # The page starts reporting camera state as soon as its web channel is
        # up, which is BEFORE loadFinished reaches Python — so a host reacting
        # to that first signal would otherwise be calling into a widget that
        # says it is not ready. Queued calls keep their callback, so an early
        # request is answered late rather than refused or silently dropped.
        if not self._ready:
            self._pending.append((code, callback))
        elif callback is None:
            self.page().runJavaScript(code)
        else:
            self.page().runJavaScript(code, 0, callback)

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            logger.error("3D Preview host page failed to load: %s", self.url().toString())
            return
        self._ready = True
        pending, self._pending = self._pending, []
        for code, callback in pending:
            self._dispatch(code, callback)
