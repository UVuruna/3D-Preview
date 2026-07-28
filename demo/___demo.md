# demo/

Standalone browser demo — open `index.html` directly in a browser (no server needed).

## Files

### `index.html` — Demo Page
DESIGN.md-styled page (dark surfaces, indigo accent, glass-free card layout): a viewer stage plus a control panel — axes gizmo / colored cube switching, GLB file load, animation playback, view presets, projection, grid, background cycling, a live camera readout, a parts list, and GLB export via `exportGLB()` (the "make a real file" path of root Rule #19).

The ANIMATION section plays `Preview3D.SCENES` — the descriptors from `shared/scenes.json`, the very same ones the Qt demo plays through the Python renderers, with the same transport: restart, single-frame stepping, play/pause, jump-to-end, a scrub slider and 0.5× / 1× / 2×. See [Animation Scenes](../SCENES.md).

## Connections

### Uses
- [Web (folder)](../web/___web.md) — loads `../web/preview3d.min.js`

## Design Decisions

- The demo doubles as the **verification harness**: the Playwright recipe in [CLAUDE.md](../CLAUDE.md) screenshots this page headless to prove rendering after changes.
