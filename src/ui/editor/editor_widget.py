"""Lightweight editor widget setup and ownership helpers."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtGui import QColor, QPalette, QTextDocument
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from ..widgets import GCodeEditor


def create_editor_layout(parent: QWidget) -> QVBoxLayout:
    """Create the editor panel layout with consistent margins."""
    layout = QVBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)
    return layout


def create_editor_widget() -> GCodeEditor:
    """Create and configure the editor widget instance."""
    text_edit = GCodeEditor()
    text_edit.setReadOnly(False)
    text_edit.setLineWrapMode(GCodeEditor.LineWrapMode.NoWrap)
    configure_editor_palette(text_edit)
    return text_edit


def configure_editor_palette(text_edit: GCodeEditor) -> None:
    """Neutralize native QTextCursor selection rendering.

    Semantic selections are rendered through ExtraSelections overlays.
    QTextCursor remains an interaction/navigation primitive only.
    """
    palette = text_edit.palette()

    transparent_selection = QColor(0, 0, 0, 0)

    palette.setColor(
        QPalette.ColorGroup.Active,
        QPalette.ColorRole.Highlight,
        transparent_selection,
    )
    palette.setColor(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.Highlight,
        transparent_selection,
    )
    palette.setColor(
        QPalette.ColorGroup.Active,
        QPalette.ColorRole.HighlightedText,
        QColor("#111111"),
    )
    palette.setColor(
        QPalette.ColorGroup.Inactive,
        QPalette.ColorRole.HighlightedText,
        QColor("#111111"),
    )

    text_edit.setPalette(palette)


def configure_editor_document(text_edit: GCodeEditor) -> QTextDocument:
    """Return the editor document after lightweight configuration."""
    document = text_edit.document()
    assert document is not None
    document.setUndoRedoEnabled(True)
    return document


def enable_editor_mouse_tracking(text_edit: GCodeEditor) -> None:
    """Enable viewport mouse tracking for tooltip handling."""
    viewport = text_edit.viewport()
    assert viewport is not None
    viewport.setMouseTracking(True)


def install_editor_event_filters(
    text_edit: GCodeEditor,
    event_filter_owner: QWidget,
) -> None:
    """Install editor and viewport event filters."""
    text_edit.installEventFilter(event_filter_owner)

    viewport = text_edit.viewport()
    assert viewport is not None
    viewport.installEventFilter(event_filter_owner)


def connect_editor_signals(
    text_edit: GCodeEditor,
    cursor_position_changed: Callable[[], None],
    text_changed: Callable[[], None],
) -> None:
    """Connect core editor lifecycle signals."""
    text_edit.cursorPositionChanged.connect(cursor_position_changed)
    text_edit.textChanged.connect(text_changed)


def add_editor_to_layout(
    layout: QVBoxLayout,
    text_edit: GCodeEditor,
) -> None:
    """Attach the editor widget to the layout."""
    layout.addWidget(text_edit)


def get_editor_document(text_edit: GCodeEditor) -> QTextDocument:
    """Return the active editor document with a non-optional type."""
    document = text_edit.document()
    assert document is not None
    return document