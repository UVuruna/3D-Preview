"""The model layer must mean the same thing in both languages, and in both renderers.

The model layer now exists TWICE — `preview3d/` in Python and `src/` in
JavaScript — for the same reason the timeline does: a website has no Python and
a lean Qt app has no browser. That is a standing invitation to drift (root Rule
#5), and here it would drift silently: a colour rounded the other way, a seat
positioned from a different rule, a switcher lighting a different group.

Two levels of pin, deliberately:

1. **Data parity** — the two implementations are run head to head and their
   OUTPUT compared exactly: the computed palette, the whole model, the scene
   spec it becomes, and the 24 orientations. This is the strongest check the
   component has, because the answer is a value rather than a picture. It needs
   Node (only to run the JS at all) and skips without it.
2. **Renderer parity** — the same model goes into both widgets and everything a
   host can observe is compared: part paths, per-part colour, the Switcher's
   effect, and a view's opacities. This needs no Node, and covers the two
   renderers rather than the two languages.
"""

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from preview3d import Preview3DLightWidget, Preview3DWidget  # noqa: E402
from preview3d import axis_colors, model_scene, orientations  # noqa: E402
from preview3d.cube_model import build_cube_model  # noqa: E402

LOAD_TIMEOUT_MS = 20_000
SETTLE_MS = 500
SIZE = (600, 480)

# What the JS side is asked to produce. Kept beside the Python expression of the
# same thing below, so the two cannot answer different questions.
DUMP_ENTRY = """
import { buildCubeModel } from './src/cubemodel.js';
import { buildSpec } from './src/modelscene.js';
import { deriveAll } from './src/axiscolors.js';
import { orientationAxes, orientationIds } from './src/orientations.js';
const model = buildCubeModel();
console.log(JSON.stringify({
    palette: deriveAll(),
    model,
    spec: buildSpec(model),
    orientations: Object.fromEntries(orientationIds().map((id) => [id, orientationAxes(id)])),
}));
"""


