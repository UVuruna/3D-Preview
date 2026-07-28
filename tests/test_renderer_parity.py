"""Conformance: the two renderers must agree on everything a host can observe.

Two rendering implementations of one component is a standing invitation to
drift (root Rule #5). These tests are the mitigation: the SAME scene specs go
into both, and what a host can see — part paths, visibility, opacity, framing,
camera state, the palette — has to come back the same.

They do not compare pixels. The renderers deliberately look different (the web
core shades with real materials, the LIGHT one flat-shades), and pinning that
would forbid either from ever improving.

Run: python -m pytest tests/
"""

import json
import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from preview3d import Preview3DLightWidget, Preview3DWidget  # noqa: E402

LOAD_TIMEOUT_MS = 20_000
SETTLE_MS = 400
SIZE = (600, 480)

SPECS = {
    "axes": {"type": "axes"},
    "labelled axes": {
        "type": "axes",
        "arms": [
            {"axis": "+x", "label": ["East", "Istok", "E"]},
            {"axis": "+y", "label": "Zenith"},
            {"axis": "-z", "label": ["South", "Jug"]},
        ],
    },
    "cube": {"type": "cube", "colors": "poles"},
    "nested": {
        "type": "cube", "name": "shell", "colors": "poles",
        "children": [{"type": "cube", "name": "core", "size": 0.45, "color": "#F5F5F5"}],
    },
}


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication(sys.argv)


def _settle(app, ms: int = SETTLE_MS) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    app.processEvents()


@pytest.fixture(scope="module")
def web(app):
    widget = Preview3DWidget()
    widget.resize(*SIZE)
    widget.show()
    loop = QEventLoop()
    widget.loadFinished.connect(lambda ok: loop.quit())
    QTimer.singleShot(LOAD_TIMEOUT_MS, loop.quit)
    loop.exec()
    _settle(app)
    yield widget
    widget.deleteLater()


@pytest.fixture
def light(app):
    widget = Preview3DLightWidget()
    widget.resize(*SIZE)
    widget.show()
    _settle(app, 100)
    yield widget
    widget.deleteLater()


def _web_parts(app, widget) -> list[dict]:
    result = {}
    loop = QEventLoop()

    def done(parts):
        result["parts"] = parts
        loop.quit()

    widget.list_parts(done)
    QTimer.singleShot(5_000, loop.quit)
    loop.exec()
    return result.get("parts", [])


@pytest.mark.parametrize("name", list(SPECS))
def test_same_part_paths(app, web, light, name):
    """A model authored per MODELS.md must be addressable identically in both."""
    spec = SPECS[name]
    web.show_scene(spec)
    light.show_scene(spec)
    _settle(app)

    web_paths = [p["path"] for p in _web_parts(app, web)]
    light_paths = [p["path"] for p in light.list_parts()]
    assert light_paths == web_paths, f"part trees diverge for the {name!r} spec"


@pytest.mark.parametrize("name", list(SPECS))
def test_same_initial_visibility(app, web, light, name):
    """Switch groups must start on the same child in both."""
    spec = SPECS[name]
    web.show_scene(spec)
    light.show_scene(spec)
    _settle(app)

    web_visible = {p["path"]: p["visible"] for p in _web_parts(app, web)}
    light_visible = {p["path"]: p["visible"] for p in light.list_parts()}
    assert light_visible == web_visible


def test_show_only_agrees(app, web, light):
    spec = SPECS["labelled axes"]
    group = "axes/arm:+x/labels"
    web.show_scene(spec)
    light.show_scene(spec)
    _settle(app)

    web.show_only(group, "label:2")
    light.show_only(group, "label:2")
    _settle(app)

    web_visible = [p["visible"] for p in _web_parts(app, web) if p["path"].startswith(group + "/")]
    light_visible = [p["visible"] for p in light.list_parts() if p["path"].startswith(group + "/")]
    assert web_visible == light_visible == [False, False, True]


def test_opacity_does_not_leak_to_siblings(app, web, light):
    """Both must isolate a part's opacity, whatever their material model."""
    spec = SPECS["axes"]
    web.show_scene(spec)
    light.show_scene(spec)
    _settle(app)

    web.set_part_opacity("axes/arm:+x/shaft", 0.25)
    light.set_part_opacity("axes/arm:+x/shaft", 0.25)
    _settle(app)

    for parts in (_web_parts(app, web), light.list_parts()):
        by_path = {p["path"]: p["opacity"] for p in parts}
        assert by_path["axes/arm:+x/shaft"] == pytest.approx(0.25)
        assert by_path["axes/arm:+x/tip"] == pytest.approx(1.0)


def test_framing_and_camera_state_agree(app, web, light):
    """Same spec, same view, same aspect — the camera must land in the same place."""
    spec = SPECS["cube"]
    web.show_scene(spec)
    light.show_scene(spec)
    _settle(app)
    web.set_view("iso")
    light.set_view("iso")
    _settle(app)

    seen = {}
    web.camera_changed.connect(lambda state: seen.update(state))
    web.orbit_by(0, 0)          # nudge a fresh report without moving anything
    _settle(app)

    light_state = light.camera_state()
    assert light_state["azimuth"] == pytest.approx(seen["azimuth"], abs=0.5)
    assert light_state["elevation"] == pytest.approx(seen["elevation"], abs=0.5)
    # Aspect differs slightly (the web page has its own margins), so compare loosely.
    assert light_state["distance"] == pytest.approx(seen["distance"], rel=0.15)


def test_unknown_part_path_fails_loudly(light):
    with pytest.raises(KeyError):
        light.set_part_visible("axes/nope", False)


def test_shared_spec_is_the_only_palette_source():
    """Neither renderer may restate a pole colour in its own source."""
    shared = json.loads((ROOT / "shared" / "spec.json").read_text(encoding="utf-8"))
    poles = set(shared["poles"].values())

    sources = [ROOT / "src" / "primitives.js", ROOT / "preview3d" / "light" / "primitives.py"]
    for source in sources:
        text = source.read_text(encoding="utf-8")
        restated = [color for color in poles if color in text]
        assert not restated, (
            f"{source.name} restates {restated} instead of reading shared/spec.json"
        )
