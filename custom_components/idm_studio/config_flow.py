"""Config flow for iDotMatrix Studio."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .const import CONF_SIZE, DEFAULT_SIZE, DOMAIN

SIZE_SCHEMA = vol.In({16: "16 x 16", 32: "32 x 32", 64: "64 x 64"})


def _is_panel(info: BluetoothServiceInfoBleak) -> bool:
    return bool(info.name) and info.name.startswith("IDM-")


class IdmConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovery: BluetoothServiceInfoBleak | None = None
        self._found: dict[str, str] = {}

    async def async_step_bluetooth(self, info: BluetoothServiceInfoBleak) -> ConfigFlowResult:
        await self.async_set_unique_id(info.address)
        self._abort_if_unique_id_configured()
        self._discovery = info
        self.context["title_placeholders"] = {"name": info.name}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        info = self._discovery
        if user_input is not None:
            return self.async_create_entry(
                title=info.name,
                data={CONF_ADDRESS: info.address, CONF_SIZE: user_input[CONF_SIZE]},
            )
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({vol.Required(CONF_SIZE, default=DEFAULT_SIZE): SIZE_SCHEMA}),
            description_placeholders={"name": info.name},
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._found[address],
                data={CONF_ADDRESS: address, CONF_SIZE: user_input[CONF_SIZE]},
            )
        configured = self._async_current_ids(include_ignore=False)
        self._found = {
            info.address: info.name
            for info in async_discovered_service_info(self.hass, connectable=True)
            if _is_panel(info) and info.address not in configured
        }
        if not self._found:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {a: f"{n} ({a})" for a, n in self._found.items()}
                    ),
                    vol.Required(CONF_SIZE, default=DEFAULT_SIZE): SIZE_SCHEMA,
                }
            ),
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
