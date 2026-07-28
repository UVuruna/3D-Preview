"""Parametric primitives for the LIGHT renderer.

Reads the SAME spec JSON the web core reads (see src/primitives.md and
MODELS.md) and produces the same named part tree, so a host can hand either
renderer the identical scene description. The colour table is not restated here
— both renderers read shared/palette.json.
"""

import math

from ..resources import load_shared_spec
from .scene import Face, Label, Node, Segment
from .vectors import UP, Vec3, add, cross, normalize, rotate_towards, scale

_SPEC = load_shared_spec()
POLE_COLORS: dict[str, str] = _SPEC["poles"]
FACE_ORDER: list[str] = _SPEC["faceOrder"]
_NEUTRAL = _SPEC["neutral"]

AXIS_DIRECTIONS: dict[str, Vec3] = {
    "+x": (1.0, 0.0, 0.0), "-x": (-1.0, 0.0, 0.0),
    "+y": (0.0, 1.0, 0.0), "-y": (0.0, -1.0, 0.0),
    "+z": (0.0, 0.0, 1.0), "-z": (0.0, 0.0, -1.0),
}

AXES_DEFAULTS = {"armLength": 1.0, "armRadius": 0.03}
CUBE_DEFAULTS = {"size": 1.0, "color": _NEUTRAL["body"], "colors": None, "edges": True}

# Tessellation. Higher is smoother and costs polygons; these are the point
# where a shaft stops reading as faceted at normal preview sizes.
SHAFT_SEGMENTS = 14
TIP_SEGMENTS = 16
SPHERE_SEGMENTS = 12
SPHERE_RINGS = 6


def build_primitive(spec: dict) -> Node:
    """Universal spec fields — name, position, scale, children — as in the web core."""
    builder = _BUILDERS.get(spec.get("type"))
    if builder is None:
        raise ValueError(
            f"Unknown primitive type {spec.get('type')!r} — available: {', '.join(_BUILDERS)}"
        )
    node = builder(spec)
    if spec.get("name"):
        node.name = spec["name"]
    if spec.get("position"):
        node.position = tuple(spec["position"])
    if spec.get("scale"):
        node.scale = float(spec["scale"])
    for child in spec.get("children", ()):
        node.add(build_primitive(child))
    return node


# ---- Axes -------------------------------------------------------------------


def _default_arms() -> list[dict]:
    return [{"axis": axis, "label": axis[1].upper() + axis[0]} for axis in AXIS_DIRECTIONS]


def build_axes(spec: dict) -> Node:
    arm_length = float(spec.get("armLength", AXES_DEFAULTS["armLength"]))
    arm_radius = float(spec.get("armRadius", AXES_DEFAULTS["armRadius"]))
    arms = spec.get("arms") or _default_arms()

    root = Node(name="axes")
    shaft_length = arm_length * 0.8
    tip_length = arm_length * 0.2

    joint = Node(name="joint")
    joint.faces = _sphere(arm_radius * 2, _NEUTRAL["joint"])
    root.add(joint)

    for arm in arms:
        axis = arm.get("axis")
        direction = AXIS_DIRECTIONS.get(axis)
        if direction is None:
            raise ValueError(
                f"Unknown arm axis {axis!r} — expected one of: {', '.join(AXIS_DIRECTIONS)}"
            )
        # An arm's colour defaults to its pole hue, exactly as in the web core.
        color = arm.get("color") or POLE_COLORS[axis]
        group = root.add(Node(name=f"arm:{axis}"))

        shaft = Node(name="shaft")
        shaft.faces = _cylinder(arm_radius, shaft_length, direction, 0.0, color)
        group.add(shaft)

        tip = Node(name="tip")
        tip.faces = _cone(arm_radius * 2.4, tip_length, direction, shaft_length, color)
        group.add(tip)

        if arm.get("label"):
            group.add(_arm_labels(arm["label"], color, direction, arm_length))
    return root


def _arm_labels(label, color: str, direction: Vec3, arm_length: float) -> Node:
    """A string makes one label; a list makes a switch group with the first shown."""
    texts = label if isinstance(label, list) else [label]
    holder = Node(name="labels")
    anchor = scale(direction, arm_length * 1.16)
    for index, text in enumerate(texts):
        node = Node(name=f"label:{index}", visible=index == 0)
        node.labels = [Label(anchor=anchor, text=str(text), color=color,
                             height=arm_length * 0.16)]
        holder.add(node)
    return holder


# ---- Cube -------------------------------------------------------------------


