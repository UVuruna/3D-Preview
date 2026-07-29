# Orientations

**Script:** [Orientations (script)](orientations.py)

## Purpose

The cube's twenty-four orientations, COMPUTED, plus the snap-view arithmetic.

A cube can be set down in exactly 24 ways, and they are the product of two
choices rather than a table of 24 matrices to copy (root Rule #19):

```
FOR EACH face in the shared face order:      # 6 choices of "which way is up"
    FOR spin in 0..3:                        # 4 quarter turns about it
        id      <- "<face>:<spin>"
        up      <- direction(face)
        ref     <- world +Z if up IS world up else world +Y
        right0  <- normalise(up x ref)
        right   <- right0 * cos(spin*90) + (up x right0) * sin(spin*90)
        forward <- right x up
        matrix  <- the matrix whose columns are right, up, forward
```

`+y:0` is the identity, so a freshly shown model starts unrotated without anyone
saying so.

PLAN.md's Scene 4 — the 24-orientations clock — is blocked on DOMY's
rotation-to-hour rule. The ENGINE feature ships now, so when that rule lands the
clock is a data drop rather than an engine change.

## Connections

### Uses
- [Directions](directions.md), [Vectors](vectors.md)
- `shared/spec.json` — `faceOrder`

### Used by
- [Light Model View](light/model_view.md) — the basis a snapped cube carries
- [Light Widget](light/view.md) — `set_orientation`, `step_orientation`, `snap_to`

### Mirrored by
- `src/orientations.js`

## Functions

- `orientation_ids()` — all 24, in the order a stepped auto-advance walks them
- `orientation(id)` — the rotation matrix
- `orientation_axes(id)` — where the cube's own +X, +Y and +Z end up
- `step_orientation(id, ±1)` — the next in enumeration order, wrapping
- `snap_angles(direction)` — `(azimuth, elevation)` for a camera looking DOWN a
  direction. A token works as well as a vector, so the four body diagonals that
  no view preset covers are one call away
- `is_rotation(matrix)` — orthonormal with determinant +1

## Design Decisions

- **A reflection would look perfectly plausible in a screenshot** and be wrong —
  the cube would come back mirrored. `is_rotation` exists so the tests can
  refuse one rather than trusting the construction.
- **Snapping an orientation does not re-frame.** A cube keeps its silhouette as
  it turns, and re-fitting on every step would make a stepped clock jitter.
- **The degenerate-case rule is the cameras' own** (world +Z stands in for world
  up when the direction IS world up), so "which way is spin 0" is one decision
  in this component rather than two.
