# Light Model View

**Script:** [Light Model View (script)](model_view.py)

## Purpose

The model layer's viewer-side operations, for the LIGHT renderer: validate a
model, turn it into content, work out what a view asks for, and resolve an
orientation to a basis.

Split out of [Light Widget](view.md) for the reason [Light Scene](scene.md) was:
showing a MODEL is its own responsibility, and the widget's job is to be a
widget (root Rule #20 / THE STRUCTURE LAW). Everything here takes what it needs
and RETURNS what it decided; none of it touches Qt or reaches into a widget, so
the model half can be exercised without a GUI.

## Connections

### Uses
- [Model](../model.md) — validation
- [Model Scene](../model_scene.md) — the spec a model becomes, and a view's opacities
- [Orientations](../orientations.md) — the 24 rotations
- [Light Primitives](primitives.md), [Light Scene](scene.md)

### Used by
- [Light Widget](view.md)

### Mirrored by
- `src/modelview.js` — function for function

## Functions

- `build_model_content(model)` — `(validated model, content root)`. Validation
  happens HERE rather than at the call site so both renderers reject the same
  models
- `view_settings(model, name)` — `(opacities by path, camera direction or None)`
- `model_view_list(model)` — `[{name, label}, …]`, what a host builds buttons from
- `orientation_basis(id)` — the rotation matrix, or `None` for upright
- `check_register(model, register)` — a model may carry fewer registers than the
  component offers; asking a seat for one it does not have would fail deep
  inside a switch group, so it is refused where it was chosen
- `require_model(model, what)` — content first, view second
