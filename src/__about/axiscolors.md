# Axis Colours

**Script:** [Axis Colours (script)](../axiscolors.js)

**Flow:** [diagram](../__flow/axiscolors.md)

## Purpose

The colour of an axis end — and therefore of the seat it points at — COMPUTED from the poles it lies between. Owner decree 2026-07-28, and a direct application of root Rule #19: a colour per axis would be twenty-six invented values to keep in sync, where four rules cover every direction the cube has.

## Connections

### Uses
- [Directions](directions.md) — `cubeTokens`, `tierOf`, `tokenLetters`

### Used by
- [Cube Model](cubemodel.md) — dressing all 26 directions
- [Source (folder)](../___src.md) — exported through the public API
- [Axis Colours (Python mirror)](../../preview3d/__about/axis_colors.md) — the mirror implementation; both read `poles` and `axisColors` from `shared/spec.json` and round the same way (`Math.round`, matched in Python), so they arrive at the same hex

## Exports

- `MOONLIGHT`, `THIN`, `INK`, `DEEPEN`, `SACRED`, `MIN_POLE_DISTANCE`, `MIN_SEAT_DISTANCE` — read from `shared/spec.json`'s `axisColors` block
- `hexToRgb(color)` / `rgbToHex(rgb)` — `'#rrggbb'` conversion, fails loudly on an unusable string
- `mix(a, b, t)` — move `t` of the way from colour `a` to colour `b`, per channel
- `blend(colors)` — the per-channel mean; one colour blends to itself, which is what makes the primary case the same rule as the others rather than an exception
- `polesOf(token)` — the pole hues a direction token lies between, in the token's own order
- `colorFor(token, tier)` — the rule below
- `distance(a, b)` — straight-line RGB distance, good enough to prove two colours differ
- `verifyPalette(colors)` — the collision rule, enforced
- `deriveAll()` — every one of the cube's 26 directions dressed by geometry alone, verified before returning

## The Collision Rule

The moonlight thinning is not decoration. A naive two-pole blend can land on a hue the palette already spends (the blue+yellow case the canon names), and two seats wearing one colour is a lie about the structure. Thinning the whole edge family toward a pale moonlight, and deepening the vertex family toward ink, moves both off the saturated pole ring so the collision cannot happen by construction rather than by luck — `verifyPalette` fails loudly if it ever does anyway (root Rule #1).

## Design Decisions

- **`blend` of one colour is that colour.** The one-pole case needs no special branch — it is the two/three-pole rule with an identity blend.
- **The sacred dress is not applied in `deriveAll()`.** Which body diagonal is sacred is a model's statement about meaning, not something the cube's own geometry knows — `cubemodel.js` applies it afterward.
- **Distance is plain RGB Euclidean, not perceptual (e.g. Lab).** It only has to prove two colours are NOT the same colour, which straight-line RGB does well enough for the six-pole range this palette lives in.
- **Rounding matches JavaScript's `Math.round`, not Python's banker's rounding**, so the same formula in both languages produces the same hex on an exact tie — pinned by `tests/test_model_parity.py`.
