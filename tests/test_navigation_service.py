"""Tests for navigation_service – no Qt widget lifecycle required."""

from PyQt6.QtCore import Qt

from src.ui.navigation_service import (
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
    SUPPORTED_NAV_STYLES,
    get_navigation_action,
)

_NO_MOD = Qt.KeyboardModifier.NoModifier
_SHIFT = Qt.KeyboardModifier.ShiftModifier
_CTRL = Qt.KeyboardModifier.ControlModifier
_ALT = Qt.KeyboardModifier.AltModifier

_MB_LEFT = Qt.MouseButton.LeftButton
_MB_MID = Qt.MouseButton.MiddleButton
_MB_RIGHT = Qt.MouseButton.RightButton


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _action(style: str, button: Qt.MouseButton,
            mods: Qt.KeyboardModifier = _NO_MOD) -> str | None:
    return get_navigation_action(style, button, mods)


# ---------------------------------------------------------------------------
# CAD style
# ---------------------------------------------------------------------------

class TestCadStyle:
    def test_middle_rotates(self):
        assert _action(NAV_STYLE_CAD, _MB_MID) == "rotate"

    def test_shift_right_rotates(self):
        assert _action(NAV_STYLE_CAD, _MB_RIGHT, _SHIFT) == "rotate"

    def test_shift_mid_pans(self):
        assert _action(NAV_STYLE_CAD, _MB_MID, _SHIFT) == "pan"

    def test_ctrl_right_pans(self):
        assert _action(NAV_STYLE_CAD, _MB_RIGHT, _CTRL) == "pan"

    def test_left_button_is_none(self):
        assert _action(NAV_STYLE_CAD, _MB_LEFT) is None

    def test_right_no_mod_is_none(self):
        assert _action(NAV_STYLE_CAD, _MB_RIGHT) is None


# ---------------------------------------------------------------------------
# Blender style
# ---------------------------------------------------------------------------

class TestBlenderStyle:
    def test_middle_rotates(self):
        assert _action(NAV_STYLE_BLENDER, _MB_MID) == "rotate"

    def test_shift_mid_pans(self):
        assert _action(NAV_STYLE_BLENDER, _MB_MID, _SHIFT) == "pan"

    def test_right_button_is_none(self):
        assert _action(NAV_STYLE_BLENDER, _MB_RIGHT) is None


# ---------------------------------------------------------------------------
# Gesture style
# ---------------------------------------------------------------------------

class TestGestureStyle:
    def test_right_rotates(self):
        assert _action(NAV_STYLE_GESTURE, _MB_RIGHT) == "rotate"

    def test_alt_left_rotates(self):
        assert _action(NAV_STYLE_GESTURE, _MB_LEFT, _ALT) == "rotate"

    def test_middle_pans(self):
        assert _action(NAV_STYLE_GESTURE, _MB_MID) == "pan"


# ---------------------------------------------------------------------------
# MayaGesture style
# ---------------------------------------------------------------------------

class TestMayaGestureStyle:
    def test_alt_left_rotates(self):
        assert _action(NAV_STYLE_MAYA_GESTURE, _MB_LEFT, _ALT) == "rotate"

    def test_alt_mid_pans(self):
        assert _action(NAV_STYLE_MAYA_GESTURE, _MB_MID, _ALT) == "pan"

    def test_mid_no_mod_is_none(self):
        assert _action(NAV_STYLE_MAYA_GESTURE, _MB_MID) is None


# ---------------------------------------------------------------------------
# OpenCascade / OpenInventor / Revit / SolidWorks (same rotate binding)
# ---------------------------------------------------------------------------

class TestMiddleOnlyRotateStyles:
    """Styles whose rotate is plain middle-button press."""

    _styles = [
        NAV_STYLE_OPEN_CASCADE,
        NAV_STYLE_OPEN_INVENTOR,
        NAV_STYLE_REVIT,
        NAV_STYLE_SOLIDWORKS,
    ]

    def test_middle_rotates_for_all(self):
        for style in self._styles:
            assert _action(style, _MB_MID) == "rotate", f"failed for {style}"

    def test_pan_binding_open_cascade(self):
        assert _action(NAV_STYLE_OPEN_CASCADE, _MB_MID, _CTRL) == "pan"

    def test_pan_binding_open_inventor(self):
        assert _action(NAV_STYLE_OPEN_INVENTOR, _MB_MID, _SHIFT) == "pan"

    def test_pan_binding_revit(self):
        assert _action(NAV_STYLE_REVIT, _MB_MID, _SHIFT) == "pan"

    def test_pan_binding_solidworks(self):
        assert _action(NAV_STYLE_SOLIDWORKS, _MB_MID, _CTRL) == "pan"


