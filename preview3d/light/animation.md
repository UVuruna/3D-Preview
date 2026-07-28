# Light Timeline

**Script:** [Light Timeline (script)](animation.py)

## Purpose

The animation driver for the LIGHT renderer: keyframe evaluation plus the playback clock. Pure Python, **no Qt** — so it is testable without a GUI, and [Light Widget](view.md) only owns the timer that calls `tick()`.

Mirror of the web core's [Timeline](../../src/animation.md): the same descriptor format, the same channel table, the same easing curves. The scene format is documented once, for both renderers, in [Animation Scenes](../../SCENES.md).

## Connections

### Uses
- [Preview3d Package (folder)](../___preview3d.md) → `resources.load_shared_spec()` — frame rate, speeds, easing names, channels

### Used by
- [Light Widget](view.md) — owns one `Timeline` and applies its samples
- [Preview3d Package (folder)](../___preview3d.md) — `NO_ANIMATION` is re-exported as public API

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

## Interpolation

```
value of a track at progress p:

    IF p ≤ first key's t   → first key's value
    IF p ≥ last key's t    → last key's value
    OTHERWISE:
        from, to  ← the key pair bracketing p
        local     ← (p − from.t) / (to.t − from.t)

        IF from.value AND to.value are both numbers:
            → from.value + (to.value − from.value) × ease(from.ease, local)
        OTHERWISE:
            → from.value            # names, flags and choices STEP
```

## Design Decisions

- **`bool` is excluded from "is a number" explicitly.** In Python `bool` subclasses `int`, so without the guard a `part.visible` track would cross-fade through 0.5 here while stepping in JavaScript — two renderers disagreeing on a channel that looks correct in both sources. Pinned by `test_non_numeric_values_step_rather_than_interpolate`.
- **Rounding is half-up, not Python's default.** The built-in `round()` rounds halves to even; JavaScript's `Math.round` rounds them up. On an exact tie that would put the two renderers one frame apart.
- **Validation happens at load**, naming the scene in the message, rather than failing silently mid-playback (root Rule #1).
- **No Qt import anywhere in this module** — the LIGHT renderer keeps its geometry and its timeline testable headless; only `view.py` and `renderer.py` touch Qt.
- **The easing names in `shared/spec.json` are checked against what is implemented, at import**, so the shared spec cannot advertise a curve this module lacks.
