"""Demo window — the viewer stage plus every control the component exposes.

Doubles as the integration example: each control is one call into
Preview3DWidget, and the camera readout is one signal connection.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from preview3d import (
    NO_ANIMATION,
    Preview3DLightWidget,
    Preview3DWidget,
    build_five_stations_scene,
    load_shared_scenes,
    load_shared_spec,
)

from .flow_layout import FlowLayout, flow_size_policy
from .model_panel import DEMO_MODEL, ModelPanel
from .parts_panel import PartsPanel
from .theme import THEME

# The two interchangeable renderers — see RENDERERS.md.
RENDERERS = [
    ("web", "Web", Preview3DWidget, True),
    ("light", "Light", Preview3DLightWidget, False),
]

WINDOW = {
    "title": "3D Preview — Demo",
    "width": 1360,
    "height": 880,
    # The window must fit comfortably in half a screen. Nothing inside is
    # allowed to dictate a larger floor: the panel scrolls, the legend wraps,
    # and the stage may shrink to a thumbnail.
    "min_width": 560,
    "min_height": 420,
}
PANEL_WIDTH = 300
STAGE_MINIMUM = (220, 160)

# The demo scenes: parametric specs, not model files (root Rule #19).
DEMO_SCENES = [
    {"name": "Axes gizmo", "spec": {"type": "axes"}},
    {
        # Multiple labels per arm: the parts panel's `solo` button cycles them,
        # which is the "three legend terms for one axis tip" case from MODELS.md.
        # Colours are omitted so every arm wears its pole hue from the engine's
        # own table — the palette is never restated on the host side (Rule 19).
        "name": "Compass axes",
        "spec": {
            "type": "axes",
            "arms": [
                {"axis": "+x", "label": ["East", "Istok", "E"]},
                {"axis": "-x", "label": ["West", "Zapad", "W"]},
                {"axis": "+y", "label": ["Zenith", "Zenit", "Up"]},
                {"axis": "-y", "label": ["Nadir", "Nadir", "Down"]},
                {"axis": "+z", "label": ["North", "Sever", "N"]},
                {"axis": "-z", "label": ["South", "Jug", "S"]},
            ],
        },
    },
    {"name": "Cube", "spec": {"type": "cube", "colors": "poles"}},
    {
        # Dim a shell face in the parts panel and the core shows through.
        "name": "Cube + core",
        "spec": {
            "type": "cube",
            "name": "shell",
            "colors": "poles",
            "children": [{"type": "cube", "name": "core", "size": 0.45, "color": "#F5F5F5"}],
        },
    },
]

# The animation scenes ship with the component as DATA — the demo plays the
# very same descriptors both renderers read (shared/scenes.json, SCENES.md).
ANIMATIONS = load_shared_scenes()
SPEEDS = load_shared_spec()["animation"]["speeds"]

# Words rather than media glyphs: the bundled Inter subset has no ⏮ / ⏯ / ⏭,
# and a missing glyph in the demo would read as a broken button.
TRANSPORT = [
    ("stop", "Restart", "Back to the first frame"),
    ("back", "-1", "Previous frame"),
    ("play", "Play", "Play / pause"),
    ("forward", "+1", "Next frame"),
    ("end", "End", "Jump straight to the end state (instant mode)"),
]
SCRUB_STEPS = 1000     # slider resolution; the scene's own frame count drives stepping

VIEW_BUTTONS = [
    ("iso", "Iso"), ("front", "Front"), ("right", "Right"), ("back", "Back"),
    ("left", "Left"), ("top", "Top"), ("bottom", "Bottom"),
]

PROJECTIONS = [("perspective", "Perspective"), ("orthographic", "Orthographic")]

BACKGROUNDS = [
    {"name": "Dark", "color": THEME["surface_1"]},
    {"name": "Light", "color": "#ECEEF6"},
    {"name": "Transparent", "color": "transparent"},
]

CONTROLS_LEGEND = [
    ("Drag", "Rotate"),
    ("Wheel", "Zoom"),
    ("Right-drag", "Pan"),
    ("Arrows", "Move around"),
    ("Ctrl+Arrows", "Pan"),
    ("Shift+←→", "Cycle views"),
    ("Shift+↑↓", "Top / bottom"),
    ("P G R", "Projection · Grid · Reset"),
]

MODEL_FILTER = "3D models (*.glb *.gltf)"


class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW["title"])
        self.resize(WINDOW["width"], WINDOW["height"])
        self.setMinimumSize(WINDOW["min_width"], WINDOW["min_height"])

        self.viewer = Preview3DWidget()
        self.parts = PartsPanel(self.viewer, THEME["space_s"])
        self.model = ModelPanel(self.viewer, THEME, self._section, on_activate=self._on_model_shown)
        self._renderer = RENDERERS[0][0]
        self._background_index = 0
        self._content_version = None
        self._spec = None            # replayed when the renderer is swapped
        self._animation = None       # likewise — the loaded scene descriptor
        self._playing = False
        self._syncing_scrub = False  # tells the slider's own signal from a report
        # True while a scene's own "content" is being shown as a SIDE EFFECT of
        # loading that scene (rather than a direct MODEL button click) — without
        # it, showing the model this way would trigger _on_model_shown()'s own
        # "a hand-picked view invalidates whatever scene was loaded" rule and
        # immediately clear the very animation being loaded.
        self._suspend_animation_clear = False

        self.viewer.camera_changed.connect(self._on_camera_changed)
        self.viewer.animation_changed.connect(self._on_animation_changed)

        root = QVBoxLayout(self)
        root.setContentsMargins(*[THEME["space_l"]] * 4)
        root.setSpacing(THEME["space_m"])
        root.addLayout(self._build_header())

        body = QHBoxLayout()
        body.setSpacing(THEME["space_m"])
        body.addWidget(self._build_stage(), stretch=1)
        body.addWidget(self._build_panel())
        root.addLayout(body)

        # The LIGHT widget reports playback only once a scene is set, so the
        # transport starts from the shared "nothing loaded" state either way.
        self._on_animation_changed(dict(NO_ANIMATION))
        self._scene_buttons.buttons()[1].click()   # open on the labelled compass

    # ---- Layout ------------------------------------------------------------

    def _build_header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        header.setSpacing(2)
        title = QLabel("3D Preview")
        title.setObjectName("Title")
        subtitle = QLabel("Embeddable viewer component — the same core runs in websites and Qt apps.")
        subtitle.setObjectName("Subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        return header

    def _build_stage(self) -> QFrame:
        # Padding insets the web view so the card's rounded corners stay clean —
        # a native web view always paints its own rectangle square.
        stage = QFrame()
        stage.setObjectName("Card")
        stage.setMinimumSize(*STAGE_MINIMUM)
        self._stage_layout = QVBoxLayout(stage)
        self._stage_layout.setContentsMargins(*[THEME["space_s"]] * 4)
        self._stage_layout.addWidget(self.viewer)
        return stage

    # The legend lives in the scrolling panel, not under the stage: wrapped onto
    # eight rows in a narrow window it would eat the height the 3D view needs,
    # and the view is the point of the window while the legend is reference.
    def _build_legend(self) -> QWidget:
        # A QHBoxLayout would report the SUM of the chips as its minimum and
        # single-handedly set a ~1250 px floor on the window (see FlowLayout).
        legend = QWidget()
        legend.setSizePolicy(flow_size_policy())
        flow = FlowLayout(legend, spacing=THEME["space_s"])
        for key, action in CONTROLS_LEGEND:
            flow.addWidget(self._legend_item(key, action))
        return legend

    def _build_panel(self) -> QFrame:
        # The panel scrolls as ONE column — controls and parts together. Without
        # it the stacked sections set a ~770 px floor on the window's height,
        # and nesting a second scroll area for the parts would give the user two
        # scrollbars for one list.
        panel = QFrame()
        panel.setObjectName("Card")
        panel.setFixedWidth(PANEL_WIDTH)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(*[THEME["space_s"]] * 4)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(*[THEME["space_s"]] * 4)
        layout.setSpacing(THEME["space_s"])

        layout.addWidget(self._section("RENDERER"))
        self._renderer_buttons = self._toggle_row(
            layout, [(key, label) for key, label, _, _ in RENDERERS],
            columns=2, on_click=self.set_renderer,
        )
        self._sync_toggle(self._renderer_buttons, self._renderer)

        layout.addWidget(self._section("SCENE"))
        self._scene_buttons = QButtonGroup(self)
        scenes = QGridLayout()
        scenes.setSpacing(THEME["space_s"])
        for index, scene in enumerate(DEMO_SCENES):
            button = QPushButton(scene["name"])
            button.setObjectName("Compact")
            button.setCheckable(True)
            button.clicked.connect(lambda _, s=scene["spec"]: self._show_scene(s))
            self._scene_buttons.addButton(button, index)
            scenes.addWidget(button, index // 2, index % 2)
        layout.addLayout(scenes)

        self._load_button = QPushButton("Load GLB file…")
        self._load_button.clicked.connect(self._load_model)
        layout.addWidget(self._load_button)

        layout.addWidget(self.model)

        layout.addWidget(self._section("ANIMATION"))
        self._build_animation(layout)

        layout.addWidget(self._section("VIEW"))
        self._view_buttons = self._toggle_row(
            layout, VIEW_BUTTONS, columns=4, on_click=self.viewer.set_view
        )
        layout.addWidget(self._section("PROJECTION"))
        self._projection_buttons = self._toggle_row(
            layout, PROJECTIONS, columns=2, on_click=self.viewer.set_projection
        )

        layout.addWidget(self._section("DISPLAY"))
        display = QHBoxLayout()
        display.setSpacing(THEME["space_s"])
        self._grid_button = QPushButton("Grid")
        self._grid_button.setObjectName("Compact")
        self._grid_button.setCheckable(True)
        self._grid_button.toggled.connect(self._toggle_grid)
        display.addWidget(self._grid_button)
        self._background_button = QPushButton()
        self._background_button.setObjectName("Compact")
        self._background_button.clicked.connect(self._cycle_background)
        display.addWidget(self._background_button)
        layout.addLayout(display)
        self._apply_background()

        layout.addWidget(self._section("CAMERA"))
        self._readout = QLabel()
        self._readout.setObjectName("Readout")
        layout.addWidget(self._readout)

        layout.addWidget(self._section("PARTS"))
        hint = QLabel("Toggle visibility, drag for opacity, solo cycles a group's children.")
        hint.setObjectName("ReadoutMuted")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addWidget(self.parts)

        layout.addWidget(self._section("CONTROLS"))
        layout.addWidget(self._build_legend())
        layout.addStretch()
        return panel

    # Scene picker, transport, scrub and speed. Every control here is one call
    # into `self.viewer` — and both renderers answer the same five methods, so
    # nothing in this section knows or cares which one is mounted.
    def _build_animation(self, layout) -> None:
        self._animation_buttons = QButtonGroup(self)
        scenes = QGridLayout()
        scenes.setSpacing(THEME["space_s"])
        for index, scene in enumerate(ANIMATIONS):
            button = QPushButton(scene.get("label", scene["name"]))
            button.setObjectName("Compact")
            button.setCheckable(True)
            button.setProperty("key", scene["name"])
            button.clicked.connect(lambda _, s=scene: self._play_animation(s))
            self._animation_buttons.addButton(button, index)
            scenes.addWidget(button, index // 2, index % 2)
        layout.addLayout(scenes)

        handlers = {
            "stop": lambda: self.viewer.stop_animation(),
            "back": lambda: self.viewer.step_frame(-1),
            "play": lambda: self.viewer.toggle_animation(),
            "forward": lambda: self.viewer.step_frame(1),
            "end": lambda: self.viewer.jump_to_end(),
        }
        transport = QHBoxLayout()
        transport.setSpacing(THEME["space_s"])
        self._transport = {}
        for key, label, tip in TRANSPORT:
            button = QPushButton(label)
            button.setObjectName("Compact")
            button.setToolTip(tip)
            button.clicked.connect(lambda _, k=key: self._with_focus(handlers[k]))
            transport.addWidget(button)
            self._transport[key] = button
        layout.addLayout(transport)

        self._scrub = QSlider(Qt.Orientation.Horizontal)
        self._scrub.setRange(0, SCRUB_STEPS)
        self._scrub.setToolTip("Scrub through the scene")
        self._scrub.valueChanged.connect(self._on_scrub)
        layout.addWidget(self._scrub)

        self._speed_buttons = self._toggle_row(
            layout, [(str(speed), f"{speed:g}x") for speed in SPEEDS],
            columns=len(SPEEDS), on_click=lambda key: self.viewer.set_speed(float(key)),
        )

        self._animation_readout = QLabel()
        self._animation_readout.setObjectName("Readout")
        layout.addWidget(self._animation_readout)

        # The Five Stations "generalize control" (PLAN.md): the shipped scene
        # is ONE baked instance of build_five_stations_scene(); this regenerates
        # the identical choreography for any of the model's 13 axes on demand,
        # rather than shipping 13 near-identical descriptors (root Rule 19).
        generalize = QHBoxLayout()
        generalize.setSpacing(THEME["space_s"])
        self._axis_picker = QComboBox()
        for axis in DEMO_MODEL["axes"]:
            self._axis_picker.addItem(axis["name"], axis["id"])
        generalize_button = QPushButton("Generalize")
        generalize_button.setObjectName("Compact")
        generalize_button.setToolTip("Play the Five Stations on the chosen axis instead")
        generalize_button.clicked.connect(self._play_generalized_five_stations)
        generalize.addWidget(self._axis_picker, stretch=1)
        generalize.addWidget(generalize_button)
        layout.addLayout(generalize)

    def _play_generalized_five_stations(self) -> None:
        axis_id = self._axis_picker.currentData()
        self._play_animation(build_five_stations_scene(DEMO_MODEL, axis_id))
        self.viewer.setFocus()

    def _toggle_row(self, layout, entries, columns, on_click) -> QButtonGroup:
        group = QButtonGroup(self)
        grid = QGridLayout()
        grid.setSpacing(THEME["space_s"])
        for index, (key, label) in enumerate(entries):
            button = QPushButton(label)
            button.setObjectName("Compact")
            button.setCheckable(True)
            button.setProperty("key", key)
            button.clicked.connect(lambda _, k=key: self._with_focus(on_click, k))
            group.addButton(button, index)
            grid.addWidget(button, index // columns, index % columns)
        layout.addLayout(grid)
        return group

    def _section(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

    def _legend_item(self, key: str, action: str) -> QWidget:
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        key_label = QLabel(key)
        key_label.setObjectName("LegendKey")
        action_label = QLabel(action)
        action_label.setObjectName("LegendValue")
        layout.addWidget(key_label)
        layout.addWidget(action_label)
        return item

    # ---- Actions -----------------------------------------------------------

    # Every button hands focus back to the viewer, so the keyboard bindings
    # keep working after a click without the user re-clicking the stage.
    def _with_focus(self, action, *args) -> None:
        action(*args)
        self.viewer.setFocus()

    # Swaps the widget in the stage and replays the current state onto it, so
    # the two renderers can be compared on the very same scene.
    def set_renderer(self, key: str) -> None:
        if key == self._renderer:
            return
        factory = next(f for k, _, f, _ in RENDERERS if k == key)
        supports_files = next(s for k, _, _, s in RENDERERS if k == key)

        was_playing = self._playing      # reported state is about to be reset

        old = self.viewer
        old.camera_changed.disconnect(self._on_camera_changed)
        old.animation_changed.disconnect(self._on_animation_changed)
        self._stage_layout.removeWidget(old)
        old.deleteLater()

        self._renderer = key
        self._sync_toggle(self._renderer_buttons, key)
        self.viewer = factory()
        self.viewer.camera_changed.connect(self._on_camera_changed)
        self.viewer.animation_changed.connect(self._on_animation_changed)
        self._stage_layout.addWidget(self.viewer)
        self.parts.set_viewer(self.viewer)

        self._load_button.setEnabled(supports_files)

        self._load_button.setToolTip(
            "" if supports_files else "The Light renderer draws parametric scenes only"
        )
        self._content_version = None
        self._apply_background()
        # The model re-shows itself on the new widget if it was the content;
        # otherwise it just unticks, and the primitive spec is replayed instead.
        # Suspended the same way _play_animation() is: replaying the model here
        # must not fire _on_model_shown()'s own "clear the loaded scene" rule.
        self._suspend_animation_clear = True
        try:
            self.model.set_viewer(self.viewer)
        finally:
            self._suspend_animation_clear = False
        if self._spec is not None:
            self.viewer.show_scene(self._spec)
        # Carry the scene across the swap — comparing the two renderers on the
        # same animation is the point of having the switch at all.
        if self._animation is not None:
            self.viewer.set_animation(self._animation)
            if was_playing:
                self.viewer.play_animation()
        else:
            self._on_animation_changed(dict(NO_ANIMATION))
        self._grid_button.setChecked(False)
        self.viewer.setFocus()

    def _show_scene(self, spec: dict) -> None:
        self._spec = spec
        # New content need not contain the parts a loaded scene drives, so
        # choosing content clears the animation rather than letting it fail on
        # a path that no longer exists.
        self._clear_animation()
        self.model.clear()
        self._with_focus(self.viewer.show_scene, spec)

    def _load_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load 3D model", "", MODEL_FILTER)
        if not path:
            return
        self._clear_checks(self._scene_buttons)
        self._clear_animation()
        self.model.clear()
        self._with_focus(self.viewer.load_model, path)

    # The model is content like any other: it owns the stage, so the primitive
    # scene the renderer switch would otherwise replay has to let go of it.
    def _on_model_shown(self) -> None:
        self._spec = None
        self._clear_checks(self._scene_buttons)
        if not self._suspend_animation_clear:
            self._clear_animation()

    # ---- Animation ---------------------------------------------------------

    def _play_animation(self, descriptor: dict) -> None:
        content = descriptor.get("content")
        if content is not None:
            # The scene ships the content it was written for — a host-level
            # convention, not a timeline channel (see SCENES.md). `type:
            # "model"` names the demo MODEL and one of its views rather than a
            # primitive spec (Blindness and Five Stations need the 27-seat
            # model; Hexagram X-ray's cast is a handful of bespoke primitives).
            self._clear_checks(self._scene_buttons)
            if content.get("type") == "model":
                self._spec = None
                self._suspend_animation_clear = True
                try:
                    self.model.show_model(content.get("view"))
                finally:
                    self._suspend_animation_clear = False
            else:
                self._spec = content
                self.viewer.show_scene(content)
                self.model.clear()
        self._animation = descriptor
        self._sync_toggle(self._animation_buttons, descriptor["name"])
        self.viewer.set_animation(descriptor)
        self._with_focus(self.viewer.play_animation)

    # Only the panel's own state: showing content clears the loaded scene inside
    # the viewer itself, and the report that follows resets the transport.
    def _clear_animation(self) -> None:
        self._animation = None
        self._clear_checks(self._animation_buttons)

    def _on_scrub(self, value: int) -> None:
        if self._syncing_scrub:
            return
        self.viewer.seek_animation(value / SCRUB_STEPS)

    def _on_animation_changed(self, state: dict) -> None:
        loaded = state["scene"] is not None
        self._playing = state["playing"]
        for button in self._transport.values():
            button.setEnabled(loaded)
        self._transport["play"].setText("Pause" if state["playing"] else "Play")
        self._scrub.setEnabled(loaded)

        # The slider is both an input and a readout; without the guard its own
        # setValue would be indistinguishable from the user dragging it.
        self._syncing_scrub = True
        self._scrub.setValue(round(state["progress"] * SCRUB_STEPS))
        self._syncing_scrub = False

        if not loaded:
            self._animation_readout.setText("No scene loaded — pick one above.")
            return
        self._sync_toggle(self._speed_buttons, f"{state['speed']:g}")
        self._animation_readout.setText(
            f"{state['label']}{' · loop' if state['loop'] else ''}\n"
            f"{state['time']:.1f} / {state['duration']:.0f} s\n"
            f"Frame  {state['frame']} / {state['frames']}"
        )

    def _toggle_grid(self, enabled: bool) -> None:
        self._with_focus(self.viewer.set_grid, enabled)

    def _cycle_background(self) -> None:
        self._background_index = (self._background_index + 1) % len(BACKGROUNDS)
        self._apply_background()

    def _apply_background(self) -> None:
        background = BACKGROUNDS[self._background_index]
        self._background_button.setText(f"Bg: {background['name']}")
        self._with_focus(self.viewer.set_background, background["color"])

    # ---- Camera state ------------------------------------------------------

    def _on_camera_changed(self, state: dict) -> None:
        grid = f"{state['gridStep']:g} per cell" if state["grid"] else "off"
        self._readout.setText(
            f"Azimuth  {state['azimuth']:+.1f}°\n"
            f"Elevation  {state['elevation']:+.1f}°\n"
            f"Distance  {state['distance']:.2f}\n"
            f"View  {state['view']} · {state['projection']}\n"
            f"Grid  {grid}"
        )
        self._sync_toggle(self._view_buttons, state["view"])
        self._sync_toggle(self._projection_buttons, state["projection"])
        self._grid_button.setChecked(state["grid"])

        # Content loading is async; this is the moment the part list is real.
        if state["contentVersion"] != self._content_version:
            self._content_version = state["contentVersion"]
            self.parts.reload()

    def _sync_toggle(self, group: QButtonGroup, key: str) -> None:
        group.setExclusive(False)
        for button in group.buttons():
            button.setChecked(button.property("key") == key)
        group.setExclusive(True)

    def _clear_checks(self, group: QButtonGroup) -> None:
        self._sync_toggle(group, None)
