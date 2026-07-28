# Light Widget

**Script:** [Light Widget (script)](view.py)

## Purpose

`Preview3DLightWidget` — a plain `QWidget` that draws the 3D preview itself. Same scene specs, same part paths and same method names as the web-backed [Preview3D Widget](../widget.md), so a host can swap one for the other; see [The Two Renderers](../../RENDERERS.md).

## Connections

### Uses
- [Light Scene](scene.md), [Light Primitives](primitives.md), [Light Camera](camera.md), [Light Renderer](renderer.md)
- [Light Timeline](animation.md) — the loaded animation scene; this widget applies its samples and owns the timer that advances it

### Used by
- [Demo Window](../../demoapp/window.md) — the RENDERER switch
- Consumers that cannot afford Qt WebEngine

## Classes

### Preview3DLightWidget

#### Signals
- `camera_changed(dict)`: the same payload the web-backed widget emits — `{azimuth, elevation, distance, view, projection, grid, gridStep, background, contentVersion}` — so a host's readout code works with either renderer.
- `animation_changed(dict)`: `{scene, label, playing, time, duration, progress, speed, frame, frames, loop}` — likewise.

#### Methods
The shared contract in full: `show_scene`, `show_axes`, `list_parts`, `set_part_visible`, `set_part_opacity`, `show_only`, `remove_part`, `set_view`, `step_view`, `set_projection`, `orbit_by`, `set_orbit`, `pan_by`, `zoom_by`, `reset_view`, `camera_state`, `set_background`, `set_grid`.

Animation, likewise identical on both: `set_animation`, `play_animation`, `pause_animation`, `toggle_animation`, `stop_animation`, `seek_animation`, `step_frame`, `set_speed`, `jump_to_end`, `animation_state` — see [Animation Scenes](../../SCENES.md).

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
- **A resize re-frames only while the framing is still ours.** Framing is aspect-dependent, so narrowing the widget clips content that used to fit — but once the user has orbited, panned or zoomed, that view is theirs. Same rule as the web core. A loaded scene owns the camera outright, so it always re-frames and re-applies the current instant.
- **The playback timer runs only while a scene plays.** A paused viewer costs nothing; the timer starts on play and stops on pause or when a non-looping scene ends.
- **Showing new content clears the loaded scene**, exactly as in the web core: a scene is written against the parts of specific content, and keeping it would mean raising from inside `show_scene()` on a path that no longer exists. Content first, scene second.
- **`camera.dolly` is applied against a baseline captured when the scene loads** — the framing the presets would give — so one descriptor plays correctly on content of any size. Both baselines (distance and orthographic height) come from one quantity, so a mid-flight projection switch does not jump in size.
- **Background is applied to the widget palette**, and transparent mode sets `WA_TranslucentBackground` — the LIGHT renderer has no page behind it to flash white, which is one whole class of bug it simply does not have.
