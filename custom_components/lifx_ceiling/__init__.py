"""Extra support for LIFX Ceiling."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import LIFXCeilingConfigEntry, LIFXCeilingUpdateCoordinator

PLATFORMS = [Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: LIFXCeilingConfigEntry) -> bool:
    """Set up extra LIFX Ceiling light entities from config entry."""
    coordinator = LIFXCeilingUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    # Store coordinator in hass.data for service access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: LIFXCeilingConfigEntry
) -> bool:
    """Unload LIFX Ceiling extras config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
