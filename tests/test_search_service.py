"""Unit tests for pure search/replace helpers used by EditorPanel."""

from src.ui.search_service import (
    compute_match_ranges,
    find_next_match,
    find_previous_match,
    replace_all_in_ranges,
)


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
