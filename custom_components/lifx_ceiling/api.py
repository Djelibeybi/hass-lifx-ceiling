"""Extra methods for LIFX Ceiling."""

from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import TYPE_CHECKING

from aiolifx.aiolifx import Light
from aiolifx.products import product_map
from aiolifx.products_defs import features_map
from homeassistant.components.lifx.util import (
    async_execute_lifx,
    async_multi_execute_lifx_with_retries,
)

from .const import DEFAULT_ATTEMPTS, LIFX_CEILING_PRODUCT_IDS, OVERALL_TIMEOUT

if TYPE_CHECKING:
    from aiolifx.msgtypes import StateGroup, StateLabel, StateVersion

UDP_BROADCAST_PORT = 56700
UDP_BROADCAST_MAC = "00:00:00:00:00:00"
MESSAGE_TIMEOUT = 3

CEILING_ZONE_COUNT = 64
HSBK_HUE = 0
HSBK_SATURATION = 1
HSBK_BRIGHTNESS = 2
HSBK_KELVIN = 3

_LOGGER = logging.getLogger(__package__)


class LIFXCeilingError(Exception):
    """LIFX Ceiling specific exception."""


class LIFXCeilingConnection:
    """Establish a connection to the Ceiling."""

    def __init__(self, host: str, mac: str) -> None:
        """Initialize the connection."""
        self.host = host
        self.mac = mac
        self.device: LIFXCeiling | None = None
        self.transport: asyncio.DatagramTransport | None = None

    async def async_setup(self) -> None:
        """Connect to the LIFX Ceiling."""
        loop = asyncio.get_running_loop()
        self.transport, self.device = await loop.create_datagram_endpoint(
            lambda: LIFXCeiling(loop, self.mac, self.host),
            remote_addr=(self.host, UDP_BROADCAST_PORT),
        )

    def async_stop(self) -> None:
        """Close the transport."""
        if self.transport is not None:
            self.transport.close()


