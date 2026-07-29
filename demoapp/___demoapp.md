# demoapp/

The PySide6 demo application — the runnable showcase and the integration example. Launched by [Demo Application](../main.md) (`python main.py`).

## Files

### `theme.py` — Theme Tokens & Stylesheet
Small module (~140 lines, mostly one QSS string, documented here). Holds `FONT_FILE`, the `THEME` token dict (DESIGN.md dark surfaces, one indigo accent, radii, spacing) and `build_qss(theme)` which turns the tokens into the application stylesheet. No component anywhere hardcodes a colour or a radius (root Rule #4).

The stylesheet carries one non-obvious rule: `QLabel { background: transparent; }`. Without it every label inherits the `QWidget` background and paints the window surface over whatever card it sits on — see the trap noted in [CLAUDE.md](../CLAUDE.md).

### `flow_layout.py` — Wrapping Layout
Small module (~80 lines, documented here). Qt ships no wrapping layout, and a `QHBoxLayout` reports the **sum** of its items as its minimum width — which is how a single row of legend chips came to dictate a 1649 px minimum window. `FlowLayout` places items left to right and wraps at the right edge; its minimum is the widest **single** item, so the strip can collapse to one item per row.

```
FOR EACH item:
    IF x + item width > right edge AND the row is not empty:
        x ← left edge;  y ← y + row height + spacing;  row height ← 0
    place item at (x, y)
    x ← x + item width + spacing
    row height ← max(row height, item height)
```

`flow_size_policy()` returns the size policy a hosting widget needs for the layout's height-for-width to be honoured — without it Qt asks for the height once, at the wrong width.

### `window.py` — Demo Window
The window: viewer stage, control panel, animation transport, camera readout. See [Demo Window](window.md).

### `parts_panel.py` — Parts Panel
The scrollable per-element control list. See [Parts Panel](parts_panel.md).

### `model_panel.py` — Model Controls
The four owner models, the register/reading Switcher and the 24-orientation stepper. See [Model Panel](model_panel.md).

## Connections

### Uses
- [Preview3D Widget](../preview3d/widget.md) — every control is one call into it
- [Assets (folder)](../assets/___assets.md) — the bundled Inter typeface

### Used by
- [Demo Application](../main.md) — the entry point that builds the window

## Design Decisions

- **Split from `main.py` by responsibility** (root Rule #20): the entry point stays a dozen lines, and the window, the parts list and the model controls are separate cohesive units with the theme as data.
- **Every button hands focus back to the viewer** (`_with_focus`), so the keyboard bindings keep working after a click without the user re-clicking the stage.
- **The panel mirrors the component's API one-to-one.** Anything the demo can do, a consumer can do with the same call — that is the point of a demo that doubles as documentation.
- **Nothing inside may set a large window minimum.** The panel scrolls as one column, the legend wraps and lives inside that scroll, and the stage may shrink to a thumbnail — so the window fits in half a screen. Pinned by `tests/test_window_minimum_size.py`.
