"""Selection and cursor helpers for EditorPanel."""

from __future__ import annotations

from dataclasses import dataclass, field

from PyQt6.QtGui import QColor, QTextCursor, QTextDocument, QTextFormat
from PyQt6.QtWidgets import QTextEdit

from ...analyzer.analyzer import WarningSeverity
from ..selection.selection_model import SelectionModel
from ..selection.selection_types import LineRange


_CURRENT_LINE_COLOR = "#D9E8FF"
_MULTI_LINE_SELECTION_COLOR = "#FFE3B8"


@dataclass(slots=True)
class EditorSelectionState:
    """Mutable selection state shared with EditorPanel.

    Transition notes:
    - SelectionModel is the semantic selection source shared with canvas.
    - QTextCursor state still coexists during the migration phase.
    """

    selection_model: SelectionModel = field(default_factory=SelectionModel)
    selection_anchor_line: int | None = None
    selected_line: int | None = None
    locked_selection: tuple[int, int] | None = None


def capture_locked_selection(
    state: EditorSelectionState,
    cursor: QTextCursor,
    interaction_lock: bool,
) -> None:
    """Capture the current cursor selection while interaction lock is active."""
    if not interaction_lock:
        return

    if cursor.hasSelection():
        state.locked_selection = (
            cursor.selectionStart(),
            cursor.selectionEnd(),
        )
        return

    position = cursor.position()
    state.locked_selection = (position, position)


def build_line_selection(
    block_cursor: QTextCursor,
    color: str,
) -> QTextEdit.ExtraSelection:
    """Create a full-width line selection overlay."""
    selection = QTextEdit.ExtraSelection()
    selection.cursor = QTextCursor(block_cursor)
    selection.cursor.clearSelection()
    selection.format.setBackground(QColor(color))
    selection.format.setProperty(
        QTextFormat.Property.FullWidthSelection,
        True,
    )
    return selection


def build_current_line_selection(
    cursor: QTextCursor,
) -> QTextEdit.ExtraSelection:
    """Create the current-line overlay selection."""
    return build_line_selection(cursor, _CURRENT_LINE_COLOR)


def build_multi_line_selections(
    document: QTextDocument,
    selection_model: SelectionModel,
) -> list[QTextEdit.ExtraSelection]:
    """Build overlays for semantic multi-line selections."""
    selections: list[QTextEdit.ExtraSelection] = []

    for line_number in selection_model.selected_lines():
        block = document.findBlockByLineNumber(line_number - 1)
        if not block.isValid():
            continue

        selections.append(
            build_line_selection(
                QTextCursor(block),
                _MULTI_LINE_SELECTION_COLOR,
            ),
        )

    return selections


def get_selected_lines(
    document: QTextDocument,
    cursor: QTextCursor,
) -> list[int]:
    """Return the active 1-based selected lines.

    Transition note:
    - Semantic SelectionModel ownership is preferred.
    """
    if cursor.hasSelection():
        selection_start = cursor.selectionStart()
        selection_end = cursor.selectionEnd()

        start_block = document.findBlock(selection_start).blockNumber()
        end_block = document.findBlock(
            max(selection_start, selection_end - 1),
        ).blockNumber()

        return list(range(start_block + 1, end_block + 2))

    return [cursor.blockNumber() + 1]


def create_line_range_cursor(
    document: QTextDocument,
    start_line: int,
    end_line: int,
) -> QTextCursor | None:
    """Create a cursor selecting the given inclusive line range."""
    if start_line <= 0 or end_line <= 0:
        return None

    start_line, end_line = sorted((start_line, end_line))

    start_block = document.findBlockByLineNumber(start_line - 1)
    end_block = document.findBlockByLineNumber(end_line - 1)

    if not start_block.isValid() or not end_block.isValid():
        return None

    cursor = QTextCursor(document)
    cursor.setPosition(start_block.position())
    cursor.setPosition(
        end_block.position() + len(end_block.text()),
        QTextCursor.MoveMode.KeepAnchor,
    )

    return cursor


def create_range_cursor(
    document: QTextDocument,
    start: int,
    end: int,
) -> QTextCursor:
    """Create a cursor selecting the given text range."""
    cursor = QTextCursor(document)
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
    return cursor


def restore_locked_selection_cursor(
    document: QTextDocument,
    locked_selection: tuple[int, int] | None,
) -> QTextCursor | None:
    """Create a cursor restoring the locked selection range."""
    if locked_selection is None:
        return None

    start, end = locked_selection
    max_position = document.characterCount() - 1

    start = max(0, min(start, max_position))
    end = max(0, min(end, max_position))

    cursor = QTextCursor(document)
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

    return cursor


def update_single_line_selection(
    state: EditorSelectionState,
    line_number: int,
) -> None:
    """Update state for a single active line selection."""
    state.selection_model.set_single_line(line_number)

    state.selection_anchor_line = line_number
    state.selected_line = line_number


def update_multi_line_selection(
    state: EditorSelectionState,
    line_numbers: list[int],
) -> None:
    """Update state for multiple active selected lines."""
    first_line = line_numbers[0]

    state.selected_line = first_line
    state.selection_anchor_line = first_line

    ranges = [
        LineRange(line_number, line_number)
        for line_number in sorted(set(line_numbers))
    ]

    state.selection_model.set_ranges(ranges)


def clear_line_selection(
    state: EditorSelectionState,
) -> None:
    """Clear multi-line selection tracking."""
    state.selection_model.clear()
    state.selection_anchor_line = None


def should_show_current_line_selection(
    cursor_line: int,
    selection_model: SelectionModel,
) -> bool:
    """Return whether the current-line overlay should be visible."""
    return not selection_model.contains(cursor_line)


_SEVERITY_COLORS: dict[WarningSeverity, str] = {
    WarningSeverity.ERROR: "#FFCCCC",
    WarningSeverity.WARNING: "#FFF3CC",
    WarningSeverity.INFO: "#CCE5FF",
}


def build_warning_selections(
    document: QTextDocument,
    warning_severity: dict[int, WarningSeverity],
) -> list[QTextEdit.ExtraSelection]:
    """Build full-width warning overlays."""
    selections: list[QTextEdit.ExtraSelection] = []

    for line_number, severity in warning_severity.items():
        block = document.findBlockByLineNumber(line_number - 1)
        if not block.isValid():
            continue

        selections.append(
            build_line_selection(
                QTextCursor(block),
                _SEVERITY_COLORS[severity],
            ),
        )

    return selections