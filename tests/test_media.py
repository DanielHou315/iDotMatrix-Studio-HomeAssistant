"""Tests for framing and fit analysis."""

import io

from PIL import Image, ImageDraw, ImageFont

from conftest import load

m = load("media")


def png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def gif(frames: list[Image.Image], duration=80) -> bytes:
    buf = io.BytesIO()
    frames[0].save(buf, "GIF", save_all=True, append_images=frames[1:], duration=duration, loop=0)
    return buf.getvalue()


def bold_shape() -> Image.Image:
    img = Image.new("RGB", (400, 400), (0, 0, 40))
    ImageDraw.Draw(img).ellipse((80, 80, 320, 320), fill=(255, 60, 60))
    return img


def fine_text() -> Image.Image:
    img = Image.new("RGB", (400, 400), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=11)
    for row in range(30):
        draw.text((4, row * 13), "The quick brown fox jumps over the lazy dog 0123", fill="black", font=font)
    return img


def test_simple_shape_fits_well():
    prepared = m.prepare(png(bold_shape()), 32, m.View())
    assert prepared.analysis["level"] == "good"
    assert prepared.analysis["score"] >= 88
    assert len(prepared.frames) == 1 and prepared.frames[0].size == (32, 32)


def test_fine_text_is_flagged_poor():
    analysis = m.prepare(png(fine_text()), 32, m.View()).analysis
    assert analysis["level"] == "poor"
    assert "unreadable" in analysis["notes"][0]


def test_zooming_in_improves_the_score():
    stripes = Image.new("RGB", (512, 512), "black")
    draw = ImageDraw.Draw(stripes)
    for x in range(0, 512, 6):
        draw.line((x, 0, x, 511), fill="white", width=2)
    far = m.prepare(png(stripes), 32, m.View()).analysis["score"]
    near = m.prepare(png(stripes), 32, m.View(zoom=8)).analysis["score"]
    assert near > far


def test_pixel_art_suggests_sharp_mode():
    art = Image.new("RGB", (16, 16), "black")
    art.putpixel((3, 3), (255, 255, 0))
    notes = m.prepare(png(art), 32, m.View()).analysis["notes"]
    assert any("Sharp pixels" in n for n in notes)
    assert not any("Sharp pixels" in n for n in m.prepare(png(art), 32, m.View(sharp=True)).analysis["notes"])


def test_large_flat_image_is_not_pixel_art():
    notes = m.prepare(png(bold_shape()), 32, m.View()).analysis["notes"]
    assert not any("Sharp pixels" in n for n in notes)


def test_dark_image_warning():
    dark = Image.new("RGB", (64, 64), (8, 8, 8))
    assert any("dark" in n for n in m.prepare(png(dark), 32, m.View()).analysis["notes"])


def test_animation_keeps_frames_and_delays():
    frames = [Image.new("RGB", (64, 48), c) for c in ("red", "green", "blue")]
    prepared = m.prepare(gif(frames, duration=120), 32, m.View(fit="contain"))
    assert prepared.animated
    assert prepared.delays == [120, 120, 120]
    assert prepared.analysis["duration_ms"] == 360
    # contain letterboxes a 4:3 source: top row stays black
    assert prepared.frames[0].getpixel((16, 0)) == (0, 0, 0)
    assert prepared.frames[0].getpixel((16, 16)) != (0, 0, 0)


def test_long_animation_is_truncated():
    frames = [Image.new("RGB", (8, 8), (i, 0, 0)) for i in range(80)]
    prepared = m.prepare(gif(frames), 32, m.View())
    assert len(prepared.frames) == m.MAX_FRAMES
    assert any("first 64 of 80" in n for n in prepared.analysis["notes"])


def test_pan_moves_the_crop():
    img = Image.new("RGB", (200, 100), "red")
    img.paste((0, 0, 255), (100, 0, 200, 100))  # right half blue
    left = m.compose(img, 32, m.View(x=-1))
    right = m.compose(img, 32, m.View(x=1))
    assert left.getpixel((16, 16)) == (255, 0, 0)
    assert right.getpixel((16, 16)) == (0, 0, 255)


def test_transparency_becomes_black():
    img = Image.new("RGBA", (32, 32), (255, 255, 255, 0))
    out = m.prepare(png(img), 32, m.View()).frames[0]
    assert out.getpixel((5, 5)) == (0, 0, 0)
