# Light Camera

**Script:** [Light Camera (script)](camera.py)

## Purpose

The orbit camera and the projection maths for the LIGHT renderer. Pure Python — no Qt. The angles, the presets and the framing rule are the same as the web core's ([Viewer](../../src/viewer.md)), so the same spec lands at the same camera in both renderers.

## Connections

### Uses
- [Preview3d Package (folder)](../___preview3d.md) → `resources.py` — view presets and camera defaults from `shared/spec.json`

### Used by
- [Light Renderer](renderer.md) — projects world points through it
- [Light Widget](view.md) — drives it from mouse and keyboard

## Classes

### Camera

#### Attributes
`target`, `distance`, `azimuth` (degrees), `elevation` (degrees), `projection`, `fov`, `ortho_height`, `aspect`.

Stored as **orbit parameters, not as a position and a matrix**: azimuth and elevation are exactly what the readout shows and what `orbit_by` changes, so there is one representation instead of a position that must be decomposed back into angles every time anyone asks where the camera is.

#### Methods
- `position` / `basis()`: the eye, and the orthonormal (forward, right, up); forward points from the target toward the eye
- `look_along(direction)`: aim down a direction without changing distance
- `orbit_by`, `pan_by`, `zoom_by`: movement; pan steps are fractions of the visible height so they feel the same at any zoom
- `set_projection(kind)`: swaps while keeping the content the same size on screen
- `visible_height()` / `visible_height_at(depth)`: world height the viewport spans
- `fit(points, direction, margin)`: framing (below)
- `project(point, width, height)`: world point → screen x, y and depth in front of the eye
- `state()`: azimuth, elevation, distance, projection

## Framing Algorithm

```
basis ← orthonormal (forward, right, up) from the view direction
project every content point onto that basis
centre ← middle of the projected extent

tanY ← tan(fov / 2);  tanX ← tanY × aspect
FOR EACH projected point:
    need ← depth + max(|up offset| / tanY, |right offset| / tanX) × fitMargin
    distance ← max(distance, need)

target ← centre mapped back to world;  aim down the view direction
IF orthographic: frustum height ← 2 × max(halfHeight, halfWidth / aspect) × fitMargin
```

Per-point, not aggregate: `halfDepth + halfHeight / tan(fov/2)` assumes the widest point is also the nearest, which for anything viewed corner-on it is not, and that assumption costs about a third of the frame.

## Design Decisions

- **Elevation is clamped just short of the poles.** At exactly ±90° the horizontal component vanishes and azimuth becomes meaningless, so the view would snap unpredictably as the user passes over the top.
- **Orthographic has no foreshortening**, so `visible_height_at` ignores depth — which is why a label keeps its size as it recedes in that projection, and shrinks in perspective.
