"""Model panel — the four owner models, the Switcher, and the orientation table.

Its own widget rather than another block inside the demo window, because it is
its own responsibility: everything here drives a MODEL (MODELS.md), and none of
it means anything for a plain primitive scene. The window owns the stage and the
renderer switch; this owns the model controls.

Like the parts panel, it holds no state of its own beyond what it has shown: the
viewer is the authority, and `set_viewer` re-points it at the other renderer
without any of the controls knowing which one they are driving.
"""

from PySide6.QtWidgets import QButtonGroup, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from preview3d import READINGS, REGISTERS, build_cube_model, orientation_ids

# The demo model: the neutral thirteen-axis cube the gadget ships. A consumer
# passes its own vocabulary to the same builder (root Rule 19 — the geometry is
# computed, only the words are anyone's content).
DEMO_MODEL = build_cube_model()

ORIENTATION_STEPS = [("−", -1), ("+", 1)]
UPRIGHT = orientation_ids()[0]


class ModelPanel(QWidget):
    """The four owner models plus the Switcher, driving either renderer."""

    def __init__(self, viewer, theme: dict, section, on_activate=None, parent=None):
        super().__init__(parent)
        self._viewer = viewer
        self._theme = theme
        self._on_activate = on_activate
        self._orientation = None
        self._view = None          # the model's active view, or None when unloaded

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(theme["space_s"])

        layout.addWidget(section("MODEL"))
        hint = QLabel("The four owner models are four VIEWS over one model — the same 13 axes each time.")
        hint.setObjectName("ReadoutMuted")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self._view_buttons = self._row(
            layout,
            [(view["name"], view["label"]) for view in DEMO_MODEL["views"]],
            columns=2,
            on_click=self._show_view,
        )

        layout.addWidget(section("REGISTER"))
        self._register_buttons = self._row(
            layout, [(name, name.title()) for name in REGISTERS], columns=2,
            on_click=lambda key: self._switch(register=key),
        )

        layout.addWidget(section("READING"))
        self._reading_buttons = self._row(
            layout, [(name, name.title()) for name in READINGS], columns=3,
            on_click=lambda key: self._switch(reading=key),
        )

        layout.addWidget(section("ORIENTATION"))
        row = QHBoxLayout()
        row.setSpacing(theme["space_s"])
        self._orientation_label = QLabel()
        self._orientation_label.setObjectName("Readout")
        row.addWidget(self._orientation_label, stretch=1)
        for label, step in ORIENTATION_STEPS:
            button = QPushButton(label)
            button.setObjectName("Compact")
            button.setFixedWidth(36)
            button.setToolTip("Step through the cube's 24 orientations")
            button.clicked.connect(lambda _, s=step: self._step_orientation(s))
            row.addWidget(button)
        upright = QPushButton("Upright")
        upright.setObjectName("Compact")
        upright.clicked.connect(lambda: self._set_orientation(None))
        row.addWidget(upright)
        layout.addLayout(row)

        self._set_orientation(None)

    # ---- Wiring ------------------------------------------------------------

    def set_viewer(self, viewer) -> None:
        """Point at another renderer's widget — both expose the same methods.

        A renderer swap starts from empty content, so a model that was on screen
        is shown again on the new widget rather than left as ticked buttons over
        somebody else's scene.
        """
        self._viewer = viewer
        view, self._view = self._view, None
        if view:
            self.show_model(view)
        else:
            self.clear()

    def show_model(self, view: str | None = None) -> None:
        """Load the demo model and open it on `view` (its first, by default)."""
        name = view or DEMO_MODEL["views"][0]["name"]
        self._viewer.show_model(DEMO_MODEL, name)
        self._view = name
        self._orientation = None
        self._orientation_label.setText(f"Upright ({UPRIGHT})")
        self._check(self._view_buttons, name)
        self._check(self._register_buttons, REGISTERS[0])
        self._check(self._reading_buttons, READINGS[0])
        if self._on_activate:
            self._on_activate()

    def clear(self) -> None:
        """Nothing model-shaped is on screen any more — untick everything."""
        self._view = None
        self._orientation = None
        self._orientation_label.setText(f"Upright ({UPRIGHT})")
        for group in (self._view_buttons, self._register_buttons, self._reading_buttons):
            self._check(group, None)

    # ---- Actions -----------------------------------------------------------

    def _show_view(self, name: str) -> None:
        # A view is a cheap re-dress of content already built, so it is only the
        # FIRST press that has to build the model.
        if self._view is None:
            self.show_model(name)
            return
        self._viewer.set_model_view(name)
        self._view = name

    def _switch(self, register: str | None = None, reading: str | None = None) -> None:
        self._viewer.set_switcher(register=register, reading=reading)

    def _step_orientation(self, step: int) -> None:
        table = orientation_ids()
        index = table.index(self._orientation) + step if self._orientation in table else (
            0 if step > 0 else -1
        )
        self._set_orientation(table[index % len(table)])

    def _set_orientation(self, identifier: str | None) -> None:
        self._orientation = identifier
        self._viewer.set_orientation(identifier)
        self._orientation_label.setText(identifier or f"Upright ({UPRIGHT})")

    # ---- Small helpers -----------------------------------------------------

    def _row(self, layout, entries, columns: int, on_click) -> QButtonGroup:
        group = QButtonGroup(self)
        grid = QGridLayout()
        grid.setSpacing(self._theme["space_s"])
        for index, (key, label) in enumerate(entries):
            button = QPushButton(label)
            button.setObjectName("Compact")
            button.setCheckable(True)
            button.setProperty("key", key)
            button.clicked.connect(lambda _, k=key: self._pick(on_click, k))
            group.addButton(button, index)
            grid.addWidget(button, index // columns, index % columns)
        layout.addLayout(grid)
        return group

    def _pick(self, action, key: str) -> None:
        action(key)
        self._viewer.setFocus()

    def _check(self, group: QButtonGroup, key) -> None:
        group.setExclusive(False)
        for button in group.buttons():
            button.setChecked(button.property("key") == key)
        group.setExclusive(True)
