# Axis Colours

**Script:** [Axis Colours (script)](../axis_colors.py)
**Flow:** [diagram](../__flow/axis_colors.md)

## Purpose

The colour of an axis end — and therefore of the seat it points at — COMPUTED
from the poles it lies between. Owner decree 2026-07-28, and a direct
application of root Rule #19: a colour per axis would be twenty-six invented
values to keep in sync, where four rules cover every direction the cube has.

## Connections

### Uses
- [Directions](directions.md) — a token's poles (`token_letters`) and its tier (`tier_of`, `cube_tokens`)
- [Arithmetic to Match JavaScript](jsmath.md) — `round_half_up`, so both languages round alike
- [Bundled Data](resources.md) — `load_shared_spec()` for `poles` and `axisColors`

### Used by
- [Cube Model](cube_model.md) — `derive_all()` dresses all 26 directions; `SACRED` marks the one diagonal a model singles out

### Mirrored by
- [src/axiscolors.js](../../src/__about/axiscolors.md)

## Functions

- `hex_to_rgb`, `rgb_to_hex`, `mix(a, b, t)`, `blend(colors)`
- `poles_of(token)` — the pole hues a token lies between, in its own order
- `color_for(token, tier)` — the rule (see the flow diagram)
- `derive_all()` — all 26, dressed by GEOMETRY alone, verified before returning.
  The sacred dress is deliberately not applied here: two seats may legitimately
  share white-gold, while two DERIVED seats sharing a colour is a defect
- `distance(a, b)`, `verify_palette(colors)` — the collision rule

## The Collision Rule

| Guard | Meaning |
|-------|---------|
| `minPoleDistance` (60) | no derived colour may sit this close to one of the six poles |
| `minSeatDistance` (12) | no two seats may collapse into one colour |

The closest pair is inherently the two body diagonals whose three poles are
complementary and therefore average to grey (currently 17 apart), which is
what the second threshold is set just below.

## Design Decisions

- **`blend` of one colour is that colour**, which is what makes the primary
  case the same rule as the others rather than an exception.
- **Rounding is JavaScript's**, not Python's, so the same formula in the two
  languages produces the same hex — pinned by `tests/test_model_parity.py`.
- **The moonlight thinning and ink deepening are not decoration.** A plain
  blend can land on a hue the palette already spends (`+x+y-z` — orange,
  yellow and red — averages to a few units from the orange pole), and two
  seats wearing one colour is a lie about the structure. Thinning the edge
  family and deepening the vertex family moves both off the saturated pole
  ring, so the collision cannot happen by construction rather than by luck —
  `verify_palette` refuses it anyway if it ever does (root Rule #1).
