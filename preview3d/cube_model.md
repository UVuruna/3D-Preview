# Cube Model

**Script:** [Cube Model (script)](cube_model.py)

## Purpose

The thirteen-axis cube model, COMPUTED — the model the four owner views are
views OVER.

**The four owner models are four VIEWS over ONE model, never four hand-built
scenes** (PLAN.md, The Four Owner Models). This module builds that model: 13
axes (3 face + 6 edge + 4 vertex), 27 seats (6 + 12 + 8 + the centre), every
colour derived, every position derived, and the four views.

Nothing here is a stored file (root Rule #19). The geometry follows from the
cube, the colours follow from the poles, and the words follow from a small seed
vocabulary of the SIX poles:

```
words for a seat named by TOKEN, in register R:

    IF token is the centre -> the register's centre pair
    poles    <- the signed letters of the token
    luminous <- join(R[pole].luminous for each pole, " · ")
    fallen   <- join(R[pole].fallen   for each pole, " · ")
```

Twelve words per register become fifty-four seats.

## Connections

### Uses
- [Directions](directions.md) — the axes, the tokens, the seat positions
- [Axis Colours](axis_colors.md) — `derive_all()` and the sacred dress
- [Model](model.md) — validates before returning
- [Model Scene](model_scene.md) — `GROUP_PATHS`, which a view's short group
  names expand through

### Used by
- [Model Panel](../demoapp/model_panel.md) — the demo model
- DOMY Watch's exporter — with its own vocabulary

### Mirrored by
- `src/cubemodel.js`

## Functions

### `build_cube_model(...)`

| Argument | Default | Meaning |
|----------|---------|---------|
| `name`, `label` | `cube13`, `The Thirteen Axes` | identity |
| `size` | `1.0` | the cube's edge; every length and radius is a fraction of it |
| `sacred` | `"+x+y+z"` | which body diagonal leaves the six-colour palette; `None` leaves all four human |
| `registers` | all four | the vocabularies the model carries |
| `vocabulary` | `DEMO_VOCABULARY` | `register -> {pole or "centre": (luminous, fallen)}` |
| `views` | `DEFAULT_VIEWS` | the owner models |

Returns a validated model. A vocabulary with a hole fails HERE, not later as a
blank label nobody can explain.

### `DEFAULT_VIEWS`

| View | Shows | Camera |
|------|-------|--------|
| `primary` | the 3 face axes | `+x+y+z` |
| `secondary` | the 6 edge axes at their TRUE angles, face axes faint behind | `+x+y+z` |
| `tertiary` | the 4 vertex diagonals, the sacred one dressed and sized apart | `-x+y` |
| `cube` | everything, glass shell at 0.12, all 27 seats through it | `+x+y+z` |

## Design Decisions

- **A consumer supplies the WORDS, never the geometry.** DOMY Watch calls this
  with its own canon, so its sixty-five terms stay in DOMY and this gadget stays
  content-agnostic. What ships here is a neutral demo vocabulary that shows the
  structure and claims nothing.
- **A seat's position is its token's un-normalised vector times half the cube.**
  One rule places a face centre, an edge midpoint and a vertex — and puts each
  seat exactly where the axis end of the same name points.
- **The tertiary view stands PERPENDICULAR to the sacred diagonal.** Looking
  down an axis collapses it to a point, which is exactly what the isometric view
  does to `+x+y+z`.
- **A view sets every group explicitly, including to zero.** Leaving one out
  would let a family stay lit from the view before it.
- **The centre seat wears the sacred dress whether or not a sacred axis was
  named**, because it is where every axis crosses.
