"""3D Preview — an embeddable 3D viewer with two interchangeable renderers.

`Preview3DWidget`      — the web core (Three.js in QWebEngineView): loads
                         glTF/GLB files, real materials, GPU rendering, and the
                         same code runs in a browser.
`Preview3DLightWidget` — QPainter software 3D: no browser engine, no GPU, no
                         file loading; parametric scenes only.

Both take the same scene specs, play the same animation descriptors, expose the
same methods and emit the same camera and playback state. See RENDERERS.md for
how to choose.

The MODEL layer (`model`, `model_scene`, `cube_model`, `directions`,
`axis_colors`, `orientations`, `switcher`) is pure Python and imports no Qt at
all, so a consumer's exporter can build and validate a model without a GUI —
which is exactly what DOMY Watch's Character-Cube exporter does.
"""

from .cinematics import build_five_stations_scene
from .cube_model import build_cube_model
from .directions import cube_axes, cube_tokens, hidden_from, parse_direction, tier_of, vertex_neighbors
from .light import Preview3DLightWidget
from .light.animation import NO_ANIMATION
from .model import ModelError, load_schema, validate
from .model_scene import build_spec
from .orientations import orientation_ids, snap_angles
from .resources import load_shared_scenes, load_shared_spec
from .switcher import DEFAULT_STATE as SWITCHER_DEFAULT, READINGS, REGISTERS
from .widget import Preview3DWidget

__all__ = [
    "Preview3DWidget",
    "Preview3DLightWidget",
    "NO_ANIMATION",
    "load_shared_scenes",
    "load_shared_spec",
    # The model layer — no Qt, usable from an exporter script.
    "ModelError",
    "REGISTERS",
    "READINGS",
    "SWITCHER_DEFAULT",
    "build_cube_model",
    "build_five_stations_scene",
    "build_spec",
    "cube_axes",
    "cube_tokens",
    "hidden_from",
    "load_schema",
    "orientation_ids",
    "parse_direction",
    "snap_angles",
    "tier_of",
    "validate",
    "vertex_neighbors",
]
