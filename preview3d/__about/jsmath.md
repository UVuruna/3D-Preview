# Arithmetic to Match JavaScript

**Script:** [Arithmetic to Match JavaScript (script)](../jsmath.py)

## Purpose

Arithmetic defined to match JavaScript's. Two implementations of one formula
must produce the same number, not nearly the same number: Python's built-in
`round` breaks ties to EVEN while JavaScript's `Math.round` breaks them UP,
so any formula that rounds — a frame index, a colour channel — would put the
two renderers one unit apart on an exact tie and nowhere else, which is the
hardest kind of drift to notice.

Deliberately small: this is the one place the difference is spelled out, so
no other module has to remember it (No Duplicate Code (rules/CODE.md)).

## Connections

### Uses
- none (stdlib `math` only)

### Used by
- [Axis Colours](axis_colors.md) — `mix()` and `blend()` round every channel
  through it, so a computed hex matches its JS counterpart exactly

### Mirrored by
- none — this module exists so PYTHON matches JavaScript's own native
  `Math.round`; there is nothing to mirror on the JS side

## Functions

- `round_half_up(value)` — JavaScript's `Math.round`: `floor(value + 0.5)`

## Design Decisions

- **Ties break UP, not to even.** The one-line difference from Python's
  built-in `round` is spelled out here once rather than left for every
  caller to remember.
