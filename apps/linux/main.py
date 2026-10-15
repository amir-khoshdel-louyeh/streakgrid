"""StreakGrid Linux entry point (S01: bare window)."""

import sys

from PySide6.QtWidgets import QApplication, QMainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("StreakGrid")
    window = QMainWindow()
    window.setWindowTitle("StreakGrid")
    window.resize(900, 600)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
