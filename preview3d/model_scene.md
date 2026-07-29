# Model Scene

**Script:** [Model Scene (script)](model_scene.py)

## Purpose

Model data to a scene SPEC — the one translation, in plain data.

A model says what EXISTS (axes, seats, words); a scene spec says what to DRAW
(primitives, names, colours). This module is the whole bridge, and it produces
nothing but the same JSON specs a host could have written by hand — so both
renderers build a model through the primitive builders they already have,
rather than each growing its own model renderer.

## Connections

### Uses
- [Directions](directions.md) — an end's unit direction
- `shared/spec.json` — `axisTiers`, `cellKinds`, `modelScene`, `switcher.radial`

### Used by
- [Cube Model](cube_model.md) — `GROUP_PATHS`, so a view's short group names and
  the tree's paths are one statement
- [Light Model View](light/model_view.md) and the web core

### Mirrored by
- `src/modelscene.js` — pinned against this one, exactly, by
  `tests/test_model_parity.py`

## The Tree

```
<root>/
  axes/     primary/ secondary/ tertiary/ sacred/     <- one group per tier
  cells/    faces/ edges/ vertices/ centre/           <- one group per kind
  glass                                               <- the shell
```

**Every group exists whether or not it has anything in it.** That skeleton is a
contract, not a convenience: a VIEW addresses those paths to say which family
speaks, so a missing group would be a view that fails halfway through instead of
one that dims nothing.

## Functions

- `build_spec(model)` — the whole model as one nested primitive spec
- `view_opacities(model, name)` — a view's opacity map keyed by FULL part path
- `find_view(model, name)` — or a failure listing the views that do exist
- `root_name(model)`, `outward(position)`
- `GROUP_PATHS` — short group name to part path

## Design Decisions

- **The radial law is geometry, not a caption.** An arm's `luminous` stop is
  anchored INSIDE the geometric end (0.72 of the arm) and its `fallen` stop PAST
  it (1.18), so a reading of *both* draws the five stations of the axis by
  itself.
- **Seats do not carry the radial law** — a seat IS a station — so a seat's two
  readings simply sit above and below its marker, which keeps them legible when
  twenty-seven are on screen at once.
- **Axes are one `axes` primitive each, with the joint off.** Thirteen gizmos
  would stack thirteen joints in one spot; the centre seat is the crossing point
  the model actually names.
- **A stop's anchor is computed here**, not by the primitive builder, so the
  same `stops` shape serves an arm and a seat and the builders stay dumb.
