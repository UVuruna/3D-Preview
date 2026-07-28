"""3D Preview — an embeddable 3D viewer with two interchangeable renderers.

`Preview3DWidget`      — the web core (Three.js in QWebEngineView): loads
                         glTF/GLB files, real materials, GPU rendering, and the
                         same code runs in a browser.
`Preview3DLightWidget` — QPainter software 3D: no browser engine, no GPU, no
                         file loading; parametric scenes only.

Both take the same scene specs, play the same animation descriptors, expose the
same methods and emit the same camera and playback state. See RENDERERS.md for
how to choose.
"""

from .light import Preview3DLightWidget
from .light.animation import NO_ANIMATION
from .resources import load_shared_scenes, load_shared_spec
from .widget import Preview3DWidget

__all__ = [
    "Preview3DWidget",
    "Preview3DLightWidget",
    "NO_ANIMATION",
    "load_shared_scenes",
    "load_shared_spec",
]
