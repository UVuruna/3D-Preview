"""Conformance: a scene must play the same in both renderers.

The timeline is the one piece of the component that exists twice in two
languages — `src/animation.js` and `preview3d/light/animation.py`. Everything
else either reads shared/spec.json or is renderer-specific by design, so this
file is where drift would actually happen: an easing curve rounded differently,
a key boundary resolved on the other side, a bool interpolating in one language
and stepping in the other.

These are PLAN.md's golden tests, made concrete: every shipped scene is driven
to t = 0, ½ and 1 in both renderers and what a host can observe — camera angles,
projection, per-part visibility and opacity, the frame counter — has to match.

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

from preview3d import Preview3DLightWidget, Preview3DWidget, load_shared_scenes, load_shared_spec  # noqa: E402
from preview3d.light.animation import EASINGS, Timeline, ease  # noqa: E402

LOAD_TIMEOUT_MS = 20_000
SETTLE_MS = 400
SIZE = (600, 480)
ANGLE_TOLERANCE = 0.5
INSTANTS = (0.0, 0.5, 1.0)

SCENES = {scene["name"]: scene for scene in load_shared_scenes()}
SPEC = load_shared_spec()

# Scenes that do not ship their own content play on whatever is loaded.
DEFAULT_CONTENT = {"type": "cube", "colors": "poles"}


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


# ---- Reading the web renderer ----------------------------------------------


def _await_callback(app, call) -> object:
    """Drive the event loop until an async widget answer arrives."""
    result = {}
    loop = QEventLoop()

    def done(value):
        result["value"] = value
        loop.quit()

    call(done)
    QTimer.singleShot(5_000, loop.quit)
    loop.exec()
    assert "value" in result, "the web renderer did not answer in time"
    return result["value"]


def _web_evaluate(app, widget, expression):
    """Evaluate a JS expression in the page.

    Reaches for the widget's private marshaller on purpose: the viewer's JS API
    is public but Python has no general "evaluate this" entry point, and adding
    one to the shipping widget just so a test could compare the two easing
    implementations would be a worse trade than this line.
    """
    return _await_callback(app, lambda done: widget._run_json(expression, done))


def _web_camera(app, widget, action) -> dict:
    """Run `action`, then return the camera state the page reports for it."""
    seen = {}

    def remember(state):
        seen.update(state)

    widget.camera_changed.connect(remember)
    try:
        action()
        _settle(app)
    finally:
        widget.camera_changed.disconnect(remember)
    assert seen, "the web renderer reported no camera state"
    return seen


# ---- Helpers ----------------------------------------------------------------


def _angle_gap(a: float, b: float) -> float:
    """Shortest distance between two bearings.

    -180 and +180 name the same direction, and the two renderers arrive at that
    boundary from different arithmetic (an atan2 versus a modulo), so comparing
    the raw numbers would fail on the one scene that passes through due south.
    """
    return abs((a - b + 180) % 360 - 180)


def _load(app, web, light, scene: dict) -> None:
    content = scene.get("content", DEFAULT_CONTENT)
    for widget in (web, light):
        widget.show_scene(content)
        # A scene without a projection track leaves the projection alone — which
        # is correct, and means the web widget (one instance for the whole
        # module) would otherwise carry the hexagon scene's orthographic switch
        # into the next scene while the LIGHT widget starts fresh.
        widget.set_projection("perspective")
        widget.set_animation(scene)
    _settle(app)


def _part_state(parts: list[dict]) -> dict:
    return {part["path"]: (part["visible"], round(part["opacity"], 4)) for part in parts}


# ---- The pins ---------------------------------------------------------------


@pytest.mark.parametrize("name", list(SCENES))
def test_every_shipped_scene_loads(name):
    """A descriptor that fails validation must fail here, not on the owner's screen."""
    timeline = Timeline(SCENES[name])
    assert timeline.tracks, f"scene {name!r} animates nothing"
    assert timeline.frames > 0


def test_easing_curves_agree():
    """The highest-risk drift: two hand-written implementations of one curve."""
    for curve in SPEC["animation"]["easings"]:
        assert curve in EASINGS, f"shared/spec.json lists easing {curve!r} that Python lacks"


def test_easing_curves_agree_with_the_web_core(app, web):
    samples = [0.0, 0.25, 0.5, 0.75, 1.0]
    for curve in SPEC["animation"]["easings"]:
        expression = f"[{','.join(f'Preview3D.ease({json.dumps(curve)},{t})' for t in samples)}]"
        from_js = _web_evaluate(app, web, expression)
        from_python = [ease(curve, t) for t in samples]
        assert from_js == pytest.approx(from_python, abs=1e-9), f"easing {curve!r} differs"


def test_both_read_the_shared_animation_spec(app, web):
    """Neither renderer may carry its own copy of fps, speeds or the channels."""
    shared = SPEC["animation"]
    from_js = _web_evaluate(app, web, "Preview3D.ANIMATION_DEFAULTS")
    assert from_js["fps"] == shared["fps"]
    assert from_js["speeds"] == shared["speeds"]
    assert sorted(from_js["channels"]) == sorted(shared["channels"])
    assert Timeline(SCENES["turntable"]).fps == shared["fps"]


