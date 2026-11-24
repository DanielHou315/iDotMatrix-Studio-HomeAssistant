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
# BlueZ reports the minimum write size (20) until the MTU exchange finishes,
# shortly after connecting; uploads sent before then crawl in 20-byte writes.
MTU_WAIT = 2.0
MIN_WRITE = 20
BULK_PAUSE = 0.05
# Uploads go in 4096-byte chunks, and the panel answers each one on the notify
# characteristic with ``05 00 <kind> 00 <status>``. Sending the next chunk
# before that answer makes it drop data. The official app waits 5 s.
ACK_TIMEOUT = 5.0
ACK_NEXT = {0: 2, 1: 1, 2: 1}  # kind -> status meaning "send the next chunk"
ACK_DONE = {0: (0, 1), 1: (3,), 2: (3,)}


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
        self._write_size = MIN_WRITE
        self._acks: asyncio.Queue[bytes] = asyncio.Queue()

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
        await self._wait_for_mtu()
        try:
            await self._client.start_notify(protocol.UUID_NOTIFY, self._on_notification)
        except BleakError as err:
            _LOGGER.debug("No notifications from %s: %s", self.address, err)
        await self._write(protocol.set_time(dt_util.now()))
        self._notify()
        return self._client

    async def _wait_for_mtu(self) -> None:
        """Learn the negotiated write size, which BlueZ may not report yet."""
        client = self._client
        char = client.services.get_characteristic(protocol.UUID_WRITE)
        if char is None or char.max_write_without_response_size > MIN_WRITE:
            return
        # Ask BlueZ directly (AcquireWrite also triggers the MTU exchange).
        acquire = getattr(getattr(client, "_backend", None), "_acquire_mtu", None)
        if acquire is not None:
            try:
                await acquire()
                self._write_size = client.mtu_size - 3
            except Exception as err:  # noqa: BLE001 - best effort, fall back to 20
                _LOGGER.debug("Could not acquire MTU from %s: %s", self.address, err)
        if self._write_size <= MIN_WRITE:
            try:
                async with asyncio.timeout(MTU_WAIT):
                    while char.max_write_without_response_size <= MIN_WRITE:
                        await asyncio.sleep(0.1)
            except TimeoutError:
                _LOGGER.debug("%s still reports %s-byte writes", self.address, MIN_WRITE)
        _LOGGER.debug(
            "%s write size: reported %s, acquired %s",
            self.address, char.max_write_without_response_size, self._write_size,
        )

    def _on_disconnect(self, _client) -> None:
        _LOGGER.debug("Disconnected from %s", self.address)
        self._client = None
        self._write_size = MIN_WRITE
        self.hass.loop.call_soon_threadsafe(self._notify)

    async def _write(self, packet: bytes) -> None:
        client = self._client
        char = client.services.get_characteristic(protocol.UUID_WRITE)
        if char is None:
            raise HomeAssistantError("Panel has no write characteristic")
        size = min(max(char.max_write_without_response_size, self._write_size), MAX_WRITE)
        if len(packet) > size:
            _LOGGER.debug("Writing %s bytes to %s in %s-byte chunks", len(packet), self.address, size)
        for start in range(0, len(packet), size):
            await client.write_gatt_char(char, packet[start : start + size], response=True)

    def _on_notification(self, _char, data: bytearray) -> None:
        _LOGGER.debug("%s says %s", self.address, data.hex(" "))
        self._acks.put_nowait(bytes(data))

    async def _upload(self, chunks: Sequence[bytes]) -> None:
        """Send a bulk transfer one chunk at a time, waiting for each answer."""
        for index, chunk in enumerate(chunks):
            kind = chunk[2]
            while not self._acks.empty():
                self._acks.get_nowait()
            await self._write(chunk)
            try:
                status = await self._chunk_status(kind)
            except TimeoutError:
                # Keep going like before acknowledgements were known, but say so.
                _LOGGER.warning(
                    "%s did not acknowledge chunk %s/%s", self.name, index + 1, len(chunks)
                )
                await asyncio.sleep(BULK_PAUSE)
                continue
            if status in ACK_DONE.get(kind, ()):
                return  # finished (or the panel already had this exact file)
            if status == ACK_NEXT.get(kind):
                continue
            if status == 2:
                raise HomeAssistantError(f"{self.name} has no room for this upload; try a smaller file")
            raise HomeAssistantError(f"{self.name} rejected the upload (status {status})")

    async def _chunk_status(self, kind: int) -> int:
        async with asyncio.timeout(ACK_TIMEOUT):
            while True:
                data = await self._acks.get()
                if len(data) >= 5 and data[0] == 5 and data[2] == kind and data[3] == 0:
                    return data[4]

    async def send(self, *packets: bytes | Sequence[bytes]) -> None:
        """Send packets in order. Lists of packets are acknowledged uploads."""
        async with self._lock:
            self._cancel_idle()
            for attempt in (1, 2):
                try:
                    await self._ensure_connected()
                    for item in packets:
                        if isinstance(item, list):
                            await self._upload(item)
                        else:
                            await self._write(item)
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
        self._write_size = MIN_WRITE
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
