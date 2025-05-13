"""Extra methods for LIFX Ceiling."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from aiolifx.aiolifx import UDP_BROADCAST_PORT, Light
from aiolifx.products import product_map
from aiolifx.products_defs import features_map
from homeassistant.components.lifx.util import async_execute_lifx

if TYPE_CHECKING:
    import asyncio

MESSAGE_TIMEOUT = 3

CEILING_ZONE_COUNT = 64


class LIFXCeilingError(Exception):
    """LIFX Ceiling specific exception."""


class LIFXCeiling(Light):
    """Represents a LIFX Ceiling."""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        mac_addr: str,
        ip_addr: str,
        port: int = UDP_BROADCAST_PORT,
        parent: Any | None = None,
    ) -> None:
        """Initialize the LIFX Ceiling."""
        super().__init__(loop, mac_addr, ip_addr, port, parent)

    @classmethod
    def cast(cls, device: Light) -> LIFXCeiling:
        """Cast the device to LIFXCeiling."""
        assert isinstance(device, Light)  # noqa: S101
        device.__class__ = cls
        assert isinstance(device, LIFXCeiling)  # noqa: S101
        return device

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
    def uplight_hs_color(self) -> tuple[float, float]:
        """Return hue, saturation as a tuple."""
        hue, saturation, _, _ = self.chain[0][63]
        hue = hue / 65535 * 360
        saturation = saturation / 65535 * 100
        return hue, saturation

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
    def downlight_hs_color(self) -> tuple[float, float]:
        """Return the hue, saturation from zone 0."""
        hue, saturation, _, _ = self.chain[0][0]
        hue = hue / 65535 * 360
        saturation = saturation / 65535 * 100
        return hue, saturation

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
