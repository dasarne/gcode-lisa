"""Tests for src.ui modules (import-only; no display required)."""

import os
import sys
import pytest


@pytest.mark.skipif(
    not os.environ.get("DISPLAY") and not os.environ.get("QT_QPA_PLATFORM"),
    reason="No display available",
)
def test_main_window_import():
    """MainWindow should be importable."""
    from src.ui.main_window import MainWindow  # noqa: F401


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
    monkeypatch.setattr(app_main.Path, "exists", lambda _self: False)
    monkeypatch.setattr(sys, "argv", ["gcode-lisa", "/tmp/example.gcode"])

    with pytest.raises(SystemExit) as exc_info:
        app_main.main()

    assert exc_info.value.code == 0
    assert opened_paths == ["/tmp/example.gcode"]
    assert shown is True
