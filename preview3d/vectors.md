# Vectors

**Script:** [Vectors (script)](vectors.py)

## Purpose

Minimal 3-vector and 3×3-matrix arithmetic. Plain tuples and functions rather
than numpy: this component exists to keep consumers free of heavy dependencies,
and the scenes it draws are a few hundred polygons — far below the point where
vectorisation would pay.

It sits at the package root rather than inside `light/` because the pure model
layer needs the same arithmetic and belongs to neither renderer.

## Connections

### Used by
- [Directions](directions.md) — resolving tokens to unit directions
- [Orientations](orientations.md) — building the 24 rotation matrices
- [Light Camera](light/camera.md), [Light Renderer](light/renderer.md), [Light Primitives](light/primitives.md), [Light Scene](light/scene.md)

## Types

- `Vec3` — `(x, y, z)`
- `Mat3` — row-major `(row0, row1, row2)`. A rotation's **columns** are the
  images of the basis vectors, which is how `basis_matrix` builds one.

## Functions

- `add`, `sub`, `scale`, `dot`, `cross`, `length`, `normalize` — the usual ones;
  `normalize` raises on a zero-length vector rather than returning NaN (Rule #1)
- `basis_from(direction)` — orthonormal `(forward, right, up)` for a view
  direction, with world +Z standing in for world up on a straight top/bottom
  view, where the cross product would otherwise collapse
- `basis_matrix(right, up, forward)` — the matrix whose COLUMNS are those axes
- `mat_apply(matrix, point)`, `mat_multiply(a, b)` — `a · b` applies `b` first
- `rotate_towards(source, target, point)` — Rodrigues' formula, which orients a
  shape built along +Y onto an arbitrary axis exactly as the web core's
  quaternion does

## Design Decisions

- **A rotation is carried as `None` when there is none.** The renderer's walk
  skips the matrix entirely in that case, which is the overwhelmingly common
  one; paying a matrix multiply per vertex everywhere would cost real time with
  nothing to show for it (root Priority A).
