"""Lightweight comment-related editor helpers."""

from __future__ import annotations

from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QToolTip

from ..editor_tooltips import (
    describe_line_warnings,
    describe_token_at,
)


def update_hover_tooltip(
    *,
    text_edit,
    event: QMouseEvent,
    language: str,
    profile_id: str | None,
    line_warnings,
) -> None:
    """Show a lightweight hover tooltip for comments/tokens/warnings."""
    cursor = text_edit.cursorForPosition(event.position().toPoint())
    block = cursor.block()

    if not block.isValid():
        QToolTip.hideText()
        return

    line_text = block.text()
    line_number = block.blockNumber() + 1
    column = cursor.positionInBlock()

    token_text = describe_token_at(
        line_text,
        column,
        language=language,
        profile_id=profile_id,
    )

    warning_text = describe_line_warnings(
        line_number,
        line_warnings,
        language=language,
    )

    if token_text and warning_text:
        tooltip = f"{token_text}\n\n{warning_text}"
    elif token_text:
        tooltip = token_text
    elif warning_text:
        tooltip = warning_text
    else:
        QToolTip.hideText()
        return

    QToolTip.showText(
        event.globalPosition().toPoint(),
        tooltip,
        text_edit.viewport(),
    )