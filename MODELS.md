# Making Models for 3D Preview

How to build (or repair) a model so its elements can be **addressed** — shown, hidden, made translucent, swapped for one another, or dropped entirely. Written for the case where we author the models ourselves.

## Table of Contents

- [The One Rule](#the-one-rule)
- [Paths — How a Part Is Addressed](#paths)
- [Naming Conventions](#naming)
- [Switch Groups — One of Several, at a Time](#switch-groups)
- [Materials — The Sharing Trap](#materials)
- [Seeing Inside — Translucency That Works](#translucency)
- [Authoring in Blender](#blender)
- [Repairing a Model We Did Not Make](#repairing)
- [Parametric Models — No File at All](#parametric)
- [A MODEL — Axes, Seats and Views](#model)
  - [Directions — One Grammar for the Whole Cube](#directions)
  - [The Schema](#schema)
  - [The Tree a Model Becomes](#model-tree)
  - [Views — The Four Owner Models](#views)
  - [The Switcher — Register and Reading](#switcher)
  - [Orientations and Snap Views](#orientations)
  - [Colours Are Computed](#model-colours)
  - [Exporting a Model From Your Own Data](#exporting)
- [The API](#api)
- [Checklist](#checklist)

---

<a id="the-one-rule"></a>

## The One Rule

**A part that has no name cannot be addressed.**

Everything in this document follows from that. The viewer identifies elements by their names in the model's node tree; an unnamed node falls back to `Mesh#3`, which is not something anyone can write into code, and which silently changes the moment the model is re-exported.

So: **name every node you will ever want to touch, and group the ones that belong together.**

---

<a id="paths"></a>

## Paths — How a Part Is Addressed

A part's address is the chain of node names from the content root, joined with `/`:

```
axes/arm:+x/labels/label:1
│    │      │      └── the node itself
│    │      └───────── its group
│    └──────────────── the arm group
└───────────────────── the model root
```

Two consequences worth internalising:

- **Renaming a node changes its address.** Names are the public interface of a model; treat a rename like renaming a function, and update the host code that addresses it.
- **A group is addressable too.** Hiding a group hides everything under it, in one call — which is why grouping is not cosmetic.

`listParts()` returns every part with its `path`, `depth`, whether it is `drawable` (carries geometry) or a pure group, plus its current `visible` and `opacity`. That is what the demo app's PARTS panel is built from.

---

<a id="naming"></a>

## Naming Conventions

Names are free-form, but the house conventions below make models readable and predictable. **Never put `/` in a name** — it is the path separator.

| Pattern | Use for | Example |
|---------|---------|---------|
| `noun` | a single distinct element | `joint`, `body`, `edges`, `core` |
| `kind:key` | one of a family, keyed by what distinguishes it | `arm:+x`, `face:-z`, `station:3` |
| plural noun | a group holding a family | `arms`, `labels`, `faces` |
| `label:N` | numbered alternatives inside a switch group | `label:0`, `label:1` |

Rules of thumb:

- **Group by what you will manipulate together.** If the whole arm should dim at once, the shaft, tip and labels belong in one `arm:+x` group. If only the tip should dim, they must be siblings.
- **Keep the tree shallow but real.** Two or three levels is plenty; nesting every mesh in its own group makes long addresses and buys nothing.
- **Names carry no language.** They are identifiers, not display text (root Rule #12). Display text lives in the label sprite's content, which the host can swap.

---

<a id="switch-groups"></a>

## Switch Groups — One of Several, at a Time

The exact case that motivated this system: **three legend terms on one axis tip, only one shown, then the next.**

Model it as a group whose children are the alternatives:

```
axes/
  arm:+x/
    shaft
    tip
    labels/          ← the switch group
      label:0        ← "East"    (visible)
      label:1        ← "Istok"   (hidden)
      label:2        ← "E"       (hidden)
```

Then one call selects which one speaks:

```javascript
viewer.showOnly('axes/arm:+x/labels', 'label:1');   // now only "Istok" is shown
```

```python
widget.show_only("axes/arm:+x/labels", "label:1")
```

`showOnly` shows the named child and hides its siblings — no bookkeeping on the host side, no risk of two terms visible at once. The demo app's `solo` button next to a group is exactly this, cycling through the children and back to all.

**Author all alternatives in the same place, at the same size.** They are alternates, not a layout — the viewer swaps visibility and nothing else.

The same selection can be driven by an animation instead of by hand: the `group.show` channel steps a group through its children over time. See [Animation Scenes](SCENES.md), where the shipped "Legend cycle" scene does exactly this for all six arms.

---

<a id="materials"></a>

## Materials — The Sharing Trap

The single most common reason "I dimmed one part and something else went transparent too."

**A material is a shared object.** In a real glTF file, one material typically dresses many meshes; a modelling tool assigns the same material to every part of the same colour. Changing its opacity would change every part wearing it.

The viewer handles this for you: the first time a part's opacity is changed, that part gets its **own copy** of the material, and only that copy is modified. Verified behaviour — dimming an arm's shaft to 0.25 leaves the neighbouring tip at 1.0 even though the two are the same colour.

What that means when authoring:

- You do **not** need a unique material per part just to make opacity work.
- You **do** need a unique material per part if the parts must have different **colours** — that part is ordinary modelling.
- Do not rely on editing a material to change many parts at once through the viewer; address the parts (or their common group) instead.

---

<a id="translucency"></a>

## Seeing Inside — Translucency That Works

Setting a part's opacity below 1 also turns off its **depth writing**. Without that, a translucent shell still writes into the depth buffer and hides whatever is inside it — the exact opposite of why anyone makes a shell translucent.

For a model meant to be looked into:

- **Model the outer shell as separate, individually addressable faces**, not as one closed mesh. A single mesh can only be dimmed as a whole; six named faces let you open the two facing the camera and keep the rest solid, which reads far better than a uniformly ghostly box.
- **Give shell faces double-sided materials.** Once you can see through the near face, you are looking at the *back* of the far ones; single-sided faces vanish and the object looks broken.
- **Put the inner content in its own group** so it can be revealed and hidden independently.

The `Cube + core` demo scene is exactly this shape: a `shell` of six named faces with a `core` inside it. Dim `shell/face:+z` and `shell/face:+y` and the core is plainly visible through them.

---

<a id="blender"></a>

## Authoring in Blender

The viewer reads **glTF 2.0** (`.glb` preferred — one self-contained file).

1. **Name every object in the Outliner.** Blender's object names become the glTF node names, which become the path segments. `Cube.001` is a bug waiting to happen.
2. **Parent by empties for grouping.** An Empty named `arm:+x` with the shaft, tip and labels parented under it becomes exactly the group structure above. Blender collections do **not** survive the export as groups — parenting does.
3. **Apply transforms** (Object → Apply → All Transforms) before export, unless a transform is meaningful. Unapplied scale is the usual cause of "it loaded ten times too big".
4. **Keep the model near the origin and roughly unit-sized.** The viewer frames whatever it gets, so absolute size does not break anything, but a model 5000 units from the origin makes grid and depth settings awkward.
5. **Y is up.** Use the glTF exporter's default `+Y up` conversion; the viewer's `top`/`bottom` views and the ground grid assume it.
6. **Export settings:** include Selected Objects only if that is what you mean; keep *Materials*; drop *Cameras* and *Lights* — the viewer supplies its own lighting, and an exported light will not be used.
7. **One material per intended colour**, not per object. Sharing is fine (see above).

**Verify before shipping the file:** load it in the demo app and read the PARTS list. Every element you plan to control must appear there with a name you recognise. If it says `Mesh#4`, the model is not finished.

---

<a id="repairing"></a>

## Repairing a Model We Did Not Make

Downloaded models are almost never addressable — flat hierarchies, `mesh_0_1` names, one giant merged mesh.

1. **Load it in the demo app and read the PARTS list first.** That tells you what you actually got.
2. **One merged mesh cannot be split by the viewer.** Separate it in Blender (Edit Mode → `P` → By Loose Parts, or by material), then name the pieces.
3. **Rename and re-parent** to the conventions above.
4. **Re-export as `.glb`** and check the PARTS list again.

Budget the work honestly: renaming is minutes, splitting a merged mesh is real modelling time.

---

<a id="parametric"></a>

## Parametric Models — No File at All

Before authoring a file, ask the derivation question (root Rule #19): **can this be computed from parameters?** If yes, it belongs in `src/primitives.js` as a builder, not on disk — every variant then comes free and nothing has to be re-exported when a colour or a size changes.

A parametric spec is plain JSON and nests:

```javascript
{
    type: 'cube', name: 'shell', colors: 'poles',
    children: [
        { type: 'cube', name: 'core', size: 0.45, color: '#F5F5F5' }
    ]
}
```

Every spec accepts `name`, `position`, `scale` and `children`, so an assembly is one JSON tree with the same addressable structure a file would give you. Builders name their own children (`axes/arm:+x/shaft`, `cube/face:+y`), so parts control works identically for computed and loaded content.

Adding a builder is documented in [Parametric Primitives](src/primitives.md).

The builders that ship: `axes` (arms from the origin), `cube` (a shell of six
named faces), `marker` (a small seat with labels), and `group` (an empty node
that only holds children).

---

<a id="model"></a>

## A MODEL — Axes, Seats and Views

Everything above is about a SCENE — what to draw. A **model** is one level up:
what EXISTS. It is renderer-neutral JSON that names axes, the seats they point
at, the words each seat says in each register, and the views that decide who
speaks. The viewer turns it into a scene; nothing about the model knows how it
will be drawn.

```python
from preview3d import Preview3DLightWidget, build_cube_model

widget = Preview3DLightWidget()
widget.show_model(build_cube_model())          # opens on the model's first view
widget.set_model_view("cube")                  # the glass cube
widget.set_switcher(register="myth", reading="both")
```

```javascript
const model = Preview3D.buildCubeModel();
viewer.showModel(model, 'cube');
viewer.setSwitcher('myth', 'both');
```

<a id="directions"></a>

### Directions — One Grammar for the Whole Cube

A direction is a **token**: one or more distinct signed cube letters. Its value
is the NORMALISED sum of those letters.

| Token | Direction | What it is |
|-------|-----------|------------|
| `+x`, `-z` | `(1,0,0)`, `(0,0,-1)` | a face normal — 6 of them, **3 axes** |
| `+x+y`, `+x-z` | `(1,1,0)/√2` | an edge midpoint — 12 of them, **6 axes** |
| `+x+y+z`, `-x+y-z` | `(1,1,1)/√3` | a vertex diagonal — 8 of them, **4 axes** |

Thirteen axes, twenty-six directions, one rule (root Rule #19). The six legacy
tokens still work because they are the **one-letter case** of that rule, not a
table beside it. A raw unit vector is accepted anywhere a token is.

- **Letter order is canonical.** `+y+x` and `+x+y` are one direction, so they
  are one NAME — `arm:+x+y` — and an arm can never be addressable by two paths.
- **The tier follows the letter count**: 1 → `primary`, 2 → `secondary`,
  3 → `tertiary`. `sacred` is *not* a fourth geometry; it is the one vertex
  diagonal a model singles out, and only the model can say which.
- **A seat sits at its token's un-normalised vector times half the cube.** `+x`
  lands on a face centre, `+x+y` on an edge midpoint, `+x+y+z` on a vertex —
  so a seat is exactly where the axis end of the same name points.

Angle exactness is pinned, not eyeballed: every direction's dot products are in
`tests/test_axis_geometry.py`, together with golden screen projections.

<a id="schema"></a>

### The Schema

The model's shape is stated once, as data, in
[`shared/model_schema.json`](shared/model_schema.json), and read by BOTH
validators — `preview3d/model.py` and `src/model.js`. That is what makes "it
validates" mean the same thing on both sides.

```json
{
  "name": "cube13",
  "label": "The Thirteen Axes",
  "root": "model",
  "size": 1.0,
  "registers": ["canon", "myth", "historical", "movie"],

  "axes": [
    {
      "id": "+x+y",
      "tier": "secondary",
      "name": "+x+y / -x-y",
      "ends": [
        {
          "direction": "+x+y",
          "color": "#E5B16A",
          "names": {
            "canon": { "luminous": "Warmth · Clarity", "fallen": "Scorching · Glare" },
            "myth":  { "luminous": "Hearth · Sun",     "fallen": "Wildfire · Drought" }
          }
        },
        { "direction": "-x-y", "color": "#9599FA", "names": { "…": "…" } }
      ]
    }
  ],

  "cells": [
    {
      "id": "+x", "kind": "face", "position": [0.5, 0, 0], "color": "#F97316",
      "names": { "canon": { "luminous": "Warmth", "fallen": "Scorching" } }
    }
  ],

  "glass": { "opacity": 0.12 },

  "views": [
    { "name": "cube", "label": "The Cube", "camera": "+x+y+z",
      "opacity": { "axes/primary": 0.55, "cells/faces": 1.0, "glass": 0.12 } }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `registers` | The vocabularies this model carries. Every seat must speak in **exactly** these — a switcher position can never find nothing to say |
| `axes[].tier` | `primary` / `secondary` / `tertiary` / `sacred` — decides dress, size and which group it lands in |
| `axes[].ends` | Exactly two, each with a direction, a colour and its `names` |
| `cells[].kind` | `face` / `edge` / `vertex` / `centre` |
| `names` | `register → { luminous, fallen }`; both readings are required |
| `views[].camera` | A direction to snap to — a token or a vector |
| `views[].opacity` | Part path → opacity, for every group in the tree |

**Errors carry the path** — `model.axes[3].ends[1].color` — because a model is
generated data and "invalid model" without a location is not something anyone
can act on (root Rule #1).

<a id="model-tree"></a>

### The Tree a Model Becomes

```
model/
  axes/
    primary/ secondary/ tertiary/ sacred/
      axis:+x+y/
        arm:+x+y/
          shaft
          tip
          luminous/                ← a switch group, one child per register
            label:canon  label:myth  label:historical  label:movie
          fallen/                  ← the same, at the other radius
        arm:-x-y/  …
  cells/
    faces/ edges/ vertices/ centre/
      cell:+x/
        body
        luminous/  fallen/
  glass                            ← the shell, six named faces
```

**Every group exists whether or not it has anything in it.** That skeleton is a
contract: a view addresses those paths to say which family speaks, so a missing
group would be a view that fails halfway through rather than one that dims
nothing.

The **radial law** is geometry here, not a caption: an arm's `luminous` stop
sits INSIDE the geometric end (0.72 of the arm) and its `fallen` stop PAST it
(1.18), so a reading of *both* draws the five stations of the axis by itself.
Seats do not carry it — a seat IS a station — so their two readings simply sit
above and below the marker.

An axis stop also carries a small **bead** — its own sphere geometry, on the
same part its labels sit on — because unlike a seat it has no marker of its
own to be visible as. That is what the Five Stations animation slides with
`part.position` ([Animation Scenes](SCENES.md#channels)): the bead is one
addressable part, never a separate child, so the whole thing (sphere and
labels together) moves as one.

<a id="views"></a>

### Views — The Four Owner Models

**The four owner models are four VIEWS over ONE model, never four hand-built
scenes.** A view is nothing but per-group opacities plus a camera direction,
which is also what lets an animation scene TWEEN from one owner model into
another without any engine change.

| View | Shows | Camera |
|------|-------|--------|
| `primary` | The 3 face axes | `+x+y+z` (isometric) |
| `secondary` | The 6 edge axes at their TRUE angles, face axes faint behind them | `+x+y+z` |
| `tertiary` | The 4 vertex diagonals, the sacred one dressed and sized apart | `-x+y` |
| `cube` | Everything, glass shell at 0.12, all 27 seats visible through it | `+x+y+z` |

The tertiary view stands **perpendicular to the sacred diagonal** on purpose:
looking *down* an axis collapses it to a point, which is exactly what the
isometric view does to `+x+y+z`.

<a id="switcher"></a>

### The Switcher — Register and Reading

Two independent flat parameters:

| Control | Values | Does |
|---------|--------|------|
| `register` | `canon` / `myth` / `historical` / `movie` | swaps every visible label |
| `reading` | `luminous` / `fallen` / `both` | which radial stops are lit |

Neither is a mode with its own code path. A switcher position resolves to
ordinary part operations — the same `show_only` and `set_part_visible` a host
could call by hand — which is why a timeline can drive `switcher.register` like
any other channel ([Animation Scenes](SCENES.md)).

**The convention it works by**, and therefore what makes *any* content
switchable, including a consumer's own: a seat carries one group per **stop**
(`luminous`, `fallen`), each holding one `label:<register>` child per register.

```python
widget.set_switcher(register="historical")     # reading unchanged
widget.set_switcher(reading="both")            # register unchanged
widget.switcher_state()                        # {"register": …, "reading": …}
```

<a id="orientations"></a>

### Orientations and Snap Views

A cube can be set down in exactly **24** ways, and they are computed from 6
up-faces × 4 spins rather than stored (root Rule #19). Each is named
`<face>:<spin>` — `+y:0` is upright.

```python
widget.set_orientation("-z:2")     # snap
widget.step_orientation(1)         # the next in enumeration order
widget.set_orientation(None)       # upright
widget.snap_to("+x+y+z")           # look down a body diagonal and re-frame
```

`snap_to` exists because the seven view presets cannot express the four body
diagonals a cube is actually read along. Snapping an orientation deliberately
does **not** re-frame: a cube keeps its silhouette as it turns, and re-fitting
on every step would make a stepped clock jitter for no gain.

<a id="model-colours"></a>

### Colours Are Computed

Owner decree 2026-07-28. Twenty-six invented hex values would be twenty-six
things to keep in sync; four rules cover every direction the cube has:

| Tier | Rule |
|------|------|
| primary | the sealed pole hue itself |
| secondary | blend of its two poles, **thinned by moonlight** |
| tertiary | blend of its three poles, **deepened toward ink** |
| sacred | none of the six — **white-gold**, the seventh dress |

The thinning is not decoration. A plain blend can land on a hue the palette
already spends (`+x+y-z` — orange, yellow and red — averages to a few units
from the orange pole), and two seats wearing one colour is a lie about the
structure. `verify_palette` refuses it, and every model build runs it.

A seat wears **the colour of the axis end that points at it** — one formula for
both, because they are the same place.

Tunables live in `shared/spec.json` under `axisColors`; both languages read them
and round identically, so the same seat reports the same hex in both renderers
(`list_parts()` now carries `color`).

<a id="exporting"></a>

### Exporting a Model From Your Own Data

**A consumer supplies the WORDS, never the geometry.** The cube's axes, seats,
positions and colours are all derived; the only content anyone owns is the
vocabulary.

```python
from preview3d import build_cube_model, validate

model = build_cube_model(
    name="character-cube",
    sacred="+x+y+z",                 # which diagonal leaves the six-colour palette
    registers=["canon", "myth"],     # a model may carry fewer than the four
    vocabulary={
        "canon": {
            "+x": ("Courage", "Recklessness"),   # (luminous, fallen)
            "-x": ("…", "…"), "+y": ("…", "…"), "-y": ("…", "…"),
            "+z": ("…", "…"), "-z": ("…", "…"),
            "centre": ("…", "…"),
        },
        "myth": { "…": "…" },
    },
)
validate(model)                      # already run by the builder; free to re-check
```

Twelve words per register become fifty-four seats: a two-letter seat says what
its two poles say, a three-letter seat what its three say, joined with ` · `.
Write your own JSON instead if the derived wording is not what you want — it
only has to pass the schema.

The model layer imports **no Qt at all**, so an exporter script needs no GUI.

---

<a id="api"></a>

## The API

Same operations on both sides; JS names are camelCase, Python snake_case.

| Operation | JavaScript | Python |
|-----------|-----------|--------|
| List parts | `viewer.listParts()` | `widget.list_parts(callback)` |
| Show / hide | `viewer.setPartVisible(path, on)` | `widget.set_part_visible(path, on)` |
| Opacity 0–1 | `viewer.setPartOpacity(path, a)` | `widget.set_part_opacity(path, a)` |
| One of a group | `viewer.showOnly(group, child)` | `widget.show_only(group, child)` |
| Remove for good | `viewer.removePart(path)` | `widget.remove_part(path)` |
| Show a model | `viewer.showModel(model, view)` | `widget.show_model(model, view)` |
| Pick a view | `viewer.setModelView(name)` | `widget.set_model_view(name)` |
| List its views | `viewer.modelViews()` | `widget.model_views(callback)` |
| Switcher | `viewer.setSwitcher(register, reading)` | `widget.set_switcher(register=…, reading=…)` |
| Switcher state | `viewer.switcherState()` | `widget.switcher_state(callback)` |
| Snap the camera | `viewer.snapTo(direction)` | `widget.snap_to(direction)` |
| Orientation | `viewer.setOrientation(id)` · `stepOrientation(±1)` | `widget.set_orientation(id)` · `step_orientation(±1)` |

The Python listing is asynchronous — the answer arrives in the callback, because the model may still be loading when you ask. On the LIGHT widget every such method *also* returns the value outright, so code written either way drives either renderer.

`listParts()` reports each part's `color` as `#RRGGBB` (or `null` for a pure group) alongside `visible` and `opacity`. That is what a legend reads — and what lets a test prove a *computed* palette came out the same in both renderers, since the pictures deliberately cannot be compared.

**Opacity multiplies down.** A part's reported opacity is its OWN; dimming a group dims everything under it without changing what those children say about themselves. Both renderers implement it that way, and `tests/test_model_parity.py` pins that they agree.

**Hiding is not removing.** `setPartVisible(path, false)` is the reversible one and is what toggling wants. `removePart` detaches the part and frees its geometry and materials; it is for content that must not stay in memory, and it cannot be undone without rebuilding the scene.

**A wrong path raises**, listing the paths that do exist. That is deliberate (root Rule #1): a typo must not look like a part that simply had nothing to change.

---

<a id="checklist"></a>

## Checklist

Before a model is considered done:

- [ ] Every element you intend to control has a **deliberate name**
- [ ] Elements manipulated together share a **group**
- [ ] Alternatives (labels, language variants, registers) sit in a **switch group** as siblings
- [ ] Shell faces meant to be seen through are **separate and double-sided**
- [ ] Transforms applied; model near the origin; **+Y up**
- [ ] The demo app's PARTS list shows the names **you expect**, with no `Mesh#N`
- [ ] Anything derivable from parameters was built as a **primitive**, not exported as a file (root Rule #19)
