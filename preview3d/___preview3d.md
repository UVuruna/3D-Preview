# preview3d/

The Python package. It ships **two interchangeable renderers** behind one API — see [The Two Renderers](../RENDERERS.md). Installable with `pip install git+<repo-url>`; the wheel force-includes the [Web (folder)](../web/___web.md) bundle and `shared/`, so consumers never need Node.

## Files

### `__init__.py` — Package Entry
Exports `Preview3DWidget` (web core) and `Preview3DLightWidget` (QPainter).

### `widget.py` — Preview3D Widget
The QWebEngineView wrapper around the web core. See [Preview3D Widget](widget.md).

### `resources.py` — Bundled Data
Small module (~35 lines, documented here). Locates a shipped directory in either of its two documented places — an installed wheel (`preview3d/<name>/`) or a repo checkout (`<project root>/<name>/`) — and loads `shared/spec.json`. One resolver serves the web bundle and the shared spec rather than each growing its own copy of the same search.

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

- **The web wrapper only marshals** — specs as JSON, model files as base64 bytes. All of its rendering behaviour lives in the JS core.
- **Both widgets present the same surface**, so a consumer changes one constructor call and nothing else. The single unavoidable difference — asynchronous `list_parts` on the web side — is absorbed by the LIGHT widget accepting a callback as well as returning the list.
- **Neither renderer restates a shared value.** Palette, face order, view presets and camera defaults come from `shared/spec.json`; `tests/test_renderer_parity.py` fails if either source hardcodes a pole colour.
