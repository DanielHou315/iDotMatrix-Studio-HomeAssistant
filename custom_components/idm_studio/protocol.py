"""iDotMatrix BLE packet builders.

Pure functions that turn high-level requests into the byte packets the
display expects on characteristic 0xFA02. Nothing here touches Bluetooth or
Home Assistant, so it can be unit tested on its own.

Most packets share a small header: ``[length_lo, length_hi, command, subcommand]``
followed by the arguments. Bulk transfers (images, GIFs, text) use a 16-byte
header carrying the payload size and CRC32.
"""

from __future__ import annotations

import io
import zlib
from collections.abc import Iterable, Sequence
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

RGB = tuple[int, int, int]

UUID_WRITE = "0000fa02-0000-1000-8000-00805f9b34fb"
UUID_NOTIFY = "0000fa03-0000-1000-8000-00805f9b34fb"

SCREEN_SIZES = (16, 32, 64)
BULK_CHUNK = 4096

CLOCK_STYLES = 8
EFFECT_STYLES = 7
TEXT_MODES = 9
TEXT_COLOR_MODES = 6

COUNTDOWN_MODES = {"stop": 0, "start": 1, "pause": 2, "restart": 3}
STOPWATCH_MODES = {"reset": 0, "start": 1, "pause": 2, "resume": 3}


def _byte(value: int, name: str, lo: int = 0, hi: int = 255) -> int:
    value = int(value)
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be between {lo} and {hi}, got {value}")
    return value


def _rgb(color: Sequence[int], name: str = "color") -> list[int]:
    if len(color) != 3:
        raise ValueError(f"{name} must have 3 components")
    return [_byte(c, name) for c in color]


# --- simple settings -------------------------------------------------------


def screen_power(on: bool) -> bytes:
    return bytes([5, 0, 7, 1, 1 if on else 0])


def brightness(percent: int) -> bytes:
    return bytes([5, 0, 4, 128, _byte(percent, "brightness", 5, 100)])


def flip(flipped: bool) -> bytes:
    return bytes([5, 0, 6, 128, 1 if flipped else 0])


def set_time(now: datetime) -> bytes:
    return bytes(
        [
            11,
            0,
            1,
            128,
            now.year % 100,
            now.month,
            now.day,
            now.isoweekday(),
            now.hour,
            now.minute,
            now.second,
        ]
    )


# --- modes -----------------------------------------------------------------


def clock(style: int, show_date: bool, hour24: bool, color: Sequence[int]) -> bytes:
    flags = _byte(style, "style", 0, CLOCK_STYLES - 1)
    if show_date:
        flags |= 128
    if hour24:
        flags |= 64
    return bytes([8, 0, 6, 1, flags, *_rgb(color)])


def solid_color(color: Sequence[int]) -> bytes:
    return bytes([7, 0, 2, 2, *_rgb(color)])


def effect(style: int, colors: Sequence[Sequence[int]]) -> bytes:
    if not 2 <= len(colors) <= 7:
        raise ValueError("effect needs between 2 and 7 colors")
    flat = [c for color in colors for c in _rgb(color)]
    # The length byte matches the official app (6 + number of colors), not
    # the real packet length; the firmware relies on the color count instead.
    return bytes(
        [
            6 + len(colors),
            0,
            3,
            2,
            _byte(style, "style", 0, EFFECT_STYLES - 1),
            90,
            len(colors),
            *flat,
        ]
    )


def scoreboard(left: int, right: int) -> bytes:
    left = max(0, min(999, int(left)))
    right = max(0, min(999, int(right)))
    return bytes([8, 0, 10, 128, left & 255, left >> 8, right & 255, right >> 8])


def countdown(action: str, minutes: int = 0, seconds: int = 0) -> bytes:
    return bytes(
        [
            7,
            0,
            8,
            128,
            COUNTDOWN_MODES[action],
            _byte(minutes, "minutes", 0, 255),
            _byte(seconds, "seconds", 0, 59),
        ]
    )


