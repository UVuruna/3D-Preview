# Parametric Primitives

**Script:** [Parametric Primitives (script)](primitives.js)

## Purpose

Simple shapes COMPUTED from plain-JSON specs — the root Rule #19 workhorse of this project. No stored model files: an axes gizmo or a cube is a handful of parameters, and every variant (colours, lengths, labels) is derived live. `buildPrimitive(spec)` dispatches on `spec.type` and returns a `THREE.Group` whose children are **named**, so the [Parts](parts.md) API can address them one by one.

## Connections

### Uses
- [Source (folder)](___src.md) → `labels.js` — text sprites for arm labels

### Used by
- [Viewer](viewer.md) — `show(spec)` calls `buildPrimitive()`

## Universal Spec Fields

Honoured for every primitive, so an assembly is one JSON tree rather than host-side scene building:

| Field | Meaning |
|-------|---------|
| `name` | the part name this group is addressed by |
| `position` | `[x, y, z]` offset |
| `scale` | uniform scale factor |
| `children` | nested specs, built recursively |

## Directions

An arm's `axis` is a **direction token or a 3-vector**, resolved by the shared grammar in [Directions](../preview3d/directions.md). It used to be one of six hardcoded entries, which made the cube's six edge axes and four vertex diagonals inexpressible; the six face tokens are now the one-letter case of one rule rather than a table beside it, so every spec written against the old table still means exactly what it meant.

## The Pole Palette

`POLE_COLORS` — the owner's six hues (decree 2026-07-28), one table serving both the axes gizmo and the cube's faces, because a pole colour belongs to the **direction**, not to the shape pointing that way:

| Direction | Colour | | Direction | Colour |
|-----------|--------|-|-----------|--------|
| `+x` | orange `#F97316` | | `-x` | blue `#3B82F6` |
| `+y` | yellow `#EAB308` | | `-y` | purple `#A855F7` |
| `+z` | green `#22C55E` | | `-z` | red `#EF4444` |

An arm with no `color` wears its pole hue; a cube asks for the set by name with `colors: 'poles'`. A host therefore never restates the palette and can never drift out of sync with it. Only a **one-letter** token has a pole to inherit — an arm pointing down an edge or a diagonal must bring its own colour, or say so loudly, rather than be given a made-up one. Those colours are computed, never invented: [Axis Colours](../preview3d/axis_colors.md).

## Specs

### `axes` — Axes Gizmo

Up to 6 arms from the origin, each its own group. Defaults in `AXES_DEFAULTS`:

| Field | Default | Meaning |
|-------|---------|---------|
| `armLength` | `1` | arm length in scene units |
| `armRadius` | `0.03` | shaft radius |
| `joint` | `true` | the neutral sphere at the origin. A model draws thirteen axes as thirteen `axes` specs, which would stack thirteen joints in one spot, so it turns this off and names its own centre seat |
| `stopHeight` | `0.16 × armLength` | label height for the arm's `stops` |
| `arms` | all six poles, labelled `X+`…`Z−` | each: `{axis, name?, color?, label?, stops?}` |

`label` may be a **string or an array of strings**. An array builds a switch group holding `label:0`, `label:1`, … with only the first visible — the "three legend terms for one arm tip, one shown at a time" case (see [Making Models](../MODELS.md)).

`stops` is the model layer's richer form: each is `{name, anchor, labels}` where `labels` maps register to text. It builds a switch group NAMED for the stop, holding `label:<register>` children at that anchor — which is what the [Switcher](../preview3d/switcher.md) drives, and how the radial law becomes geometry rather than a caption. The anchor is computed by [Model Scene](../preview3d/model_scene.md), so the same shape serves an arm and a seat and the builders stay dumb.

An arm's **name** is `arm:<canonical token>`, or `arm:<index>` for a raw vector with no explicit `name`. Canonical means the cube's own letter order: `+y+x` and `+x+y` are one direction, so they cannot become two addresses for one arm.

Part tree:

```
axes/
  joint                ← only when `joint` is on
  arm:+x/
    shaft
    tip
    labels/            ← only when a `label` was given
      label:0  label:1  label:2
    luminous/          ← one group per `stop`
      label:canon  label:myth  …
  arm:-x/ …
```

Build algorithm (per arm):

```
direction ← unit vector of arm.axis        (+x → (1,0,0), …)
rotation  ← quaternion mapping +Y onto direction
shaft     ← cylinder(armRadius, 0.8·L), rotated, centred at direction · 0.4·L
tip       ← cone(2.4·armRadius, 0.2·L), rotated, centred at direction · 0.9·L
labels    ← text sprites at direction · 1.16·L, height 0.16·L, in the arm's colour
```

plus one neutral sphere at the origin as the joint.

### `cube` — Cube

Defaults in `CUBE_DEFAULTS`:

| Field | Default | Meaning |
|-------|---------|---------|
| `size` | `1` | edge length |
| `color` | `#818CF8` | single colour → one `body` mesh |
| `colors` | `null` | six colours in order `+x −x +y −y +z −z`, or the string `'poles'` → six named `face:*` meshes |
| `edges` | `true` | soft translucent edge lines, named `edges`; how faint is `neutral.edgeOpacity` in `shared/spec.json`, so both renderers report and draw the same value |

**Per-face colours build six separate face meshes, not one mesh with six material slots.** A material slot cannot be hidden or dimmed on its own — and a face nobody can address is a face nobody can look through. Faces are double-sided, so once the near face is dimmed the far ones still read as solid.

### `group` — An Empty Node

`{type: 'group', name, children}`. A model's tree is mostly groups, and a group that has to be a shape is a group that cannot be empty when its family is.

### `marker` — A Seat

Defaults in `MARKER_DEFAULTS`:

| Field | Default | Meaning |
|-------|---------|---------|
| `radius` | `0.05` | sphere radius |
| `color` | `#818CF8` | its own colour — a seat's is computed, never inherited |
| `stopHeight` | `2.6 × radius` | label height |
| `stops` | none | as for an arm, above |

Part tree: `marker/body` plus one group per stop. Its **position** comes from the universal `position` field, like every other primitive's.

## Adding a Primitive

1. Write `buildName(spec)` — pure function, spec in, `Group` out; **name every child**; export a `NAME_DEFAULTS` object for its parameters.
2. Register it in the `BUILDERS` table.
3. Mirror it in `preview3d/light/primitives.py` with the same part names, or record its absence in [The Two Renderers](../RENDERERS.md) — a capability in one renderer only is a bug unless it is written down.
4. Document its spec and its part tree in this file; `npm run build`.

Planned: `book`, `screen` (window screen for Vaske Komarnici — design it against that site's product configurator).

## Design Decisions

- **Unknown types, axes and malformed colour lists fail loudly** (root Rule #1) — a typo in a spec throws with the valid values, it never renders an empty scene silently.
- **Shaft and tip get their own material each.** Sharing one would make a later opacity change on the shaft silently dim the tip; the parts layer would clone anyway, but a model should not depend on that rescue.
- **Specs are plain JSON** so they cross the Python↔JS bridge untouched — the Python side never constructs geometry, only specs.
