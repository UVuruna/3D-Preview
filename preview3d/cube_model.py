"""The thirteen-axis cube model, COMPUTED.

The four owner models — primary axes, secondary axes, tertiary axes, the glass
cube — are four VIEWS over ONE model, never four hand-built scenes. This module
builds that model: 13 axes (3 face + 6 edge + 4 vertex), 27 seats (6 + 12 + 8 +
the centre), every colour derived, every position derived, and the four views.

Nothing here is a stored file (root Rule 19). The geometry follows from the
cube, the colours follow from the poles, and the words follow from a small seed
vocabulary of the SIX poles: a two-letter seat says what its two poles say, a
three-letter seat what its three say. Twelve words per register become
fifty-four seats.

**A consumer supplies the words, never the geometry.** Watch Academy's exporter
calls `build_cube_model(vocabulary=..., sacred=...)` with its own canon, so the
sixty-five terms stay in DOMY and this gadget stays content-agnostic. What ships
here is a neutral demo vocabulary that shows the structure and claims nothing.

Pure Python; the JS mirror is src/cubemodel.js.
"""

from . import axis_colors
from .directions import (
    canonical_token,
    cube_axes,
    cube_tokens,
    opposite_token,
    tier_of,
    token_letters,
    token_vector,
)
from .model import validate
from .model_scene import GROUP_PATHS
from .resources import load_shared_spec

_SPEC = load_shared_spec()
_SWITCHER = _SPEC["switcher"]
REGISTERS: list[str] = list(_SWITCHER["registers"])

# How a derived seat says what its poles say. One separator, so a reader can
# always see that a compound term IS its parents.
JOIN = " · "

CENTRE = "centre"
ROOT_NAME = "model"

# Where each family sits in the scene tree. Owned by model_scene, because the
# tree is its statement — a view here only names the families.
GROUPS = GROUP_PATHS

# The seed vocabulary: six poles plus the centre, per register, each as
# (luminous, fallen). Deliberately generic English — this is a DEMO of the
# structure, not anybody's canon.
DEMO_VOCABULARY: dict[str, dict[str, tuple[str, str]]] = {
    "canon": {
        "+x": ("Warmth", "Scorching"),   "-x": ("Calm", "Coldness"),
        "+y": ("Clarity", "Glare"),      "-y": ("Depth", "Murk"),
        "+z": ("Growth", "Rankness"),    "-z": ("Force", "Violence"),
        CENTRE: ("Centre", "Dispersion"),
    },
    "myth": {
        "+x": ("Hearth", "Wildfire"),    "-x": ("Ocean", "Abyss"),
        "+y": ("Sun", "Drought"),        "-y": ("Night", "Delirium"),
        "+z": ("Forest", "Thicket"),     "-z": ("Forge", "Ruin"),
        CENTRE: ("The Axis", "The Void"),
    },
    "historical": {
        "+x": ("Trade", "Plunder"),      "-x": ("Council", "Stagnation"),
        "+y": ("Reason", "Dogma"),       "-y": ("Mystery", "Superstition"),
        "+z": ("Harvest", "Excess"),     "-z": ("Defence", "Conquest"),
        CENTRE: ("The Capital", "The Interregnum"),
    },
    "movie": {
        "+x": ("Hero", "Zealot"),        "-x": ("Mentor", "Recluse"),
        "+y": ("Sage", "Pedant"),        "-y": ("Seer", "Charlatan"),
        "+z": ("Guardian", "Hoarder"),   "-z": ("Champion", "Tyrant"),
        CENTRE: ("The Protagonist", "The Extra"),
    },
}

# The four owner models. Each is a view: which groups speak, how loudly, and
# where the camera stands. Values are plain opacities, so a scene can TWEEN
# from one owner model into another without an engine change.
DEFAULT_VIEWS = [
    {
        "name": "primary", "label": "Primary Axes", "camera": "+x+y+z",
        "opacity": {"primary": 1.0},
    },
    {
        # The whole point of a 3D previewer: a flat wheel cannot show an edge
        # axis at its true angle. The face axes stay faintly lit as the frame
        # the edge axes are measured against.
        "name": "secondary", "label": "Secondary Axes", "camera": "+x+y+z",
        "opacity": {"primary": 0.18, "secondary": 1.0},
    },
    {
        # Seen from a direction PERPENDICULAR to the sacred diagonal, so the one
        # axis that matters most shows its true length instead of collapsing to
        # a point (which is exactly what the iso view does to it).
        "name": "tertiary", "label": "Tertiary Axes", "camera": "-x+y",
        "opacity": {"primary": 0.15, "tertiary": 1.0, "sacred": 1.0, "vertex": 0.85, CENTRE: 1.0},
    },
    {
        "name": "cube", "label": "The Cube", "camera": "+x+y+z",
        "opacity": {
            "primary": 0.55, "secondary": 0.5, "tertiary": 0.5, "sacred": 0.85,
            "face": 1.0, "edge": 1.0, "vertex": 1.0, CENTRE: 1.0, "glass": 0.12,
        },
    },
]

GLASS_OPACITY = 0.12


