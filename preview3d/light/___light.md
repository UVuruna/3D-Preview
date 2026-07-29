# light/

The LIGHT renderer: 3D drawn with QPainter — no browser engine, no GPU, no model files. One of the project's two interchangeable back ends; see [The Two Renderers](../../RENDERERS.md) for how to choose.

Only `renderer.py` and `view.py` touch Qt. `scene`, `primitives`, `camera`, `animation` and `model_view` are pure Python, so the geometry, the timeline and the model half can be exercised without a GUI. The vector maths moved up to the package root as [Vectors](../vectors.md) once the pure model layer needed it too.

## Files

### `scene.py` — Scene Graph and Part Addressing
Nodes, faces, segments, labels — and the part operations. See [Light Scene](scene.md).

### `primitives.py` — Parametric Primitives
Builds the same specs the web core builds, into the same named part tree. See [Light Primitives](primitives.md).

### `camera.py` — Orbit Camera and Projection
Target, distance, azimuth, elevation, both projections, and the silhouette fit. See [Light Camera](camera.md).

### `animation.py` — Timeline
Keyframe evaluation and the playback clock, mirroring the web core's timeline. See [Light Timeline](animation.md).

### `model_view.py` — The Model Layer's Viewer-Side Operations
Validate a model, build its content, resolve a view and an orientation. No Qt. See [Light Model View](model_view.md).

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
