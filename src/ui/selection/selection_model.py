"""Shared semantic selection model.

The model is intentionally independent from Qt and QTextCursor.

It acts as the authoritative semantic selection state shared between
editor and canvas.

Transition status:
- QTextCursor is still used for native editor interaction and rendering.
- QTextCursor selections are currently projected from SelectionModel.
- Some editor workflows still temporarily inspect cursor selections.
- Undo/redo integration is not complete yet, but snapshots are serializable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .selection_types import LineRange, SelectionSnapshot


@dataclass(slots=True)
class SelectionModel:
    """Semantic multi-range selection state."""

    ranges: list[LineRange] = field(default_factory=list)
    primary_index: int | None = None

    def clear(self) -> None:
        self.ranges.clear()
        self.primary_index = None

    @property
    def is_empty(self) -> bool:
        return not self.ranges

    @property
    def primary_range(self) -> LineRange | None:
        if self.primary_index is None:
            return None

        if self.primary_index >= len(self.ranges):
            return None

        return self.ranges[self.primary_index]

    def set_single_line(self, line_number: int) -> None:
        self.set_ranges([LineRange(line_number, line_number)])

    def set_range(self, start_line: int, end_line: int) -> None:
        self.set_ranges([LineRange(start_line, end_line)])

    def set_ranges(
        self,
        ranges: list[LineRange],
        primary_index: int | None = 0,
    ) -> None:
        normalized = self._normalize_ranges(ranges)

        self.ranges = normalized

        if not normalized:
            self.primary_index = None
            return

        if primary_index is None:
            self.primary_index = 0
            return

        self.primary_index = max(
            0,
            min(primary_index, len(normalized) - 1),
        )

    def add_range(
        self,
        line_range: LineRange,
        make_primary: bool = True,
    ) -> None:
        """Add a semantic range to the selection."""
        updated = list(self.ranges)
        updated.append(line_range)

        self.ranges = self._normalize_ranges(updated)

        if not self.ranges:
            self.primary_index = None
            return

        if make_primary:
            self.primary_index = self.ranges.index(
                self._find_covering_range(line_range),
            )

    def toggle_range(
        self,
        line_range: LineRange,
        make_primary: bool = True,
    ) -> None:
        """Toggle a semantic range on or off."""
        updated: list[LineRange] = []

        removed = False

        for existing in self.ranges:
            if existing == line_range:
                removed = True
                continue

            updated.append(existing)

        if not removed:
            updated.append(line_range)

        self.set_ranges(updated)

        if (
            not removed
            and make_primary
            and self.ranges
        ):
            covering = self._find_covering_range(line_range)
            self.primary_index = self.ranges.index(covering)

    def extend_primary_to_line(
        self,
        line_number: int,
    ) -> None:
        """Extend the primary range to include the target line."""
        primary = self.primary_range

        if primary is None:
            self.set_single_line(line_number)
            return

        updated = LineRange(
            min(primary.start_line, line_number),
            max(primary.end_line, line_number),
        )

        ranges = list(self.ranges)

        if self.primary_index is None:
            ranges.append(updated)
        else:
            ranges[self.primary_index] = updated

        self.set_ranges(
            ranges,
            self.primary_index,
        )

    def contains(self, line_number: int) -> bool:
        return any(
            line_range.contains(line_number)
            for line_range in self.ranges
        )

    def toggle_line(
        self,
        line_number: int,
        make_primary: bool = True,
    ) -> None:
        """Toggle a single semantic line on/off.

        Behavior:
        - Non-selected line:
            inserted into an existing adjacent range or becomes a new range.
        - Interior line:
            splits the containing range into two ranges.
        - Edge line:
            shrinks the containing range.
        - Single-line range:
            removes the range entirely.
        """
        if line_number <= 0:
            return

        updated: list[LineRange] = []

        removed = False
        inserted = False

        for existing in self.ranges:
            if not existing.contains(line_number):
                updated.append(existing)
                continue

            removed = True

            if (
                existing.start_line == line_number
                and existing.end_line == line_number
            ):
                continue

            if line_number == existing.start_line:
                updated.append(
                    LineRange(
                        existing.start_line + 1,
                        existing.end_line,
                    ),
                )
                continue

            if line_number == existing.end_line:
                updated.append(
                    LineRange(
                        existing.start_line,
                        existing.end_line - 1,
                    ),
                )
                continue

            updated.append(
                LineRange(
                    existing.start_line,
                    line_number - 1,
                ),
            )
            updated.append(
                LineRange(
                    line_number + 1,
                    existing.end_line,
                ),
            )

        if not removed:
            updated.append(LineRange(line_number, line_number))
            inserted = True

        self.set_ranges(updated)

        if (
            inserted
            and make_primary
            and self.ranges
        ):
            covering = self._find_covering_range(
                LineRange(line_number, line_number),
            )
            self.primary_index = self.ranges.index(covering)

    def selected_lines(self) -> list[int]:
        lines: set[int] = set()

        for line_range in self.ranges:
            lines.update(line_range.iter_lines())

        return sorted(lines)

    def to_snapshot(self) -> SelectionSnapshot:
        return {
            "ranges": [
                line_range.to_dict()
                for line_range in self.ranges
            ],
            "primary_index": self.primary_index,
        }

    @classmethod
    def from_snapshot(
        cls,
        snapshot: SelectionSnapshot,
    ) -> "SelectionModel":
        raw_ranges_value = snapshot.get("ranges", [])

        if not isinstance(raw_ranges_value, list):
            raw_ranges: list[object] = []
        else:
            raw_ranges = raw_ranges_value

        ranges: list[LineRange] = []

        for raw_range in raw_ranges:
            if not isinstance(raw_range, dict):
                continue

            start_line = raw_range.get("start_line")
            end_line = raw_range.get("end_line")

            if not isinstance(start_line, int):
                continue

            if not isinstance(end_line, int):
                continue

            ranges.append(
                LineRange(
                    start_line,
                    end_line,
                ),
            )

        raw_primary_index = snapshot.get("primary_index")

        primary_index = (
            raw_primary_index
            if isinstance(raw_primary_index, int)
            else None
        )

        model = cls()
        model.set_ranges(
            ranges,
            primary_index,
        )
        return model

    def _find_covering_range(
        self,
        line_range: LineRange,
    ) -> LineRange:
        for candidate in self.ranges:
            if (
                candidate.start_line <= line_range.start_line
                and candidate.end_line >= line_range.end_line
            ):
                return candidate

        return line_range

    @staticmethod
    def _normalize_ranges(
        ranges: list[LineRange],
    ) -> list[LineRange]:
        if not ranges:
            return []

        ordered = sorted(ranges)

        merged: list[LineRange] = [ordered[0]]

        for current in ordered[1:]:
            previous = merged[-1]

            overlaps = current.start_line <= (previous.end_line + 1)

            if overlaps:
                merged[-1] = LineRange(
                    previous.start_line,
                    max(previous.end_line, current.end_line),
                )
                continue

            merged.append(current)

        return merged