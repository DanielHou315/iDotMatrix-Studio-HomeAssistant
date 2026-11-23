"""Buttons for iDotMatrix Studio."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import IdmConfigEntry
from .entity import IdmEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: IdmConfigEntry, add: AddConfigEntryEntitiesCallback
) -> None:
    add([SyncTimeButton(entry.runtime_data, "sync_time")])


class SyncTimeButton(IdmEntity, ButtonEntity):
    _attr_translation_key = "sync_time"
    _attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        await self.display.async_run("sync_time", {})