# ---------------------------------------------------------------------------
# OpenSCAD style
# ---------------------------------------------------------------------------

class TestOpenScadStyle:
    def test_right_rotates(self):
        assert _action(NAV_STYLE_OPEN_SCAD, _MB_RIGHT) == "rotate"

    def test_ctrl_right_also_rotates(self):
        assert _action(NAV_STYLE_OPEN_SCAD, _MB_RIGHT, _CTRL) == "rotate"

    def test_middle_pans(self):
        assert _action(NAV_STYLE_OPEN_SCAD, _MB_MID) == "pan"


# ---------------------------------------------------------------------------
# Siemens NX – two pan bindings
# ---------------------------------------------------------------------------

class TestSiemensNxStyle:
    def test_middle_rotates(self):
        assert _action(NAV_STYLE_SIEMENS_NX, _MB_MID) == "rotate"

    def test_ctrl_mid_pans(self):
        assert _action(NAV_STYLE_SIEMENS_NX, _MB_MID, _CTRL) == "pan"

    def test_shift_mid_pans(self):
        assert _action(NAV_STYLE_SIEMENS_NX, _MB_MID, _SHIFT) == "pan"


# ---------------------------------------------------------------------------
# TinkerCAD style
# ---------------------------------------------------------------------------

class TestTinkerCadStyle:
    def test_right_rotates(self):
        assert _action(NAV_STYLE_TINKERCAD, _MB_RIGHT) == "rotate"

    def test_middle_pans(self):
        assert _action(NAV_STYLE_TINKERCAD, _MB_MID) == "pan"


# ---------------------------------------------------------------------------
# Touchpad style
# ---------------------------------------------------------------------------

class TestTouchpadStyle:
    def test_alt_left_rotates(self):
        assert _action(NAV_STYLE_TOUCHPAD, _MB_LEFT, _ALT) == "rotate"

    def test_shift_left_pans(self):
        assert _action(NAV_STYLE_TOUCHPAD, _MB_LEFT, _SHIFT) == "pan"

    def test_left_no_mod_is_none(self):
        assert _action(NAV_STYLE_TOUCHPAD, _MB_LEFT) is None


# ---------------------------------------------------------------------------
# Legacy style
# ---------------------------------------------------------------------------

class TestLegacyStyle:
    def test_ctrl_right_rotates(self):
        assert _action(NAV_STYLE_LEGACY, _MB_RIGHT, _CTRL) == "rotate"

    def test_middle_pans(self):
        assert _action(NAV_STYLE_LEGACY, _MB_MID) == "pan"

    def test_right_no_mod_is_none(self):
        assert _action(NAV_STYLE_LEGACY, _MB_RIGHT) is None


# ---------------------------------------------------------------------------
# Unknown style falls back to CAD
# ---------------------------------------------------------------------------

class TestUnknownStyleFallback:
    def test_unknown_style_falls_back_to_cad(self):
        assert _action("unknown_xyz", _MB_MID) == "rotate"


# ---------------------------------------------------------------------------
# SUPPORTED_NAV_STYLES completeness
# ---------------------------------------------------------------------------

class TestSupportedNavStyles:
    def test_all_styles_in_supported(self):
        expected = {
            NAV_STYLE_CAD, NAV_STYLE_BLENDER, NAV_STYLE_GESTURE,
            NAV_STYLE_MAYA_GESTURE, NAV_STYLE_OPEN_CASCADE, NAV_STYLE_OPEN_INVENTOR,
            NAV_STYLE_OPEN_SCAD, NAV_STYLE_REVIT, NAV_STYLE_SIEMENS_NX,
            NAV_STYLE_SOLIDWORKS, NAV_STYLE_TINKERCAD, NAV_STYLE_TOUCHPAD,
            NAV_STYLE_LEGACY,
        }
        assert set(SUPPORTED_NAV_STYLES) == expected

    def test_modifier_noise_ignored(self):
        """Num-lock / Caps-lock bits outside the mask must not affect action."""
        num_lock = Qt.KeyboardModifier.KeypadModifier
        assert _action(NAV_STYLE_CAD, _MB_MID, num_lock) == "rotate"
