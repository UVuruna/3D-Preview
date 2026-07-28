"""Regression: the demo window must fit in half a screen.

Pins the fix for the oversized minimum reported 2026-07-28, when the window
could not be made narrower than 1649 x 767 — wider than half of a 3072 px
display.

Root causes, both structural:
  * the keyboard legend was a QHBoxLayout, whose minimum is the SUM of its
    items, so eight chips on one unwrappable row dictated ~1250 px on their own;
  * the control panel's sections were stacked unscrolled, setting a ~770 px
    floor on the height.

Fixes: a wrapping FlowLayout for the legend (moved into the panel so it never
competes with the 3D view for height), and one scroll area for the whole panel.

What each test actually pins, verified against the pre-fix code:
  * `test_layout_minimum_fits_half_a_screen` — the reported bug; fails there
    with "layout demands 1340 px of width";
  * `test_declared_minimum_is_enforceable` — guards the declared floor against
    drifting above what the layout can reach;
  * `test_stage_keeps_its_height_when_the_window_is_small` — guards a second
    failure found while fixing the first: with the legend wrapped under the
    stage, eight rows of chips squeezed the 3D view to a thumbnail. It passes
    against the ORIGINAL code, which simply refused to get small at all.

Run: python -m pytest tests/
"""

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from demoapp.window import WINDOW, DemoWindow  # noqa: E402  (needs the path above)

# A window nobody can fit beside another window is a broken window. These are
# the ceilings the layout must stay under, not the sizes it should open at.
MAX_MINIMUM_WIDTH = 700
MAX_MINIMUM_HEIGHT = 620
# A small window to prove the layout behaves there; kept independent of the
# WINDOW config so this stays a real assertion rather than a missing-key error.
SMALL = (560, 420)
SETTLE_MS = 300


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication(sys.argv)


@pytest.fixture
def window(app):
    win = DemoWindow()
    win.show()
    _settle(app)
    yield win
    win.close()
    win.deleteLater()


def _settle(app, ms: int = SETTLE_MS) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    app.processEvents()


def test_layout_minimum_fits_half_a_screen(window):
    hint = window.minimumSizeHint()
    assert hint.width() <= MAX_MINIMUM_WIDTH, (
        f"layout demands {hint.width()} px of width; something inside cannot wrap or scroll"
    )
    assert hint.height() <= MAX_MINIMUM_HEIGHT, (
        f"layout demands {hint.height()} px of height; the panel is not scrolling"
    )


def test_declared_minimum_is_enforceable(window):
    """The declared floor must be one the layout can actually reach."""
    assert window.minimumWidth() == WINDOW["min_width"]
    assert window.minimumHeight() == WINDOW["min_height"]
    assert window.minimumSizeHint().width() <= WINDOW["min_width"] + 40


def test_stage_keeps_its_height_when_the_window_is_small(app, window):
    """The 3D view is the point of the window; chrome must not crowd it out."""
    window.resize(*SMALL)
    _settle(app)
    stage = window.viewer.parentWidget()
    assert stage.height() >= window.height() * 0.5, (
        f"stage is {stage.height()} px in a {window.height()} px window — "
        "something below or above it is taking the room"
    )
