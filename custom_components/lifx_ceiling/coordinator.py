"""LIFX Ceiling Extras data update coordinator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    LIFXCeiling,
    LIFXCeilingConnection,
    LIFXCeilingError,
)
from .const import (
    _LOGGER,
    SCAN_INTERVAL,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


LIGHT_UPDATE_INTERVAL = 10
REQUEST_REFRESH_DELAY = 0.35

type LIFXCeilingConfigEntry = ConfigEntry[LIFXCeilingUpdateCoordinator]


@dataclass
class LIFXCeilingData:
    """LIFX data stored in the DataUpdateCoordinator."""

    downlight_brightness: int
    downlight_color: tuple[int, int, int, int]
    downlight_hs_color: tuple[float, float]
    downlight_is_on: bool
    downlight_kelvin: int
    label: str
    max_kelvin: int
    min_kelvin: int
    model: str
    power_level: int
    serial: str
    suggested_area: str
    sw_version: str
    uplight_brightness: int
    uplight_color: tuple[int, int, int, int]
    uplight_hs_color: tuple[float, float]
    uplight_is_on: bool
    uplight_kelvin: int


class LIFXCeilingUpdateCoordinator(DataUpdateCoordinator[LIFXCeilingData]):
    """LIFX Ceiling data update coordinator."""

    config_entry: LIFXCeilingConfigEntry

    def __init__(self, hass: HomeAssistant, entry: LIFXCeilingConfigEntry) -> None:
        """Initialize the coordinator."""
        self._entry = entry
        self._conn = LIFXCeilingConnection(entry.data[CONF_HOST], entry.unique_id)
        self.device: LIFXCeiling | None = None
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{entry.title} ({entry.data[CONF_HOST]})",
            update_interval=SCAN_INTERVAL,
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=REQUEST_REFRESH_DELAY, immediate=True
            ),
        )

    async def _async_setup(self) -> None:
        """Connect to LIFX Ceiling."""
        await self._conn.async_setup()
        if isinstance(self._conn.device, LIFXCeiling):
            self.device = self._conn.device
            await self.device.async_setup()

    async def _async_update_data(self) -> LIFXCeilingData:
        """Fetch current state from LIFX Ceiling."""
        assert isinstance(self.device, LIFXCeiling)  # noqa: S101

        try:
            await self.device.async_update()
            light = self.device
            return LIFXCeilingData(
                downlight_brightness=light.downlight_brightness,
                downlight_color=light.downlight_color,
                downlight_hs_color=light.downlight_hs_color,
                downlight_is_on=light.downlight_is_on,
                downlight_kelvin=light.downlight_kelvin,
                label=light.label,
                max_kelvin=light.max_kelvin,
                min_kelvin=light.min_kelvin,
                model=light.model,
                power_level=light.power_level,
                serial=light.mac_addr,
                suggested_area=light.group,
                sw_version=light.host_firmware_version,
                uplight_brightness=light.uplight_brightness,
                uplight_color=light.uplight_color,
                uplight_hs_color=light.uplight_hs_color,
                uplight_is_on=light.uplight_is_on,
                uplight_kelvin=light.uplight_kelvin,
            )
        except LIFXCeilingError as err:
            raise UpdateFailed(err) from err
