"""Model data to a scene SPEC — the one translation, in plain data.

A model says what exists (axes, seats, words); a scene spec says what to draw
(primitives, names, colours). This module is the whole bridge, and it produces
nothing but the same JSON specs a host could have written by hand — so both
renderers build a model through the primitive builders they already have,
rather than each growing its own model renderer.

The tree it builds is fixed, and every group in it exists whether or not it has
anything in it:

    <root>/
      axes/       primary/ secondary/ tertiary/ sacred/   ← a tier group each
      cells/      faces/ edges/ vertices/ centre/         ← a kind group each
      glass                                               ← the shell

That skeleton is a contract, not a convenience: a VIEW addresses those paths to
say which family speaks, so a missing group would be a view that fails halfway
through instead of one that dims nothing.

Pure Python; the JS mirror is src/modelscene.js, and both are pinned against
each other through the renderers by tests/test_model_parity.py.
"""

from .directions import parse_direction
from .resources import load_shared_spec
from .vectors import normalize, scale

_SPEC = load_shared_spec()
_TIERS: dict = {k: v for k, v in _SPEC["axisTiers"].items() if not k.startswith("_")}
TIER_ORDER: list[str] = list(_SPEC["tierOrder"])
_KINDS: dict = {k: v for k, v in _SPEC["cellKinds"].items() if not k.startswith("_")}
KIND_ORDER: list[str] = list(_SPEC["cellKindOrder"])
_SCENE: dict = _SPEC["modelScene"]
_RADIAL: dict = _SPEC["switcher"]["radial"]
STOPS: list[str] = list(_SPEC["switcher"]["stops"])

AXES_GROUP = "axes"
CELLS_GROUP = "cells"
GLASS_GROUP = "glass"

# Short group name -> the path a view addresses it by. A view speaks in
# families ('secondary', 'glass'); the tree speaks in paths.
GROUP_PATHS: dict[str, str] = {
    **{tier: f"{AXES_GROUP}/{tier}" for tier in TIER_ORDER},
    **{kind: f"{CELLS_GROUP}/{_KINDS[kind]['group']}" for kind in KIND_ORDER},
    GLASS_GROUP: GLASS_GROUP,
}


def root_name(model: dict) -> str:
    return model.get("root") or "model"


def build_spec(model: dict) -> dict:
    """The whole model as one nested primitive spec."""
    size = float(model.get("size", 1.0))
    registers = list(model["registers"])
    return {
        "type": "group",
        "name": root_name(model),
        "children": [
            _axes_group(model, size, registers),
            _cells_group(model, size, registers),
            _glass(model, size),
        ],
    }


def view_opacities(model: dict, view_name: str) -> dict[str, float]:
    """A view's opacity map, keyed by FULL part path."""
    view = find_view(model, view_name)
    prefix = root_name(model)
    return {f"{prefix}/{path}": float(alpha) for path, alpha in view["opacity"].items()}


def find_view(model: dict, view_name: str) -> dict:
    for view in model["views"]:
        if view["name"] == view_name:
            return view
    known = ", ".join(view["name"] for view in model["views"])
    raise KeyError(f"Model {model['name']!r} has no view {view_name!r} — available: {known}")


# ---- Axes -------------------------------------------------------------------


def _axes_group(model: dict, size: float, registers: list[str]) -> dict:
    by_tier: dict[str, list[dict]] = {tier: [] for tier in TIER_ORDER}
    for axis in model["axes"]:
        by_tier[axis["tier"]].append(_axis(axis, size, registers))
    return {
        "type": "group", "name": AXES_GROUP,
        "children": [
            {"type": "group", "name": tier, "children": by_tier[tier]}
            for tier in TIER_ORDER
        ],
    }


def _axis(axis: dict, size: float, registers: list[str]) -> dict:
    tier = _TIERS[axis["tier"]]
    length = float(tier["length"]) * size
    return {
        "type": "axes",
        "name": f"axis:{axis['id']}",
        "armLength": length,
        "armRadius": float(tier["radius"]) * size,
        # One joint per axis would put thirteen spheres in the same spot; the
        # centre seat is the crossing point the model actually names.
        "joint": False,
        "arms": [_arm(end, length, registers) for end in axis["ends"]],
    }


def _arm(end: dict, length: float, registers: list[str]) -> dict:
    """One half-axis, with its two radial stops.

    The radial law is geometry here, not a caption: the luminous stop sits
    INSIDE the geometric end and the fallen stop PAST it, so a reading of
    'both' draws the five stations of the axis by itself.
    """
    direction = parse_direction(end["direction"])
    arm = {
        "axis": end["direction"] if isinstance(end["direction"], str) else list(direction),
        "color": end["color"],
        "stopHeight": float(_SCENE["armLabelHeight"]) * length,
        "stops": [
            {
                "name": stop,
                "anchor": list(scale(direction, length * float(_RADIAL[stop]))),
                "labels": {register: end["names"][register][stop] for register in registers},
            }
            for stop in STOPS
        ],
    }
    return arm


# ---- Cells ------------------------------------------------------------------


def _cells_group(model: dict, size: float, registers: list[str]) -> dict:
    by_kind: dict[str, list[dict]] = {kind: [] for kind in KIND_ORDER}
    for cell in model.get("cells", ()):
        by_kind[cell["kind"]].append(_cell(cell, size, registers))
    return {
        "type": "group", "name": CELLS_GROUP,
        "children": [
            {"type": "group", "name": _KINDS[kind]["group"], "children": by_kind[kind]}
            for kind in KIND_ORDER
        ],
    }


def _cell(cell: dict, size: float, registers: list[str]) -> dict:
    """A seat: a small marker plus its two readings, stacked around it.

    Seats do not carry the axes' radial law — a seat IS a station — so its two
    readings simply sit above and below the marker, which keeps them legible
    when twenty-seven of them are on screen at once.
    """
    gap = float(_SCENE["cellLabelGap"]) * size
    return {
        "type": "marker",
        "name": f"cell:{cell['id']}",
        "position": list(cell["position"]),
        "radius": float(_KINDS[cell["kind"]]["radius"]) * size,
        "color": cell["color"],
        "stopHeight": float(_SCENE["labelHeight"]) * size,
        "stops": [
            {
                "name": stop,
                "anchor": [0.0, gap if stop == STOPS[0] else -gap, 0.0],
                "labels": {register: cell["names"][register][stop] for register in registers},
            }
            for stop in STOPS
        ],
    }


# ---- Glass ------------------------------------------------------------------


def _glass(model: dict, size: float) -> dict:
    """The shell the seats are seen through — an empty group when there is none,
    so a view can always address the path."""
    glass = model.get("glass")
    if not glass:
        return {"type": "group", "name": GLASS_GROUP, "children": []}
    spec = {"type": "cube", "name": GLASS_GROUP, "size": size, "colors": "poles"}
    if glass.get("colors"):
        spec["colors"] = list(glass["colors"])
    return spec


def outward(position) -> tuple:
    """The direction a seat faces, for a host that wants to place something
    beside it. The centre has no outward direction, so it reports world up."""
    if all(abs(component) < 1e-12 for component in position):
        return (0.0, 1.0, 0.0)
    return normalize(tuple(float(component) for component in position))
