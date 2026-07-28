# Demo Window

**Script:** [Demo Window (script)](window.py)

## Purpose

The demo application's window: the viewer stage with the keyboard legend beneath it, and a control panel exposing every capability of the component — scenes, view presets, projection, grid, background, a live camera readout and the parts list.

## Connections

### Uses
- [Preview3D Widget](../preview3d/widget.md) — one call per control
- [Parts Panel](parts_panel.md) — the PARTS section
- [Demo App (folder)](___demoapp.md) → `theme.py` — spacing tokens

### Used by
- [Demo Application](../main.md)

## Config

Module-level constants (root Rule #4):

| Constant | Contents |
|----------|----------|
| `RENDERERS` | the two back ends, their labels and whether each can load files |
| `WINDOW` | title, start size, and the minimum the layout must be able to reach |
| `PANEL_WIDTH` / `STAGE_MINIMUM` | control-panel width; how small the 3D view may get |
| `DEMO_SCENES` | `Axes gizmo`, `Compass axes` (multi-label arms), `Cube`, `Cube + core` — parametric specs, not model files (root Rule #19) |
| `VIEW_BUTTONS` / `PROJECTIONS` | the preset and projection toggles |
| `BACKGROUNDS` | the cycle: Dark → Light → Transparent |
| `CONTROLS_LEGEND` | the key/action strip under the stage |
| `MODEL_FILTER` | file-dialog filter for loadable models |

The scenes deliberately omit arm colours and pass `colors: "poles"` for the cube, so the palette comes from the engine's own table and is never restated here.

## Classes

### DemoWindow

#### Methods
- `_build_header()` / `_build_stage_column()` / `_build_panel()`: layout construction
- `_toggle_row(...)`: builds a grid of checkable buttons for a preset family and returns the `QButtonGroup`
- `set_renderer(key)`: swap the widget in the stage and replay the current scene, background and part panel onto it, so the two renderers can be compared on the very same content
- `_with_focus(action, *args)`: run a control's action, then return keyboard focus to the viewer
- `_load_model()`: file dialog → `load_model()`; clears the scene selection, since what is shown is no longer a demo scene
- `_cycle_background()` / `_apply_background()`: step through `BACKGROUNDS`, keeping the button label in sync
- `_on_camera_changed(state)`: the readout, the toggle states, and the parts reload — see below

## Camera Readout & Reload

One signal drives everything that reflects viewer state:

```
ON camera_changed(state):
    readout ← azimuth, elevation, distance, view · projection, grid cell size
    sync the VIEW and PROJECTION toggles to state.view / state.projection
    sync the GRID button to state.grid
    IF state.contentVersion changed → parts.reload()
```

The content-version check is why the parts list is correct after loading a **file**: model loading is asynchronous, so "right after calling `load_model`" is not a moment at which the parts exist. The viewer bumps the version when content is actually in place, and the panel reloads then.

## Design Decisions

- **The stage card pads the web view by one spacing unit.** A native web view always paints its own rectangle square, so without the inset its corners would cover the card's rounded ones.
- **The keyboard legend lives in the scrolling panel, not under the stage.** Under the stage it wraps onto eight rows in a narrow window and eats the height the 3D view needs — and the view is the point of the window while the legend is reference material.
- **The whole panel scrolls as one column.** Stacked unscrolled, its sections set a ~770 px floor on the window's height; a second scroll area just for the parts would give the user two scrollbars for one list.
- **Toggle states are never set optimistically.** A button reflects what the viewer reported, so a key press (`P`, `G`, Shift+arrows) updates the buttons exactly as a click would.
