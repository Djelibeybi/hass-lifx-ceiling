"""LIFX Ceiling Extras light."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv

from .const import ATTR_DOWNLIGHT, ATTR_POWER, ATTR_UPLIGHT, DOMAIN
from .coordinator import LIFXCeilingConfigEntry, LIFXCeilingUpdateCoordinator
from .entity import LIFXCeilingEntity
from .util import hsbk_for_turn_on

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import VolDictType

PARALLEL_UPDATES = 1

SERVICE_SET_STATE = "set_state"

LIFX_CEILING_SET_STATE_SCHEMA: VolDictType = {
    vol.Optional(ATTR_UPLIGHT): vol.Schema(
        {
            vol.Optional(ATTR_POWER): cv.boolean,
            vol.Optional(ATTR_BRIGHTNESS): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=255)
            ),
            vol.Optional(ATTR_COLOR_TEMP_KELVIN): vol.All(
                vol.Coerce(int), vol.Range(min=1500, max=9000)
            ),
            vol.Optional(ATTR_HS_COLOR): vol.All(
                vol.ExactSequence((cv.positive_float, cv.positive_float)),
                vol.Coerce(tuple),
            ),
            vol.Optional(ATTR_RGB_COLOR): vol.All(
                vol.ExactSequence((cv.byte, cv.byte, cv.byte)), vol.Coerce(tuple)
            ),
        }
    ),
    vol.Optional(ATTR_DOWNLIGHT): vol.Schema(
        {
            vol.Optional(ATTR_POWER): cv.boolean,
            vol.Optional(ATTR_BRIGHTNESS): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=255)
            ),
            vol.Optional(ATTR_COLOR_TEMP_KELVIN): vol.All(
                vol.Coerce(int), vol.Range(min=1500, max=9000)
            ),
            vol.Optional(ATTR_HS_COLOR): vol.All(
                vol.ExactSequence((cv.positive_float, cv.positive_float)),
                vol.Coerce(tuple),
            ),
            vol.Optional(ATTR_RGB_COLOR): vol.All(
                vol.ExactSequence((cv.byte, cv.byte, cv.byte)), vol.Coerce(tuple)
            ),
        }
    ),
    vol.Optional(ATTR_TRANSITION): vol.All(
        vol.Coerce(float), vol.Range(min=0, max=3600)
    ),
}


def _handle_uplight_config(uplight_data: dict[str, Any]) -> tuple[int, int, int, int]:
    """Process uplight configuration and return HSBK color tuple."""
    # Default to on if not specified
    uplight_on = uplight_data.get(ATTR_POWER, True)

    if uplight_on:
        color_kwargs = {}
        for attr in (
            ATTR_BRIGHTNESS,
            ATTR_COLOR_TEMP_KELVIN,
            ATTR_HS_COLOR,
            ATTR_RGB_COLOR
        ):
            if attr in uplight_data:
                color_kwargs[attr] = uplight_data[attr]

        # Use a default color (white at full brightness) if no color specified
        default_color = (0, 0, 65535, 3500)
        return hsbk_for_turn_on(default_color, **color_kwargs)

    # Off state - set brightness to 0 but keep color values
    return (0, 0, 0, 3500)


def _handle_downlight_config(
    downlight_data: dict[str, Any]
) -> tuple[int, int, int, int]:
    """Process downlight configuration and return HSBK color tuple."""
    # Default to on if not specified
    downlight_on = downlight_data.get(ATTR_POWER, True)

    if downlight_on:
        color_kwargs = {}
        for attr in (
            ATTR_BRIGHTNESS,
            ATTR_COLOR_TEMP_KELVIN,
            ATTR_HS_COLOR,
            ATTR_RGB_COLOR
        ):
            if attr in downlight_data:
                color_kwargs[attr] = downlight_data[attr]

        # Use a default color (white at full brightness) if no color specified
        default_color = (0, 0, 65535, 3500)
        return hsbk_for_turn_on(default_color, **color_kwargs)

    # Off state - set brightness to 0 but keep color values
    return (0, 0, 0, 3500)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LIFXCeilingConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LIFX Ceiling extra lights."""
    coordinator = entry.runtime_data
    await coordinator.device.async_update()

    # Register the service for the LIFX Ceiling domain (only needs to be done once)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_STATE):

        async def async_handle_set_state(call: ServiceCall) -> None:
            """Handle the set_state service call."""
            target_entity_ids = call.data.get("entity_id", None)

            # Get all LIFX Ceiling coordinators using list comprehension
            all_coordinators = [
                entry_data for entry_data in hass.data[DOMAIN].values()
                if isinstance(entry_data, LIFXCeilingUpdateCoordinator)
            ]

            # If no target entities specified, apply to all
            if not target_entity_ids:
                for coordinator in all_coordinators:
                    await async_set_state(coordinator, call)
                return

            # If specific entities are targeted, find the matching coordinators
            for entity_id in target_entity_ids:
                entity = hass.data["entity_components"]["light"].get_entity(entity_id)
                if entity and hasattr(entity, "coordinator") and isinstance(
                    entity.coordinator, LIFXCeilingUpdateCoordinator
                ):
                    await async_set_state(entity.coordinator, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_STATE,
            async_handle_set_state,
            schema=LIFX_CEILING_SET_STATE_SCHEMA,
        )

    async_add_entities(
        [
            LIFXCeilingDownlight(coordinator),
            LIFXCeilingUplight(coordinator),
        ],
        update_before_add=True,
    )


