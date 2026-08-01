# Switcher

**Script:** [Switcher (script)](../switcher.js)

## Purpose

Which vocabulary speaks, and which readings are lit. Two independent controls, per the owner's spec (PLAN.md, The Switcher):

| Control | Values | Does |
|---------|--------|------|
| `register` | `canon` / `myth` / `historical` / `movie` | swaps every visible label |
| `reading` | `luminous` / `fallen` / `both` | which radial stops are shown |

Both are **flat parameters**. Nothing here is a mode with its own code path: a switcher position resolves to a list of ordinary part operations — the same `showOnly` and `setPartVisible` a host could call by hand — so a timeline can drive `switcher.register` exactly like any other channel, and no renderer needs a second way of doing it.

## Connections

### Used by
- [Viewer](viewer.md) — `setSwitcher`, `switcherState`, and `_applySwitcher()` which runs `operations()` over `listParts()`
- [Source (folder)](../___src.md) — exported through the public API
- [Switcher (Python mirror)](../../preview3d/__about/switcher.md) — the mirror implementation

## The Convention It Works By

Stated in [Making Models](../../MODELS.md), and what makes ANY content switchable — including a consumer's own, not just what this component builds:

```
<seat>/
  luminous/                  ← a group named for the stop
    label:canon              ← one child per register, the first shown
    label:myth
    ...
  fallen/
    ...
```

## Exports

- `REGISTERS`, `READINGS`, `STOPS`, `DEFAULT_REGISTER`, `DEFAULT_READING`, `LABEL_PREFIX` — read from `shared/spec.json`
- `DEFAULT_STATE` — `{register, reading}`, frozen
- `normalise(state, register, reading)` — a complete, checked state; unknown values fail loudly
- `litStops(reading)` — anything that is not one stop lights all of them, which is what `'both'` means
- `operations(parts, state)` — for each part whose last path segment is a stop name: `['visible', path, lit]` then `['show_only', path, 'label:' + register]`, in that fixed order for every part

## Design Decisions

- **Matching is on the LAST path segment**, not on a remembered list of paths, so a switcher survives any content the convention is followed in and needs no bookkeeping across a content swap.
- **The register is checked against the MODEL's own list by the caller** ([Model View](modelview.md)'s `checkRegister`), not here — this module only knows what the component offers, not what a particular model carries.
- **Operations come back in a FIXED order** (`visible` before `show_only`, parts in `listParts()`'s tree order) so both renderers apply exactly the same sequence and cannot diverge on an intermediate frame.