def build_cube_model(
    name: str = "cube13",
    label: str = "The Thirteen Axes",
    size: float = 1.0,
    sacred: str | None = "+x+y+z",
    registers: list[str] | None = None,
    vocabulary: dict | None = None,
    views: list[dict] | None = None,
) -> dict:
    """The full model, validated against the shipped schema before it is returned.

    `sacred` names the one body diagonal that leaves the six-colour palette for
    white-gold; `None` leaves all four vertex axes in the human tertiary family.
    """
    registers = list(registers or REGISTERS)
    vocabulary = vocabulary or DEMO_VOCABULARY
    _check_vocabulary(vocabulary, registers)

    sacred_token = canonical_token(sacred) if sacred else None
    sacred_ends = {sacred_token, opposite_token(sacred_token)} if sacred_token else set()
    palette = axis_colors.derive_all()

    def dress(token: str) -> str:
        return axis_colors.SACRED if token in sacred_ends else palette[token]

    model = {
        "name": name,
        "label": label,
        "root": ROOT_NAME,
        "size": float(size),
        "registers": registers,
        "axes": _build_axes(sacred_token, registers, vocabulary, dress),
        "cells": _build_cells(size, registers, vocabulary, dress, sacred_ends),
        "glass": {"opacity": GLASS_OPACITY},
        "views": [_expand_view(view) for view in (views or DEFAULT_VIEWS)],
    }
    return validate(model)


# ---- Axes -------------------------------------------------------------------


def _build_axes(sacred_token, registers, vocabulary, dress) -> list[dict]:
    axes = []
    for letters in (1, 2, 3):
        for positive, negative in cube_axes(letters):
            tier = "sacred" if positive == sacred_token else tier_of(positive)
            axes.append({
                "id": positive,
                "tier": tier,
                "name": f"{positive} / {negative}",
                "ends": [
                    _end(positive, dress(positive), registers, vocabulary),
                    _end(negative, dress(negative), registers, vocabulary),
                ],
            })
    return axes


def _end(token: str, color: str, registers, vocabulary) -> dict:
    return {"direction": token, "color": color, "names": _names(token, registers, vocabulary)}


# ---- Cells ------------------------------------------------------------------


def _build_cells(size, registers, vocabulary, dress, sacred_ends) -> list[dict]:
    """The 26 seats plus the centre.

    A seat's position is its token's UN-normalised vector times half the cube:
    '+x' lands on a face centre, '+x+y' on an edge midpoint, '+x+y+z' on a
    vertex. One rule, three kinds of seat — and each seat is exactly where the
    axis end of the same name points.
    """
    kinds = {1: "face", 2: "edge", 3: "vertex"}
    half = float(size) / 2
    cells = []
    for letters in (1, 2, 3):
        for token in cube_tokens(letters):
            vector = token_vector(token)
            cells.append({
                "id": token,
                "kind": kinds[letters],
                "position": [component * half for component in vector],
                "color": dress(token),
                "names": _names(token, registers, vocabulary),
            })
    cells.append({
        "id": CENTRE,
        "kind": CENTRE,
        "position": [0.0, 0.0, 0.0],
        # The centre is the one seat no axis points at; it wears the sacred
        # dress whether or not a sacred axis was named, because it is where
        # every axis crosses.
        "color": axis_colors.SACRED,
        "names": _names(CENTRE, registers, vocabulary),
    })
    return cells


# ---- Words ------------------------------------------------------------------


def _names(token: str, registers, vocabulary) -> dict:
    """What this seat says, per register — computed from its poles."""
    return {register: _seat(token, vocabulary[register]) for register in registers}


def _seat(token: str, words: dict) -> dict:
    if token == CENTRE:
        luminous, fallen = words[CENTRE]
        return {"luminous": luminous, "fallen": fallen}
    poles = [("+" if sign > 0 else "-") + letter for letter, sign in token_letters(token)]
    return {
        "luminous": JOIN.join(words[pole][0] for pole in poles),
        "fallen": JOIN.join(words[pole][1] for pole in poles),
    }


def _check_vocabulary(vocabulary: dict, registers: list[str]) -> None:
    """A missing word must fail here, not as a blank label nobody can explain."""
    needed = [token for token in cube_tokens(1)] + [CENTRE]
    for register in registers:
        words = vocabulary.get(register)
        if not words:
            raise ValueError(
                f"The vocabulary has no register {register!r} — it must cover {', '.join(registers)}"
            )
        missing = [token for token in needed if token not in words]
        if missing:
            raise ValueError(
                f"The {register!r} vocabulary is missing {', '.join(missing)} — every "
                "register needs the six poles and the centre"
            )


# ---- Views ------------------------------------------------------------------


def _expand_view(view: dict) -> dict:
    """Turn a view's short group keys into the part paths the viewer addresses.

    A view names GROUPS ('secondary', 'glass'); the scene tree wants paths
    ('axes/secondary', 'glass'). Every group the view does not mention is set
    to 0 explicitly rather than left out, so switching between views can never
    leave a group lit from the previous one.
    """
    unknown = [key for key in view["opacity"] if key not in GROUPS]
    if unknown:
        raise ValueError(
            f"View {view['name']!r} sets unknown group(s) {', '.join(sorted(unknown))} — "
            f"available: {', '.join(GROUPS)}"
        )
    expanded = {path: 0.0 for path in GROUPS.values()}
    for group, opacity in view["opacity"].items():
        expanded[GROUPS[group]] = float(opacity)
    result = {"name": view["name"], "opacity": expanded}
    if "label" in view:
        result["label"] = view["label"]
    if "camera" in view:
        result["camera"] = view["camera"]
    return result
