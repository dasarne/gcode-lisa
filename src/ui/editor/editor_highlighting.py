"""Highlighting and overlay composition helpers for EditorPanel."""

from __future__ import annotations

from dataclasses import dataclass, field

from PyQt6.QtGui import QColor, QTextCursor, QTextDocument
from typing import Protocol

from PyQt6.QtWidgets import QTextEdit

from .editor_selection import (
    build_current_line_selection,
    build_multi_line_selections,
    build_warning_selections,
    should_show_current_line_selection,
)

_SEARCH_SCOPE_COLOR = "#FFF4BF"
_SEARCH_MATCH_COLOR = "#CCF5CC"


class _ExtraSelectionEditor(Protocol):
    """Editor protocol exposing setExtraSelections()."""

    def setExtraSelections(
        self,
        selections: list[QTextEdit.ExtraSelection],
    ) -> None: ...


@dataclass(slots=True)
class EditorHighlightState:
    """Overlay/highlighting state shared with EditorPanel."""

    search_scope: tuple[int, int] | None = None
    search_matches: list[tuple[int, int]] = field(default_factory=list)


def build_search_scope_selection(
    document: QTextDocument,
    scope: tuple[int, int],
) -> QTextEdit.ExtraSelection:
    """Build the search-scope overlay selection."""
    scope_start, scope_end = scope

    selection = QTextEdit.ExtraSelection()
    scope_cursor = QTextCursor(document)
    scope_cursor.setPosition(scope_start)
    scope_cursor.setPosition(scope_end, QTextCursor.MoveMode.KeepAnchor)

    selection.cursor = scope_cursor
    selection.format.setBackground(QColor(_SEARCH_SCOPE_COLOR))

    return selection


def build_search_match_selection(
    document: QTextDocument,
    match_start: int,
    match_end: int,
) -> QTextEdit.ExtraSelection:
    """Build a search-match overlay selection."""
    selection = QTextEdit.ExtraSelection()

    match_cursor = QTextCursor(document)
    match_cursor.setPosition(match_start)
    match_cursor.setPosition(match_end, QTextCursor.MoveMode.KeepAnchor)

    selection.cursor = match_cursor
    selection.format.setBackground(QColor(_SEARCH_MATCH_COLOR))

    return selection


def build_search_overlay_selections(
    document: QTextDocument,
    state: EditorHighlightState,
) -> list[QTextEdit.ExtraSelection]:
    """Build search scope and match overlays in render order."""
    selections: list[QTextEdit.ExtraSelection] = []

    if state.search_scope is not None:
        selections.append(
            build_search_scope_selection(
                document,
                state.search_scope,
            ),
        )

    for match_start, match_end in state.search_matches:
        selections.append(
            build_search_match_selection(
                document,
                match_start,
                match_end,
            ),
        )

    return selections


def build_editor_overlay_selections(
    document: QTextDocument,
    cursor: QTextCursor,
    warning_severity,
    selection_model,
    highlight_state: EditorHighlightState,
) -> list[QTextEdit.ExtraSelection]:
    """Compose editor overlays in the current rendering order."""
    selections: list[QTextEdit.ExtraSelection] = []

    selections.extend(
        build_warning_selections(
            document,
            warning_severity,
        ),
    )

    selections.extend(
        build_multi_line_selections(
            document,
            selection_model,
        ),
    )

    cursor_line = cursor.blockNumber() + 1
    if should_show_current_line_selection(
        cursor_line,
        selection_model,
    ):
        selections.append(
            build_current_line_selection(cursor),
        )

    # Search overlays intentionally render last so they remain visible
    # above line-based overlays.
    selections.extend(
        build_search_overlay_selections(
            document,
            highlight_state,
        ),
    )

    return selections


def apply_editor_overlay_selections(
    editor: _ExtraSelectionEditor,
    document: QTextDocument,
    cursor: QTextCursor,
    warning_severity,
    selection_model,
    highlight_state: EditorHighlightState,
) -> None:
    """Build and apply all editor overlay selections."""
    selections = build_editor_overlay_selections(
        document,
        cursor,
        warning_severity,
        selection_model,
        highlight_state,
    )
    editor.setExtraSelections(selections)