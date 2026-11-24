"""Tests for the pure packet builders."""

import io
import zlib
from datetime import datetime

import pytest
from PIL import Image, ImageFont

from conftest import load

p = load("protocol")


def test_simple_settings():
    assert p.screen_power(True) == bytes([5, 0, 7, 1, 1])
    assert p.screen_power(False) == bytes([5, 0, 7, 1, 0])
    assert p.brightness(50) == bytes([5, 0, 4, 128, 50])
    assert p.flip(True) == bytes([5, 0, 6, 128, 1])
    with pytest.raises(ValueError):
        p.brightness(4)


def test_set_time_uses_iso_weekday():
    # 2026-11-23 is a Monday -> weekday byte 1
    packet = p.set_time(datetime(2026, 11, 23, 14, 5, 9))
    assert packet == bytes([11, 0, 1, 128, 26, 11, 23, 1, 14, 5, 9])


def test_clock_flags():
    assert p.clock(3, True, True, (1, 2, 3)) == bytes([8, 0, 6, 1, 3 | 128 | 64, 1, 2, 3])
    assert p.clock(0, False, False, (0, 0, 0))[4] == 0
    with pytest.raises(ValueError):
        p.clock(8, True, True, (0, 0, 0))


def test_effect_and_color():
    assert p.solid_color((10, 20, 30)) == bytes([7, 0, 2, 2, 10, 20, 30])
    packet = p.effect(2, [(255, 0, 0), (0, 0, 255)])
    assert packet == bytes([8, 0, 3, 2, 2, 90, 2, 255, 0, 0, 0, 0, 255])
    with pytest.raises(ValueError):
        p.effect(0, [(1, 1, 1)])


def test_scoreboard_little_endian_and_clamped():
    assert p.scoreboard(300, 7) == bytes([8, 0, 10, 128, 44, 1, 7, 0])
    assert p.scoreboard(5000, -3) == bytes([8, 0, 10, 128, 0xE7, 3, 0, 0])


def test_timers():
    assert p.countdown("start", 5, 30) == bytes([7, 0, 8, 128, 1, 5, 30])
    assert p.stopwatch("pause") == bytes([5, 0, 9, 128, 2])
    with pytest.raises(ValueError):
        p.countdown("start", 1, 60)


def test_pixel():
    assert p.pixel(3, 4, (9, 8, 7)) == bytes([10, 0, 5, 1, 0, 9, 8, 7, 3, 4])


def test_image_packets_single_chunk():
    rgb = bytes(range(256)) * 12  # 32*32*3 = 3072
    (packet,) = p.image_packets(rgb, 32)
    assert int.from_bytes(packet[0:2], "little") == 16 + 3072
    assert packet[2] == 2 and packet[4] == 0
    assert int.from_bytes(packet[5:9], "little") == 3072
    assert int.from_bytes(packet[9:13], "little") == zlib.crc32(rgb)
    assert packet[13:16] == bytes([5, 0, 13])
    assert packet[16:] == rgb


def test_bulk_continuation_flag():
    rgb = bytes(64 * 64 * 3)  # 12288 bytes -> 3 chunks
    packets = p.image_packets(rgb, 64)
    assert [pk[4] for pk in packets] == [0, 2, 2]
    assert sum(len(pk) - 16 for pk in packets) == len(rgb)
    with pytest.raises(ValueError):
        p.image_packets(rgb, 32)


def test_frames_to_gif_roundtrip():
    red = Image.new("RGB", (32, 32), (255, 0, 0))
    blue = Image.new("RGB", (64, 64), (0, 0, 255))
    gif = p.frames_to_gif([red, blue], 32, 150)
    with Image.open(io.BytesIO(gif)) as img:
        assert img.size == (32, 32)
        assert img.n_frames == 2
    gif2 = p.frames_to_gif([red, blue], 32, [60, 400])
    with Image.open(io.BytesIO(gif2)) as img:
        img.seek(1)
        assert img.info["duration"] == 400
    packets = p.gif_packets(gif)
    assert packets[0][2] == 1
    assert packets[0][13:16] == bytes([5, 0, 13])


