"""Extra support for LIFX Ceiling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.event import async_track_time_interval

from .const import DISCOVERY_INTERVAL, DOMAIN, SERVICE_LIFX_CEILING_SET_STATE
from .coordinator import LIFXCeilingConfigEntry, LIFXCeilingUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall


PLATFORMS: list[Platform] = [Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: LIFXCeilingConfigEntry) -> bool:
    """Set up LIFX Ceiling Extras."""
    coordinator = LIFXCeilingUpdateCoordinator(hass, entry)
    await coordinator.async_update()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_set_state(call: ServiceCall) -> None:
        """Handle the set_state service call."""
        await coordinator.async_set_state(call)

    hass.services.async_register(
        DOMAIN, SERVICE_LIFX_CEILING_SET_STATE, handle_set_state
    )

    coordinator.stop_discovery = async_track_time_interval(
        hass, coordinator.async_update, DISCOVERY_INTERVAL
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: LIFXCeilingConfigEntry
) -> bool:
    """Unload LIFX Ceiling extras config entry."""
    data: LIFXCeilingUpdateCoordinator = entry.runtime_data
    if data.stop_discovery is not None and callable(data.stop_discovery):
        data.stop_discovery()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
