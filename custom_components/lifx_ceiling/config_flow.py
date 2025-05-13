"""Config flow for the LIFX Ceiling integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.lifx.const import DOMAIN as LIFX_DOMAIN
from homeassistant.components.lifx.const import LIFX_CEILING_PRODUCT_IDS
from homeassistant.components.lifx.coordinator import LIFXUpdateCoordinator
from homeassistant.helpers import config_entry_flow

from .const import DOMAIN, NAME

if TYPE_CHECKING:
    from homeassistant.components.lifx.manager import LIFXManager
    from homeassistant.core import HomeAssistant


async def _async_has_devices(hass: HomeAssistant) -> bool:
    """Return if there are devices that can be discovered."""
    lifx_data: dict[str, LIFXManager | LIFXUpdateCoordinator] = hass.data[LIFX_DOMAIN]

    lifx_coordinators = {
        coordinator
        for coordinator in lifx_data.values()
        if isinstance(coordinator, LIFXUpdateCoordinator)
    }

    coordinators = {
        coordinator
        for coordinator in lifx_coordinators
        if coordinator.is_matrix
        and coordinator.device.product in LIFX_CEILING_PRODUCT_IDS
    }

    return len(coordinators) > 0


config_entry_flow.register_discovery_flow(DOMAIN, NAME, _async_has_devices)
