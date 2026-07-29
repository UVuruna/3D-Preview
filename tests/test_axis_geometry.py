"""ANGLE EXACTNESS — the cube's thirteen axes at their TRUE directions.

The whole reason this component exists is that a flat wheel cannot show an edge
axis at its real angle (PLAN.md, The Four Owner Models). An axis drawn at an
approximated angle would look plausible and teach the wrong thing, so every
direction's dot products are pinned here rather than eyeballed.

Before this, the direction table was six hardcoded entries in each renderer and
the six edge axes and four vertex diagonals could not be expressed at all.

Run: python -m pytest tests/
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from preview3d.directions import (  # noqa: E402
    canonical_token, cube_axes, cube_tokens, hidden_from, opposite_token,
    parse_direction, tier_of, token_of, token_vector, vertex_neighbors,
)
from preview3d.light.camera import Camera  # noqa: E402
from preview3d.light.primitives import arm_name, build_axes, build_primitive  # noqa: E402
from preview3d.light.renderer import NEAR_CULL, _face_item  # noqa: E402
from preview3d.light.scene import Node, collect_parts  # noqa: E402

ROOT_HALF = 1 / math.sqrt(2)      # a two-letter direction's share of each parent
ROOT_THIRD = 1 / math.sqrt(3)     # a three-letter direction's share of each parent
EXACT = 1e-12


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


# ---- The grammar ------------------------------------------------------------


def test_the_cube_has_three_six_and_four_axes():
    """3 face axes, 6 edge axes, 4 vertex diagonals — 13, computed not listed."""
    assert [len(cube_axes(n)) for n in (1, 2, 3)] == [3, 6, 4]
    assert [len(cube_tokens(n)) for n in (1, 2, 3)] == [6, 12, 8]


def test_tiers_follow_the_letter_count():
    assert tier_of("+x") == "primary"
    assert tier_of("+x-y") == "secondary"
    assert tier_of("-x+y-z") == "tertiary"


def test_a_token_names_one_direction_only():
    """'+y+x' and '+x+y' are one direction, so they must be one NAME — otherwise
    the same arm is addressable by two different paths."""
    assert canonical_token("+y+x") == "+x+y"
    assert canonical_token("+z-x") == "-x+z"
    assert parse_direction("+y+x") == parse_direction("+x+y")


def test_every_direction_round_trips_through_its_token():
    for letters in (1, 2, 3):
        for token in cube_tokens(letters):
            assert token_of(parse_direction(token)) == token


def test_opposite_is_the_exact_antipode():
    for letters in (1, 2, 3):
        for token in cube_tokens(letters):
            assert dot(parse_direction(token), parse_direction(opposite_token(token))) == pytest.approx(-1, abs=EXACT)


@pytest.mark.parametrize("bad", ["", "x", "+q", "+x+x", "++x", "+xy", "3"])
def test_a_malformed_token_fails_loudly(bad):
    """A typo must never resolve to some other direction (root Rule 1)."""
    with pytest.raises(ValueError):
        parse_direction(bad)


def test_a_zero_vector_is_not_a_direction():
    with pytest.raises(ValueError):
        parse_direction([0, 0, 0])


# ---- Angle exactness --------------------------------------------------------


def test_primary_axes_are_exactly_orthogonal():
    for a in cube_tokens(1):
        for b in cube_tokens(1):
            if a == b or b == opposite_token(a):
                continue
            assert dot(parse_direction(a), parse_direction(b)) == pytest.approx(0, abs=EXACT)


def test_secondary_axes_sit_exactly_on_the_edge_midpoints():
    """An edge direction makes 45 degrees with each of its two parent poles and
    exactly 90 with the third — that IS the midpoint of the cube's edge."""
    for token in cube_tokens(2):
        direction = parse_direction(token)
        parents = [("+" if sign > 0 else "-") + letter for letter, sign in _letters(token)]
        for parent in parents:
            assert dot(direction, parse_direction(parent)) == pytest.approx(ROOT_HALF, abs=EXACT)
        third = next(t for t in "xyz" if t not in token)
        assert dot(direction, parse_direction("+" + third)) == pytest.approx(0, abs=EXACT)
        assert len(direction) == 3 and dot(direction, direction) == pytest.approx(1, abs=EXACT)


