# preview3d/

The Python package. It ships **two interchangeable renderers** behind one
API — see [The Two Renderers](../RENDERERS.md). Installable with
`pip install git+<repo-url>`; the wheel force-includes the
[Web (folder)](../web/___web.md) bundle and `shared/`, so consumers never
need Node.

Below the widgets sits a pure-Python **model layer** — the direction
grammar, the computed palette, the 24 orientations, the 13-axis/27-seat
model and its scene translation, the switcher and the cinematic scene
generators — shared by both renderers and usable from a plain script with no
GUI at all.

## Files

| File | Tier | One line |
|------|------|----------|
| `__init__.py` | Trivial | package re-exports — the public API surface |
| `resources.py` | Standard | locates and loads the bundled shared data — [about](__about/resources.md) |
| `vectors.py` | Standard | 3-vector / 3×3-matrix arithmetic, no numpy — [about](__about/vectors.md) |
| `jsmath.py` | Standard | `round_half_up`, so Python rounds ties the way JavaScript does — [about](__about/jsmath.md) |
| `directions.py` | Algorithmic | every direction the cube has, from one token grammar — [about](__about/directions.md) · [flow](__flow/directions.md) |
| `axis_colors.py` | Algorithmic | a seat's colour derived from its poles, collision-checked — [about](__about/axis_colors.md) · [flow](__flow/axis_colors.md) |
| `orientations.py` | Algorithmic | the 24 orientations (6 faces × 4 spins) and snap-view angles — [about](__about/orientations.md) · [flow](__flow/orientations.md) |
| `model.py` | Standard | the interpreter of `shared/model_schema.json` — [about](__about/model.md) |
| `model_scene.py` | Standard | model data to a scene spec, the one translation — [about](__about/model_scene.md) |
| `cube_model.py` | Algorithmic | the computed 13-axis, 27-seat cube and its four views — [about](__about/cube_model.md) · [flow](__flow/cube_model.md) |
| `switcher.py` | Standard | register and reading as ordinary part operations — [about](__about/switcher.md) |
| `cinematics.py` | Algorithmic | the Five Stations generator, any axis on demand — [about](__about/cinematics.md) · [flow](__flow/cinematics.md) |
| `widget.py` | Standard | the QWebEngineView wrapper — marshals calls, no rendering logic — [about](__about/widget.md) |
| `light/` | — | the LIGHT renderer (QPainter, software 3D) — [Light (subfolder)](light/___light.md) |

## Connections

### Uses
- [Web (folder)](../web/___web.md) — host page + bundle for the web renderer
- [Light (subfolder)](light/___light.md) — the QPainter renderer, built on this package's model layer
- `shared/spec.json`, `shared/scenes.json`, `shared/model_schema.json` — the values and shipped data both renderers read

### Used by
- [Demo App (folder)](../demoapp/___demoapp.md) — both renderers, switchable live; `build_cube_model`, `READINGS`/`REGISTERS`, `orientation_ids`
- [Tests (folder)](../tests/___tests.md) — parity and regression pins
- Watch Academy (external consumer, not part of this repo) — the Character Cube in its Encyclopedia, and its own Character-Cube exporter built on the Qt-free model layer

## Design Decisions

- **The model layer imports no Qt at all.** `model`, `model_scene`,
  `cube_model`, `directions`, `axis_colors`, `orientations`, `switcher`,
  `cinematics`, `vectors`, `jsmath` and `resources` are pure Python, so a
  consumer's exporter can build and validate a model from a script with no
  GUI — which is exactly what Watch Academy's Character-Cube exporter does.
  Only the two widget layers touch PySide6. (`cinematics.py` reaches into
  `light.camera.Camera` for one piece of pure trigonometry — confirmed
  Qt-free, and reused rather than re-derived.)
- **The model layer exists twice, once per language**, for the same reason
  the timeline does: a website has no Python and a lean Qt app has no
  browser. `tests/test_model_parity.py` runs the two head to head and
  compares their OUTPUT exactly — the palette, the model, the scene spec
  and the 24 orientations — because the answer here is a value rather than
  a picture.
- **The web wrapper only marshals** — specs as JSON, models as JSON, model
  files as base64 bytes. All of its rendering behaviour lives in the JS
  core (`src/`).
- **Both widgets present the same surface**, so a consumer changes one
  constructor call and nothing else. The single unavoidable difference —
  asynchronous `list_parts` on the web side — is absorbed by the LIGHT
  widget accepting a callback as well as returning the list.
- **Neither renderer restates a shared value.** Palette, face order, view
  presets, camera defaults and the animation channel table come from
  `shared/spec.json`; the shipped scenes come from `shared/scenes.json`.
  `tests/test_renderer_parity.py` fails if either source hardcodes a pole
  colour, and `tests/test_animation_parity.py` fails if either carries its
  own copy of the frame rate, speeds or channels.
- **The timeline exists twice, in two languages, and is pinned as such.**
  JS drives playback inside the page; Python drives it with a timer. Every
  shipped scene is played to t = 0, ½ and 1 in both and compared — see
  [Animation Scenes](../SCENES.md).
