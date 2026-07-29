# Model Panel

**Script:** [Model Panel (script)](model_panel.py)

## Purpose

The demo app's MODEL controls: the four owner models, the Switcher (register and
reading), and the orientation stepper.

Its own widget rather than another block inside [Demo Window](window.md),
because it is its own responsibility — everything here drives a MODEL
([Making Models](../MODELS.md)), and none of it means anything for a plain
primitive scene. The window owns the stage and the renderer switch; this owns
the model controls.

## Connections

### Uses
- [Preview3d Package (folder)](../preview3d/___preview3d.md) — `build_cube_model`,
  `orientation_ids`, the register and reading lists

### Used by
- [Demo Window](window.md)

## Classes

### ModelPanel

#### Attributes
- `DEMO_MODEL` (module level) — the neutral thirteen-axis cube the gadget ships.
  A consumer passes its own vocabulary to the same builder (root Rule #19 — the
  geometry is computed; only the words are anyone's content)

#### Methods
- `set_viewer(widget)` — point at the other renderer. A renderer swap starts
  from empty content, so a model that was on screen is SHOWN AGAIN on the new
  widget rather than left as ticked buttons over somebody else's scene
- `show_model(view)` — load the demo model and open it on a view
- `clear()` — nothing model-shaped is on screen any more; untick everything

## Design Decisions

- **Only the first press builds.** A view is a cheap re-dress of content already
  built, so pressing another view calls `set_model_view` rather than rebuilding
  seven hundred parts.
- **The panel holds no state the viewer could answer for**, beyond which view it
  last opened — which it needs in order to know whether a press is the first.
- **`on_activate` tells the window the model took the stage**, so the window
  drops the primitive spec it would otherwise replay on a renderer swap.
