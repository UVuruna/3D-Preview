# preview3d/

The Python package: a PySide6 widget that embeds the web core. Installable with `pip install git+<repo-url>` (the wheel force-includes the [Web (folder)](../web/___web.md) artifact — consumers never need Node).

## Files

### `__init__.py` — Package Entry
Exports `Preview3DWidget`.

### `widget.py` — Preview3D Widget
The QWebEngineView wrapper. See [Preview3D Widget](widget.md).

## Connections

### Uses
- [Web (folder)](../web/___web.md) — host page + bundle, resolved from the installed wheel (`preview3d/web/`) or the repo checkout (`../web/`)

### Used by
- DOMY Watch — axes gizmo with per-arm colors and labels (first consumer)

## Design Decisions

- **The wrapper only marshals** — specs as JSON, model files as base64 bytes. All rendering behavior lives in the JS core; the two APIs mirror each other method-for-method (see project [CLAUDE.md](../CLAUDE.md)).
