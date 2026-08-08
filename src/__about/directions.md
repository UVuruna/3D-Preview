# Directions

**Script:** [Directions (script)](../directions.js)

**Flow:** [diagram](../__flow/directions.md)

## Purpose

Every direction the cube has, from ONE rule. An arm used to be one of six hardcoded entries, which made the cube's six edge axes and four vertex diagonals literally inexpressible — the exact thing a 3D previewer exists to show (Compute, Don't Generate (rules/CODE.md): define how the pieces move, never enumerate the games).

A **token** is one or more distinct signed cube letters (`'+x'`, `'-z'`, `'+x+y'`, `'+x-z'`, `'+x+y+z'`, `'-x+y-z'`), and its direction is the NORMALISED sum of those letters. So `'+x'` is `(1,0,0)`, `'+x+y'` is `(1,1,0)/√2` — the true midpoint of the cube's +x/+y edge — and `'+x+y+z'` is `(1,1,1)/√3`, the true body diagonal. The six legacy tokens keep working because they are the one-letter case of the same rule, not a special case beside it. A raw unit vector is accepted anywhere a token is.

## Connections

### Uses
- `shared/spec.json` — `axisLetters`, `axisTiers`, `tierOrder`

### Used by
- [Axis Colours](axiscolors.md) — a token's poles
- [Cube Model](cubemodel.md) — the 13 axes and 26 seats
- [Model Scene](modelscene.md), [Model](model.md), [Orientations](orientations.md), [Parametric Primitives](primitives.md), [Cinematics](cinematics.md)
- [Source (folder)](../___src.md) — exported through the public API
- [Directions (Python mirror)](../../preview3d/__about/directions.md) — the same grammar in Python, reading the same spec

## Exports

- `LETTERS`, `LETTER_ORDER`, `AXIS_TIERS`, `TIER_ORDER` — read from `shared/spec.json`
- `tokenLetters(token)` — `[letter, sign]` pairs; rejects repeats and unknown letters
- `tokenVector(token)` — the UN-normalised sum; times half the cube, this is where the seat of that name sits
- `parseDirection(value)` — token or 3-vector to a UNIT direction
- `canonicalToken(token)` — the same direction with its letters in the cube's own order
- `oppositeToken(token)`, `isPositiveEnd(token)`
- `tierOf(token)` — `primary` / `secondary` / `tertiary` from the letter count; never `sacred`, that is a model's choice
- `cubeTokens(letters)` — all 6 / 12 / 8 tokens of that tier
- `cubeAxes(letters)` — all 3 / 6 / 4 axes as `[positive end, negative end]`
- `vertexNeighbors(vertex)` — the three vertices an edge away
- `hiddenFrom(vertex)` — the seven cells hidden behind that vertex's own view
- `tokenOf(vector)` — the token for a direction that IS one of the cube's 26

## Design Decisions

- **`sacred` is not derived.** It shares the vertex geometry with `tertiary`; which diagonal is sacred is a statement about meaning, and only a model can make it.
- **Canonical naming is enforced at the name, not at the lookup.** Two spellings of one direction resolving to two part paths would be a model whose parts move depending on how a host happened to write them.
- **Distinct-letter tokens are the whole grammar.** A malformed token (repeated letter, unknown letter, odd length) fails loudly naming what was wrong, rather than resolving to some other direction (No Error Masking (rules/CODE.md)).
