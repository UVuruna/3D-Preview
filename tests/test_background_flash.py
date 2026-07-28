"""Regression: the widget must never leave a white sheet behind the canvas.

Pins the fix for the resize white-flash (2026-07-28). Root cause: QWebEnginePage
defaults to OPAQUE WHITE, while the host page's html, body and container are all
transparent — so that white sheet showed through in any frame where the WebGL
canvas was not painted, and a resize clears the canvas backing store for at
least one frame.

Deterministic on purpose: it asserts the COLOUR behind the canvas rather than
trying to catch a flash on camera, because the flash is a consequence of the
colour and a screen-grab race would be a flaky test.

Run: python -m pytest tests/
"""

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preview3d import Preview3DWidget  # noqa: E402  (needs the path above)

LOAD_TIMEOUT_MS = 20_000
SETTLE_MS = 400
DARK = "#16161f"      # the viewer's default background
CUSTOM = "#2a1b3d"


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication(sys.argv)


@pytest.fixture
def widget(app):
    view = Preview3DWidget()
    view.resize(400, 300)
    view.show()

    loop = QEventLoop()
    view.loadFinished.connect(lambda ok: loop.quit())
    QTimer.singleShot(LOAD_TIMEOUT_MS, loop.quit)
    loop.exec()
    _settle(app)

    yield view
    view.deleteLater()


def _settle(app, ms: int = SETTLE_MS) -> None:
    """Let the page's reports reach Python."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    app.processEvents()


def test_page_surface_is_not_white_by_default(widget):
    """The bug itself: an untouched widget used to sit on opaque white."""
    surface = widget.page().backgroundColor()
    assert surface.name() != "#ffffff", (
        "page background is opaque white — a resize will flash white behind the canvas"
    )
    assert surface.name() == DARK


def test_page_surface_follows_the_requested_background(app, widget):
    widget.set_background(CUSTOM)
    _settle(app)
    assert widget.page().backgroundColor().name() == CUSTOM


def test_transparent_background_stays_transparent(app, widget):
    """The see-through mode must not be 'fixed' into an opaque surface."""
    widget.set_background("transparent")
    _settle(app)
    assert widget.page().backgroundColor().alpha() == 0


def test_container_is_painted_behind_the_canvas(app, widget):
    """The in-page half of the fix: no transparent gap around the canvas."""
    widget.set_background(CUSTOM)
    _settle(app)

    seen = {}
    loop = QEventLoop()

    def done(value):
        seen["background"] = value
        loop.quit()

    widget.page().runJavaScript(
        "getComputedStyle(document.getElementById('app')).backgroundColor", 0, done
    )
    QTimer.singleShot(5_000, loop.quit)
    loop.exec()

    assert seen.get("background") == "rgb(42, 27, 61)", (
        f"container is {seen.get('background')!r}; a transparent container lets "
        "whatever is behind the page show through while the canvas is cleared"
    )
