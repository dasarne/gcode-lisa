"""Regression tests for initial non-GRBL dialect profile support."""

from src.gcode.parser import GCodeParser
from src.analyzer.analyzer import GCodeAnalyzer, WarningSeverity


def test_parser_validate_program_accepts_linuxcnc_basics():
    parser = GCodeParser("linuxcnc")
    program = parser.parse_text("G54\nG43 H1\nM6 T1\n")
    warnings = parser.validate_program(program)
    assert warnings == []


def test_parser_validate_program_accepts_marlin_basics():
    parser = GCodeParser("marlin")
    program = parser.parse_text("M104 S210\nM109 S210\nG28\n")
    warnings = parser.validate_program(program)
    assert warnings == []


def test_analyzer_unknown_command_message_uses_selected_profile_name():
    parser = GCodeParser("linuxcnc")
    program = parser.parse_text("G81 X1 Y1 Z-1\n")
    analyzer = GCodeAnalyzer("linuxcnc")
    warnings = analyzer.analyze(program)
    errors = [w for w in warnings if w.severity == WarningSeverity.ERROR]
    assert errors
    assert "LinuxCNC" in errors[0].message
