"""Lightweight document mutation and cursor helpers for EditorPanel."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator

from PyQt6.QtGui import QTextCursor, QTextDocument
from PyQt6.QtWidgets import QPlainTextEdit, QScrollBar


@contextmanager
def grouped_edit(cursor: QTextCursor) -> Iterator[None]:
    """Wrap mutations in a single undo edit block."""
    cursor.beginEditBlock()
    try:
        yield
    finally:
        cursor.endEditBlock()


def delete_document_range(
    document: QTextDocument,
    start: int,
    end: int,
) -> None:
    """Delete the given document range."""
    cursor = QTextCursor(document)
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
    cursor.removeSelectedText()


def replace_document_range(
    document: QTextDocument,
    start: int,
    end: int,
    text: str,
) -> None:
    """Replace the given document range with text."""
    cursor = QTextCursor(document)
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
    cursor.removeSelectedText()
    cursor.insertText(text)


def restore_plain_cursor(
    text_edit: QPlainTextEdit,
    position: int,
) -> QTextCursor:
    """Restore a plain insertion cursor without a selection."""
    cursor = text_edit.textCursor()
    cursor.setPosition(position)
    text_edit.setTextCursor(cursor)
    return cursor


def restore_scrollbars(
    vertical_scrollbar: QScrollBar,
    horizontal_scrollbar: QScrollBar,
    vertical_value: int,
    horizontal_value: int,
) -> None:
    """Restore editor scrollbar positions."""
    vertical_scrollbar.setValue(vertical_value)
    horizontal_scrollbar.setValue(horizontal_value)