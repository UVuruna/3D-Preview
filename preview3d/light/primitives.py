"""Parametric primitives for the LIGHT renderer.

Reads the SAME spec JSON the web core reads (see src/primitives.md and
MODELS.md) and produces the same named part tree, so a host can hand either
renderer the identical scene description. The colour table is not restated here
— both renderers read shared/palette.json.
"""

import math

from ..directions import canonical_token, opposite_token, parse_direction, token_vector, vertex_neighbors
from ..resources import load_shared_spec
from .scene import Face, Label, Node, Segment
from ..vectors import UP, Vec3, add, cross, normalize, rotate_towards, scale

_SPEC = load_shared_spec()
POLE_COLORS: dict[str, str] = _SPEC["poles"]
FACE_ORDER: list[str] = _SPEC["faceOrder"]
_NEUTRAL = _SPEC["neutral"]
_SCENE = _SPEC["modelScene"]
_COLORS = _SPEC["axisColors"]
_HEXAGRAM = _SPEC["hexagram"]
BEAD_RADIUS_FACTOR: float = float(_SCENE["beadRadiusFactor"])

# An arm's direction is no longer a six-entry lookup: it is a TOKEN or a vector,
# resolved by the shared grammar (directions.py). The six face tokens are the
# one-letter case of that grammar rather than a table beside it, so every spec
# written against the old table still means exactly what it meant — and the
# cube's six edge axes and four vertex diagonals became expressible at all.
AXES_DEFAULTS = {"armLength": 1.0, "armRadius": 0.03, "joint": True}
CUBE_DEFAULTS = {"size": 1.0, "color": _NEUTRAL["body"], "colors": None, "edges": True}
MARKER_DEFAULTS = {"radius": 0.05, "color": _NEUTRAL["body"]}
LABEL_PREFIX = "label:"

# Tessellation. Higher is smoother and costs polygons; these are the point
# where a shaft stops reading as faceted at normal preview sizes.
SHAFT_SEGMENTS = 14
TIP_SEGMENTS = 16
SPHERE_SEGMENTS = 12
SPHERE_RINGS = 6
# A model puts twenty-seven markers on screen at once, each a few percent of the
# cube across. At that size the extra facets are invisible and the polygons are
# not: the full sphere would be two thirds of everything this renderer sorts.
MARKER_SEGMENTS = 8
MARKER_RINGS = 4


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
    return [{"axis": axis, "label": axis[1].upper() + axis[0]} for axis in FACE_ORDER]


def arm_name(arm: dict, index: int) -> str:
    """The path segment an arm is addressed by — one rule, both renderers.

    A token names itself in the cube's own letter order, so '+y+x' and '+x+y'
    can never become two addresses for one arm. An arm given a raw vector and
    no name falls back to its position in the list, which is at least stable.
    """
    if arm.get("name"):
        return arm["name"]
    axis = arm.get("axis")
    if isinstance(axis, str):
        return f"arm:{canonical_token(axis)}"
    return f"arm:{index}"


def build_axes(spec: dict) -> Node:
    arm_length = float(spec.get("armLength", AXES_DEFAULTS["armLength"]))
    arm_radius = float(spec.get("armRadius", AXES_DEFAULTS["armRadius"]))
    arms = spec.get("arms") or _default_arms()

    root = Node(name="axes")
    shaft_length = arm_length * 0.8
    tip_length = arm_length * 0.2

    # Thirteen axes drawn as thirteen gizmos would stack thirteen joints in one
    # spot, so a model turns the joint off and names its own centre seat.
    if spec.get("joint", AXES_DEFAULTS["joint"]):
        joint = Node(name="joint")
        joint.faces = _sphere(arm_radius * 2, _NEUTRAL["joint"])
        root.add(joint)

    for index, arm in enumerate(arms):
        axis = arm.get("axis")
        if axis is None:
            raise ValueError("Every arm needs an 'axis' — a direction token or a 3-vector")
        direction = parse_direction(axis)
        # An arm's colour defaults to its pole hue, exactly as in the web core;
        # only a one-letter token HAS a pole, so anything else must say.
        color = arm.get("color") or POLE_COLORS.get(axis if isinstance(axis, str) else "")
        if not color:
            raise ValueError(
                f"Arm {arm_name(arm, index)!r} has no colour and its direction is not "
                "one of the six poles, so there is none to inherit"
            )
        group = root.add(Node(name=arm_name(arm, index)))

        shaft = Node(name="shaft")
        shaft.faces = _cylinder(arm_radius, shaft_length, direction, 0.0, color)
        group.add(shaft)

        tip = Node(name="tip")
        tip.faces = _cone(arm_radius * 2.4, tip_length, direction, shaft_length, color)
        group.add(tip)

        height = float(spec.get("stopHeight", arm_length * float(_SCENE["armLabelHeight"])))
        if arm.get("label"):
            group.add(_arm_labels(arm["label"], color, direction, arm_length, height))
        for stop in arm.get("stops", ()):
            # An axis stop gets a small bead: unlike a cell, an arm's stop has no
            # marker sphere of its own, and "Five beads slide to their stations"
            # (PLAN.md, The Five Stations) needs something visible to slide.
            group.add(build_stop(stop, color, height, bead=True))
    return root


