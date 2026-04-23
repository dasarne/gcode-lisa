"""G-Code analysis: version compatibility, warnings, and checks."""

from dataclasses import dataclass
from enum import Enum, auto

from ..gcode.commands import ALL_COMMANDS
from ..gcode.dialects import get_profile

# G-code commands that require a positive feedrate (non-rapid feed moves).
_FEED_MOVE_COMMANDS = frozenset({"G1", "G2", "G3"})


class WarningSeverity(Enum):
    """Severity level for an analysis warning."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()


@dataclass
class AnalysisWarning:
    """A single warning produced by the analyzer."""

    severity: WarningSeverity
    message: str
    line_number: int | None = None
    suggestion: str | None = None


class GCodeAnalyzer:
    """Analyzes a GCodeProgram and produces a list of warnings."""

    def __init__(self, version_id: str = "1.1H") -> None:
        self.version_id = version_id

    def analyze(self, program) -> list[AnalysisWarning]:
        """Run all checks and return the combined warning list."""
        warnings: list[AnalysisWarning] = []
        warnings.extend(self._check_version_compatibility(program))
        warnings.extend(self._check_feed_rates(program))
        warnings.extend(self._check_missing_origin(program))
        warnings.extend(self._check_workpiece_geometry(program))
        return warnings

    def _check_version_compatibility(self, program) -> list[AnalysisWarning]:
        """Check for commands unsupported by the selected GRBL version.

        Produces an ERROR for commands that GRBL does not know at all
        (e.g. G81), and a WARNING for commands that exist in GRBL but are
        disabled in the currently selected firmware variant (e.g. G38.2 on
        GRBL 1.1H).
        """
        warnings: list[AnalysisWarning] = []
        profile = get_profile(self.version_id)
        known_commands = ALL_COMMANDS if profile.family == "grbl" else profile.known_commands

        for gcode_line in program.lines:
            cmd = gcode_line.command
            if cmd is None:
                continue

            if cmd not in known_commands:
                if profile.family == "grbl":
                    message = f"{cmd} is not supported by GRBL"
                    suggestion = "Remove or replace with a GRBL-compatible command."
                else:
                    message = f"{cmd} is not recognised for {profile.name}"
                    suggestion = f"Remove or replace with a {profile.name}-compatible command."
                warnings.append(AnalysisWarning(
                    severity=WarningSeverity.ERROR,
                    message=message,
                    line_number=gcode_line.line_number,
                    suggestion=suggestion,
                ))
            elif cmd in profile.unsupported_commands:
                if profile.family == "grbl":
                    message = f"{cmd} is not supported by GRBL {self.version_id}"
                    suggestion = "Use GRBL 1.1j for full command support."
                else:  # pragma: no cover – all non-GRBL profiles have empty unsupported_commands
                    message = f"{cmd} is not supported by {profile.name}"
                    suggestion = "Use a profile that supports this command."
                warnings.append(AnalysisWarning(
                    severity=WarningSeverity.WARNING,
                    message=message,
                    line_number=gcode_line.line_number,
                    suggestion=suggestion,
                ))

        return warnings

    def _check_missing_origin(self, program) -> list[AnalysisWarning]:
        """Warn if no explicit work-coordinate origin is established.

        An origin is considered established when the program contains any of:

        * A ``G92`` (Set coordinate offset) command.
        * A ``G0`` or ``G1`` move that explicitly names both ``X0`` and ``Y0``
          (i.e. a homing move to the work origin before cutting).

        If neither pattern is found and the program has at least one motion
        command, an INFO hint is emitted reminding the operator to zero the
        machine before running.
        """
        has_motion = False
        for line in program.lines:
            cmd = line.command
            if cmd is None:
                continue

            # G92 explicitly sets a coordinate-system offset — origin is defined.
            if cmd == "G92":
                return []

            if cmd in ("G0", "G00", "G1", "G01", "G2", "G02", "G3", "G03",
                       "G38.2", "G38.3", "G38.4", "G38.5"):
                has_motion = True
                params = line.parameters
                # A move to X0 Y0 (either axis may be absent if already at 0,
                # but both must be explicitly zero or already zero).
                x_at_zero = params.get('X', None) == 0.0
                y_at_zero = params.get('Y', None) == 0.0
                if x_at_zero and y_at_zero:
                    return []

        if not has_motion:
            return []

        return [AnalysisWarning(
            severity=WarningSeverity.INFO,
            message=(
                "No explicit work-coordinate origin found (no G92 and no "
                "G0/G1 X0 Y0 move). Ensure the machine is zeroed before running."
            ),
            suggestion=(
                "Add 'G92 X0 Y0 Z0' at the start of the program, or jog the "
                "machine to the work origin and zero it before running."
            ),
        )]

    def _check_feed_rates(self, program) -> list[AnalysisWarning]:
        """Warn about missing or zero feed rates on cut moves (G1/G2/G3)."""
        warnings: list[AnalysisWarning] = []
        current_feed: float | None = None

        for gcode_line in program.lines:
            # Update modal feedrate whenever an F word appears on any line.
            if 'F' in gcode_line.parameters:
                current_feed = gcode_line.parameters['F']

            cmd = gcode_line.command
            if cmd not in _FEED_MOVE_COMMANDS:
                continue

            if current_feed is None:
                warnings.append(AnalysisWarning(
                    severity=WarningSeverity.WARNING,
                    message=f"{cmd} has no feedrate — add an F parameter",
                    line_number=gcode_line.line_number,
                    suggestion="Specify a positive feedrate, e.g. F500.",
                ))
            elif current_feed == 0.0:
                warnings.append(AnalysisWarning(
                    severity=WarningSeverity.WARNING,
                    message=f"{cmd} has a feedrate of 0 — machine will not move",
                    line_number=gcode_line.line_number,
                    suggestion="Set a positive feedrate, e.g. F500.",
                ))

        return warnings

    def _check_workpiece_geometry(self, program) -> list[AnalysisWarning]:
        """Geometry infos are intentionally suppressed in warnings UI.

        Workpiece dimensions and origin context are already shown directly in
        the canvas/status surface, so we avoid duplicate INFO entries in the
        warnings list.
        """
        return []
