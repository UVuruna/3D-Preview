"""Orbit camera and projection for the LIGHT renderer.

Pure Python — no Qt. Angles and framing follow the same rules as the web core
(src/viewer.md), including the silhouette fit, so the same spec lands at the
same camera in both renderers.
"""

import math
from dataclasses import dataclass, field

from ..resources import load_shared_spec
from .vectors import Vec3, add, basis_from, dot, scale, sub

_SPEC = load_shared_spec()
VIEWS: dict[str, dict] = _SPEC["views"]
VIEW_ORDER: list[str] = _SPEC["viewOrder"]
CAMERA_DEFAULTS: dict = _SPEC["camera"]

FREE_VIEW = "free"
PERSPECTIVE = "perspective"
ORTHOGRAPHIC = "orthographic"
_POLE_LIMIT = 89.99      # stops the orbit flipping over the poles
_MIN_DISTANCE = 1e-3


def view_direction(name: str) -> Vec3:
    preset = VIEWS.get(name)
    if preset is None:
        raise ValueError(f"Unknown view {name!r} — available: {', '.join(VIEW_ORDER)}")
    return tuple(float(v) for v in preset["direction"])


def step_view(current: str, step: int) -> str:
    """Next preset in cycle order; from a free view, land on an end."""
    if current not in VIEW_ORDER:
        return VIEW_ORDER[0 if step > 0 else -1]
    return VIEW_ORDER[(VIEW_ORDER.index(current) + step) % len(VIEW_ORDER)]


