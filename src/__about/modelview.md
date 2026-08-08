# Model View

**Script:** [Model View (script)](../modelview.js)

## Purpose

The model layer's viewer-side operations. Split out of `viewer.js` for the reason `parts.js` was: showing a MODEL is its own responsibility (validate it, turn it into content, work out what a view asks for, resolve an orientation), and the Viewer's job is to be a container (THE STRUCTURE LAW (rules/CODE.md)). Everything here takes what it needs and RETURNS what it decided; none of it reaches into a viewer, so it is testable and mirrors the Python side function for function.

## Connections

### Uses
- [Model](model.md) — `validate`
- [Parametric Primitives](primitives.md) — `buildPrimitive`
- [Model Scene](modelscene.md) — `buildSpec`, `findView`, `viewOpacities`
- [Orientations](orientations.md) — `orientationAxes`

### Used by
- [Viewer](viewer.md) — `showModel`, `setModelView`, `modelViews`, `setOrientation`, `setSwitcher`
- [Light Model View (Python mirror)](../../preview3d/light/__about/model_view.md) — the same functions, mirrored one-for-one

## Exports

- `buildModelContent(model)` — `{model: checked, content}`; validation happens HERE rather than at the call site so both renderers reject the same models
- `viewSettings(model, name)` — `{opacity, camera}`; a view is nothing more than that, which is what lets a scene TWEEN from one owner model into another instead of cutting between two built scenes
- `modelViewList(model)` — `[{name, label}, …]`, what a host builds buttons from
- `orientationQuaternion(identifier)` — the rotation for one of the cube's 24 orientations, or `null` for upright
- `checkRegister(model, register)` — refuses a register the model does not carry, where the register was CHOSEN rather than deep inside a switch group
- `requireModel(model, what)` — the "content first, view second" refusal

## Design Decisions

- **A model may carry fewer registers than the component offers.** Asking one of its seats for a vocabulary it does not have would fail deep inside a switch group; `checkRegister` refuses it at the point the register was chosen instead (No Error Masking (rules/CODE.md)).
- **Nothing here reaches into a Viewer instance.** Every function takes plain data (a model, an identifier) and returns plain data (opacities, a quaternion) — which is what lets it be tested standalone and lets the LIGHT renderer's `model_view.py` mirror it function for function despite touching neither Three.js nor Qt.
