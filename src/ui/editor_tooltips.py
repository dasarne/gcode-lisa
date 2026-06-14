"""Tooltip helpers for the G-Code editor panel."""

from __future__ import annotations

import re

from ..analyzer.analyzer import AnalysisWarning, WarningSeverity
from ..gcode.commands import EXTENDED_COMMAND_DESCRIPTIONS
from ..gcode.dialects import get_profile

_CMD_TOKEN_RE = re.compile(r"\b([GMT]\d+(?:\.\d+)?)\b", re.IGNORECASE)
_PARAM_TOKEN_RE = re.compile(r"\b([A-Z])([-+]?\d*\.?\d+)\b", re.IGNORECASE)
_PAREN_COMMENT_RE = re.compile(r"\([^)]*\)")

_PARAM_EXPLANATIONS_DE: dict[str, str] = {
    "X": "X-Koordinate",
    "Y": "Y-Koordinate",
    "Z": "Z-Koordinate",
    "A": "A-Achse (Mehrachsensystem)",
    "B": "B-Achse (Mehrachsensystem)",
    "C": "C-Achse (Mehrachsensystem)",
    "I": "Relativer Kreismittelpunkt I (X-Anteil)",
    "J": "Relativer Kreismittelpunkt J (Y-Anteil)",
    "F": "Vorschub",
}

_PARAM_EXPLANATIONS_EN: dict[str, str] = {
    "X": "X coordinate",
    "Y": "Y coordinate",
    "Z": "Z coordinate",
    "A": "A axis (multi-axis system)",
    "B": "B axis (multi-axis system)",
    "C": "C axis (multi-axis system)",
    "I": "Arc centre offset I (X component)",
    "J": "Arc centre offset J (Y component)",
    "F": "Feed rate",
}


def describe_token_at(
    line_text: str,
    column: int,
    *,
    language: str,
    profile_id: str | None,
) -> str | None:
    """Return a short explanation for the token located at the given column."""
    if not line_text:
        return None

    de = language != "en"

    semicolon_idx = line_text.find(";")
    if semicolon_idx >= 0 and column >= semicolon_idx:
        comment = line_text[semicolon_idx + 1:].strip()
        comment_text = comment if comment else ("(leer)" if de else "(empty)")
        label = "Kommentar" if de else "Comment"
        return f"{label}: {comment_text}"

    for match in _PAREN_COMMENT_RE.finditer(line_text):
        start, end = match.span()
        if start <= column < end:
            comment = match.group(0)[1:-1].strip()
            comment_text = comment if comment else ("(leer)" if de else "(empty)")
            label = "Kommentar" if de else "Comment"
            return f"{label}: {comment_text}"

    for match in _CMD_TOKEN_RE.finditer(line_text):
        start, end = match.span(1)
        if start <= column < end:
            command = match.group(1).upper()
            description = EXTENDED_COMMAND_DESCRIPTIONS.get(command)
            cmd_label = "Befehl" if de else "Command"
            parts: list[str] = []

            if description:
                parts.append(f"{cmd_label} {command}: {description}")
            else:
                parts.append(f"{cmd_label} {command}")

            if profile_id is not None:
                try:
                    profile = get_profile(profile_id)
                    if command in profile.unsupported_commands:
                        hint = (
                            f"⚠ Nicht unterstützt durch {profile.name}"
                            if de
                            else f"⚠ Not supported by {profile.name}"
                        )
                        parts.append(hint)
                    elif command not in profile.known_commands:
                        hint = (
                            f"⚠ Unbekannt für Dialekt {profile.name}"
                            if de
                            else f"⚠ Unknown for dialect {profile.name}"
                        )
                        parts.append(hint)
                except ValueError:
                    pass

            return "\n".join(parts)

    for match in _PARAM_TOKEN_RE.finditer(line_text):
        start, end = match.span(0)
        if start <= column < end:
            key = match.group(1).upper()
            raw_value = match.group(2)
            return format_parameter_tooltip(key, raw_value, language=language)

    return None


def format_parameter_tooltip(
    key: str,
    raw_value: str,
    *,
    language: str,
) -> str:
    """Format tooltip text for a parameter token."""
    de = language != "en"
    explanations = _PARAM_EXPLANATIONS_DE if de else _PARAM_EXPLANATIONS_EN
    description = explanations.get(
        key,
        f"{key}-Parameter" if de else f"{key} parameter",
    )

    try:
        value = float(raw_value)
    except ValueError:
        value_text = raw_value
    else:
        if key == "F":
            value_text = f"{value:.2f} " + (
                "Einheit/min" if de else "units/min"
            )
        elif key in {"X", "Y", "Z", "I", "J", "A", "B", "C"}:
            value_text = f"{value:.3f}"
        else:
            value_text = f"{value:g}"

    return f"{description}: {value_text}"


def describe_line_warnings(
    line_number: int,
    line_warnings: dict[int, list[AnalysisWarning]],
    *,
    language: str,
) -> str | None:
    """Return analyzer warning/error context for a given line, if available."""
    warnings = line_warnings.get(line_number)
    if not warnings:
        return None

    de = language != "en"
    header = "Analysehinweise:" if de else "Analysis notes:"
    parts: list[str] = [header]

    for warning in warnings[:3]:
        parts.append(f"- {warning.severity.name}: {warning.message}")

        if warning.severity == WarningSeverity.ERROR:
            reason_label = "Grund" if de else "Reason"
            parts.append(f"  {reason_label}: {warning.message}")

        if warning.suggestion:
            suggestion_label = "Vorschlag" if de else "Suggestion"
            parts.append(
                f"  {suggestion_label}: {warning.suggestion}"
            )

    if len(warnings) > 3:
        more = len(warnings) - 3
        parts.append(
            f"- ... {more} weitere Hinweise"
            if de
            else f"- ... {more} more notes"
        )

    return "\n".join(parts)