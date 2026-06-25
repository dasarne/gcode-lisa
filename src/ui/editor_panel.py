"""G-Code editor panel."""

import re
from PyQt6.QtWidgets import QWidget, QTextEdit, QToolTip
from PyQt6.QtCore import pyqtSignal, QEvent, Qt
from PyQt6.QtGui import (
    QTextCharFormat,
    QColor,
    QTextCursor,
    QTextFormat,
    QSyntaxHighlighter,
    QFont,
    QTextDocument,
    QKeyEvent,
    QMouseEvent,
    QPalette,
    QGuiApplication,
)
from PyQt6.QtCore import QRegularExpression

from ..analyzer.analyzer import AnalysisWarning, WarningSeverity
from ..gcode.dialects import get_profile
from .editor.editor_search import (
    EditorSearchState,
    get_search_bounds,
    get_search_ranges,
    semantic_ranges_to_text_ranges,
    shift_scope_after_replace,
    update_search_scope,
)
from .editor.editor_comments import (
    update_hover_tooltip,
)
from .editor.editor_widget import (
    add_editor_to_layout,
    configure_editor_document,
    connect_editor_signals,
    create_editor_layout,
    create_editor_widget,
    enable_editor_mouse_tracking,
    get_editor_document,
    install_editor_event_filters,
)
from .editor.editor_highlighting import (
    EditorHighlightState,
    apply_editor_overlay_selections,
)
from .editor.editor_selection import (
    EditorSelectionState,
    capture_locked_selection,
    clear_line_selection,
    create_line_range_cursor,
    create_range_cursor,
    get_selected_lines,
    restore_locked_selection_cursor,
    update_multi_line_selection,
    update_single_line_selection,
)
from .selection.selection_model import SelectionModel
from .selection.selection_types import LineRange
from .editor.editor_undo import (
    delete_document_range,
    grouped_edit,
    replace_document_range,
    restore_plain_cursor,
    restore_scrollbars,
)
from .search_service import (
    compute_match_ranges,
    deserialize_multi_range_text,
    find_next_match,
    find_previous_match,
    replace_all_in_ranges,
    serialize_multi_range_text,
)
from .widgets import GCodeEditor

