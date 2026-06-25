"""Unit tests for pure search/replace helpers used by EditorPanel."""

from src.ui.editor.editor_search import (
    semantic_ranges_to_text_ranges,
)
from src.ui.search_service import (
    compute_match_ranges,
    deserialize_multi_range_text,
    find_next_match,
    find_previous_match,
    replace_all_in_ranges,
    serialize_multi_range_text,
)
from src.ui.selection.selection_model import SelectionModel
from src.ui.selection.selection_types import LineRange


def test_compute_match_ranges_literal_multiple_ranges() -> None:
    content = "A F100\nB F200\nC F300\n"
    ranges = [(0, 7), (7, len(content))]

    matches = compute_match_ranges("F", use_regex=False, content=content, ranges=ranges)

    assert matches == [(2, 3), (9, 10), (16, 17)]


def test_compute_match_ranges_regex() -> None:
    content = "F100\nF250\nG1\n"
    ranges = [(0, len(content))]

    matches = compute_match_ranges(r"F\d+", use_regex=True, content=content, ranges=ranges)

    assert matches == [(0, 4), (5, 9)]


def test_compute_match_ranges_invalid_regex_returns_empty() -> None:
    matches = compute_match_ranges("(", use_regex=True, content="abc", ranges=[(0, 3)])

    assert matches == []


def test_compute_match_ranges_case_insensitive_default() -> None:
    content = "G0 X10\ng1 Y20\n"
    ranges = [(0, len(content))]

    # Default: case_sensitive=False – should match both "G0" and "g0"
    matches = compute_match_ranges("g0", use_regex=False, content=content, ranges=ranges, case_sensitive=False)
    assert len(matches) == 1

    # With case_sensitive=True – "g0" does NOT match "G0"
    matches_cs = compute_match_ranges("g0", use_regex=False, content=content, ranges=ranges, case_sensitive=True)
    assert matches_cs == []


def test_compute_match_ranges_case_sensitive() -> None:
    content = "G1 g1\n"
    ranges = [(0, len(content))]

    matches = compute_match_ranges("G1", use_regex=False, content=content, ranges=ranges, case_sensitive=True)
    assert matches == [(0, 2)]


def test_find_next_previous_match_wraparound() -> None:
    matches = [(10, 12), (20, 22), (30, 32)]

    assert find_next_match(matches, anchor=21) == (30, 32)
    assert find_next_match(matches, anchor=40) == (10, 12)
    assert find_previous_match(matches, anchor=21) == (10, 12)
    assert find_previous_match(matches, anchor=5) == (30, 32)


def test_replace_all_in_ranges_literal() -> None:
    content = "X10 F100\nX20 F200\n"
    new_content, count = replace_all_in_ranges(
        content,
        ranges=[(0, len(content))],
        needle="F",
        replacement="S",
        use_regex=False,
    )

    assert count == 2
    assert new_content == "X10 S100\nX20 S200\n"


def test_replace_all_in_ranges_case_insensitive_literal() -> None:
    content = "F100\nf200\n"
    new_content, count = replace_all_in_ranges(
        content,
        ranges=[(0, len(content))],
        needle="f",
        replacement="S",
        use_regex=False,
        case_sensitive=False,
    )

    assert count == 2
    assert new_content == "S100\nS200\n"


def test_replace_all_in_ranges_case_sensitive_literal() -> None:
    content = "F100\nf200\n"
    new_content, count = replace_all_in_ranges(
        content,
        ranges=[(0, len(content))],
        needle="f",
        replacement="S",
        use_regex=False,
        case_sensitive=True,
    )

    assert count == 1
    assert new_content == "F100\nS200\n"


def test_replace_all_in_ranges_regex_error_no_change() -> None:
    content = "F100\n"
    new_content, count = replace_all_in_ranges(
        content,
        ranges=[(0, len(content))],
        needle="(",
        replacement="X",
        use_regex=True,
    )

    assert count == 0
    assert new_content == content


def test_selection_model_multi_range_normalization() -> None:
    model = SelectionModel()

    model.set_ranges(
        [
            LineRange(10, 12),
            LineRange(1, 3),
            LineRange(4, 5),
            LineRange(20, 22),
        ],
    )

    assert model.ranges == [
        LineRange(1, 5),
        LineRange(10, 12),
        LineRange(20, 22),
    ]
    assert model.selected_lines() == [
        1,
        2,
        3,
        4,
        5,
        10,
        11,
        12,
        20,
        21,
        22,
    ]


def test_selection_model_snapshot_roundtrip() -> None:
    model = SelectionModel()

    model.set_ranges(
        [
            LineRange(2, 4),
            LineRange(8, 9),
        ],
        primary_index=1,
    )

    restored = SelectionModel.from_snapshot(
        model.to_snapshot(),
    )

    assert restored.ranges == [
        LineRange(2, 4),
        LineRange(8, 9),
    ]
    assert restored.primary_index == 1
    assert restored.primary_range == LineRange(8, 9)


