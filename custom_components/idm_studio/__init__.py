"""iDotMatrix Studio: iDotMatrix panels with an app-style sidebar panel."""

from __future__ import annotations

import base64
import binascii
import hashlib
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send

from .const import CONF_SIZE, DEFAULT_SIZE, DOMAIN, PANEL_ELEMENT, PANEL_URL, STATIC_URL
from .library import MediaLibrary
from .runtime import SCHEMAS, IdmDisplay

PLATFORMS = [Platform.BUTTON, Platform.LIGHT, Platform.SELECT]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
FRONTEND_DIR = Path(__file__).parent / "frontend"
SIGNAL_PANELS = f"{DOMAIN}_panels_changed"

type IdmConfigEntry = ConfigEntry[IdmDisplay]


DATA_LIBRARY = f"{DOMAIN}_library"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    library = MediaLibrary(hass)
    await library.async_load()
    hass.data[DATA_LIBRARY] = library
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=False)]
    )
    for command in (
        ws_subscribe,
        ws_run,
        ws_save_design,
        ws_delete_design,
        ws_preview,
        ws_media_list,
        ws_media_upload,
        ws_media_delete,
        ws_media_rename,
    ):
        websocket_api.async_register_command(hass, command)
    _register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: IdmConfigEntry) -> bool:
    display = IdmDisplay(
        hass,
        entry.entry_id,
        entry.data[CONF_ADDRESS],
        entry.title,
        entry.options.get(CONF_SIZE, entry.data.get(CONF_SIZE, DEFAULT_SIZE)),
        hass.data[DATA_LIBRARY],
    )
    await display.async_load()
    entry.runtime_data = display
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    if PANEL_URL not in hass.data.get(frontend.DATA_PANELS, {}):
        # A content hash in the URL busts every cache (browsers, and proxies such
        # as Cloudflare that ignore Cache-Control) whenever panel.js changes.
        version = await hass.async_add_executor_job(_panel_hash)
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_URL,
            webcomponent_name=PANEL_ELEMENT,
            sidebar_title="iDotMatrix",
            sidebar_icon="mdi:dots-grid",
            module_url=f"{STATIC_URL}/panel.js?v={version}",
            require_admin=False,
        )
    entry.async_on_unload(lambda: async_dispatcher_send(hass, SIGNAL_PANELS))
    async_dispatcher_send(hass, SIGNAL_PANELS)
    return True


def _panel_hash() -> str:
    return hashlib.sha256((FRONTEND_DIR / "panel.js").read_bytes()).hexdigest()[:12]


