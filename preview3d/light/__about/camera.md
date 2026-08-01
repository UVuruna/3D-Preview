# Light Camera

**Script:** [Light Camera (script)](../camera.py)
**Flow:** [diagram](../__flow/camera.md)

## Purpose

The orbit camera and the projection maths for the LIGHT renderer. Pure Python — no Qt. The angles, the presets and the framing rule are the same as the web core's (`src/viewer.js`), so the same spec lands at the same camera in both renderers.

## Connections

### Uses
- [Preview3d Package (folder)](../../___preview3d.md) — `resources.py` — view presets and camera defaults from `shared/spec.json`
- [Preview3d Package (folder)](../../___preview3d.md) — `vectors.py` (`Vec3`, `add`, `basis_from`, `dot`, `scale`, `sub`)

### Used by
- [Light Renderer](renderer.md) — projects world points through it; takes a `camera` object as a parameter and calls `.project()` / `.position`, without importing the `Camera` class itself
- [Light Widget](view.md) — drives it from mouse and keyboard, and imports the `Camera` class directly

## Classes

### Camera

#### Attributes
`target`, `distance`, `azimuth` (degrees), `elevation` (degrees), `projection`, `fov`, `ortho_height`, `aspect`.

Stored as **orbit parameters, not as a position and a matrix**: azimuth and elevation are exactly what the readout shows and what `orbit_by` changes, so there is one representation instead of a position that must be decomposed back into angles every time anyone asks where the camera is.

#### Methods
- `position` / `basis()`: the eye, and the orthonormal (forward, right, up); forward points from the target toward the eye
- `look_along(direction)`: aim down a direction without changing distance
- `orbit_by`, `pan_by`, `zoom_by`: movement; pan steps are fractions of the visible height so they feel the same at any zoom
- `set_orbit(azimuth, elevation)`: look from an **absolute** direction at the same distance — what a snap view or a timeline needs, where `orbit_by` is what a drag or an arrow key needs. Elevation is clamped short of the poles
- `set_projection(kind)`: swaps while keeping the content the same size on screen
- `visible_height()` / `visible_height_at(depth)`: world height the viewport spans
- `fit(points, direction, margin)`: framing — see [flow diagram](../__flow/camera.md)
- `project(point, width, height)`: world point → screen x, y and depth in front of the eye
- `state()`: azimuth (normalised to -180..180), elevation, distance, projection

## Module functions

- `view_direction(name)`: a preset's direction vector, or raises with the available names
- `step_view(current, step)`: next preset in cycle order; from a free view, lands on an end

## Design Decisions

- **Elevation is clamped just short of the poles** (`_POLE_LIMIT = 89.99`). At exactly ±90° the horizontal component vanishes and azimuth becomes meaningless, so the view would snap unpredictably as the user passes over the top.
- **Orthographic has no foreshortening**, so `visible_height_at` ignores depth — which is why a label keeps its size as it recedes in that projection, and shrinks in perspective.
- **`project()` guards against a near-zero depth** (`safe = depth if abs(depth) > 1e-6 else 1e-6`) so a perspective divide never divides by exactly zero; it does NOT cull points behind the eye — that guard lives in [Light Renderer](renderer.md) (`NEAR_CULL`), because only the renderer knows whether a whole face or line should be dropped.
