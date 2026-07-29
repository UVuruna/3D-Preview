# preview3d/

The Python package. It ships **two interchangeable renderers** behind one API — see [The Two Renderers](../RENDERERS.md). Installable with `pip install git+<repo-url>`; the wheel force-includes the [Web (folder)](../web/___web.md) bundle and `shared/`, so consumers never need Node.

## Files

### `__init__.py` — Package Entry
Exports `Preview3DWidget` (web core), `Preview3DLightWidget` (QPainter), the shipped animation scenes via `load_shared_scenes()`, `load_shared_spec()`, and `NO_ANIMATION` (the playback state reported when nothing is loaded).

### `widget.py` — Preview3D Widget
The QWebEngineView wrapper around the web core. See [Preview3D Widget](widget.md).

### `resources.py` — Bundled Data
Small module (~45 lines, documented here). Locates a shipped directory in either of its two documented places — an installed wheel (`preview3d/<name>/`) or a repo checkout (`<project root>/<name>/`) — and loads `shared/spec.json` (`load_shared_spec`) and `shared/scenes.json` (`load_shared_scenes`). One resolver serves the web bundle and both shared files rather than each growing its own copy of the same search.

### `vectors.py` — 3-Vector and 3×3-Matrix Helpers
Plain tuples and functions rather than numpy. See [Vectors](vectors.md).

### `jsmath.py` — Arithmetic Defined to Match JavaScript
Tiny module (~20 lines, documented here). One function, `round_half_up`. Python's built-in `round` breaks ties to EVEN while JavaScript's `Math.round` breaks them UP, so any formula that rounds — a frame index, a colour channel — would put the two implementations one unit apart on an exact tie and nowhere else. Spelled out once here so no module has to remember it (root Rule #5).

### `directions.py` — The Direction Grammar
Every direction the cube has, from one rule. See [Directions](directions.md).

### `axis_colors.py` — The Computed Palette
A seat's colour derived from the poles it lies between, with the collision rule enforced. See [Axis Colours](axis_colors.md).

### `orientations.py` — The 24 Orientations and Snap Views
Computed from 6 up-faces × 4 spins, plus the direction-to-camera-angles snap. See [Orientations](orientations.md).

### `model.py` — Model Schema Validation
The interpreter of `shared/model_schema.json`. See [Model](model.md).

### `model_scene.py` — Model Data to a Scene Spec
The one translation, in plain data. See [Model Scene](model_scene.md).

### `cube_model.py` — The Thirteen-Axis Cube, Computed
The model the four owner views are views OVER. See [Cube Model](cube_model.md).

### `switcher.py` — Register and Reading
Which vocabulary speaks, and which readings are lit. See [Switcher](switcher.md).

### `cinematics.py` — Cinematic Scene Generators
A master rule for a whole family of scenes — `build_five_stations_scene(model, axis_id)` computes the Five Stations descriptor for any of the model's 13 axes, rather than shipping 13 near-identical ones. See [Cinematics](cinematics.md).

### `light/` — The LIGHT Renderer
QPainter software 3D, no browser engine. See [Light (subfolder)](light/___light.md).

## Connections

### Uses
- [Web (folder)](../web/___web.md) — host page + bundle for the web renderer
- `shared/spec.json` — the values both renderers must agree on

### Used by
- [Demo Window](../demoapp/window.md) — both renderers, switchable live
- DOMY Watch — the Character Cube in its Encyclopedia

## Design Decisions

- **The model layer imports no Qt at all.** `model`, `model_scene`, `cube_model`, `directions`, `axis_colors`, `orientations`, `switcher`, `cinematics`, `vectors` and `jsmath` are pure Python, so a consumer's exporter can build and validate a model from a script with no GUI — which is exactly what DOMY Watch's Character-Cube exporter does. Only the two widget layers touch PySide6. (`cinematics.py` reaches into `light.camera.Camera` for one piece of pure trigonometry — confirmed Qt-free, and reused rather than re-derived.)
- **The model layer exists twice, once per language**, for the same reason the timeline does: a website has no Python and a lean Qt app has no browser. `tests/test_model_parity.py` runs the two head to head and compares their OUTPUT exactly — the palette, the model, the scene spec and the 24 orientations — because the answer here is a value rather than a picture.
- **The web wrapper only marshals** — specs as JSON, models as JSON, model files as base64 bytes. All of its rendering behaviour lives in the JS core.
- **Both widgets present the same surface**, so a consumer changes one constructor call and nothing else. The single unavoidable difference — asynchronous `list_parts` on the web side — is absorbed by the LIGHT widget accepting a callback as well as returning the list.
- **Neither renderer restates a shared value.** Palette, face order, view presets, camera defaults and the animation channel table come from `shared/spec.json`; the shipped scenes come from `shared/scenes.json`. `tests/test_renderer_parity.py` fails if either source hardcodes a pole colour, and `tests/test_animation_parity.py` fails if either carries its own copy of the frame rate, speeds or channels.
- **The timeline exists twice, in two languages, and is pinned as such.** JS drives playback inside the page; Python drives it with a timer. Every shipped scene is played to t = 0, ½ and 1 in both and compared — see [Animation Scenes](../SCENES.md).
