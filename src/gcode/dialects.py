"""Dialect and controller profile registry for G-code support."""

from dataclasses import dataclass, field

from .commands import ALL_COMMANDS


@dataclass(frozen=True)
class DialectProfile:
    """Describes one selectable G-code dialect/controller profile."""

    profile_id: str
    family: str
    name: str
    description: str
    supported_commands: set[str] = field(default_factory=set)
    unsupported_commands: set[str] = field(default_factory=set)
    notes: str = ""

    @property
    def version_id(self) -> str:
        """Backward-compatible alias for GRBL-focused call sites."""
        return self.profile_id

    @property
    def known_commands(self) -> set[str]:
        """Return all commands known to the profile family."""
        return self.supported_commands | self.unsupported_commands


# Initial registry: current GRBL variants expressed as dialect profiles.
GRBL_1_1 = DialectProfile(
    profile_id="1.1",
    family="grbl",
    name="GRBL 1.1",
    description="Standard GRBL 1.1 release",
    supported_commands={"G0", "G1", "G2", "G3", "G38.2", "G38.3", "G38.4", "G38.5", "M3", "M4", "M5"},
    unsupported_commands={"M7", "M8"},
    notes="No coolant support.",
)

GRBL_1_1H = DialectProfile(
    profile_id="1.1H",
    family="grbl",
    name="GRBL 1.1H",
    description="Hobbyist variant - no probing, no coolant",
    supported_commands={"G0", "G1", "G2", "G3", "M3", "M4", "M5"},
    unsupported_commands={"G38.2", "G38.3", "G38.4", "G38.5", "M7", "M8"},
    notes="Probing (G38.x) and coolant (M7/M8) are not available.",
)

GRBL_1_1J = DialectProfile(
    profile_id="1.1j",
    family="grbl",
    name="GRBL 1.1j",
    description="Most feature-complete GRBL 1.1 variant",
    supported_commands={
        "G0", "G1", "G2", "G3",
        "G38.2", "G38.3", "G38.4", "G38.5",
        "M3", "M4", "M5", "M7", "M8", "M9",
    },
    unsupported_commands=set(),
    notes="Full feature set including probing and coolant.",
)

LINUXCNC = DialectProfile(
    profile_id="linuxcnc",
    family="linuxcnc",
    name="LinuxCNC",
    description="LinuxCNC RS-274/NGC style controller profile",
    supported_commands={
        "G0", "G1", "G2", "G3", "G4",
        "G17", "G18", "G19", "G20", "G21",
        "G40", "G41", "G42", "G43", "G43.1", "G49",
        "G53", "G54", "G55", "G56", "G57", "G58", "G59",
        "G61", "G64", "G90", "G91", "G92", "G92.1",
        "M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M30",
    },
    unsupported_commands=set(),
    notes="Initial LinuxCNC profile for validation and detection.",
)

MARLIN = DialectProfile(
    profile_id="marlin",
    family="marlin",
    name="Marlin",
    description="Marlin 3D-printer firmware profile",
    supported_commands={
        "G0", "G1", "G2", "G3", "G4", "G28", "G29", "G90", "G91", "G92",
        "M82", "M83", "M84", "M104", "M106", "M107", "M109", "M140", "M190",
    },
    unsupported_commands=set(),
    notes="Initial Marlin profile focused on common slicer output.",
)


DEFAULT_PROFILE_ID = "1.1H"

PROFILE_MAP: dict[str, DialectProfile] = {
    GRBL_1_1.profile_id: GRBL_1_1,
    GRBL_1_1H.profile_id: GRBL_1_1H,
    GRBL_1_1J.profile_id: GRBL_1_1J,
    LINUXCNC.profile_id: LINUXCNC,
    MARLIN.profile_id: MARLIN,
}


def get_profile(profile_id: str) -> DialectProfile:
    """Return a dialect/controller profile by its id."""
    if profile_id not in PROFILE_MAP:
        valid = ", ".join(sorted(PROFILE_MAP))
        raise ValueError(f"Unknown profile: {profile_id!r}. Valid: [{valid}]")
    return PROFILE_MAP[profile_id]


def list_profile_ids(family: str | None = None) -> list[str]:
    """Return known profile ids, optionally filtered by family."""
    if family is None:
        return sorted(PROFILE_MAP)
    return sorted(pid for pid, p in PROFILE_MAP.items() if p.family == family)


def list_profiles(family: str | None = None) -> list[DialectProfile]:
    """Return known profiles, optionally filtered by family."""
    ids = list_profile_ids(family=family)
    return [PROFILE_MAP[pid] for pid in ids]


def is_command_supported(command: str, profile_id: str) -> bool:
    """Return whether a command is supported by the selected profile."""
    profile = get_profile(profile_id)
    if command in profile.unsupported_commands:
        return False
    if profile.family == "grbl":
        if command not in ALL_COMMANDS:
            return False
        return command in profile.supported_commands
    return command in profile.supported_commands
