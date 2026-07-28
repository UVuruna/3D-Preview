# Demo Application

**Script:** [Demo Application (script)](main.py)

## Purpose

The project's runnable showcase: `python main.py` configures logging, registers the bundled Inter typeface, applies the theme stylesheet and opens the demo window. The window itself lives in [Demo App (folder)](demoapp/___demoapp.md) — this file is the entry point and nothing else (root Rule #20).

Running it is the fastest way to see the component work: every demo scene, loading a glTF/GLB file, view presets and projection, the grid, background modes, per-part visibility and opacity, and the orbit controls by mouse or keyboard.

It doubles as the **integration example**: it is the shortest complete answer to "how do I put this in my Qt app?"

## Connections

### Uses
- [Demo App (folder)](demoapp/___demoapp.md) — `theme.py` (font, tokens, stylesheet) and `window.py` (the window)

## Design Decisions

- **Inter is bundled, not assumed.** DESIGN.md forbids shipping the system default (Segoe) as the primary typeface, and none of the DESIGN.md typefaces are installed on a stock Windows machine — the font file travels with the project and is registered at startup, with a logged error if that fails (root Rule #1).
