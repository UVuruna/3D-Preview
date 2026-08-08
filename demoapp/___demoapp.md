# demoapp/

The PySide6 demo application — the runnable showcase and the integration
example. Launched by the demo entry point (`main.py`, `python main.py`).

## Files

| File | Tier | One line |
|------|------|----------|
| `window.py` | Algorithmic | the window shell: stage, control panel, all wiring — [about](__about/window.md) · [flow](__flow/window.md) |
| `parts_panel.py` | Algorithmic | per-element visibility/opacity list, with SOLO cycling — [about](__about/parts_panel.md) · [flow](__flow/parts_panel.md) |
| `flow_layout.py` | Algorithmic | the wrapping Qt layout the legend strip needs — [about](__about/flow_layout.md) · [flow](__flow/flow_layout.md) |
| `model_panel.py` | Standard | the four owner models, Switcher and orientation stepper — [about](__about/model_panel.md) |
| `theme.py` | Standard | DESIGN.md tokens and the generated QSS — [about](__about/theme.md) |
| `__init__.py` | Trivial | package marker, one docstring line |

## Connections

### Uses
- [Preview3D Widget](../preview3d/__about/widget.md) — every control is one call into it
- [Assets (folder)](../assets/___assets.md) — the bundled Inter typeface

### Used by
- the demo entry point (`main.py`) — the entry point that builds and shows `DemoWindow` (Trivial tier, no own doc — see [README](../README.md))

## Design Decisions

- **Split from `main.py` by responsibility** (THE STRUCTURE LAW (rules/CODE.md)): the entry point stays a few lines of pure wiring, and the window, the parts list and the model controls are separate cohesive units with the theme as data.
- **Every button hands focus back to the viewer** (`_with_focus` / `_pick`), so the keyboard bindings keep working after a click without the user re-clicking the stage.
- **The panel mirrors the component's API one-to-one.** Anything the demo can do, a consumer can do with the same call — that is the point of a demo that doubles as documentation.
- **Nothing inside may set a large window minimum.** The panel scrolls as one column, the legend wraps and lives inside that scroll, and the stage may shrink to a thumbnail — so the window fits in half a screen. Pinned by [tests (folder)](../tests/___tests.md)'s `test_window_minimum_size.py`.
