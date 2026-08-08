# Light Widget

**Script:** [Light Widget (script)](../view.py)

## Purpose

`Preview3DLightWidget` — a plain `QWidget` that draws the 3D preview itself. Same scene specs, same part paths and same method names as the web-backed `Preview3DWidget`, so a host can swap one for the other; see [RENDERERS.md](../../../RENDERERS.md).

This is the widget shell: it owns Qt state (the paint surface, the animation `QTimer`, mouse/keyboard event handlers) and delegates every actual algorithm to the modules it wraps — projection and painting to [Light Renderer](renderer.md), framing and orbiting to [Light Camera](camera.md), keyframe evaluation to [Light Timeline](animation.md), model resolution to [Light Model View](model_view.md). Its own logic is orchestration (dispatch tables for input and animation channels, state bookkeeping) rather than a multi-step algorithm of its own, so it stays Standard tier with no `__flow/` — a diagram here would mostly restate a dispatch table already given as a table below. At 600 lines it is near the project's file-size smell threshold (THE STRUCTURE LAW (rules/CODE.md)); splitting it is out of scope for this migration.

## Connections

### Uses
- [Light Scene](scene.md), [Light Primitives](primitives.md), [Light Camera](camera.md), [Light Renderer](renderer.md)
- [Light Timeline](animation.md) — the loaded animation scene; this widget applies its samples and owns the timer that advances it
- [Light Model View](model_view.md) — the model half: validate, build, resolve a view or an orientation
- [Preview3d Package (folder)](../../___preview3d.md) — `switcher.py` (a switcher position as ordinary part operations), `directions.parse_direction`, `resources.load_shared_spec`

### Used by
- [Preview3d Package (folder)](../../___preview3d.md) — re-exports `Preview3DLightWidget` (`from .light import Preview3DLightWidget` in `preview3d/__init__.py`)
- Demo Window (`demoapp/window.py`) — imports it from the package root for the RENDERER switch
- Consumers that cannot afford Qt WebEngine

## Classes

### Preview3DLightWidget

#### Signals
- `camera_changed(dict)`: the same payload the web-backed widget emits — `{azimuth, elevation, distance, view, projection, grid, gridStep, background, contentVersion, orientation, modelView}` — so a host's readout code works with either renderer.
- `animation_changed(dict)`: `{scene, label, playing, time, duration, progress, speed, frame, frames, loop}` — likewise.

#### Methods
The shared contract in full: `show_scene`, `show_axes`, `list_parts`, `set_part_visible`, `set_part_opacity`, `set_part_position`, `set_part_stroke`, `show_only`, `remove_part`, `set_view`, `step_view`, `set_projection`, `orbit_by`, `set_orbit`, `pan_by`, `zoom_by`, `reset_view`, `snap_to`, `camera_state`, `set_background`, `set_grid`.

`set_part_position(path, position)` and `set_part_stroke(path, progress)` are M3's additions — a part's absolute position, and 0..1 of a line part's own length drawn from its start — both `part.position` / `part.strokeProgress` in `SCENES.md`, and both mirrored in `viewer.js`'s `setPartPosition`/`setPartStroke`.

Models and the Switcher, likewise on both: `show_model`, `set_model_view`, `model_views`, `set_switcher`, `switcher_state`, `set_orientation`, `step_orientation` — see [MODELS.md](../../../MODELS.md).

Animation: `set_animation`, `play_animation`, `pause_animation`, `toggle_animation`, `stop_animation`, `seek_animation`, `step_frame`, `set_speed`, `jump_to_end`, `animation_state` — see `SCENES.md`.

`load_model` exists and **raises `NotImplementedError`**.

## Input

| Input | Action |
|-------|--------|
| Drag (not right button) | Orbit |
| Right-drag | Pan |
| Wheel | Zoom |
| Arrows · Ctrl+Arrows | Orbit · pan |
| Shift+←→ · Shift+↑↓ | Cycle views · top/bottom |
| `+` `−` · `P` `G` `R` | Zoom · projection, grid, reset |

Bindings mirror the web renderer's, defined in `src/keyboard.js`.

## Design Decisions

- **`load_model` refuses loudly rather than showing a blank view** (No Error Masking (rules/CODE.md)). A host calling it has picked the wrong renderer and should learn that at the call site, not from an empty widget.
- **`list_parts`, `switcher_state` and `animation_state` all accept an optional callback and also return the value directly.** The web-backed widget can only answer asynchronously (it crosses into JS and back), so host code written against it passes a callback; supporting both shapes is what makes the two widgets genuinely interchangeable.
- **A resize re-frames only while the framing is still ours.** Framing is aspect-dependent, so narrowing the widget clips content that used to fit — but once the user has orbited, panned or zoomed (`_user_framed`), that view is theirs. Same rule as the web core. A loaded scene owns the camera outright, so it always re-frames and re-applies the current instant.
- **Showing new content clears the loaded scene**, exactly as in the web core: a scene is written against the parts of specific content, and keeping it would mean raising from inside `show_scene()` on a path that no longer exists. Content first, scene second. **The loaded MODEL and any snapped orientation go the same way**, and for the same reason — both are state about content that no longer exists (`_mount`).
- **A snapped orientation does not re-frame.** A cube keeps its silhouette as it turns, and re-fitting on every step would make a stepped clock jitter for no gain. It is carried as a rotation on the content root (`Node.basis`), which the painter's walk skips entirely while it is `None`.
- **The Switcher walks the part list rather than remembering paths.** A switcher position matches on a part's last path segment, so it survives any content that follows the convention and needs no bookkeeping across a content swap.
- **`camera.dolly` is applied against a baseline captured when the scene loads** (`_reframe_animation`) — the framing the presets would give — so one descriptor plays correctly on content of any size. Both baselines (distance and orthographic height) come from one quantity, so a mid-flight projection switch does not jump in size.
- **The playback timer runs only while a scene plays** (`_sync_clock`). A paused viewer costs nothing; the timer starts on play and stops on pause or when a non-looping scene ends.
- **Background is applied to the widget palette**, and transparent mode sets `WA_TranslucentBackground` — the LIGHT renderer has no page behind it to flash white, which is one whole class of bug it simply does not have.
