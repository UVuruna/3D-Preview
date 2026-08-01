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
- [The Cinematic Scenes](#cinematic)
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
| `part.position` | `[x, y, z]` | yes | Absolute position; lerps component-wise like a lone number does |
| `part.strokeProgress` | 0…1 | yes | 0..1 of a line part's own length, drawn from its start toward its end |
| `group.show` | child name | yes | Shows one child of a switch group, hides its siblings |
| `grid` | `true` / `false` | — | The reference grid |
| `switcher.register` | `canon` \| `myth` \| `historical` \| `movie` | — | Which vocabulary speaks — see [the Switcher](MODELS.md#switcher) |
| `switcher.reading` | `luminous` \| `fallen` \| `both` | — | Which radial stops are lit |
| `content.orientation` | `<face>:<spin>`, or `null` | — | One of the cube's 24 orientations; `null` is upright |

Paths are the ones from [MODELS.md](MODELS.md) — `shell/face:+x`, `axes/arm:+x/labels`. An unknown path fails loudly; it is never a silent no-op.

**`camera.dolly` is a factor, not a distance**, on purpose: the scene is measured against whatever framing the content happens to need, so one descriptor plays correctly on a 1-unit cube and on a 100-unit model. It is also how a first-person shot works: dollying past `1` moves the eye CLOSER than the content's own framing distance, and far enough in it passes the content's own extent — which is what the Blindness view's "camera flies into the vertex" is, with no separate "inside" mode. Software rasterising that closely needed one correctness fix, not a new channel: a face or line with any point behind the eye's own near plane is now culled WHOLE in the LIGHT renderer (`NEAR_CULL` in `preview3d/light/renderer.py`) — three.js already clips there in hardware, so this is a LIGHT-only fix, not a capability difference (see CLAUDE.md, Known Traps).

**`part.position` and `part.strokeProgress` are M3's additions.** `part.position` is what lets a scene SLIDE a part — a bead to its station (Five Stations), a seat collapsing into the centre (the Hexagram's Being variant) — rather than only fade or step it; a `[x, y, z]` lerps component-wise by the same rule a lone number does, so it costs nothing extra to support. `part.strokeProgress` is what lets a line "draw itself" — the Hexagram's two triangles emerging stroke by stroke — by shortening the part's own segments toward their start; it needs a part actually built from segments (the `hexagram` primitive's `triangle:up`/`triangle:down`), and is a no-op on anything else.

**The three register/reading/orientation channels are all names**, so they step by themselves like any other non-numeric value — no easing, no special case. They are the reason the Switcher and the orientation table were built as flat parameters rather than as modes: a scene that walks the four registers, or that turns the cube through its 24 orientations, is a descriptor rather than an engine change. Driving `part.opacity` on the four view groups is likewise how a scene TWEENS from one owner model into another (`axes/primary`, `cells/faces`, `glass`, … — see [Views](MODELS.md#views)).

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
        IF from.value AND to.value are both vectors of the SAME length:
            → each component lerped the same way             # part.position
        OTHERWISE:
            → from.value            # names, flags and mismatched shapes STEP
```

Two consequences worth knowing:

- **A key's easing governs the segment that starts at it** — the last key's easing is never used.
- **Anything that is not a number, or not a same-length vector of numbers, steps automatically.** A projection name, a visibility flag and a switch-group child need no special handling and no easing — and neither does a `part.position` track, which is a vector rather than a scalar but follows the exact same rule.
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

**`content` may itself name a MODEL instead of a primitive spec:** `{"type": "model", "view": "cube"}` tells the demo apps to build the demo's thirteen-axis model ([MODELS.md](MODELS.md#model)) and call `show_model(model, view)` rather than `show_scene(content)`. Blindness and Five Stations are written against the model's own 27 seats — reproducing that tree as a hand-written primitive spec would just be duplicating `model_scene.py` (root Rule #5), and the model is exactly what `build_cube_model()` already computes. This is still a host convention, not a channel: nothing in `preview3d/light/animation.py` or `src/animation.js` reads `content.type` — only `demoapp/window.py`'s `_play_animation`, `demo/index.html`'s `playAnimation`, and the test harness's `_load()` do.

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
| **Hexagram X-ray — Offices / Being** | The Cube BECOMES the Hexagram — see [The Cinematic Scenes](#cinematic) |
| **The Blindness — Christic / Diabolic** | First-person from a sacred vertex; 19 of 26 cells visible — see [The Cinematic Scenes](#cinematic) |
| **Five Stations** | The Sacred Axis alone, its five stations sliding into place — see [The Cinematic Scenes](#cinematic) |

**"Hexagon reveal" and "X-ray shell" are demo material, superseded for the cinematic showcase.** They are the two generic PROBES the Hexagram X-ray and the Blindness were built from — a bare orthographic body-diagonal flight, and a bare per-face opacity tween — and they still demonstrate those two mechanisms cleanly on a plain cube. The five scenes below are what actually ships as "the cinematic scenes" (PLAN.md, M3): the same two mechanisms, aimed at the real content (the 27-seat model, the hexagram overlay, the radial law) and carrying the meaning PLAN.md's storyboards describe. Both probes stay shipped; nothing about them is wrong, they simply are not the finished teaching device.

---

<a id="cinematic"></a>

## The Cinematic Scenes

The five scenes PLAN.md's "Cinematic Scenes — Self-Playing Instructions" commissioned for M3, in the shipped order. Each plays on the demo's own neutral vocabulary (`build_cube_model()`'s generic English words) or a handful of bespoke primitives — a real consumer (DOMY Watch's Character-Cube exporter) plays the identical descriptors over its own model, since a scene addresses PARTS, not words.

### Hexagram X-ray — Offices (`hexagram_offices`) and Being (`hexagram_being`)

*Storyboard: PLAN.md, Scene 1.* The camera flies to the `+x+y+z` body diagonal while the shell thins to glass and the projection blends perspective → orthographic; at alignment the silhouette is already the regular hexagon (free, from the cube's own geometry under orthographic), and the two triangles of the [`hexagram`](src/__about/primitives.md) overlay draw themselves in.

- **Content:** a bespoke `group` — a poles-coloured `cube` shell, a `hexagram` (`diagonal: "+x+y+z"`), and three `marker` "sacred seats" (the two vertex cells plus the centre) in white-gold. Not the full 13-axis model: the sacred seats here are three generic markers, not DOMY's Christic/One/Diabolic seats — a real consumer swaps in its own labelled model.
- **Channels:** `camera.azimuth`/`elevation` (the flight), `camera.projection` (the blend), `camera.dolly` (a closing push-in), `part.opacity` (the shell thinning to glass, the wireframe brightening into "spokes", the seats fading in), `part.strokeProgress` (the two triangles drawing themselves).
- **Being's difference:** at alignment, `part.position` slides the two vertex seats along the axis into the centre seat already there — "all three become the central axis" (PLAN.md's own image). Offices instead leaves the two triangles in their default dress (`upColor`/`downColor` — the hexagram builder's own sacred/neutral defaults, standing in for Court/Genesis).
- **Simplifications, stated rather than hidden:** the storyboard's "labels cross-fade from 3D billboards to flat dial-style labels" has no separate flat-label rendering mode here — this demo content carries no label text at all, and a consumer's own model would drive the SAME `part.opacity`/`group.show` channels on its own labels. The storyboard's "exit plays the whole flight in reverse" is a host interaction (scrub backward, then close), not scene data.

### The Blindness — Christic (`blindness_christic`) and Diabolic (`blindness_diabolic`)

*Storyboard: PLAN.md, Scene 2.* The camera flies to (and past) a sacred vertex — first-person, via an ordinary `camera.dolly` value large enough to pass the content's own extent, no separate "inside" mode — while the antipode's own seven-cell court (`hidden_from(vertex)`, [Directions](preview3d/__about/directions.md)) pulses once, then fades: 19 of 26 visible. The "Centre button" is not a separate control here; it is where the scene ENDS — the camera glides back to standard framing and all 26 relight, so `jump_to_end()` and a reduced-motion viewer both land on "only The One sees everything" rather than stuck mid-blindness.

- **Content:** `{"type": "model", "view": "cube"}` — the demo's full 27-seat model, glass shell included.
- **Channels:** `camera.azimuth`/`elevation`/`dolly` (the flight in and the pull-back), `part.opacity` on the seven hidden cells (pulse, fade, hold, relight).
- **Christic/Diabolic** are the mirror flight from `+x+y+z` and `-x-y-z`; `hidden_from()` computes each variant's seven paths from the OTHER vertex's own letters, so nothing about which seven cells hide is hand-picked.
- **The HUD ("19 of 26 visible") is host business, not an engine channel** — `list_parts()` already reports every cell's opacity, so a host counts the visible ones itself. The engine does not paint a HUD number, the same way it does not paint the sealed epigraph PLAN.md's end card wants; both are exactly what "host supplies the text" means.
- **A swap control** is simply loading the OTHER variant's scene — a cut, not a bespoke cross-fade transition; a host wanting a smoother swap can seek one out while loading the other in, but the engine does not owe a dedicated blend for it.

### Five Stations (`five_stations`)

*Storyboard: PLAN.md, Scene 3.* The cube fades until only one axis remains; the camera settles side-on to it; the two radial stops per end (`luminous`, `fallen`) — already a bead each, M3's `bead=True` addition to an axis stop — slide from the geometric vertex to their final stations, growing into visibility as they go. See [Cinematics](preview3d/__about/cinematics.md) for the generator and [Model](MODELS.md#model-tree) for the radial law the geometry already encodes.

- **Content:** `{"type": "model", "view": "cube"}`.
- **Channels:** `camera.azimuth`/`elevation` (the side-on settle, computed PER AXIS — never one hardcoded perpendicular), `part.opacity` (the fade-to-one-line, the beads growing in), `part.position` (the slide).
- **Generalizes to any axis, by construction, not by extra scenes.** The shipped descriptor is one baked call to `build_five_stations_scene(build_cube_model(), "+x+y+z")` ([Cinematics](preview3d/__about/cinematics.md)); the demo apps' GENERALIZE control (an axis picker) calls the identical function for whichever of the 13 axes is selected. `tests/test_animation_parity.py::test_shipped_five_stations_matches_the_generator` pins that the baked JSON and the live generator never quietly diverge.

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

**Generate the descriptor when the shape is the point, not the content.** Five Stations is one CHOREOGRAPHY that happens to apply to any of the cube's 13 axes; hand-authoring 13 near-identical JSON blocks would be exactly the enumeration root Rule #19 forbids. [Cinematics](preview3d/__about/cinematics.md) computes the descriptor from the model and the chosen axis instead, and ships one baked instance so the shipped scene is still ordinary data like every other.
