# Preview3D Widget

**Script:** [Preview3D Widget (script)](widget.py)

## Purpose

`Preview3DWidget` — a drop-in PySide6 widget: any Qt layout gets a 3D preview with orbit controls by constructing one object and calling one method. Internally a `QWebEngineView` loading the bundled host page; every public method runs the mirrored JS Viewer call via `runJavaScript`.

## Connections

### Uses
- [Web (folder)](../web/___web.md) — host page (`index.html`) + bundle
- [Viewer](../src/viewer.md) — the JS object every method drives

### Used by
- Host applications (DOMY Watch first) — plain Qt widget, no special integration

## Classes

### _ConsolePage
`QWebEnginePage` subclass forwarding the JS console into Python `logging` (`preview3d.widget` logger) — a JS error inside the viewer lands in the host app's log (root Rule #1).

### Preview3DWidget

#### Attributes
- `_ready` / `_pending`: calls made before the page finishes loading are queued and flushed on `loadFinished` — construct-and-immediately-show works without races

#### Methods
- `show_scene(spec)`: any parametric spec, passed through as JSON — see [Parametric Primitives](../src/primitives.md)
- `show_axes(arms=None, arm_length=1.0)`: convenience for the axes gizmo; each arm `{"axis": "+x".."-z", "color": hex, "label": str}`
- `load_model(path)`: local glTF/GLB — bytes are read in Python and handed to JS as base64, because Chromium refuses `fetch()` on `file://` URLs
- `set_background(color)`: CSS hex or `"transparent"` (also clears the Qt page background → see-through widget)
- `reset_view()`: re-frame the content

## Design Decisions

- **Bundle resolution, two documented locations:** installed wheel → `preview3d/web/`; repo checkout → `../web/`. Anything else raises `FileNotFoundError` with the fix (`npm run build`) — no silent blank widget.
- **`LocalContentCanAccessFileUrls/RemoteUrls`** are enabled so the local host page may also load http(s) model URLs when a consumer passes one through `show_scene({type: 'model', url})`.
