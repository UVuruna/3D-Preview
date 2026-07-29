"""Snap views and the twenty-four orientations.

Two M2 features that both come down to "point something at an exact direction":

- **Snap views** — the seven presets cannot express the four body diagonals a
  cube is actually read along, so a model's view carries a DIRECTION and the
  camera snaps to it.
- **The orientation table** — a cube can be set down in exactly 24 ways, and
  they are computed from 6 up-faces times 4 spins rather than stored as 24
  matrices (root Rule 19). PLAN.md's Scene 4 (the 24-orientations clock) is
  blocked on DOMY's rotation-to-hour rule; the ENGINE feature ships now, so
  when that rule lands the clock is a data drop.

The thing that would silently go wrong is a REFLECTION passing for a rotation:
the cube would come back mirrored and a screenshot would look perfectly fine.
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from preview3d.directions import parse_direction  # noqa: E402
from preview3d.orientations import (  # noqa: E402
    SPINS, is_rotation, orientation, orientation_axes, orientation_ids,
    snap_angles, step_orientation,
)
from preview3d.vectors import IDENTITY  # noqa: E402


def test_there_are_exactly_twenty_four():
    ids = orientation_ids()
    assert len(ids) == 24 == len(set(ids))


def test_the_first_one_is_upright():
    """So a freshly shown model starts unrotated without anyone saying so."""
    assert orientation_ids()[0] == "+x:0"
    assert orientation("+y:0") == IDENTITY


def test_every_orientation_is_a_true_rotation():
    """Not a reflection. A mirrored cube looks entirely plausible in a still."""
    for identifier in orientation_ids():
        assert is_rotation(orientation(identifier)), identifier


def test_all_twenty_four_are_distinct():
    seen = {tuple(round(c, 9) for row in orientation(i) for c in row) for i in orientation_ids()}
    assert len(seen) == 24


def test_the_named_face_really_ends_up_where_it_says():
    """`<face>:<spin>` takes the cube's own +Y onto that world direction."""
    for identifier in orientation_ids():
        face = identifier.split(":")[0]
        _, up, _ = orientation_axes(identifier)
        assert up == pytest.approx(parse_direction(face), abs=1e-12), identifier


def test_the_spins_are_quarter_turns_about_that_face():
    """Four spins bring the cube back to where it started, and no fewer do."""
    for face in ("+x", "-y", "+z"):
        axes = [orientation_axes(f"{face}:{spin}")[0] for spin in range(SPINS)]
        for i in range(SPINS):
            following = axes[(i + 1) % SPINS]
            assert sum(a * b for a, b in zip(axes[i], following)) == pytest.approx(0, abs=1e-12)
        assert axes[0] == pytest.approx(
            [-c for c in axes[2]], abs=1e-12)      # half a turn is the antipode


def test_stepping_walks_the_whole_table_and_wraps():
    ids = orientation_ids()
    walked = []
    current = ids[0]
    for _ in range(24):
        walked.append(current)
        current = step_orientation(current, 1)
    assert walked == ids
    assert current == ids[0]
    assert step_orientation("", 1) == ids[0]
    assert step_orientation("", -1) == ids[-1]


@pytest.mark.parametrize("bad", ["+y", "+y:4", "+q:0", "+y:x", ""])
def test_an_unknown_orientation_fails_loudly(bad):
    with pytest.raises(ValueError):
        orientation(bad)


# ---- Snap views -------------------------------------------------------------


def test_snapping_down_a_body_diagonal_is_the_isometric_view():
    """The one direction whose cube silhouette is a regular hexagon."""
    azimuth, elevation = snap_angles("+x+y+z")
    assert azimuth == pytest.approx(45.0, abs=1e-12)
    assert elevation == pytest.approx(math.degrees(math.asin(1 / math.sqrt(3))), abs=1e-12)


def test_the_tertiary_view_stands_perpendicular_to_the_sacred_axis():
    """Looking DOWN an axis collapses it to a point, so the view that is about
    the diagonals must stand across the one that matters."""
    camera = parse_direction("-x+y")
    sacred = parse_direction("+x+y+z")
    assert sum(a * b for a, b in zip(camera, sacred)) == pytest.approx(0, abs=1e-12)
    assert snap_angles("-x+y") == pytest.approx((-90.0, 45.0), abs=1e-12)


def test_snapping_straight_up_stops_short_of_the_pole():
    """At the pole the azimuth is undefined and the orbit flips; the camera's
    own clamp is the value snapping must respect."""
    _, elevation = snap_angles("+y")
    assert elevation == pytest.approx(89.99)
    assert snap_angles("-y")[1] == pytest.approx(-89.99)


def test_snapping_takes_a_vector_as_readily_as_a_token():
    assert snap_angles([1, 1, 1]) == pytest.approx(snap_angles("+x+y+z"))
