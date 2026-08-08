# Bundled Data

**Script:** [Bundled Data (script)](../resources.py)

## Purpose

Locating the data files that ship with the package. Everything bundled lives
in exactly one of two places: an installed wheel (`preview3d/<name>/`,
force-included by `pyproject.toml`) or a repo checkout (`<project root>/<name>/`).
One resolver serves the web bundle and the shared palette rather than each
growing its own copy of the same two-location search.

## Connections

### Uses
- none (stdlib `json`, `pathlib` only)

### Used by
- every pure-Python module in this package that reads shared data:
  [Directions](directions.md), [Axis Colours](axis_colors.md),
  [Orientations](orientations.md), [Model](model.md), [Model Scene](model_scene.md),
  [Cube Model](cube_model.md), [Cinematics](cinematics.md), [Switcher](switcher.md)
- [Light Camera](../light/__about/camera.md), [Light Animation](../light/__about/animation.md),
  [Light Primitives](../light/__about/primitives.md), [Light Widget](../light/__about/view.md)
  — the LIGHT renderer reads the same spec at run time

## Functions

- `bundled_dir(name)` — directory `name` as shipped, wherever it ended up; a
  `FileNotFoundError` naming both candidate paths if neither exists
- `load_shared_spec()` — `shared/spec.json`, the values both renderers must
  agree on
- `load_shared_scenes()` — `shared/scenes.json`'s `scenes` list, the shipped
  animation scenes

## Design Decisions

- **Two documented locations, one search.** An installed wheel and a repo
  checkout put the bundled directories in different places; every caller
  that needs shared data goes through this one resolver instead of growing
  its own copy of the same two-candidate search (No Duplicate Code (rules/CODE.md)).
