# preview3d/light/

The LIGHT renderer: 3D drawn with QPainter — no browser engine, no GPU, no model files. One of the project's two interchangeable back ends; see [RENDERERS.md](../../RENDERERS.md) for how to choose.

Only `renderer.py` and `view.py` touch Qt. `scene`, `primitives`, `camera`, `animation` and `model_view` are pure Python, so the geometry, the timeline and the model half can be exercised without a GUI. The vector maths lives at the package root (`vectors.py`) since the pure model layer needed it too, not duplicated here.

## Files

| File | Tier | One line |
|------|------|----------|
| `__init__.py` | Trivial | re-exports `Preview3DLightWidget` from `view.py` |
| `scene.py` | Standard | node tree (`Node`, `Face`, `Segment`, `Label`) and part addressing — [about](__about/scene.md) |
| `model_view.py` | Standard | the model layer's viewer-side operations: validate, build content, resolve a view/orientation — [about](__about/model_view.md) |
| `view.py` | Standard | `Preview3DLightWidget` — the QWidget shell, orchestrates the modules below (600 lines, near the smell threshold; splitting is out of scope here) — [about](__about/view.md) |
| `primitives.py` | Algorithmic | parametric shape builders — [about](__about/primitives.md) · [flow](__flow/primitives.md) |
| `camera.py` | Algorithmic | orbit camera, projection and silhouette-fit framing — [about](__about/camera.md) · [flow](__flow/camera.md) |
| `animation.py` | Algorithmic | keyframe evaluation and the fixed-timestep playback clock — [about](__about/animation.md) · [flow](__flow/animation.md) |
| `renderer.py` | Algorithmic | flatten → project → near-cull → sort → paint pipeline — [about](__about/renderer.md) · [flow](__flow/renderer.md) |

## Connections

### Uses
- [Preview3d Package (folder)](../___preview3d.md) — `resources.py` (reads `shared/spec.json`), `vectors.py`, `directions.py`, `model.py`, `model_scene.py`, `orientations.py`, `switcher.py`

### Used by
- [Preview3d Package (folder)](../___preview3d.md) — re-exports `Preview3DLightWidget` and `animation.NO_ANIMATION` as public API
- Demo Window (`demoapp/window.py`) — the RENDERER switch
- Consumers that cannot afford Qt WebEngine

## Design Decisions

- **Painter's algorithm, not a depth buffer.** Sort back to front and paint over. Exact for the separated, non-intersecting shapes this renderer is for — and it is why translucency needs no special handling here: with nothing writing depth, a dimmed face simply lets what is behind it through. The cost is that intersecting geometry cannot be ordered correctly, which is stated plainly in [RENDERERS.md](../../RENDERERS.md) rather than hidden.
- **The part contract is copied deliberately, the pixels are not.** Paths, visibility, opacity and framing must match the web core exactly (pinned by `tests/test_renderer_parity.py`); shading and text rendering are free to differ, because forcing them to match would freeze both renderers.
- **Values both renderers must agree on live in `shared/spec.json`**, never in this package's source.
- **Only `renderer.py` and `view.py` import Qt.** `scene.py`, `primitives.py`, `camera.py`, `animation.py` and `model_view.py` are plain Python, which is what lets the geometry, the timeline and the model half be tested headless.
- **Tier calls in this folder:** `scene.py` and `model_view.py` read as Standard rather than Algorithmic — each is a set of short, direct operations (find/set by path; validate/build/resolve) with no multi-step algorithm of its own. The genuinely multi-step tree walk that propagates opacity and applies transforms down the node tree lives in `renderer.py`'s `iter_world_geometry`, not in `scene.py` — a distinction worth stating explicitly because it is easy to assume the data-holder owns the algorithm that walks it.