@dataclass
class Camera:
    target: Vec3 = (0.0, 0.0, 0.0)
    distance: float = 4.0
    azimuth: float = 45.0            # degrees, atan2(x, z) of the eye offset
    elevation: float = 35.264        # degrees above the horizon
    projection: str = PERSPECTIVE
    fov: float = field(default_factory=lambda: float(CAMERA_DEFAULTS["fov"]))
    ortho_height: float = 2.0        # world height the viewport spans
    aspect: float = 1.0

    # ---- Placement ---------------------------------------------------------

    @property
    def position(self) -> Vec3:
        azimuth = math.radians(self.azimuth)
        elevation = math.radians(self.elevation)
        horizontal = math.cos(elevation) * self.distance
        return add(self.target, (
            horizontal * math.sin(azimuth),
            math.sin(elevation) * self.distance,
            horizontal * math.cos(azimuth),
        ))

    def basis(self) -> tuple[Vec3, Vec3, Vec3]:
        """(forward, right, up); forward points from the target toward the eye."""
        return basis_from(sub(self.position, self.target))

    def look_along(self, direction: Vec3) -> None:
        """Point the camera down `direction` without changing the distance."""
        x, y, z = direction
        horizontal = math.hypot(x, z)
        self.azimuth = math.degrees(math.atan2(x, z)) if horizontal else self.azimuth
        self.elevation = math.degrees(math.atan2(y, horizontal)) if horizontal else (
            _POLE_LIMIT if y > 0 else -_POLE_LIMIT
        )
        self.elevation = max(-_POLE_LIMIT, min(_POLE_LIMIT, self.elevation))

    # ---- Movement ----------------------------------------------------------

    def orbit_by(self, d_azimuth: float, d_elevation: float) -> None:
        self.azimuth = (self.azimuth + d_azimuth) % 360.0
        self.elevation = max(-_POLE_LIMIT, min(_POLE_LIMIT, self.elevation + d_elevation))

    def pan_by(self, dx: float, dy: float) -> None:
        """Steps are fractions of the visible height, so panning feels the same at any zoom."""
        height = self.visible_height()
        _, right, up = self.basis()
        self.target = add(self.target, add(
            scale(right, dx * height * self.aspect), scale(up, dy * height)))

    def zoom_by(self, factor: float) -> None:
        if self.projection == ORTHOGRAPHIC:
            self.ortho_height = max(self.ortho_height / factor, _MIN_DISTANCE)
        else:
            self.distance = max(self.distance / factor, _MIN_DISTANCE)

    def set_projection(self, kind: str) -> None:
        """Swap projection while keeping the content the same size on screen."""
        if kind not in (PERSPECTIVE, ORTHOGRAPHIC):
            raise ValueError(f"Unknown projection {kind!r} — expected {PERSPECTIVE} or {ORTHOGRAPHIC}")
        if kind == self.projection:
            return
        height = self.visible_height()
        self.projection = kind
        if kind == ORTHOGRAPHIC:
            self.ortho_height = height
        else:
            # Perspective has no zoom knob: apparent size IS distance.
            self.distance = height / (2 * math.tan(math.radians(self.fov / 2)))

    def visible_height(self) -> float:
        """World height the viewport spans at the target."""
        return self.visible_height_at(self.distance)

    def visible_height_at(self, depth: float) -> float:
        """World height the viewport spans at `depth` in front of the eye.

        Orthographic has no foreshortening, so the height is the same
        everywhere — which is why a label keeps its size as it recedes.
        """
        if self.projection == ORTHOGRAPHIC:
            return self.ortho_height
        return 2 * math.tan(math.radians(self.fov / 2)) * depth

    # ---- Framing -----------------------------------------------------------

    def fit(self, points, direction: Vec3 | None = None, margin: float | None = None) -> None:
        """Frame `points` (an iterable of world Vec3) as seen from `direction`.

        Same rule as the web core: measure the real silhouette, then require, per
        point, `depth + offset / tan(fov/2)` — not the aggregate half-extent
        formula, which assumes the widest point is also the nearest and wastes
        about a third of the frame on anything viewed corner-on.
        """
        if direction is None:
            direction = sub(self.position, self.target)
        margin = float(CAMERA_DEFAULTS["fitMargin"]) if margin is None else margin
        forward, right, up = basis_from(direction)

        projected = [(dot(p, right), dot(p, up), dot(p, forward)) for p in points]
        if not projected:
            return

        xs = [p[0] for p in projected]
        ys = [p[1] for p in projected]
        zs = [p[2] for p in projected]
        centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)

        tan_y = math.tan(math.radians(self.fov / 2))
        tan_x = tan_y * self.aspect
        distance = 0.0
        for x, y, z in projected:
            need = (z - centre[2]) + max(abs(y - centre[1]) / tan_y,
                                         abs(x - centre[0]) / tan_x) * margin
            distance = max(distance, need)

        self.target = add(add(scale(right, centre[0]), scale(up, centre[1])),
                          scale(forward, centre[2]))
        self.distance = max(distance, _MIN_DISTANCE)
        self.look_along(direction)
        if self.projection == ORTHOGRAPHIC:
            half_height = (max(ys) - min(ys)) / 2
            half_width = (max(xs) - min(xs)) / 2
            self.ortho_height = 2 * max(half_height, half_width / self.aspect) * margin

    # ---- Projection --------------------------------------------------------

    def project(self, point: Vec3, width: int, height: int) -> tuple[float, float, float]:
        """World point → (screen x, screen y, depth in front of the eye)."""
        forward, right, up = self.basis()
        eye = self.position
        local = sub(point, eye)
        depth = -dot(local, forward)
        x, y = dot(local, right), dot(local, up)

        if self.projection == ORTHOGRAPHIC:
            half_height = self.ortho_height / 2
            ndc_x = x / (half_height * self.aspect)
            ndc_y = y / half_height
        else:
            safe = depth if abs(depth) > 1e-6 else 1e-6
            tan_y = math.tan(math.radians(self.fov / 2))
            ndc_x = x / (safe * tan_y * self.aspect)
            ndc_y = y / (safe * tan_y)

        return ((ndc_x + 1) * 0.5 * width, (1 - ndc_y) * 0.5 * height, depth)

    def state(self) -> dict:
        return {
            "azimuth": ((self.azimuth + 180) % 360) - 180,
            "elevation": self.elevation,
            "distance": self.distance,
            "projection": self.projection,
        }
