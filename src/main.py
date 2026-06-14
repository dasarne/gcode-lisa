"""Main entry point for the GCode Lisa application."""

import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from src.runtime_paths import asset_path
from src.ui.main_window import MainWindow


def main() -> None:
    """Create and launch the GCode Lisa application."""
    app = QApplication(sys.argv)
    app.setApplicationName("GCode Lisa")
    app.setApplicationVersion("1.0.0")
    startup_path = sys.argv[1] if len(sys.argv) > 1 else None

    logo_path = asset_path("Lisa.svg")
    if logo_path.exists():
        icon = QIcon(str(logo_path))
        app.setWindowIcon(icon)

    window = MainWindow()
    if logo_path.exists():
        window.setWindowIcon(QIcon(str(logo_path)))
    if startup_path:
        window._open_file_path(startup_path)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
