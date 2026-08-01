# Cube Model

**Script:** [Cube Model (script)](../cubemodel.js)

## Purpose

The thirteen-axis cube model, COMPUTED — the model the four owner views are views OVER. Nothing here is a stored file (root Rule #19): the geometry follows from the cube's own direction grammar, the colours follow from the poles, and the words follow from a small seed vocabulary of the six poles plus the centre. Twelve words per register become fifty-four seats.

A consumer supplies the WORDS, never the geometry — DOMY Watch's exporter calls this with its own canon, so its terms stay in DOMY and this gadget stays content-agnostic. `DEMO_VOCABULARY` is a neutral demo that shows the structure and claims nothing.

## Connections

### Uses
- [Axis Colours](axiscolors.md) — `deriveAll()` and the `SACRED` dress
- [Directions](directions.md) — the axes, the tokens, the seat positions
- [Model](model.md) — validates before returning
- [Model Scene](modelscene.md) — `GROUP_PATHS`, which a view's short group names expand through

### Used by
- [Source (folder)](../___src.md) — exported through the public API
- [Cube Model (Python mirror)](../../preview3d/__about/cube_model.md) — the mirror implementation

## Exports

- `REGISTERS` — the four vocabularies, read from `shared/spec.json`
- `JOIN` (`' · '`) — the separator a compound seat's words are joined with
- `CENTRE`, `ROOT_NAME`, `GLASS_OPACITY`
- `DEMO_VOCABULARY` — `register -> {pole or 'centre': [luminous, fallen]}`
- `DEFAULT_VIEWS` — the four owner models, see below
- `buildCubeModel(options)` — the builder

## `buildCubeModel(options)`

| Option | Default | Meaning |
|--------|---------|---------|
| `name`, `label` | `cube13`, `The Thirteen Axes` | identity |
| `size` | `1` | the cube's edge; every length and radius is a fraction of it |
| `sacred` | `'+x+y+z'` | which body diagonal leaves the six-colour palette; `null` leaves all four human |
| `registers` | all four | the vocabularies the model carries |
| `vocabulary` | `DEMO_VOCABULARY` | must cover every register with the six poles and the centre — a hole fails HERE, not later as a blank label |
| `views` | `DEFAULT_VIEWS` | the owner models |

Builds 13 axes (3 face + 6 edge + 4 vertex, from `cubeAxes(1|2|3)`), 27 cells (6 + 12 + 8 + the centre, from `cubeTokens(1|2|3)` plus one centre entry) and expands each view's short group names (`primary`, `glass`, …) into full opacity maps via `GROUP_PATHS`, defaulting every unmentioned group to 0 so a view can never leave a family lit from the one before it. Returns the result through `validate()`.

## `DEFAULT_VIEWS`

| View | Shows | Camera |
|------|-------|--------|
| `primary` | the 3 face axes | `+x+y+z` |
| `secondary` | the 6 edge axes at their TRUE angles, face axes faint behind | `+x+y+z` |
| `tertiary` | the 4 vertex diagonals, the sacred one dressed and sized apart | `-x+y` — perpendicular to the sacred diagonal, since looking down it collapses it to a point |
| `cube` | everything, glass shell at `GLASS_OPACITY` (0.12), all 27 seats through it | `+x+y+z` |

## Design Decisions

- **A seat's position is its token's un-normalised vector times half the cube.** One rule places a face centre, an edge midpoint and a vertex — and puts each seat exactly where the axis end of the same name points.
- **The centre seat wears the sacred dress whether or not a sacred axis was named**, because it is where every axis crosses.
- **A view sets every group explicitly, including to zero** (`expandView`) — leaving one out would let a family stay lit from the view before it.
- **`checkVocabulary` fails at build time, not at render time.** A missing word for a register/pole pair would otherwise surface as a blank label three screens later.