def stopwatch(action: str) -> bytes:
    return bytes([5, 0, 9, 128, STOPWATCH_MODES[action]])


def pixel(x: int, y: int, color: Sequence[int]) -> bytes:
    """Paint one pixel in drawing (graffiti) mode."""
    return bytes([10, 0, 5, 1, 0, *_rgb(color), _byte(x, "x"), _byte(y, "y")])


def image_mode() -> bytes:
    """Switch the panel into DIY image mode, required before an image upload."""
    return bytes([5, 0, 4, 1, 1])


# --- bulk transfers --------------------------------------------------------


def _bulk_packets(payload: bytes, kind: int, tail: Sequence[int]) -> list[bytes]:
    """Split a payload into chunks, each with a 16-byte transfer header.

    Header: length(2) kind(1) 0 continuation(1) total_size(4) crc32(4) tail(3).
    """
    size = len(payload).to_bytes(4, "little")
    crc = zlib.crc32(payload).to_bytes(4, "little")
    packets = []
    for index, start in enumerate(range(0, len(payload), BULK_CHUNK)):
        chunk = payload[start : start + BULK_CHUNK]
        header = bytearray([0, 0, kind, 0, 2 if index else 0, *size, *crc, *tail])
        header[0:2] = (len(header) + len(chunk)).to_bytes(2, "little")
        packets.append(bytes(header) + chunk)
    return packets


def image_packets(rgb: bytes, size: int) -> list[bytes]:
    """Packets for a raw RGB888 frame of ``size`` x ``size`` pixels."""
    if len(rgb) != size * size * 3:
        raise ValueError(f"image must be {size}x{size} RGB ({size * size * 3} bytes)")
    return _bulk_packets(rgb, kind=2, tail=(5, 0, 13))


def gif_packets(gif: bytes, slot: int = 13, interval: int = 5) -> list[bytes]:
    """Packets for an animated GIF already sized for the panel."""
    if gif[:3] != b"GIF":
        raise ValueError("not a GIF")
    return _bulk_packets(gif, kind=1, tail=(interval & 255, 0, slot & 255))


# --- GIF building ----------------------------------------------------------


def _dark_background(gif: bytes) -> bytes:
    """Point the GIF background index at its darkest palette entry.

    The firmware paints the background color between frames, so a bright
    background index shows up as a flash.
    """
    if len(gif) < 14 or not gif[10] & 128:
        return gif
    count = 2 << (gif[10] & 7)
    table = gif[13 : 13 + count * 3]
    if len(table) < count * 3:
        return gif
    darkest = min(range(count), key=lambda i: sum(table[i * 3 : i * 3 + 3]))
    out = bytearray(gif)
    out[11] = darkest
    return bytes(out)


def frames_to_gif(frames: Sequence[Image.Image], size: int, delay_ms: int) -> bytes:
    """Encode RGB frames as a looping GIF sized for the panel."""
    if not frames:
        raise ValueError("animation needs at least one frame")
    rgb = [
        f.convert("RGB").resize((size, size), Image.Resampling.NEAREST)
        if f.size != (size, size)
        else f.convert("RGB")
        for f in frames
    ]
    # One shared palette keeps colors stable between frames.
    strip = Image.new("RGB", (size, size * len(rgb)))
    for i, frame in enumerate(rgb):
        strip.paste(frame, (0, i * size))
    palette = strip.quantize(colors=256)
    indexed = [frame.quantize(palette=palette) for frame in rgb]
    buffer = io.BytesIO()
    indexed[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=indexed[1:],
        loop=0,
        duration=max(20, int(delay_ms)),
        disposal=2,
    )
    return _dark_background(buffer.getvalue())


