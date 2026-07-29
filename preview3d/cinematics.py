"""Cinematic scene GENERATORS — a master rule for a whole family of scenes,
never one hand-authored descriptor per case (root Rule 19).

The Five Stations (PLAN.md, Extra 3D Views) "generalizes to any axis on
demand" — the cube has 13 of them, and hand-authoring 13 near-identical JSON
descriptors would be exactly the enumeration root Rule 19 forbids. This module
computes the scene descriptor for ANY axis of a model instead: the geometry
(vertex positions, the side-on camera angle, which OTHER parts to fade) is all
derived from the model's own data, so a new axis is a function argument, not a
new file.

Pure Python; the JS mirror is src/cinematics.js. Both read shared/spec.json for
the radial factors and switcher stop names, so neither restates them.
"""

from .directions import canonical_token, opposite_token, parse_direction
from .light.camera import Camera
from .model_scene import GROUP_PATHS, KIND_ORDER, TIER_ORDER
from .resources import load_shared_spec
from .vectors import basis_from, scale

_SPEC = load_shared_spec()
_TIERS: dict = _SPEC["axisTiers"]
_RADIAL: dict = _SPEC["switcher"]["radial"]
STOPS: list[str] = list(_SPEC["switcher"]["stops"])

FADE_END = 0.35     # the cube is gone by here
SLIDE_END = 0.75     # the beads have reached their stations by here
EASE = "ease-in-out"

# A gentle three-quarter opening pose — any axis starts here and eases to its
# own side-on angle, so no axis begins already looking straight down its line.
_OPENING = {"azimuth": 35.0, "elevation": 22.0}


def _find_axis(model: dict, axis_id: str) -> dict:
    wanted = canonical_token(axis_id)
    for axis in model["axes"]:
        if axis["id"] == wanted or opposite_token(axis["id"]) == wanted:
            return axis
    known = ", ".join(axis["id"] for axis in model["axes"])
    raise KeyError(f"Model {model['name']!r} has no axis {axis_id!r} — available: {known}")


def _side_on_angles(direction) -> tuple[float, float]:
    """Azimuth/elevation of a camera looking ACROSS `direction` rather than
    down it — the tertiary view's own trick (cube_model.py's DEFAULT_VIEWS),
    generalised to any axis instead of the one hardcoded perpendicular."""
    _, right, _ = basis_from(direction)
    camera = Camera()
    camera.look_along(right)
    return camera.azimuth, camera.elevation


def build_five_stations_scene(model: dict, axis_id: str, *, duration: float = 8.0) -> dict:
    """The Five Stations, played on ONE axis of `model`: the cube fades to a
    single line, the camera settles side-on, and the luminous/fallen beads
    slide from the geometric vertex to their radial stations (SCENES.md).
    """
    axis = _find_axis(model, axis_id)
    tier = axis["tier"]
    root = model.get("root") or "model"
    size = float(model.get("size", 1.0))
    length = float(_TIERS[tier]["length"]) * size
    axis_path = f"{root}/{GROUP_PATHS[tier]}/axis:{axis['id']}"
    centre_path = f"{root}/{GROUP_PATHS['centre']}"

    positive, negative = axis["ends"]
    azimuth, elevation = _side_on_angles(parse_direction(positive["direction"]))

    tracks = [
        _camera_track("camera.azimuth", _OPENING["azimuth"], azimuth),
        _camera_track("camera.elevation", _OPENING["elevation"], elevation),
        *_fade_everything_else(model, root, tier, axis["id"]),
        # Forced to 1 regardless of the view the content happened to open on —
        # this axis's own TIER group might have started dimmed (e.g. the
        # "cube" view leaves "secondary" at 0.5), and opacity multiplies down.
        _opacity_track(f"{root}/{GROUP_PATHS[tier]}", 1.0, 1.0),
        _opacity_track(axis_path, 1.0, 1.0),
        _opacity_track(centre_path, 1.0, 1.0),
    ]
    for end in (positive, negative):
        arm_path = f"{axis_path}/arm:{end['direction']}"
        direction = parse_direction(end["direction"])
        for stop in STOPS:
            stop_path = f"{arm_path}/{stop}"
            vertex_point = list(scale(direction, length))
            station_point = list(scale(direction, length * float(_RADIAL[stop])))
            tracks.append({
                "channel": "part.position", "path": stop_path,
                "keys": [
                    {"t": 0.0, "value": vertex_point},
                    {"t": FADE_END, "value": vertex_point, "ease": EASE},
                    {"t": SLIDE_END, "value": station_point},
                ],
            })
            tracks.append(_opacity_track(stop_path, 0.0, 1.0))

    return {
        "name": f"five_stations:{axis['id']}",
        "label": f"Five Stations — {axis['id']}",
        "duration": duration,
        "loop": False,
        "content": {"type": "model", "view": "cube"},
        "tracks": tracks,
    }


def _camera_track(channel: str, start: float, end: float) -> dict:
    return {
        "channel": channel,
        "keys": [{"t": 0.0, "value": start, "ease": EASE}, {"t": FADE_END, "value": end}],
    }


def _opacity_track(path: str, start: float, end: float) -> dict:
    return {
        "channel": "part.opacity", "path": path,
        "keys": [{"t": 0.0, "value": start, "ease": EASE}, {"t": SLIDE_END, "value": end}],
    }


def _fade_everything_else(model: dict, root: str, tier: str, axis_id: str) -> list[dict]:
    """Every group that is NOT this axis or the centre, faded to nothing by
    FADE_END — "the cube fades until only the Sacred Axis line remains"."""
    paths = [f"{root}/{GROUP_PATHS['glass']}"]
    for other_tier in TIER_ORDER:
        if other_tier != tier:
            paths.append(f"{root}/{GROUP_PATHS[other_tier]}")
    for sibling in model["axes"]:
        if sibling["tier"] == tier and sibling["id"] != axis_id:
            paths.append(f"{root}/{GROUP_PATHS[tier]}/axis:{sibling['id']}")
    for kind in KIND_ORDER:
        if kind != "centre":
            paths.append(f"{root}/{GROUP_PATHS[kind]}")
    return [_opacity_track(path, 1.0, 0.0) for path in paths]
