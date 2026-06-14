"""Search orchestration helpers for EditorPanel."""

from __future__ import annotations

from dataclasses import dataclass, field

from PyQt6.QtGui import QTextCursor


TextRange = tuple[int, int]


@dataclass(slots=True)
class EditorSearchState:
    """Mutable editor search state shared with EditorPanel."""

    scope: TextRange | None = None
    matches: list[TextRange] = field(default_factory=list)

    def clear(self) -> None:
        """Reset cached scope and match state."""
        self.scope = None
        self.matches.clear()


def get_search_bounds(
    content: str,
    cursor: QTextCursor,
    search_in_selection: bool,
    scope: TextRange | None,
) -> TextRange | None:
    """Return active search bounds for the current editor state."""
    if not search_in_selection:
        return (0, len(content))

    if scope is not None:
        return scope

    if not cursor.hasSelection():
        return None

    return (cursor.selectionStart(), cursor.selectionEnd())


def get_search_ranges(
    content: str,
    cursor: QTextCursor,
    search_in_selection: bool,
    scope: TextRange | None,
) -> list[TextRange] | None:
    """Return concrete search ranges from document or active selection."""
    if not search_in_selection:
        return [(0, len(content))]

    if cursor.hasSelection():
        return [(cursor.selectionStart(), cursor.selectionEnd())]

    bounds = get_search_bounds(
        content,
        cursor,
        search_in_selection,
        scope,
    )
    if bounds is None:
        return None

    return [bounds]


def update_search_scope(
    state: EditorSearchState,
    cursor: QTextCursor,
    search_in_selection: bool,
) -> bool:
    """Update persistent search scope.

    Returns True when the scope changed.
    """
    if not search_in_selection:
        if state.scope is None:
            return False

        state.scope = None
        return True

    # Preserve explicitly locked scope created from the original user
    # selection. Match selections must not overwrite it.
    if state.scope is not None:
        return False

    if not cursor.hasSelection():
        return False

    state.scope = (
        cursor.selectionStart(),
        cursor.selectionEnd(),
    )
    return True


def shift_scope_after_replace(
    state: EditorSearchState,
    match_start: int,
    match_end: int,
    new_length: int,
) -> None:
    """Shift cached scope and match ranges after replacement edits."""
    delta = new_length - (match_end - match_start)

    if state.scope is not None:
        scope_start, scope_end = state.scope
        if match_end <= scope_end:
            state.scope = (scope_start, scope_end + delta)

    updated: list[TextRange] = []

    for start, end in state.matches:
        if end <= match_start:
            updated.append((start, end))
        elif start >= match_end:
            updated.append((start + delta, end + delta))

    state.matches = updated