def test_tertiary_axes_sit_exactly_on_the_vertex_diagonals():
    """A body diagonal makes the same angle — acos(1/sqrt 3) — with all three of
    its poles. Nothing else does, which is why the hexagram appears down it."""
    for token in cube_tokens(3):
        direction = parse_direction(token)
        for letter, sign in _letters(token):
            pole = ("+" if sign > 0 else "-") + letter
            assert dot(direction, parse_direction(pole)) == pytest.approx(ROOT_THIRD, abs=EXACT)
        assert dot(direction, direction) == pytest.approx(1, abs=EXACT)


def test_the_angle_between_a_diagonal_and_an_edge_it_contains():
    """A body diagonal and an edge direction sharing two letters are 2/sqrt(6)
    apart — the value a flat wheel has no way to draw."""
    assert dot(parse_direction("+x+y+z"), parse_direction("+x+y")) == pytest.approx(
        2 / math.sqrt(6), abs=EXACT)


def test_adjacent_edge_axes_are_sixty_degrees_apart():
    assert dot(parse_direction("+x+y"), parse_direction("+x+z")) == pytest.approx(0.5, abs=EXACT)


def test_a_seat_sits_where_its_axis_end_points():
    """A seat's position is its token vector times half the cube, so the '+x+y'
    seat IS the midpoint of that edge and the '+x' seat IS the face centre."""
    assert token_vector("+x") == (1.0, 0.0, 0.0)
    assert token_vector("+x+y") == (1.0, 1.0, 0.0)
    assert token_vector("-x+y-z") == (-1.0, 1.0, -1.0)


# ---- Hexagram and Blindness geometry (M3) -----------------------------------


@pytest.mark.parametrize("vertex", cube_tokens(3))
def test_vertex_neighbors_are_exactly_one_flip_away(vertex):
    """Each of the three neighbours shares two of the vertex's own letters and
    flips the third — the definition of a cube EDGE, not an approximation of it."""
    neighbors = vertex_neighbors(vertex)
    assert len(neighbors) == 3
    assert len(set(neighbors)) == 3        # no vertex is its own neighbour twice
    assert vertex not in neighbors
    vertex_signed = dict(_letters(vertex))
    for neighbor in neighbors:
        neighbor_signed = dict(_letters(neighbor))
        flipped = [letter for letter in vertex_signed if neighbor_signed[letter] != vertex_signed[letter]]
        assert len(flipped) == 1, f"{neighbor} is not one flip away from {vertex}"


def test_the_two_triangles_are_the_equatorial_ring_split_in_half():
    """The Hexagram's two triangles: a pole's own three neighbours, plus the
    antipode's own three neighbours, are together exactly the six vertices that
    are NEITHER pole — the equatorial ring a body diagonal's silhouette hexagon
    is drawn from, split into the two triangles the builder draws."""
    pole, antipode = "+x+y+z", "-x-y-z"
    up = set(vertex_neighbors(pole))
    down = set(vertex_neighbors(antipode))
    assert up.isdisjoint(down)
    ring = set(cube_tokens(3)) - {pole, antipode}
    assert up | down == ring
    assert {opposite_token(token) for token in up} == down


@pytest.mark.parametrize("vertex", cube_tokens(3))
def test_hidden_from_is_the_antipodes_own_seven_cells(vertex):
    """26 - 7 = 19 visible — the Blindness law, pinned as a count and as a set."""
    hidden = hidden_from(vertex)
    assert len(hidden) == 7
    assert len(set(hidden)) == 7
    antipode = opposite_token(vertex)
    assert antipode in hidden
    antipode_letters = set(letter for letter, _ in _letters(antipode))
    for token in hidden:
        token_letters_signed = dict(_letters(token))
        # Every hidden cell agrees with the antipode on every letter it carries.
        assert set(token_letters_signed) <= antipode_letters
        for letter, sign in token_letters_signed.items():
            assert dict(_letters(antipode))[letter] == sign


def test_hidden_from_and_visible_from_together_are_all_26_cells():
    hidden = set(hidden_from("+x+y+z"))
    all_cells = set(cube_tokens(1)) | set(cube_tokens(2)) | set(cube_tokens(3))
    visible = all_cells - hidden
    assert len(hidden) == 7
    assert len(visible) == 19
    assert "+x+y+z" in visible          # a vertex is never blind to itself


# ---- The arms that get built from them --------------------------------------


def test_an_arm_can_be_given_a_raw_vector():
    """A host is never forced into the cube's vocabulary."""
    node = build_axes({"arms": [{"axis": [2, 0, 0], "color": "#FFFFFF", "name": "arm:east"}]})
    assert [child.name for child in node.children] == ["joint", "arm:east"]


