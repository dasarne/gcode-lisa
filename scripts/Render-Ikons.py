"""Render platform-specific icon assets for packaging and desktop integration."""

from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"

SOURCE_IMAGE = ASSETS_DIR / "Ikon-Base-Image.png"
OUTPUT_DIR = ASSETS_DIR / "icons"

WINDOWS_ICON = OUTPUT_DIR / "gcode-lisa.ico"
MACOS_ICON = OUTPUT_DIR / "gcode-lisa.icns"

PNG_SIZES = [32, 64, 128, 256, 512]
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
ICNS_SIZES = [
    (16, 16),
    (32, 32),
    (64, 64),
    (128, 128),
    (256, 256),
    (512, 512),
    (1024, 1024),
]


def ensure_output_directories() -> None:
    """Create required output directories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for size in PNG_SIZES:
        (
            OUTPUT_DIR
            / "hicolor"
            / f"{size}x{size}"
            / "apps"
        ).mkdir(parents=True, exist_ok=True)


def load_source_image() -> Image.Image:
    """Load the source image used for icon rendering."""
    if not SOURCE_IMAGE.exists():
        raise FileNotFoundError(
            f"Quelldatei nicht gefunden: {SOURCE_IMAGE}"
        )

    return Image.open(SOURCE_IMAGE).convert("RGBA")


def render_windows_icon(image: Image.Image) -> None:
    """Render multi-resolution Windows ICO."""
    image.save(
        WINDOWS_ICON,
        format="ICO",
        sizes=ICO_SIZES,
    )


def render_macos_icon(image: Image.Image) -> None:
    """Render macOS ICNS icon."""
    image.save(
        MACOS_ICON,
        format="ICNS",
        sizes=ICNS_SIZES,
    )


def render_linux_pngs(image: Image.Image) -> None:
    """Render PNG icon assets for Linux/AppImage integration."""
    for size in PNG_SIZES:
        resized = image.resize(
            (size, size),
            Image.Resampling.LANCZOS,
        )

        filename = f"gcode-lisa-{size}.png"

        output_path = OUTPUT_DIR / filename
        resized.save(output_path, format="PNG")

        hicolor_path = (
            OUTPUT_DIR
            / "hicolor"
            / f"{size}x{size}"
            / "apps"
            / "gcode-lisa.png"
        )

        resized.save(hicolor_path, format="PNG")


def main() -> None:
    """Generate all platform-specific icon assets."""
    print("Erzeuge GCode Lisa Icon-Artefakte...")

    ensure_output_directories()

    image = load_source_image()

    render_windows_icon(image)
    render_macos_icon(image)
    render_linux_pngs(image)

    print("Fertig.")
    print(f"Quelldatei: {SOURCE_IMAGE}")
    print(f"Ausgabeordner: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()