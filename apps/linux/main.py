"""StreakGrid Linux entry point (S07: MainWindow shell)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import apply_dark


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("StreakGrid")
    apply_dark(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
