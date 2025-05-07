"""Extra support for LIFX Ceiling."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, SERVICE_LIFX_CEILING_SET_STATE
from .coordinator import LIFXCeilingConfigEntry, LIFXCeilingUpdateCoordinator

PLATFORMS = [Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: LIFXCeilingConfigEntry) -> bool:
    """Set up extra LIFX Ceiling light entities from config entry."""
    coordinator = LIFXCeilingUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_set_state(call: ServiceCall) -> None:
        """Handle the set_state service call."""
        await coordinator.async_set_state(call)

    hass.services.async_register(
        DOMAIN, SERVICE_LIFX_CEILING_SET_STATE, handle_set_state
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: LIFXCeilingConfigEntry
) -> bool:
    """Unload LIFX Ceiling extras config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
