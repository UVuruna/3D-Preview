# Light Timeline

**Script:** [Light Timeline (script)](../animation.py)
**Flow:** [diagram](../__flow/animation.md)

## Purpose

The animation driver for the LIGHT renderer: keyframe evaluation plus the playback clock. Pure Python, **no Qt** — so it is testable without a GUI, and [Light Widget](view.md) only owns the timer that calls `tick()`.

Mirror of the web core's Timeline (`src/animation.js`): the same descriptor format, the same channel table, the same easing curves. The scene format is documented once, for both renderers, in [SCENES.md](../../../SCENES.md).

## Connections

### Uses
- [Preview3d Package (folder)](../../___preview3d.md) — `resources.load_shared_spec()` — frame rate, speeds, easing names, channels

### Used by
- [Light Widget](view.md) — owns one `Timeline` and applies its samples
- [Preview3d Package (folder)](../../___preview3d.md) — `NO_ANIMATION` is re-exported as public API (`from .light.animation import NO_ANIMATION` in `preview3d/__init__.py`)

## Module contents

- `Timeline` — a loaded scene plus its clock
- `ANIMATION_DEFAULTS`, `CHANNELS` — the shared spec's animation block and channel table
- `EASINGS`, `ease(name, t)` — the curves
- `prepare_track()`, `sample_track()` — validation and interpolation
- `NO_ANIMATION` — the state reported when nothing is loaded

## Classes

### Timeline

#### Attributes
- `name`, `label`, `duration`, `loop` — from the descriptor
- `fps`, `frames` — the fixed step rate and the scene's frame count
- `tracks` — validated tracks, keys sorted by `t`
- `time`, `speed`, `playing` — the clock
- `progress`, `frame` — properties derived from `time`

#### Methods
- `sample(progress)` / `values()`: every track resolved → `[{channel, path, value}]`
- `play()`, `pause()`, `toggle()`, `stop()`, `seek(progress)`, `step_frame(±1)`, `set_speed(x)`, `jump_to_end()`
- `tick(elapsed_seconds)`: advances by whole fixed steps; returns `True` if the time moved
- `state()`: `{scene, label, playing, time, duration, progress, speed, frame, frames, loop}`

## Design Decisions

- **`bool` is excluded from "is a number" explicitly.** In Python `bool` subclasses `int`, so without the guard a `part.visible` track would cross-fade through 0.5 here while stepping in JavaScript — two renderers disagreeing on a channel that looks correct in both sources.
- **Vector interpolation reuses the same eased fraction as a scalar's**, computed once per sample rather than per component — a `part.position` track costs the same one `ease()` call a `camera.azimuth` track does.
- **Rounding is half-up, not Python's default.** The built-in `round()` rounds halves to even; JavaScript's `Math.round` rounds them up. On an exact tie that would put the two renderers one frame apart (`_round_half_up`).
- **Validation happens at load** (`prepare_track`), naming the scene in the message, rather than failing silently mid-playback (No Error Masking (rules/CODE.md)).
- **No Qt import anywhere in this module** — the LIGHT renderer keeps its geometry and its timeline testable headless; only `view.py` and `renderer.py` touch Qt.
- **The easing names in `shared/spec.json` are checked against what is implemented, at import time** (`_UNIMPLEMENTED`), so the shared spec cannot advertise a curve this module lacks — it raises `RuntimeError` at import if it does.
