"""Extra support for LIFX Ceiling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    _LOGGER,
    DISCOVERY_INTERVAL,
    DOMAIN,
    NAME,
    SERVICE_LIFX_CEILING_SET_STATE,
)
from .coordinator import LIFXCeilingConfigEntry, LIFXCeilingUpdateCoordinator
from .util import async_get_legacy_entries, has_single_config_entry

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall
    from homeassistant.helpers.typing import ConfigType


PLATFORMS: list[Platform] = [Platform.LIGHT]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the LIFX Ceiling integration."""
    legacy_entries = async_get_legacy_entries(hass)
    if len(legacy_entries) == 0:
        # No legacy entries found, no need to migrate
        _LOGGER.debug("No legacy entries found, skipping migration")
        return True

    if not has_single_config_entry(hass) and len(legacy_entries) > 0:
        # Migrate the first legacy entry to the new single config entry
        _LOGGER.debug(
            "Migrating legacy entry %s to single config", legacy_entries[0].entry_id
        )
        if hass.config_entries.async_update_entry(
            legacy_entries[0],
            data={},
            options={},
            title=NAME,
            unique_id=DOMAIN,
        ):
            legacy_entries.pop(0)

    if len(legacy_entries) > 0:
        # Remove any remaining legacy entries
        for entry in legacy_entries:
            _LOGGER.debug("Removing legacy entry %s", entry.title)
            await hass.config_entries.async_remove(entry.entry_id)

    return True


async def async_setup_entry(
    hass: HomeAssistant, config_entry: LIFXCeilingConfigEntry
) -> bool:
    """Set up LIFX Ceiling."""
    coordinator = LIFXCeilingUpdateCoordinator(hass, config_entry)
    await coordinator.async_update()

    config_entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

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
