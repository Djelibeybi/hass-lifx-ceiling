"""LIFX Ceiling Extras data update coordinator."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from homeassistant.components.lifx.const import DOMAIN as LIFX_DOMAIN
from homeassistant.components.lifx.const import LIFX_CEILING_PRODUCT_IDS
from homeassistant.components.lifx.coordinator import LIFXUpdateCoordinator
from homeassistant.components.lifx.util import async_execute_lifx
from homeassistant.components.light import ATTR_TRANSITION
from homeassistant.const import ATTR_DEVICE_ID
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

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.components.lifx.manager import LIFXManager
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

    async def async_update(self) -> None:
        """Fetch new LIFX Ceiling coordinators from the core integration."""
        _LOGGER.debug("Looking for new LIFX Ceiling devices")

        lifx_data: dict[str, LIFXManager | LIFXUpdateCoordinator] = self.hass.data[
            LIFX_DOMAIN
        ]

        lifx_coordinators = {
            coordinator
            for coordinator in lifx_data.values()
            if isinstance(coordinator, LIFXUpdateCoordinator)
        }

        for coordinator in lifx_coordinators:
            if (
                coordinator.is_matrix
                and coordinator.device.product in LIFX_CEILING_PRODUCT_IDS
                and coordinator.device.mac_addr not in self._ceiling_coordinators
            ):
                # Cast the existing connection to a LIFX Ceiling objects
                ceiling = LIFXCeiling.cast(coordinator.device)
                self._ceiling_coordinators[ceiling.mac_addr] = coordinator

                self._ceilings.add(ceiling)

                if self._discovery_callback and callable(self._discovery_callback):
                    self._discovery_callback(ceiling)

    async def async_set_state(self, call: ServiceCall) -> None:
        """Handle the set_state service call."""
        device_ids = call.data.get(ATTR_DEVICE_ID)
        if not isinstance(device_ids, list):
            device_ids = [device_ids]

        downlight_hue = (
            call.data[ATTR_DOWNLIGHT_HUE] / 360 * 65535
            if ATTR_DOWNLIGHT_HUE in call.data
            else 0
        )
        downlight_saturation = (
            call.data[ATTR_DOWNLIGHT_SATURATION] / 100 * 65535
            if ATTR_DOWNLIGHT_SATURATION in call.data
            else 0
        )
        downlight_brightness = (
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

        uplight_hue = (
            call.data[ATTR_UPLIGHT_HUE] / 360 * 65535
            if ATTR_UPLIGHT_HUE in call.data
            else 0
        )
        uplight_saturation = (
            call.data[ATTR_UPLIGHT_SATURATION] / 100 * 65535
            if ATTR_UPLIGHT_SATURATION in call.data
            else 0
        )
        uplight_brightness = (
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
                if downlight_brightness == 0 and uplight_brightness == 0:
                    await async_execute_lifx(
                        partial(device.set_power, value="off", duration=transition)
                    )
                else:
                    colors = [downlight_color] * 63 + [uplight_color]
                    device.set64(
                        tile_index=0,
                        x=0,
                        y=0,
                        width=8,
                        duration=transition,
                        colors=colors,
                    )
                    if device.power_level == 0:
                        await async_execute_lifx(
                            partial(device.set_power, value="on", duration=transition)
                        )

    async def turn_uplight_on(
        self, device: LIFXCeiling, color: tuple[int, int, int, int], duration: int = 0
    ) -> None:
        """Turn on the uplight."""
        await device.turn_uplight_on(color, duration)
        await self._ceiling_coordinators[device.mac_addr].async_request_refresh()

    async def turn_uplight_off(self, device: LIFXCeiling, duration: int = 0) -> None:
        """Turn off the uplight."""
        await device.turn_uplight_off(duration)
        await self._ceiling_coordinators[device.mac_addr].async_request_refresh()

    async def turn_downlight_on(
        self, device: LIFXCeiling, color: tuple[int, int, int, int], duration: int = 0
    ) -> None:
        """Turn on the downlight."""
        await device.turn_downlight_on(color, duration)
        await self._ceiling_coordinators[device.mac_addr].async_request_refresh()

    async def turn_downlight_off(self, device: LIFXCeiling, duration: int = 0) -> None:
        """Turn off the downlight."""
        await device.turn_downlight_off(duration)
        await self._ceiling_coordinators[device.mac_addr].async_request_refresh()
