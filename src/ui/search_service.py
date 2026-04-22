"""Pure search/replace helpers for editor text operations."""

from __future__ import annotations

import re

TextRange = tuple[int, int]


def compute_match_ranges(
    term: str,
    use_regex: bool,
    content: str,
    ranges: list[TextRange],
) -> list[TextRange]:
    """Return all match ranges within the given text ranges."""
    if not term:
        return []

    results: list[TextRange] = []

    if use_regex:
        try:
            pattern = re.compile(term, re.MULTILINE)
        except re.error:
            return []

        for start_bound, end_bound in ranges:
            target = content[start_bound:end_bound]
            for match in pattern.finditer(target):
                results.append((start_bound + match.start(), start_bound + match.end()))
        return results

    for start_bound, end_bound in ranges:
        target = content[start_bound:end_bound]
        start = 0
        while True:
            index = target.find(term, start)
            if index == -1:
                break
            begin = start_bound + index
            end = begin + len(term)
            results.append((begin, end))
            start = index + len(term)

    return results


def find_next_match(matches: list[TextRange], anchor: int) -> TextRange | None:
    """Return the next match at/after anchor, wrapping around."""
    if not matches:
        return None
    for start, end in matches:
        if start >= anchor:
            return (start, end)
    return matches[0]


def find_previous_match(matches: list[TextRange], anchor: int) -> TextRange | None:
    """Return the previous match before anchor, wrapping around."""
    if not matches:
        return None
    for start, end in reversed(matches):
        if end <= anchor:
            return (start, end)
    return matches[-1]


def replace_all_in_ranges(
    content: str,
    ranges: list[TextRange],
    needle: str,
    replacement: str,
    use_regex: bool,
) -> tuple[str, int]:
    """Replace all matches within ranges and return (new_content, count)."""
    if not needle:
        return (content, 0)

    try:
        new_content = content
        count = 0

        for start_bound, end_bound in reversed(ranges):
            target = new_content[start_bound:end_bound]
            if use_regex:
                new_target, local_count = re.subn(
                    needle,
                    replacement,
                    target,
                    flags=re.MULTILINE,
                )
            else:
                local_count = target.count(needle)
                new_target = target.replace(needle, replacement)

            if local_count == 0:
                continue

            count += local_count
            new_content = (
                new_content[:start_bound]
                + new_target
                + new_content[end_bound:]
            )

        return (new_content, count)
    except re.error:
        return (content, 0)
