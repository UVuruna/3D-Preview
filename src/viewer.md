# Viewer

**Script:** [Viewer (script)](viewer.js)

## Purpose

The 3D Preview container: owns the renderer, both cameras, orbit controls, studio lighting, the optional ground grid, and the lifecycle of whatever content is shown. Everything a consumer embeds *is* one `Viewer` instance, and every host control — button, key, Python method — routes through one of its methods.

## Connections

### Uses
- [Parametric Primitives](primitives.md) — builds computed shapes from `show()` specs
- [Parts](parts.md) — the part operations are thin delegations
- [Timeline](animation.md) — the loaded animation scene; the viewer applies its samples
- [Source (folder)](___src.md) → `views.js`, `grid.js`, `keyboard.js`
- Three.js addons: `OrbitControls`, `GLTFLoader`, `GLTFExporter`, `RoomEnvironment`

### Used by
- [Source (folder)](___src.md) — exported through the public API (`mount()`)
- [Preview3D Widget](../preview3d/widget.md) — every Python method maps onto one method here

## Classes

### Viewer

#### Attributes
- `options`: instance config — `VIEWER_DEFAULTS` overridden by the constructor argument (background, fov, fitMargin, dampingFactor, view, projection, grid, keyboard, stateInterval)
- `perspectiveCamera` / `orthographicCamera`: both exist for the life of the viewer; `camera` points at the active one
- `projection`: `'perspective'` | `'orthographic'`
- `viewName`: the active preset, or `'free'` once the user orbits away
- `gridEnabled` / `gridStep`: grid state; the step is the rounded cell size
- `_content`: a `Group` holding the current object — swapped atomically by `_setContent()`
- `_contentVersion`: bumped on every content swap; a host watches it to know when to re-read the part list

#### Content
- `show(spec)`: display a parametric primitive; `{type: 'model', url}` delegates to `loadModel()`
- `loadModel(url)` / `loadModelData(base64)`: async glTF/GLB load. The base64 form is the PySide6 path, since Chromium blocks `fetch()` on `file://` URLs
- `exportGLB()`: current content as a binary glTF `Blob`

#### Parts
`listParts()`, `setPartVisible(path, visible)`, `setPartOpacity(path, alpha)`, `setPartPosition(path, position)`, `setPartStroke(path, progress)`, `showOnly(groupPath, childName)`, `removePart(path)` — see [Parts](parts.md) and [Making Models](../MODELS.md). The last two are M3's additions: an absolute position (the mirror of `Node.position` in the LIGHT renderer), and 0..1 of a line part's own length drawn from its start toward its end — the Hexagram X-ray triangles' "draw themselves" effect and the Five Stations beads' slide, both `part.position` / `part.strokeProgress` in [Animation Scenes](../SCENES.md).

#### Camera
- `setView(name)` / `stepView(±1)`: jump to or cycle the presets
- `setProjection(kind)`: swap projection while keeping the content the same apparent size
- `orbitBy(azimuth°, elevation°)`: move around the content; the point looked at stays put
- `setOrbit(azimuth°, elevation°)`: look from an **absolute** direction at the same distance — what a snap view or a timeline wants, where `orbitBy` is what a drag or an arrow key wants
- `panBy(dx, dy)`: slide the view; steps are fractions of the visible height, so they feel identical at any zoom
- `zoomBy(factor)`: `> 1` zooms in
- `fitView()` / `resetView()`: frame the content (algorithm below)
- `cameraState()`: azimuth, elevation, distance, view, projection, grid state, content version
- `onCameraChange(callback)`: subscribe; fires immediately with the current state and returns an unsubscribe function

#### Animation
- `setAnimation(descriptor)`: load a scene — keyframes over flat parameters, see [Animation Scenes](../SCENES.md). Loaded paused at t = 0 with that instant already applied; `null` clears
- `playAnimation()`, `pauseAnimation()`, `toggleAnimation()`, `stopAnimation()`, `seekAnimation(0…1)`, `stepFrame(±1)`, `setSpeed(x)`, `jumpToEnd()` — with no scene loaded, every one is a documented no-op
- `animationState()` / `onAnimationChange(callback)`: playback state, and a subscription that fires immediately and returns an unsubscribe function

#### Appearance & lifecycle
`setBackground(color)` (CSS colour or `'transparent'`), `setGrid(enabled)`, `requestRender()`, `dispose()`.

`setBackground` also **paints the container** behind the canvas and reports the colour in the viewer state. Both matter: resizing clears the canvas backing store for at least one frame, and whatever sits behind it is what the user sees in that gap — a transparent container over a white host surface is a white flash on every resize. Reporting the colour lets an embedding host paint its own surface to match without restating it. See `tests/test_background_flash.py`.

## Framing Algorithm (fitView)

