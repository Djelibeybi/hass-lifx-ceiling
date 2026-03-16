"""LIFX Ceiling Extras light."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.light import (
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import format_mac

from .entity import LIFXCeilingEntity
from .util import hsbk_for_turn_on

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .api import LIFXCeiling
    from .coordinator import (
        LIFXCeilingConfigEntry,
        LIFXCeilingUpdateCoordinator,
    )

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LIFXCeilingConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up LIFX Ceiling extra lights."""
    coordinator: LIFXCeilingUpdateCoordinator = entry.runtime_data

    @callback
    def _add_ceiling_entities(device: LIFXCeiling) -> None:
        async_add_entities(
            [
                LIFXCeilingDownlight(coordinator, device),
                LIFXCeilingUplight(coordinator, device),
            ]
        )

    for device in coordinator.devices:
        _add_ceiling_entities(device)

    coordinator.set_discovery_callback(_add_ceiling_entities)


class LIFXCeilingDownlight(LIFXCeilingEntity, LightEntity):
    """Represents the LIFX Ceiling downlight zone."""

    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(
        self, coordinator: LIFXCeilingUpdateCoordinator, device: LIFXCeiling
    ) -> None:
        """Instantiate the zoned light."""
        super().__init__(coordinator, device)
        self._device = device
        coordinator.async_add_core_listener(device, self._update_callback)

        self._attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.HS}
        self._attr_name = "Downlight"
        self._attr_unique_id = f"{format_mac(device.mac_addr)}_downlight"
        self._attr_max_color_temp_kelvin = device.max_kelvin
        self._attr_min_color_temp_kelvin = device.min_kelvin

    @callback
    def _update_callback(self) -> None:
        """Handle coordinator updates."""
        self._attr_is_on = self.coordinator.get_downlight_is_on(self._device)
        # Use stored color for brightness when off, hardware state when on
        if self._attr_is_on:
            self._attr_brightness = self._device.downlight_brightness
        else:
            _, _, brightness, _ = self.coordinator.get_downlight_color(self._device)
            self._attr_brightness = brightness >> 8
        self._attr_hs_color = self._device.downlight_hs_color
        self._attr_color_temp_kelvin = self._device.downlight_kelvin
        _, sat = self._device.downlight_hs_color
        if sat > 0:
            self._attr_color_mode = ColorMode.HS
        else:
            self._attr_color_mode = ColorMode.COLOR_TEMP
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the downlight."""
        duration = int(kwargs.get(ATTR_TRANSITION, 0))
        await self.coordinator.turn_downlight_off(self._device, duration)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the downlight."""
        duration = int(kwargs.get(ATTR_TRANSITION, 0))
        # Use stored color as base instead of hardware state
        stored_color = self.coordinator.get_downlight_color(self._device)

        # Check if light is currently off (virtual state)
        is_on = self.coordinator.get_downlight_is_on(self._device)

        if not is_on:
            # Light is off - check if this is just a brightness/color adjustment
            # (no actual turn-on intent) vs an explicit turn-on request.
            # is_adjustment_only is True when kwargs has values AND all keys are
            # color/brightness related (no unknown keys that might indicate intent)
            color_brightness_keys = {
                ATTR_TRANSITION,
                "brightness",
                "brightness_pct",
                "hs_color",
                "color_temp_kelvin",
                "color_name",
            }
            is_adjustment_only = bool(
                kwargs and not any(k not in color_brightness_keys for k in kwargs)
            )

            if is_adjustment_only:
                # Just storing brightness/color, not turning on
                color = hsbk_for_turn_on(stored_color, **kwargs)
                self.coordinator.set_downlight_color(self._device, color)
                self.async_write_ha_state()
                return

            # Explicit turn-on: use stored color directly, applying any kwargs
            # but don't let hsbk_for_turn_on override 0 brightness to 100%
            if kwargs:
                color = hsbk_for_turn_on(stored_color, **kwargs)
            else:
                # No kwargs - use stored color directly
                color = stored_color
                # If stored brightness is 0, use a sensible default
                if color[2] == 0:
                    color = (color[0], color[1], 65535, color[3])

            self.coordinator.set_downlight_color(self._device, color)
        else:
            color = hsbk_for_turn_on(stored_color, **kwargs)

        await self.coordinator.turn_downlight_on(self._device, color, duration)
        self.async_write_ha_state()


