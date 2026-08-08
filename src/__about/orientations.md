# Orientations

**Script:** [Orientations (script)](../orientations.js)

**Flow:** [diagram](../__flow/orientations.md)

## Purpose

The cube's twenty-four orientations, COMPUTED. A cube can be set down in exactly 24 ways, and they are the product of two choices, not a table of 24 matrices to copy: pick which face points up (6), then how far it is spun about that direction (4). Compute, Don't Generate (rules/CODE.md) in its plainest form — define how the piece moves and every position follows.

Also here: `snapAngles`, which turns any direction into the azimuth and elevation a camera must stand at to look down it — the snap views, including the four body diagonals no preset covers.

## Connections

### Uses
- [Directions](directions.md) — `parseDirection`

### Used by
- [Model View](modelview.md) — `orientationAxes` → `orientationQuaternion`
- [Viewer](viewer.md) — `stepOrientation`
- [Source (folder)](../___src.md) — exported through the public API
- [Orientations (Python mirror)](../../preview3d/__about/orientations.md) — the mirror implementation

## Exports

- `FACE_ORDER` — the six faces in the shared enumeration order, from `shared/spec.json`
- `SPINS` (4)
- `orientationIds()` — all 24 ids, in the order a stepped auto-advance walks them
- `orientationAxes(identifier)` — `[right, up, forward]` for `<face>:<spin>`
- `stepOrientation(identifier, step)` — next/previous id, wrapping
- `snapAngles(direction)` — `{azimuth, elevation}` in degrees for a camera looking DOWN `direction`

## Design Decisions

- **Each orientation is named `<face>:<spin>`**, e.g. `'+y:0'` (the identity) or `'-z:2'`, enumerated in the shared face order with spins 0..3 — so "the next orientation" means the same thing in both renderers.
- **The degenerate-case reference (`WORLD_FORWARD` vs `WORLD_UP`) matches what the cameras use.** "Which way is spin 0" for a face pointing straight up or down is one decision shared with `Viewer._viewBasis()`, not two formulas that could quietly disagree.
- **`snapAngles`' elevation is clamped to `POLE_LIMIT` (89.99°), never a full 90°.** A camera parked exactly at the pole loses a well-defined azimuth (gimbal-adjacent), so the clamp keeps orbiting meaningful even for a body-diagonal snap view.
