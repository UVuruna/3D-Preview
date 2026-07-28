"""FlowLayout — a layout that wraps its items onto as many rows as it needs.

Qt ships no wrapping layout. A `QHBoxLayout` of N items reports the SUM of
their widths as its minimum, so a single row of legend chips can dictate a
1600 px minimum window width — which is the bug this exists to kill. This
layout's minimum is the widest SINGLE item, so the window can shrink until the
strip is one item per row.
"""

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QSizePolicy


class FlowLayout(QLayout):
    def __init__(self, parent=None, spacing: int = 8):
        super().__init__(parent)
        self._items = []
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(spacing)

    # ---- QLayout plumbing --------------------------------------------------

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    # ---- Wrapping ----------------------------------------------------------

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._arrange(QRect(0, 0, width, 0), apply=False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrange(rect, apply=True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(),
                            margins.top() + margins.bottom())

    def _arrange(self, rect, apply: bool) -> int:
        """Place items left to right, wrapping at the right edge. Returns height."""
        margins = self.contentsMargins()
        area = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x, y, row_height = area.x(), area.y(), 0

        for item in self._items:
            hint = item.sizeHint()
            if x + hint.width() > area.right() and row_height > 0:
                x = area.x()
                y += row_height + self.spacing()
                row_height = 0
            if apply:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + self.spacing()
            row_height = max(row_height, hint.height())

        return y + row_height - rect.y() + margins.bottom()


def flow_size_policy() -> QSizePolicy:
    """Size policy a widget needs for its FlowLayout's height-for-width to be honoured."""
    policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    policy.setHeightForWidth(True)
    return policy