def test_an_arm_off_the_poles_must_bring_its_own_colour():
    """There is no pole hue to inherit for an edge direction, and silently
    picking one would be a made-up colour nobody chose (Rule 1)."""
    with pytest.raises(ValueError, match="no colour"):
        build_axes({"arms": [{"axis": "+x+y"}]})


def test_arm_names_are_canonical():
    assert arm_name({"axis": "+y+x"}, 0) == "arm:+x+y"
    assert arm_name({"axis": [1, 1, 0]}, 3) == "arm:3"
    assert arm_name({"axis": "+x", "name": "arm:east"}, 0) == "arm:east"


def test_the_joint_can_be_turned_off():
    """Thirteen axes drawn as thirteen gizmos would stack thirteen joints."""
    paths = [p["path"] for p in _parts(build_axes({"joint": False, "arms": [{"axis": "+x"}]}))]
    assert "joint" not in paths


# ---- Golden projections -----------------------------------------------------


def _iso_camera() -> Camera:
    """Orthographic, looking straight down the +x+y+z body diagonal."""
    return Camera(
        target=(0.0, 0.0, 0.0), distance=4.0, azimuth=45.0,
        elevation=math.degrees(math.asin(1 / math.sqrt(3))),
        projection="orthographic", ortho_height=4.0, aspect=1.0,
    )


def _screen_angle(point) -> float:
    """Bearing of a projected point from the centre of a 600x600 view, degrees
    anticlockwise from screen right."""
    x, y, _ = _iso_camera().project(point, 600, 600)
    return math.degrees(math.atan2(-(y - 300), x - 300)) % 360


def test_the_six_primary_arms_project_thirty_degrees_apart():
    """Down the body diagonal the three face axes become the hexagram's six
    spokes, exactly 60 degrees apart in pairs — the claim the whole Hexagram
    X-ray rests on, pinned as a number rather than admired in a screenshot."""
    angles = {token: _screen_angle(parse_direction(token)) for token in cube_tokens(1)}
    assert angles["+y"] == pytest.approx(90.0, abs=1e-9)
    assert angles["-z"] == pytest.approx(30.0, abs=1e-9)
    assert angles["+x"] == pytest.approx(330.0, abs=1e-9)
    assert angles["-y"] == pytest.approx(270.0, abs=1e-9)
    assert angles["+z"] == pytest.approx(210.0, abs=1e-9)
    assert angles["-x"] == pytest.approx(150.0, abs=1e-9)


def test_the_six_primary_arms_project_at_one_radius():
    camera = _iso_camera()
    radii = [
        math.hypot(*(camera.project(parse_direction(t), 600, 600)[:2][i] - 300 for i in (0, 1)))
        for t in cube_tokens(1)
    ]
    assert all(radius == pytest.approx(radii[0], abs=1e-9) for radius in radii)


def test_the_sacred_diagonal_projects_to_the_exact_centre():
    """Looking down an axis, that axis is a point — which is why the tertiary
    view stands PERPENDICULAR to it instead."""
    x, y, _ = _iso_camera().project(parse_direction("+x+y+z"), 600, 600)
    assert (x, y) == pytest.approx((300.0, 300.0), abs=1e-9)


@pytest.mark.parametrize(("token", "expected"), [
    ("+x", (406.0660171779821, 361.2372435695795)),
    ("+y", (300.0, 177.52551286084117)),
    ("+x+y", (375.0, 256.69872981077805)),
    ("+x-y", (375.0, 429.9038105676658)),
    ("+x+y-z", (422.47448713915885, 229.2893218813452)),
    ("-x+y+z", (177.52551286084115, 229.2893218813452)),
])
def test_golden_projections(token, expected):
    """Known camera plus known direction to an exact screen point — the pin that
    keeps the projection maths honest forever (PLAN.md, Testing)."""
    x, y, _ = _iso_camera().project(parse_direction(token), 600, 600)
    assert (x, y) == pytest.approx(expected, abs=1e-9)


def _letters(token):
    from preview3d.directions import token_letters
    return token_letters(token)


def _parts(node):
    root = Node(name="content")
    root.add(node)
    return collect_parts(root)


# ---- The hexagram primitive (M3) ---------------------------------------------


