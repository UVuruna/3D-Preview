"""Demo window — the viewer stage plus every control the component exposes.

Doubles as the integration example: each control is one call into
Preview3DWidget, and the camera readout is one signal connection.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from preview3d import Preview3DWidget

from .parts_panel import PartsPanel
from .theme import THEME

WINDOW = {"title": "3D Preview — Demo", "width": 1360, "height": 880}
PANEL_WIDTH = 340

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

        self.viewer = Preview3DWidget()
        self.parts = PartsPanel(self.viewer, THEME["space_s"])
        self._background_index = 0
        self._content_version = None

        self.viewer.camera_changed.connect(self._on_camera_changed)

        root = QVBoxLayout(self)
        root.setContentsMargins(*[THEME["space_l"]] * 4)
        root.setSpacing(THEME["space_m"])
        root.addLayout(self._build_header())

        body = QHBoxLayout()
        body.setSpacing(THEME["space_m"])
        body.addLayout(self._build_stage_column(), stretch=1)
        body.addWidget(self._build_panel())
        root.addLayout(body)

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

    def _build_stage_column(self) -> QVBoxLayout:
        column = QVBoxLayout()
        column.setSpacing(THEME["space_s"])

        # Padding insets the web view so the card's rounded corners stay clean —
        # a native web view always paints its own rectangle square.
        stage = QFrame()
        stage.setObjectName("Card")
        stage_layout = QVBoxLayout(stage)
        stage_layout.setContentsMargins(*[THEME["space_s"]] * 4)
        stage_layout.addWidget(self.viewer)
        column.addWidget(stage, stretch=1)

        legend = QHBoxLayout()
        legend.setSpacing(THEME["space_m"])
        for key, action in CONTROLS_LEGEND:
            legend.addLayout(self._legend_item(key, action))
        legend.addStretch()
        column.addLayout(legend)
        return column

    def _build_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Card")
        panel.setFixedWidth(PANEL_WIDTH)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(*[THEME["space_m"]] * 4)
        layout.setSpacing(THEME["space_s"])

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

        load = QPushButton("Load GLB file…")
        load.clicked.connect(self._load_model)
        layout.addWidget(load)

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
        layout.addWidget(self.parts, stretch=1)
        return panel

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

    def _legend_item(self, key: str, action: str) -> QHBoxLayout:
        item = QHBoxLayout()
        item.setSpacing(6)
        key_label = QLabel(key)
        key_label.setObjectName("LegendKey")
        action_label = QLabel(action)
        action_label.setObjectName("LegendValue")
        item.addWidget(key_label)
        item.addWidget(action_label)
        return item

    # ---- Actions -----------------------------------------------------------

    # Every button hands focus back to the viewer, so the keyboard bindings
    # keep working after a click without the user re-clicking the stage.
    def _with_focus(self, action, *args) -> None:
        action(*args)
        self.viewer.setFocus()

    def _show_scene(self, spec: dict) -> None:
        self._with_focus(self.viewer.show_scene, spec)

    def _load_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load 3D model", "", MODEL_FILTER)
        if not path:
            return
        self._scene_buttons.setExclusive(False)
        for button in self._scene_buttons.buttons():
            button.setChecked(False)
        self._scene_buttons.setExclusive(True)
        self._with_focus(self.viewer.load_model, path)

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
