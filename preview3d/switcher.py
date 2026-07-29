"""The Switcher — which vocabulary speaks, and which readings are lit.

Two independent controls, per the owner's spec:

    register   canon / myth / historical / movie — swaps every visible label
    reading    Luminous / Fallen / Both — 'both' draws the five-station
               radial layout, because the two stops are already at their
               two radii (see model_scene)

Both are FLAT parameters. Nothing here is a mode with its own code path: a
switcher position resolves to a list of ordinary part operations — the same
`show_only` and `set_part_visible` a host could call by hand — so a timeline can
drive `switcher.register` exactly like any other channel, and no renderer needs
a second way of doing it.

The convention it works by is stated in MODELS.md: a seat carries one group per
STOP (`luminous`, `fallen`), each holding one `label:<register>` per register.
Anything built that way is switchable, whether this component built it or a
consumer did.

Pure Python; the JS mirror is src/switcher.js.
"""

from .resources import load_shared_spec

_SPEC = load_shared_spec()
_SWITCHER: dict = _SPEC["switcher"]

REGISTERS: list[str] = list(_SWITCHER["registers"])
READINGS: list[str] = list(_SWITCHER["readings"])
STOPS: list[str] = list(_SWITCHER["stops"])
DEFAULT_REGISTER: str = _SWITCHER["defaultRegister"]
DEFAULT_READING: str = _SWITCHER["defaultReading"]

LABEL_PREFIX = "label:"

DEFAULT_STATE = {"register": DEFAULT_REGISTER, "reading": DEFAULT_READING}


def normalise(state: dict | None = None, register: str | None = None,
              reading: str | None = None) -> dict:
    """A complete, checked switcher state — unknown values fail loudly."""
    result = dict(state or DEFAULT_STATE)
    if register is not None:
        result["register"] = register
    if reading is not None:
        result["reading"] = reading
    if result["register"] not in REGISTERS:
        raise ValueError(
            f"Unknown register {result['register']!r} — available: {', '.join(REGISTERS)}"
        )
    if result["reading"] not in READINGS:
        raise ValueError(
            f"Unknown reading {result['reading']!r} — available: {', '.join(READINGS)}"
        )
    return result


def lit_stops(reading: str) -> list[str]:
    """Which radial stops a reading lights. Anything that is not one stop lights
    all of them, which is what 'both' means."""
    return [reading] if reading in STOPS else list(STOPS)


def operations(parts: list[dict], state: dict) -> list[tuple]:
    """The part operations that put `parts` into this switcher position.

    `parts` is a part list as either renderer reports it. Returns
    ('visible', path, on) and ('show_only', path, child) in a fixed order, so
    both renderers apply exactly the same sequence.
    """
    state = normalise(state)
    lit = lit_stops(state["reading"])
    child = LABEL_PREFIX + state["register"]
    result: list[tuple] = []
    for part in parts:
        path = part["path"]
        stop = path.rsplit("/", 1)[-1]
        if stop not in STOPS:
            continue
        result.append(("visible", path, stop in lit))
        result.append(("show_only", path, child))
    return result