def test_selection_model_toggle_range() -> None:
    model = SelectionModel()

    model.toggle_range(LineRange(2, 2))

    assert model.ranges == [
        LineRange(2, 2),
    ]

    model.toggle_range(LineRange(2, 2))

    assert model.ranges == []
    assert model.primary_index is None


def test_selection_model_toggle_line_adds_new_range() -> None:
    model = SelectionModel()

    model.toggle_line(10)

    assert model.ranges == [
        LineRange(10, 10),
    ]
    assert model.primary_range == LineRange(10, 10)


def test_selection_model_toggle_line_removes_single_line() -> None:
    model = SelectionModel()

    model.set_ranges(
        [
            LineRange(10, 10),
        ],
    )

    model.toggle_line(10)

    assert model.ranges == []
    assert model.primary_index is None


def test_selection_model_toggle_line_shrinks_range_start() -> None:
    model = SelectionModel()

    model.set_ranges(
        [
            LineRange(10, 20),
        ],
    )

    model.toggle_line(10)

    assert model.ranges == [
        LineRange(11, 20),
    ]


def test_selection_model_toggle_line_shrinks_range_end() -> None:
    model = SelectionModel()

    model.set_ranges(
        [
            LineRange(10, 20),
        ],
    )

    model.toggle_line(20)

    assert model.ranges == [
        LineRange(10, 19),
    ]


def test_selection_model_toggle_line_splits_range() -> None:
    model = SelectionModel()

    model.set_ranges(
        [
            LineRange(10, 20),
        ],
    )

    model.toggle_line(15)

    assert model.ranges == [
        LineRange(10, 14),
        LineRange(16, 20),
    ]


def test_selection_model_toggle_line_merges_adjacent_ranges() -> None:
    model = SelectionModel()

    model.set_ranges(
        [
            LineRange(10, 14),
            LineRange(16, 20),
        ],
    )

    model.toggle_line(15)

    assert model.ranges == [
        LineRange(10, 20),
    ]


def test_selection_model_extend_primary_range() -> None:
    model = SelectionModel()

    model.set_ranges(
        [
            LineRange(5, 5),
            LineRange(20, 22),
        ],
        primary_index=0,
    )

    model.extend_primary_to_line(10)

    assert model.ranges == [
        LineRange(5, 10),
        LineRange(20, 22),
    ]

    assert model.primary_range == LineRange(5, 10)


def test_multi_range_clipboard_roundtrip() -> None:
    serialized = serialize_multi_range_text(
        [
            "N10 G0 X0",
            "N20 G1 X10",
            "N30 M30",
        ],
    )

    restored = deserialize_multi_range_text(serialized)

    assert restored == [
        "N10 G0 X0",
        "N20 G1 X10",
        "N30 M30",
    ]


def test_replace_all_in_ranges_stable_offset_updates() -> None:
    content = "AA test\nBB test\n"

    new_content, count = replace_all_in_ranges(
        content,
        ranges=[
            (0, 8),
            (8, len(content)),
        ],
        needle="test",
        replacement="LONGER_VALUE",
        use_regex=False,
    )

    assert count == 2
    assert new_content == (
        "AA LONGER_VALUE\n"
        "BB LONGER_VALUE\n"
    )


def test_semantic_ranges_to_text_ranges() -> None:
    content = (
        "N10 F100\n"
        "N20 F200\n"
        "N30 F300\n"
        "N40 F400\n"
    )

    ranges = semantic_ranges_to_text_ranges(
        content,
        [
            LineRange(2, 3),
        ],
    )

    assert ranges == [
        (9, 27),
    ]


def test_replace_all_in_selected_ranges_preparation() -> None:
    content = (
        "N10 F100\n"
        "N20 F200\n"
        "N30 F300\n"
        "N40 F400\n"
    )

    selection = SelectionModel()
    selection.set_ranges(
        [
            LineRange(2, 3),
        ],
    )

    lines = content.splitlines(keepends=True)

    offset = 0
    ranges: list[tuple[int, int]] = []

    for index, line in enumerate(lines, start=1):
        start = offset
        end = offset + len(line)

        if selection.contains(index):
            ranges.append((start, end))

        offset = end

    new_content, count = replace_all_in_ranges(
        content,
        ranges=ranges,
        needle="F",
        replacement="S",
        use_regex=False,
    )

    assert count == 2
    assert new_content == (
        "N10 F100\n"
        "N20 S200\n"
        "N30 S300\n"
        "N40 F400\n"
    )
