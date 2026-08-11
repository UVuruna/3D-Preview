# Light Model View

**Script:** [Light Model View (script)](../model_view.py)

## Purpose

The model layer's viewer-side operations, for the LIGHT renderer: validate a model, turn it into content, work out what a view asks for, and resolve an orientation to a basis.

Split out of [Light Widget](view.md) for the reason [Light Scene](scene.md) was: showing a MODEL is its own responsibility, and the widget's job is to be a widget (THE STRUCTURE LAW — rules/CODE.md). Everything here takes what it needs and RETURNS what it decided; none of it touches Qt or reaches into a widget, so the model half can be exercised without a GUI. Mirrored function-for-function by the web core's `src/modelview.js`.

This is a thin coordination layer — each function is a short, direct call into `model`, `model_scene`, `orientations` or `primitives`, with no multi-step algorithm of its own — so it stays Standard tier with no flow diagram.

## Connections

### Uses
- [Preview3d Package (folder)](../../___preview3d.md) — `model.validate()`, `model_scene.build_spec()` / `find_view()` / `view_opacities()`, `orientations.orientation()`
- [Light Primitives](primitives.md) — `build_primitive()`, to turn the model's spec into a content tree
- [Light Scene](scene.md) — `Node`, the content root it builds

### Used by
- [Light Widget](view.md) — `show_model`, `set_model_view`, `model_views`, `set_switcher` and `set_orientation` all delegate here

## Functions

- `build_model_content(model)` → `(validated model, content root)`. Validation happens HERE rather than at the call site so both renderers reject the same models (No Error Masking (rules/CODE.md) — a generated field that is quietly wrong should not surface three screens later as a missing label)
- `view_settings(model, name)` → `(opacities by path, camera direction or None)`
- `model_view_list(model)` → `[{name, label}, …]`, what a host builds buttons from
- `orientation_basis(identifier)` → the rotation matrix for one of the cube's 24 orientations, or `None` for upright
- `check_register(model, register)` — a model may carry fewer registers than the component offers; asking a seat for one it does not have would fail deep inside a switch group, so it is refused where it was chosen
- `require_model(model, what)` — raises if no model is loaded yet ("content first, view second")

## Design Decisions

- **Validation happens at `build_model_content`, not at the call site.** A model is generated data (e.g. by Watch Academy's exporter); rejecting a bad one where it enters the viewer means both renderers agree on what "valid" means, instead of each guessing at a malformed field independently.
- **Nothing here touches Qt.** Every function takes plain data and a model dict and returns plain data or a `Node` — so the model half of the LIGHT renderer is exercised by tests without constructing a widget.