def _arm_labels(label, color: str, direction: Vec3, arm_length: float, height: float) -> Node:
    """A string makes one label; a list makes a switch group with the first shown."""
    texts = label if isinstance(label, list) else [label]
    holder = Node(name="labels")
    anchor = scale(direction, arm_length * 1.16)
    for index, text in enumerate(texts):
        node = Node(name=f"label:{index}", visible=index == 0)
        node.labels = [Label(anchor=anchor, text=str(text), color=color, height=height)]
        holder.add(node)
    return holder


def build_stop(stop: dict, color: str, height: float, bead: bool = False) -> Node:
    """One radial stop: a switch group of one label per register.

    This is what the Switcher drives (switcher.py) — a group named for the stop,
    holding `label:<register>` children with the first shown. The stop itself
    SITS at its anchor (`Node.position`, not a per-label offset) so a scene can
    address it directly with `part.position` — the channel the Five Stations
    scene tweens to slide a stop from the geometric vertex to its final radial
    factor (SCENES.md). Labels then anchor at the LOCAL origin, which is exactly
    where the stop already put them.
    """
    anchor = tuple(float(component) for component in stop["anchor"])
    holder = Node(name=stop["name"], position=anchor)
    if bead:
        holder.faces = _sphere(height * BEAD_RADIUS_FACTOR, stop.get("color") or color)
    for index, (register, text) in enumerate(stop["labels"].items()):
        node = Node(name=LABEL_PREFIX + register, visible=index == 0)
        node.labels = [Label(anchor=(0.0, 0.0, 0.0), text=str(text),
                             color=stop.get("color") or color, height=height)]
        holder.add(node)
    return holder


# ---- Group and marker -------------------------------------------------------


def build_group(spec: dict) -> Node:
    """An empty node. A model's tree is mostly groups, and a group that has to
    be a shape is a group that cannot be empty when its family is."""
    return Node(name=spec.get("name") or "group")


def build_marker(spec: dict) -> Node:
    """A seat: a small sphere, plus its radial stops. Its position comes from
    the universal `position` field, like every other primitive's."""
    radius = float(spec.get("radius", MARKER_DEFAULTS["radius"]))
    color = spec.get("color") or MARKER_DEFAULTS["color"]
    root = Node(name="marker")
    body = Node(name="body")
    body.faces = _sphere(radius, color, MARKER_SEGMENTS, MARKER_RINGS)
    root.add(body)
    height = float(spec.get("stopHeight", radius * 2.6))
    for stop in spec.get("stops", ()):
        root.add(build_stop(stop, color, height))
    return root


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
        # The wireframe is deliberately faint, and how faint is a shared value:
        # the web core puts it on the line material, this on the node, and both
        # therefore report the same opacity for the same part.
        node = Node(name="edges", opacity=float(_NEUTRAL["edgeOpacity"]))
        node.segments = _cube_edges(size, _NEUTRAL["edges"])
        root.add(node)
    return root


# ---- Hexagram ----------------------------------------------------------------


def build_hexagram(spec: dict) -> Node:
    """The two triangles a cube's silhouette splits into, seen down `diagonal`.

    Computed from the cube's own geometry (root Rule 19), never per-scene
    coordinates: each pole of the chosen body diagonal has three edge-neighbour
    vertices (`vertex_neighbors`), and those two triangles ARE the six
    "equatorial face-diagonals" the Hexagram X-ray draws itself into. Each
    triangle is one Node holding its three segments, so a single
    `part.strokeProgress` on `hexagram/triangle:up` (or `:down`) draws all three
    sides at once — the "DRAW themselves" beat of Scene 1 (SCENES.md).
    """
    diagonal = spec.get("diagonal")
    if diagonal is None:
        raise ValueError("A hexagram needs a 'diagonal' — a vertex direction token")
    size = float(spec.get("size", 1.0))
    up_color = spec.get("upColor") or _COLORS["sacred"]
    down_color = spec.get("downColor") or _NEUTRAL["joint"]
    width = float(spec.get("lineWidth", _HEXAGRAM["lineWidth"]))

    root = Node(name="hexagram")
    root.add(_triangle("triangle:up", canonical_token(diagonal), size, up_color, width))
    root.add(_triangle("triangle:down", opposite_token(canonical_token(diagonal)), size, down_color, width))
    return root


def _triangle(name: str, pole: str, size: float, color: str, width: float) -> Node:
    """A vertex's position is its token's UN-normalised vector times half the
    cube — same rule as a model's cells (cube_model.py), so a triangle corner
    lands exactly on the cube's own vertex, never on an approximation of it."""
    half = size / 2
    corners = [scale(token_vector(vertex), half) for vertex in vertex_neighbors(pole)]
    node = Node(name=name)
    node.segments = [
        Segment(start=corners[i], end=corners[(i + 1) % 3], color=color, width=width)
        for i in range(3)
    ]
    return node


def _face_quad(face: str, size: float) -> list[Vec3]:
    """One cube face, wound so its normal points outward."""
    normal = parse_direction(face)
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


def _sphere(radius: float, color: str, segments: int = SPHERE_SEGMENTS,
            rings: int = SPHERE_RINGS) -> list[Face]:
    faces = []
    for ring in range(rings):
        phi0 = math.pi * ring / rings
        phi1 = math.pi * (ring + 1) / rings
        for seg in range(segments):
            theta0 = 2 * math.pi * seg / segments
            theta1 = 2 * math.pi * (seg + 1) / segments
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


_BUILDERS = {
    "axes": build_axes,
    "cube": build_cube,
    "group": build_group,
    "marker": build_marker,
    "hexagram": build_hexagram,
}