async def _reload(hass: HomeAssistant, entry: IdmConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: IdmConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        await entry.runtime_data.async_unload()
        if not [e for e in _loaded(hass) if e.entry_id != entry.entry_id]:
            frontend.async_remove_panel(hass, PANEL_URL)
    return ok


def _loaded(hass: HomeAssistant) -> list[IdmConfigEntry]:
    return [e for e in hass.config_entries.async_loaded_entries(DOMAIN)]


def _display(hass: HomeAssistant, entry_id: str | None) -> IdmDisplay:
    entries = _loaded(hass)
    if entry_id:
        entries = [e for e in entries if e.entry_id == entry_id]
    if len(entries) != 1:
        raise ServiceValidationError(
            "Pick a panel with config_entry_id" if entries else "No iDotMatrix panel is loaded"
        )
    return entries[0].runtime_data


# --- services ------------------------------------------------------------------

SERVICE_ACTIONS = (
    "text", "clock", "color", "effect", "image", "gif", "scoreboard",
    "countdown", "stopwatch", "design", "sync_time", "clear", "media",
)


def _register_services(hass: HomeAssistant) -> None:
    for action in SERVICE_ACTIONS:

        async def handle(call: ServiceCall, action: str = action) -> None:
            data = dict(call.data)
            display = _display(hass, data.pop("config_entry_id", None))
            await display.async_run(action, data)

        hass.services.async_register(
            DOMAIN,
            action,
            handle,
            schema=vol.Schema(
                {vol.Optional("config_entry_id"): cv.string}, extra=vol.ALLOW_EXTRA
            ),
        )


# --- websocket API for the sidebar panel -------------------------------------


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/subscribe"})
@callback
def ws_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Stream the state of every panel; resent whenever anything changes."""
    unsubs: list = []

    @callback
    def send() -> None:
        connection.send_message(
            websocket_api.event_message(
                msg["id"], {"panels": [e.runtime_data.as_dict() for e in _loaded(hass)]}
            )
        )

    @callback
    def resubscribe(*_: Any) -> None:
        while unsubs:
            unsubs.pop()()
        for entry in _loaded(hass):
            unsubs.append(entry.runtime_data.add_listener(send))
        send()

    remove_dispatch = async_dispatcher_connect(hass, SIGNAL_PANELS, resubscribe)

    @callback
    def unsubscribe() -> None:
        remove_dispatch()
        while unsubs:
            unsubs.pop()()

    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"])
    resubscribe()


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/run",
        vol.Required("entry_id"): str,
        vol.Required("action"): vol.In(list(SCHEMAS)),
        vol.Optional("data", default={}): dict,
    }
)
@websocket_api.async_response
async def ws_run(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        await _display(hass, msg["entry_id"]).async_run(msg["action"], msg["data"])
    except (HomeAssistantError, vol.Invalid) as err:
        connection.send_error(msg["id"], "failed", str(err))
        return
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/design/save",
        vol.Required("entry_id"): str,
        vol.Required("name"): vol.All(str, vol.Length(1, 60)),
        vol.Required("action"): str,
        vol.Required("data"): dict,
        vol.Optional("thumb"): vol.All(str, vol.Length(max=20000)),
    }
)
@websocket_api.async_response
async def ws_save_design(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        design_id = _display(hass, msg["entry_id"]).save_design(
            msg["name"], msg["action"], msg["data"], msg.get("thumb")
        )
    except (HomeAssistantError, vol.Invalid) as err:
        connection.send_error(msg["id"], "failed", str(err))
        return
    connection.send_result(msg["id"], {"id": design_id})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/design/delete",
        vol.Required("entry_id"): str,
        vol.Required("design_id"): str,
    }
)
@callback
def ws_delete_design(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    _display(hass, msg["entry_id"]).delete_design(msg["design_id"])
    connection.send_result(msg["id"])


# --- media library -----------------------------------------------------------


def _ws_errors(func):
    """Turn expected errors into websocket error replies."""

    async def wrapper(hass, connection, msg):
        try:
            await func(hass, connection, msg)
        except (HomeAssistantError, vol.Invalid) as err:
            connection.send_error(msg["id"], "failed", str(err))

    return wrapper


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/preview",
        vol.Required("entry_id"): str,
        vol.Required("view"): dict,
    }
)
@websocket_api.async_response
@_ws_errors
async def ws_preview(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    connection.send_result(msg["id"], await _display(hass, msg["entry_id"]).async_preview(msg["view"]))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/media/list"})
@callback
def ws_media_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    connection.send_result(msg["id"], {"items": hass.data[DATA_LIBRARY].as_list()})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/media/upload",
        vol.Required("name"): str,
        vol.Required("file"): str,
    }
)
@websocket_api.async_response
@_ws_errors
async def ws_media_upload(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        raw = base64.b64decode(msg["file"], validate=True)
    except (binascii.Error, ValueError) as err:
        raise HomeAssistantError("Invalid file data") from err
    item = await hass.data[DATA_LIBRARY].async_add(msg["name"], raw)
    connection.send_result(msg["id"], {"id": item["id"], "kind": item["kind"]})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/media/delete", vol.Required("media_id"): str}
)
@websocket_api.async_response
@_ws_errors
async def ws_media_delete(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    await hass.data[DATA_LIBRARY].async_delete(msg["media_id"])
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/media/rename",
        vol.Required("media_id"): str,
        vol.Required("name"): vol.All(str, vol.Length(1, 60)),
    }
)
@websocket_api.async_response
@_ws_errors
async def ws_media_rename(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    await hass.data[DATA_LIBRARY].async_rename(msg["media_id"], msg["name"])
    connection.send_result(msg["id"])
