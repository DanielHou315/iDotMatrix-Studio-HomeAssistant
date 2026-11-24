"""Turn images and animations into panel frames, and judge how well they fit.

Pure Pillow code with no Home Assistant imports. The same ``prepare`` result
drives both the sidebar preview and the upload, so the preview shows exactly
the pixels the panel will get.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

from PIL import Image, ImageChops, ImageOps, ImageSequence, ImageStat

MAX_FRAMES = 64
MIN_DELAY = 20
DEFAULT_DELAY = 100
ANALYSIS_SCALE = 4  # analyse at 4x panel resolution
ANALYSIS_FRAMES = 6
MAX_SOURCE_EDGE = 768  # decoded frames are shrunk to this to bound memory
MAX_PIXELS = 16_000_000  # per frame; refuses decompression bombs before decoding
MAX_TOTAL_PIXELS = 64_000_000  # across the decoded frames


class MediaError(ValueError):
    """The data is not an image this integration will decode."""

FITS = ("cover", "contain", "stretch")


@dataclass
class View:
    """How a source is framed on the panel."""

    fit: str = "cover"
    zoom: float = 1.0  # 1 = fit exactly, >1 = closer
    x: float = 0.0  # pan, -1 (left edge) .. 1 (right edge)
    y: float = 0.0
    sharp: bool = False  # nearest-neighbour, for pixel art


@dataclass
class Source:
    frames: list[Image.Image]
    delays: list[int]
    total_frames: int
    width: int
    height: int


@dataclass
class Prepared:
    frames: list[Image.Image]
    delays: list[int]
    analysis: dict = field(default_factory=dict)

    @property
    def animated(self) -> bool:
        return len(self.frames) > 1


def load(data: bytes) -> Source:
    """Decode a still or animated image (GIF, PNG/APNG, WebP, JPEG...)."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            total = getattr(img, "n_frames", 1)
            if width * height > MAX_PIXELS or width * height * min(total, MAX_FRAMES) > MAX_TOTAL_PIXELS:
                raise MediaError(f"Image is too large ({width}x{height}, {total} frames)")
            img.draft("RGB", (MAX_SOURCE_EDGE, MAX_SOURCE_EDGE))  # JPEG: decode already shrunk
            frames, delays = [], []
            for frame in ImageSequence.Iterator(img):
                if len(frames) >= MAX_FRAMES:
                    break
                frame = ImageOps.exif_transpose(frame) if not frames and total == 1 else frame
                rgba = frame.convert("RGBA")
                if max(rgba.size) > MAX_SOURCE_EDGE:
                    rgba.thumbnail((MAX_SOURCE_EDGE, MAX_SOURCE_EDGE), Image.Resampling.BOX)
                flat = Image.new("RGB", rgba.size, (0, 0, 0))
                flat.paste(rgba, mask=rgba.getchannel("A"))
                frames.append(flat)
                delays.append(max(MIN_DELAY, int(frame.info.get("duration") or DEFAULT_DELAY)))
    except MediaError:
        raise
    except Image.DecompressionBombError as err:
        raise MediaError("Image is too large") from err
    except (OSError, SyntaxError, ValueError) as err:
        raise MediaError(f"Could not read the image: {err}") from err
    if not frames:
        raise MediaError("The image has no frames")
    return Source(frames, delays, total, width, height)


def _placement(w: int, h: int, n: int, view: View) -> tuple[int, int, int, int]:
    """Scaled size and top-left offset of the source on an n x n canvas."""
    zoom = max(1.0, min(8.0, view.zoom))
    if view.fit == "stretch":
        sw, sh = n * zoom, n * zoom
    else:
        pick = max if view.fit == "cover" else min
        scale = pick(n / w, n / h) * zoom
        sw, sh = w * scale, h * scale
    # Pan moves across the overflow (or the free space when smaller).
    x0 = (n - sw) / 2 - view.x * abs(sw - n) / 2
    y0 = (n - sh) / 2 - view.y * abs(sh - n) / 2
    return max(1, round(sw)), max(1, round(sh)), round(x0), round(y0)


