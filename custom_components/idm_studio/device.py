"""Bluetooth connection to one iDotMatrix panel."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    close_stale_connections_by_address,
    establish_connection,
)

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from . import protocol

_LOGGER = logging.getLogger(__name__)

# The panel accepts long writes, but some adapters misreport the MTU; 509 is
# what the official app uses as its ceiling.
MAX_WRITE = 509
IDLE_DISCONNECT = 120.0
BULK_PAUSE = 0.05


class IdmConnection:
    """Serialises writes to one panel and keeps the link up while it is busy."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self.hass = hass
        self.address = address
        self.name = name
        self._client: BleakClientWithServiceCache | None = None
        self._lock = asyncio.Lock()
        self._idle: asyncio.TimerHandle | None = None
        self._listeners: list = []

    @property
    def connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    @callback
    def add_listener(self, update) -> callable:
        self._listeners.append(update)
        return lambda: self._listeners.remove(update)

    def _notify(self) -> None:
        for update in list(self._listeners):
            update()

    def _ble_device(self) -> BLEDevice:
        device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if device is None:
            raise HomeAssistantError(
                f"{self.name} is not in Bluetooth range ({self.address})"
            )
        return device

    async def _ensure_connected(self) -> BleakClientWithServiceCache:
        if self.connected:
            return self._client
        device = self._ble_device()
        await close_stale_connections_by_address(self.address)
        _LOGGER.debug("Connecting to %s", self.address)
        self._client = await establish_connection(
            BleakClientWithServiceCache,
            device,
            self.name,
            disconnected_callback=self._on_disconnect,
            ble_device_callback=self._ble_device,
        )
        # Keep the panel clock right every time we talk to it.
        await self._write(protocol.set_time(dt_util.now()))
        self._notify()
        return self._client

    def _on_disconnect(self, _client) -> None:
        _LOGGER.debug("Disconnected from %s", self.address)
        self._client = None
        self.hass.loop.call_soon_threadsafe(self._notify)

    async def _write(self, packet: bytes) -> None:
        client = self._client
        char = client.services.get_characteristic(protocol.UUID_WRITE)
        if char is None:
            raise HomeAssistantError("Panel has no write characteristic")
        size = min(char.max_write_without_response_size, MAX_WRITE)
        for start in range(0, len(packet), size):
            await client.write_gatt_char(char, packet[start : start + size], response=True)

    async def send(self, *packets: bytes | Sequence[bytes]) -> None:
        """Send packets in order. Lists of packets are bulk transfers."""
        flat: list[bytes] = []
        for item in packets:
            flat.extend(item if isinstance(item, list) else [item])
        async with self._lock:
            self._cancel_idle()
            for attempt in (1, 2):
                try:
                    await self._ensure_connected()
                    for index, packet in enumerate(flat):
                        if index and len(packet) > MAX_WRITE:
                            await asyncio.sleep(BULK_PAUSE)
                        await self._write(packet)
                    break
                except (BleakError, TimeoutError, EOFError) as err:
                    _LOGGER.debug("Write to %s failed (attempt %s): %s", self.address, attempt, err)
                    await self._drop()
                    if attempt == 2:
                        raise HomeAssistantError(f"Could not reach {self.name}: {err}") from err
            self._idle = self.hass.loop.call_later(
                IDLE_DISCONNECT, lambda: self.hass.async_create_task(self.disconnect())
            )

    def _cancel_idle(self) -> None:
        if self._idle:
            self._idle.cancel()
            self._idle = None

    async def _drop(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            try:
                await client.disconnect()
            except BleakError:
                pass
        self._notify()

    async def disconnect(self) -> None:
        self._cancel_idle()
        async with self._lock:
            await self._drop()