Measures the content's real **silhouette** from the view direction, then pulls the camera back until that silhouette fills the frustum — in BOTH axes, so a wide container is actually used.

```
basis ← orthonormal (right, up, forward) from the view direction
        forward points from the content toward the camera
        (world +Z replaces world up as the reference for a straight top/bottom view)

PASS 1 — extent:
FOR EACH point OF content (see below):
    project onto (right, up, forward) → track min/max
center ← middle of that extent

PASS 2 — distance:
tanY ← tan(fov / 2);  tanX ← tanY × aspect
FOR EACH point:
    need ← depth + max(|up offset| / tanY, |right offset| / tanX) × fitMargin
    distance ← max(distance, need)

camera ← center + forward × distance;  orbit target ← center
IF orthographic: frustum height ← 2 × max(halfHeight, halfWidth / aspect) × fitMargin
```

A "point" is a real vertex for meshes, and the four screen-parallel corners for billboard sprites — they turn to face the camera, so their world geometry says nothing about their size.

**Why not the bounding box or sphere** (a few lines shorter each): both measure the enclosing solid, not the shape. The axes gizmo's box corners sit at `(±L, ±L, ±L)` where the gizmo has nothing at all, framing it at roughly 55% of the space it should fill. **And why per-point rather than aggregate:** `halfDepth + halfHeight / tan(fov/2)` assumes the widest point is also the nearest, which for anything viewed corner-on it is not — that assumption alone costs about a third of the frame. Both passes run once per content swap, never per frame.

## Projection Switching

Switching keeps the content the same size on screen: the visible height at the orbit target is measured before the swap and reproduced after it — as a frustum height for the orthographic camera, and as a camera distance for the perspective one (perspective has no zoom knob; apparent size *is* distance).

`OrbitControls` binds to one camera at construction and reads its projection type for zoom behaviour, so a switch builds fresh controls and copies the target across.

**Orthographic is not a style choice.** It is the only projection in which a cube viewed down its body diagonal produces a geometrically exact regular hexagon; under perspective the six corner radii differ by about 25% at a 45° field of view. Measured: silhouette corner-radius spread 1.001x orthographic versus 1.269x perspective.

## Playing a Scene

The [Timeline](animation.md) resolves values; the viewer applies them, and that split is what lets the identical descriptor drive the LIGHT renderer too.

```
EACH FRAME (and after every transport command):
    FOR EACH {channel, path, value} IN timeline.values():
        camera.* → remember;  everything else (including part.position,
            part.strokeProgress) → apply immediately
    IF any camera channel appeared:
        place the camera absolutely from azimuth / elevation / dolly
```

Two things make a scene content-independent:

- **`camera.dolly` is a factor of the scene's own framing**, captured when the scene is loaded (`_reframeAnimation()` frames the content the way the presets would, then remembers the distance). One descriptor therefore plays correctly on a 1-unit cube and on a 100-unit model.
- **Both baselines come from ONE quantity.** The orthographic frustum height is derived from the perspective framing distance rather than from its own silhouette fit — otherwise a scene that switches projection mid-flight would jump in size at the switch.

A scene owns the camera outright while loaded, so a resize always re-frames and re-applies, where an un-animated viewer leaves a user-moved camera alone.

**Showing new content clears the loaded scene.** A scene is written against the parts of specific content; keeping it would mean driving paths that need not exist any more, and failing from inside `show()` rather than anywhere the host could act on it. Content first, scene second.

## Design Decisions

- **Render-on-demand:** `_tick()` runs every frame but renders only when `controls.update()` reports movement (orbiting / damping inertia) or `_dirty` is set. Idle preview = idle GPU. A playing scene marks the frame dirty itself.
- **Camera and playback notifications are rate-limited** to `stateInterval` (80 ms) while something is moving — a drag, damping inertia or a playing scene — with a final state the moment it stops. A 60 Hz stream over the Qt bridge buys nothing a readout can show.
- **Runtime environment lighting:** `RoomEnvironment` through `PMREMGenerator` gives PBR materials a neutral studio look with **no HDR asset** (root Rule #19), plus one directional light for definition.
- **Content disposal on swap:** `_clear()` walks the outgoing content and disposes geometry, materials and textures — repeated `show()` calls cannot leak GPU memory.
- **The grid lives outside the content group**, so enabling it never changes how the content is framed.
- **A resize re-frames, but only while the framing is still the viewer's own.** Framing depends on the aspect ratio, so narrowing the container clips content that used to fit — but once the user has orbited, panned or zoomed, that view is theirs and a resize must not throw it away. The signal is the controls' `start` event, not `change`: damping raises `change` for a frame or two after a *programmatic* camera move, which would mark the view as the user's the instant the viewer framed it itself.
