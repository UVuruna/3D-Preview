# Model

**Script:** [Model (script)](model.py)

## Purpose

Loading and validating a MODEL — the content a consumer hands the viewer: axes,
seats and views. The full authoring guide is [Making Models](../MODELS.md); this
module is only the **interpreter of the schema**, and `src/model.js` is the same
interpreter in JavaScript.

The schema itself is DATA, in `shared/model_schema.json`. Stating it once is
what makes "it validates" mean the same thing on both sides: a consumer's
exporter — DOMY Watch builds the Character Cube this way — checks against the
same file the renderers read.

## Connections

### Uses
- [Directions](directions.md) — the `direction` field type
- `shared/model_schema.json`, `shared/spec.json`

### Used by
- [Cube Model](cube_model.md) — validates before returning
- [Light Model View](light/model_view.md) and the web core — validate before mounting

### Mirrored by
- `src/model.js`

## The Schema Language

Deliberately tiny — it exists to be read by two small interpreters, not to be a
general schema engine.

| Field key | Meaning |
|-----------|---------|
| `type` | a primitive (`string`, `number`, `boolean`, `vector3`, `direction`, `color`), `array`, `map`, or the name of a declared type |
| `required` | default false |
| `of` | element type, for `array` and `map` |
| `keys` | for `map`: `*` for any string, `@dotted.path` for a list in `shared/spec.json`, `$field` for a list on the model itself |
| `enum` | a literal list, or a `@`/`$` reference as above |
| `length` | for `array`: the exact number of entries |

The `$` form is what holds a model to its OWN declaration: a model carrying only
two registers is required to have exactly those two on every seat, and is not
forced to invent the other two.

## Functions

- `validate(model)` — check and return it unchanged, so a caller can write
  `model = validate(loaded)` and never hold an unchecked one
- `load(path)` — read a JSON file and validate it
- `load_schema()` — the schema as shipped, for a consumer that wants to inspect it
- `ModelError` — a `ValueError` subclass

## Design Decisions

- **Errors carry the PATH** — `model.axes[3].ends[1].names.canon`. A model is
  generated data; "invalid model" without a location is not something a
  consumer can act on (root Rule #1).
- **Unknown fields are refused**, not ignored: a misspelled field that validated
  would be a field nobody notices is missing.
- **Keys beginning with `_` are allowed everywhere**, so a generated model can
  carry `_comment` notes the way the shared JSON files do.
