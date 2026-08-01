# Model Scene

**Script:** [Model Scene (script)](../modelscene.js)

## Purpose

Model data to a scene SPEC — the one translation, in plain data. A model says what EXISTS (axes, seats, words); a scene spec says what to DRAW (primitives, names, colours). This module is the whole bridge, and it produces nothing but the same JSON specs a host could have written by hand — so both renderers build a model through the primitive builders they already have, rather than each growing its own model renderer.

## Connections

### Uses
- [Directions](directions.md) — an end's unit direction

### Used by
- [Cube Model](cubemodel.md) — `GROUP_PATHS`, so a view's short group names and the tree's paths are one statement
- [Cinematics](cinematics.md) — `GROUP_PATHS`, `KIND_ORDER`, `TIER_ORDER`
- [Model View](modelview.md) — `buildSpec`, `findView`, `viewOpacities`
- [Source (folder)](../___src.md) — exported through the public API
- [Model Scene (Python mirror)](../../preview3d/__about/model_scene.md) — pinned against this one, exactly, by `tests/test_model_parity.py`

## The Tree

```
<root>/
  axes/     primary/ secondary/ tertiary/ sacred/     ← one group per tier
  cells/    faces/ edges/ vertices/ centre/           ← one group per kind
  glass                                               ← the shell
```

**Every group exists whether or not it has anything in it.** That skeleton is a contract, not a convenience: a VIEW addresses those paths to say which family speaks, so a missing group would be a view that fails halfway through instead of one that dims nothing.

## Exports

- `TIER_ORDER`, `KIND_ORDER`, `AXES_GROUP`, `CELLS_GROUP`, `GLASS_GROUP`
- `GROUP_PATHS` — short group name (`'primary'`, `'glass'`, …) → full part path
- `rootName(model)`
- `findView(model, viewName)` — or a failure listing the views that do exist
- `viewOpacities(model, viewName)` — a view's opacity map keyed by FULL part path
- `buildSpec(model)` — the whole model as one nested primitive spec

## Design Decisions

- **The radial law is geometry, not a caption.** An arm's `luminous` stop is anchored INSIDE the geometric end (`RADIAL['luminous']` of the arm) and its `fallen` stop PAST it, so a reading of "both" draws the five stations of the axis by itself.
- **Seats do not carry the radial law** — a seat IS a station — so a seat's two readings simply sit above and below its marker (`cellLabelGap`), which keeps them legible when twenty-seven are on screen at once.
- **Axes are one `axes` primitive each, with the joint off.** Thirteen gizmos would stack thirteen joints in one spot; the centre seat is the crossing point the model actually names.
- **A stop's anchor is computed here, not by the primitive builder**, so the same `stops` shape serves an arm and a seat and the builders in `primitives.js` stay dumb.
