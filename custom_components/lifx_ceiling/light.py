"""LIFX Ceiling Extras light."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.light import (
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)

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
    async_add_entities(
        [
            LIFXCeilingDownlight(coordinator),
            LIFXCeilingUplight(coordinator),
        ]
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

    @property
    def brightness(self) -> int:
        """Return brightness."""
        return self.coordinator.data.downlight_brightness

    @property
    def color_temp_kelvin(self) -> int:
        """Return the color temperature in kelvin."""
        return self.coordinator.data.downlight_kelvin

    @property
    def color_mode(self) -> ColorMode:
        """Return the color mode of the downlight."""
        _, sat = self.coordinator.data.downlight_hs_color
        if sat > 0:
            return ColorMode.HS
        return ColorMode.COLOR_TEMP

    @property
    def hs_color(self) -> tuple[int, int]:
        """Return hue and saturation as a tuple."""
        return self.coordinator.data.downlight_hs_color

    @property
    def is_on(self) -> bool:
        """Return true if downlight is on."""
        return self.coordinator.data.downlight_is_on

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the downlight."""
        duration = int(kwargs.get(ATTR_TRANSITION, 0))
        await self.coordinator.device.turn_downlight_off(duration)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the downlight."""
        duration = int(kwargs.get(ATTR_TRANSITION, 0))
        color = hsbk_for_turn_on(self.coordinator.data.downlight_color, **kwargs)
        await self.coordinator.device.turn_downlight_on(color, duration)


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

    @property
    def brightness(self) -> int:
        """Return brightness."""
        return self.coordinator.data.uplight_brightness

    @property
    def color_temp_kelvin(self) -> int:
        """Return the color temperature in kelvin."""
        return self.coordinator.data.uplight_kelvin

    @property
    def color_mode(self) -> ColorMode:
        """Return the color mode of the uplight."""
        _, sat = self.coordinator.data.uplight_hs_color
        if sat > 0:
            return ColorMode.HS
        return ColorMode.COLOR_TEMP

    @property
    def hs_color(self) -> tuple[int, int]:
        """Return hue and saturation as a tuple."""
        return self.coordinator.data.uplight_hs_color

    @property
    def is_on(self) -> bool:
        """Return true if uplight is on."""
        return self.coordinator.data.uplight_is_on

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the uplight."""
        duration = int(kwargs[ATTR_TRANSITION]) if ATTR_TRANSITION in kwargs else 0
        await self.coordinator.device.turn_uplight_off(duration)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the uplight."""
        duration = int(kwargs[ATTR_TRANSITION]) if ATTR_TRANSITION in kwargs else 0
        color = hsbk_for_turn_on(self.coordinator.data.uplight_color, **kwargs)
        await self.coordinator.device.turn_uplight_on(color, duration)
        await self.coordinator.async_request_refresh()
