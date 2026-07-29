"""The model layer's viewer-side operations, for the LIGHT renderer.

Split out of view.py for the reason scene.py was: showing a MODEL is its own
responsibility (validate it, turn it into content, dress it per view, set the
Switcher, turn it to an orientation), and the widget's job is to be a widget.

Everything here takes what it needs and RETURNS what it decided; none of it
touches Qt or reaches into a widget, so the model half can be exercised without
a GUI and mirrors the web core (src/modelview.js) function for function.
"""

from .. import model_scene, orientations
from ..model import validate
from .primitives import build_primitive
from .scene import Node


def build_model_content(model: dict) -> tuple[dict, Node]:
    """A validated model as a ready-to-mount content root.

    Validation happens HERE rather than at the call site so both renderers
    reject the same models: a model is generated data, and a field that is
    quietly wrong would surface as a missing label three screens later (Rule 1).
    """
    checked = validate(model)
    root = Node(name="content")
    root.add(build_primitive(model_scene.build_spec(checked)))
    return checked, root


def view_settings(model: dict, name: str) -> tuple[dict[str, float], object]:
    """What a view asks for: per-part opacities, and where the camera stands.

    A view is nothing more than that, which is what lets a scene TWEEN from one
    owner model into another instead of cutting between two built scenes.
    """
    view = model_scene.find_view(model, name)
    return model_scene.view_opacities(model, name), view.get("camera")


def model_view_list(model: dict) -> list[dict]:
    return [
        {"name": view["name"], "label": view.get("label", view["name"])}
        for view in model["views"]
    ]


def orientation_basis(identifier: str | None):
    """The rotation for one of the cube's 24 orientations, or None for upright."""
    return orientations.orientation(identifier) if identifier else None


def check_register(model: dict | None, register: str) -> None:
    """A model may carry fewer registers than the component offers, and asking
    one of its seats for a vocabulary it does not have would fail deep inside a
    switch group. Refuse where the register was chosen instead."""
    if model and register not in model["registers"]:
        raise ValueError(
            f"Model {model['name']!r} has no register {register!r} — "
            f"it carries: {', '.join(model['registers'])}"
        )


def require_model(model: dict | None, what: str) -> None:
    if model is None:
        raise RuntimeError(
            f"{what}() needs a model — call show_model() first (content first, view second)"
        )
