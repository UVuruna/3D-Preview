# Model

**Script:** [Model (script)](../model.js)

**Flow:** [diagram](../__flow/model.md)

## Purpose

Loading and validating a MODEL — the content a consumer hands the viewer: axes, seats and views. The full authoring guide is [Making Models](../../MODELS.md); this module is only the **interpreter of the schema**, and `preview3d/model.py` is the same interpreter in Python.

The schema itself is DATA, in `shared/model_schema.json`. Stating it once is what makes "it validates" mean the same thing on both sides: a consumer's exporter — DOMY Watch builds the Character Cube this way — checks against the same file the renderers read.

## Connections

### Uses
- [Directions](directions.md) — the `direction` field type (`parseDirection`)
- `shared/spec.json`, `shared/model_schema.json`

### Used by
- [Cube Model](cubemodel.md) — validates before returning
- [Model View](modelview.md) — validates before mounting
- [Source (folder)](../___src.md) — exported through the public API
- [Model (Python mirror)](../../preview3d/__about/model.md) — the same interpreter in Python

## The Schema Language

Deliberately tiny — it exists to be read by two small interpreters, not to be a general schema engine.

| Field key | Meaning |
|-----------|---------|
| `type` | a primitive (`string`, `number`, `boolean`, `vector3`, `direction`, `color`), `array`, `map`, or the name of a declared type |
| `required` | default false |
| `of` | element type, for `array` and `map` |
| `keys` | for `map`: `*` for any string, `@dotted.path` for a list in `shared/spec.json`, `$field` for a list on the model itself |
| `enum` | a literal list, or a `@`/`$` reference as above |
| `length` | for `array`: the exact number of entries |

The `$` form is what holds a model to its OWN declaration: a model carrying only two registers is required to have exactly those two on every seat, and is not forced to invent the other two.

## Exports

- `TYPES`, `ROOT_TYPE` — the schema, as loaded from `shared/model_schema.json`
- `validate(model)` — check and return it unchanged, so a caller can write `model = validate(loaded)` and never hold an unchecked one

## Design Decisions

- **Errors carry the PATH** — `model.axes[3].ends[1].names.canon`. A model is generated data; "invalid model" without a location is not something a consumer can act on (root Rule #1).
- **Unknown fields are refused, not ignored.** A misspelled field that validated would be a field nobody notices is missing.
- **Keys beginning with `_` are allowed everywhere**, so a generated model can carry `_comment` notes the way the shared JSON files do.
