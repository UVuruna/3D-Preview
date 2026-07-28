"""3D Preview — demo application entry point.

Run with `python main.py`. Everything it shows is documented in main.md;
the window itself lives in demoapp/.
"""

import logging
import sys

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from demoapp.theme import FONT_FILE, THEME, build_qss
from demoapp.window import DemoWindow

logger = logging.getLogger(__name__)


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
