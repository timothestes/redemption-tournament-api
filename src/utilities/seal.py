import os

import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
from PIL import ImageFont


def generate_seal(
    valid: bool, deck_format: str = "Type 1", size: int = 200
) -> Image.Image:
    """
    Generate a transparent stamp/seal image indicating deck legality.

    Args:
        valid: True for a green "LEGAL" seal, False for a red "ILLEGAL" seal.
        deck_format: "Type 1" or "Type 2" — displayed on the seal.
        size: Diameter of the seal in pixels.

    Returns:
        PIL Image in RGBA mode (transparent background).
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size // 2
    radius = center - 4
    border_width = max(size // 25, 3)

    if valid:
        color = (34, 139, 34)  # forest green
        status_text = "LEGAL"
    else:
        color = (180, 30, 30)  # dark red
        status_text = "ILLEGAL"

    # Outer circle
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        outline=(*color, 210),
        width=border_width,
    )

    # Inner circle
    inner_gap = border_width + max(size // 40, 2)
    inner_radius = radius - inner_gap
    draw.ellipse(
        [
            center - inner_radius,
            center - inner_radius,
            center + inner_radius,
            center + inner_radius,
        ],
        outline=(*color, 210),
        width=max(border_width // 2, 2),
    )

    # Semi-transparent fill
    fill_radius = inner_radius - max(size // 50, 1)
    draw.ellipse(
        [
            center - fill_radius,
            center - fill_radius,
            center + fill_radius,
            center + fill_radius,
        ],
        fill=(*color, 35),
    )

    # Load font
    try:
        font_path = os.path.join("fonts", "dejavu-sans-bold.ttf")
        status_font_size = int(size * 0.16) if valid else int(size * 0.13)
        status_font = ImageFont.truetype(font_path, status_font_size)
        format_font_size = int(size * 0.12)
        format_font = ImageFont.truetype(font_path, format_font_size)
    except Exception:
        status_font = ImageFont.load_default()
        format_font = status_font

    # Format label (e.g. "TYPE 1") — top half
    format_label = deck_format.upper()
    fmt_bbox = draw.textbbox((0, 0), format_label, font=format_font)
    fmt_w = fmt_bbox[2] - fmt_bbox[0]
    fmt_h = fmt_bbox[3] - fmt_bbox[1]
    fmt_x = center - fmt_w // 2
    fmt_y = center - fmt_h - int(size * 0.06)
    draw.text((fmt_x, fmt_y), format_label, fill=(*color, 180), font=format_font)

    # Status text (LEGAL / ILLEGAL) — bottom half
    st_bbox = draw.textbbox((0, 0), status_text, font=status_font)
    st_w = st_bbox[2] - st_bbox[0]
    st_h = st_bbox[3] - st_bbox[1]
    st_x = center - st_w // 2
    st_y = center + int(size * 0.02)
    draw.text((st_x, st_y), status_text, fill=(*color, 210), font=status_font)

    return img
