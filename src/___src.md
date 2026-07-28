# src/

JavaScript source of the 3D Preview core. Bundled by esbuild (`npm run build`) into `web/preview3d.min.js` as an IIFE with the global name `Preview3D`.

## Files

### `index.js` — Public API
Entry point (~20 lines, documented here). Re-exports `Viewer`, `buildPrimitive`, `makeLabelSprite`, the pole colour table, the view presets and the tunable defaults of every module, and defines `mount(container, options)` — the one call every consumer starts with.

### `viewer.js` — Viewer Container
The container itself: renderer, the two cameras, orbit controls, lighting, content lifecycle, framing, grid, camera-state events, and the part operations a host calls. See [Viewer](viewer.md).

### `primitives.js` — Parametric Primitives
Simple shapes computed from JSON specs (root Rule #19), with named parts. See [Parametric Primitives](primitives.md).

### `parts.js` — Part Addressing
Show, hide, dim, solo and remove the individual elements of whatever is being shown. See [Parts](parts.md).

### `views.js` — View Presets
Small data module (~40 lines, documented here). The seven standard directions and the order they cycle in:

| Preset | Direction (from content toward camera) |
|--------|----------------------------------------|
| `iso` | `(1, 1, 1)` — the body diagonal; the only direction whose cube silhouette is a hexagon |
| `front` / `back` | `(0, 0, ±1)` |
| `right` / `left` | `(±1, 0, 0)` |
| `top` / `bottom` | `(0, ±1, 0)` |

`stepView(current, ±1)` walks that order; `FREE_VIEW` (`'free'`) is what the viewer reports once the user has orbited off a preset. An unknown name throws with the list of valid ones (root Rule #1).

### `grid.js` — Ground Grid
Small module (~50 lines, documented here). Builds an optional reference plane sized to the content instead of a fixed helper that is wrong for anything but a unit cube.

```
box      ← bounds of the content
footprint← max(width, depth, height / 2)
span     ← footprint × spanFactor
step     ← round span / targetCells UP to the nearest 1, 2 or 5 × 10ⁿ
grid     ← GridHelper(step × divisions, divisions), centred under the content,
           sitting on its floor, depth-write off so it never occludes the model
```

The rounded step is why the camera readout can honestly say "0.5 per cell". The grid lives in the scene but **outside** the content group, so it never affects framing.

### `keyboard.js` — Key Bindings
Small module (~60 lines, documented here). Each binding is one call into the Viewer's public API, so a GUI button and a key do the same thing.

| Key | Action |
|-----|--------|
| Arrows | Orbit in steps — move around the model |
| Ctrl + Arrows | Pan — move the point being looked at |
| Shift + ← / → | Previous / next view preset |
| Shift + ↑ / ↓ | Top / bottom view |
| `+` / `−` | Zoom |
| `P` · `G` · `R` | Projection · grid · reset |

Bound to the **container**, not to `window`: a viewer embedded in someone else's page must not swallow that page's arrow keys. Clicking the viewer focuses it; the bundled host page focuses it on load.

### `labels.js` — Text Label Sprites
Small module (~40 lines, documented here): draws text onto a 2D canvas at runtime and mounts it as a camera-facing sprite — no image assets.

```
measure text width with the chosen font
size canvas ← text width + padding, font height + padding
draw centered text onto the canvas
texture ← canvas; sprite material ← texture (transparent)
sprite scale ← worldHeight × canvas aspect ratio
```

## Connections

### Used by
- [Web (folder)](../web/___web.md) — the built bundle is the shipped form of these sources
- [Demo (folder)](../demo/___demo.md) — drives the bundle from a browser page
- [Preview3d Package (folder)](../preview3d/___preview3d.md) — drives the bundle from PySide6

## Design Decisions

- **Render-on-demand:** the animation loop ticks but only renders when the camera moved or something changed — the GPU is idle while the preview sits still (root Priority A; consumers are always-on desktop apps).
- **IIFE bundle with a global**, not ESM: consumers are a PHP website and a Qt host page — one `<script src>` with zero build tooling on their side beats module plumbing.
- **Defaults-as-config:** every tunable lives in an exported `*_DEFAULTS` object at the top of its module (root Rule #4), overridable per instance/spec.
- **One palette table for all shapes:** the six pole colours live once in `primitives.js` and dress both the axes gizmo and the cube's faces — a colour belongs to a DIRECTION, not to the shape pointing that way (root Rule #19).
