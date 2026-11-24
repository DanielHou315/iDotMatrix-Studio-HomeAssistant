"""Per-panel runtime: actions, remembered state and saved designs."""

from __future__ import annotations

import base64
import binascii
import copy
import json
import uuid
from collections.abc import Callable
from typing import Any

import voluptuous as vol
from PIL import ImageFont

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from . import media, protocol
from .const import CONF_SIZE, DOMAIN, STORAGE_VERSION
from .device import IdmConnection
from .library import MediaLibrary

COLOR = vol.All(
    vol.ExactSequence([vol.Coerce(int)] * 3),
    [vol.All(vol.Coerce(int), vol.Range(0, 255))],
)
BASE64 = cv.string

MAX_UPLOAD = 2 * 1024 * 1024
MAX_FRAMES = 64
MAX_DESIGNS = 100
MAX_DESIGN_BYTES = 2 * 1024 * 1024

# Actions that change what the panel shows; these can be saved as designs.
SHOW_ACTIONS = ("clock", "color", "effect", "image", "gif", "animation", "text", "scoreboard", "media")

VIEW = {
    vol.Optional("fit", default="cover"): vol.In(media.FITS),
    vol.Optional("zoom", default=1.0): vol.All(vol.Coerce(float), vol.Range(1, 8)),
    vol.Optional("x", default=0.0): vol.All(vol.Coerce(float), vol.Range(-1, 1)),
    vol.Optional("y", default=0.0): vol.All(vol.Coerce(float), vol.Range(-1, 1)),
    vol.Optional("sharp", default=False): cv.boolean,
}

SCHEMAS: dict[str, vol.Schema] = {
    "power": vol.Schema({vol.Required("on"): cv.boolean}),
    "brightness": vol.Schema({vol.Required("value"): vol.All(vol.Coerce(int), vol.Range(5, 100))}),
    "flip": vol.Schema({vol.Required("flip"): cv.boolean}),
    "sync_time": vol.Schema({}),
    "clock": vol.Schema(
        {
            vol.Optional("style", default=0): vol.All(vol.Coerce(int), vol.Range(0, protocol.CLOCK_STYLES - 1)),
            vol.Optional("show_date", default=True): cv.boolean,
            vol.Optional("hour24", default=True): cv.boolean,
            vol.Optional("color", default=[255, 255, 255]): COLOR,
        }
    ),
    "color": vol.Schema({vol.Required("color"): COLOR}),
    "effect": vol.Schema(
        {
            vol.Optional("style", default=0): vol.All(vol.Coerce(int), vol.Range(0, protocol.EFFECT_STYLES - 1)),
            vol.Required("colors"): vol.All([COLOR], vol.Length(2, 7)),
        }
    ),
    "scoreboard": vol.Schema(
        {
            vol.Optional("left", default=0): vol.All(vol.Coerce(int), vol.Range(0, 999)),
            vol.Optional("right", default=0): vol.All(vol.Coerce(int), vol.Range(0, 999)),
        }
    ),
    "countdown": vol.Schema(
        {
            vol.Required("action"): vol.In(list(protocol.COUNTDOWN_MODES)),
            vol.Optional("minutes", default=0): vol.All(vol.Coerce(int), vol.Range(0, 255)),
            vol.Optional("seconds", default=0): vol.All(vol.Coerce(int), vol.Range(0, 59)),
        }
    ),
    "stopwatch": vol.Schema({vol.Required("action"): vol.In(list(protocol.STOPWATCH_MODES))}),
    "pixels": vol.Schema(
        {
            vol.Required("pixels"): vol.All(
                [vol.All(vol.ExactSequence([vol.Coerce(int)] * 5))], vol.Length(1, 1024)
            )
        }
    ),
    "clear": vol.Schema({}),
    # Raw RGB frame (``rgb``) from the panel, or any image file (``file``).
    "image": vol.Schema(
        vol.All(
            {vol.Optional("rgb"): BASE64, vol.Optional("file"): BASE64, vol.Optional("path"): cv.string},
            cv.has_at_least_one_key("rgb", "file", "path"),
        )
    ),
    "gif": vol.Schema(
        vol.All(
            {vol.Optional("file"): BASE64, vol.Optional("path"): cv.string},
            cv.has_at_least_one_key("file", "path"),
        )
    ),
    "animation": vol.Schema(
        {
            vol.Required("frames"): vol.All([BASE64], vol.Length(1, MAX_FRAMES)),
            vol.Optional("delay_ms", default=150): vol.All(vol.Coerce(int), vol.Range(20, 5000)),
        }
    ),
    "text": vol.Schema(
        {
            vol.Required("text"): vol.All(cv.string, vol.Length(1, 200)),
            vol.Optional("mode", default=1): vol.All(vol.Coerce(int), vol.Range(0, protocol.TEXT_MODES - 1)),
            vol.Optional("speed", default=90): vol.All(vol.Coerce(int), vol.Range(1, 100)),
            vol.Optional("color_mode", default=1): vol.All(vol.Coerce(int), vol.Range(0, protocol.TEXT_COLOR_MODES - 1)),
            vol.Optional("color", default=[255, 255, 255]): COLOR,
            vol.Optional("background"): vol.Any(None, COLOR),
            vol.Optional("font_size"): vol.All(vol.Coerce(int), vol.Range(6, 64)),
        }
    ),
    "media": vol.Schema({vol.Required("id"): cv.string, **VIEW}),
    "design": vol.Schema({vol.Required("id"): cv.string}),
}
PREVIEW_SCHEMA = vol.Schema({vol.Required("id"): cv.string, **VIEW})


