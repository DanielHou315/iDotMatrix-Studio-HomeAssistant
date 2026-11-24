"""Draw the integration icon (original art, carries the repository license).

    uv run --with pillow python scripts/make_brand.py

Writes icon.png (256 px) and icon@2x.png (512 px) into
custom_components/idm_studio/brand/, where recent Home Assistant versions pick up
brand images of custom integrations.
"""

from __future__ import annotations

import colorsys
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parents[1] / "custom_components/idm_studio/brand"
GRID = 8
# A pixel heart on the LED grid; "#" is lit.
HEART = [
    "........",
    ".##..##.",
    "########",
    "########",
    "########",
    ".######.",
    "..####..",
    "...##...",
]


def draw(size: int) -> Image.Image:
    scale = 4  # supersample for smooth circles
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, s - 1, s - 1), radius=s // 5, fill=(22, 26, 34, 255))
    pad = s * 0.12
    cell = (s - 2 * pad) / GRID
    r = cell * 0.36
    for y, row in enumerate(HEART):
        for x, ch in enumerate(row):
            cx, cy = pad + (x + 0.5) * cell, pad + (y + 0.5) * cell
            if ch == "#":
                hue = 0.95 + (x + y) / (2 * GRID) * 0.25  # pink through orange
                color = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(hue % 1, 0.85, 1.0))
                glow = r * 1.35
                d.ellipse((cx - glow, cy - glow, cx + glow, cy + glow), fill=(*color, 70))
            else:
                color = (52, 58, 70)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*color, 255))
    return img.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    draw(256).save(OUT / "icon.png", optimize=True)
    draw(512).save(OUT / "icon@2x.png", optimize=True)
    print("wrote", *sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
