"""Minimal 3-vector helpers.

Deliberately plain tuples and functions rather than numpy: the LIGHT renderer
exists to keep consumers free of heavy dependencies, and the scenes it draws are
a few hundred polygons — far below the point where vectorisation would pay.
"""

import math

Vec3 = tuple[float, float, float]

ORIGIN: Vec3 = (0.0, 0.0, 0.0)
UP: Vec3 = (0.0, 1.0, 0.0)
FORWARD: Vec3 = (0.0, 0.0, 1.0)


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(a: Vec3, k: float) -> Vec3:
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length(a: Vec3) -> float:
    return math.sqrt(dot(a, a))


def normalize(a: Vec3) -> Vec3:
    n = length(a)
    if n == 0.0:
        raise ValueError("cannot normalize a zero-length vector")
    return (a[0] / n, a[1] / n, a[2] / n)


def basis_from(direction: Vec3) -> tuple[Vec3, Vec3, Vec3]:
    """Orthonormal (forward, right, up) for a view direction.

    `forward` points from the content toward the camera. World +Z stands in for
    world up when the direction IS world up, which is the straight top/bottom
    view — otherwise the cross product collapses.
    """
    forward = normalize(direction)
    reference = FORWARD if abs(forward[1]) > 0.999 else UP
    right = normalize(cross(reference, forward))
    up = cross(forward, right)
    return forward, right, up


def rotate_towards(source: Vec3, target: Vec3, point: Vec3) -> Vec3:
    """Apply the rotation taking unit `source` onto unit `target` to `point`.

    Rodrigues' formula. Used to orient a primitive built along +Y onto an
    arbitrary axis, matching how the web renderer orients the same shape with a
    quaternion — the two must agree or the same spec would draw differently.
    """
    axis = cross(source, target)
    sin_a = length(axis)
    cos_a = dot(source, target)
    if sin_a < 1e-9:
        return point if cos_a > 0 else scale(point, -1.0)
    axis = scale(axis, 1.0 / sin_a)
    return add(
        add(scale(point, cos_a), scale(cross(axis, point), sin_a)),
        scale(axis, dot(axis, point) * (1.0 - cos_a)),
    )
