# Light Renderer

**Script:** [Light Renderer (script)](renderer.py)

## Purpose

Turns the scene into pixels: flatten the tree to world geometry, project it, sort it back to front, and paint it with QPainter. Also builds the optional ground grid.

## Connections

### Uses
- [Light Scene](scene.md) — the tree it flattens
- [Light Camera](camera.md) — projection and visible height

### Used by
- [Light Widget](view.md) — calls `paint_scene` from `paintEvent`

## Functions

- `iter_world_geometry(root)`: yields `(kind, world data, colour, opacity)` for the whole tree, applying each node's translate + uniform scale down the chain and multiplying opacity so dimming a group dims everything under it
- `content_points(root)`: every world point — what the camera frames against
- `build_grid(points)`: ground grid sized to the content, cell step rounded to 1, 2 or 5 × 10ⁿ (same rule as the web core's, which is why the readout can honestly say "0.5 per cell")
- `paint_scene(painter, root, camera, width, height, grid_segments)`: the paint pass

## The Paint Pass

```
collect draw items: for every face, line and label
    project its points; drop anything with ANY point behind or grazing the near plane
    face → shade from its normal, average depth
    label → pixel size = world height × EM ratio × viewport height / visible height at that depth
sort all items by depth, farthest first
paint in that order
```

A node's `segments` also read its own `stroke` (0..1): below `1.0`, each segment is shortened toward its own start by that fraction before projection; at `0.0` it is skipped entirely. This is the whole implementation of a line "drawing itself" — no separate animation path, just a smaller segment handed to the same projector.

Shading is flat Lambert from one key light plus an ambient share standing in for the web core's environment map. The normal is flipped toward the eye first, because faces here are effectively double-sided — a face seen from behind must still be lit.

## Near-Culling

`NEAR_CULL` — a face or line is dropped **whole** if any of its points projects at or behind the eye's own near plane, not only when ALL of them do. Three.js's WebGL pipeline clips at its camera's near plane in hardware; this software painter has no such stage, so before this guard a vertex just past the eye divided by a near-zero (or negative) depth and projected to its **mirror image** on screen rather than off it — a garbled polygon, not an absent one. That is exactly the situation the Blindness view's first-person dolly creates (the camera flies to inside the glass shell), which is why the guard exists now rather than earlier: nothing before M3 placed the camera anywhere near its own content.

## Design Decisions

- **Painter's algorithm.** Sorting whole polygons back to front is exact for separated, non-intersecting shapes, which is what this renderer is for. It cannot order intersecting geometry, and that limit is stated in [RENDERERS.md](../../RENDERERS.md) rather than hidden.
- **Nothing writes depth, so translucency is free.** A dimmed face simply lets what is behind it through — no depth-write special case of the kind the web core needs.
- **Labels carry an em ratio.** A label's `height` is the whole billboard's height, matching the web core, where the padded text canvas puts the glyphs at about 57% of it. Without the factor the same scene shows visibly larger text here, for no reason a reader could guess.
- **Faces are stroked with a hairline pen in their own fill colour**, which hides the seams that otherwise show between adjacent facets of a tessellated cylinder.
- **Lines are painted at exactly the opacity their part carries**, with no extra fading applied here. A second factor at draw time is invisible to `list_parts`, so it made the two renderers disagree about a part they both reported: the cube's wireframe read 0.35 in the web core and 1.0 here. How faint a wireframe is now belongs to the part that owns it, from `shared/spec.json`.
