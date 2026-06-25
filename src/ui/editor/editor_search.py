"""Search orchestration helpers for EditorPanel."""

from __future__ import annotations

from dataclasses import dataclass, field

from PyQt6.QtGui import QTextCursor

from ..selection.selection_model import SelectionModel
from ..selection.selection_types import LineRange


TextRange = tuple[int, int]


def semantic_ranges_to_text_ranges(
    content: str,
    semantic_ranges: list[LineRange],
) -> list[TextRange]:
    """Convert semantic line ranges into stable text-offset ranges."""
    if not semantic_ranges:
        return []

    lines = content.splitlines(keepends=True)

    offsets: list[tuple[int, int]] = []
    offset = 0

    for line in lines:
        start = offset
        end = offset + len(line)
        offsets.append((start, end))
        offset = end

    resolved: list[TextRange] = []

    for semantic_range in semantic_ranges:
        range_start: int | None = None
        range_end: int | None = None

        for line_number in semantic_range.iter_lines():
            index = line_number - 1

            if index < 0 or index >= len(offsets):
                continue

            start, end = offsets[index]

            if range_start is None:
                range_start = start

            range_end = end

        if range_start is None or range_end is None:
            continue

        resolved.append((range_start, range_end))

    return resolved


@dataclass(slots=True)
class EditorSearchState:
    """Mutable editor search state shared with EditorPanel."""

    scope: TextRange | None = None
    semantic_scope: list[LineRange] | None = None
    matches: list[TextRange] = field(default_factory=list)

    def clear(self) -> None:
        """Reset cached scope and match state."""
        self.scope = None
        self.semantic_scope = None
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

    return None


def get_search_ranges(
    content: str,
    cursor: QTextCursor,
    search_in_selection: bool,
    scope: TextRange | None,
    semantic_scope: list[LineRange] | None = None,
) -> list[TextRange] | None:
    """Return concrete search ranges from document or active selection."""
    if not search_in_selection:
        return [(0, len(content))]

    if semantic_scope:
        resolved = semantic_ranges_to_text_ranges(
            content,
            semantic_scope,
        )

        if resolved:
            return resolved

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
    selection_model: SelectionModel | None = None,
) -> bool:
    """Update persistent search scope.

    Returns True when the scope changed.
    """
    if not search_in_selection:
        changed = (
            state.scope is not None
            or state.semantic_scope is not None
        )

        state.scope = None
        state.semantic_scope = None
        return changed

    # Preserve explicitly locked scope created from the original user
    # selection. Match selections must not overwrite it.
    if (
        state.scope is not None
        or state.semantic_scope is not None
    ):
        return False

    if (
        selection_model is not None
        and not selection_model.is_empty
    ):
        state.semantic_scope = list(selection_model.ranges)
        return True

    return False


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