@pytest.mark.parametrize("name", list(SCENES))
def test_same_camera_at_key_instants(app, web, light, name):
    scene = SCENES[name]
    _load(app, web, light, scene)

    for instant in INSTANTS:
        web_state = _web_camera(app, web, lambda: web.seek_animation(instant))
        light.seek_animation(instant)
        light_state = light.camera_state()

        where = f"scene {name!r} at t={instant}"
        assert _angle_gap(light_state["azimuth"], web_state["azimuth"]) < ANGLE_TOLERANCE, where
        assert light_state["elevation"] == pytest.approx(web_state["elevation"], abs=ANGLE_TOLERANCE), where
        assert light_state["projection"] == web_state["projection"], where
        # The page has its own margins, so the aspect — and with it the framing
        # distance — differs slightly; the RATIO between instants is what a
        # dolly track controls and what has to agree.
        assert light_state["distance"] == pytest.approx(web_state["distance"], rel=0.15), where


@pytest.mark.parametrize("name", ["xray", "legend"])
def test_same_part_state_at_key_instants(app, web, light, name):
    """The scenes that drive parts rather than only the camera."""
    scene = SCENES[name]
    _load(app, web, light, scene)

    for instant in INSTANTS:
        web.seek_animation(instant)
        light.seek_animation(instant)
        _settle(app)

        web_parts = _part_state(_await_callback(app, web.list_parts))
        light_parts = _part_state(light.list_parts())
        assert light_parts == web_parts, f"scene {name!r} leaves the parts different at t={instant}"


def test_playback_state_agrees(app, web, light):
    scene = SCENES["turntable"]
    _load(app, web, light, scene)

    for instant in INSTANTS:
        web.seek_animation(instant)
        light.seek_animation(instant)
        _settle(app)

        web_state = _await_callback(app, web.animation_state)
        light_state = light.animation_state()
        for field in ("scene", "duration", "frames", "loop", "speed", "frame", "playing"):
            assert light_state[field] == web_state[field], f"{field} differs at t={instant}"
        assert light_state["progress"] == pytest.approx(web_state["progress"], abs=1e-6)


def test_step_frame_agrees(app, web, light):
    """Single-frame stepping must land on the same instant, and pause."""
    scene = SCENES["turntable"]
    _load(app, web, light, scene)

    for _ in range(3):
        web.step_frame(1)
        light.step_frame(1)
    _settle(app)

    web_state = _await_callback(app, web.animation_state)
    light_state = light.animation_state()
    assert light_state["frame"] == web_state["frame"] == 3
    assert not light_state["playing"] and not web_state["playing"]


def test_instant_mode_matches_the_end_of_the_flight(app, web, light):
    """Jumping to the end must give exactly what playing to the end gives."""
    scene = SCENES["hexagon"]
    _load(app, web, light, scene)

    web_seek = _web_camera(app, web, lambda: web.seek_animation(1.0))
    light.seek_animation(1.0)
    light_seek = light.camera_state()

    web_jump = _web_camera(app, web, web.jump_to_end)
    light.jump_to_end()
    light_jump = light.camera_state()

    for seeked, jumped in ((web_seek, web_jump), (light_seek, light_jump)):
        assert _angle_gap(seeked["azimuth"], jumped["azimuth"]) < 1e-6
        assert seeked["elevation"] == pytest.approx(jumped["elevation"])
        assert seeked["projection"] == jumped["projection"]
    # …and the hexagon scene must actually land on the orthographic body-diagonal
    # view, which is the only one that makes a cube a regular hexagon.
    assert light_jump["projection"] == "orthographic"
    assert _angle_gap(light_jump["azimuth"], 45.0) < ANGLE_TOLERANCE
    assert light_jump["elevation"] == pytest.approx(35.264, abs=ANGLE_TOLERANCE)


def test_transport_without_a_scene_is_inert(light):
    """Documented no-op: pressing play before loading a scene must not raise."""
    light.play_animation()
    light.step_frame(1)
    light.jump_to_end()
    assert light.animation_state()["scene"] is None


def test_unknown_channel_fails_loudly():
    with pytest.raises(ValueError, match="unknown channel"):
        Timeline({"name": "bad", "duration": 1, "tracks": [
            {"channel": "camera.altitude", "keys": [{"t": 0, "value": 1}]},
        ]})


def test_channel_that_needs_a_path_fails_without_one():
    with pytest.raises(ValueError, match="needs a 'path'"):
        Timeline({"name": "bad", "duration": 1, "tracks": [
            {"channel": "part.opacity", "keys": [{"t": 0, "value": 1}]},
        ]})


def test_non_numeric_values_step_rather_than_interpolate():
    """A bool is an int in Python — without an explicit guard a visibility flag
    would cross-fade here while stepping in JavaScript."""
    timeline = Timeline({"name": "flags", "duration": 1, "tracks": [
        {"channel": "part.visible", "path": "a", "keys": [
            {"t": 0, "value": True}, {"t": 1, "value": False},
        ]},
        {"channel": "camera.projection", "keys": [
            {"t": 0, "value": "perspective"}, {"t": 1, "value": "orthographic"},
        ]},
    ]})
    midpoint = {entry["channel"]: entry["value"] for entry in timeline.sample(0.5)}
    assert midpoint["part.visible"] is True
    assert midpoint["camera.projection"] == "perspective"
