# Cinematics

**Script:** [Cinematics (script)](../cinematics.js)

**Flow:** [diagram](../__flow/cinematics.md)

## Purpose

Cinematic scene GENERATORS — a master rule for a whole family of scenes, never one hand-authored descriptor per case (root Rule #19). The Five Stations "generalizes to any axis on demand" (PLAN.md) — the cube has 13 of them, and hand-authoring 13 near-identical JSON descriptors would be exactly the enumeration Rule #19 forbids. This module computes the scene descriptor for ANY axis of a model instead: the geometry (vertex positions, the side-on camera angle, which OTHER parts to fade) is all derived from the model's own data, so a new axis is a function argument, not a new file.

Pure data — no three.js import, matching the rest of the model layer (`directions.js`, `modelscene.js`, `switcher.js`).

## Connections

### Uses
- [Directions](directions.md) — `canonicalToken`, `oppositeToken`, `parseDirection`
- [Model Scene](modelscene.md) — `GROUP_PATHS`, `KIND_ORDER`, `TIER_ORDER` — the part paths a fade/position track addresses

### Used by
- [Source (folder)](../___src.md) — exported through the public API
- [Cinematics (Python mirror)](../../preview3d/__about/cinematics.md) — the mirror implementation; both read `shared/spec.json` for the radial factors and switcher stop names, and `tests/test_model_parity.py` runs the two head to head on the same model and axis
- `shared/scenes.json` — the shipped `five_stations` scene is one baked instance of `buildFiveStationsScene(buildCubeModel(), '+x+y+z')`

## Exports

- `STOPS` — the switcher's stop names, re-exported from `shared/spec.json`
- `buildFiveStationsScene(model, axisId, duration = 8.0)` — the descriptor below

## Design Decisions

- **One function, not thirteen scenes.** Every number the descriptor needs — vertex positions, the perpendicular viewing angle, which groups to fade — is DERIVED from the model and the chosen axis; nothing here is a per-axis constant.
- **A stop starts at its GEOMETRIC vertex (radial factor 1.0), not at its final station.** The model itself builds a stop's anchor already at its final radial factor; the scene's own `t = 0` key immediately overrides that to the vertex, which is what makes "the luminous stops pull INWARD from the geometric vertices, the fallen stops slide PAST them" a real animation rather than a caption.
- **Forces its own tier group to opacity 1, not only the individual axis.** A tier group might have opened dimmed (the `cube` view leaves `secondary` at 0.5), and opacity multiplies down; leaving the parent alone would make the axis invisible despite its own opacity being correct.
- **The camera looks ACROSS the axis, not down it.** Looking down an axis collapses it to a point — the whole reason `sideOnAngles` reads a `right` vector out of an orthonormal basis rather than the axis direction itself.
