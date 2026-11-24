"""Config flow for iDotMatrix Studio."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from bleak.exc import BleakError

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_SIZE, DEFAULT_SIZE, DOMAIN
from .device import IdmConnection

_LOGGER = logging.getLogger(__name__)
PROBE_TIMEOUT = 30.0

SIZE_SCHEMA = vol.In({16: "16 x 16", 32: "32 x 32", 64: "64 x 64"})


def _is_panel(info: BluetoothServiceInfoBleak) -> bool:
    return bool(info.name) and info.name.startswith("IDM-")


class IdmConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovery: BluetoothServiceInfoBleak | None = None
        self._found: dict[str, str] = {}
        self._address = ""
        self._name = ""

    async def async_step_bluetooth(self, info: BluetoothServiceInfoBleak) -> ConfigFlowResult:
        await self.async_set_unique_id(info.address)
        self._abort_if_unique_id_configured()
        self._discovery = info
        self.context["title_placeholders"] = {"name": info.name}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        info = self._discovery
        if user_input is not None:
            self._address, self._name = info.address, info.name
            return await self._async_detect()
        return self.async_show_form(step_id="confirm", description_placeholders={"name": info.name})

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            self._address, self._name = address, self._found[address]
            return await self._async_detect()
        configured = self._async_current_ids(include_ignore=False)
        self._found = {
            info.address: info.name
            for info in async_discovered_service_info(self.hass, connectable=True)
            if _is_panel(info) and info.address not in configured
        }
        if not self._found:
            return await self.async_step_manual()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {a: f"{n} ({a})" for a, n in self._found.items()}
                    ),
                }
            ),
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """No panel advertising right now (off, or busy with the phone app)."""
        errors = {}
        if user_input is not None:
            address = user_input[CONF_ADDRESS].strip().upper()
            if not re.fullmatch(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", address):
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                await self.async_set_unique_id(address, raise_on_progress=False)
                self._abort_if_unique_id_configured()
                self._address = address
                self._name = user_input[CONF_NAME].strip() or f"IDM {address[-8:]}"
                return await self._async_detect()
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): str,
                    vol.Optional(CONF_NAME, default=""): str,
                }
            ),
            errors=errors,
        )

    async def _async_detect(self) -> ConfigFlowResult:
        """Ask the panel for its screen size; fall back to asking the user."""
        conn = IdmConnection(self.hass, self._address, self._name)
        reason = "it did not report a size this integration knows"
        try:
            async with asyncio.timeout(PROBE_TIMEOUT):
                info = await conn.async_read_info()
        except (HomeAssistantError, BleakError, TimeoutError, EOFError) as err:
            _LOGGER.debug("Could not read the size of %s: %s", self._address, err)
            info = None
            reason = "it could not be reached (close the phone app, and check it is on and in range)"
        finally:
            await conn.disconnect()
        if info and info.size:
            return self._create(info.size)
        return await self.async_step_size(reason=reason)

    async def async_step_size(
        self, user_input: dict[str, Any] | None = None, reason: str = ""
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self._create(user_input[CONF_SIZE])
        return self.async_show_form(
            step_id="size",
            data_schema=vol.Schema({vol.Required(CONF_SIZE, default=DEFAULT_SIZE): SIZE_SCHEMA}),
            description_placeholders={"name": self._name, "reason": reason},
        )

    def _create(self, size: int) -> ConfigFlowResult:
        return self.async_create_entry(
            title=self._name, data={CONF_ADDRESS: self._address, CONF_SIZE: size}
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return IdmOptionsFlow()


class IdmOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(
            CONF_SIZE, self.config_entry.data.get(CONF_SIZE, DEFAULT_SIZE)
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Required(CONF_SIZE, default=current): SIZE_SCHEMA}),
        )
