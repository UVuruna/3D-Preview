# Directions

**Script:** [Directions (script)](../directions.py)
**Flow:** [diagram](../__flow/directions.md)

## Purpose

Every direction the cube has, from ONE rule. An arm used to be one of six
hardcoded entries in each renderer, which made the cube's six edge axes and
four vertex diagonals literally inexpressible — the exact thing a 3D
previewer exists to show (Compute, Don't Generate (rules/CODE.md): define how the pieces move, never
enumerate the games).

A TOKEN is one or more distinct signed cube letters ("+x", "-z", "+x+y",
"+x-z", "+x+y+z", "-x+y-z"), and its direction is the NORMALISED sum of those
letters. The six legacy tokens keep working because they are the one-letter
case of the same rule, not a special case beside it. A raw unit vector is
accepted anywhere a token is.

## Connections

### Uses
- [Vectors](vectors.md) — `Vec3`, `normalize`
- [Bundled Data](resources.md) — `load_shared_spec()` for `axisLetters`, `axisTiers`, `tierOrder`

### Used by
- [Axis Colours](axis_colors.md) — a token's poles and tier
- [Cube Model](cube_model.md) — the 13 axes and 26 seats
- [Cinematics](cinematics.md) — `canonical_token`, `opposite_token`, `parse_direction`
- [Model](model.md) — the `direction` field type
- [Model Scene](model_scene.md) — an end's unit direction
- [Orientations](orientations.md) — `parse_direction`
- [Light Primitives](../light/__about/primitives.md) — an arm's direction; `vertex_neighbors`/`hidden_from` for the hexagram overlay

### Mirrored by
- [src/directions.js](../../src/__about/directions.md) — the same grammar in JavaScript, reading the same spec

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
- `tier_of(token)` — `primary` / `secondary` / `tertiary` from the letter
  count. Never `sacred`: that is a model's choice of one vertex diagonal, not
  a geometry
- `cube_tokens(letters)` — all 6 / 12 / 8 tokens of that tier
- `cube_axes(letters)` — all 3 / 6 / 4 axes as `(positive end, negative end)`,
  each line named after the end whose first letter is written positive
- `token_of(vector)` — the token for a direction that IS one of the cube's 26
- `vertex_neighbors(vertex)` — the three vertices an edge away: flip exactly
  one of the vertex's own letters, keep the other two
- `hidden_from(vertex)` — the seven cells hidden behind that vertex's own
  view: the ANTIPODE, its three adjacent edges and its three adjacent faces

## Design Decisions

- **`sacred` is not derived.** It shares the vertex geometry with `tertiary`;
  which diagonal is sacred is a statement about meaning, and only a model can
  make it.
- **Canonical naming is enforced at the name, not at the lookup.** Two
  spellings of one direction resolving to two part paths would be a model
  whose parts move depending on how a host happened to write them.
