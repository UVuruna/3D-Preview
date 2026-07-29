# Light Scene

**Script:** [Light Scene (script)](scene.py)

## Purpose

The node tree the LIGHT renderer draws, and the part operations on it. The paths and semantics are the **same contract** the web core implements in `src/parts.js` — a model authored per [MODELS.md](../../MODELS.md) behaves identically in both.

## Connections

### Used by
- [Light Primitives](primitives.md) — builds these nodes
- [Light Renderer](renderer.md) — flattens the tree into draw items
- [Light Widget](view.md) — exposes the operations as widget methods

## Classes

### Face / Segment / Label
The three things a node can draw. `Face` is a flat convex polygon, `Segment` a stroked line, `Label` a billboard text anchor whose `height` is in world units. Coordinates are in the owning node's local space; the renderer applies the ancestor chain.

### Node
`name`, `position`, `scale` (uniform), `visible`, `opacity`, `basis` (an optional rotation), `stroke`, the three drawable lists, and `children`. `drawable` is true when the node carries geometry, as opposed to being a pure group.

`stroke` (default `1.0`) is how much of the node's own **segments** are drawn, from each one's start toward its end — a line "growing" into place. Only segments read it; a node's faces and labels are unaffected, so a group can carry both a stroke-drawn overlay and solid geometry without splitting. This is what the Hexagram X-ray's triangles "draw themselves" with (`part.strokeProgress` in [Animation Scenes](../../SCENES.md)).

## Functions

`collect_parts`, `find_part`, `require_part`, `set_part_visible`, `set_part_opacity`, `set_part_position`, `set_part_stroke`, `show_only`, `remove_part` — mirroring `src/parts.js` name for name (`setPartPosition`, `setPartStroke` there).

## Design Decisions

- **`require_part` raises `KeyError` listing the paths that exist** (root Rule #1). A typo must never look like a part that simply had nothing to change — the same rule the web core follows.
- **Only translate and uniform scale.** That is what the spec format offers, and keeping the transform to two numbers means a world point is one multiply and one add per level rather than a matrix chain.
- **Opacity multiplies down the tree**, so dimming a group dims everything under it — matching the web core, where the same effect comes from applying opacity to a subtree.
