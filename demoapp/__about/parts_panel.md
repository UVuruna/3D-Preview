# Parts Panel

**Script:** [Parts Panel (script)](../parts_panel.py) ·
**Flow:** [diagram](../__flow/parts_panel.md)

## Purpose

A scrollable list with one row per element of whatever is currently shown,
carrying the two controls a host actually needs — a visibility checkbox and
an opacity slider — plus a SOLO button on group rows with more than one
child.

## Connections

### Uses
- [Preview3D Widget](../../preview3d/__about/widget.md) — `list_parts`, `set_part_visible`, `set_part_opacity`, `show_only`

### Used by
- [Demo Window](window.md) — the PARTS section

## Classes

### PartsPanel
Deliberately NOT scrollable itself — the whole control panel scrolls as one
column, so the window has a single scrollbar and this panel contributes
almost nothing to the window's minimum height.

#### Attributes
- `_solo: dict[str, int]` — per-group solo cursor (`SOLO_ALL = -1` means "show every child")
- `_children: dict[str, list[str]]` — each group path's direct children, from `_group_children(parts)`

#### Methods
- `set_viewer(viewer)` — point at another renderer's widget, then `reload()`
- `reload()` — rebuild for NEW content; solo state belongs to the old scene and is cleared
- `refresh()` — re-read the parts and rebuild the rows, **keeping** solo state
- `_rebuild(parts)` — clears and repopulates the row list from a fresh `list_parts()` callback
- `_build_row(part)` — indented by `part["depth"] * INDENT_PX`; a drawable part gets the opacity slider, a group with 2+ children gets the SOLO button
- `_solo_label(group_path)` — `"solo"` when nothing is soloed, else `"{index+1}/{count}"`
- `_cycle_solo(group_path)` — the solo algorithm; see [flow](../__flow/parts_panel.md)

### Module function `_group_children(parts)`
Maps every group path to the list of its direct children's names, by
splitting each part's path on its last `/`.
