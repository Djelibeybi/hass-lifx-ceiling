"""LIFX Ceiling Extras data update coordinator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from awesomeversion import AwesomeVersion
from homeassistant.components.light import ATTR_TRANSITION
from homeassistant.const import ATTR_DEVICE_ID, MAJOR_VERSION, MINOR_VERSION
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import LIFXCeiling
from .const import (
    _LOGGER,
    ATTR_DOWNLIGHT_BRIGHTNESS,
    ATTR_DOWNLIGHT_HUE,
    ATTR_DOWNLIGHT_KELVIN,
    ATTR_DOWNLIGHT_SATURATION,
    ATTR_UPLIGHT_BRIGHTNESS,
    ATTR_UPLIGHT_HUE,
    ATTR_UPLIGHT_KELVIN,
    ATTR_UPLIGHT_SATURATION,
    DOMAIN,
)
from .util import find_lifx_coordinators

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from homeassistant.components.lifx.coordinator import LIFXUpdateCoordinator
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall

type LIFXCeilingConfigEntry = ConfigEntry[LIFXCeilingUpdateCoordinator]


class LIFXCeilingUpdateCoordinator(DataUpdateCoordinator[list[LIFXCeiling]]):
    """LIFX Ceiling data update coordinator."""

    config_entry: LIFXCeilingConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: LIFXCeilingConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            config_entry=config_entry,
            name="LIFX Ceiling",
        )

        self.stop_discovery: Callable[[], None] | None = None
        self._discovery_callback: Callable[[LIFXCeiling], None] | None = None
        self._ceiling_coordinators: dict[str, LIFXUpdateCoordinator] = {}
        self._ceilings: set[LIFXCeiling] = set()
        self._hass_version = AwesomeVersion(f"{MAJOR_VERSION}.{MINOR_VERSION}")

        # Track virtual on/off state and desired colors for uplight/downlight
        # Key is mac_addr, value is the state/color
        self._uplight_is_on: dict[str, bool] = {}
        self._downlight_is_on: dict[str, bool] = {}
        # Store desired colors (HSBK tuples) for when light is turned on
        self._uplight_color: dict[str, tuple[int, int, int, int]] = {}
        self._downlight_color: dict[str, tuple[int, int, int, int]] = {}

    @property
    def devices(self) -> list[LIFXCeiling]:
        """Return a list of instantiated LIFX Ceiling devices."""
        return list(self._ceilings)

    @property
    def discovery_callback(self) -> Callable[[LIFXCeiling], None] | None:
        """Return the discovery callback for the LIFX Ceiling Finder."""
        return self._discovery_callback

    @callback
    def set_discovery_callback(
        self, callback: Callable[[LIFXCeiling], None]
    ) -> Callable[[LIFXCeiling], None]:
        """Set the discovery callback for the LIFX Ceiling Finder."""
        old_callback = self._discovery_callback
        self._discovery_callback = callback
        return old_callback

    def async_add_core_listener(
        self, device: LIFXCeiling, callback: Callable[[], None]
    ) -> None:
        """Set the update listener for the LIFX Ceiling Finder."""
        self._ceiling_coordinators[device.mac_addr].async_add_listener(callback)

    async def async_update(self, update_time: datetime | None = None) -> None:
        """Fetch new LIFX Ceiling coordinators from the core integration."""
        lifx_coordinators = [
            coordinator
            for coordinator in find_lifx_coordinators(self.hass)
            if coordinator.device.mac_addr not in self._ceiling_coordinators
        ]

        for coordinator in lifx_coordinators:
            # Cast the existing connection to a LIFX Ceiling objects
            ceiling = LIFXCeiling.cast(coordinator.device)
            self._ceiling_coordinators[ceiling.mac_addr] = coordinator

            self._ceilings.add(ceiling)

            # Initialize virtual state from hardware state on discovery
            mac = ceiling.mac_addr
            if mac not in self._uplight_is_on:
                self._uplight_is_on[mac] = ceiling.uplight_is_on
                self._uplight_color[mac] = ceiling.uplight_color
            if mac not in self._downlight_is_on:
                self._downlight_is_on[mac] = ceiling.downlight_is_on
                self._downlight_color[mac] = ceiling.downlight_color

            if self._discovery_callback and callable(self._discovery_callback):
                self._discovery_callback(ceiling)

    async def async_set_state(self, call: ServiceCall) -> None:
        """Handle the set_state service call."""
        device_ids = call.data.get(ATTR_DEVICE_ID)
        if not isinstance(device_ids, list):
            device_ids = [device_ids]

        downlight_hue = int(
            call.data[ATTR_DOWNLIGHT_HUE] / 360 * 65535
            if ATTR_DOWNLIGHT_HUE in call.data
            else 0
        )
        downlight_saturation = int(
            call.data[ATTR_DOWNLIGHT_SATURATION] / 100 * 65535
            if ATTR_DOWNLIGHT_SATURATION in call.data
            else 0
        )
        downlight_brightness = int(
            call.data[ATTR_DOWNLIGHT_BRIGHTNESS] / 100 * 65535
            if ATTR_DOWNLIGHT_BRIGHTNESS in call.data
            else 65535
        )
        downlight_kelvin = call.data.get(ATTR_DOWNLIGHT_KELVIN, 3500)
        downlight_color = (
            downlight_hue,
            downlight_saturation,
            downlight_brightness,
            downlight_kelvin,
        )

        uplight_hue = int(
            call.data[ATTR_UPLIGHT_HUE] / 360 * 65535
            if ATTR_UPLIGHT_HUE in call.data
            else 0
        )
        uplight_saturation = int(
            call.data[ATTR_UPLIGHT_SATURATION] / 100 * 65535
            if ATTR_UPLIGHT_SATURATION in call.data
            else 0
        )
        uplight_brightness = int(
            call.data[ATTR_UPLIGHT_BRIGHTNESS] / 100 * 65535
            if ATTR_UPLIGHT_BRIGHTNESS in call.data
            else 65535
        )
        uplight_kelvin = call.data.get(ATTR_UPLIGHT_KELVIN, 3500)
        uplight_color = (
            uplight_hue,
            uplight_saturation,
            uplight_brightness,
            uplight_kelvin,
        )

        transition = call.data[ATTR_TRANSITION]

        for device_id in device_ids:
            device_registry = dr.async_get(self.hass)
            device_entry = device_registry.async_get(device_id)

            device: LIFXCeiling | None = None
            for identifier in device_entry.identifiers:
                if (
                    identifier[0] == DOMAIN
                    and identifier[1] in self._ceiling_coordinators
                ):
                    device = self._ceiling_coordinators.get(identifier[1]).device

            if device is not None and isinstance(device, LIFXCeiling):
                mac = device.mac_addr

                # Always store the desired colors
                self._uplight_color[mac] = uplight_color
                self._downlight_color[mac] = downlight_color

                # Check virtual on/off state for each light
                uplight_is_on = self._uplight_is_on.get(mac, device.uplight_is_on)
                downlight_is_on = self._downlight_is_on.get(mac, device.downlight_is_on)

                # If both are virtually off, don't change hardware
                if not uplight_is_on and not downlight_is_on:
                    continue

                # Build colors based on virtual state - use stored color for
                # lights that are on, zero brightness for lights that are off
                if downlight_is_on:
                    effective_downlight = downlight_color
                else:
                    h, s, _, k = downlight_color
                    effective_downlight = (h, s, 0, k)

                if uplight_is_on:
                    effective_uplight = uplight_color
                else:
                    h, s, _, k = uplight_color
                    effective_uplight = (h, s, 0, k)

                colors = [effective_downlight] * (device.total_zones - 1) + [
                    effective_uplight
                ]
                await device.async_set64(
                    colors=colors,
                    duration=transition,
                    power_on=False,
                )

    async def turn_uplight_on(
        self, device: LIFXCeiling, color: tuple[int, int, int, int], duration: int = 0
    ) -> None:
        """Turn on the uplight."""
        mac = device.mac_addr
        self._uplight_is_on[mac] = True
        self._uplight_color[mac] = color
        await device.turn_uplight_on(color, duration)
        await self._ceiling_coordinators[mac].async_request_refresh()

    async def turn_uplight_off(self, device: LIFXCeiling, duration: int = 0) -> None:
        """Turn off the uplight."""
        mac = device.mac_addr
        self._uplight_is_on[mac] = False
        await device.turn_uplight_off(duration)
        await self._ceiling_coordinators[mac].async_request_refresh()

    async def turn_downlight_on(
        self, device: LIFXCeiling, color: tuple[int, int, int, int], duration: int = 0
    ) -> None:
        """Turn on the downlight."""
        mac = device.mac_addr
        self._downlight_is_on[mac] = True
        self._downlight_color[mac] = color
        await device.turn_downlight_on(color, duration)
        await self._ceiling_coordinators[mac].async_request_refresh()

    async def turn_downlight_off(self, device: LIFXCeiling, duration: int = 0) -> None:
        """Turn off the downlight."""
        mac = device.mac_addr
        self._downlight_is_on[mac] = False
        await device.turn_downlight_off(duration)
        await self._ceiling_coordinators[mac].async_request_refresh()

    def set_uplight_color(
        self, device: LIFXCeiling, color: tuple[int, int, int, int]
    ) -> None:
        """Store desired uplight color without applying to hardware."""
        self._uplight_color[device.mac_addr] = color

    def set_downlight_color(
        self, device: LIFXCeiling, color: tuple[int, int, int, int]
    ) -> None:
        """Store desired downlight color without applying to hardware."""
        self._downlight_color[device.mac_addr] = color

    def get_uplight_is_on(self, device: LIFXCeiling) -> bool:
        """Get virtual on/off state for uplight."""
        # If main light is off, uplight is off regardless of virtual state
        if device.power_level == 0:
            return False
        return self._uplight_is_on.get(device.mac_addr, device.uplight_is_on)

    def get_downlight_is_on(self, device: LIFXCeiling) -> bool:
        """Get virtual on/off state for downlight."""
        # If main light is off, downlight is off regardless of virtual state
        if device.power_level == 0:
            return False
        return self._downlight_is_on.get(device.mac_addr, device.downlight_is_on)

    def get_uplight_color(self, device: LIFXCeiling) -> tuple[int, int, int, int]:
        """Get stored uplight color."""
        return self._uplight_color.get(device.mac_addr, device.uplight_color)

    def get_downlight_color(self, device: LIFXCeiling) -> tuple[int, int, int, int]:
        """Get stored downlight color."""
        return self._downlight_color.get(device.mac_addr, device.downlight_color)
