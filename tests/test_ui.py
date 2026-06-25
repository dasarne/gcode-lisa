"""Tests for src.ui modules (import-only; no display required)."""

import os
import sys

import pytest
from pathlib import Path

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest


from src.ui.canvas_panel import _axis_limits
from src.ui.editor_panel import EditorPanel
from src.ui.view_math import (
    axis_tick_steps,
    nice_integer_step,
    normalized_spacing_step,
)


@pytest.mark.skipif(
    not os.environ.get("DISPLAY") and not os.environ.get("QT_QPA_PLATFORM"),
    reason="No display available",
)
def test_main_window_import():
    """MainWindow should be importable."""
    from src.ui.main_window import MainWindow  # noqa: F401


@pytest.mark.parametrize(
    ("min_step", "expected"),
    [
        (0.0, 1),
        (0.1, 1),
        (0.999, 1),
        (1.0, 1),
        (1.1, 2),
        (2.1, 5),
        (5.1, 10),
        (11.0, 20),
        (99.0, 100),
        (101.0, 200),
    ],
)
def test_nice_integer_step(min_step, expected):
    """Integer helper should round up to stable human-friendly steps."""
    assert nice_integer_step(min_step) == expected


@pytest.mark.parametrize(
    ("min_value", "max_value", "expected"),
    [
        (0.0, 0.0, (0, 2)),
        (2.0, 10.0, (0, 11)),
        (-10.0, 3.0, (-11, 0)),
        (-2.0, 8.0, (0, 9)),
    ],
)
def test_axis_limits(min_value, max_value, expected):
    """Axis limits should preserve dominant direction and padding."""
    assert _axis_limits(min_value, max_value) == expected


def test_axis_tick_steps_generates_major_and_minor_ticks():
    """Axis tick helper should generate stable major/minor intervals."""
    major_step, minor_step = axis_tick_steps(
        start=0,
        end=20,
        unit_screen_px=20.0,
    )

    assert major_step == 2
    assert minor_step is None


@pytest.mark.parametrize(
    (
        "start",
        "end",
        "unit_screen_px",
        "max_ticks",
        "expected_major",
        "expected_minor",
    ),
        [
            (0, 0, 20.0, 20, 2, None),
            (0, 100, 100.0, 20, 10, None),
            (0, 100, 5.0, 20, 10, None),
            (0, 1000, 0.01, 20, 5000, 2500),
            (-50, 50, 30.0, 20, 10, None),
        ],
)
def test_axis_tick_steps_handles_density_and_span_edge_cases(
    start,
    end,
    unit_screen_px,
    max_ticks,
    expected_major,
    expected_minor,
):
    """Axis tick math should remain deterministic across edge-case spans."""
    major_step, minor_step = axis_tick_steps(
        start=start,
        end=end,
        unit_screen_px=unit_screen_px,
        max_ticks=max_ticks,
    )

    assert major_step == expected_major
    assert minor_step == expected_minor


@pytest.mark.parametrize(
    ("span", "expected"),
    [
        (0.0, 0.1),
        (1.0, 0.1),
        (9.0, 1.0),
        (10.0, 1.0),
        (11.0, 2.0),
        (49.0, 5.0),
        (50.0, 5.0),
        (51.0, 10.0),
        (499.0, 50.0),
        (500.0, 50.0),
        (501.0, 100.0),
    ],
)
def test_normalized_spacing_step_preserves_stable_progression(span, expected):
    """Spacing progression should remain deterministic across span changes."""
    assert normalized_spacing_step(span) == expected


@pytest.mark.skipif(
    not os.environ.get("DISPLAY") and not os.environ.get("QT_QPA_PLATFORM"),
    reason="No display available",
)
def test_ctrl_drag_adds_multiple_lines(qtbot):
    """Ctrl-drag should continuously add lines to semantic selection."""
    panel = EditorPanel()
    qtbot.addWidget(panel)

    panel.load_content(
        "G0 X0\n"
        "G1 X1\n"
        "G1 X2\n"
        "G1 X3\n"
        "M30\n",
    )

    editor = panel._text_edit
    viewport = editor.viewport()

    start_cursor = editor.textCursor()
    start_cursor.movePosition(start_cursor.MoveOperation.Start)
    editor.setTextCursor(start_cursor)

    start_rect = editor.cursorRect(start_cursor)

    target_cursor = editor.textCursor()
    target_cursor.movePosition(target_cursor.MoveOperation.Down)
    target_cursor.movePosition(target_cursor.MoveOperation.Down)
    target_rect = editor.cursorRect(target_cursor)

    assert viewport is not None

    qtbot.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ControlModifier,
        pos=start_rect.center(),
    )

    qtbot.mouseMove(
        viewport,
        pos=QPoint(
            target_rect.center().x(),
            target_rect.center().y(),
        ),
    )

    qtbot.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ControlModifier,
        pos=target_rect.center(),
    )

    assert panel.selection_model().selected_lines() == [1, 2, 3]


@pytest.mark.skipif(
    not os.environ.get("DISPLAY") and not os.environ.get("QT_QPA_PLATFORM"),
    reason="No display available",
)
def test_ctrl_drag_removes_multiple_lines(qtbot):
    """Ctrl-drag should continuously remove selected lines."""
    panel = EditorPanel()
    qtbot.addWidget(panel)

    panel.load_content(
        "G0 X0\n"
        "G1 X1\n"
        "G1 X2\n"
        "G1 X3\n"
        "M30\n",
    )

    panel.highlight_lines([1, 2, 3, 4])

    editor = panel._text_edit
    viewport = editor.viewport()

    start_cursor = editor.textCursor()
    start_cursor.movePosition(start_cursor.MoveOperation.Start)
    editor.setTextCursor(start_cursor)

    start_rect = editor.cursorRect(start_cursor)

    target_cursor = editor.textCursor()
    target_cursor.movePosition(target_cursor.MoveOperation.Down)
    target_cursor.movePosition(target_cursor.MoveOperation.Down)
    target_rect = editor.cursorRect(target_cursor)

    assert viewport is not None

    qtbot.mousePress(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ControlModifier,
        pos=start_rect.center(),
    )

    qtbot.mouseMove(
        viewport,
        pos=QPoint(
            target_rect.center().x(),
            target_rect.center().y(),
        ),
    )

    qtbot.mouseRelease(
        viewport,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ControlModifier,
        pos=target_rect.center(),
    )

    assert panel.selection_model().selected_lines() == [4]


def test_main_opens_startup_file(monkeypatch):
    """main() should forward the first CLI file argument to the main window."""
    opened_paths: list[str] = []
    shown = False

    class FakeApplication:
        def __init__(self, argv):
            self.argv = argv

        def setApplicationName(self, _name):
            pass

        def setApplicationVersion(self, _version):
            pass

        def setWindowIcon(self, _icon):
            pass

        def exec(self):
            return 0

    class FakeWindow:
        def setWindowIcon(self, _icon):
            pass

        def _open_file_path(self, path):
            opened_paths.append(path)

        def show(self):
            nonlocal shown
            shown = True

    from src import main as app_main

    monkeypatch.setattr(app_main, "QApplication", FakeApplication)
    monkeypatch.setattr(app_main, "MainWindow", FakeWindow)
    monkeypatch.setattr(app_main, "QIcon", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(Path, "exists", lambda _self: False)
    monkeypatch.setattr(sys, "argv", ["gcode-lisa", "/tmp/example.gcode"])

    with pytest.raises(SystemExit) as exc_info:
        app_main.main()

    assert exc_info.value.code == 0
    assert opened_paths == ["/tmp/example.gcode"]
    assert shown is True
