"""The model schema — what a consumer's exporter is held to.

PLAN.md promised one renderer-neutral schema (axes / cells / views) and that
"the demo model and DOMY's exported model both validate". DOMY generates its
model from its canon, so the failure mode this guards is a field that is quietly
wrong in generated data and surfaces three screens later as a missing label.

The schema itself is DATA (shared/model_schema.json), read by this validator and
by src/model.js — which is what makes "it validates" mean the same thing on both
sides. These tests check the interpreter, not a hand-written list of rules.
"""

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from preview3d.cube_model import build_cube_model  # noqa: E402
from preview3d.model import ModelError, load_schema, validate  # noqa: E402
from preview3d.model_scene import GROUP_PATHS  # noqa: E402


@pytest.fixture(scope="module")
def model():
    return build_cube_model()


def test_the_shipped_model_validates(model):
    assert validate(copy.deepcopy(model)) is not None


def test_the_schema_ships_as_data():
    """A schema in code could not be read by the JS validator, and the two would
    drift the first time either was edited."""
    schema = load_schema()
    assert schema["root"] == "model"
    assert {"axis", "cell", "view", "names", "seat"} <= set(schema["types"])


def test_the_shape_the_plan_promised(model):
    """axes (id, tier, two end directions, per-end luminous/fallen terms and a
    colour), cells (id, position, kind, colours, per-register names) and views."""
    axis = model["axes"][0]
    assert set(axis) == {"id", "tier", "name", "ends"}
    assert len(axis["ends"]) == 2
    assert set(axis["ends"][0]) == {"direction", "color", "names"}
    assert set(axis["ends"][0]["names"]["canon"]) == {"luminous", "fallen"}

    cell = model["cells"][0]
    assert set(cell) == {"id", "kind", "position", "color", "names"}

    view = model["views"][0]
    assert set(view) >= {"name", "opacity"}


def test_thirteen_axes_and_twenty_seven_seats(model):
    assert len(model["axes"]) == 13
    assert len(model["cells"]) == 27
    kinds = [cell["kind"] for cell in model["cells"]]
    assert [kinds.count(k) for k in ("face", "edge", "vertex", "centre")] == [6, 12, 8, 1]


def test_every_seat_speaks_in_every_register(model):
    for cell in model["cells"]:
        assert set(cell["names"]) == set(model["registers"])
    for axis in model["axes"]:
        for end in axis["ends"]:
            assert set(end["names"]) == set(model["registers"])


# ---- What it refuses --------------------------------------------------------


def _broken(model, mutate):
    copied = copy.deepcopy(model)
    mutate(copied)
    return copied


@pytest.mark.parametrize(("what", "mutate", "expected"), [
    ("a missing required field", lambda m: m["axes"][0].pop("tier"), "missing required field"),
    ("an unknown field", lambda m: m["axes"][0].update(colour="#FFFFFF"), "unknown field"),
    ("a tier that is not one", lambda m: m["axes"][0].update(tier="quaternary"), "not one of"),
    ("a direction that is not one", lambda m: m["axes"][0]["ends"][0].update(direction="+q"), "Unknown direction"),
    ("a colour that is not one", lambda m: m["axes"][0]["ends"][0].update(color="orange"), "#rrggbb"),
    ("an axis with one end", lambda m: m["axes"][0]["ends"].pop(), "exactly 2 entries"),
    ("a seat kind that is not one", lambda m: m["cells"][0].update(kind="corner"), "not one of"),
    ("a position that is not a point", lambda m: m["cells"][0].update(position=[0, 0]), "3 finite numbers"),
    ("a register the model does not carry", lambda m: m["cells"][0]["names"].update(extra={"luminous": "a", "fallen": "b"}), "unexpected entries"),
    ("a register with nothing to say", lambda m: m["cells"][0]["names"].pop("myth"), "missing entries"),
    ("a seat with only one reading", lambda m: m["cells"][0]["names"]["canon"].pop("fallen"), "missing required field"),
    ("no views at all", lambda m: m.pop("views"), "missing required field"),
])
def test_a_broken_model_fails_with_a_path(model, what, mutate, expected):
    """The message must say WHERE. A model is generated data — 'invalid model'
    with no location is not something a consumer can act on (Rule 1)."""
    with pytest.raises(ModelError) as error:
        validate(_broken(model, mutate))
    message = str(error.value)
    assert expected in message, f"{what}: {message}"
    assert message.startswith("model"), f"{what}: no path in {message!r}"


def test_the_path_points_at_the_offending_entry(model):
    with pytest.raises(ModelError, match=r"model\.axes\[2\]\.ends\[1\]\.color"):
        validate(_broken(model, lambda m: m["axes"][2]["ends"][1].update(color="nope")))


def test_a_model_with_fewer_registers_is_held_to_exactly_those():
    """The schema reads the model's OWN register list, so a two-register model
    is not forced to invent the other two — and cannot silently omit one."""
    small = build_cube_model(registers=["canon", "myth"])
    assert set(small["cells"][0]["names"]) == {"canon", "myth"}
    with pytest.raises(ModelError, match="unexpected entries"):
        validate(_broken(small, lambda m: m["cells"][0]["names"].update(
            movie={"luminous": "a", "fallen": "b"})))


def test_a_vocabulary_with_a_hole_fails_at_the_builder():
    """Before validation even runs: a missing word would otherwise become a
    blank label nobody could explain."""
    from preview3d.cube_model import DEMO_VOCABULARY
    holed = copy.deepcopy(DEMO_VOCABULARY)
    holed["canon"].pop("+z")
    with pytest.raises(ValueError, match="missing"):
        build_cube_model(vocabulary=holed)


def test_a_view_naming_an_unknown_group_fails():
    with pytest.raises(ValueError, match="unknown group"):
        build_cube_model(views=[{"name": "bad", "opacity": {"quaternary": 1.0}}])


def test_every_view_addresses_every_group(model):
    """A view sets every group explicitly, including to zero — otherwise
    switching views would leave a family lit from the one before it."""
    for view in model["views"]:
        assert set(view["opacity"]) == set(GROUP_PATHS.values())
