# Vectors

**Script:** [Vectors (script)](../vectors.py)

## Purpose

Minimal 3-vector and 3×3-matrix arithmetic. Plain tuples and functions
rather than numpy: this component exists to keep consumers free of heavy
dependencies, and the scenes it draws are a few hundred polygons — far below
the point where vectorisation would pay.

It sits at the package root rather than inside `light/` because the pure
model layer needs the same arithmetic and belongs to neither renderer.

## Connections

### Uses
- none (stdlib `math` only)

### Used by
- [Directions](directions.md) — resolving tokens to unit directions
- [Orientations](orientations.md) — building the 24 rotation matrices
- [Cinematics](cinematics.md) — `basis_from`, `scale`
- [Model Scene](model_scene.md) — `normalize`, `scale`
- [Light Camera](../light/__about/camera.md), [Light Renderer](../light/__about/renderer.md),
  [Light Primitives](../light/__about/primitives.md), [Light Scene](../light/__about/scene.md)

### Mirrored by
- none — the web core uses Three.js's own `Vector3`/`Matrix3`, so there is no
  hand-written JS counterpart to keep in step with

## Types

- `Vec3` — `(x, y, z)`
- `Mat3` — row-major `(row0, row1, row2)`. A rotation's **columns** are the
  images of the basis vectors, which is how `basis_matrix` builds one.

## Functions

- `add`, `sub`, `scale`, `dot`, `cross`, `length`, `normalize` — the usual
  ones; `normalize` raises on a zero-length vector rather than returning NaN
  (root Rule #1)
- `basis_from(direction)` — orthonormal `(forward, right, up)` for a view
  direction, with world +Z standing in for world up on a straight
  top/bottom view, where the cross product would otherwise collapse
- `basis_matrix(right, up, forward)` — the matrix whose COLUMNS are those
  axes
- `mat_apply(matrix, point)`, `mat_multiply(a, b)` — `a · b` applies `b`
  first
- `rotate_towards(source, target, point)` — Rodrigues' formula, which
  orients a shape built along +Y onto an arbitrary axis exactly as the web
  core's quaternion does

## Design Decisions

- **Plain tuples, not a `Vector3` class.** No method dispatch and no
  accidental mutation; functions instead of methods keep the arithmetic
  obviously value-based, matching how `Vec3`/`Mat3` are treated as data
  everywhere else in the model layer.
- **`normalize` raises on a zero-length vector** rather than returning NaN
  or an arbitrary zero vector — a silent NaN would propagate through every
  downstream computation and surface far from its cause (root Rule #1).
