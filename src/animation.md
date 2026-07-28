# Timeline

**Script:** [Timeline (script)](animation.js)

## Purpose

The animation driver for the web core: turns a scene descriptor — keyframes over flat parameters — into resolved values at any instant, and keeps the playback clock that walks through them.

It knows **nothing about rendering**. `sample()` returns plain `{channel, path, value}` entries and the [Viewer](viewer.md) applies them, which is exactly what lets the LIGHT renderer run the identical descriptor through its own applier.

The scene format itself is documented once, for both renderers, in [Animation Scenes](../SCENES.md).

## Connections

### Uses
- `shared/spec.json` — frame rate, speeds, easing names and the channel table

### Used by
- [Viewer](viewer.md) — owns one `Timeline` and applies its samples
- [Source (folder)](___src.md) — exported through the public API
- [Light Timeline](../preview3d/light/animation.md) — the mirror implementation in Python

## Exports

- `Timeline` — a loaded scene plus its clock
- `ANIMATION_DEFAULTS` — the shared spec's `animation` block
- `CHANNELS` — the channel table (which channels exist, which need a `path`)
- `NO_ANIMATION` — the state reported when nothing is loaded
- `ease(name, t)` / `sampleTrack(track, progress)` — the curve and the interpolator, exported for tests

## Classes

### Timeline

#### Attributes
- `name`, `label`, `duration`, `loop` — from the descriptor
- `fps`, `frames` — the fixed step rate and the scene's frame count
- `tracks` — validated tracks, keys sorted by `t`
- `time`, `speed`, `playing` — the clock
- `progress` (getter) — `time / duration`
- `frame` (getter) — the current frame index

#### Evaluation
- `sample(progress)`: every track resolved at `progress` → `[{channel, path, value}]`
- `values()`: `sample()` at the current instant

#### Transport
`play()`, `pause()`, `toggle()`, `stop()`, `seek(progress)`, `stepFrame(±1)`, `setSpeed(x)`, `jumpToEnd()`, `state()`.

#### Clock
- `tick(elapsedSeconds)`: advances by whole fixed steps; returns `true` if the time moved

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

A key's easing governs the segment that **starts** at it, so the last key's easing is never used.

## Design Decisions

- **Validation happens at load, not during playback.** An unknown channel, a missing `path`, an empty key list or an unknown easing throws while the scene is being loaded — where the scene can be named in the message — instead of silently animating nothing halfway through (root Rule #1).
- **Non-numeric values step automatically.** A projection name, a visibility flag and a switch-group child need no special case; "cannot be interpolated" and "should step" are the same set. The Python mirror needs one extra guard for this, because `bool` is an `int` there.
- **Fixed timestep.** Wall time accumulates and is spent in whole 1/fps steps, so a scene evaluates at the same instants regardless of the host's frame rate — that is what makes both renderers agree and `stepFrame` mean something exact. `maxStep` caps the catch-up so a hidden tab does not fast-forward the scene on return.
- **`t` is a fraction, not seconds.** Changing `duration` re-times a whole scene without touching a key.
- **No end-of-scene callback.** A finished non-looping scene simply reports `playing: false` at `progress: 1`; a second mechanism would be one more thing to miss.
- **The easing names in `shared/spec.json` are checked against what is implemented, at module load.** Advertising a curve to scene authors that does not exist would be a silent authoring trap.
