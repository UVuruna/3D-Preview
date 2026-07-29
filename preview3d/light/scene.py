"""Scene graph and part addressing for the LIGHT renderer.

The node tree and the path rules are the SAME contract the web renderer
implements in `src/parts.js` — same names, same paths, same semantics for
visibility, opacity and switch groups. A model authored per MODELS.md must
behave identically in both. `tests/test_renderer_parity.py` pins that.
"""

from dataclasses import dataclass, field

from ..vectors import Mat3, Vec3

PATH_SEPARATOR = "/"


@dataclass
class Face:
    """A flat convex polygon. Vertices are in the owning node's local space."""

    points: list[Vec3]
    color: str


@dataclass
class Segment:
    """A straight line, drawn with a stroke rather than as geometry."""

    start: Vec3
    end: Vec3
    color: str
    width: float = 1.0


@dataclass
class Label:
    """A billboard text anchor. `height` is in world units, as in the web core."""

    anchor: Vec3
    text: str
    color: str
    height: float


@dataclass
class Node:
    name: str = ""
    position: Vec3 = (0.0, 0.0, 0.0)
    scale: float = 1.0
    visible: bool = True
    opacity: float = 1.0
    # An optional rotation, `None` meaning none — which is the overwhelmingly
    # common case, and why the painter can skip the matrix entirely rather than
    # multiply every point by an identity. This is what carries a snapped cube
    # orientation (orientations.py); the web core carries it as a quaternion on
    # the same node.
    basis: Mat3 | None = None
    # How much of this node's own SEGMENTS are drawn, 0..1 — a line "growing"
    # from its start toward its end. 1.0 (the default) draws the whole line;
    # below that, every segment is shortened toward its own start point. Only
    # segments read this; faces and labels are unaffected, so a group holding
    # both a stroke-drawn overlay and solid geometry never has to be split.
    stroke: float = 1.0
    faces: list[Face] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)
    labels: list[Label] = field(default_factory=list)
    children: list["Node"] = field(default_factory=list)

    @property
    def drawable(self) -> bool:
        return bool(self.faces or self.segments or self.labels)

    def add(self, child: "Node") -> "Node":
        self.children.append(child)
        return child


# ---- Part addressing --------------------------------------------------------


def _named(node: Node, index: int) -> str:
    return node.name or f"Node#{index}"


def walk(root: Node, prefix: str = "", chain: list[Node] | None = None):
    """Yield (node, path, ancestor_chain) for every node under root."""
    chain = chain or [root]
    for index, child in enumerate(root.children):
        path = prefix + _named(child, index)
        child_chain = chain + [child]
        yield child, path, child_chain
        yield from walk(child, path + PATH_SEPARATOR, child_chain)


def collect_parts(root: Node) -> list[dict]:
    """The part list, in the same shape the web renderer returns."""
    parts = []
    for node, path, _ in walk(root):
        parts.append({
            "path": path,
            "name": node.name or "Node",
            "type": "Mesh" if node.drawable else "Group",
            "depth": path.count(PATH_SEPARATOR),
            "drawable": node.drawable,
            "visible": node.visible,
            "opacity": node.opacity,
            "color": node_color(node),
        })
    return parts


def node_color(node: Node) -> str | None:
    """What colour a part wears, or None for a pure group.

    Reported because a host needs it for a legend, and because it is the only
    way a test can check that a COMPUTED palette came out the same in both
    renderers: the pictures cannot be compared, the values can.
    """
    for source in (node.faces, node.segments, node.labels):
        if source:
            return source[0].color.upper()
    return None


def find_part(root: Node, path: str) -> Node | None:
    for node, candidate, _ in walk(root):
        if candidate == path:
            return node
    return None


def require_part(root: Node, path: str) -> Node:
    """Resolve or fail loudly — a typo must not look like a no-op (Rule #1)."""
    node = find_part(root, path)
    if node is None:
        known = ", ".join(part["path"] for part in collect_parts(root))
        raise KeyError(f"Unknown part {path!r} — available: {known or '(none)'}")
    return node


def set_part_visible(root: Node, path: str, visible: bool) -> None:
    require_part(root, path).visible = visible


def set_part_opacity(root: Node, path: str, alpha: float) -> None:
    require_part(root, path).opacity = alpha


def set_part_position(root: Node, path: str, position) -> None:
    require_part(root, path).position = tuple(float(component) for component in position)


def set_part_stroke(root: Node, path: str, progress: float) -> None:
    require_part(root, path).stroke = float(progress)


def show_only(root: Node, group_path: str, child_name: str) -> None:
    """Show one child of a group and hide its siblings."""
    group = require_part(root, group_path)
    found = False
    for index, child in enumerate(group.children):
        matches = _named(child, index) == child_name
        child.visible = matches
        found = found or matches
    if not found:
        names = ", ".join(_named(c, i) for i, c in enumerate(group.children))
        raise KeyError(f"Group {group_path!r} has no child {child_name!r} — available: {names or '(none)'}")


def remove_part(root: Node, path: str) -> None:
    node = require_part(root, path)
    for parent, _, _ in [(root, "", None), *walk(root)]:
        if node in parent.children:
            parent.children.remove(node)
            return
