"""Preview3DWidget — PySide6 wrapper around the 3D Preview web core.

Loads the bundled host page (web/index.html + preview3d.min.js) into a
QWebEngineView and mirrors the JS Viewer API as Python methods. Calls made
before the page finishes loading are queued and flushed on load.
"""

import base64
import json
import logging
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

logger = logging.getLogger(__name__)

# The web bundle lives in exactly one of two places:
# installed wheel → preview3d/web/ (force-included by pyproject.toml);
# repo checkout   → ../web/ next to this package.
_WEB_LOCATIONS = (
    Path(__file__).parent / "web",
    Path(__file__).parent.parent / "web",
)


def _host_page() -> Path:
    for root in _WEB_LOCATIONS:
        page = root / "index.html"
        if page.exists():
            return page
    raise FileNotFoundError(
        f"3D Preview web bundle not found in {[str(p) for p in _WEB_LOCATIONS]} — "
        "run `npm run build` in the project root first."
    )


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
    """Embeddable 3D preview: parametric primitives, GLB models, orbit controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPage(_ConsolePage(self))
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        self._ready = False
        self._pending: list[str] = []
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl.fromLocalFile(str(_host_page())))

    # ---- Public API — mirrors the JS Viewer --------------------------------

    def show_scene(self, spec: dict) -> None:
        """Show a parametric primitive, e.g. {"type": "axes", ...} — see primitives.md."""
        self._run(f"viewer.show({json.dumps(spec)})")

    def show_axes(self, arms: list[dict] | None = None, arm_length: float = 1.0) -> None:
        """Axes gizmo: up to 6 arms, each {"axis": "+x".."-z", "color": hex, "label": str}."""
        spec: dict = {"type": "axes", "armLength": arm_length}
        if arms is not None:
            spec["arms"] = arms
        self.show_scene(spec)

    def load_model(self, path: str | Path) -> None:
        """Load a local glTF/GLB file (bytes are handed to JS — file:// fetch is blocked)."""
        data = base64.b64encode(Path(path).read_bytes()).decode("ascii")
        self._run(f"viewer.loadModelData('{data}')")

    def set_background(self, color: str) -> None:
        """CSS hex color, or 'transparent' for a see-through widget."""
        if color == "transparent":
            self.page().setBackgroundColor(QColor(0, 0, 0, 0))
        self._run(f"viewer.setBackground({json.dumps(color)})")

    def reset_view(self) -> None:
        self._run("viewer.resetView()")

    # ---- Internals ---------------------------------------------------------

    def _run(self, code: str) -> None:
        if self._ready:
            self.page().runJavaScript(code)
        else:
            self._pending.append(code)

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            logger.error("3D Preview host page failed to load: %s", self.url().toString())
            return
        self._ready = True
        for code in self._pending:
            self.page().runJavaScript(code)
        self._pending.clear()
