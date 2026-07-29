# Cinematics

**Script:** [Cinematics (script)](cinematics.py)

## Purpose

Cinematic scene GENERATORS — a master rule for a whole family of scenes, never one hand-authored descriptor per case (root Rule #19). The Five Stations "generalizes to any axis on demand" (PLAN.md, Extra 3D Views) — the cube has 13 of them, and hand-authoring 13 near-identical JSON descriptors in `shared/scenes.json` would be exactly the enumeration Rule #19 forbids. This module computes the scene descriptor for ANY axis of a model instead: the geometry (vertex positions, the side-on camera angle, which OTHER parts to fade) is all derived from the model's own data, so a new axis is a function argument, not a new file.

Pure Python — no Qt. The JS mirror is `src/cinematics.js`; both read `shared/spec.json` for the radial factors and switcher stop names, and `tests/test_model_parity.py` runs the two head to head on the same model and axis and compares the descriptor exactly.

## Connections

### Uses
- [Directions](directions.md) — `canonical_token`, `opposite_token`, `parse_direction`
- [Light Camera](light/camera.md) — `Camera.look_along()`, reused ONLY for its trig (no Qt), so the side-on angle formula is not duplicated
- [Model Scene](model_scene.md) — `GROUP_PATHS`, `TIER_ORDER`, `KIND_ORDER` — the part paths a fade/position track addresses
- `resources.load_shared_spec()` — the radial factors (`switcher.radial`) and the axis tier lengths (`axisTiers`)

### Used by
- `shared/scenes.json` — the shipped `five_stations` scene is one baked instance of `build_five_stations_scene(build_cube_model(), "+x+y+z")`
- `demoapp/window.py`, `demo/index.html` — the Five Stations "generalize" control regenerates the descriptor live for whichever of the model's 13 axes the picker selects

## Functions

### `build_five_stations_scene(model, axis_id, *, duration=8.0)`

The Five Stations, played on ONE axis: the cube fades to a single line, the camera settles side-on, and the luminous/fallen beads slide from the geometric vertex (radial factor 1.0) to their radial stations (0.72 / 1.18).

```
axis        ← the model's axis whose id or opposite matches axis_id
azimuth,
elevation   ← angles of a camera looking ACROSS the axis (basis_from's "right"
              vector), not down it — looking down an axis collapses it to a point
tracks:
    camera.azimuth / camera.elevation   opening pose  →  side-on angle
    part.opacity on every OTHER tier, every sibling axis of this tier,
        every cell kind except centre, and the glass shell   →  0
        ("the cube fades until only the Sacred Axis line remains")
    part.opacity forced to 1 on this axis's own tier group, this axis,
        and the centre — regardless of which view the content opened on
    FOR EACH end × FOR EACH stop (luminous, fallen):
        part.position   vertex point  →  (hold)  →  station point
        part.opacity    0  →  1                      (the bead grows into place)
```

### `_find_axis(model, axis_id)`
Matches the model's own token or its opposite, so a host can name either end of an axis. Fails loudly, listing the axes that exist.

### `_side_on_angles(direction)`
`basis_from(direction)`'s `right` vector, read as a camera direction through `Camera.look_along()` — reused rather than re-derived, so the angle formula cannot drift from what `camera.py` already implements.

## Design Decisions

- **One function, not thirteen scenes.** Every number the descriptor needs — vertex positions, the perpendicular viewing angle, which groups to fade — is DERIVED from the model and the chosen axis; nothing here is a per-axis constant.
- **The shipped `five_stations` scene is baked, not computed at load.** `shared/scenes.json` still ships ONE ordinary JSON descriptor (matching every other shipped scene), and `tests/test_animation_parity.py::test_shipped_five_stations_matches_the_generator` pins that it is exactly what the generator produces — a drift here (a spec.json radial factor changed without regenerating) fails loudly instead of shipping a silently stale scene.
- **A stop starts at its GEOMETRIC vertex (radial factor 1.0), not at its final station.** The model itself builds a stop's anchor already at its final radial factor (0.72 / 1.18); the scene's OWN `t = 0` key immediately overrides that to the vertex, which is what makes "the luminous stops pull INWARD from the geometric vertices, the fallen stops slide PAST them" (PLAN.md) a real animation rather than a caption.
- **Forces its own tier group to opacity 1**, not only the individual axis — a tier group might have opened dimmed (the "cube" view leaves `secondary` at 0.5), and opacity multiplies down; leaving the parent alone would make the axis invisible despite its own opacity being correct.
