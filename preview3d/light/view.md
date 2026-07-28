# Light Widget

**Script:** [Light Widget (script)](view.py)

## Purpose

`Preview3DLightWidget` — a plain `QWidget` that draws the 3D preview itself. Same scene specs, same part paths and same method names as the web-backed [Preview3D Widget](../widget.md), so a host can swap one for the other; see [The Two Renderers](../../RENDERERS.md).

## Connections

### Uses
- [Light Scene](scene.md), [Light Primitives](primitives.md), [Light Camera](camera.md), [Light Renderer](renderer.md)

### Used by
- [Demo Window](../../demoapp/window.md) — the RENDERER switch
- Consumers that cannot afford Qt WebEngine

## Classes

### Preview3DLightWidget

#### Signals
- `camera_changed(dict)`: the same payload the web-backed widget emits — `{azimuth, elevation, distance, view, projection, grid, gridStep, background, contentVersion}` — so a host's readout code works with either renderer.

#### Methods
The shared contract in full: `show_scene`, `show_axes`, `list_parts`, `set_part_visible`, `set_part_opacity`, `show_only`, `remove_part`, `set_view`, `step_view`, `set_projection`, `orbit_by`, `pan_by`, `zoom_by`, `reset_view`, `camera_state`, `set_background`, `set_grid`.

`load_model` exists and **raises `NotImplementedError`**.

## Input

| Input | Action |
|-------|--------|
| Left-drag | Orbit |
| Right-drag | Pan |
| Wheel | Zoom |
| Arrows · Ctrl+Arrows | Orbit · pan |
| Shift+←→ · Shift+↑↓ | Cycle views · top/bottom |
| `+` `−` · `P` `G` `R` | Zoom · projection, grid, reset |

Identical to the web renderer's bindings, which are defined in `src/keyboard.js`.

## Design Decisions

- **`load_model` refuses loudly rather than showing a blank view** (root Rule #1). A host calling it has picked the wrong renderer and should learn that at the call site, not from an empty widget.
- **`list_parts` accepts a callback and also returns the list.** The web-backed widget can only answer asynchronously, so host code written against it passes a callback; supporting both shapes is what makes the two widgets genuinely interchangeable.
- **A resize re-frames only while the framing is still ours.** Framing is aspect-dependent, so narrowing the widget clips content that used to fit — but once the user has orbited, panned or zoomed, that view is theirs. Same rule as the web core.
- **Background is applied to the widget palette**, and transparent mode sets `WA_TranslucentBackground` — the LIGHT renderer has no page behind it to flash white, which is one whole class of bug it simply does not have.
