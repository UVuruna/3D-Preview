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

## The Pole Palette

`POLE_COLORS` — the owner's six hues (decree 2026-07-28), one table serving both the axes gizmo and the cube's faces, because a pole colour belongs to the **direction**, not to the shape pointing that way:

| Direction | Colour | | Direction | Colour |
|-----------|--------|-|-----------|--------|
| `+x` | orange `#F97316` | | `-x` | blue `#3B82F6` |
| `+y` | yellow `#EAB308` | | `-y` | purple `#A855F7` |
| `+z` | green `#22C55E` | | `-z` | red `#EF4444` |

An arm with no `color` wears its pole hue; a cube asks for the set by name with `colors: 'poles'`. A host therefore never restates the palette and can never drift out of sync with it.

## Specs

### `axes` — Axes Gizmo

Up to 6 arms from the origin, each its own group. Defaults in `AXES_DEFAULTS`:

| Field | Default | Meaning |
|-------|---------|---------|
| `armLength` | `1` | arm length in scene units |
| `armRadius` | `0.03` | shaft radius |
| `arms` | all six poles, labelled `X+`…`Z−` | each: `{axis, color?, label?}`; omit `color` for the pole hue, omit `label` for a bare arm |

`label` may be a **string or an array of strings**. An array builds a switch group holding `label:0`, `label:1`, … with only the first visible — the "three legend terms for one arm tip, one shown at a time" case (see [Making Models](../MODELS.md)).

Part tree:

```
axes/
  joint
  arm:+x/
    shaft
    tip
    labels/          ← only when a label was given
      label:0  label:1  label:2
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

## Adding a Primitive

1. Write `buildName(spec)` — pure function, spec in, `Group` out; **name every child**; export a `NAME_DEFAULTS` object for its parameters.
2. Register it in the `BUILDERS` table.
3. Document its spec and its part tree in this file; `npm run build`. Nothing is mirrored in Python — `show_scene(spec)` passes any spec through.

Planned: `book`, `screen` (window screen for Vaske Komarnici — design it against that site's product configurator).

## Design Decisions

- **Unknown types, axes and malformed colour lists fail loudly** (root Rule #1) — a typo in a spec throws with the valid values, it never renders an empty scene silently.
- **Shaft and tip get their own material each.** Sharing one would make a later opacity change on the shaft silently dim the tip; the parts layer would clone anyway, but a model should not depend on that rescue.
- **Specs are plain JSON** so they cross the Python↔JS bridge untouched — the Python side never constructs geometry, only specs.
