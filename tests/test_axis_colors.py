"""The computed axis palette, and the collision rule with teeth.

Owner decree 2026-07-28 (PLAN.md, Colors for the New Axes): every non-primary
colour is DERIVED from the pole hues — a two-letter direction blends its two
poles and is thinned by moonlight, a three-letter one blends its three and is
deepened, and the singled-out sacred diagonal wears white-gold. Twenty-six
invented hex values would be twenty-six things to keep in sync (root Rule 19).

The moonlight thinning exists for one stated reason: a naive blend can land on a
hue the palette already spends, and two seats wearing one colour is a lie about
the structure. That is what `verify_palette` refuses, and what these tests pin —
including the arithmetic being identical in the two languages, since the same
formula exists twice (src/axiscolors.js).
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from preview3d import axis_colors  # noqa: E402
from preview3d.cube_model import build_cube_model  # noqa: E402
from preview3d.directions import cube_tokens  # noqa: E402
from preview3d.resources import load_shared_spec  # noqa: E402

POLES = load_shared_spec()["poles"]


def test_a_pole_wears_its_own_hue_unchanged():
    """The sealed six are not derived from anything — they ARE the seed."""
    for token, color in POLES.items():
        assert axis_colors.color_for(token, "primary") == color.upper()


def test_every_direction_gets_a_colour():
    palette = axis_colors.derive_all()
    assert len(palette) == 26
    assert set(palette) == {t for n in (1, 2, 3) for t in cube_tokens(n)}


def test_no_derived_colour_lands_on_a_pole():
    """THE COLLISION RULE. The naive blend of two poles can equal a third pole's
    hue; the moonlight thinning is what makes that impossible by construction."""
    palette = axis_colors.derive_all()
    for token, color in palette.items():
        if len(token) == 2:
            continue
        for pole, pole_color in POLES.items():
            assert axis_colors.distance(color, pole_color) >= axis_colors.MIN_POLE_DISTANCE, (
                f"{token} ({color}) is too close to the {pole} pole ({pole_color})"
            )


def test_no_two_seats_wear_the_same_colour():
    palette = axis_colors.derive_all()
    assert len(set(palette.values())) == len(palette)


def test_the_plain_blends_really_do_collide_and_the_dressed_ones_do_not():
    """The rule is only worth having if the UN-dressed colours are actually the
    broken ones, so the comparison is made rather than asserted.

    The worst plain blend is `+x+y-z` — orange, yellow and red average to
    something a few units from the orange pole itself, which is exactly the
    "two seats, one colour" failure the canon warns about. After thinning and
    deepening the closest anything comes to a pole is over four times the
    threshold away.
    """
    def nearest_pole(color):
        return min(axis_colors.distance(color, pole) for pole in POLES.values())

    compound = cube_tokens(2) + cube_tokens(3)
    plain = min(nearest_pole(axis_colors.blend(axis_colors.poles_of(t))) for t in compound)
    dressed = min(nearest_pole(color) for token, color in axis_colors.derive_all().items()
                  if token in compound)
    assert plain < axis_colors.MIN_POLE_DISTANCE, "the plain blends were fine; the rule would be pointless"
    assert dressed >= axis_colors.MIN_POLE_DISTANCE
    assert dressed > 4 * plain


def test_the_edge_family_is_lighter_and_the_vertex_family_darker():
    """Thinned toward moonlight, deepened toward ink — the two families must be
    distinguishable at a glance, which is the point of both operations."""
    def lightness(color):
        return sum(axis_colors.hex_to_rgb(color)) / 3

    palette = axis_colors.derive_all()
    edges = [lightness(palette[t]) for t in cube_tokens(2)]
    vertices = [lightness(palette[t]) for t in cube_tokens(3)]
    assert min(edges) > max(vertices)


def test_the_sacred_axis_wears_none_of_the_six():
    """White-gold, the seventh dress, so the one line through the centre never
    competes with the pole palette."""
    model = build_cube_model(sacred="+x+y+z")
    sacred = next(axis for axis in model["axes"] if axis["tier"] == "sacred")
    assert sacred["id"] == "+x+y+z"
    assert {end["color"] for end in sacred["ends"]} == {axis_colors.SACRED}
    for pole in POLES.values():
        assert axis_colors.distance(axis_colors.SACRED, pole) >= axis_colors.MIN_POLE_DISTANCE


def test_without_a_sacred_axis_all_four_diagonals_stay_human():
    model = build_cube_model(sacred=None)
    assert not [axis for axis in model["axes"] if axis["tier"] == "sacred"]
    assert len([axis for axis in model["axes"] if axis["tier"] == "tertiary"]) == 4


def test_the_centre_seat_is_sacred_even_without_a_sacred_axis():
    """It is where every axis crosses, whether or not one of them was named."""
    model = build_cube_model(sacred=None)
    centre = next(cell for cell in model["cells"] if cell["kind"] == "centre")
    assert centre["color"] == axis_colors.SACRED


def test_a_seat_wears_the_colour_of_the_axis_end_that_points_at_it():
    """One formula dresses the axis and the seat, because they are the same
    place — a second table for the cells would be the drift waiting to happen."""
    model = build_cube_model()
    ends = {end["direction"]: end["color"] for axis in model["axes"] for end in axis["ends"]}
    for cell in model["cells"]:
        if cell["kind"] == "centre":
            continue
        assert cell["color"] == ends[cell["id"]]


def test_the_verifier_actually_refuses_a_collision():
    """A guard nobody has seen fail is not a guard."""
    palette = axis_colors.derive_all()
    palette["+x+y"] = POLES["+y"]
    with pytest.raises(ValueError, match="collides"):
        axis_colors.verify_palette(palette)


def test_the_verifier_refuses_two_seats_with_one_colour():
    palette = axis_colors.derive_all()
    palette["+x+y"] = palette["+x+z"]
    with pytest.raises(ValueError, match="apart"):
        axis_colors.verify_palette(palette)


@pytest.mark.parametrize(("token", "expected"), [
    ("+x", "#F97316"),        # the pole itself
    ("+x+y", "#E5B16A"),      # orange + yellow, thinned
    ("-x+y", "#AAB6B0"),      # the collision case: blue + yellow, thinned
    ("+x+y+z", "#6B6623"),    # orange + yellow + green, deepened
    ("-x-y-z", "#613D77"),
])
def test_golden_colours(token, expected):
    """The exact hex the formula produces. Both languages round the same way
    (Math.round, matched by jsmath.round_half_up), so these are also what the
    web core reports for the same part."""
    from preview3d.directions import tier_of
    assert axis_colors.color_for(token, tier_of(token)) == expected


def test_neither_source_restates_a_derived_colour():
    """The formula is the source; a hardcoded result would be a second one."""
    palette = set(axis_colors.derive_all().values())
    for source in (ROOT / "src" / "axiscolors.js", ROOT / "preview3d" / "axis_colors.py",
                   ROOT / "src" / "cubemodel.js", ROOT / "preview3d" / "cube_model.py"):
        text = source.read_text(encoding="utf-8")
        restated = [color for color in palette if color in text]
        assert not restated, f"{source.name} hardcodes {restated} instead of computing it"
