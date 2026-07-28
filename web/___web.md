# web/

The shipped web artifact: the minimal host page plus the built bundle. This folder is what consumers actually take.

## Files

### `index.html` — Host Page
Minimal full-viewport page that mounts one viewer as the global `viewer`. Loaded by the PySide6 widget (`QUrl.fromLocalFile`) and usable as an embed reference. Transparent page background so `setBackground('transparent')` produces a genuinely see-through widget.

### `preview3d.min.js` — Built Bundle
**Computed artifact** (`npm run build` from [Source (folder)](../src/___src.md)) that is nevertheless **committed**: consumers — a PHP site, a pip-installed wheel — must not need Node. Regenerate and commit it together with every `src/` change. IIFE, global name `Preview3D`, ~615 KB (Three.js included, no external requests at runtime).

## Connections

### Uses
- [Source (folder)](../src/___src.md) — bundle input

### Used by
- [Preview3d Package (folder)](../preview3d/___preview3d.md) — loads `index.html` into QWebEngineView; the wheel force-includes this folder
- [Demo (folder)](../demo/___demo.md) — loads the bundle with its own page and controls
- Websites — copy `preview3d.min.js`, add a container div and two script lines (see [README](../README.md))

## Design Decisions

- **Errors stay visible (root Rule #1):** the host page routes `unhandledrejection` to `console.error`, and the widget forwards the JS console into Python `logging` — an async model-load failure lands in the host app's log, never silently vanishes.
