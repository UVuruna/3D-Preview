# Light Primitives

**Script:** [Light Primitives (script)](primitives.py)

## Purpose

Builds the LIGHT renderer's scene from the **same JSON specs** the web core takes, producing the **same named part tree**. A host hands either renderer the identical scene description; see [Parametric Primitives](../../src/primitives.md) for the spec reference and [MODELS.md](../../MODELS.md) for the naming contract.

## Connections

### Uses
- [Light Scene](scene.md) — the nodes it produces
- [Preview3d Package (folder)](../___preview3d.md) → `resources.py` — the palette from `shared/spec.json`

### Used by
- [Light Widget](view.md) — `show_scene` calls `build_primitive`

## Specs

Identical to the web core's: `axes` (arm groups with `shaft`, `tip` and a `labels` switch group; an arm's colour defaults to its pole hue; `label` may be a string or a list), and `cube` (`colors: "poles"` or six colours build six named `face:*` nodes; otherwise one `body`; optional `edges`). Universal fields `name`, `position`, `scale` and `children` apply to every spec.

## Tessellation

The web core hands geometry to a GPU; here every curved surface becomes explicit polygons:

| Shape | Built as |
|-------|----------|
| Arm shaft | cylinder, `SHAFT_SEGMENTS` quads |
| Arm tip | cone, `TIP_SEGMENTS` triangles plus a base fan |
| Joint | UV sphere, `SPHERE_SEGMENTS` × `SPHERE_RINGS` |
| Cube face | one quad, wound so its normal points outward |
| Cube edges | 12 segments — corner pairs differing along exactly one axis |

The segment counts are the point where a shaft stops reading as faceted at normal preview sizes; raising them costs polygons for no visible gain.

## Design Decisions

- **Orientation uses Rodrigues' formula** (`rotate_towards` in `vectors.py`) to map a shape built along +Y onto its axis — the same rotation the web core expresses as a quaternion. If the two disagreed, the same spec would draw differently in the two renderers.
- **The cone gets a base fan.** Without it, looking at an arm from behind shows straight through the tip, because nothing here culls back faces.
- **No colour is restated here.** The palette comes from `shared/spec.json`, and `tests/test_renderer_parity.py` fails if a pole colour appears in this file's source.
