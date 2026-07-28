"""3D Preview — demo application.

Minimal PySide6 GUI that shows the embeddable viewer in action: the built-in
demo scenes, loading a glTF/GLB file, background modes, and the orbit controls
(rotate / zoom / pan). Run it with `python main.py`.
"""

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from preview3d import Preview3DWidget

logger = logging.getLogger(__name__)

# ---- Config (root Rule #4) --------------------------------------------------

WINDOW = {"title": "3D Preview — Demo", "width": 1180, "height": 760}

FONT_FILE = Path(__file__).parent / "assets" / "fonts" / "Inter.ttf"

# DESIGN.md tokens — dark surfaces, one indigo accent.
THEME = {
    "surface_0": "#121218",
    "surface_1": "#1E1E26",
    "surface_2": "#24242E",
    "surface_hover": "#2C2C38",
    "border": "rgba(255, 255, 255, 0.10)",
    "text_primary": "#F5F5F5",
    "text_secondary": "#A8A8B3",
    "accent": "#818CF8",
    "accent_strong": "#6366F1",
    "radius_control": "8px",
    "radius_card": "14px",
    "space_s": 8,
    "space_m": 16,
    "space_l": 24,
}

# The demo scenes: parametric specs, not model files (root Rule #19).
DEMO_SCENES = [
    {
        "name": "Axes gizmo",
        "spec": {"type": "axes"},
    },
    {
        "name": "Compass axes",
        "spec": {
            "type": "axes",
            "arms": [
                {"axis": "+x", "color": "#EF4444", "label": "East"},
                {"axis": "-x", "color": "#F97316", "label": "West"},
                {"axis": "+y", "color": "#22C55E", "label": "Zenith"},
                {"axis": "-y", "color": "#EAB308", "label": "Nadir"},
                {"axis": "+z", "color": "#3B82F6", "label": "North"},
                {"axis": "-z", "color": "#A855F7", "label": "South"},
            ],
        },
    },
    {
        "name": "Cube",
        "spec": {
            "type": "cube",
            "colors": ["#EF4444", "#F97316", "#22C55E", "#EAB308", "#3B82F6", "#A855F7"],
        },
    },
]

BACKGROUNDS = [
    {"name": "Dark", "color": THEME["surface_1"]},
    {"name": "Light", "color": "#ECEEF6"},
    {"name": "Transparent", "color": "transparent"},
]

CONTROLS_LEGEND = [
    ("Left-drag", "Rotate"),
    ("Wheel", "Zoom"),
    ("Right-drag", "Pan"),
]

MODEL_FILTER = "3D models (*.glb *.gltf)"


def build_qss(theme: dict) -> str:
    return f"""
    QWidget {{
        background: {theme["surface_0"]};
        color: {theme["text_primary"]};
        font-family: Inter;
        font-size: 14px;
    }}
    /* A QLabel inherits the QWidget rule above and would paint the window
       surface over whatever card it sits on — every label is transparent
       unless it explicitly styles itself (the legend key pill below). */
    QLabel {{ background: transparent; }}
    QLabel#Title {{ font-size: 22px; font-weight: 700; }}
    QLabel#Subtitle {{ color: {theme["text_secondary"]}; font-size: 13px; }}
    QLabel#SectionLabel {{
        color: {theme["text_secondary"]};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        padding-top: {theme["space_s"]}px;
    }}
    QLabel#LegendKey {{
        background: {theme["surface_2"]};
        border: 1px solid {theme["border"]};
        border-radius: 6px;
        color: {theme["text_primary"]};
        font-size: 12px;
        font-weight: 500;
        padding: 3px 8px;
    }}
    QLabel#LegendValue {{ color: {theme["text_secondary"]}; font-size: 13px; }}
    QFrame#Card {{
        background: {theme["surface_1"]};
        border: 1px solid {theme["border"]};
        border-radius: {theme["radius_card"]};
    }}
    QFrame#Divider {{ background: {theme["border"]}; border: none; max-height: 1px; }}
    QPushButton {{
        background: {theme["surface_2"]};
        border: 1px solid {theme["border"]};
        border-radius: {theme["radius_control"]};
        font-size: 14px;
        font-weight: 500;
        padding: 10px 14px;
        text-align: center;
    }}
    QPushButton:hover {{ background: {theme["surface_hover"]}; }}
    QPushButton:checked {{
        background: {theme["accent_strong"]};
        border-color: transparent;
    }}
    QPushButton:checked:hover {{ background: {theme["accent"]}; }}
    """