class LIFXCeiling(Light):
    """Represents a LIFX Ceiling."""

    async def async_is_lifx_ceiling(self) -> bool:
        """Return true if this is a LIFX Ceiling."""
        if self.label is None or not self.label:
            resp: StateLabel = await async_execute_lifx(self.get_label)
            self.label = resp.label.decode().replace("\x00", "")

        if self.group is None or not self.group:
            resp: StateGroup = await async_execute_lifx(self.get_group)
            self.group = resp.label.decode().replace("\x00", "")

        if self.product is None:
            resp: StateVersion = await async_execute_lifx(self.get_version)
            self.product = resp.product

        return self.product in LIFX_CEILING_PRODUCT_IDS

    async def async_setup(self) -> None:
        """Update from device."""
        if self.product is None:
            await async_execute_lifx(self.get_version)
        if self.host_firmware_version is None:
            await async_execute_lifx(self.get_hostfirmware)
        if self.label is None:
            await async_execute_lifx(self.get_color)
        if self.group is None:
            await async_execute_lifx(self.get_group)

        if self.product is not None and (
            self.tile_devices is None or len(self.tile_devices) == 0
        ):
            await async_multi_execute_lifx_with_retries(
                [
                    self.get_device_chain,
                    partial(self.get64, tile_index=0, length=1, width=8),
                ],
                DEFAULT_ATTEMPTS,
                OVERALL_TIMEOUT,
            )

        await self.async_update()

    async def async_update(self) -> None:
        """Update internal state from device."""
        await async_multi_execute_lifx_with_retries(
            [
                self.get_color,
                partial(self.get64, tile_index=0, length=1, width=8),
            ],
            DEFAULT_ATTEMPTS,
            OVERALL_TIMEOUT,
        )

    @property
    def min_kelvin(self) -> int:
        """Return the minimum kelvin value."""
        return features_map[self.product]["min_kelvin"]

    @property
    def max_kelvin(self) -> int:
        """Return the maximum kelvin value."""
        return features_map[self.product]["max_kelvin"]

    @property
    def model(self) -> str:
        """Return a friendly model name."""
        return product_map.get(self.product, "LIFX Bulb")

    @property
    def uplight_color(self) -> tuple[int, int, int, int]:
        """Return the HSBK values for the last zone."""
        hue, saturation, brightness, kelvin = self.chain[0][63]
        return hue, saturation, brightness, kelvin

    @property
    def uplight_hs_color(self) -> tuple[int, int]:
        """Return hue, saturation as a tuple."""
        hue, saturation, _, _ = self.chain[0][63]
        hue = round(hue / 65535 * 360)
        return hue, saturation >> 8

    @property
    def uplight_brightness(self) -> int:
        """Return uplight brightness."""
        _, _, brightness, _ = self.chain[0][63]
        return brightness >> 8

    @property
    def uplight_kelvin(self) -> int:
        """Return uplight kelvin."""
        _, _, _, kelvin = self.chain[0][63]
        return kelvin

    @property
    def downlight_hs_color(self) -> tuple[int, int]:
        """Return the hue, saturation from zone 0."""
        hue, saturation, _, _ = self.chain[0][0]
        hue = round(hue / 65535 * 360)
        return hue, saturation >> 8

    @property
    def downlight_brightness(self) -> int:
        """Return max brightness value for all downlight zones."""
        unscaled = max(brightness for _, _, brightness, _ in self.chain[0][:63])
        return unscaled >> 8

    @property
    def downlight_kelvin(self) -> int:
        """Return kelvin from zone 0."""
        _, _, _, kelvin = self.chain[0][0]
        return kelvin

    @property
    def downlight_color(self) -> tuple[int, int, int, int]:
        """Return zone 0 hue, saturation, kelvin with max brightness."""
        brightness = max(brightness for _, _, brightness, _ in self.chain[0][:63])
        hue, saturation, _, kelvin = self.chain[0][0]
        return hue, saturation, brightness, kelvin

    @property
    def uplight_is_on(self) -> bool:
        """Return true if power > 0 and uplight brightess > 0."""
        return bool(self.power_level > 0 and self.uplight_brightness > 0)

    @property
    def downlight_is_on(self) -> bool:
        """Return true if power > 0 and downlight zones max brightness > 0."""
        return bool(self.power_level > 0 and self.downlight_brightness > 0)

    async def turn_uplight_on(
        self, color: tuple[int, int, int, int], duration: int = 0
    ) -> None:
        """
        Turn the uplight on.

        Color is a tuple of hue, saturation, brightness and kelvin values (0-65535).
        Duration is time in milliseconds to transition from current state to color.
        """
        if self.power_level > 0:
            # The device is already on, just change the color of the uplight.
            self.set64(
                tile_index=0, x=7, y=7, width=8, duration=duration, colors=[color]
            )
        else:
            # The device is off, so set the downlight brightess to 0 first.
            colors = [(h, s, 0, k) for h, s, _, k in self.chain[0][:63]]
            colors.append(color)

            self.set64(tile_index=0, x=0, y=0, width=8, duration=0, colors=colors)
            await async_execute_lifx(
                partial(self.set_power, value="on", duration=duration * 1000)
            )

    async def turn_uplight_off(self, duration: int = 0) -> None:
        """
        Turn the uplight off.

        If the downlight is on, lower the brightness of the uplight to zero.
        If the downlight is off, turn off the entire light.
        """
        if self.downlight_is_on is True:
            await self.async_update()
            hue, saturation, _, kelvin = self.chain[0][63]
            self.set64(
                tile_index=0,
                x=7,
                y=7,
                width=8,
                duration=duration,
                colors=[(hue, saturation, 0, kelvin)],
            )
        else:
            await async_execute_lifx(
                partial(self.set_power, value="off", duration=duration * 1000)
            )

    async def turn_downlight_on(
        self, color: tuple[int, int, int, int], duration: int = 0
    ) -> None:
        """
        Turn the downlight on.

        Color is a tuple of hue, saturation, brightness and kelvin values (0-65535).
        Duration is the time in milliseconds to transition from current state to color.
        """
        colors = [color] * 63
        if self.power_level > 0:
            colors.append(self.chain[0][63])
            self.set64(
                tile_index=0, x=0, y=0, width=8, duration=duration, colors=colors
            )
        else:
            hue, saturation, _, kelvin = self.chain[0][63]
            colors.append((hue, saturation, 0, kelvin))

            self.set64(tile_index=0, x=0, y=0, width=8, duration=0, colors=colors)
            await async_execute_lifx(
                partial(self.set_power, value="on", duration=duration * 1000)
            )

    async def turn_downlight_off(self, duration: int = 0) -> None:
        """
        Turn the downlight off.

        If the uplight is on, lower the downlight brightness to zero.
        If the uplight is off, turn off the entire device.
        """
        if self.uplight_is_on:
            await self.async_update()
            colors = [(h, s, 0, k) for h, s, _, k in self.chain[0][:63]]
            colors.append(self.chain[0][63])
            self.set64(
                tile_index=0,
                x=0,
                y=0,
                width=8,
                duration=duration,
                colors=colors,
            )
        else:
            await async_execute_lifx(
                partial(self.set_power, value="off", duration=duration * 1000)
            )
