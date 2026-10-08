"""Config flow for the LIFX Ceiling integration."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import TYPE_CHECKING, Any

from homeassistant.helpers import config_entry_flow

from .const import DOMAIN, ISSUE_REPLACED_BY_CORE, NAME
from .util import find_lifx_coordinators, is_replaced_by_core

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult
    from homeassistant.core import HomeAssistant


async def _async_has_devices(hass: HomeAssistant) -> bool:
    """Return if there are devices that can be discovered."""
    coordinators = find_lifx_coordinators(hass)

    return len(coordinators) > 0


class LIFXCeilingConfigFlow(
    config_entry_flow.DiscoveryFlowHandler[Awaitable[bool]], domain=DOMAIN
):
    """Discovery config flow for LIFX Ceiling."""

    def __init__(self) -> None:
        """Initialise the config flow."""
        super().__init__(DOMAIN, NAME, _async_has_devices)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Refuse setup on Home Assistant versions with native support."""
        if is_replaced_by_core():
            return self.async_abort(reason=ISSUE_REPLACED_BY_CORE)
        return await super().async_step_user(user_input)
