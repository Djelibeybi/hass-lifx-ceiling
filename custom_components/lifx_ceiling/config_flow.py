"""Config flow for the LIFX Ceiling integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers import config_entry_flow

from .const import DOMAIN, NAME
from .util import find_lifx_coordinators

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def _async_has_devices(hass: HomeAssistant) -> bool:
    """Return if there are devices that can be discovered."""
    coordinators = find_lifx_coordinators(hass)

    return len(coordinators) > 0


config_entry_flow.register_discovery_flow(DOMAIN, NAME, _async_has_devices)
