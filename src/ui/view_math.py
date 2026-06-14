"""Pure viewport and axis math helpers for canvas rendering.

This module intentionally contains only deterministic numeric helpers with:
- no Qt imports
- no QWidget coupling
- no rendering ownership
- no mutable viewport state

The functions here are safe to test independently from the rendering pipeline
and are intended to support conservative extraction boundaries only.
"""

from __future__ import annotations

import math


def nice_integer_step(min_step: float) -> int:
    """Return a human-friendly integer step >= min_step."""
    if min_step <= 1.0:
        return 1

    magnitude = 10 ** math.floor(math.log10(min_step))
    for factor in (1, 2, 5, 10):
        step = factor * magnitude
        if step >= min_step:
            return int(step)
    return int(10 * magnitude)


def normalized_spacing_step(
    span: float,
    target_divisions: float = 10.0,
) -> float:
    """Return a stable 1/2/5×10ⁿ spacing step for a numeric span.

    This helper intentionally contains only deterministic spacing progression
    math. It does not define:
    - viewport meaning
    - grid ownership
    - overlay semantics
    - floor-plane interpretation

    Callers remain responsible for deciding how spacing is applied.
    """
    normalized_span = max(span, 1.0)
    raw_step = normalized_span / max(target_divisions, 1.0)
    magnitude = 10 ** math.floor(math.log10(raw_step))

    for factor in (1, 2, 5, 10):
        step = factor * magnitude
        if raw_step <= step:
            return step

    return 10 * magnitude


def axis_tick_steps(
    start: int,
    end: int,
    unit_screen_px: float,
    max_ticks: int = 20,
) -> tuple[int, int | None]:
    """Return stable integer major/minor tick steps for a viewport axis.

    The helper is intentionally projection-agnostic and operates purely on:
    - integer axis bounds
    - visible span
    - screen-space density constraints

    No viewport ownership, rendering state, or Qt types are involved.
    """
    span = max(end - start, 1)
    min_major_step = max(1, math.ceil(28.0 / max(unit_screen_px, 1e-6)))
    major_step = max(
        nice_integer_step(span / max(max_ticks / 2, 1)),
        nice_integer_step(min_major_step),
    )

    minor_step: int | None = None
    for divisor in (5, 2):
        if major_step % divisor != 0:
            continue

        candidate = major_step // divisor
        if candidate < 1:
            continue

        if candidate * unit_screen_px < 12.0:
            continue

        tick_count = span / candidate + 1
        if tick_count <= max_ticks:
            minor_step = candidate
            break

    return major_step, minor_step