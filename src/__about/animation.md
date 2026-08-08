# Timeline

**Script:** [Timeline (script)](../animation.js)

**Flow:** [diagram](../__flow/animation.md)

## Purpose

The animation driver for the WEB core: turns a scene descriptor — keyframes over flat parameters — into resolved values at any instant, and keeps the playback clock that walks through them.

It knows **nothing about rendering**. `sample()` returns plain `{channel, path, value}` entries and [Viewer](viewer.md) applies them, which is exactly what lets the LIGHT renderer run the identical descriptor through its own applier.

The scene format itself is documented once, for both renderers, in [Animation Scenes](../../SCENES.md).

## Connections

### Uses
- `shared/spec.json` — frame rate, speeds, easing names and the channel table

### Used by
- [Viewer](viewer.md) — owns one `Timeline` and applies its samples
- [Source (folder)](../___src.md) — exported through the public API
- [Light Timeline](../../preview3d/light/__about/animation.md) — the mirror implementation in Python

## Exports

- `Timeline` — a loaded scene plus its clock
- `ANIMATION_DEFAULTS` — the shared spec's `animation` block
- `CHANNELS` — the channel table (which channels exist, which need a `path`)
- `NO_ANIMATION` — the state reported when nothing is loaded
- `ease(name, t)` / `sampleTrack(track, progress)` — the curve and the interpolator, exported for tests

## Classes

### Timeline
The loaded scene plus its clock.

#### Attributes
- `name`, `label`, `duration`, `loop` — from the descriptor
- `fps`, `frames` — the fixed step rate and the scene's frame count
- `tracks` — validated tracks (each `{channel, path, keys}`), keys sorted by `t`
- `time`, `speed`, `playing` — the clock
- `progress` (getter) — `time / duration`
- `frame` (getter) — the current frame index, rounded

#### Methods
- `sample(progress)`: every track resolved at `progress` → `[{channel, path, value}]`
- `values()`: `sample()` at the current instant
- `play()`, `pause()`, `toggle()`, `stop()`, `seek(progress)`, `stepFrame(±1)`, `setSpeed(x)`, `jumpToEnd()`, `state()` — transport
- `tick(elapsedSeconds)`: advances by whole fixed steps; returns `true` if the time moved

## Design Decisions

- **Validation happens at load, not during playback.** An unknown channel, a missing `path`, an empty key list or an unknown easing throws while the scene is being loaded — where the scene can be named in the message — instead of silently animating nothing halfway through (No Error Masking (rules/CODE.md)).
- **Non-numeric values step automatically.** A projection name, a visibility flag and a switch-group child need no special case; "cannot be interpolated" and "should step" are the same set. The Python mirror needs one extra guard for this, because `bool` is an `int` there.
- **Vector interpolation reuses the same eased fraction as a scalar's.** One `ease()` call per sample, whether the channel is a number or a `[x, y, z]`. Pinned cross-language by `test_vector_interpolation_agrees_with_the_web_core` in `tests/test_animation_parity.py`.
- **Fixed timestep.** Wall time accumulates and is spent in whole 1/fps steps, so a scene evaluates at the same instants regardless of the host's frame rate — that is what makes both renderers agree and `stepFrame` mean something exact. `maxStep` caps the catch-up so a hidden tab does not fast-forward the scene on return.
- **`t` is a fraction, not seconds.** Changing `duration` re-times a whole scene without touching a key.
- **No end-of-scene callback.** A finished non-looping scene simply reports `playing: false` at `progress: 1`; a second mechanism would be one more thing to miss.
- **The easing names in `shared/spec.json` are checked against what is implemented, at module load** (a loop over `ANIMATION_DEFAULTS.easings` throws if `animation.js` is missing one) — advertising a curve to scene authors that does not exist would be a silent authoring trap.