def compose(frame: Image.Image, n: int, view: View) -> Image.Image:
    """Frame one source image on an n x n black canvas."""
    sw, sh, x0, y0 = _placement(frame.width, frame.height, n, view)
    # Crop to the visible part first so huge zooms stay cheap.
    sx = frame.width / sw
    sy = frame.height / sh
    left, top = max(0, -x0), max(0, -y0)
    right, bottom = min(sw, n - x0), min(sh, n - y0)
    canvas = Image.new("RGB", (n, n), (0, 0, 0))
    if right <= left or bottom <= top:
        return canvas
    box = (left * sx, top * sy, right * sx, bottom * sy)
    size = (right - left, bottom - top)
    if view.sharp:
        part = frame.resize(size, Image.Resampling.NEAREST, box=box)
    else:
        shrinking = size[0] < (box[2] - box[0])
        part = frame.resize(
            size, Image.Resampling.BOX if shrinking else Image.Resampling.BICUBIC, box=box
        )
    canvas.paste(part, (x0 + left, y0 + top))
    return canvas


def _detail_loss(frame: Image.Image, n: int, view: View) -> float:
    """Share of the visible detail that is finer than one LED (0..1).

    Renders the view at ``ANALYSIS_SCALE`` times the panel resolution, shrinks
    that to the panel (area average) and scales it back up. Whatever differs
    between the two is high-frequency content the panel cannot show; we
    report its energy relative to the image's own variance.
    """
    big = n * ANALYSIS_SCALE
    reference = compose(frame, big, View(view.fit, view.zoom, view.x, view.y, False)).convert("L")
    variance = ImageStat.Stat(reference).var[0]
    if variance < 4:  # flat image: nothing to lose
        return 0.0
    small = reference.resize((n, n), Image.Resampling.BOX)
    rebuilt = small.resize((big, big), Image.Resampling.BILINEAR)
    lost = ImageStat.Stat(ImageChops.difference(reference, rebuilt)).rms[0] ** 2
    return min(1.0, lost / variance)


def _is_pixel_art(source: Source, n: int) -> bool:
    """Small, few-colour sources: drawn for low resolution, best kept crisp."""
    first = source.frames[0]
    return max(source.width, source.height) <= n * 4 and first.getcolors(maxcolors=256) is not None


def analyse(source: Source, frames: list[Image.Image], n: int, view: View) -> dict:
    step = max(1, len(source.frames) // ANALYSIS_FRAMES)
    samples = source.frames[::step][:ANALYSIS_FRAMES]
    loss = max(_detail_loss(f, n, view) for f in samples)
    score = round(100 * (1 - loss))

    lum = [ImageStat.Stat(f.convert("L")).mean[0] for f in frames[:: max(1, len(frames) // 6)]]
    dark = sum(lum) / len(lum) < 28

    notes = []
    if loss < 0.12:
        level = "good"
        notes.append(f"Fits well at {n}×{n}.")
    elif loss < 0.3:
        level = "fair"
        notes.append("Some fine detail will soften. Zooming in on the subject can help.")
    else:
        level = "poor"
        notes.append(
            f"Most of the detail is finer than one LED, so text and thin lines will be "
            f"unreadable at {n}×{n}. Try zooming or cropping to the subject, or a "
            "simpler picture."
        )
    if dark:
        notes.append("Very dark overall; LEDs show dark tones as off.")
    if _is_pixel_art(source, n) and not view.sharp:
        notes.append("Looks like pixel art: try Sharp pixels.")
    if source.total_frames > MAX_FRAMES:
        notes.append(f"Only the first {MAX_FRAMES} of {source.total_frames} frames are used.")
    return {
        "score": score,
        "level": level,
        "notes": notes,
        "frames": len(frames),
        "source": [source.width, source.height],
    }


def prepare(data: bytes, n: int, view: View) -> Prepared:
    source = load(data)
    frames = [compose(f, n, view) for f in source.frames]
    analysis = analyse(source, frames, n, view)
    analysis["duration_ms"] = sum(source.delays) if len(frames) > 1 else 0
    return Prepared(frames, source.delays, analysis)


def thumbnail(data: bytes, n: int = 32) -> Image.Image:
    """First frame framed like the default view; for gallery tiles."""
    source = load(data)
    return compose(source.frames[0], n, View(sharp=_is_pixel_art(source, n)))
