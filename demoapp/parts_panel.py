"""Parts panel — one row per element of whatever is being shown.

Each row carries the two controls a host actually needs: a visibility switch
and an opacity slider. A group row additionally offers SOLO, which shows one
child at a time and cycles — the "three legend terms on one arm tip, one shown
at a time" case from MODELS.md.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

INDENT_PX = 12
OPACITY_STEPS = 100
SOLO_ALL = -1        # solo index meaning "every child visible"


class PartsPanel(QWidget):
    """Scrollable list of parts, driving a Preview3DWidget."""

    def __init__(self, viewer, spacing: int, parent=None):
        super().__init__(parent)
        self._viewer = viewer
        self._spacing = spacing
        self._solo: dict[str, int] = {}
        self._children: dict[str, list[str]] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._body = QWidget()
        self._rows = QVBoxLayout(self._body)
        self._rows.setContentsMargins(0, 0, 0, 0)
        self._rows.setSpacing(2)
        self._rows.addStretch()
        self._scroll.setWidget(self._body)
        outer.addWidget(self._scroll)

    def reload(self) -> None:
        """Rebuild for NEW content — solo state belongs to the old scene."""
        self._solo.clear()
        self.refresh()

    def refresh(self) -> None:
        """Re-read the current parts and rebuild the rows, keeping solo state."""
        self._viewer.list_parts(self._rebuild)

    # ---- Building ----------------------------------------------------------

    def _rebuild(self, parts: list[dict]) -> None:
        while self._rows.count() > 1:
            item = self._rows.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._children = _group_children(parts)
        for part in parts:
            self._rows.insertWidget(self._rows.count() - 1, self._build_row(part))

    def _build_row(self, part: dict) -> QWidget:
        path = part["path"]
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(part["depth"] * INDENT_PX, 0, 0, 0)
        layout.setSpacing(self._spacing)

        visible = QCheckBox()
        visible.setChecked(part["visible"])
        visible.setToolTip(f"Show / hide {path}")
        visible.toggled.connect(lambda on, p=path: self._viewer.set_part_visible(p, on))
        layout.addWidget(visible)

        name = QLabel(part["name"])
        name.setObjectName("PartName" if part["drawable"] else "PartNameGroup")
        name.setToolTip(path)
        layout.addWidget(name, stretch=1)

        if part["drawable"]:
            opacity = QSlider(Qt.Orientation.Horizontal)
            opacity.setRange(0, OPACITY_STEPS)
            opacity.setValue(round(part["opacity"] * OPACITY_STEPS))
            opacity.setFixedWidth(72)
            opacity.setToolTip(f"Opacity of {path}")
            opacity.valueChanged.connect(
                lambda value, p=path: self._viewer.set_part_opacity(p, value / OPACITY_STEPS)
            )
            layout.addWidget(opacity)
        elif len(self._children.get(path, ())) > 1:
            solo = QPushButton(self._solo_label(path))
            solo.setObjectName("Compact")
            solo.setFixedWidth(72)
            solo.setToolTip("Show one child at a time; cycles, then back to all")
            solo.clicked.connect(lambda _, p=path: self._cycle_solo(p))
            layout.addWidget(solo)

        return row

    def _solo_label(self, group_path: str) -> str:
        index = self._solo.get(group_path, SOLO_ALL)
        if index == SOLO_ALL:
            return "solo"
        return f"{index + 1}/{len(self._children[group_path])}"

    # ---- Solo cycling ------------------------------------------------------

    def _cycle_solo(self, group_path: str) -> None:
        children = self._children[group_path]
        index = self._solo.get(group_path, SOLO_ALL) + 1
        if index >= len(children):
            index = SOLO_ALL
        self._solo[group_path] = index

        if index == SOLO_ALL:
            for child in children:
                self._viewer.set_part_visible(f"{group_path}/{child}", True)
        else:
            self._viewer.show_only(group_path, children[index])
        # The child checkboxes would otherwise still show the old state.
        self.refresh()


def _group_children(parts: list[dict]) -> dict[str, list[str]]:
    """Map every group path to its direct children's names."""
    children: dict[str, list[str]] = {}
    for part in parts:
        parent, _, name = part["path"].rpartition("/")
        if parent:
            children.setdefault(parent, []).append(name)
    return children
