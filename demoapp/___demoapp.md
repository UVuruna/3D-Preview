# demoapp/

The PySide6 demo application — the runnable showcase and the integration example. Launched by [Demo Application](../main.md) (`python main.py`).

## Files

### `theme.py` — Theme Tokens & Stylesheet
Small module (~140 lines, mostly one QSS string, documented here). Holds `FONT_FILE`, the `THEME` token dict (DESIGN.md dark surfaces, one indigo accent, radii, spacing) and `build_qss(theme)` which turns the tokens into the application stylesheet. No component anywhere hardcodes a colour or a radius (root Rule #4).

The stylesheet carries one non-obvious rule: `QLabel { background: transparent; }`. Without it every label inherits the `QWidget` background and paints the window surface over whatever card it sits on — see the trap noted in [CLAUDE.md](../CLAUDE.md).

### `window.py` — Demo Window
The window: viewer stage, control panel, camera readout. See [Demo Window](window.md).

### `parts_panel.py` — Parts Panel
The scrollable per-element control list. See [Parts Panel](parts_panel.md).

## Connections

### Uses
- [Preview3D Widget](../preview3d/widget.md) — every control is one call into it
- [Assets (folder)](../assets/___assets.md) — the bundled Inter typeface

### Used by
- [Demo Application](../main.md) — the entry point that builds the window

## Design Decisions

- **Split from `main.py` by responsibility** (root Rule #20): the entry point stays a dozen lines, the window and the parts list are separate cohesive units, and the theme is data.
- **Every button hands focus back to the viewer** (`_with_focus`), so the keyboard bindings keep working after a click without the user re-clicking the stage.
- **The panel mirrors the component's API one-to-one.** Anything the demo can do, a consumer can do with the same call — that is the point of a demo that doubles as documentation.
