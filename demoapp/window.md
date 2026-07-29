# Demo Window

**Script:** [Demo Window (script)](window.py)

## Purpose

The demo application's window: the viewer stage and a control panel exposing every capability of the component — the renderer switch, scenes, animation playback, view presets, projection, grid, background, a live camera readout, the parts list and the keyboard legend.

## Connections

### Uses
- [Preview3D Widget](../preview3d/widget.md) — one call per control
- [Parts Panel](parts_panel.md) — the PARTS section
- [Model Panel](model_panel.md) — the MODEL, REGISTER, READING and ORIENTATION sections
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
| `ANIMATIONS` / `SPEEDS` | read from `shared/scenes.json` and `shared/spec.json` — the demo plays the very descriptors both renderers ship with, and never restates a scene or a speed |
| `TRANSPORT` / `SCRUB_STEPS` | the five playback buttons and the scrub slider's resolution |
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
- `_build_animation(layout)`: the ANIMATION section — scene picker, transport, scrub, speed and playback readout
- `set_renderer(key)`: swap the widget in the stage and replay the current content, animation, background and part panel onto it — including whether it was playing — so the two renderers can be compared on the very same scene mid-flight
- `_with_focus(action, *args)`: run a control's action, then return keyboard focus to the viewer
- `_load_model()`: file dialog → `load_model()`; clears the scene selection, since what is shown is no longer a demo scene
- `_play_animation(descriptor)`: load the scene's own content if it declares one, then `set_animation` + `play_animation`. `content.type == "model"` (a HOST CONVENTION, not a timeline channel — [Animation Scenes](../SCENES.md#content)) shows the demo MODEL and one of its views through `self.model.show_model(...)` instead of a bare primitive spec — Blindness and Five Stations need the 27-seat model
- `_play_generalized_five_stations()`: the Five Stations "generalize control" (PLAN.md) — regenerates `build_five_stations_scene(DEMO_MODEL, axis_id)` for whichever axis the combo box selects and plays it through the same `_play_animation` path, rather than shipping 13 near-identical scenes (root Rule #19)
- `_cycle_background()` / `_apply_background()`: step through `BACKGROUNDS`, keeping the button label in sync
- `_on_camera_changed(state)` / `_on_animation_changed(state)`: the readouts, the toggle states, and the parts reload — see below

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

## Playback Readout

```
ON animation_changed(state):
    enable / disable the transport and the scrub  ← state.scene is not None
    the play button reads "Pause" while playing
    move the scrub to state.progress             (guarded — see below)
    sync the SPEED toggle; write scene · time · frame
```

The scrub slider is both an input and a readout, so a guard flag distinguishes the panel's own `setValue` from the user dragging it; without it the two would be indistinguishable and every report would seek.

## Design Decisions

- **The stage card pads the web view by one spacing unit.** A native web view always paints its own rectangle square, so without the inset its corners would cover the card's rounded ones.
- **The keyboard legend lives in the scrolling panel, not under the stage.** Under the stage it wraps onto eight rows in a narrow window and eats the height the 3D view needs — and the view is the point of the window while the legend is reference material.
- **The whole panel scrolls as one column.** Stacked unscrolled, its sections set a ~770 px floor on the window's height; a second scroll area just for the parts would give the user two scrollbars for one list.
- **Toggle states are never set optimistically.** A button reflects what the viewer reported, so a key press (`P`, `G`, Shift+arrows) updates the buttons exactly as a click would. The transport is the same: the play button reads "Pause" because the viewer says it is playing, not because it was clicked.
- **Picking content clears the animation selection.** The viewer itself drops the scene when new content is shown (a scene is written against specific parts), so the panel only has to un-check the button and let the report that follows reset the transport.
- **Every transport button calls `self.viewer.<method>()` at click time**, never a bound method captured at build time — the widget under it is replaced whole when the renderer is switched.
- **A model is content like any other.** Showing one clears the primitive spec the window would otherwise replay on a renderer swap, and the [Model Panel](model_panel.md) re-shows the model instead — `on_activate` is the one line that keeps the two from both claiming the stage.
- **`_suspend_animation_clear` breaks a real ordering trap.** `ModelPanel.show_model()` always calls `on_activate` (`_on_model_shown`), which clears the loaded animation — correct when a MODEL button is clicked by hand, wrong when the model is being shown AS the content of the very scene about to play (or being replayed across a renderer swap). The flag suppresses that one clear for exactly those two call sites, set and reset around a single call each, never left standing.
