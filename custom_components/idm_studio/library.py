"""Media library: built-in animations plus the user's uploads."""

from __future__ import annotations

import base64
import io
import json
import uuid
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from . import media
from .const import DOMAIN, STORAGE_VERSION

BUILTIN_DIR = Path(__file__).parent / "library"
MAX_UPLOAD = 8 * 1024 * 1024
FORMATS = {"GIF": "gif", "PNG": "png", "JPEG": "jpg", "WEBP": "webp", "BMP": "bmp"}


def _thumb_data_url(data: bytes) -> str:
    buffer = io.BytesIO()
    media.thumbnail(data).save(buffer, "PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


class MediaLibrary:
    """Shared by every panel; files live under ``<config>/idm_studio/media``."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.dir = Path(hass.config.path(DOMAIN, "media"))
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.media")
        self.items: list[dict[str, Any]] = []
        self.builtin: list[dict[str, Any]] = []
        self._listeners: list = []

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.items = data.get("items", [])
        self.builtin = await self.hass.async_add_executor_job(self._load_builtin)

    def _load_builtin(self) -> list[dict[str, Any]]:
        index = json.loads((BUILTIN_DIR / "index.json").read_text())
        out = []
        for entry in index:
            raw = (BUILTIN_DIR / entry["file"]).read_bytes()
            out.append(
                {
                    "id": f"builtin:{entry['id']}",
                    "name": entry["name"],
                    "kind": "gif",
                    "builtin": True,
                    "thumb": _thumb_data_url(raw),
                }
            )
        return out

    @callback
    def add_listener(self, update) -> callable:
        self._listeners.append(update)
        return lambda: self._listeners.remove(update)

    def _changed(self) -> None:
        self._store.async_delay_save(lambda: {"items": self.items}, 1)
        for update in list(self._listeners):
            update()

    def as_list(self) -> list[dict[str, Any]]:
        user = [{k: i[k] for k in ("id", "name", "kind", "thumb")} | {"builtin": False} for i in self.items]
        return user + self.builtin

    def _find(self, media_id: str) -> tuple[Path, dict[str, Any]]:
        if media_id.startswith("builtin:"):
            key = media_id.split(":", 1)[1]
            for item in self.builtin:
                if item["id"] == media_id:
                    return BUILTIN_DIR / f"{key}.gif", item
        for item in self.items:
            if item["id"] == media_id:
                return self.dir / item["file"], item
        raise HomeAssistantError(f"No media item {media_id}")

    async def async_read(self, media_id: str) -> bytes:
        path, _ = self._find(media_id)
        return await self.hass.async_add_executor_job(path.read_bytes)

    async def async_add(self, name: str, data: bytes) -> dict[str, Any]:
        if len(data) > MAX_UPLOAD:
            raise HomeAssistantError("File is larger than 8 MB")

        def write() -> tuple[str, str, str]:
            try:
                with Image.open(io.BytesIO(data)) as img:
                    fmt = img.format
                    animated = getattr(img, "n_frames", 1) > 1
            except UnidentifiedImageError as err:
                raise HomeAssistantError("Not an image this panel can use") from err
            if fmt not in FORMATS:
                raise HomeAssistantError(f"Unsupported image format {fmt}")
            media_id = uuid.uuid4().hex[:12]
            filename = f"{media_id}.{FORMATS[fmt]}"
            self.dir.mkdir(parents=True, exist_ok=True)
            (self.dir / filename).write_bytes(data)
            return media_id, filename, ("gif" if animated else "image"), _thumb_data_url(data)

        media_id, filename, kind, thumb = await self.hass.async_add_executor_job(write)
        item = {
            "id": media_id,
            "name": name[:60] or "Upload",
            "file": filename,
            "kind": kind,
            "thumb": thumb,
            "added": dt_util.utcnow().isoformat(),
        }
        self.items.insert(0, item)
        self._changed()
        return item

    async def async_delete(self, media_id: str) -> None:
        if media_id.startswith("builtin:"):
            raise HomeAssistantError("Built-in items cannot be deleted")
        path, item = self._find(media_id)
        self.items.remove(item)
        await self.hass.async_add_executor_job(lambda: path.unlink(missing_ok=True))
        self._changed()

    async def async_rename(self, media_id: str, name: str) -> None:
        _, item = self._find(media_id)
        if item.get("builtin"):
            raise HomeAssistantError("Built-in items cannot be renamed")
        item["name"] = name[:60]
        self._changed()
