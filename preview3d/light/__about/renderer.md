# Light Renderer

**Script:** [Light Renderer (script)](../renderer.py)
**Flow:** [diagram](../__flow/renderer.md)

## Purpose

Turns the scene into pixels: flatten the tree to world geometry, project it, sort it back to front, and paint it with QPainter. Also builds the optional ground grid. This module and `view.py` are the only ones in the LIGHT renderer that touch Qt.

## Connections

### Uses
- [Light Scene](scene.md) — `Node`, the tree it flattens
- [Preview3d Package (folder)](../../___preview3d.md) — `vectors.py`: `Mat3`, `Vec3`, `add`, `cross`, `dot`, `mat_apply`, `mat_multiply`, `normalize`, `scale`, `sub`
- a `camera`-shaped object (typically a [Light Camera](camera.md)) passed in by the caller — `paint_scene` calls `.project()` and reads `.position`, without importing the `Camera` class

### Used by
- [Light Widget](view.md) — calls `build_grid`, `content_points` and `paint_scene` from `paintEvent` and its own internals

## Functions

- `iter_world_geometry(root, visible_only=True)`: yields `(kind, world data, colour, opacity)` for the whole tree, applying each node's rotation (`basis`), translate and uniform scale down the chain, and multiplying opacity so dimming a group dims everything under it — this is the opacity-propagation step (see the [flow diagram](../__flow/renderer.md))
- `content_points(root)`: every world point of the content — what the camera frames against
- `build_grid(points, options=None)`: ground grid sized to the content, cell step rounded to 1, 2 or 5 × 10ⁿ (same rule as the web core's, which is why the readout can honestly say "0.5 per cell")
- `paint_scene(painter, root, camera, width, height, grid_segments)`: the paint pass — see the flow diagram

## Near-Culling

`NEAR_CULL` (`1e-3`) — a face or line is dropped **whole** if any of its points projects at or behind the eye's own near plane, not only when ALL of them do. Three.js's WebGL pipeline clips at its camera's near plane in hardware; this software painter has no such stage, so before this guard a vertex just past the eye divided by a near-zero (or negative) depth and projected to its **mirror image** on screen rather than off it — a garbled polygon, not an absent one. That is exactly the situation the Blindness view's first-person dolly creates (the camera flies to inside the glass shell), which is why the guard exists (project's `NEAR_CULL` module constant, applied in `_face_item` and `_line_item`) — nothing before M3 placed the camera anywhere near its own content. See CLAUDE.md's "Known Traps" for the project-wide framing of this issue.

## Design Decisions

- **Painter's algorithm.** Sorting whole polygons back to front by average projected depth (`items.sort(key=..., reverse=True)`) is exact for separated, non-intersecting shapes, which is what this renderer is for. It cannot order intersecting geometry, and that limit is stated in [RENDERERS.md](../../../RENDERERS.md) rather than hidden.
- **Nothing writes depth, so translucency is free.** A dimmed face simply lets what is behind it through — no depth-write special case of the kind the web core needs.
- **A branch dimmed to invisibility is skipped whole**, not transformed and then discarded per polygon (`opacity * node.opacity <= _INVISIBLE`) — a model view lights one family of thirteen axes and dims the rest to zero, so this is most of the scene most of the time (root Priority A: this walk is the hot path).
- **The rotation matrix is only paid where a rotation exists.** `basis` is carried as `None` for the overwhelmingly common case, and the transform stays a plain scale-and-offset; a matrix multiply per vertex everywhere else would cost real time with nothing to show for it.
- **Labels carry an em ratio** (`LABEL_EM_RATIO = 0.57`). A label's `height` is the whole billboard's height, matching the web core, where the padded text canvas puts the glyphs at about 57% of it. Without the factor the same scene shows visibly larger text here, for no reason a reader could guess.
- **Faces are stroked with a hairline pen in their own fill colour**, which hides the seams that otherwise show between adjacent facets of a tessellated cylinder.
- **Lines are painted at exactly the opacity their part carries**, with no extra fading applied here. A second factor at draw time is invisible to `list_parts`, so it made the two renderers disagree about a part they both reported: the cube's wireframe read 0.35 in the web core and 1.0 here. How faint a wireframe is now belongs to the part that owns it, from `shared/spec.json`.
