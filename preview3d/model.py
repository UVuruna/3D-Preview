"""Model loading and schema validation.

A MODEL is the content a consumer hands the viewer: axes, cells and views (see
MODELS.md). Its shape is stated once, as data, in `shared/model_schema.json` —
this module is only the interpreter of that statement, and `src/model.js` is the
same interpreter in JavaScript. Stating the schema once is what makes "it
validates" mean the same thing on both sides; a consumer's exporter (DOMY Watch
builds the Character Cube this way) checks against the same file the renderers
read.

Errors carry the PATH of the offending field — `axes[3].ends[1].names.canon` —
because a model is generated data and "invalid model" without a location is not
something anyone can act on (Rule 1).

Pure Python: no Qt, no renderer.
"""

import json
import math

from .directions import parse_direction
from .resources import bundled_dir, load_shared_spec

_SPEC = load_shared_spec()


def load_schema() -> dict:
    """The schema as shipped — read fresh so a consumer can inspect it too."""
    return json.loads((bundled_dir("shared") / "model_schema.json").read_text(encoding="utf-8"))


_SCHEMA = load_schema()
TYPES: dict = _SCHEMA["types"]
ROOT_TYPE: str = _SCHEMA["root"]


class ModelError(ValueError):
    """An invalid model, with the path of the field that broke the schema."""


def validate(model: dict) -> dict:
    """Check `model` against the schema and return it unchanged.

    Returning the model rather than a bool lets a caller write
    `model = validate(loaded)` and never hold an unchecked one.
    """
    _check(model, ROOT_TYPE, "model", model)
    return model


def load(path) -> dict:
    """Read a model JSON file and validate it."""
    with open(path, "r", encoding="utf-8") as handle:
        return validate(json.load(handle))


# ---- The interpreter --------------------------------------------------------


def _fail(where: str, message: str) -> None:
    raise ModelError(f"{where}: {message}")


def _resolve_list(reference, model: dict, where: str) -> list:
    """A literal list, or a reference to one.

    `@dotted.path` reads shared/spec.json (the registers and tiers the whole
    component agrees on); `$field` reads the model's own declaration, which is
    how a model that carries only two registers is held to exactly those two.
    """
    if isinstance(reference, list):
        return reference
    if not isinstance(reference, str):
        _fail(where, f"schema reference {reference!r} is neither a list nor a '@'/'$' path")
    if reference == "*":
        return []
    if reference.startswith("@"):
        node = _SPEC
        for part in reference[1:].split("."):
            node = node[part]
        return list(node)
    if reference.startswith("$"):
        return list(model.get(reference[1:]) or [])
    _fail(where, f"schema reference {reference!r} must start with '@' or '$'")
    return []


def _check(value, type_name: str, where: str, model: dict) -> None:
    if type_name in TYPES:
        _check_declared(value, TYPES[type_name], where, model)
        return
    if type_name == "string":
        if not isinstance(value, str) or not value:
            _fail(where, f"expected a non-empty string, got {value!r}")
    elif type_name == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            _fail(where, f"expected a finite number, got {value!r}")
    elif type_name == "boolean":
        if not isinstance(value, bool):
            _fail(where, f"expected true or false, got {value!r}")
    elif type_name == "vector3":
        if (not isinstance(value, (list, tuple)) or len(value) != 3
                or not all(isinstance(c, (int, float)) and math.isfinite(c) for c in value)):
            _fail(where, f"expected 3 finite numbers, got {value!r}")
    elif type_name == "direction":
        try:
            parse_direction(value)
        except ValueError as error:
            _fail(where, str(error))
    elif type_name == "color":
        if (not isinstance(value, str) or len(value) != 7 or value[0] != "#"
                or any(c not in "0123456789abcdefABCDEF" for c in value[1:])):
            _fail(where, f"expected a '#rrggbb' colour, got {value!r}")
    else:
        _fail(where, f"the schema names an unknown type {type_name!r}")


def _check_declared(value, declared: dict, where: str, model: dict) -> None:
    if "map" in declared:
        # A declared type may itself be a map (`names` is register -> seat);
        # it goes through the same body as a map FIELD so the two cannot diverge.
        _map_body(value, declared["map"], where, model)
        return
    fields = declared["fields"]
    if not isinstance(value, dict):
        _fail(where, f"expected an object with fields {', '.join(fields)}, got {value!r}")
    unknown = [key for key in value if key not in fields and not key.startswith("_")]
    if unknown:
        _fail(where, f"unknown field(s) {', '.join(sorted(unknown))} — the schema allows {', '.join(fields)}")
    for name, field in fields.items():
        if name not in value:
            if field.get("required"):
                _fail(where, f"missing required field {name!r}")
            continue
        _check_field(value[name], field, f"{where}.{name}", model)


def _check_field(value, field: dict, where: str, model: dict) -> None:
    kind = field["type"]
    if kind == "array":
        if not isinstance(value, list):
            _fail(where, f"expected a list, got {value!r}")
        if "length" in field and len(value) != field["length"]:
            _fail(where, f"expected exactly {field['length']} entries, got {len(value)}")
        allowed = _resolve_list(field["enum"], model, where) if "enum" in field else None
        for index, item in enumerate(value):
            _check(item, field["of"], f"{where}[{index}]", model)
            if allowed and item not in allowed:
                _fail(f"{where}[{index}]", f"{item!r} is not one of {', '.join(map(str, allowed))}")
        return
    if kind == "map":
        _map_body(value, field, where, model)
        return
    if "enum" in field:
        allowed = _resolve_list(field["enum"], model, where)
        if allowed and value not in allowed:
            _fail(where, f"{value!r} is not one of {', '.join(map(str, allowed))}")
    _check(value, kind, where, model)


def _map_body(value, field: dict, where: str, model: dict) -> None:
    if not isinstance(value, dict):
        _fail(where, f"expected an object, got {value!r}")
    keys = field.get("keys", "*")
    if keys != "*":
        required = _resolve_list(keys, model, where)
        missing = [key for key in required if key not in value]
        extra = [key for key in value if key not in required]
        if missing:
            _fail(where, f"missing entries for {', '.join(missing)}")
        if extra:
            _fail(where, f"unexpected entries {', '.join(sorted(extra))} — allowed: {', '.join(required)}")
    for key, item in value.items():
        _check(item, field["of"], f"{where}.{key}", model)