def _numbers(value):
    """Compare by VALUE, not by JSON spelling: JavaScript writes 1 where Python
    writes 1.0, and neither is a difference anybody could act on."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return round(float(value), 12)
    if isinstance(value, list):
        return [_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: _numbers(item) for key, item in value.items()}
    return value


@pytest.fixture(scope="module")
def javascript():
    """Run the JS model layer once and return what it produced."""
    entry = ROOT / f"_parity_{uuid.uuid4().hex}.js"
    bundle = entry.with_suffix(".mjs")
    entry.write_text(DUMP_ENTRY, encoding="utf-8")
    try:
        build = subprocess.run(
            ["npx", "esbuild", str(entry.name), "--bundle", "--format=esm",
             "--platform=node", f"--outfile={bundle.name}", "--log-level=error"],
            cwd=ROOT, capture_output=True, text=True, shell=True,
        )
        if build.returncode != 0:
            pytest.skip(f"esbuild unavailable — cannot compare the two languages ({build.stderr.strip()[:120]})")
        run = subprocess.run(["node", str(bundle.name)], cwd=ROOT,
                             capture_output=True, text=True, shell=True)
        if run.returncode != 0:
            pytest.fail(f"the JS model layer failed to run: {run.stderr.strip()}")
        return json.loads(run.stdout)
    except FileNotFoundError:            # pragma: no cover - environment without Node
        pytest.skip("Node is not installed — cannot compare the two languages")
    finally:
        entry.unlink(missing_ok=True)
        bundle.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def python_side():
    model = build_cube_model()
    return {
        "palette": axis_colors.derive_all(),
        "model": model,
        "spec": model_scene.build_spec(model),
        "orientations": {
            identifier: [list(axis) for axis in orientations.orientation_axes(identifier)]
            for identifier in orientations.orientation_ids()
        },
    }


@pytest.mark.parametrize("part", ["palette", "model", "spec", "orientations"])
def test_the_two_languages_produce_the_same_data(javascript, python_side, part):
    """Not "close enough" — identical. Every number here is derived by a stated
    rule, so any difference at all is one implementation reading the rule
    differently."""
    assert _numbers(javascript[part]) == _numbers(python_side[part])


# ---- Renderer parity --------------------------------------------------------


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication(sys.argv)


def _settle(app, ms: int = SETTLE_MS) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    app.processEvents()


@pytest.fixture(scope="module")
def model():
    return build_cube_model()


@pytest.fixture(scope="module")
def web(app, model):
    widget = Preview3DWidget()
    widget.resize(*SIZE)
    widget.show()
    loop = QEventLoop()
    widget.loadFinished.connect(lambda ok: loop.quit())
    QTimer.singleShot(LOAD_TIMEOUT_MS, loop.quit)
    loop.exec()
    _settle(app)
    widget.show_model(model)
    _settle(app, 1500)
    yield widget
    widget.deleteLater()


@pytest.fixture(scope="module")
def light(app, model):
    widget = Preview3DLightWidget()
    widget.resize(*SIZE)
    widget.show()
    _settle(app, 100)
    widget.show_model(model)
    _settle(app, 100)
    yield widget
    widget.deleteLater()


def _ask(app, widget, method, *args):
    """Read an answer out of the web widget, which can only answer late."""
    result = {}
    loop = QEventLoop()
    getattr(widget, method)(*args, lambda value: (result.setdefault("value", value), loop.quit()))
    QTimer.singleShot(5_000, loop.quit)
    loop.exec()
    return result.get("value")


def test_the_same_model_builds_the_same_part_tree(app, web, light):
    assert [p["path"] for p in light.list_parts()] == [p["path"] for p in _ask(app, web, "list_parts")]


def test_both_report_the_same_computed_colour_for_every_part(app, web, light):
    """The picture cannot be compared — the two shade differently on purpose —
    but the VALUE can, and a computed palette is exactly the thing that would
    drift unnoticed."""
    web_colors = {p["path"]: p["color"] for p in _ask(app, web, "list_parts")}
    light_colors = {p["path"]: p["color"] for p in light.list_parts()}
    assert set(web_colors) == set(light_colors)
    mismatched = {
        path: (web_colors[path], light_colors[path])
        for path in light_colors if web_colors[path] != light_colors[path]
    }
    assert not mismatched


def test_a_model_opens_on_its_first_view_in_both(app, web, light):
    seen = {}
    web.camera_changed.connect(lambda state: seen.update(state))
    web.orbit_by(0, 0)             # nudge a fresh report without moving anything
    _settle(app)
    assert light.camera_state()["modelView"] == seen["modelView"] == "primary"


@pytest.mark.parametrize("view", ["primary", "secondary", "tertiary", "cube"])
def test_every_owner_model_dims_the_same_groups(app, web, light, model, view):
    """The four owner models are four VIEWS over one model, and a view is
    nothing but per-group opacities — so the two renderers must land on the same
    numbers for the same view."""
    web.set_model_view(view)
    light.set_model_view(view)
    _settle(app)

    expected = model_scene.view_opacities(model, view)
    for parts in (_ask(app, web, "list_parts"), light.list_parts()):
        by_path = {p["path"]: p["opacity"] for p in parts}
        for path, alpha in expected.items():
            assert by_path[path] == pytest.approx(alpha), f"{view}: {path}"


@pytest.mark.parametrize(("register", "reading"), [
    ("canon", "luminous"), ("myth", "fallen"), ("movie", "both"),
])
def test_the_switcher_lights_the_same_labels_in_both(app, web, light, register, reading):
    web.set_switcher(register, reading)
    light.set_switcher(register, reading)
    _settle(app)

    web_visible = {p["path"]: p["visible"] for p in _ask(app, web, "list_parts")}
    light_visible = {p["path"]: p["visible"] for p in light.list_parts()}
    assert web_visible == light_visible

    # And it is the RIGHT set: the chosen register speaks, the others do not,
    # and only the lit stops are shown.
    lit = {"luminous", "fallen"} if reading == "both" else {reading}
    for path, visible in light_visible.items():
        tail = path.rsplit("/", 1)[-1]
        if tail in ("luminous", "fallen"):
            assert visible == (tail in lit), path
        elif tail.startswith("label:"):
            assert visible == (tail == f"label:{register}"), path


def test_showing_other_content_drops_the_model_in_both(app, web, light):
    """Content first, model second — the same rule a loaded scene follows."""
    web.show_scene({"type": "cube", "colors": "poles"})
    light.show_scene({"type": "cube", "colors": "poles"})
    _settle(app)

    seen = {}
    web.camera_changed.connect(lambda state: seen.update(state))
    web.orbit_by(0, 0)
    _settle(app)
    assert light.camera_state()["modelView"] is None
    assert seen["modelView"] is None
    with pytest.raises(RuntimeError, match="needs a model"):
        light.set_model_view("cube")
