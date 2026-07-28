"""Projecting and painting the LIGHT scene with QPainter.

This module and `view.py` are the only ones in the LIGHT renderer that touch Qt;
`vectors`, `scene`, `primitives` and `camera` stay pure Python so the geometry
can be tested without a GUI.

Hidden surfaces are handled by the painter's algorithm — sort back to front and
paint over. That is exact for the separated, non-intersecting shapes this
renderer is for, and it is also why translucency needs no special handling here:
with nothing writing depth, a dimmed face simply lets what is behind it through.
"""

import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF

from .scene import Node
from .vectors import Vec3, add, cross, dot, normalize, scale, sub

# Lighting matches the web core's single key light at (5, 8, 6) over a bright
# neutral environment; the ambient share stands in for that environment.
LIGHT_DIRECTION: Vec3 = (5.0, 8.0, 6.0)
AMBIENT = 0.55
DIFFUSE = 0.45

GRID_DEFAULTS = {
    "lineColor": "#8A8AA0",
    "opacity": 0.28,
    "spanFactor": 2.5,
    "targetCells": 12,
}

LABEL_FONT = "Inter"
MIN_LABEL_PX = 7      # below this a label is unreadable; do not paint noise
EPSILON = 1e-6

# A label's `height` is the height of the whole billboard, matching the web
# core, where the text canvas is padded and the glyphs occupy about this
# fraction of it. Without the factor the same scene shows visibly bigger text
# here than there, for no reason a reader could guess.
LABEL_EM_RATIO = 0.57


@dataclass
class _Item:
    depth: float
    kind: str            # 'face' | 'line' | 'label'
    payload: tuple


# ---- Scene flattening -------------------------------------------------------


def iter_world_geometry(root: Node, visible_only: bool = True):
    """Yield (kind, world data, colour, opacity) for the whole tree.

    Applies each node's translate + uniform scale down the chain, and multiplies
    opacity so dimming a group dims everything under it.
    """
    def walk(node: Node, offset: Vec3, factor: float, opacity: float):
        if visible_only and not node.visible:
            return
        here_offset = add(offset, scale(node.position, factor))
        here_scale = factor * node.scale
        here_opacity = opacity * node.opacity

        def to_world(point: Vec3) -> Vec3:
            return add(here_offset, scale(point, here_scale))

        for face in node.faces:
            yield "face", [to_world(p) for p in face.points], face.color, here_opacity
        for segment in node.segments:
            yield "line", (to_world(segment.start), to_world(segment.end),
                           segment.width), segment.color, here_opacity
        for label in node.labels:
            yield "label", (to_world(label.anchor), label.text,
                            label.height * here_scale), label.color, here_opacity

        for child in node.children:
            yield from walk(child, here_offset, here_scale, here_opacity)

    yield from walk(root, (0.0, 0.0, 0.0), 1.0, 1.0)


def content_points(root: Node) -> list[Vec3]:
    """Every world point of the content — what the camera frames against."""
    points: list[Vec3] = []
    for kind, data, _, _ in iter_world_geometry(root, visible_only=False):
        if kind == "face":
            points.extend(data)
        elif kind == "line":
            points.extend((data[0], data[1]))
        else:
            points.append(data[0])
    return points


# ---- Grid -------------------------------------------------------------------


def _nice_step(raw: float) -> float:
    """Round up to 1, 2 or 5 x 10^n so a cell is a number a human can read off."""
    if raw <= 0:
        return 1.0
    magnitude = 10 ** math.floor(math.log10(raw))
    normalized = raw / magnitude
    rounded = 1 if normalized <= 1 else 2 if normalized <= 2 else 5 if normalized <= 5 else 10
    return rounded * magnitude


def build_grid(points: list[Vec3], options: dict | None = None):
    """Ground grid sized to the content. Returns (segments, step) or (None, 0)."""
    if not points:
        return None, 0.0
    opts = {**GRID_DEFAULTS, **(options or {})}
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    footprint = max(max(xs) - min(xs), max(zs) - min(zs), (max(ys) - min(ys)) * 0.5) or 1.0
    span = footprint * opts["spanFactor"]
    step = _nice_step(span / opts["targetCells"])
    divisions = max(2, round(span / step))
    extent = divisions * step
    half = extent / 2
    cx = (min(xs) + max(xs)) / 2
    cz = (min(zs) + max(zs)) / 2
    floor = min(ys)

    segments = []
    for i in range(divisions + 1):
        offset = -half + i * step
        segments.append(((cx + offset, floor, cz - half), (cx + offset, floor, cz + half)))
        segments.append(((cx - half, floor, cz + offset), (cx + half, floor, cz + offset)))
    return segments, step


