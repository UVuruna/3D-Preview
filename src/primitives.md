# Parametric Primitives

**Script:** [Parametric Primitives (script)](primitives.js)

## Purpose

Simple shapes COMPUTED from plain-JSON specs — the root Rule #19 workhorse of this project. No stored model files: an axes gizmo or a cube is a handful of parameters, and every variant (colors, lengths, labels) is derived live. `buildPrimitive(spec)` dispatches on `spec.type` and returns a `THREE.Group`.

## Connections

### Uses
- [Source (folder)](___src.md) → `labels.js` — text sprites for arm labels

### Used by
- [Viewer](viewer.md) — `show(spec)` calls `buildPrimitive()`

## Specs

### `axes` — Axes Gizmo

Up to 6 arms from the origin, each with its own color and label (the DOMY Watch use case). Defaults in `AXES_DEFAULTS`:

| Field | Default | Meaning |
|-------|---------|---------|
| `armLength` | `1` | arm length in scene units |
| `armRadius` | `0.03` | shaft radius |
| `arms` | 6 arms `+x −x +y −y +z −z`, distinct colors, labels `X+`…`Z−` | each: `{axis, color, label}`; omit `label` for a bare arm; pass fewer arms for a partial gizmo |

Build algorithm (per arm):

```
direction ← unit vector of arm.axis        (+x → (1,0,0), …)
rotation  ← quaternion mapping +Y onto direction
shaft     ← cylinder(armRadius, 0.8·L), rotated, centered at direction · 0.4·L
tip       ← cone(2.4·armRadius, 0.2·L), rotated, centered at direction · 0.9·L
label     ← text sprite at direction · 1.16·L, height 0.16·L, arm color
```

plus one neutral sphere at the origin as the joint.

### `cube` — Cube

Defaults in `CUBE_DEFAULTS`:

| Field | Default | Meaning |
|-------|---------|---------|
| `size` | `1` | edge length |
| `color` | `#818CF8` | single color for all faces |
| `colors` | `null` | optional 6 per-face colors, BoxGeometry order `[+x, −x, +y, −y, +z, −z]` |
| `edges` | `true` | soft translucent edge lines |

## Adding a Primitive

1. Write `buildName(spec)` — pure function, spec in, `Group` out; export a `NAME_DEFAULTS` object for its parameters.
2. Register it in the `BUILDERS` table.
3. Document its spec in this file; `npm run build`; mirror nothing in Python — `show_scene(spec)` already passes any spec through.

Planned: `book`, `screen` (window screen for Vaske Komarnici — design it against that site's product configurator).

## Design Decisions

- **Unknown types and axes fail loudly** (root Rule #1) — a typo in a spec throws with the list of valid values, it never renders an empty scene silently.
- **Specs are plain JSON** so they cross the Python↔JS bridge untouched — the Python side never constructs geometry, only specs.