def build_cube(spec: dict) -> Node:
    size = float(spec.get("size", CUBE_DEFAULTS["size"]))
    colors = spec.get("colors", CUBE_DEFAULTS["colors"])
    color = spec.get("color", CUBE_DEFAULTS["color"])
    edges = spec.get("edges", CUBE_DEFAULTS["edges"])

    root = Node(name="cube")
    face_colors = [POLE_COLORS[face] for face in FACE_ORDER] if colors == "poles" else colors

    if face_colors:
        if len(face_colors) != len(FACE_ORDER):
            raise ValueError(
                f"cube 'colors' needs {len(FACE_ORDER)} entries in order "
                f"{', '.join(FACE_ORDER)}, or the string 'poles'"
            )
        for face, face_color in zip(FACE_ORDER, face_colors):
            node = Node(name=f"face:{face}")
            node.faces = [Face(points=_face_quad(face, size), color=face_color)]
            root.add(node)
    else:
        body = Node(name="body")
        body.faces = [Face(points=_face_quad(face, size), color=color) for face in FACE_ORDER]
        root.add(body)

    if edges:
        node = Node(name="edges")
        node.segments = _cube_edges(size, _NEUTRAL["edges"])
        root.add(node)
    return root


def _face_quad(face: str, size: float) -> list[Vec3]:
    """One cube face, wound so its normal points outward."""
    normal = AXIS_DIRECTIONS[face]
    centre = scale(normal, size / 2)
    reference = (0.0, 0.0, 1.0) if abs(normal[1]) > 0.5 else UP
    right = normalize(cross(reference, normal))
    up = cross(normal, right)
    half = size / 2
    return [
        add(centre, add(scale(right, -half), scale(up, -half))),
        add(centre, add(scale(right, half), scale(up, -half))),
        add(centre, add(scale(right, half), scale(up, half))),
        add(centre, add(scale(right, -half), scale(up, half))),
    ]


def _cube_edges(size: float, color: str) -> list[Segment]:
    half = size / 2
    corners = [(x, y, z) for x in (-half, half) for y in (-half, half) for z in (-half, half)]
    segments = []
    for i, a in enumerate(corners):
        for b in corners[i + 1:]:
            # Two corners share an edge when they differ along exactly one axis.
            if sum(1 for k in range(3) if a[k] != b[k]) == 1:
                segments.append(Segment(start=a, end=b, color=color, width=1.0))
    return segments


# ---- Tessellation -----------------------------------------------------------


def _ring(radius: float, y: float, direction: Vec3, offset: float, segments: int) -> list[Vec3]:
    """A circle of points around +Y at height `y`, rotated onto `direction`."""
    points = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        local = (radius * math.cos(angle), y + offset, radius * math.sin(angle))
        points.append(rotate_towards(UP, direction, local))
    return points


def _cylinder(radius: float, height: float, direction: Vec3, offset: float, color: str) -> list[Face]:
    bottom = _ring(radius, 0.0, direction, offset, SHAFT_SEGMENTS)
    top = _ring(radius, height, direction, offset, SHAFT_SEGMENTS)
    return [
        Face(points=[bottom[i], bottom[(i + 1) % SHAFT_SEGMENTS],
                     top[(i + 1) % SHAFT_SEGMENTS], top[i]], color=color)
        for i in range(SHAFT_SEGMENTS)
    ]


def _cone(radius: float, height: float, direction: Vec3, offset: float, color: str) -> list[Face]:
    base = _ring(radius, 0.0, direction, offset, TIP_SEGMENTS)
    apex = rotate_towards(UP, direction, (0.0, height + offset, 0.0))
    centre = rotate_towards(UP, direction, (0.0, offset, 0.0))
    faces = [
        Face(points=[base[i], base[(i + 1) % TIP_SEGMENTS], apex], color=color)
        for i in range(TIP_SEGMENTS)
    ]
    faces += [
        Face(points=[base[(i + 1) % TIP_SEGMENTS], base[i], centre], color=color)
        for i in range(TIP_SEGMENTS)
    ]
    return faces


def _sphere(radius: float, color: str) -> list[Face]:
    faces = []
    for ring in range(SPHERE_RINGS):
        phi0 = math.pi * ring / SPHERE_RINGS
        phi1 = math.pi * (ring + 1) / SPHERE_RINGS
        for seg in range(SPHERE_SEGMENTS):
            theta0 = 2 * math.pi * seg / SPHERE_SEGMENTS
            theta1 = 2 * math.pi * (seg + 1) / SPHERE_SEGMENTS
            quad = [
                _on_sphere(radius, phi0, theta0), _on_sphere(radius, phi0, theta1),
                _on_sphere(radius, phi1, theta1), _on_sphere(radius, phi1, theta0),
            ]
            faces.append(Face(points=quad, color=color))
    return faces


def _on_sphere(radius: float, phi: float, theta: float) -> Vec3:
    return (
        radius * math.sin(phi) * math.cos(theta),
        radius * math.cos(phi),
        radius * math.sin(phi) * math.sin(theta),
    )


_BUILDERS = {"axes": build_axes, "cube": build_cube}
