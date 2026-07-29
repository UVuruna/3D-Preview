# The Two Renderers

3D Preview ships **two interchangeable rendering back ends**. They take the same scene specs, expose the same methods, emit the same camera state, and address parts by the same paths — so a consumer picks one by what its project needs, not by rewriting anything.

## Table of Contents

- [Which One](#which-one)
- [What Each Can Do](#capabilities)
- [The Shared Contract](#contract)
- [What Is Deliberately Different](#differences)
- [How Drift Is Prevented](#drift)
- [Switching](#switching)

---

<a id="which-one"></a>

## Which One

**Take LIGHT unless you need something only WEB has.** It is the smaller, simpler dependency, and for labelled diagrammatic scenes it is arguably the nicer picture.

| You need… | Renderer |
|-----------|----------|
| To load `.glb` / `.gltf` files a user picks | **Web** |
| To run in a browser as well as in Qt | **Web** |
| Real materials, environment lighting, big meshes | **Web** |
| A Qt app whose installer must stay small | **Light** |
| Parametric scenes you author yourself | **Light** |
| Crisp text labels at any zoom | **Light** |

The weight is the whole trade: the web core drags Qt WebEngine into a consumer's installer — **343 MB on disk** in this PySide6 installation (compressed to less in an installer, but it is the single largest thing in a lean app). The LIGHT renderer adds nothing beyond PySide6 itself.

---

<a id="capabilities"></a>

## What Each Can Do

Both, identically:

- Free orbit from any angle, zoom, pan — by mouse **and** keyboard
- Seven view presets and the perspective ↔ orthographic switch
- Silhouette framing, so content fills its container
- Per-part show / hide / dim / solo / remove, by path
- Parametric primitives from JSON specs, nested into assemblies
- **Animation playback** from the same scene descriptors — play, pause, single-frame stepping, scrub, speed, instant mode ([Animation Scenes](SCENES.md))
- The optional ground grid with a rounded cell size
- The live camera and playback readouts
- Transparent-background mode

Only the **web** renderer:

- **glTF / GLB loading** — the LIGHT one raises `NotImplementedError` rather than showing a blank view, because a host that calls it has picked the wrong renderer
- **GLB export**
- **Real materials and environment lighting** — physically based shading, not flat shading
- **Large meshes** — tens of thousands of triangles per frame are a GPU's job, not a Python loop's
- **Intersecting geometry** — the LIGHT renderer sorts whole polygons back to front, which no per-polygon order can get right for shapes that pass through each other
- **Browsers** — the same bundle serves a website; QPainter cannot

Only the **light** renderer:

- **No browser engine in the installer**
- **Native text rendering** — labels are drawn with the font engine, so they stay sharp at any zoom instead of being textures that blur

---

<a id="contract"></a>

## The Shared Contract

Anything a host can observe is the same on both sides.

| Operation | Both |
|-----------|------|
| Show a scene | `show_scene(spec)`, `show_axes(...)` |
| Parts | `list_parts(...)`, `set_part_visible`, `set_part_opacity`, `show_only`, `remove_part` |
| Camera | `set_view`, `step_view`, `set_projection`, `orbit_by`, `set_orbit`, `pan_by`, `zoom_by`, `reset_view`, `snap_to` |
| Models | `show_model(model, view)`, `set_model_view`, `model_views(...)` — see [Making Models](MODELS.md#model) |
| Switcher | `set_switcher(register, reading)`, `switcher_state(...)` |
| Orientation | `set_orientation(id)`, `step_orientation(±1)` — the cube's 24 |
| Animation | `set_animation`, `play_animation`, `pause_animation`, `toggle_animation`, `stop_animation`, `seek_animation`, `step_frame`, `set_speed`, `jump_to_end`, `animation_state` |
| Appearance | `set_background`, `set_grid` |
| State | `camera_changed(dict)` — azimuth, elevation, distance, view, projection, grid, gridStep, background, contentVersion, orientation, modelView<br>`animation_changed(dict)` — scene, label, playing, time, duration, progress, speed, frame, frames, loop |

One difference, and it is unavoidable: **`list_parts`, `animation_state`, `switcher_state` and `model_views` are asynchronous on the web renderer** (the answer has to cross into the page and back), so they take a callback. The LIGHT ones accept the same callback *and* return the value directly, so code written either way works with either renderer.

**Opacity multiplies down in both.** A part's reported opacity is its OWN; dimming a group dims everything under it without changing what its children say about themselves. That was not true until the model pins caught it — the web core used to push a group's value straight onto every descendant's material, so a child claimed its parent's dimming as its own and re-lighting one child silently escaped the group.

Scene specs and part paths are documented once, in [MODELS.md](MODELS.md); animation descriptors in [SCENES.md](SCENES.md). Both apply to both renderers.

---

<a id="differences"></a>

## What Is Deliberately Different

**They do not look identical, and that is intended.** The web core shades with physically based materials over an environment map; the LIGHT one flat-shades each polygon from a single key light. Forcing them to match pixel for pixel would mean freezing both.

What *is* pinned is everything a program can check: part trees, visibility, opacity isolation, framing, camera angles, the palette. See `tests/test_renderer_parity.py`.

Hidden-surface handling also differs in kind. The web core uses a depth buffer, so a translucent part must be told to stop writing depth or it hides what is inside it. The LIGHT renderer paints back to front with nothing writing depth at all, so translucency needs no special case — the same scene simply works.

---

<a id="drift"></a>

## How Drift Is Prevented

Two implementations of one component invite drift (root Rule #5). Two mechanisms hold them together:

1. **`shared/spec.json`** — the pole palette, neutral colours, face order, view presets, camera defaults and the animation channel table live in ONE file, and **`shared/scenes.json`** holds the shipped scenes. The JS core imports both at build time; the Python renderer reads them at run time. A colour changed there changes in both, and a test asserts neither source restates a pole colour or its own copy of the frame rate.
2. **`tests/test_renderer_parity.py`** — the same specs go into both widgets and the observable results are compared: part paths, initial visibility, `show_only`, opacity isolation, framing and camera state.
3. **`tests/test_model_parity.py`** — the model layer exists twice as well (a website has no Python, a lean Qt app has no browser), so the two implementations are run head to head and their OUTPUT compared exactly: the computed palette, the whole model, the scene spec it becomes, the 24 orientations. That is the strongest check here, because the answer is a value rather than a picture. A second half drives the same model through both widgets and compares part paths, per-part colour, the Switcher's effect and each view's opacities.
4. **`tests/test_animation_parity.py`** — every shipped scene is driven to t = 0, ½ and 1 in both and compared: camera angles, projection, per-part visibility and opacity, the frame counter. The easing curves are sampled through both implementations and compared numerically, since the timeline is the one part of the component that genuinely exists twice.

Whenever a capability is added to one renderer, it either lands in both or is recorded in the "only" lists above. An undocumented difference is a bug.

That is not theoretical: the animation pins found, on their first run, that the cube's wireframe was 0.35 opaque in the web core and 1.0 in the LIGHT one — the same part reporting two different values. It is now `neutral.edgeOpacity` in the shared spec.

---

<a id="switching"></a>

## Switching

```python
from preview3d import Preview3DWidget, Preview3DLightWidget

from preview3d import load_shared_scenes

viewer = Preview3DLightWidget()      # or Preview3DWidget()
viewer.show_scene({"type": "cube", "colors": "poles"})
viewer.set_projection("orthographic")
viewer.set_part_opacity("cube/face:+z", 0.2)

scene = next(s for s in load_shared_scenes() if s["name"] == "turntable")
viewer.set_animation(scene)          # content first, scene second
viewer.play_animation()
```

The demo app (`python main.py`) has a **RENDERER** switch at the top of its panel that swaps them live on the same scene — including mid-animation, so a flight can be watched in both back to back. The fastest way to see the difference on your own content.