class _GCodeSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for G-code commands, axis words, and comments."""

    def __init__(self, document) -> None:
        super().__init__(document)
        # Commands known to the active dialect profile (None = accept any command)
        self._known_commands: set[str] | None = None

        _ci = QRegularExpression.PatternOption.CaseInsensitiveOption

        self._cmd_re = QRegularExpression(
            r"^\s*(?:N\d+\s+)?([GMT]\d+(?:\.\d+)?)", _ci,
        )
        self._x_re  = QRegularExpression(r"\bX[-+]?\d*\.?\d+\b", _ci)
        self._y_re  = QRegularExpression(r"\bY[-+]?\d*\.?\d+\b", _ci)
        self._z_re  = QRegularExpression(r"\bZ[-+]?\d*\.?\d+\b", _ci)
        self._ij_re = QRegularExpression(r"\b[IJ][-+]?\d*\.?\d+\b", _ci)
        self._f_re  = QRegularExpression(r"\bF[-+]?\d*\.?\d+\b", _ci)
        # Parenthetical comment: ( ... )
        self._paren_comment_re = QRegularExpression(r"\([^)]*\)")
        # Semicolon comment: ; to end of line
        self._semi_comment_re  = QRegularExpression(r";.*$")

        self._cmd_fmt = QTextCharFormat()
        self._cmd_fmt.setForeground(QColor("#0B3D91"))
        self._cmd_fmt.setFontWeight(QFont.Weight.Bold)

        # Unknown / unsupported command in the active dialect
        self._cmd_unknown_fmt = QTextCharFormat()
        self._cmd_unknown_fmt.setForeground(QColor("#AA3300"))
        self._cmd_unknown_fmt.setFontWeight(QFont.Weight.Bold)
        self._cmd_unknown_fmt.setFontUnderline(True)

        self._x_fmt = QTextCharFormat()
        self._x_fmt.setForeground(QColor("#CC3333"))

        self._y_fmt = QTextCharFormat()
        self._y_fmt.setForeground(QColor("#33AA33"))

        self._z_fmt = QTextCharFormat()
        self._z_fmt.setForeground(QColor("#3366CC"))

        self._ij_fmt = QTextCharFormat()
        self._ij_fmt.setForeground(QColor("#CC6600"))

        self._f_fmt = QTextCharFormat()
        self._f_fmt.setForeground(QColor("#9933CC"))

        self._comment_fmt = QTextCharFormat()
        self._comment_fmt.setForeground(QColor("#6A9955"))
        self._comment_fmt.setFontWeight(QFont.Weight.Bold)

    def update_profile(self, profile_id: str | None) -> None:
        """Set the active dialect profile; rehighlights all blocks."""
        if profile_id is None:
            self._known_commands = None
        else:
            try:
                profile = get_profile(profile_id)
                self._known_commands = {c.upper() for c in profile.known_commands}
            except ValueError:
                self._known_commands = None
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        # Commands first (highest visual priority)
        cmd_match = self._cmd_re.match(text)
        if cmd_match.hasMatch():
            start = cmd_match.capturedStart(1)
            length = cmd_match.capturedLength(1)
            command = cmd_match.captured(1).upper()
            if self._known_commands is not None and command not in self._known_commands:
                fmt = self._cmd_unknown_fmt
            else:
                fmt = self._cmd_fmt
            self.setFormat(start, length, fmt)

        self._apply_regex(text, self._x_re,  self._x_fmt)
        self._apply_regex(text, self._y_re,  self._y_fmt)
        self._apply_regex(text, self._z_re,  self._z_fmt)
        self._apply_regex(text, self._ij_re, self._ij_fmt)
        self._apply_regex(text, self._f_re,  self._f_fmt)

        # Comments last — override everything they cover
        self._apply_regex(text, self._paren_comment_re, self._comment_fmt)
        self._apply_regex(text, self._semi_comment_re,  self._comment_fmt)

    def _apply_regex(
        self,
        text: str,
        regex: QRegularExpression,
        fmt: QTextCharFormat,
    ) -> None:
        it = regex.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class EditorPanel(QWidget):
    """Side-panel showing the raw G-Code text with line highlighting."""

    line_selected = pyqtSignal(int)
    lines_selected = pyqtSignal(list)   # list[int] – all 1-based line numbers in selection
    content_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._language = "de"
        self._profile_id: str | None = None
        self._selected_line: int | None = None
        self._warning_severity: dict[int, WarningSeverity] = {}
        self._line_warnings: dict[int, list[AnalysisWarning]] = {}
        self._search_state = EditorSearchState()
        self._highlight_state = EditorHighlightState()
        self._selection_state = EditorSelectionState()
        self._interaction_lock = False
        self._suppress_cursor_events = False
        self._suppress_text_change = False
        self._managed_search_edit = False
        self._ctrl_drag_active = False
        self._ctrl_drag_mode: str | None = None
        self._ctrl_drag_visited_lines: set[int] = set()
        self._setup_ui()

    def set_language(self, language: str) -> None:
        self._language = language

    def set_profile_id(self, profile_id: str | None) -> None:
        """Update the active dialect profile and refresh syntax highlighting."""
        self._profile_id = profile_id
        # rehighlight() triggers textChanged which would re-enter _on_editor_content_changed.
        self._suppress_text_change = True
        self._syntax.update_profile(profile_id)
        self._suppress_text_change = False

    def _setup_ui(self) -> None:
        """Build the editor layout."""
        layout = create_editor_layout(self)

        self._text_edit = create_editor_widget()

        doc = configure_editor_document(self._text_edit)
        self._syntax = _GCodeSyntaxHighlighter(doc)

        enable_editor_mouse_tracking(self._text_edit)

        install_editor_event_filters(self._text_edit, self)

        connect_editor_signals(
            self._text_edit,
            self._on_cursor_moved,
            self._on_text_changed,
        )

        add_editor_to_layout(layout, self._text_edit)

    def eventFilter(self, obj, event) -> bool:
        """Handle hover tooltips without overriding native editor selection."""
        if self._interaction_lock and obj in (self._text_edit, self._text_edit.viewport()):
            if event.type() in {
                QEvent.Type.MouseButtonPress,
                QEvent.Type.MouseButtonRelease,
                QEvent.Type.MouseButtonDblClick,
            }:
                return True

            if event.type() == QEvent.Type.KeyPress:
                if not isinstance(event, QKeyEvent):
                    return True
                mods = event.modifiers()
                ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
                shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
                key = event.key()

                # Keep undo/redo available while interaction lock is active.
                allow_undo = ctrl and not shift and key in {Qt.Key.Key_Z, Qt.Key.Key_Y}
                allow_redo_alt = ctrl and shift and key == Qt.Key.Key_Z
                if allow_undo or allow_redo_alt:
                    return False

                return True

        if (
            obj is self._text_edit.viewport()
            and event.type() == QEvent.Type.MouseButtonPress
            and isinstance(event, QMouseEvent)
        ):
            if (
                event.button() == Qt.MouseButton.LeftButton
                and (
                    event.modifiers()
                    & Qt.KeyboardModifier.ControlModifier
                )
            ):
                cursor = self._text_edit.cursorForPosition(
                    event.position().toPoint(),
                )

                line_number = cursor.blockNumber() + 1

                self._selection_state.selected_line = line_number

                already_selected = (
                    self._selection_state.selection_model.contains(
                        line_number,
                    )
                )

                self._ctrl_drag_active = True
                self._ctrl_drag_mode = (
                    "remove" if already_selected else "add"
                )
                self._ctrl_drag_visited_lines = {line_number}

                self._selection_state.selection_model.toggle_line(
                    line_number,
                )

                self._suppress_cursor_events = True
                cursor.clearSelection()
                self._text_edit.setTextCursor(cursor)
                self._suppress_cursor_events = False

                self._apply_extra_selections(cursor)

                self.line_selected.emit(line_number)
                self.lines_selected.emit(
                    self._selection_state.selection_model.selected_lines(),
                )

                return True

        if (
            obj is self._text_edit.viewport()
            and event.type() == QEvent.Type.MouseMove
            and isinstance(event, QMouseEvent)
        ):
            if (
                self._ctrl_drag_active
                and self._ctrl_drag_mode is not None
                and (
                    event.buttons()
                    & Qt.MouseButton.LeftButton
                )
                and (
                    event.modifiers()
                    & Qt.KeyboardModifier.ControlModifier
                )
            ):
                cursor = self._text_edit.cursorForPosition(
                    event.position().toPoint(),
                )

                line_number = cursor.blockNumber() + 1

                if line_number not in self._ctrl_drag_visited_lines:
                    is_selected = (
                        self._selection_state.selection_model.contains(
                            line_number,
                        )
                    )

                    should_toggle = (
                        self._ctrl_drag_mode == "add"
                        and not is_selected
                    ) or (
                        self._ctrl_drag_mode == "remove"
                        and is_selected
                    )

                    if should_toggle:
                        self._selection_state.selection_model.toggle_line(
                            line_number,
                        )

                    self._ctrl_drag_visited_lines.add(
                        line_number,
                    )

                    self._suppress_cursor_events = True
                    cursor.clearSelection()
                    self._text_edit.setTextCursor(cursor)
                    self._suppress_cursor_events = False

                    self._apply_extra_selections(cursor)

                    self.line_selected.emit(line_number)
                    self.lines_selected.emit(
                        self._selection_state.selection_model.selected_lines(),
                    )

                return True

            update_hover_tooltip(
                text_edit=self._text_edit,
                event=event,
                language=self._language,
                profile_id=self._profile_id,
                line_warnings=self._line_warnings,
            )
            return False

        if (
            obj is self._text_edit.viewport()
            and event.type() == QEvent.Type.MouseButtonRelease
            and isinstance(event, QMouseEvent)
        ):
            self._ctrl_drag_active = False
            self._ctrl_drag_mode = None
            self._ctrl_drag_visited_lines.clear()

            return False

        if obj is self._text_edit.viewport() and event.type() == QEvent.Type.Leave:
            QToolTip.hideText()
            return False

        return super().eventFilter(obj, event)

    def set_interaction_lock(self, locked: bool) -> None:
        """Lock manual source edits/selection changes while keeping undo/redo available."""
        self._interaction_lock = locked
        if not locked:
            self._selection_state.locked_selection = None
            return

        capture_locked_selection(
            self._selection_state,
            self._text_edit.textCursor(),
            self._interaction_lock,
        )

    def _capture_locked_selection(self, cursor: QTextCursor) -> None:
        capture_locked_selection(
            self._selection_state,
            cursor,
            self._interaction_lock,
        )

    def _restore_locked_selection(self) -> None:
        if not self._interaction_lock:
            return

        cursor = restore_locked_selection_cursor(
            self._document(),
            self._selection_state.locked_selection,
        )
        if cursor is None:
            return
        self._suppress_cursor_events = True
        self._text_edit.setTextCursor(cursor)
        self._suppress_cursor_events = False

    def _document(self) -> QTextDocument:
        """Return the active editor document with a non-optional type."""
        return get_editor_document(self._text_edit)

    def load_content(self, content: str) -> None:
        """Load G-Code text into the editor."""
        self._suppress_text_change = True
        self._text_edit.setPlainText(content)
        document = self._text_edit.document()
        assert document is not None
        document.setModified(False)
        self._warning_severity.clear()
        self._line_warnings.clear()
        self._search_state.clear()
        self._sync_highlight_state()
        clear_line_selection(self._selection_state)
        self._apply_extra_selections()
        self._suppress_text_change = False

    def get_content(self) -> str:
        """Return the full editor content."""
        return self._text_edit.toPlainText()

    def is_modified(self) -> bool:
        """Return whether the editor document has unsaved changes."""
        document = self._text_edit.document()
        assert document is not None
        return document.isModified()

    def set_modified(self, modified: bool) -> None:
        """Set document modified flag."""
        document = self._text_edit.document()
        assert document is not None
        document.setModified(modified)

    def highlight_line(self, line_number: int) -> bool:
        """Scroll to and select the given 1-based line in the editor."""
        doc = self._document()
        block = doc.findBlockByLineNumber(line_number - 1)
        if not block.isValid():
            return False
        update_single_line_selection(
            self._selection_state,
            line_number,
        )

        cursor = QTextCursor(block)
        cursor.clearSelection()
        self._suppress_cursor_events = True
        self._text_edit.setTextCursor(cursor)
        self._suppress_cursor_events = False
        self._text_edit.centerCursor()
        self._apply_extra_selections(cursor)
        return True

    def highlight_lines(self, line_numbers: list[int]) -> None:
        """Highlight a non-contiguous set of 1-based line numbers."""
        if not line_numbers:
            clear_line_selection(self._selection_state)
            self._apply_extra_selections()
            return
        if len(line_numbers) == 1:
            self.highlight_line(line_numbers[0])
            return
        doc = self._document()
        valid_lines = sorted({ln for ln in line_numbers if ln > 0})
        if not valid_lines:
            return
        first = valid_lines[0]
        first_block = doc.findBlockByLineNumber(first - 1)
        if not first_block.isValid():
            return
        update_multi_line_selection(
            self._selection_state,
            valid_lines,
        )

        cursor = QTextCursor(first_block)
        cursor.clearSelection()
        self._suppress_cursor_events = True
        self._text_edit.setTextCursor(cursor)
        self._suppress_cursor_events = False
        self._text_edit.centerCursor()
        self._apply_extra_selections(cursor)
        # Keep canvas/editor in sync without collapsing to a contiguous range.
        self.lines_selected.emit(valid_lines)

    def _delete_multi_selected_lines(self) -> None:
        """Delete all currently multi-selected lines as full logical blocks."""
        doc = self._document()
        lines = sorted(
            self._selection_state.selection_model.selected_lines(),
            reverse=True,
        )
        if not lines:
            return

        self._suppress_cursor_events = True
        edit_cursor = self._text_edit.textCursor()
        with grouped_edit(edit_cursor):
            for line_number in lines:
                block = doc.findBlockByLineNumber(line_number - 1)
                if not block.isValid():
                    continue
                start = block.position()
                end = start + block.length()
                delete_document_range(doc, start, end)
        self._suppress_cursor_events = False

        clear_line_selection(self._selection_state)
        self._search_state.clear()
        self._sync_highlight_state()
        self._apply_extra_selections()
        self.lines_selected.emit([])

    def mark_warning_lines(self, warnings: list[AnalysisWarning]) -> None:
        """Apply warning highlights as non-destructive extra selections."""
        line_severity: dict[int, WarningSeverity] = {}
        line_warnings: dict[int, list[AnalysisWarning]] = {}
        for w in warnings:
            if w.line_number is None:
                continue
            line_warnings.setdefault(w.line_number, []).append(w)
            existing = line_severity.get(w.line_number)
            if existing is None or w.severity.value > existing.value:
                line_severity[w.line_number] = w.severity
        self._warning_severity = line_severity
        self._line_warnings = line_warnings
        self._apply_extra_selections()

    def copy(self) -> None:
        selection_model = self.selection_model()

        if len(selection_model.ranges) <= 1:
            self._text_edit.copy()
            return

        doc = self._document()
        copied_segments: list[str] = []

        for semantic_range in selection_model.ranges:
            for line_number in semantic_range.iter_lines():
                block = doc.findBlockByLineNumber(line_number - 1)

                if not block.isValid():
                    continue

                copied_segments.append(block.text())

        clipboard = QGuiApplication.clipboard()
        assert clipboard is not None
        clipboard.setText(
            serialize_multi_range_text(copied_segments),
        )

    def copy_lines(self, line_numbers: list[int]) -> str:
        """Copy explicit 1-based lines to clipboard and return copied text."""
        if not line_numbers:
            return ""
        old_selection = SelectionModel.from_snapshot(
            self._selection_state.selection_model.to_snapshot(),
        )

        valid_lines = sorted({ln for ln in line_numbers if ln > 0})

        update_multi_line_selection(
            self._selection_state,
            valid_lines,
        )

        self._copy_multi_selected_lines()

        clipboard = QGuiApplication.clipboard()
        assert clipboard is not None
        copied = clipboard.text()

        self._selection_state.selection_model = old_selection

        self._apply_extra_selections()
        return copied

    def delete_lines(self, line_numbers: list[int]) -> int:
        """Delete explicit 1-based lines and return deleted line count."""
        valid = sorted({ln for ln in line_numbers if ln > 0})
        if not valid:
            return 0
        update_multi_line_selection(
            self._selection_state,
            valid,
        )

        self._delete_multi_selected_lines()
        return len(valid)

    def cut_lines(self, line_numbers: list[int]) -> int:
        """Copy explicit lines to clipboard and delete them."""
        copied = self.copy_lines(line_numbers)
        if not copied:
            return 0
        return self.delete_lines(line_numbers)

    def scale_feedrate_lines(self, line_numbers: list[int], factor: float) -> int:
        """Scale F parameters on explicit 1-based lines; return changed line count."""
        valid = sorted({ln for ln in line_numbers if ln > 0})
        if not valid or factor <= 0:
            return 0

        doc = self._document()
        feed_re = re.compile(r"(?i)\\bF([+-]?\\d*\\.?\\d+)\\b")
        changed = 0

        self._managed_search_edit = True
        self._suppress_cursor_events = True
        edit_cursor = self._text_edit.textCursor()
        try:
            with grouped_edit(edit_cursor):
                for line_number in valid:
                    block = doc.findBlockByLineNumber(line_number - 1)
                    if not block.isValid():
                        continue

                    original = block.text()

                    def _replace(match: re.Match[str]) -> str:
                        value = float(match.group(1))
                        return f"F{value * factor:g}"

                    updated = feed_re.sub(_replace, original)
                    if updated == original:
                        continue

                    changed += 1
                    start = block.position()
                    end = start + len(original)
                    replace_document_range(doc, start, end, updated)
        finally:
            self._suppress_cursor_events = False
            self._managed_search_edit = False

        if changed > 0:
            self._invalidate_search_state()

        return changed

    def _copy_multi_selected_lines(self) -> None:
        doc = self._document()
        lines_text: list[str] = []
        for line_number in (
            self._selection_state.selection_model.selected_lines()
        ):
            block = doc.findBlockByLineNumber(line_number - 1)
            if block.isValid():
                lines_text.append(block.text())

        clipboard = QGuiApplication.clipboard()
        assert clipboard is not None
        clipboard.setText(
            serialize_multi_range_text(lines_text),
        )

    def paste(self) -> None:
        """Paste using semantic primary selection semantics.

        Transition note:
        - Multi-range paste fan-out is not implemented yet.
        - Clipboard multi-range structure is already preserved.
        - Current behavior pastes merged content into the primary selection.
        """
        clipboard = QGuiApplication.clipboard()
        assert clipboard is not None

        pasted_text = clipboard.text()

        if not pasted_text:
            return

        segments = deserialize_multi_range_text(pasted_text)

        cursor = self._text_edit.textCursor()

        self._managed_search_edit = True

        try:
            with grouped_edit(cursor):
                cursor.insertText("\n".join(segments))

            self._text_edit.setTextCursor(cursor)

            inserted_line = cursor.blockNumber() + 1

            update_single_line_selection(
                self._selection_state,
                inserted_line,
            )

            self._apply_extra_selections(cursor)
        finally:
            self._managed_search_edit = False

    def undo(self) -> None:
        """Undo last edit."""
        self._text_edit.undo()

        self._apply_extra_selections()

    def redo(self) -> None:
        """Redo last undone edit."""
        self._text_edit.redo()

        self._apply_extra_selections()

    def can_undo(self) -> bool:
        """Return whether undo is available."""
        return self._document().isUndoAvailable()

    def can_redo(self) -> bool:
        """Return whether redo is available."""
        return self._document().isRedoAvailable()

    def get_selected_text(self) -> str:
        """Return text of currently selected lines."""
        semantic_lines = (
            self._selection_state.selection_model.selected_lines()
        )

        if semantic_lines:
            doc = self._document()
            lines_text: list[str] = []

            for ln in semantic_lines:
                block = doc.findBlockByLineNumber(ln - 1)

                if block.isValid():
                    lines_text.append(block.text())

            return "\n".join(lines_text)
        cursor = self._text_edit.textCursor()
        return cursor.selectedText()

    def get_selected_lines(self) -> list[int]:
        """Return currently active selected lines (1-based).

        Transition note:
        - SelectionModel is now the primary semantic source.
        - QTextCursor fallback remains only for native transient text selection.
        """
        model_lines = self._selection_state.selection_model.selected_lines()

        if model_lines:
            return model_lines

        cursor = self._text_edit.textCursor()

        if not cursor.hasSelection():
            return []

        return get_selected_lines(
            self._document(),
            cursor,
        )

    def selection_model(self) -> SelectionModel:
        """Return the shared semantic selection model instance.

        Transition note:
        - QTextCursor is still used for native editor interaction.
        - The semantic ownership is gradually moving into SelectionModel.
        """
        return self._selection_state.selection_model

    def select_line_range(self, start_line: int, end_line: int) -> None:
        """Create a native text selection from start_line to end_line (1-based).

        Transition note:
        - QTextCursor selection remains a rendering/native interaction layer.
        - SelectionModel stores the semantic authoritative range.
        """
        semantic_range = LineRange(
            min(start_line, end_line),
            max(start_line, end_line),
        )

        self._selection_state.selection_model.set_ranges(
            [semantic_range],
        )

        cursor = create_line_range_cursor(
            self._document(),
            start_line,
            end_line,
        )

        if cursor is None:
            return

        self._suppress_cursor_events = True
        self._text_edit.setTextCursor(cursor)
        self._suppress_cursor_events = False
        self._capture_locked_selection(cursor)
        self._selected_line = cursor.blockNumber() + 1
        self._apply_extra_selections(cursor)

    def clear_search_highlights(self) -> None:
        """Clear search-scope and match overlays."""
        self._search_state.clear()
        self._apply_extra_selections()

    def find_next(self, term: str, use_regex: bool = False, search_in_selection: bool = False, case_sensitive: bool = False) -> bool:
        """Find next occurrence with optional regex support and wrap-around."""
        if not term:
            self._search_state.matches = []
            self._apply_extra_selections()
            return False

        cursor = self._text_edit.textCursor()
        update_search_scope(
            self._search_state,
            cursor,
            search_in_selection,
            self.selection_model(),
        )
        self._update_search_matches(
            term,
            use_regex,
            cursor,
            search_in_selection,
            case_sensitive,
        )

        if not self._search_state.matches:
            return False

        anchor = cursor.selectionEnd() if cursor.hasSelection() else cursor.position()
        match = find_next_match(self._search_state.matches, anchor)
        if match is None:
            return False

        self._select_range(*match)
        return True

    def find_previous(self, term: str, use_regex: bool = False, search_in_selection: bool = False, case_sensitive: bool = False) -> bool:
        """Find previous occurrence with optional regex support and wrap-around."""
        if not term:
            self._search_state.matches = []
            self._apply_extra_selections()
            return False

        cursor = self._text_edit.textCursor()
        update_search_scope(
            self._search_state,
            cursor,
            search_in_selection,
            self.selection_model(),
        )
        self._update_search_matches(
            term,
            use_regex,
            cursor,
            search_in_selection,
            case_sensitive,
        )

        if not self._search_state.matches:
            return False

        anchor = cursor.selectionStart() if cursor.hasSelection() else cursor.position()
        match = find_previous_match(self._search_state.matches, anchor)
        if match is None:
            return False

        self._select_range(*match)
        return True

    def get_search_match_count(self) -> int:
        """Return the number of currently cached search matches."""
        return len(self._search_state.matches)

    def preview_search(
        self,
        term: str,
        use_regex: bool = False,
        search_in_selection: bool = False,
        case_sensitive: bool = False,
    ) -> tuple[bool, int]:
        """Incremental search preview: keep match selected and return hit count."""
        cursor = self._text_edit.textCursor()
        update_search_scope(
            self._search_state,
            cursor,
            search_in_selection,
            self.selection_model(),
        )
        # When the scope was just locked from the cursor's current selection,
        # that selection (orange QPalette highlight) would cover the green
        # match highlights.  Move the cursor to scope start to make them visible.
        if (
            search_in_selection
            and self._search_state.scope is not None
            and cursor.hasSelection()
            and cursor.selectionStart() == self._search_state.scope[0]
            and cursor.selectionEnd() == self._search_state.scope[1]
        ):
            cleared = QTextCursor(self._document())
            cleared.setPosition(self._search_state.scope[0])
            self._suppress_cursor_events = True
            self._text_edit.setTextCursor(cleared)
            self._suppress_cursor_events = False
            cursor = cleared

        if not term:
            self._search_state.matches = []
            self._apply_extra_selections()
            return (False, 0)

        content = self.get_content()
        ranges = get_search_ranges(
            content,
            cursor,
            search_in_selection,
            self._search_state.scope,
            self._search_state.semantic_scope,
        )
        if ranges is None:
            self._search_state.matches = []
            self._apply_extra_selections()
            return (False, 0)

        self._search_state.matches = compute_match_ranges(
            term,
            use_regex,
            content,
            ranges,
            case_sensitive,
        )
        self._apply_extra_selections()
        count = len(self._search_state.matches)
        # Do not move the text cursor during incremental preview typing.
        # This keeps the user's current selection/scope intact.
        return (count > 0, count)

    def replace_next(
        self,
        needle: str,
        replacement: str,
        use_regex: bool = False,
        search_in_selection: bool = False,
        case_sensitive: bool = False,
    ) -> bool:
        """Replace next occurrence and move to next. Returns True if replacement made."""
        if not needle:
            return False
        cursor = self._text_edit.textCursor()
        if use_regex:
            return self._replace_regex_next(needle, replacement, cursor, search_in_selection, case_sensitive)
        if not self.find_next(needle, use_regex=False, search_in_selection=search_in_selection, case_sensitive=case_sensitive):
            return False
        cursor = self._text_edit.textCursor()
        match_start = cursor.selectionStart()
        match_end = cursor.selectionEnd()
        self._managed_search_edit = True
        try:
            with grouped_edit(cursor):
                cursor.removeSelectedText()
                cursor.insertText(replacement)
            self._text_edit.setTextCursor(cursor)
            shift_scope_after_replace(
                self._search_state,
                match_start,
                match_end,
                len(replacement),
            )
        finally:
            self._managed_search_edit = False
        return True

    def replace_previous(
        self,
        needle: str,
        replacement: str,
        use_regex: bool = False,
        search_in_selection: bool = False,
        case_sensitive: bool = False,
    ) -> bool:
        """Replace previous occurrence and move to previous. Returns True if replacement made."""
        if not needle:
            return False
        cursor = self._text_edit.textCursor()
        if use_regex:
            return self._replace_regex_previous(needle, replacement, cursor, search_in_selection, case_sensitive)
        if not self._selection_matches_query(cursor, needle, use_regex=False):
            if not self.find_previous(needle, use_regex=False, search_in_selection=search_in_selection, case_sensitive=case_sensitive):
                return False
            cursor = self._text_edit.textCursor()
        match_start = cursor.selectionStart()
        match_end = cursor.selectionEnd()
        self._managed_search_edit = True
        try:
            with grouped_edit(cursor):
                cursor.removeSelectedText()
                cursor.insertText(replacement)
            self._text_edit.setTextCursor(cursor)
            shift_scope_after_replace(
                self._search_state,
                match_start,
                match_end,
                len(replacement),
            )
        finally:
            self._managed_search_edit = False
        self._move_cursor_to_position(match_start)
        self.find_previous(needle, use_regex=False, search_in_selection=search_in_selection, case_sensitive=case_sensitive)
        return True

    def replace_all(
        self,
        needle: str,
        replacement: str,
        use_regex: bool = False,
        search_in_selection: bool = False,
        case_sensitive: bool = False,
    ) -> int:
        """Replace all occurrences and return replacement count."""
        if not needle:
            return 0
        content = self.get_content()

        cursor = self._text_edit.textCursor()
        update_search_scope(
            self._search_state,
            cursor,
            search_in_selection,
            self.selection_model(),
        )
        ranges = get_search_ranges(
            content,
            cursor,
            search_in_selection,
            self._search_state.scope,
            self._search_state.semantic_scope,
        )

        selection_ranges = self.selection_model().ranges

        if search_in_selection and selection_ranges:
            semantic_ranges = semantic_ranges_to_text_ranges(
                content,
                selection_ranges,
            )

            if semantic_ranges:
                ranges = semantic_ranges

        if ranges is None:
            return 0

        new_content, count = replace_all_in_ranges(
            content,
            ranges,
            needle,
            replacement,
            use_regex,
            case_sensitive,
        )
        if count == 0:
            return 0

        # Keep the user's context stable (cursor + visible source viewport).
        prev_cursor = self._text_edit.textCursor()
        prev_anchor = prev_cursor.anchor()
        prev_pos = prev_cursor.position()
        vscroll = self._text_edit.verticalScrollBar()
        hscroll = self._text_edit.horizontalScrollBar()
        assert vscroll is not None
        assert hscroll is not None

        prev_vscroll = vscroll.value()
        prev_hscroll = hscroll.value()

        self._suppress_text_change = True
        edit_cursor = QTextCursor(self._document())
        with grouped_edit(edit_cursor):
            edit_cursor.select(QTextCursor.SelectionType.Document)
            edit_cursor.insertText(new_content)

        max_pos = len(new_content)
        restore_pos = max(0, min(prev_pos, max_pos))
        # Do NOT restore the selection anchor – after content changed, the old
        # selection offsets are wrong and would leave a stale _search_scope that
        # causes double-replacements on the next operation.
        self._suppress_cursor_events = True
        restore_plain_cursor(self._text_edit, restore_pos)
        self._suppress_cursor_events = False
        restore_scrollbars(
            vscroll,
            hscroll,
            prev_vscroll,
            prev_hscroll,
        )

        # Invalidate scope and match cache – positions are meaningless in the
        # new content.  The next interaction will re-establish them.
        self._search_state.clear()
        self._apply_extra_selections()
        self._suppress_text_change = False
        return count

    def _find_literal(
        self,
        term: str,
        forward: bool,
        cursor: QTextCursor,
        search_in_selection: bool,
    ) -> bool:
        content = self.get_content()
        bounds = get_search_bounds(
            content,
            cursor,
            search_in_selection,
            self._search_state.scope,
        )
        if bounds is None:
            return False
        start_bound, end_bound = bounds

        if forward:
            search_from = cursor.selectionEnd() if cursor.hasSelection() else cursor.position()
            search_from = max(start_bound, min(search_from, end_bound))
            found = content.find(term, search_from, end_bound)
            if found == -1:
                found = content.find(term, start_bound, search_from)
        else:
            search_to = cursor.selectionStart() if cursor.hasSelection() else cursor.position()
            search_to = max(start_bound, min(search_to, end_bound))
            found = content.rfind(term, start_bound, search_to)
            if found == -1:
                found = content.rfind(term, search_to, end_bound)

        if found == -1:
            return False

        self._select_range(found, found + len(term))
        return True

    def _find_regex(
        self,
        pattern: str,
        forward: bool = True,
        cursor: QTextCursor | None = None,
        search_in_selection: bool = False,
    ) -> bool:
        """Find regex pattern from current cursor position."""
        if cursor is None:
            cursor = self._text_edit.textCursor()
        content = self.get_content()
        try:
            regex = re.compile(pattern, re.MULTILINE)
        except re.error:
            return False

        bounds = get_search_bounds(
            content,
            cursor,
            search_in_selection,
            self._search_state.scope,
        )
        if bounds is None:
            return False
        start_bound, end_bound = bounds

        if forward:
            start_pos = cursor.position()
            if cursor.hasSelection():
                start_pos = cursor.selectionEnd()
            start_pos = max(start_bound, min(start_pos, end_bound))

            matches = list(regex.finditer(content[start_pos:end_bound]))
            if matches:
                match = matches[0]
                self._select_range(start_pos + match.start(), start_pos + match.end())
                return True

            matches = list(regex.finditer(content[start_bound:start_pos]))
            if matches:
                match = matches[0]
                self._select_range(start_bound + match.start(), start_bound + match.end())
                return True
            return False

        end_pos = cursor.position()
        if cursor.hasSelection():
            end_pos = cursor.selectionStart()
        end_pos = max(start_bound, min(end_pos, end_bound))

        if end_pos > start_bound:
            matches = list(regex.finditer(content[start_bound:end_pos]))
            if cursor.hasSelection():
                end_pos = cursor.selectionStart()
            if matches:
                match = matches[-1]
                self._select_range(start_bound + match.start(), start_bound + match.end())
                return True

        matches = list(regex.finditer(content[end_pos:end_bound]))
        if matches:
            match = matches[-1]
            self._select_range(end_pos + match.start(), end_pos + match.end())
            return True
        return False

    def _replace_regex_next(
        self,
        pattern: str,
        replacement: str,
        cursor: QTextCursor,
        search_in_selection: bool,
        case_sensitive: bool = False,
    ) -> bool:
        """Replace next regex match and move cursor."""
        flags = re.MULTILINE
        if not case_sensitive:
            flags |= re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error:
            return False
        if not self.find_next(pattern, use_regex=True, search_in_selection=search_in_selection, case_sensitive=case_sensitive):
            return False
        cursor = self._text_edit.textCursor()
        match_text = cursor.selectedText()
        new_text = regex.sub(replacement, match_text, count=1)
        match_start = cursor.selectionStart()
        match_end = cursor.selectionEnd()
        self._managed_search_edit = True
        try:
            with grouped_edit(cursor):
                cursor.removeSelectedText()
                cursor.insertText(new_text)
            self._text_edit.setTextCursor(cursor)
            shift_scope_after_replace(
                self._search_state,
                match_start,
                match_end,
                len(new_text),
            )
        finally:
            self._managed_search_edit = False
        return True

    def _replace_regex_previous(
        self,
        pattern: str,
        replacement: str,
        cursor: QTextCursor,
        search_in_selection: bool,
        case_sensitive: bool = False,
    ) -> bool:
        """Replace previous regex match and move cursor."""
        flags = re.MULTILINE
        if not case_sensitive:
            flags |= re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error:
            return False
        if not self._selection_matches_query(cursor, pattern, use_regex=True):
            if not self.find_previous(pattern, use_regex=True, search_in_selection=search_in_selection, case_sensitive=case_sensitive):
                return False
            cursor = self._text_edit.textCursor()
        match_text = cursor.selectedText()
        new_text = regex.sub(replacement, match_text, count=1)
        match_start = cursor.selectionStart()
        match_end = cursor.selectionEnd()
        self._managed_search_edit = True
        try:
            with grouped_edit(cursor):
                cursor.removeSelectedText()
                cursor.insertText(new_text)
            self._text_edit.setTextCursor(cursor)
            shift_scope_after_replace(
                self._search_state,
                match_start,
                match_end,
                len(new_text),
            )
        finally:
            self._managed_search_edit = False
        self._move_cursor_to_position(match_start)
        self.find_previous(pattern, use_regex=True, search_in_selection=search_in_selection, case_sensitive=case_sensitive)
        return True

    def _move_cursor_to_position(self, position: int) -> None:
        """Move the text cursor to a plain insertion point without selection."""
        self._suppress_cursor_events = True
        restore_plain_cursor(self._text_edit, position)
        self._suppress_cursor_events = False

    def _selection_matches_query(
        self,
        cursor: QTextCursor,
        term: str,
        use_regex: bool,
    ) -> bool:
        """Return whether the current selection itself is a match for the query."""
        if not cursor.hasSelection():
            return False
        selected_text = cursor.selectedText()
        if use_regex:
            try:
                return re.fullmatch(term, selected_text, re.MULTILINE) is not None
            except re.error:
                return False
        return selected_text == term

    def _count_matches(
        self,
        term: str,
        use_regex: bool,
        content: str,
        bounds: tuple[int, int],
        case_sensitive: bool = False,
    ) -> int:
        return len(compute_match_ranges(term, use_regex, content, [bounds], case_sensitive))

    def _update_search_matches(
        self,
        term: str,
        use_regex: bool,
        cursor: QTextCursor,
        search_in_selection: bool,
        case_sensitive: bool = False,
    ) -> None:
        content = self.get_content()
        ranges = get_search_ranges(
            content,
            cursor,
            search_in_selection,
            self._search_state.scope,
            self._search_state.semantic_scope,
        )
        if not term or ranges is None:
            self._search_state.matches = []
            self._apply_extra_selections(cursor)
            return

        self._search_state.matches = compute_match_ranges(
            term,
            use_regex,
            content,
            ranges,
            case_sensitive,
        )
        self._apply_extra_selections(cursor)

    def _compute_match_ranges(
        self,
        term: str,
        use_regex: bool,
        content: str,
        ranges: list[tuple[int, int]],
        case_sensitive: bool = False,
    ) -> list[tuple[int, int]]:
        return compute_match_ranges(term, use_regex, content, ranges, case_sensitive)

    def _select_range(self, start: int, end: int) -> None:
        new_cursor = create_range_cursor(
            self._document(),
            start,
            end,
        )
        self._suppress_cursor_events = True
        self._text_edit.setTextCursor(new_cursor)
        self._suppress_cursor_events = False
        self._capture_locked_selection(new_cursor)
        self._selection_state.selected_line = (
            new_cursor.blockNumber() + 1
        )
        self._apply_extra_selections(new_cursor)

    def _on_cursor_moved(self) -> None:
        """Emit the current 1-based line number whenever the cursor moves."""
        if self._suppress_cursor_events:
            return
        if self._interaction_lock:
            self._restore_locked_selection()
            return
        cursor = self._text_edit.textCursor()
        line_number = cursor.blockNumber() + 1
        self._selection_state.selected_line = line_number

        if cursor.hasSelection():
            selected_lines = get_selected_lines(
                self._document(),
                cursor,
            )

            update_multi_line_selection(
                self._selection_state,
                selected_lines,
            )

            active_position = cursor.position()

            self._suppress_cursor_events = True

            cursor.clearSelection()
            cursor.setPosition(active_position)

            self._text_edit.setTextCursor(cursor)

            self._suppress_cursor_events = False
        else:
            update_single_line_selection(
                self._selection_state,
                line_number,
            )

        self._apply_extra_selections(cursor)
        self.line_selected.emit(line_number)
        self.lines_selected.emit(
            self._selection_state.selection_model.selected_lines(),
        )

    def _on_text_changed(self) -> None:
        if self._suppress_text_change:
            return
        if not self._managed_search_edit:
            self._invalidate_search_state()
        self.content_changed.emit(self.get_content())

    def _invalidate_search_state(self) -> None:
        """Clear cached search overlays after arbitrary document edits.

        Undo/redo and free typing can move or delete text without going through
        the managed search-replace path, so cached absolute match offsets are no
        longer trustworthy after such edits.

        Transition note:
        - SelectionModel remains authoritative semantic state.
        - Undo/redo must not implicitly discard semantic selections.
        """
        self._search_state.clear()
        self._apply_extra_selections()

    def _sync_highlight_state(self) -> None:
        """Synchronize overlay rendering state from search state."""
        self._highlight_state.search_scope = self._search_state.scope
        self._highlight_state.search_matches = list(
            self._search_state.matches,
        )

    def _apply_extra_selections(self, cursor: QTextCursor | None = None) -> None:
        """Apply warning-line and current-line overlays."""
        if cursor is None:
            cursor = self._text_edit.textCursor()

        self._sync_highlight_state()

        apply_editor_overlay_selections(
            self._text_edit,
            self._document(),
            cursor,
            self._warning_severity,
            self._selection_state.selection_model,
            self._highlight_state,
        )