def resize_gif(data: bytes, size: int) -> bytes:
    """Re-encode an arbitrary GIF to the panel size, keeping its timing."""
    with Image.open(io.BytesIO(data)) as img:
        delay = img.info.get("duration", 100) or 100
        frames = []
        try:
            while True:
                frames.append(img.convert("RGB").copy())
                img.seek(img.tell() + 1)
        except EOFError:
            pass
    return frames_to_gif(frames, size, delay)


def fit_image(data: bytes, size: int) -> bytes:
    """Decode any image file and return ``size`` x ``size`` RGB bytes."""
    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB")
        if img.size != (size, size):
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        return img.tobytes()


# --- native scrolling text ---------------------------------------------------


def _text_geometry(size: int) -> tuple[int, int, bytes]:
    """Glyph cell width, height and separator for a panel size."""
    if size == 16:
        return 8, 16, b"\x02\xff\xff\xff"
    return 16, 32, b"\x05\xff\xff\xff"


def render_text_strip(
    text: str, size: int, font: ImageFont.ImageFont | ImageFont.FreeTypeFont
) -> Image.Image:
    """Render text as one monochrome strip as tall as a glyph cell."""
    width, height, _ = _text_geometry(size)
    probe = ImageDraw.Draw(Image.new("1", (1, 1)))
    left, top, right, bottom = probe.textbbox((0, 0), text, font=font)
    strip_width = max(width, right - left)
    strip_width = -(-strip_width // width) * width  # round up to whole cells
    strip = Image.new("1", (strip_width, height), 0)
    y = (height - (bottom - top)) // 2 - top
    ImageDraw.Draw(strip).text((-left, y), text, fill=1, font=font)
    return strip


def _cells(strip: Image.Image, size: int) -> Iterable[bytes]:
    width, height, _ = _text_geometry(size)
    pixels = strip.load()
    for x0 in range(0, strip.width, width):
        cell = bytearray()
        for y in range(height):
            for byte_x in range(0, width, 8):
                byte = 0
                for bit in range(8):
                    if pixels[x0 + byte_x + bit, y]:
                        byte |= 1 << bit
                cell.append(byte)
        yield bytes(cell)


def text_bitmaps(
    text: str, size: int, font: ImageFont.ImageFont | ImageFont.FreeTypeFont
) -> bytes:
    """Glyph-cell bitmaps for native text, each prefixed with its separator."""
    if not text:
        raise ValueError("text must not be empty")
    _, _, separator = _text_geometry(size)
    return b"".join(separator + cell for cell in _cells(render_text_strip(text, size, font), size))


def text_packet(
    bitmaps: bytes,
    size: int,
    *,
    mode: int = 1,
    speed: int = 90,
    color_mode: int = 1,
    color: Sequence[int] = (255, 255, 255),
    background: Sequence[int] | None = None,
) -> bytes:
    """Native text packet; the firmware scrolls or animates it by itself.

    ``mode``: 0 static, 1 scroll left, 2 scroll right, 3 scroll up, 4 scroll
    down, 5 blink, 6 fade, 7 tetris, 8 fill.
    ``color_mode``: 0 white, 1 ``color``, 2-5 rainbow variants.
    """
    _, _, separator = _text_geometry(size)
    metadata = bytes(
        [
            *bitmaps.count(separator).to_bytes(2, "little"),
            0,
            1,
            _byte(mode, "mode", 0, TEXT_MODES - 1),
            _byte(speed, "speed", 1, 100),
            _byte(color_mode, "color_mode", 0, TEXT_COLOR_MODES - 1),
            *_rgb(color),
            0 if background is None else 1,
            *_rgb(background or (0, 0, 0), "background"),
        ]
    )
    payload = metadata + bitmaps
    header = bytearray(16)
    header[0:2] = (len(header) + len(payload)).to_bytes(2, "little")
    header[2] = 3
    header[5:9] = len(payload).to_bytes(4, "little")
    header[9:13] = zlib.crc32(payload).to_bytes(4, "little")
    header[15] = 12
    return bytes(header) + payload
