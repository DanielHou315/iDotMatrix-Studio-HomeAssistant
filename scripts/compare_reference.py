"""Compare our packets with the reference iDotMatrix client byte for byte.

Run inside a Home Assistant container that has the tukies/iDotMatrix-HomeAssistant
integration installed (its client is the reference):

    docker cp custom_components/idm_studio/protocol.py homeassistant:/tmp/idm_protocol.py
    docker exec -i homeassistant python3 - < scripts/compare_reference.py
"""

import asyncio
import importlib.util
import io
import sys
from datetime import datetime

from PIL import Image, ImageFont

sys.path.insert(0, "/config")
spec = importlib.util.spec_from_file_location("ours", "/tmp/idm_protocol.py")
ours = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ours)

from custom_components.idotmatrix.client.modules import (  # noqa: E402
    chronograph, clock, common, countdown, effect, fullscreenColor, gif, graffiti, image,
    scoreboard, text,
)


def ref(module, cls):
    obj = getattr(module, cls)()
    obj.conn = None  # build packets only, never touch Bluetooth
    return obj


async def main() -> int:
    c = ref(common, "Common")
    when = datetime(2026, 11, 23, 14, 5, 9)
    rgb = bytes((i * 7) % 256 for i in range(32 * 32 * 3))
    frames = [Image.new("RGB", (32, 32), col) for col in ((255, 0, 0), (0, 0, 255), (0, 255, 0))]
    buf = io.BytesIO()
    frames[0].save(buf, "GIF", save_all=True, append_images=frames[1:], duration=120, loop=0)
    gif_bytes = buf.getvalue()
    font = ImageFont.load_default(size=26)
    bitmaps = ours.text_bitmaps("Hello 42", 32, font)
    t = ref(text, "Text")

    cases = {
        "screen on": (await c.screenOn(), ours.screen_power(True)),
        "screen off": (await c.screenOff(), ours.screen_power(False)),
        "brightness": (await c.setBrightness(37), ours.brightness(37)),
        "flip": (await c.flipScreen(True), ours.flip(True)),
        "set time": (await c.setTime(2026, 11, 23, 14, 5, 9), ours.set_time(when)),
        "clock": (await ref(clock, "Clock").setMode(5, True, False, 1, 2, 3), ours.clock(5, True, False, (1, 2, 3))),
        "color": (await ref(fullscreenColor, "FullscreenColor").setMode(9, 8, 7), ours.solid_color((9, 8, 7))),
        "effect": (
            await ref(effect, "Effect").setMode(3, [(255, 0, 0), (0, 255, 0), (0, 0, 255)]),
            ours.effect(3, [(255, 0, 0), (0, 255, 0), (0, 0, 255)]),
        ),
        "scoreboard": (await ref(scoreboard, "Scoreboard").setMode(300, 7), ours.scoreboard(300, 7)),
        "countdown": (await ref(countdown, "Countdown").setMode(1, 5, 30), ours.countdown("start", 5, 30)),
        "stopwatch": (await ref(chronograph, "Chronograph").setMode(2), ours.stopwatch("pause")),
        "pixel": (await ref(graffiti, "Graffiti").setPixel(9, 8, 7, 3, 4), ours.pixel(3, 4, (9, 8, 7))),
        "image mode": (await ref(image, "Image").setMode(1), ours.image_mode()),
        "image upload": (ref(image, "Image")._createPayloads(bytearray(rgb)), ours.image_packets(rgb, 32)),
        "big image upload": (
            ref(image, "Image")._createPayloads(bytearray(rgb * 4)),
            ours.image_packets(rgb * 4, 64),
        ),
        "gif upload": (ref(gif, "Gif")._createPayloads(bytearray(gif_bytes)), ours.gif_packets(gif_bytes)),
        "text": (
            t._buildStringPacket(text_bitmaps=bytearray(bitmaps), text_mode=2, speed=70, text_color_mode=1,
                                 text_color=(1, 2, 3), text_bg_mode=1, text_bg_color=(4, 5, 6)),
            ours.text_packet(bitmaps, 32, mode=2, speed=70, color_mode=1, color=(1, 2, 3), background=(4, 5, 6)),
        ),
    }
    failed = 0
    for name, (theirs, mine) in cases.items():
        theirs = [bytes(x) for x in theirs] if isinstance(theirs, list) else bytes(theirs)
        mine = [bytes(x) for x in mine] if isinstance(mine, list) else bytes(mine)
        ok = theirs == mine
        failed += not ok
        print(f"{'OK  ' if ok else 'DIFF'} {name}")
        if not ok:
            print("   reference:", theirs if isinstance(theirs, bytes) else [x[:24] for x in theirs])
            print("   ours:     ", mine if isinstance(mine, bytes) else [x[:24] for x in mine])
    return failed


sys.exit(asyncio.run(main()))
