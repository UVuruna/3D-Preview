# Switcher

**Script:** [Switcher (script)](../switcher.py)

## Purpose

Which vocabulary speaks, and which readings are lit. Two independent
controls, per the owner's spec (PLAN.md, The Switcher):

| Control | Values | Does |
|---------|--------|------|
| `register` | `canon` / `myth` / `historical` / `movie` | swaps every visible label |
| `reading` | `luminous` / `fallen` / `both` | which radial stops are shown |

Both are **flat parameters**. Nothing here is a mode with its own code path:
a switcher position resolves to a list of ordinary part operations — the
same `show_only` and `set_part_visible` a host could call by hand — so a
timeline can drive `switcher.register` exactly like any other channel, and
no renderer needs a second way of doing it.

## Connections

### Uses
- [Bundled Data](resources.md) — `load_shared_spec()` for `switcher`

### Used by
- [Light Widget](../light/__about/view.md) — `set_switcher`, `switcher_state`

### Mirrored by
- [src/switcher.js](../../src/__about/switcher.md)

## The Convention It Works By

Stated in [Making Models](../../MODELS.md#switcher), and what makes ANY
content switchable — including a consumer's own, not just what this
component built:

```
<seat>/
  luminous/                  <- a group named for the stop
    label:canon              <- one child per register, the first shown
    label:myth
    ...
  fallen/
    ...
```

## Functions

- `normalise(state, register, reading)` — a complete, checked state; unknown
  values fail loudly
- `lit_stops(reading)` — anything that is not one stop lights all of them,
  which is what `both` means
- `operations(parts, state)` — the operations, in a FIXED order, so both
  renderers apply exactly the same sequence

## Design Decisions

- **Matching is on the last path segment**, not on a remembered list of
  paths, so a switcher survives any content the convention is followed in
  and needs no bookkeeping across a content swap.
- **The register is checked against the MODEL's own list** by the widget,
  not here: this module only knows what the component offers.
