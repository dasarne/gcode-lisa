"""Mouse navigation profiles for the isometric viewport.

Extracted from ``canvas_panel.py`` so that the binding logic can be tested
independently of the Qt widget lifecycle.

Public API
----------
``get_navigation_action(style, button, modifiers)``
    Return ``"rotate"``, ``"pan"``, or ``None`` for a given mouse event.

All ``NAV_STYLE_*`` constants and ``SUPPORTED_NAV_STYLES`` live here and are
re-exported through ``canvas_panel`` for backwards compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt

# ---------------------------------------------------------------------------
# Navigation style identifiers
# ---------------------------------------------------------------------------

NAV_STYLE_CAD = "cad"
NAV_STYLE_BLENDER = "blender"
NAV_STYLE_GESTURE = "gesture"
NAV_STYLE_MAYA_GESTURE = "maya_gesture"
NAV_STYLE_OPEN_CASCADE = "open_cascade"
NAV_STYLE_OPEN_INVENTOR = "open_inventor"
NAV_STYLE_OPEN_SCAD = "open_scad"
NAV_STYLE_REVIT = "revit"
NAV_STYLE_SIEMENS_NX = "siemens_nx"
NAV_STYLE_SOLIDWORKS = "solidworks"
NAV_STYLE_TINKERCAD = "tinkercad"
NAV_STYLE_TOUCHPAD = "touchpad"
NAV_STYLE_LEGACY = "legacy"

SUPPORTED_NAV_STYLES = (
    NAV_STYLE_CAD,
    NAV_STYLE_BLENDER,
    NAV_STYLE_GESTURE,
    NAV_STYLE_MAYA_GESTURE,
    NAV_STYLE_OPEN_CASCADE,
    NAV_STYLE_OPEN_INVENTOR,
    NAV_STYLE_OPEN_SCAD,
    NAV_STYLE_REVIT,
    NAV_STYLE_SIEMENS_NX,
    NAV_STYLE_SOLIDWORKS,
    NAV_STYLE_TINKERCAD,
    NAV_STYLE_TOUCHPAD,
    NAV_STYLE_LEGACY,
)

# ---------------------------------------------------------------------------
# Binding primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MouseBinding:
    """A single mouse-button + modifier combination."""

    button: Qt.MouseButton
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier


#: Mask applied to raw keyboard modifiers – ignores num-lock, caps-lock, etc.
MOD_MASK: Qt.KeyboardModifier = (
    Qt.KeyboardModifier.ShiftModifier
    | Qt.KeyboardModifier.ControlModifier
    | Qt.KeyboardModifier.AltModifier
)

# ---------------------------------------------------------------------------
# Per-style binding table
# ---------------------------------------------------------------------------

StyleBindings = dict[str, tuple[MouseBinding, ...]]

STYLE_BINDINGS: dict[str, StyleBindings] = {
    # FreeCAD CAD model (default) – extra RMB shortcuts included
    NAV_STYLE_CAD: {
        "rotate": (
            MouseBinding(Qt.MouseButton.MiddleButton),
            MouseBinding(Qt.MouseButton.RightButton, Qt.KeyboardModifier.ShiftModifier),
        ),
        "pan": (
            MouseBinding(Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.ShiftModifier),
            MouseBinding(Qt.MouseButton.RightButton, Qt.KeyboardModifier.ControlModifier),
        ),
    },
    NAV_STYLE_BLENDER: {
        "rotate": (MouseBinding(Qt.MouseButton.MiddleButton),),
        "pan": (MouseBinding(Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.ShiftModifier),),
    },
    NAV_STYLE_GESTURE: {
        "rotate": (
            MouseBinding(Qt.MouseButton.RightButton),
            MouseBinding(Qt.MouseButton.LeftButton, Qt.KeyboardModifier.AltModifier),
        ),
        "pan": (MouseBinding(Qt.MouseButton.MiddleButton),),
    },
    NAV_STYLE_MAYA_GESTURE: {
        "rotate": (MouseBinding(Qt.MouseButton.LeftButton, Qt.KeyboardModifier.AltModifier),),
        "pan": (MouseBinding(Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.AltModifier),),
    },
    NAV_STYLE_OPEN_CASCADE: {
        "rotate": (MouseBinding(Qt.MouseButton.MiddleButton),),
        "pan": (MouseBinding(Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.ControlModifier),),
    },
    NAV_STYLE_OPEN_INVENTOR: {
        "rotate": (MouseBinding(Qt.MouseButton.MiddleButton),),
        "pan": (MouseBinding(Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.ShiftModifier),),
    },
    NAV_STYLE_OPEN_SCAD: {
        "rotate": (
            MouseBinding(Qt.MouseButton.RightButton),
            MouseBinding(Qt.MouseButton.RightButton, Qt.KeyboardModifier.ControlModifier),
        ),
        "pan": (MouseBinding(Qt.MouseButton.MiddleButton),),
    },
    NAV_STYLE_REVIT: {
        "rotate": (MouseBinding(Qt.MouseButton.MiddleButton),),
        "pan": (MouseBinding(Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.ShiftModifier),),
    },
    NAV_STYLE_SIEMENS_NX: {
        "rotate": (MouseBinding(Qt.MouseButton.MiddleButton),),
        "pan": (
            MouseBinding(Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.ControlModifier),
            MouseBinding(Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.ShiftModifier),
        ),
    },
    NAV_STYLE_SOLIDWORKS: {
        "rotate": (MouseBinding(Qt.MouseButton.MiddleButton),),
        "pan": (MouseBinding(Qt.MouseButton.MiddleButton, Qt.KeyboardModifier.ControlModifier),),
    },
    NAV_STYLE_TINKERCAD: {
        "rotate": (MouseBinding(Qt.MouseButton.RightButton),),
        "pan": (MouseBinding(Qt.MouseButton.MiddleButton),),
    },
    NAV_STYLE_TOUCHPAD: {
        "rotate": (MouseBinding(Qt.MouseButton.LeftButton, Qt.KeyboardModifier.AltModifier),),
        "pan": (MouseBinding(Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier),),
    },
    NAV_STYLE_LEGACY: {
        "rotate": (MouseBinding(Qt.MouseButton.RightButton, Qt.KeyboardModifier.ControlModifier),),
        "pan": (MouseBinding(Qt.MouseButton.MiddleButton),),
    },
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_navigation_action(
    style: str,
    button: Qt.MouseButton,
    modifiers: Qt.KeyboardModifier,
) -> str | None:
    """Return ``"rotate"``, ``"pan"``, or ``None`` for the given press.

    Parameters
    ----------
    style:
        One of the ``NAV_STYLE_*`` constants.  Falls back to ``NAV_STYLE_CAD``
        when *style* is not recognised.
    button:
        The mouse button that was pressed (``event.button()``).
    modifiers:
        The keyboard modifiers at press time (``event.modifiers()``).  Only
        Shift, Ctrl, and Alt are considered; all other modifier bits are
        ignored.
    """
    bindings = STYLE_BINDINGS.get(style, STYLE_BINDINGS[NAV_STYLE_CAD])
    masked = modifiers & MOD_MASK

    for action in ("rotate", "pan"):
        for binding in bindings[action]:
            if button == binding.button and masked == binding.modifiers:
                return action

    return None