def test_dark_background():
    gif = p.frames_to_gif([Image.new("RGB", (16, 16), (255, 255, 255))] * 2, 16, 100)
    # Background index must point at the darkest palette entry.
    count = 2 << (gif[10] & 7)
    table = gif[13 : 13 + count * 3]
    bg = gif[11]
    assert sum(table[bg * 3 : bg * 3 + 3]) == min(
        sum(table[i * 3 : i * 3 + 3]) for i in range(count)
    )


def test_text_packet_layout():
    font = ImageFont.load_default(size=24)
    packet = p.text_packet(p.text_bitmaps("Hi", 32, font), 32, color=(1, 2, 3))
    payload = packet[16:]
    assert int.from_bytes(packet[0:2], "little") == len(packet)
    assert packet[2] == 3 and packet[15] == 12
    assert int.from_bytes(packet[9:13], "little") == zlib.crc32(payload)
    cells = int.from_bytes(payload[0:2], "little")
    assert cells >= 1
    assert payload[7:10] == bytes([1, 2, 3])
    # each cell: 4-byte separator + 16x32 bits
    assert len(payload) == 14 + cells * (4 + 64)
    assert payload[14:18] == b"\x05\xff\xff\xff"
    # something was actually drawn
    assert any(payload[18:])


def test_text_packet_small_panel():
    font = ImageFont.load_default(size=12)
    payload = p.text_packet(p.text_bitmaps("A", 16, font), 16)[16:]
    assert payload[14:18] == b"\x02\xff\xff\xff"
    assert len(payload) == 14 + 1 * (4 + 16)


def _frame_tables(gif: bytes) -> list[int]:
    """Local color table size of every frame (0 = uses the global table)."""
    i = 13 + (3 * (2 << (gif[10] & 7)) if gif[10] & 128 else 0)
    sizes = []
    while gif[i] != 0x3B:
        if gif[i] == 0x21:
            i += 2
        else:
            local = gif[i + 9]
            size = (2 << (local & 7)) if local & 128 else 0
            sizes.append(size)
            i += 10 + 3 * size + 1
        while gif[i]:
            i += gif[i] + 1
        i += 1
    return sizes


def test_gif_frames_share_one_full_palette():
    # Frames with few, different colors: Pillow would write tables of varying size.
    frames = [Image.new("RGB", (16, 16), (0, 0, 0)) for _ in range(4)]
    for i, frame in enumerate(frames):
        for k in range(i * 3 + 1):
            frame.putpixel((k, k), (255, k * 20, 40 * i))
    gif = p.frames_to_gif(frames, 16, 100)
    assert gif[10] & 128 and gif[10] & 7 == 7  # 256-entry global table
    assert _frame_tables(gif) == [0, 0, 0, 0]
    with Image.open(io.BytesIO(gif)) as img:
        for i, frame in enumerate(frames):
            img.seek(i)
            assert img.convert("RGB").getpixel((0, 0)) == frame.getpixel((0, 0))


def test_device_info_reports_screen_size():
    # Replies to set_time from a real 16x16 (firmware 3.16) and a 64x64 (5.09).
    small = p.parse_device_info(bytes.fromhex("09 00 01 80 03 10 01 01 00"))
    assert (small.firmware, small.screen_type, small.size, small.protected) == ("3.16", 1, 16, False)
    big = p.parse_device_info(bytes.fromhex("09 00 01 80 05 09 01 04 01"))
    assert (big.firmware, big.size, big.protected) == ("5.09", 64, True)
    assert p.parse_device_info(bytes.fromhex("09 00 01 80 03 10 01 02 00")).size is None  # 8x32
    assert p.parse_device_info(bytes.fromhex("05 00 01 00 03")) is None  # upload ack
