"""The cube's twenty-four orientations, COMPUTED.

A cube can be set down in exactly 24 ways, and they are the product of two
choices, not a table of 24 matrices to copy: pick which face points up (6), then
how far it is spun about that direction (4). Root Rule 19 in its plainest form —
define how the piece moves and every position follows.

Each orientation is named `<face>:<spin>`, e.g. `+y:0` (the identity) or
`-z:2`. The order they enumerate in is the shared face order followed by spins
0..3, so a "next orientation" step means the same thing in both renderers.

Also here: `snap_angles`, which turns any direction into the azimuth/elevation a
camera must stand at to look down it — the snap views, including the four body
diagonals no preset covers.

Pure Python. The JS mirror is src/orientations.js.
"""

import math

from .directions import parse_direction
from .resources import load_shared_spec
from .vectors import FORWARD, Mat3, UP, Vec3, basis_matrix, cross, normalize

_SPEC = load_shared_spec()
FACE_ORDER: list[str] = _SPEC["faceOrder"]
SPINS = 4
_POLE_LIMIT = 89.99      # the camera's own clamp; snapping must not exceed it


def orientation_ids() -> list[str]:
    """All 24 ids, in the order a stepped auto-advance walks them."""
    return [f"{face}:{spin}" for face in FACE_ORDER for spin in range(SPINS)]


def orientation(identifier: str) -> Mat3:
    """The rotation named by `<face>:<spin>`.

    It takes the cube's own +Y onto the world direction `face`, then spins by
    `spin` quarter turns about that direction. `+y:0` is the identity, so a
    freshly shown model starts unrotated without anyone saying so.
    """
    face, _, spin_text = identifier.partition(":")
    if not spin_text.isdigit() or not 0 <= int(spin_text) < SPINS:
        raise ValueError(
            f"Unknown orientation {identifier!r} — expected '<face>:<spin>' with "
            f"face in {', '.join(FACE_ORDER)} and spin 0..{SPINS - 1}"
        )
    if face not in FACE_ORDER:
        raise ValueError(
            f"Unknown orientation {identifier!r} — face must be one of {', '.join(FACE_ORDER)}"
        )

    up = parse_direction(face)
    # The same degenerate-case rule the cameras use, so "which way is spin 0"
    # is one decision in this component rather than two.
    reference = FORWARD if abs(up[1]) > 0.999 else UP
    right0 = normalize(cross(up, reference))
    forward0 = cross(right0, up)

    angle = math.radians(90 * int(spin_text))
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    # Rodrigues about `up`, where the (up . right0) term vanishes because the
    # two are orthogonal by construction.
    right = _combine(right0, cross(up, right0), cos_a, sin_a)
    forward = cross(right, up)
    return basis_matrix(right, up, forward)


def _combine(a: Vec3, b: Vec3, wa: float, wb: float) -> Vec3:
    return (a[0] * wa + b[0] * wb, a[1] * wa + b[1] * wb, a[2] * wa + b[2] * wb)


def step_orientation(identifier: str, step: int) -> str:
    """The next (or previous) orientation in the enumeration order."""
    ids = orientation_ids()
    if identifier not in ids:
        return ids[0 if step > 0 else -1]
    return ids[(ids.index(identifier) + step) % len(ids)]


def snap_angles(direction) -> tuple[float, float]:
    """(azimuth, elevation) in degrees for a camera looking DOWN `direction`.

    `direction` points from the content toward the camera, matching the view
    presets. A token works as well as a vector, so `snap_angles('+x+y+z')` is
    the body-diagonal view the hexagram lives on.
    """
    x, y, z = parse_direction(direction)
    horizontal = math.hypot(x, z)
    azimuth = math.degrees(math.atan2(x, z)) if horizontal else 0.0
    elevation = math.degrees(math.atan2(y, horizontal)) if horizontal else (
        _POLE_LIMIT if y > 0 else -_POLE_LIMIT
    )
    return azimuth, max(-_POLE_LIMIT, min(_POLE_LIMIT, elevation))


def orientation_axes(identifier: str) -> tuple[Vec3, Vec3, Vec3]:
    """Where the cube's own +X, +Y and +Z end up under this orientation.

    The columns of the matrix, spelled out — what a test asserts against and
    what a caption would read from.
    """
    matrix = orientation(identifier)
    return (
        (matrix[0][0], matrix[1][0], matrix[2][0]),
        (matrix[0][1], matrix[1][1], matrix[2][1]),
        (matrix[0][2], matrix[1][2], matrix[2][2]),
    )


def is_rotation(matrix: Mat3) -> bool:
    """True when the matrix is a true rotation — orthonormal, determinant +1.

    A reflection would look plausible in a screenshot and be wrong: the cube
    would come back mirrored. Pinned by the tests rather than trusted.
    """
    columns = [
        (matrix[0][i], matrix[1][i], matrix[2][i]) for i in range(3)
    ]
    for i, column in enumerate(columns):
        if abs(sum(component * component for component in column) - 1.0) > 1e-9:
            return False
        for other in columns[i + 1:]:
            if abs(sum(column[k] * other[k] for k in range(3))) > 1e-9:
                return False
    determinant = sum(
        columns[0][k] * cross(columns[1], columns[2])[k] for k in range(3)
    )
    return abs(determinant - 1.0) < 1e-9


__all__ = [
    "FACE_ORDER", "SPINS", "orientation", "orientation_ids", "orientation_axes",
    "step_orientation", "snap_angles", "is_rotation",
]