async def async_set_state(
    coordinator: LIFXCeilingUpdateCoordinator, call: ServiceCall
) -> None:
    """Set the exact state of the light without depending on current state."""
    duration = int(call.data.get(ATTR_TRANSITION, 0))
    device = coordinator.device

    # Prepare colors for both uplight and downlight
    if ATTR_UPLIGHT in call.data:
        uplight_color = _handle_uplight_config(call.data[ATTR_UPLIGHT])
    else:
        # Not specified - use current state
        uplight_color = device.chain[0][63]

    if ATTR_DOWNLIGHT in call.data:
        downlight_color = _handle_downlight_config(call.data[ATTR_DOWNLIGHT])
    else:
        # Not specified - use current state
        downlight_color = device.chain[0][0]

    # Prepare zone colors: 63 zones for downlight, 1 zone for uplight
    colors = [downlight_color] * 63 + [uplight_color]

    # Determine if we need to turn the device on/off
    any_zone_on = (uplight_color[2] > 0) or (downlight_color[2] > 0)

    if any_zone_on:
        # Set colors first, then turn on if not already on
        await device.set64(
            tile_index=0,
            x=0,
            y=0,
            width=8,
            duration=duration,
            colors=colors,
        )

        if device.power_level == 0:
            # Turn on device without changing colors
            await device.set_power("on", duration=0)
    else:
        # All zones are off - turn off the device
        await device.set_power("off", duration=duration * 1000)

    # Request immediate refresh to update state
    await device.async_update()
    await coordinator.async_request_refresh()


class LIFXCeilingDownlight(LIFXCeilingEntity, LightEntity):
    """Represents the LIFX Ceiling Uplight zone."""

    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(self, coordinator: LIFXCeilingUpdateCoordinator) -> None:
        """Instantiate the zoned light."""
        super().__init__(coordinator)
        self._attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.HS}
        self._attr_name = "Downlight"
        self._attr_unique_id = f"{coordinator.data.serial}_downlight"
        self._attr_max_color_temp_kelvin = coordinator.data.max_kelvin
        self._attr_min_color_temp_kelvin = coordinator.data.min_kelvin

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""
        self._async_update_attrs()
        super()._handle_coordinator_update()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle being updated from the coordinator."""
        self._attr_is_on = self.coordinator.data.downlight_is_on
        self._attr_brightness = self.coordinator.data.downlight_brightness
        self._attr_hs_color = self.coordinator.data.downlight_hs_color
        self._attr_color_temp_kelvin = self.coordinator.data.downlight_kelvin
        _, sat = self.coordinator.data.downlight_hs_color
        if sat > 0:
            self._attr_color_mode = ColorMode.HS
        else:
            self._attr_color_mode = ColorMode.COLOR_TEMP

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the downlight."""
        duration = int(kwargs.get(ATTR_TRANSITION, 0))
        await self.coordinator.device.turn_downlight_off(duration)
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the downlight."""
        duration = int(kwargs.get(ATTR_TRANSITION, 0))
        color = hsbk_for_turn_on(self.coordinator.data.downlight_color, **kwargs)
        await self.coordinator.device.turn_downlight_on(color, duration)
        await self.coordinator.device.async_update()

        self._attr_is_on = True
        self._attr_brightness = self.coordinator.device.downlight_brightness

        if self.coordinator.device.downlight_hs_color[1] > 0:
            self._attr_color_mode = ColorMode.HS
            self._attr_hs_color = self.coordinator.device.downlight_hs_color
        else:
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_color_temp_kelvin = self.coordinator.device.downlight_kelvin

        self.async_write_ha_state()


class LIFXCeilingUplight(LIFXCeilingEntity, LightEntity):
    """Represents the LIFX Ceiling Uplight zone."""

    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(self, coordinator: LIFXCeilingUpdateCoordinator) -> None:
        """Instantiate the zoned light."""
        super().__init__(coordinator)
        self._attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.HS}
        self._attr_name = "Uplight"
        self._attr_unique_id = f"{coordinator.data.serial}_uplight"
        self._attr_max_color_temp_kelvin = coordinator.data.max_kelvin
        self._attr_min_color_temp_kelvin = coordinator.data.min_kelvin

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator updates."""
        self._async_update_attrs()
        super()._handle_coordinator_update()

    @callback
    def _async_update_attrs(self) -> None:
        """Handle being updated from the coordinator."""
        self._attr_is_on = self.coordinator.data.uplight_is_on
        self._attr_brightness = self.coordinator.data.uplight_brightness
        self._attr_hs_color = self.coordinator.data.uplight_hs_color
        self._attr_color_temp_kelvin = self.coordinator.data.uplight_kelvin
        _, sat = self.coordinator.data.uplight_hs_color
        if sat > 0:
            self._attr_color_mode = ColorMode.HS
        else:
            self._attr_color_mode = ColorMode.COLOR_TEMP

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the uplight."""
        duration = int(kwargs[ATTR_TRANSITION]) if ATTR_TRANSITION in kwargs else 0
        await self.coordinator.device.turn_uplight_off(duration)
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the uplight."""
        duration = int(kwargs[ATTR_TRANSITION]) if ATTR_TRANSITION in kwargs else 0
        color = hsbk_for_turn_on(self.coordinator.data.uplight_color, **kwargs)
        await self.coordinator.device.turn_uplight_on(color, duration)
        await self.coordinator.device.async_update()

        self._attr_is_on = True
        self._attr_brightness = self.coordinator.device.uplight_brightness

        if self.coordinator.device.uplight_hs_color[1] > 0:
            self._attr_color_mode = ColorMode.HS
            self._attr_hs_color = self.coordinator.device.uplight_hs_color
        else:
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_color_temp_kelvin = self.coordinator.device.uplight_kelvin

        self.async_write_ha_state()
