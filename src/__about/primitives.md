# Parametric Primitives

**Script:** [Parametric Primitives (script)](../primitives.js)

**Flow:** [diagram](../__flow/primitives.md)

## Purpose

Simple shapes COMPUTED from plain-JSON specs — the Compute, Don't Generate (rules/CODE.md) workhorse of this project. No stored model files: an axes gizmo or a cube is a handful of parameters, and every variant (colours, lengths, labels) is derived live. `buildPrimitive(spec)` dispatches on `spec.type` and returns a `THREE.Group` whose children are **named**, so the [Parts](parts.md) API can address them one by one.

## Connections

### Uses
- [Text Label Sprites](labels.md) — text sprites for arm and stop labels
- [Directions](directions.md) — `canonicalToken`, `oppositeToken`, `parseDirection`, `tokenVector`, `vertexNeighbors`

### Used by
- [Viewer](viewer.md) — `show(spec)` calls `buildPrimitive()`
- [Model View](modelview.md) — `buildModelContent` builds a model's own spec tree through this
- [Source (folder)](../___src.md) — exported through the public API
- [Light Primitives (Python mirror)](../../preview3d/light/__about/primitives.md) — the same builders, same part names

## Universal Spec Fields

Honoured for every primitive, so an assembly is one JSON tree rather than host-side scene building:

| Field | Meaning |
|-------|---------|
| `name` | the part name this group is addressed by |
| `position` | `[x, y, z]` offset |
| `scale` | uniform scale factor |
| `children` | nested specs, built recursively |

## Directions

An arm's `axis` is a **direction token or a 3-vector**, resolved by the shared grammar in [Directions](directions.md). It used to be one of six hardcoded entries, which made the cube's six edge axes and four vertex diagonals inexpressible; the six face tokens are now the one-letter case of one rule rather than a table beside it, so every spec written against the old table still means exactly what it meant.

## The Pole Palette

`POLE_COLORS` — the owner's six hues (decree 2026-07-28), one table serving both the axes gizmo and the cube's faces, because a pole colour belongs to the **direction**, not to the shape pointing that way:

| Direction | Colour | | Direction | Colour |
|-----------|--------|-|-----------|--------|
| `+x` | orange `#F97316` | | `-x` | blue `#3B82F6` |
| `+y` | yellow `#EAB308` | | `-y` | purple `#A855F7` |
| `+z` | green `#22C55E` | | `-z` | red `#EF4444` |

An arm with no `color` wears its pole hue; a cube asks for the set by name with `colors: 'poles'`. A host therefore never restates the palette and can never drift out of sync with it. Only a **one-letter** token has a pole to inherit — an arm pointing down an edge or a diagonal must bring its own colour, or say so loudly, rather than be given a made-up one. Those colours are computed, never invented: [Axis Colours](axiscolors.md).

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

`label` may be a **string or an array of strings**. An array builds a switch group holding `label:0`, `label:1`, … with only the first visible — the "three legend terms for one arm tip, one shown at a time" case (see [Making Models](../../MODELS.md)).

`stops` is the model layer's richer form: each is `{name, anchor, labels}` where `labels` maps register to text. It builds a switch group NAMED for the stop, holding `label:<register>` children at that anchor — which is what the [Switcher](switcher.md) drives, and how the radial law becomes geometry rather than a caption. The anchor is computed by [Model Scene](modelscene.md), so the same shape serves an arm and a seat and the builders stay dumb.

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

The build algorithm per arm is in the [flow diagram](../__flow/primitives.md).

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

### `hexagram` — The Hexagram X-ray Overlay

The two triangles a cube's silhouette splits into when seen down a body diagonal (Scene 1, [Animation Scenes](../../SCENES.md)) — COMPUTED from the diagonal (Compute, Don't Generate (rules/CODE.md)), never per-scene coordinates.

| Field | Default | Meaning |
|-------|---------|---------|
| `diagonal` | *(required)* | a vertex direction token, e.g. `'+x+y+z'` |
| `size` | `1` | edge length of the cube it is drawn against |
| `upColor` | `axisColors.sacred` | the near pole's triangle |
| `downColor` | `neutral.joint` | the far pole's triangle |
| `lineWidth` | `hexagram.lineWidth` in `shared/spec.json` | stroke width |

Part tree: `hexagram/triangle:up`, `hexagram/triangle:down` — each ONE `LineSegments` holding all three sides, so a single `part.strokeProgress` on the path draws (or un-draws) the whole triangle at once. The corner-finding algorithm is in the [flow diagram](../__flow/primitives.md).

`vertexNeighbors`/`hiddenFrom` live in [Directions](directions.md) — the same geometry the Blindness view's 19-of-26 rule reads.

### Beads on an axis stop

A `stops` entry built through `buildAxes` (never through `marker`) also gets a small sphere: unlike a cell, an axis has no marker of its own, and "Five beads slide to their stations" (the Five Stations scene) needs something visible to slide. The bead-bearing stop is a **Mesh that also holds label children** — never a separate "bead" child — so the part tree matches the LIGHT renderer's `Node`, which carries both its own faces and its children on one object. `part.position` on the stop's own path slides the whole thing; radius is `stopHeight × modelScene.beadRadiusFactor`.

## Adding a Primitive

1. Write `buildName(spec)` — pure function, spec in, `Group` out; **name every child**; export a `NAME_DEFAULTS` object for its parameters.
2. Register it in the `BUILDERS` table.
3. Mirror it in `preview3d/light/primitives.py` with the same part names, or record its absence in [The Two Renderers](../../RENDERERS.md) — a capability in one renderer only is a bug unless it is written down.
4. Document its spec and its part tree in this file; `npm run build`.

Planned: `book`, `screen` (window screen for Vaske Komarnici — design it against that site's product configurator).

## Design Decisions

- **Unknown types, axes and malformed colour lists fail loudly** (No Error Masking (rules/CODE.md)) — a typo in a spec throws with the valid values, it never renders an empty scene silently.
- **Shaft and tip get their own material each.** Sharing one would make a later opacity change on the shaft silently dim the tip; the parts layer would clone anyway, but a model should not depend on that rescue.
- **Specs are plain JSON** so they cross the Python↔JS bridge untouched — the Python side never constructs geometry, only specs.
