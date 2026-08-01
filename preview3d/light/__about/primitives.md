# Light Primitives

**Script:** [Light Primitives (script)](../primitives.py)
**Flow:** [diagram](../__flow/primitives.md)

## Purpose

Builds the LIGHT renderer's scene from the **same JSON specs** the web core takes, producing the **same named part tree**. A host hands either renderer the identical scene description; see `src/primitives.js` for the spec reference and [MODELS.md](../../../MODELS.md) for the naming contract.

## Connections

### Uses
- [Light Scene](scene.md) — `Face`, `Label`, `Node`, `Segment`, the nodes it produces
- [Preview3d Package (folder)](../../___preview3d.md) — `resources.py` — the palette and shared geometry constants from `shared/spec.json`
- [Preview3d Package (folder)](../../___preview3d.md) — `directions.py`: `canonical_token`, `opposite_token`, `parse_direction`, `token_vector`, `vertex_neighbors`
- [Preview3d Package (folder)](../../___preview3d.md) — `vectors.py`: `UP`, `add`, `cross`, `normalize`, `rotate_towards`, `scale`

### Used by
- [Light Widget](view.md) — `show_scene` calls `build_primitive`
- [Light Model View](model_view.md) — `build_model_content` calls `build_primitive` on the model's built spec

## Specs

Identical to the web core's: `axes` (arm groups with `shaft`, `tip`, an optional `labels` switch group and any number of radial `stops`; an arm's direction is a token or a vector; its colour defaults to its pole hue, which only a one-letter token has), `cube` (`colors: "poles"` or six colours build six named `face:*` nodes; otherwise one `body`; optional `edges`), `group` (an empty node), `marker` (a seat: a `body` sphere plus its stops) and `hexagram` (the two triangles a cube's silhouette splits into down a body diagonal — see the flow diagram). Universal fields `name`, `position`, `scale` and `children` apply to every spec.

## `hexagram` — The Hexagram X-ray Overlay

The Scene 1 cinematic ([SCENES.md](../../../SCENES.md)) needs a genuinely new shape — the Star-of-David triangles a cube's silhouette hexagon splits into, down a body diagonal — computed from the diagonal (root Rule #19), never per-scene coordinates. See the [flow diagram](../__flow/primitives.md) for the derivation.

Part tree: `hexagram/triangle:up`, `hexagram/triangle:down` — one `Node` each, holding all three `Segment`s, so a single `part.strokeProgress` on the path draws (or un-draws) the whole triangle at once (see [Light Renderer](renderer.md)). Colours default to `axisColors.sacred` (up) and `neutral.joint` (down) rather than inventing new hues; a scene may override both.

## Beads on an axis stop

`build_stop(stop, color, height, bead=False)` — called with `bead=True` only from `build_axes`. A bead-bearing stop carries its own sphere `Face`s directly on the SAME `Node` that holds its label children (never a separate child), so the part tree matches the web core's, where the equivalent stop is a `Mesh` that also has children. Unlike a cell, an axis stop has no marker of its own, and the Five Stations scene's "beads slide to their stations" needs something visible to slide — `part.position` on the stop's own path is what moves it. Radius is `height × modelScene.beadRadiusFactor`.

**A stop's own anchor lives on `Node.position`, not on the label's anchor** — the label anchors at the local origin instead. This is what lets `part.position` address a stop directly; it changes nothing about where anything renders, because the two compose identically (`here_offset = parent + node.position`, then the label's own zero anchor adds nothing further).

## Tessellation

The web core hands geometry to a GPU; here every curved surface becomes explicit polygons:

| Shape | Built as |
|-------|----------|
| Arm shaft | cylinder, `SHAFT_SEGMENTS` (14) quads |
| Arm tip | cone, `TIP_SEGMENTS` (16) triangles plus a base fan |
| Joint | UV sphere, `SPHERE_SEGMENTS` (12) × `SPHERE_RINGS` (6) |
| Seat marker | UV sphere, `MARKER_SEGMENTS` (8) × `MARKER_RINGS` (4) — coarser on purpose: a model puts 27 of them on screen at a few percent of the cube across, where the extra facets are invisible and the polygons are not (a full sphere each would be two thirds of everything this renderer sorts) |
| Cube face | one quad, wound so its normal points outward |
| Cube edges | 12 segments — corner pairs differing along exactly one axis; the node carries `neutral.edgeOpacity` from `shared/spec.json`, matching the web core's line material |

The segment counts are the point where a shaft stops reading as faceted at normal preview sizes; raising them costs polygons for no visible gain.

## Design Decisions

- **An arm's direction is a grammar, not a lookup.** It used to be a six-entry table, which made the cube's six edge axes and four vertex diagonals inexpressible; see the [Directions](../../__about/directions.md) module.
- **Orientation uses Rodrigues' formula** (`rotate_towards`, in `vectors.py`) to map a shape built along +Y onto its axis — the same rotation the web core expresses as a quaternion. If the two disagreed, the same spec would draw differently in the two renderers.
- **The cone gets a base fan.** Without it, looking at an arm from behind shows straight through the tip, because nothing here culls back faces.
- **No colour is restated here.** The palette comes from `shared/spec.json`, and `tests/test_renderer_parity.py` fails if a pole colour appears in this file's source.
