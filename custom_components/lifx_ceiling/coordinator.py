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
    from homeassistant.core import HomeAssistant, ServiceCall


LIGHT_UPDATE_INTERVAL = 10
REQUEST_REFRESH_DELAY = 0.35

type LIFXCeilingConfigEntry = ConfigEntry[LIFXCeilingUpdateCoordinator]


@dataclass
class LIFXCeilingSetState:
    """LIFX Ceiling set state data."""

    config_entry: str
    transition: int = 0
    downlight_hue: int = 0
    downlight_saturation: int = 0
    downlight_brightness: int = 100
    downlight_kelvin: int = 3500
    uplight_hue: int = 0
    uplight_saturation: int = 0
    uplight_brightness: int = 100
    uplight_kelvin: int = 3500

    @property
    def downlight_hsbk(self) -> tuple[int, int, int, int]:
        """Return the downlight HSBK values."""
        return (
            int(self.downlight_hue / 360 * 65535),
            int(self.downlight_saturation / 100 * 65535),
            int(self.downlight_brightness / 100 * 65535),
            self.downlight_kelvin,
        )

    @property
    def uplight_hsbk(self) -> tuple[int, int, int, int]:
        """Return the uplight HSBK values."""
        return (
            int(self.uplight_hue / 360 * 65535),
            int(self.uplight_saturation / 100 * 65535),
            int(self.uplight_brightness / 100 * 65535),
            self.uplight_kelvin,
        )


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

    async def async_set_state(self, call: ServiceCall) -> None:
        """Set the state of the LIFX Ceiling."""
        config_entry = call.data.get("config_entry")
        if config_entry != self._entry.entry_id:
            _LOGGER.debug(
                "Ignoring state update for %s, not the current config entry",
                self._entry.title,
            )
            return

        state = LIFXCeilingSetState(**call.data)

        colors = [state.downlight_hsbk] * 63 + [state.uplight_hsbk]
        self.device.set64(
            tile_index=0,
            x=0,
            y=0,
            width=8,
            duration=state.transition,
            colors=colors,
        )
        if (
            state.downlight_brightness > 0 or state.uplight_brightness > 0
        ) and self.device.power_level == 0:
            self.device.set_power("on", duration=state.transition, rapid=True)

        if (
            state.downlight_brightness == 0 and state.uplight_brightness == 0
        ) and self.device.power_level > 0:
            self.device.set_power("off", duration=state.transition, rapid=True)

        await self._async_update_data()

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
