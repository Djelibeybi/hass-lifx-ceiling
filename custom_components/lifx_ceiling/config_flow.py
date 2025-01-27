"""Config flow for LIFX Ceiling Extras."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components import onboarding
from homeassistant.components.lifx.util import formatted_serial
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from .api import (
    LIFXCeilingConnection,
    LIFXCeilingError,
)
from .const import DOMAIN, INVALID_DEVICE, UDP_BROADCAST_MAC

if TYPE_CHECKING:
    from homeassistant.components.zeroconf import ZeroconfServiceInfo


class LIFXCeilingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flow for LIFX Ceiling Extras."""

    VERSION = 1

    host: str
    label: str
    mac: str | None = None
    group: str

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user-initiated config flow."""
        if user_input is None:
            return self._async_show_setup_form()

        self.host = user_input[CONF_HOST]

        try:
            await self._get_lifx_label(raise_on_progress=False)
        except LIFXCeilingError:
            return self._async_show_setup_form({"base": "cannot_connect"})

        return self._async_create_entry()

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle Zeroconf-initiated discovery."""
        if not discovery_info.hostname.startswith("D073D5"):
            return self.async_abort(reason="invalid_device")

        self.host = discovery_info.host or discovery_info.hostname
        self.mac = formatted_serial(
            discovery_info.hostname.removesuffix(".local.").lower()
        )

        await self.async_set_unique_id(self.mac)
        self._abort_if_unique_id_configured(updates={CONF_HOST: self.host})

        try:
            await self._get_lifx_label()
        except LIFXCeilingError:
            return self.async_abort(reason="invalid_device")

        if not onboarding.async_is_onboarded(self.hass):
            return self._async_create_entry()

        self._set_confirm_only()
        self.context["title_placeholders"] = {
            "name": f"{self.label} ({self.group})",
        }
        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"label": self.label, "group": self.group},
        )

    async def async_step_zeroconf_confirm(
        self, _: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm zeroconf discovery."""
        self.context["title_placeholders"] = {
            "name": f"{self.label} ({self.group})",
        }
        return self._async_create_entry()

    @callback
    def _async_show_setup_form(
        self, errors: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Show the steup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                }
            ),
        )

    @callback
    def _async_create_entry(self) -> ConfigFlowResult:
        """Create the config entry."""
        self._abort_if_unique_id_configured(updates={CONF_HOST: self.host})
        return self.async_create_entry(title=self.label, data={CONF_HOST: self.host})

    async def _get_lifx_label(self, raise_on_progress: bool = True) -> None:
        """Validate the LIFX device and fetch the label."""
        conn = LIFXCeilingConnection(host=self.host, mac=self.mac or UDP_BROADCAST_MAC)
        await conn.async_setup()

        if conn.device is not None:
            is_ceiling = await conn.device.async_is_lifx_ceiling()
            if not is_ceiling:
                raise LIFXCeilingError(INVALID_DEVICE)

        await self.async_set_unique_id(
            formatted_serial(conn.device.mac_addr), raise_on_progress=raise_on_progress
        )
        self._abort_if_unique_id_configured(updates={CONF_HOST: self.host})
        self.label = conn.device.label
        self.group = conn.device.group