def test_hexagram_triangle_corners_are_the_true_cube_vertices():
    """A triangle corner is a token's UN-normalised vector times half the cube
    — same rule as a model's cells — never an approximation of it."""
    node = build_primitive({"type": "hexagram", "diagonal": "+x+y+z", "size": 2.0})
    parts = {p["path"]: p for p in _parts(node)}
    assert set(parts) == {"hexagram", "hexagram/triangle:up", "hexagram/triangle:down"}
    up = next(child for child in node.children if child.name == "triangle:up")
    corners = {point for segment in up.segments for point in (segment.start, segment.end)}
    expected = {tuple(component * 1.0 for component in token_vector(v)) for v in vertex_neighbors("+x+y+z")}
    assert corners == expected


def test_hexagram_requires_a_diagonal():
    with pytest.raises(ValueError, match="diagonal"):
        build_primitive({"type": "hexagram"})


def test_hexagram_defaults_to_the_sacred_and_neutral_colours():
    """Never invented per-scene: the builder's own defaults reuse two colours
    shared/spec.json already declares (axisColors.sacred, neutral.joint)."""
    from preview3d.axis_colors import SACRED
    from preview3d.resources import load_shared_spec

    node = build_primitive({"type": "hexagram", "diagonal": "+x+y+z"})
    up = next(child for child in node.children if child.name == "triangle:up")
    down = next(child for child in node.children if child.name == "triangle:down")
    assert up.segments[0].color == SACRED
    assert down.segments[0].color == load_shared_spec()["neutral"]["joint"]


def test_an_axis_stops_bead_is_the_same_node_as_its_labels():
    """A bead-bearing stop must be ONE addressable part (a `part.position` track
    slides the whole thing) — never a separate 'bead' child the two renderers
    could disagree about having."""
    node = build_axes({"arms": [{
        "axis": "+x", "stops": [{"name": "luminous", "anchor": [0.5, 0, 0], "labels": {"canon": "x"}}],
    }]})
    arm = next(child for child in node.children if child.name == "arm:+x")
    stop = next(child for child in arm.children if child.name == "luminous")
    assert stop.faces, "an axis stop must carry its own bead geometry"
    assert stop.position == pytest.approx((0.5, 0.0, 0.0))
    assert [child.name for child in stop.children] == ["label:canon"]


def test_a_cell_stops_position_carries_its_anchor_without_a_bead():
    """A cell's own marker already has a body sphere; its stops stay text-only,
    positioned the same way (Node.position, not a per-label offset)."""
    from preview3d.light.primitives import build_marker

    node = build_marker({
        "position": [1.0, 2.0, 3.0],
        "stops": [{"name": "luminous", "anchor": [0, 0.1, 0], "labels": {"canon": "x"}}],
    })
    stop = next(child for child in node.children if child.name == "luminous")
    assert not stop.faces, "a cell's stop must stay text-only — the seat itself is the bead"
    assert stop.position == pytest.approx((0.0, 0.1, 0.0))


# ---- Near-culling (M3) --------------------------------------------------------


def _straddling_camera() -> Camera:
    """A camera close enough that a unit-ish face straddles its own near plane
    — the exact situation the Blindness view's first-person dolly creates."""
    return Camera(target=(0.0, 0.0, 0.0), distance=0.3, azimuth=0.0, elevation=0.0,
                  projection="perspective", aspect=1.0)


def test_a_face_straddling_the_near_plane_is_culled_whole():
    """Before the guard, a face with one vertex behind the eye projected to a
    mirrored, garbled polygon rather than vanishing — the defect PLAN.md's
    'inside-the-scene mode with near-culling' exists to close."""
    camera = _straddling_camera()
    # A face spanning from just in front of the eye to well behind it.
    points = [(-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (0.5, 0.5, 1.0), (-0.5, 0.5, 1.0)]
    assert _face_item(points, camera, 600, 600, "#FFFFFF", 1.0, camera.position) is None


def test_a_face_entirely_in_front_still_draws():
    """The guard must not cull ordinary, comfortably-framed geometry."""
    camera = Camera(target=(0.0, 0.0, 0.0), distance=4.0, azimuth=0.0, elevation=0.0, aspect=1.0)
    points = [(-0.5, -0.5, 0.0), (0.5, -0.5, 0.0), (0.5, 0.5, 0.0), (-0.5, 0.5, 0.0)]
    item = _face_item(points, camera, 600, 600, "#FFFFFF", 1.0, camera.position)
    assert item is not None


def test_near_cull_threshold_is_a_small_positive_depth():
    assert 0 < NEAR_CULL < 0.01
