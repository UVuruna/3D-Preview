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

Identical to the web core's: `axes` (arm groups with `shaft`, `tip`, an optional `labels` switch group and any number of radial `stops`; an arm's direction is a token or a vector; its colour defaults to its pole hue, which only a one-letter token has), `cube` (`colors: "poles"` or six colours build six named `face:*` nodes; otherwise one `body`; optional `edges`), `group` (an empty node) and `marker` (a seat: a `body` sphere plus its stops). Universal fields `name`, `position`, `scale` and `children` apply to every spec.

## Tessellation

The web core hands geometry to a GPU; here every curved surface becomes explicit polygons:

| Shape | Built as |
|-------|----------|
| Arm shaft | cylinder, `SHAFT_SEGMENTS` quads |
| Arm tip | cone, `TIP_SEGMENTS` triangles plus a base fan |
| Joint | UV sphere, `SPHERE_SEGMENTS` × `SPHERE_RINGS` |
| Seat marker | UV sphere, `MARKER_SEGMENTS` × `MARKER_RINGS` — coarser on purpose: a model puts 27 of them on screen at a few percent of the cube across, where the extra facets are invisible and the polygons are not (a full sphere each would be two thirds of everything this renderer sorts) |
| Cube face | one quad, wound so its normal points outward |
| Cube edges | 12 segments — corner pairs differing along exactly one axis; the node carries `neutral.edgeOpacity` from `shared/spec.json`, matching the web core's line material |

The segment counts are the point where a shaft stops reading as faceted at normal preview sizes; raising them costs polygons for no visible gain.

## Design Decisions

- **An arm's direction is a grammar, not a lookup.** It used to be a six-entry table, which made the cube's six edge axes and four vertex diagonals inexpressible; see [Directions](../directions.md).
- **Orientation uses Rodrigues' formula** (`rotate_towards` in [Vectors](../vectors.md)) to map a shape built along +Y onto its axis — the same rotation the web core expresses as a quaternion. If the two disagreed, the same spec would draw differently in the two renderers.
- **The cone gets a base fan.** Without it, looking at an arm from behind shows straight through the tip, because nothing here culls back faces.
- **No colour is restated here.** The palette comes from `shared/spec.json`, and `tests/test_renderer_parity.py` fails if a pole colour appears in this file's source.
