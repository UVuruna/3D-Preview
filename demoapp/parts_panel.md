# Parts Panel

**Script:** [Parts Panel (script)](parts_panel.py)

## Purpose

A scrollable list with one row per element of whatever is being shown, carrying the two controls a host actually needs — a visibility switch and an opacity slider — plus SOLO on group rows.

## Connections

### Uses
- [Preview3D Widget](../preview3d/widget.md) — `list_parts`, `set_part_visible`, `set_part_opacity`, `show_only`
- [Parts](../src/parts.md) — the part records it renders

### Used by
- [Demo Window](window.md) — the PARTS section

## Classes

### PartsPanel

#### Methods
- `reload()`: rebuild for NEW content — solo state belongs to the old scene and is cleared
- `refresh()`: re-read the parts and rebuild the rows, **keeping** solo state
- `_build_row(part)`: indented by `depth`; a drawable part gets the opacity slider, a group with two or more children gets the SOLO button
- `_cycle_solo(group_path)`: advance that group's solo index, wrapping back to "all"

## Solo Cycling

```
index ← current index for this group, + 1
IF index past the last child → index = ALL

IF index is ALL → set every child visible
ELSE            → show_only(group, children[index])
refresh()   # the child checkboxes would otherwise still show the old state
```

This is the "three legend terms on one axis tip, one shown at a time" case from [Making Models](../MODELS.md), reduced to one button.

## Design Decisions

- **`reload()` and `refresh()` are separate on purpose.** Solo state is meaningful across a refresh (the button must keep saying `2/3`) but meaningless across a scene change — collapsing the two loses the distinction and the solo indicator resets on every click.
- **Rows are rebuilt rather than updated in place.** The list is tens of rows and only changes on an explicit action; diffing widgets would be more code for no perceptible gain.
- **The panel never tracks visibility itself** — it re-reads the viewer after every change, so keyboard actions, host code and the panel can never disagree.
