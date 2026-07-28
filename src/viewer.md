# Viewer

**Script:** [Viewer (script)](viewer.js)

## Purpose

The 3D Preview container: owns the WebGL renderer, perspective camera, orbit controls (rotate / zoom / pan), studio lighting, and the lifecycle of whatever content is shown. Everything a consumer embeds *is* one `Viewer` instance.

## Connections

### Uses
- [Parametric Primitives](primitives.md) — builds computed shapes from `show()` specs
- Three.js addons: `OrbitControls`, `GLTFLoader`, `GLTFExporter`, `RoomEnvironment`

### Used by
- [Source (folder)](___src.md) — exported through the public API (`mount()`)
- [Preview3D Widget](../preview3d/widget.md) — every Python method maps onto one method here

## Classes

### Viewer

#### Attributes
- `options`: instance config — `VIEWER_DEFAULTS` overridden by the constructor argument (background, fov, fitMargin, dampingFactor, viewDirection)
- `renderer` / `scene` / `camera` / `controls`: the Three.js quartet
- `_content`: a `Group` holding the currently shown object — swapped atomically by `_setContent()`

#### Methods
- `show(spec)`: display a parametric primitive (`{type: 'axes' | 'cube', ...}`); `{type: 'model', url}` delegates to `loadModel()`
- `loadModel(url)`: async glTF/GLB load over HTTP(S)
- `loadModelData(base64)`: async glTF/GLB load from raw bytes — the PySide6 path, since Chromium blocks `fetch()` on `file://` URLs
- `exportGLB()`: current content as a binary glTF `Blob` (label sprites are viewer-side and not exported)
- `fitView()` / `resetView()`: frame the content (pseudocode below)
- `setBackground(color)`: CSS color or `'transparent'` (alpha clear + transparent container)
- `requestRender()`: mark dirty — actual rendering happens on the next tick
- `dispose()`: cancel the loop, release GPU resources, remove the canvas

## Framing Algorithm (fitView)

Measures the content's real **silhouette** from the view direction, then pulls the camera back until that silhouette fills the frustum — in BOTH axes, so a wide container is actually used.

```
basis ← orthonormal (right, up, forward) from viewDirection
        forward points from the content toward the camera
        (world +Z replaces world up as the reference for a straight top/bottom view)

FOR EACH object IN content:
    IF object is a billboard sprite:
        record its center, padded by half its scale in right and up
    ELSE:
        FOR EACH vertex: record vertex × worldMatrix
    record(point) = project onto (right, up, forward) → track min/max

halfW, halfH, halfD ← half the recorded extent in right / up / forward
target   ← center of the recorded extent
tanY ← tan(fov / 2);  tanX ← tanY × aspect
distance ← halfD + max(halfH / tanY, halfW / tanX) × fitMargin
camera   ← target + forward × distance
near/far ← distance / 100, distance × 100
```

**Why not the bounding box or sphere** (a few lines shorter each): both measure the enclosing solid, not the shape. The axes gizmo's box corners sit at `(±L, ±L, ±L)` where the gizmo has nothing at all, framing it at roughly 55% of the space it should fill. The vertex pass runs once per content swap — never per frame.

## Design Decisions

- **Render-on-demand:** `_tick()` runs every frame but renders only when `controls.update()` reports movement (orbiting / damping inertia) or `_dirty` is set. Idle preview = idle GPU.
- **Runtime environment lighting:** `RoomEnvironment` through `PMREMGenerator` gives PBR materials a neutral studio look with **no HDR asset** (root Rule #19), plus one directional light for definition.
- **Content disposal on swap:** `_clear()` walks the outgoing content and disposes geometry, materials and textures — repeated `show()` calls cannot leak GPU memory.
