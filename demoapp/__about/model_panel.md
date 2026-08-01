# Model Panel

**Script:** [Model Panel (script)](../model_panel.py)

## Purpose

The demo app's MODEL controls: the four owner models (as views over one
model), the Switcher (register and reading), and the 24-orientation stepper.

Its own widget rather than another block inside [Demo Window](window.md),
because it is its own responsibility (root Rule #20): everything here drives
a MODEL ([Making Models](../../MODELS.md)), and none of it means anything for
a plain primitive scene. The window owns the stage and the renderer switch;
this owns the model controls. Like the parts panel, it holds no state of its
own beyond what it has already shown — the viewer is the authority, and
`set_viewer` re-points it at the other renderer without any control knowing
which one it is driving.

## Connections

### Uses
- [Preview3d Package (folder)](../../preview3d/___preview3d.md) — `build_cube_model`, `orientation_ids`, `READINGS`, `REGISTERS`

### Used by
- [Demo Window](window.md) — the MODEL, REGISTER, READING and ORIENTATION sections

## Classes

### ModelPanel

#### Attributes
- `DEMO_MODEL` (module level) — the neutral thirteen-axis cube the gadget ships, built once via `build_cube_model()`; a consumer passes its own vocabulary to the same builder (root Rule #19 — the geometry is computed, only the words are anyone's content)
- `_view` — the model's currently active view name, or `None` when nothing is shown; the only state the panel keeps

#### Methods
- `set_viewer(viewer)` — point at the other renderer; if a view was showing, re-show it on the new widget (a renderer swap starts from empty content), otherwise `clear()`
- `show_model(view=None)` — load the demo model and open it on `view` (its first view by default); resets the Switcher and orientation readouts; calls `on_activate` if the caller supplied one
- `clear()` — nothing model-shaped is on screen any more; untick every button group
- `_show_view(name)` — only the FIRST press actually builds the model (`show_model`); a later press is a cheap re-dress via `set_model_view`
- `_switch(register, reading)` — one call into `viewer.set_switcher`
- `_step_orientation(step)` / `_set_orientation(identifier)` — walk `orientation_ids()` by ±1, wrapping; `None` means upright

## Design Decisions

- **Only the first press builds.** A view is a cheap re-dress of content already built, so pressing another view calls `set_model_view` rather than rebuilding several hundred parts.
- **`on_activate` tells the window the model took the stage**, so the window drops the primitive spec it would otherwise replay on a renderer swap — see [Demo Window](window.md)'s `_on_model_shown`.