class LIFXCeilingUplight(LIFXCeilingEntity, LightEntity):
    """Represents the LIFX Ceiling uplight zone."""

    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(
        self, coordinator: LIFXCeilingUpdateCoordinator, device: LIFXCeiling
    ) -> None:
        """Instantiate the zoned light."""
        super().__init__(coordinator, device)
        self._device = device
        coordinator.async_add_core_listener(device, self._update_callback)

        self._attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.HS}
        self._attr_name = "Uplight"
        self._attr_unique_id = f"{format_mac(device.mac_addr)}_uplight"
        self._attr_max_color_temp_kelvin = device.max_kelvin
        self._attr_min_color_temp_kelvin = device.min_kelvin

    @callback
    def _update_callback(self) -> None:
        """Handle device updates."""
        self._attr_is_on = self.coordinator.get_uplight_is_on(self._device)
        # Use stored color for brightness when off, hardware state when on
        if self._attr_is_on:
            self._attr_brightness = self._device.uplight_brightness
        else:
            _, _, brightness, _ = self.coordinator.get_uplight_color(self._device)
            self._attr_brightness = brightness >> 8
        self._attr_hs_color = self._device.uplight_hs_color
        self._attr_color_temp_kelvin = self._device.uplight_kelvin
        _, sat = self._device.uplight_hs_color
        if sat > 0:
            self._attr_color_mode = ColorMode.HS
        else:
            self._attr_color_mode = ColorMode.COLOR_TEMP
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the uplight."""
        duration = int(kwargs[ATTR_TRANSITION]) if ATTR_TRANSITION in kwargs else 0
        await self.coordinator.turn_uplight_off(self._device, duration)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the uplight."""
        duration = int(kwargs[ATTR_TRANSITION]) if ATTR_TRANSITION in kwargs else 0
        # Use stored color as base instead of hardware state
        stored_color = self.coordinator.get_uplight_color(self._device)

        # Check if light is currently off (virtual state)
        is_on = self.coordinator.get_uplight_is_on(self._device)

        if not is_on:
            # Light is off - check if this is just a brightness/color adjustment
            # (no actual turn-on intent) vs an explicit turn-on request.
            # is_adjustment_only is True when kwargs has values AND all keys are
            # color/brightness related (no unknown keys that might indicate intent)
            color_brightness_keys = {
                ATTR_TRANSITION,
                "brightness",
                "brightness_pct",
                "hs_color",
                "color_temp_kelvin",
                "color_name",
            }
            is_adjustment_only = bool(
                kwargs and not any(k not in color_brightness_keys for k in kwargs)
            )

            if is_adjustment_only:
                # Just storing brightness/color, not turning on
                color = hsbk_for_turn_on(stored_color, **kwargs)
                self.coordinator.set_uplight_color(self._device, color)
                self.async_write_ha_state()
                return

            # Explicit turn-on: use stored color directly, applying any kwargs
            # but don't let hsbk_for_turn_on override 0 brightness to 100%
            if kwargs:
                color = hsbk_for_turn_on(stored_color, **kwargs)
            else:
                # No kwargs - use stored color directly
                color = stored_color
                # If stored brightness is 0, use a sensible default
                if color[2] == 0:
                    color = (color[0], color[1], 65535, color[3])

            self.coordinator.set_uplight_color(self._device, color)
        else:
            color = hsbk_for_turn_on(stored_color, **kwargs)

        await self.coordinator.turn_uplight_on(self._device, color, duration)
        self.async_write_ha_state()
