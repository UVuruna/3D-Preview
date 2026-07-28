# src/

JavaScript source of the 3D Preview core. Bundled by esbuild (`npm run build`) into `web/preview3d.min.js` as an IIFE with the global name `Preview3D`.

## Files

### `index.js` — Public API
Entry point (~15 lines, documented here). Re-exports `Viewer`, `buildPrimitive`, `makeLabelSprite` and defines `mount(container, options)` — the one call every consumer starts with.

### `viewer.js` — Viewer Container
The container itself: renderer, camera, orbit controls, lighting, content lifecycle, GLB load/export. See [Viewer](viewer.md).

### `primitives.js` — Parametric Primitives
Simple shapes computed from JSON specs (root Rule #19) — currently `axes` and `cube`. See [Parametric Primitives](primitives.md).

### `labels.js` — Text Label Sprites
Small module (~40 lines, documented here): draws text onto a 2D canvas at runtime and mounts it as a camera-facing sprite — no image assets.

```
measure text width with the chosen font
size canvas ← text width + padding, font height + padding
draw centered text onto the canvas
texture ← canvas; sprite material ← texture (transparent)
sprite scale ← worldHeight × canvas aspect ratio
```

All defaults (`LABEL_DEFAULTS`) are overridable per call.

## Connections

### Used by
- [Web (folder)](../web/___web.md) — the built bundle is the shipped form of these sources
- [Demo (folder)](../demo/___demo.md) — drives the bundle from a browser page
- [Preview3d Package (folder)](../preview3d/___preview3d.md) — drives the bundle from PySide6

## Design Decisions

- **Render-on-demand:** the animation loop ticks but only renders when the camera moved or something changed — the GPU is idle while the preview sits still (root Priority A; consumers are always-on desktop apps).
- **IIFE bundle with a global**, not ESM: consumers are a PHP website and a Qt host page — one `<script src>` with zero build tooling on their side beats module plumbing.
- **Defaults-as-config:** every tunable lives in an exported `*_DEFAULTS` object at the top of its module (root Rule #4), overridable per instance/spec.