def _decode(data: str, limit: int = MAX_UPLOAD) -> bytes:
    if "," in data[:64] and data.startswith("data:"):
        data = data.split(",", 1)[1]
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as err:
        raise HomeAssistantError("Invalid base64 data") from err
    if len(raw) > limit:
        raise HomeAssistantError("Upload too large")
    return raw


class IdmDisplay:
    """State and actions for one panel."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        address: str,
        name: str,
        size: int,
        library: MediaLibrary,
    ) -> None:
        self.hass = hass
        self.library = library
        self.entry_id = entry_id
        self.name = name
        self.size = size
        self.conn = IdmConnection(hass, address, name, size, self._on_info)
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}")
        self.state: dict[str, Any] = {
            "power": True,
            "brightness": 80,
            "flip": False,
            "mode": None,
            "design": None,
            "clock": {"style": 0, "show_date": True, "hour24": True, "color": [255, 255, 255]},
            "scoreboard": {"left": 0, "right": 0},
        }
        self.designs: list[dict[str, Any]] = []
        self.canvas = bytearray(size * size * 3)
        self._listeners: list[Callable[[], None]] = []
        self._unsub_conn = self.conn.add_listener(self._changed)

    @callback
    def _on_info(self, info: protocol.PanelInfo) -> None:
        """The panel told us its firmware and screen size (on every connect)."""
        registry = dr.async_get(self.hass)
        if device := registry.async_get_device(identifiers={(DOMAIN, self.address)}):
            changes: dict[str, str] = {"sw_version": info.firmware}
            if info.size:
                changes["model"] = f"{info.size}x{info.size} pixel display"
            registry.async_update_device(device.id, **changes)
        if info.size and info.size != self.size:
            # Fix the setting; the entry reloads with the right size.
            entry = self.hass.config_entries.async_get_entry(self.entry_id)
            if entry:
                self.hass.config_entries.async_update_entry(
                    entry, options={**entry.options, CONF_SIZE: info.size}
                )

    @property
    def address(self) -> str:
        return self.conn.address

    async def async_load(self) -> None:
        if data := await self._store.async_load():
            self.state.update(data.get("state", {}))
            self.designs = data.get("designs", [])
            if canvas := data.get("canvas"):
                raw = base64.b64decode(canvas)
                if len(raw) == len(self.canvas):
                    self.canvas = bytearray(raw)

    def _save(self) -> None:
        self._store.async_delay_save(
            lambda: {
                "state": self.state,
                "designs": self.designs,
                "canvas": base64.b64encode(bytes(self.canvas)).decode(),
            },
            2,
        )

    @callback
    def add_listener(self, update: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(update)
        return lambda: self._listeners.remove(update)

    @callback
    def _changed(self) -> None:
        for update in list(self._listeners):
            update()

    async def async_unload(self) -> None:
        self._unsub_conn()
        await self._store.async_save(
            {
                "state": self.state,
                "designs": self.designs,
                "canvas": base64.b64encode(bytes(self.canvas)).decode(),
            }
        )
        await self.conn.disconnect()

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "name": self.name,
            "address": self.address,
            "size": self.size,
            "connected": self.conn.connected,
            "state": self.state,
            "canvas": base64.b64encode(bytes(self.canvas)).decode(),
            "designs": [
                {k: d[k] for k in ("id", "name", "action", "thumb") if k in d} for d in self.designs
            ],
        }

    # --- actions -----------------------------------------------------------

    async def async_run(self, action: str, data: dict[str, Any], *, design: str | None = None) -> None:
        if action not in SCHEMAS:
            raise HomeAssistantError(f"Unknown action {action}")
        data = SCHEMAS[action](dict(data))
        handler = getattr(self, f"_do_{action}")
        await handler(data)
        if action in SHOW_ACTIONS or action in ("pixels", "clear", "countdown", "stopwatch"):
            self.state["mode"] = action
            self.state["design"] = design
            if action in SHOW_ACTIONS and action not in ("image", "gif", "animation"):
                self.state["last"] = {"action": action, "data": data}
            if not self.state["power"]:
                await self.conn.send(protocol.screen_power(True))
                self.state["power"] = True
        self._save()
        self._changed()

    async def _do_power(self, data):
        await self.conn.send(protocol.screen_power(data["on"]))
        self.state["power"] = data["on"]

    async def _do_brightness(self, data):
        await self.conn.send(protocol.brightness(data["value"]))
        self.state["brightness"] = data["value"]

    async def _do_flip(self, data):
        await self.conn.send(protocol.flip(data["flip"]))
        self.state["flip"] = data["flip"]

    async def _do_sync_time(self, data):
        await self.conn.send(protocol.set_time(dt_util.now()))

    async def _do_clock(self, data):
        await self.conn.send(protocol.clock(data["style"], data["show_date"], data["hour24"], data["color"]))
        self.state["clock"] = data

    async def _do_color(self, data):
        await self.conn.send(protocol.solid_color(data["color"]))
        self.canvas = bytearray(bytes(data["color"]) * (self.size * self.size))

    async def _do_effect(self, data):
        await self.conn.send(protocol.effect(data["style"], data["colors"]))

    async def _do_scoreboard(self, data):
        await self.conn.send(protocol.scoreboard(data["left"], data["right"]))
        self.state["scoreboard"] = data

    async def _do_countdown(self, data):
        await self.conn.send(protocol.countdown(data["action"], data["minutes"], data["seconds"]))

    async def _do_stopwatch(self, data):
        await self.conn.send(protocol.stopwatch(data["action"]))

    async def _enter_drawing(self) -> None:
        if self.state.get("mode") not in ("pixels", "image", "clear"):
            await self.conn.send(protocol.image_mode())

    async def _do_pixels(self, data):
        packets = []
        for x, y, r, g, b in data["pixels"]:
            if not (0 <= x < self.size and 0 <= y < self.size):
                raise HomeAssistantError(f"Pixel {x},{y} is outside the panel")
            packets.append(protocol.pixel(x, y, (r, g, b)))
            offset = (y * self.size + x) * 3
            self.canvas[offset : offset + 3] = bytes((r, g, b))
        await self._enter_drawing()
        await self.conn.send(*packets)

    async def _do_clear(self, data):
        self.canvas = bytearray(self.size * self.size * 3)
        await self._send_canvas()

    async def _send_canvas(self) -> None:
        await self._enter_drawing()
        await self.conn.send(protocol.image_packets(bytes(self.canvas), self.size))

    async def _read_path(self, path: str) -> bytes:
        if not self.hass.config.is_allowed_path(path):
            raise HomeAssistantError(f"{path} is not in allowlist_external_dirs")

        def read() -> bytes:
            with open(path, "rb") as file:
                return file.read(MAX_UPLOAD + 1)

        raw = await self.hass.async_add_executor_job(read)
        if len(raw) > MAX_UPLOAD:
            raise HomeAssistantError("File too large")
        return raw

    async def _show_prepared(self, prepared: media.Prepared) -> None:
        if prepared.animated:
            gif = await self.hass.async_add_executor_job(
                protocol.frames_to_gif, prepared.frames, self.size, prepared.delays
            )
            await self._send_gif(gif)
        else:
            self.canvas = bytearray(prepared.frames[0].tobytes())
            await self._send_canvas()

    async def _prepare(self, raw: bytes, view: dict[str, Any]) -> media.Prepared:
        try:
            return await self.hass.async_add_executor_job(
                media.prepare, raw, self.size, media.View(**view)
            )
        except media.MediaError as err:
            raise HomeAssistantError(str(err)) from err

    async def _do_image(self, data):
        if "rgb" in data:
            rgb = _decode(data["rgb"])
            if len(rgb) != len(self.canvas):
                raise HomeAssistantError(f"Expected {self.size}x{self.size} RGB data")
            self.canvas = bytearray(rgb)
            await self._send_canvas()
            return
        raw = _decode(data["file"]) if "file" in data else await self._read_path(data["path"])
        await self._show_prepared(await self._prepare(raw, {}))

    async def _send_gif(self, gif: bytes) -> None:
        await self.conn.send(protocol.gif_packets(gif))

    async def _do_gif(self, data):
        raw = _decode(data["file"]) if "file" in data else await self._read_path(data["path"])
        await self._show_prepared(await self._prepare(raw, {}))

    async def _do_media(self, data):
        raw = await self.library.async_read(data["id"])
        view = {k: data[k] for k in ("fit", "zoom", "x", "y", "sharp")}
        await self._show_prepared(await self._prepare(raw, view))

    async def async_preview(self, request: dict[str, Any]) -> dict[str, Any]:
        """Exactly what ``media`` would send, for the sidebar preview."""
        request = PREVIEW_SCHEMA(dict(request))
        raw = await self.library.async_read(request["id"])
        view = {k: request[k] for k in ("fit", "zoom", "x", "y", "sharp")}
        prepared = await self._prepare(raw, view)
        return {
            "size": self.size,
            "frames": [base64.b64encode(f.tobytes()).decode() for f in prepared.frames],
            "delays": prepared.delays,
            "analysis": prepared.analysis,
        }

    async def _do_animation(self, data):
        from PIL import Image

        frame_len = self.size * self.size * 3
        frames = []
        for encoded in data["frames"]:
            raw = _decode(encoded)
            if len(raw) != frame_len:
                raise HomeAssistantError(f"Each frame must be {self.size}x{self.size} RGB")
            frames.append(Image.frombytes("RGB", (self.size, self.size), raw))
        gif = await self.hass.async_add_executor_job(
            protocol.frames_to_gif, frames, self.size, data["delay_ms"]
        )
        await self._send_gif(gif)

    async def _do_text(self, data):
        size = data.get("font_size") or (26 if self.size >= 32 else 13)

        def build() -> bytes:
            font = ImageFont.load_default(size=size)
            return protocol.text_packet(
                protocol.text_bitmaps(data["text"], self.size, font),
                self.size,
                mode=data["mode"],
                speed=data["speed"],
                color_mode=data["color_mode"],
                color=data["color"],
                background=data.get("background"),
            )

        await self.conn.send(await self.hass.async_add_executor_job(build))

    async def _do_design(self, data):
        design = self.get_design(data["id"])
        await self.async_run(design["action"], design["data"], design=design["id"])

    # --- designs -----------------------------------------------------------

    def get_design(self, design_id: str) -> dict[str, Any]:
        for design in self.designs:
            if design["id"] == design_id or design["name"] == design_id:
                return design
        raise HomeAssistantError(f"No saved design {design_id}")

    @callback
    def save_design(self, name: str, action: str, data: dict[str, Any], thumb: str | None) -> str:
        if action not in SHOW_ACTIONS:
            raise HomeAssistantError(f"{action} cannot be saved as a design")
        if len(self.designs) >= MAX_DESIGNS:
            raise HomeAssistantError(f"A panel holds at most {MAX_DESIGNS} designs; delete some first")
        data = SCHEMAS[action](copy.deepcopy(data))
        if len(json.dumps(data)) > MAX_DESIGN_BYTES:
            raise HomeAssistantError("Design is too large to save")
        design = {"id": uuid.uuid4().hex[:12], "name": name, "action": action, "data": data}
        if thumb:
            design["thumb"] = thumb
        self.designs.append(design)
        self._save()
        self._changed()
        return design["id"]

    @callback
    def delete_design(self, design_id: str) -> None:
        self.designs = [d for d in self.designs if d["id"] != design_id]
        self._save()
        self._changed()
