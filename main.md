# Demo Application

**Script:** [Demo Application (script)](main.py)

## Purpose

The project's runnable showcase: `python main.py` opens a small PySide6 window with the viewer on the left and a control panel on the right, so the component can be seen working — every built-in demo scene, loading a glTF/GLB file from disk, the background modes, and the orbit controls (rotate / zoom / pan).

It doubles as the **integration example**: it is the shortest complete answer to "how do I put this in my Qt app?"

## Connections

### Uses
- [Preview3D Widget](preview3d/widget.md) — the embedded widget; every panel button calls exactly one of its methods
- [Parametric Primitives](src/primitives.md) — the demo scene specs
- `assets/fonts/Inter.ttf` — see [Assets (folder)](assets/___assets.md)

## Config

Everything tunable sits in module-level constants (root Rule #4):

| Constant | Contents |
|----------|----------|
| `WINDOW` | title and start size |
| `THEME` | DESIGN.md tokens — surfaces, border, text, accent, radii, spacing |
| `DEMO_SCENES` | the scene buttons: `Axes gizmo`, `Compass axes` (labeled 6-arm gizmo), `Cube` (per-face colors) — parametric specs, not model files (root Rule #19) |
| `BACKGROUNDS` | the cycle: Dark → Light → Transparent |
| `CONTROLS_LEGEND` | the key/action rows shown in the panel |
| `MODEL_FILTER` | file-dialog filter for loadable models |

`build_qss(theme)` turns the token dict into the application stylesheet.

## Classes

### DemoWindow

#### Methods
- `_build_header()` / `_build_stage()` / `_build_panel()`: layout construction
- `_load_model()`: file dialog → `Preview3DWidget.load_model()`; clears the scene button selection because the shown content is no longer one of the demo scenes
- `_cycle_background()` / `_apply_background()`: step through `BACKGROUNDS`, keeping the button label in sync with the active mode

## Design Decisions

- **The stage card pads the web view by one spacing unit.** A native web view always paints its own rectangle square, so without the inset its corners would cover the card's rounded ones.
- **Inter is bundled, not assumed.** DESIGN.md forbids shipping the system default (Segoe) as the primary typeface, and none of the DESIGN.md typefaces are installed on a stock Windows machine — the font file travels with the project and is registered at startup via `QFontDatabase.addApplicationFont`, with a logged error if that fails (root Rule #1).
- **Adding a demo scene is one entry in `DEMO_SCENES`** — no new widget code.
