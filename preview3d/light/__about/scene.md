# Light Scene

**Script:** [Light Scene (script)](../scene.py)

## Purpose

The node tree the LIGHT renderer draws, and the part operations on it. The paths and semantics are the **same contract** the web core implements in `src/parts.js` — a model authored per [MODELS.md](../../../MODELS.md) behaves identically in both.

This module defines the `Node` structure and simple, single-pass tree operations (find by path, set a field, list parts). It does not itself walk the tree applying transforms or propagating opacity down descendants — that multi-step traversal lives in [Light Renderer](renderer.md)'s `iter_world_geometry` (see its [flow diagram](../__flow/renderer.md)), which is where the diagram for that algorithm belongs. A diagram of this module's own functions would only restate straightforward code, so it stays Standard tier with no `__flow/`.

## Connections

### Used by
- [Light Primitives](primitives.md) — builds these nodes
- [Light Model View](model_view.md) — builds a `Node` content root around the model's spec
- [Light Renderer](renderer.md) — flattens the tree into draw items
- [Light Widget](view.md) — exposes the operations as widget methods

## Classes

### Face / Segment / Label
The three things a node can draw. `Face` is a flat convex polygon, `Segment` a stroked line, `Label` a billboard text anchor whose `height` is in world units. Coordinates are in the owning node's local space; the renderer applies the ancestor chain.

### Node
`name`, `position`, `scale` (uniform), `visible`, `opacity`, `basis` (an optional rotation matrix, `Mat3 | None`), `stroke`, the three drawable lists, and `children`. `drawable` is true when the node carries geometry, as opposed to being a pure group.

`basis` carries a snapped orientation (`orientations.py`) as a rotation matrix; `None` is the overwhelmingly common case, which is why [Light Renderer](renderer.md) can skip the matrix multiply entirely rather than apply an identity matrix per vertex. The web core carries the equivalent rotation as a quaternion on the same node.

`stroke` (default `1.0`) is how much of the node's own **segments** are drawn, from each one's start toward its end — a line "growing" into place. Only segments read it; a node's faces and labels are unaffected, so a group can carry both a stroke-drawn overlay and solid geometry without splitting. This is what the Hexagram X-ray's triangles "draw themselves" with (`part.strokeProgress` in `SCENES.md`).

## Functions

`collect_parts`, `find_part`, `require_part`, `set_part_visible`, `set_part_opacity`, `set_part_position`, `set_part_stroke`, `show_only`, `remove_part` — mirroring `src/parts.js` name for name (`setPartPosition`, `setPartStroke` there).

## Design Decisions

- **`require_part` raises `KeyError` listing the paths that exist** (No Error Masking (rules/CODE.md)). A typo must never look like a part that simply had nothing to change — the same rule the web core follows.
- **Position and scale are simple per-node values (translate + uniform scale), and rotation is a separate optional field (`basis`) rather than folded into a general transform.** A world point is one multiply-by-scalar and one add per level for the common (no-rotation) case, and only pays a matrix multiply on the rare node that carries one — see [Light Renderer](renderer.md)'s `walk()`.
- **Opacity multiplies down the tree** — but the multiplication itself happens in the renderer's tree walk, not here; this module only stores the per-node `opacity` value the renderer reads.
