"""Panel power and brightness as a light."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import IdmConfigEntry
from .entity import IdmEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: IdmConfigEntry, add: AddConfigEntryEntitiesCallback
) -> None:
    add([IdmLight(entry.runtime_data, "screen")])


class IdmLight(IdmEntity, LightEntity):
    _attr_name = None
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    @property
    def is_on(self) -> bool:
        return self.display.state["power"]

    @property
    def brightness(self) -> int:
        return round(self.display.state["brightness"] * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            percent = max(5, min(100, round(kwargs[ATTR_BRIGHTNESS] * 100 / 255)))
            await self.display.async_run("brightness", {"value": percent})
        if not self.is_on:
            await self.display.async_run("power", {"on": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.display.async_run("power", {"on": False})