class DemoWindow(QWidget):
    """Viewer stage plus a control panel driving every Preview3DWidget method."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW["title"])
        self.resize(WINDOW["width"], WINDOW["height"])

        self.viewer = Preview3DWidget()
        self._background_index = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(*[THEME["space_l"]] * 4)
        root.setSpacing(THEME["space_m"])
        root.addLayout(self._build_header())

        body = QHBoxLayout()
        body.setSpacing(THEME["space_m"])
        body.addWidget(self._build_stage(), stretch=1)
        body.addWidget(self._build_panel())
        root.addLayout(body)

        self._scene_buttons.buttons()[0].click()

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
        layout = QVBoxLayout(stage)
        layout.setContentsMargins(*[THEME["space_s"]] * 4)
        layout.addWidget(self.viewer)
        return stage

    def _build_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Card")
        panel.setFixedWidth(280)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(*[THEME["space_m"]] * 4)
        layout.setSpacing(THEME["space_s"])

        layout.addWidget(self._section_label("SCENE"))
        self._scene_buttons = QButtonGroup(self)
        for index, scene in enumerate(DEMO_SCENES):
            button = QPushButton(scene["name"])
            button.setCheckable(True)
            button.clicked.connect(lambda _, s=scene["spec"]: self.viewer.show_scene(s))
            self._scene_buttons.addButton(button, index)
            layout.addWidget(button)

        load_button = QPushButton("Load GLB file…")
        load_button.clicked.connect(self._load_model)
        layout.addWidget(load_button)

        layout.addWidget(self._divider())
        layout.addWidget(self._section_label("VIEW"))
        reset_button = QPushButton("Reset view")
        reset_button.clicked.connect(self.viewer.reset_view)
        layout.addWidget(reset_button)
        self._background_button = QPushButton()
        self._background_button.clicked.connect(self._cycle_background)
        layout.addWidget(self._background_button)
        self._apply_background()

        layout.addWidget(self._divider())
        layout.addWidget(self._section_label("CONTROLS"))
        for key, action in CONTROLS_LEGEND:
            layout.addLayout(self._legend_row(key, action))

        layout.addStretch()
        return panel

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

    def _divider(self) -> QFrame:
        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        return divider

    def _legend_row(self, key: str, action: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(THEME["space_s"])
        key_label = QLabel(key)
        key_label.setObjectName("LegendKey")
        action_label = QLabel(action)
        action_label.setObjectName("LegendValue")
        row.addWidget(key_label, alignment=Qt.AlignmentFlag.AlignLeft)
        row.addWidget(action_label, stretch=1)
        return row

    # ---- Actions -----------------------------------------------------------

    def _load_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load 3D model", "", MODEL_FILTER)
        if not path:
            return
        self._scene_buttons.setExclusive(False)
        for button in self._scene_buttons.buttons():
            button.setChecked(False)
        self._scene_buttons.setExclusive(True)
        self.viewer.load_model(path)

    def _cycle_background(self) -> None:
        self._background_index = (self._background_index + 1) % len(BACKGROUNDS)
        self._apply_background()

    def _apply_background(self) -> None:
        background = BACKGROUNDS[self._background_index]
        self._background_button.setText(f"Background: {background['name']}")
        self.viewer.set_background(background["color"])


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    app = QApplication(sys.argv)

    if QFontDatabase.addApplicationFont(str(FONT_FILE)) == -1:
        logger.error("Failed to load the bundled Inter font from %s", FONT_FILE)

    app.setStyleSheet(build_qss(THEME))
    window = DemoWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
