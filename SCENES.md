# Animation Scenes

A **scene** makes the viewer play itself: the camera flies, parts fade, a switch group cycles its labels — with play, pause, single-frame stepping and a scrub slider on top.

A scene is **data**, not code. It is a JSON descriptor of keyframes over flat parameters, so a new one is written without touching either renderer — and because both renderers read the same descriptors, the same scene plays identically in the Three.js core and in the QPainter one.

## Table of Contents

- [The Descriptor](#descriptor)
- [Channels](#channels)
- [Keys and Interpolation](#keys)
- [Easing](#easing)
- [Playback](#playback)
- [Scenes and Content](#content)
- [The Shipped Scenes](#shipped)
- [Writing a New Scene](#writing)
- [Why It Is Built This Way](#why)

---

<a id="descriptor"></a>

## The Descriptor

```json
{
  "name": "turntable",
  "label": "Turntable",
  "duration": 8,
  "loop": true,
  "tracks": [
    { "channel": "camera.azimuth", "keys": [{ "t": 0, "value": 45 }, { "t": 1, "value": 405 }] },
    { "channel": "camera.elevation", "keys": [{ "t": 0, "value": 25 }] }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `name` | Identifier — how a host refers to the scene |
| `label` | Text for a button or readout; defaults to `name` |
| `duration` | Seconds at 1× speed |
| `loop` | `true` restarts at the end; `false` stops there |
| `tracks` | One entry per parameter the scene drives |
| `content` | *Optional* — the scene spec this scene was written for (see [Scenes and Content](#content)) |

A track:

```json
{ "channel": "part.opacity", "path": "shell/face:+x",
  "keys": [{ "t": 0, "value": 1, "ease": "ease-in-out" }, { "t": 0.3, "value": 0.12 }] }
```

`t` is a **fraction of the scene**, not seconds — so changing `duration` re-times the whole scene without touching a single key.

The shipped scenes live in [`shared/scenes.json`](shared/scenes.json); the channel table, easing names, frame rate and speeds live in [`shared/spec.json`](shared/spec.json).

---

<a id="channels"></a>

## Channels

A channel is one flat parameter. That is the whole design constraint: anything the viewer can show must be reachable as a plain value, or a timeline cannot drive it.

| Channel | Value | `path`? | Notes |
|---------|-------|---------|-------|
| `camera.azimuth` | degrees | — | Absolute bearing. Values may run past 360 so a full turn is one straight tween |
| `camera.elevation` | degrees | — | Above the horizon; clamped just short of the poles |
| `camera.dolly` | factor | — | Apparent size relative to the scene's own framing. `1` = framed, `2` = twice as close |
| `camera.projection` | `"perspective"` \| `"orthographic"` | — | Steps at the key |
| `part.opacity` | 0…1 | yes | The part's own opacity; children inherit it |
| `part.visible` | `true` / `false` | yes | Steps at the key |
| `group.show` | child name | yes | Shows one child of a switch group, hides its siblings |
| `grid` | `true` / `false` | — | The reference grid |

Paths are the ones from [MODELS.md](MODELS.md) — `shell/face:+x`, `axes/arm:+x/labels`. An unknown path fails loudly; it is never a silent no-op.

**`camera.dolly` is a factor, not a distance**, on purpose: the scene is measured against whatever framing the content happens to need, so one descriptor plays correctly on a 1-unit cube and on a 100-unit model.

---

<a id="keys"></a>

## Keys and Interpolation

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

Two consequences worth knowing:

- **A key's easing governs the segment that starts at it** — the last key's easing is never used.
- **Anything that is not a number steps automatically.** A projection name, a visibility flag and a switch-group child need no special handling and no easing.
- **A track with one key is a constant** — useful for pinning elevation while azimuth spins.

---

<a id="easing"></a>

## Easing

| Name | Shape |
|------|-------|
| `linear` | constant rate — the default |
| `ease-in` | starts still, accelerates (cubic) |
| `ease-out` | arrives gently (cubic) |
| `ease-in-out` | both — what camera flights normally want |
| `step` | holds the outgoing value until the next key |

---

<a id="playback"></a>

## Playback

Every method exists on **both** widgets and in the JS viewer.

| Python | JavaScript | Does |
|--------|------------|------|
| `set_animation(descriptor)` | `setAnimation(descriptor)` | Load a scene — paused at t = 0, that instant already applied. `None`/`null` clears |
| `play_animation()` | `playAnimation()` | Play (a finished non-looping scene replays from the start) |
| `pause_animation()` | `pauseAnimation()` | Pause where it stands |
| `toggle_animation()` | `toggleAnimation()` | Play / pause |
| `stop_animation()` | `stopAnimation()` | Back to the first frame, paused |
| `seek_animation(p)` | `seekAnimation(p)` | Jump to `p` = 0…1 — the scrub slider |
| `step_frame(±1)` | `stepFrame(±1)` | One frame at a time; pauses |
| `set_speed(x)` | `setSpeed(x)` | 0.5× / 1× / 2× |
| `jump_to_end()` | `jumpToEnd()` | **Instant mode** — the end state without the flight |
| `animation_state(cb)` | `animationState()` | `{scene, label, playing, time, duration, progress, speed, frame, frames, loop}` |

State arrives as the `animation_changed(dict)` signal in Qt and through `onAnimationChange(callback)` in JS, rate-limited while playing.

**There is no separate end-of-scene callback.** A non-looping scene that reaches its end reports `playing: false` at `progress: 1` — that report is the signal.

With no scene loaded every transport call is a **documented no-op**, so a host can wire buttons before it has anything to play.

Playback is **fixed-timestep** at the frame rate in `shared/spec.json` (30 fps): wall time accumulates and is spent in whole 1/fps steps. That is what makes a scene evaluate at the same instants in both renderers regardless of the host's frame rate — and what makes `step_frame` mean something exact.

---

<a id="content"></a>

## Scenes and Content

A scene is written against the **parts of specific content**. `part.opacity` on `shell/face:+x` means nothing if the viewer is showing an axes gizmo.

So the rule is simple and enforced by both renderers:

> **Content first, scene second. Showing new content clears the loaded scene.**

`show_scene()`, `show_axes()` and `load_model()` all drop the timeline and report `scene: null`. Load the content, then the scene:

```python
viewer.show_scene(scene["content"])     # or any content of your own
viewer.set_animation(scene)
viewer.play_animation()
```

A descriptor may carry a `content` field naming the spec it was written for. That is a **host convention, not a timeline channel** — the viewer never reads it; the demo app and the demo page use it to load the right content before playing. A scene that drives only the camera (`turntable`, `tour`) needs no `content` and plays on anything.

---

<a id="shipped"></a>

## The Shipped Scenes

In [`shared/scenes.json`](shared/scenes.json), available to Python as `load_shared_scenes()` and to JS as `Preview3D.SCENES`:

| Scene | Shows off |
|-------|-----------|
| **Turntable** | The plain case — a full 360° orbit, looping, no content of its own |
| **View tour** | An eased flight through front → right → back → left → top → iso |
| **Hexagon reveal** | The geometry answer: flying down the cube's body diagonal **and switching to orthographic**, the only projection under which the silhouette is an exact regular hexagon |
| **X-ray shell** | Per-part opacity as a tween — the shell turns to glass and the core inside appears |
| **Legend cycle** | `group.show` stepping three legend terms per axis tip, the case from [MODELS.md](MODELS.md), driven by the timeline instead of by hand |

---

<a id="writing"></a>

## Writing a New Scene

1. **Decide what moves.** Every moving thing must be one of the [channels](#channels) — if it is not, the channel has to be added to both renderers first, not worked around in the scene.
2. **Name the parts** you will drive, from `list_parts()` or [MODELS.md](MODELS.md).
3. **Write the descriptor** — into `shared/scenes.json` to ship it with the component, or into your own project's data.
4. **Set `t` as fractions**, and let `duration` decide the pace.
5. **Ease the camera, step the rest.** `ease-in-out` on flights; names and flags step by themselves.
6. **Check both ends**: `jump_to_end()` must land somewhere that makes sense on its own — that is the state a reduced-motion user and a test both see.

A scene never needs an engine change. If it does, that is the signal that a new channel is missing.

---

<a id="why"></a>

## Why It Is Built This Way

**Flat parameters, not internals.** The timeline may only set values a host could set by hand. It never reaches into the renderer, which is why the identical descriptor works over a WebGL scene graph and over a software painter.

**Data, not choreography.** Hardcoding a scene in either renderer would mean writing it twice and drifting immediately.

**Determinism.** Fixed-timestep evaluation plus normalized time makes t = 0, ½, 1 exactly reproducible — `tests/test_animation_parity.py` drives every shipped scene to those instants in both renderers and compares camera angles, projection, and per-part visibility and opacity.
