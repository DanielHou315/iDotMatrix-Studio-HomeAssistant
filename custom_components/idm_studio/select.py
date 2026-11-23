"""Saved designs as a select, so automations and HomeKit can pick one."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import IdmConfigEntry
from .entity import IdmEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: IdmConfigEntry, add: AddConfigEntryEntitiesCallback
) -> None:
    add([DesignSelect(entry.runtime_data, "design")])


class DesignSelect(IdmEntity, SelectEntity):
    _attr_translation_key = "design"

    @property
    def options(self) -> list[str]:
        return [d["name"] for d in self.display.designs]

    @property
    def current_option(self) -> str | None:
        current = self.display.state.get("design")
        for design in self.display.designs:
            if design["id"] == current:
                return design["name"]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.display.async_run("design", {"id": option})
