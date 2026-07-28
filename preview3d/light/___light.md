# light/

The LIGHT renderer: 3D drawn with QPainter — no browser engine, no GPU, no model files. One of the project's two interchangeable back ends; see [The Two Renderers](../../RENDERERS.md) for how to choose.

Only `renderer.py` and `view.py` touch Qt. `vectors`, `scene`, `primitives` and `camera` are pure Python, so the geometry can be exercised without a GUI.

## Files

### `vectors.py` — 3-Vector Helpers
Small module (~70 lines, documented here). Plain tuples and functions rather than numpy: this renderer exists to keep consumers free of heavy dependencies, and its scenes are a few hundred polygons — far below where vectorisation would pay. Includes `basis_from(direction)` (the same orthonormal basis rule the web core uses, with world +Z standing in for world up on a straight top/bottom view) and `rotate_towards`, Rodrigues' formula, which orients a shape built along +Y onto an arbitrary axis exactly as the web core's quaternion does.

### `scene.py` — Scene Graph and Part Addressing
Nodes, faces, segments, labels — and the part operations. See [Light Scene](scene.md).

### `primitives.py` — Parametric Primitives
Builds the same specs the web core builds, into the same named part tree. See [Light Primitives](primitives.md).

### `camera.py` — Orbit Camera and Projection
Target, distance, azimuth, elevation, both projections, and the silhouette fit. See [Light Camera](camera.md).

### `renderer.py` — Project, Sort, Paint
The Qt painting layer. See [Light Renderer](renderer.md).

### `view.py` — The Widget
`Preview3DLightWidget`. See [Light Widget](view.md).

## Connections

### Uses
- [Preview3d Package (folder)](../___preview3d.md) → `resources.py` — reads `shared/spec.json`

### Used by
- [Demo Window](../../demoapp/window.md) — the RENDERER switch
- Consumers that cannot afford Qt WebEngine

## Design Decisions

- **Painter's algorithm, not a depth buffer.** Sort back to front and paint over. Exact for the separated, non-intersecting shapes this renderer is for — and it is why translucency needs no special handling here: with nothing writing depth, a dimmed face simply lets what is behind it through. The cost is that intersecting geometry cannot be ordered correctly, which is stated plainly in RENDERERS.md rather than hidden.
- **The part contract is copied deliberately, the pixels are not.** Paths, visibility, opacity and framing must match the web core exactly (pinned by `tests/test_renderer_parity.py`); shading and text rendering are free to differ, because forcing them to match would freeze both renderers.
- **Values both renderers must agree on live in `shared/spec.json`**, never in this package's source.
