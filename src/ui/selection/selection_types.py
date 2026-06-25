"""Qt-independent semantic selection domain types.

This module intentionally contains no Qt dependencies.

The selection model represents semantic line selections shared between
editor and canvas. QTextCursor selections still exist during the migration,
but they are projections of this state instead of the authoritative source.

Current transition notes:
- QTextCursor selections still coexist with SelectionModel state.
- Search match highlighting still uses QTextCursor ranges internally.
- Some editor operations still derive transient state from the active cursor.
- Canvas highlighting and editor overlays can now share the same semantic
  line-range model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class LineRange:
    """Inclusive semantic line range using 1-based editor lines."""

    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        if self.start_line <= 0:
            raise ValueError("start_line must be > 0")

        if self.end_line <= 0:
            raise ValueError("end_line must be > 0")

        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")

    @property
    def is_single_line(self) -> bool:
        return self.start_line == self.end_line

    def iter_lines(self) -> range:
        return range(self.start_line, self.end_line + 1)

    def contains(self, line_number: int) -> bool:
        return self.start_line <= line_number <= self.end_line

    def to_dict(self) -> dict[str, int]:
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
        }

    @classmethod
    def from_lines(cls, line_numbers: list[int]) -> "LineRange":
        valid = sorted({line for line in line_numbers if line > 0})

        if not valid:
            raise ValueError("line_numbers must not be empty")

        return cls(valid[0], valid[-1])


SelectionSnapshot = dict[str, object]