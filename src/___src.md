# src/

JavaScript source of the WEB renderer's 3D Preview core. Bundled by esbuild (`npm run build`) into `web/preview3d.min.js` as an IIFE with the global name `Preview3D` — see `package.json`'s `build` script.

## Files

| File | Tier | One line |
|------|------|----------|
| `index.js` | Trivial | public API — re-exports every module and defines `mount(container, options)`, the one call every consumer starts with |
| `viewer.js` | Algorithmic | the container — renderer, both cameras, orbit controls, lighting, content lifecycle, framing, grid, animation playback — [about](__about/viewer.md) · [flow](__flow/viewer.md) |
| `animation.js` | Algorithmic | the Timeline — keyframes and easing over flat parameters, plus the playback clock — [about](__about/animation.md) · [flow](__flow/animation.md) |
| `primitives.js` | Algorithmic | parametric shapes computed from JSON specs, named parts — [about](__about/primitives.md) · [flow](__flow/primitives.md) |
| `parts.js` | Standard | show, hide, dim, solo and remove the individual elements of whatever is shown — [about](__about/parts.md) |
| `directions.js` | Algorithmic | the direction token grammar — every direction the cube has, from one rule — [about](__about/directions.md) · [flow](__flow/directions.md) |
| `axiscolors.js` | Algorithmic | the computed palette and the collision rule — [about](__about/axiscolors.md) · [flow](__flow/axiscolors.md) |
| `orientations.js` | Algorithmic | the 24 orientations, and snap-view angles — [about](__about/orientations.md) · [flow](__flow/orientations.md) |
| `model.js` | Algorithmic | the schema interpreter for `shared/model_schema.json` — [about](__about/model.md) · [flow](__flow/model.md) |
| `modelscene.js` | Standard | model data to a scene spec — the one translation, in plain data — [about](__about/modelscene.md) |
| `cubemodel.js` | Standard | the thirteen-axis cube, computed — 13 axes, 27 seats, 4 views — [about](__about/cubemodel.md) |
| `switcher.js` | Standard | which vocabulary speaks and which readings are lit, as flat part operations — [about](__about/switcher.md) |
| `cinematics.js` | Algorithmic | cinematic scene generators — the Five Stations for any of the 13 axes — [about](__about/cinematics.md) · [flow](__flow/cinematics.md) |
| `modelview.js` | Standard | the model layer's viewer-side operations, split out so the container stays a container — [about](__about/modelview.md) |
| `views.js` | Trivial | the seven standard view presets and the cycle order |
| `grid.js` | Standard | the optional ground grid, sized to the content — [about](__about/grid.md) |
| `keyboard.js` | Standard | key bindings, each one a thin call into the Viewer's public API — [about](__about/keyboard.md) |
| `labels.js` | Standard | text label sprites drawn onto a canvas at runtime, no image assets — [about](__about/labels.md) |

`directions.js`, `axiscolors.js`, `orientations.js`, `model.js`, `modelscene.js`, `cubemodel.js`, `switcher.js` and `cinematics.js` — **the model layer** — exist twice, once per language, for the reason the timeline does: a website has no Python and a lean Qt app has no browser. Each reads the same `shared/spec.json` (and `shared/model_schema.json`), and `tests/test_model_parity.py` runs the two head to head and compares their output exactly. Every one of the eight has a mirror doc linked from its own `__about/` page — the mirror is the SAME logic in the other language, function for function, not a different design.

## Connections

### Uses
- `three` (npm) — the WEB renderer's engine; bundled in, no runtime dependency for a consumer
- `shared/spec.json`, `shared/scenes.json`, `shared/model_schema.json` — the values and shipped scenes both renderers must agree on

### Used by
- [Web (folder)](../web/___web.md) — the built bundle (`preview3d.min.js`) is the shipped form of these sources
- [Demo (folder)](../demo/___demo.md) — drives the bundle from a browser page
- [Preview3d Package (folder)](../preview3d/___preview3d.md) — drives the bundle from PySide6 (`Preview3DWidget`)

## Design Decisions

- **Render-on-demand:** the animation loop ticks but only renders when the camera moved or something changed — the GPU is idle while the preview sits still (root Priority A; consumers are always-on desktop apps).
- **IIFE bundle with a global**, not ESM: consumers are a PHP website and a Qt host page — one `<script src>` with zero build tooling on their side beats module plumbing.
- **Defaults-as-config:** every tunable lives in an exported `*_DEFAULTS` object at the top of its module (root Rule #4), overridable per instance/spec.
- **One palette table for all shapes:** the six pole colours live once in `shared/spec.json` and dress both the axes gizmo and the cube's faces — a colour belongs to a DIRECTION, not to the shape pointing that way (root Rule #19). Every colour beyond those six is COMPUTED from them (`axiscolors.js`); a hardcoded derived hex fails `tests/test_axis_colors.py`.
- **A direction is a grammar, not a table.** Six hardcoded entries could not express the cube's six edge axes or four vertex diagonals at all — which was the one thing a 3D previewer was commissioned to show.
- **`viewer.js` is 912 lines — inside root Rule #20's "smell" band (500–1,000), not over the 1,000-line violation threshold.** Its responsibilities (renderer/camera lifecycle, part delegation, animation playback, model/switcher plumbing) are already partly extracted into `parts.js`, `modelview.js`, `grid.js` and `keyboard.js`; what remains is still one cohesive container. Flagged here rather than split unilaterally — a further split is a real refactor (new module boundaries, every caller updated) out of scope for this documentation migration.