# ---- Painting ---------------------------------------------------------------


def _shade(color: str, normal: Vec3, to_eye: Vec3) -> QColor:
    """Flat Lambert shading, lit from either side (faces here are double-sided)."""
    if dot(normal, to_eye) < 0:
        normal = scale(normal, -1.0)
    intensity = AMBIENT + DIFFUSE * max(0.0, dot(normal, normalize(LIGHT_DIRECTION)))
    base = QColor(color)
    return QColor.fromHslF(
        base.hueF() if base.hueF() >= 0 else 0.0,
        base.saturationF(),
        min(1.0, base.lightnessF() * intensity * 1.35),
    )


def _face_normal(points: list[Vec3]) -> Vec3 | None:
    for i in range(1, len(points) - 1):
        candidate = cross(sub(points[i], points[0]), sub(points[i + 1], points[0]))
        if dot(candidate, candidate) > EPSILON:
            return normalize(candidate)
    return None


def paint_scene(painter: QPainter, root: Node, camera, width: int, height: int,
                grid_segments=None) -> None:
    """Paint the scene, farthest first. Nothing here mutates the scene."""
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    eye = camera.position
    items: list[_Item] = []

    if grid_segments:
        color = QColor(GRID_DEFAULTS["lineColor"])
        color.setAlphaF(GRID_DEFAULTS["opacity"])
        for start, end in grid_segments:
            item = _line_item(start, end, camera, width, height, color, 1.0)
            if item:
                items.append(item)

    for kind, data, color, opacity in iter_world_geometry(root):
        if opacity <= 0.01:
            continue
        if kind == "face":
            item = _face_item(data, camera, width, height, color, opacity, eye)
        elif kind == "line":
            start, end, line_width = data
            painted = QColor(color)
            painted.setAlphaF(opacity * 0.45)
            item = _line_item(start, end, camera, width, height, painted, line_width)
        else:
            item = _label_item(data, camera, width, height, color, opacity)
        if item:
            items.append(item)

    items.sort(key=lambda item: item.depth, reverse=True)
    for item in items:
        _draw(painter, item)


def _face_item(points, camera, width, height, color, opacity, eye) -> _Item | None:
    projected = [camera.project(p, width, height) for p in points]
    if all(p[2] <= 0 for p in projected):
        return None                      # entirely behind the eye
    normal = _face_normal(points)
    if normal is None:
        return None
    shade = _shade(color, normal, normalize(sub(eye, points[0])))
    shade.setAlphaF(opacity)
    polygon = QPolygonF([QPointF(p[0], p[1]) for p in projected])
    depth = sum(p[2] for p in projected) / len(projected)
    return _Item(depth, "face", (polygon, shade))


def _line_item(start, end, camera, width, height, color: QColor, line_width) -> _Item | None:
    a = camera.project(start, width, height)
    b = camera.project(end, width, height)
    if a[2] <= 0 and b[2] <= 0:
        return None
    return _Item((a[2] + b[2]) / 2, "line",
                 (QPointF(a[0], a[1]), QPointF(b[0], b[1]), color, line_width))


def _label_item(data, camera, width, height, color, opacity) -> _Item | None:
    anchor, text, world_height = data
    x, y, depth = camera.project(anchor, width, height)
    if depth <= 0:
        return None
    pixels = (world_height * LABEL_EM_RATIO * height
              / max(camera.visible_height_at(depth), EPSILON))
    if pixels < MIN_LABEL_PX:
        return None
    painted = QColor(color)
    painted.setAlphaF(opacity)
    return _Item(depth, "label", (QPointF(x, y), text, painted, pixels))


def _draw(painter: QPainter, item: _Item) -> None:
    if item.kind == "face":
        polygon, color = item.payload
        painter.setPen(QPen(color, 1.0))     # hairline pen hides seams between facets
        painter.setBrush(color)
        painter.drawPolygon(polygon)
    elif item.kind == "line":
        start, end, color, line_width = item.payload
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(color, line_width))
        painter.drawLine(start, end)
    else:
        point, text, color, pixels = item.payload
        font = QFont(LABEL_FONT)
        font.setPixelSize(max(MIN_LABEL_PX, round(pixels)))
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QPen(color))
        metrics = painter.fontMetrics()
        painter.drawText(
            QPointF(point.x() - metrics.horizontalAdvance(text) / 2,
                    point.y() + metrics.capHeight() / 2),
            text,
        )
