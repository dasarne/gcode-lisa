"""Floating tool dialog for canvas-driven selection operations."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class GraphicsSelectionDialog(QDialog):
    """Show metrics and actions for a canvas (yellow-overlay) selection."""

    copy_requested = pyqtSignal()
    cut_requested = pyqtSignal()
    delete_requested = pyqtSignal()
    scale_feed_requested = pyqtSignal()
    find_replace_requested = pyqtSignal()
    dialog_closed = pyqtSignal()

    def __init__(self, parent=None, language: str = "de") -> None:
        super().__init__(parent)
        self._language = language
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(False)
        self.setMinimumWidth(360)
        self._setup_ui()
        self.set_language(language)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._summary_label = QLabel("")
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

        self._dims_label = QLabel("")
        self._dims_label.setWordWrap(True)
        layout.addWidget(self._dims_label)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self._copy_button = QPushButton("")
        self._copy_button.clicked.connect(self.copy_requested)
        actions.addWidget(self._copy_button)

        self._cut_button = QPushButton("")
        self._cut_button.clicked.connect(self.cut_requested)
        actions.addWidget(self._cut_button)

        self._delete_button = QPushButton("")
        self._delete_button.clicked.connect(self.delete_requested)
        actions.addWidget(self._delete_button)

        self._scale_feed_button = QPushButton("")
        self._scale_feed_button.clicked.connect(self.scale_feed_requested)
        actions.addWidget(self._scale_feed_button)

        self._find_replace_button = QPushButton("")
        self._find_replace_button.clicked.connect(self.find_replace_requested)
        actions.addWidget(self._find_replace_button)

        actions.addStretch(1)
        layout.addLayout(actions)

        done_layout = QHBoxLayout()
        done_layout.addStretch(1)
        self._done_button = QPushButton("")
        self._done_button.clicked.connect(self.close)
        done_layout.addWidget(self._done_button)
        layout.addLayout(done_layout)

    def set_language(self, language: str) -> None:
        self._language = language
        de = language != "en"
        self.setWindowTitle("Grafik-Auswahl" if de else "Graphics Selection")
        self._copy_button.setText("Kopieren" if de else "Copy")
        self._cut_button.setText("Ausschneiden" if de else "Cut")
        self._delete_button.setText("Loeschen" if de else "Delete")
        self._scale_feed_button.setText("Vorschub x..." if de else "Scale Feed x...")
        self._find_replace_button.setText("Suchen/Ersetzen" if de else "Find/Replace")
        self._done_button.setText("Fertig" if de else "Done")

    def update_selection(self, stats: dict[str, float | int]) -> None:
        de = self._language != "en"
        line_count = int(stats.get("line_count", 0))
        segment_count = int(stats.get("segment_count", 0))
        x_span = float(stats.get("x_span", 0.0))
        y_span = float(stats.get("y_span", 0.0))
        z_span = float(stats.get("z_span", 0.0))

        if de:
            self._summary_label.setText(
                f"Auswahl: {line_count} Zeilen, {segment_count} Segmente"
            )
            self._dims_label.setText(
                f"Ausmasse: X={x_span:.3f}, Y={y_span:.3f}, Z={z_span:.3f}"
            )
        else:
            self._summary_label.setText(
                f"Selection: {line_count} lines, {segment_count} segments"
            )
            self._dims_label.setText(
                f"Extents: X={x_span:.3f}, Y={y_span:.3f}, Z={z_span:.3f}"
            )

    def closeEvent(self, event) -> None:
        self.dialog_closed.emit()
        super().closeEvent(event)
