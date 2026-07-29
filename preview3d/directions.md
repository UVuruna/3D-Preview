# Directions

**Script:** [Directions (script)](directions.py)

## Purpose

Every direction the cube has, from ONE rule. An arm used to be one of six
hardcoded entries in each renderer, which made the cube's six edge axes and four
vertex diagonals literally inexpressible — the exact thing a 3D previewer exists
to show (root Rule #19: define how the pieces move, never enumerate the games).

```
a TOKEN is one or more distinct signed cube letters
its DIRECTION is the normalised sum of those letters

    "+x"      -> (1, 0, 0)                 a face normal
    "+x+y"    -> (1, 1, 0) / sqrt(2)       the midpoint of that edge
    "+x+y+z"  -> (1, 1, 1) / sqrt(3)       that body diagonal
```

The six legacy tokens keep working because they are the one-letter case of the
same rule, not a special case beside it. A raw unit vector is accepted anywhere
a token is.

## Connections

### Uses
- [Vectors](vectors.md) — normalisation
- `shared/spec.json` — `axisLetters`, `axisTiers`, `tierOrder`

### Used by
- [Axis Colours](axis_colors.md) — a token's poles
- [Cube Model](cube_model.md) — the 13 axes and 26 seats
- [Model Scene](model_scene.md), [Model](model.md), [Orientations](orientations.md)
- [Light Primitives](light/primitives.md) — an arm's direction

### Mirrored by
- `src/directions.js` — the same grammar in JavaScript, reading the same spec

## Functions

- `parse_direction(value)` — token or 3-vector to a UNIT direction; anything
  else fails loudly, naming what was wrong
- `token_letters(token)` — `(letter, sign)` pairs; rejects repeats and unknown
  letters, so a typo can never resolve to some other direction
- `token_vector(token)` — the UN-normalised sum. Times half the cube, this is
  where the seat of that name sits
- `canonical_token(token)` — the same direction with its letters in x, y, z
  order. `+y+x` and `+x+y` are one direction and must be one NAME
- `opposite_token(token)`, `is_positive_end(token)`
- `tier_of(token)` — `primary` / `secondary` / `tertiary` from the letter count.
  Never `sacred`: that is a model's choice of one vertex diagonal, not a geometry
- `cube_tokens(letters)` — all 6 / 12 / 8 tokens of that tier
- `cube_axes(letters)` — all 3 / 6 / 4 axes as `(positive end, negative end)`,
  each line named after the end whose first letter is written positive
- `token_of(vector)` — the token for a direction that IS one of the cube's 26

## Design Decisions

- **`sacred` is not derived.** It shares the vertex geometry with `tertiary`;
  which diagonal is sacred is a statement about meaning, and only a model can
  make it.
- **Canonical naming is enforced at the name, not at the lookup.** Two spellings
  of one direction resolving to two part paths would be a model whose parts move
  depending on how a host happened to write them.
