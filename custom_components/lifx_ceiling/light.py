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

from .entity import LIFXCeilingEntity
from .util import hsbk_for_turn_on

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import LIFXCeilingConfigEntry, LIFXCeilingUpdateCoordinator

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LIFXCeilingConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LIFX Ceiling extra lights."""
    coordinator = entry.runtime_data
    await coordinator.device.async_update()

    async_add_entities(
        [
            LIFXCeilingDownlight(coordinator),
            LIFXCeilingUplight(coordinator),
        ],
        update_before_add=True,
    )


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
