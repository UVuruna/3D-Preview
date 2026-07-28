# CLAUDE.md — 3D Preview

Inherits all rules from the root [CLAUDE.md](../../CLAUDE.md). Project-specific guidance below.

## What This Is

An embeddable 3D viewer **component** (library, not an installable app): a Three.js core bundled by esbuild, consumed by websites (script tag) and by Python GUIs (PySide6 `Preview3DWidget` over `QWebEngineView`). See [README](README.md) for the stack rationale (Rule #21).

**Because it is a library, the installable-app pipeline does not apply:** no `setup/` folder, no NSIS build, no Rule #23 self-update, no Rule #24 auto-release of installers. Consumers take the committed `web/preview3d.min.js` or `pip install git+` the repo.

## Ground Rules

- **One rendering implementation.** All display logic lives in `src/`. The Python wrapper only marshals calls (JSON specs, base64 model bytes) — never add rendering behavior on the Python side.
- **Primitives are computed (root Rule #19).** New simple shapes (book, window screen, …) are added as parametric builders in `src/primitives.js` — never as stored model files. `exportGLB()` exists for the rare case a real file is needed.
- **`web/preview3d.min.js` is a build artifact that IS committed** — consumers must not need Node. After ANY change in `src/`, run `npm run build` and commit the refreshed bundle together with the source change.
- **JS API and Python API move together.** A new JS Viewer method gets its snake_case mirror in `preview3d/widget.py` in the same session, and both docs are updated.

## Commands

```bash
npm install        # once
npm run build      # src/ → web/preview3d.min.js
```

## Verification Recipe

Rendering claims require screenshots (root Guideline #1):

- **Web:** Playwright headless — open `demo/index.html`, wait ~1.5s, screenshot, assert no console errors.
- **Widget:** short PySide6 script — `Preview3DWidget`, `show_axes(...)`, `QTimer.singleShot(3500, grab)`, save `widget.grab()` to PNG and inspect it.

JS console output is forwarded to Python `logging` by the widget, so JS errors surface in the host app's log (Rule #1).

## Consumers

- **DOMY Watch** — axes gizmo, 6 arms with per-arm color + label (the founding use case).
- **Vaske Komarnici** (planned) — parametric window-screen preview; the `screen` primitive does not exist yet and should be designed against that site's product configurator when integration starts.
