"""Locating the data files that ship with the package.

Everything bundled lives in exactly one of two places: an installed wheel
(`preview3d/<name>/`, force-included by pyproject.toml) or a repo checkout
(`<project root>/<name>/`). One resolver serves the web bundle and the shared
palette rather than each growing its own copy of the same two-location search.
"""

import json
from pathlib import Path

_PACKAGE = Path(__file__).parent
_PROJECT = _PACKAGE.parent


def bundled_dir(name: str) -> Path:
    """Directory `name` as shipped, wherever it ended up."""
    for candidate in (_PACKAGE / name, _PROJECT / name):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        f"3D Preview resource directory {name!r} not found in "
        f"{[str(_PACKAGE / name), str(_PROJECT / name)]}"
    )


def load_shared_spec() -> dict:
    """The values both renderers must agree on — see shared/spec.json."""
    return json.loads((bundled_dir("shared") / "spec.json").read_text(encoding="utf-8"))


def load_shared_scenes() -> list[dict]:
    """The animation scenes that ship with the component — see SCENES.md.

    The same file the web core bundles, so both renderers play the same scenes.
    """
    data = json.loads((bundled_dir("shared") / "scenes.json").read_text(encoding="utf-8"))
    return data["scenes"]
