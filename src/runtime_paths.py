"""Runtime path helpers for development and bundled application builds."""

from __future__ import annotations

from pathlib import Path
from typing import cast
import sys


def project_root() -> Path:
    """Return the project root for dev and bundled PyInstaller builds."""
    if getattr(sys, "frozen", False):
        meipass = cast(str, getattr(sys, "_MEIPASS"))
        return Path(meipass)

    return Path(__file__).resolve().parents[1]


def asset_path(*parts: str) -> Path:
    """Return an absolute path inside the assets directory."""
    return project_root() / "assets" / Path(*parts)