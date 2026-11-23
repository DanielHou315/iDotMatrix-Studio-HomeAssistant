"""Base entity for iDotMatrix Studio."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .runtime import IdmDisplay


class IdmEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, display: IdmDisplay, key: str) -> None:
        self.display = display
        self._attr_unique_id = f"{display.address}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, display.address)},
            connections={(CONNECTION_BLUETOOTH, display.address)},
            name=display.name,
            manufacturer="iDotMatrix",
            model=f"{display.size}x{display.size} pixel display",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.display.add_listener(self.async_write_ha_state))
