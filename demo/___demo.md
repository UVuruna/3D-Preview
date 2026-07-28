# demo/

Standalone browser demo — open `index.html` directly in a browser (no server needed).

## Files

### `index.html` — Demo Page
DESIGN.md-styled page (dark surfaces, indigo accent, glass-free card layout): a viewer stage plus a control panel — axes gizmo / colored cube switching, GLB file load, dark/light background toggle, reset view, and GLB export via `exportGLB()` (the "make a real file" path of root Rule #19).

## Connections

### Uses
- [Web (folder)](../web/___web.md) — loads `../web/preview3d.min.js`

## Design Decisions

- The demo doubles as the **verification harness**: the Playwright recipe in [CLAUDE.md](../CLAUDE.md) screenshots this page headless to prove rendering after changes.
