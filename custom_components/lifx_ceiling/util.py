"""Helpful methods."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import homeassistant.util.color as color_util
from awesomeversion import AwesomeVersion
from homeassistant.components.lifx.const import DOMAIN as LIFX_DOMAIN
from homeassistant.components.lifx.const import LIFX_CEILING_PRODUCT_IDS
from homeassistant.components.lifx.coordinator import LIFXUpdateCoordinator
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_COLOR_NAME,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
)
from homeassistant.const import MAJOR_VERSION, MINOR_VERSION

from .const import (
    _LOGGER,
    DOMAIN,
    HSBK_BRIGHTNESS,
    HSBK_HUE,
    HSBK_KELVIN,
    HSBK_SATURATION,
    RUNTIME_DATA_HASS_VERSION,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


def find_lifx_coordinators(hass: HomeAssistant) -> list[LIFXUpdateCoordinator]:
    """Find all LIFX coordinators in Home Assistant's device registry."""
    if AwesomeVersion(f"{MAJOR_VERSION}.{MINOR_VERSION}") < AwesomeVersion(
        RUNTIME_DATA_HASS_VERSION
    ):
        # For versions before 2025.7.0, we need to use the legacy hass.data storage
        possible = list(hass.data[LIFX_DOMAIN].values())
    else:
        # For versions 2025.7.0 and later, we can use the new entry runtime_data
        possible = [
            entry.runtime_data
            for entry in hass.config_entries.async_loaded_entries(LIFX_DOMAIN)
        ]

    coordinators: list[LIFXUpdateCoordinator] = [
        coordinator
        for coordinator in possible
        if (
            isinstance(coordinator, LIFXUpdateCoordinator)
            and (
                coordinator.is_matrix
                and coordinator.device.product in LIFX_CEILING_PRODUCT_IDS
            )
        )
    ]

    _LOGGER.debug(
        "Found %d LIFX Ceiling coordinators: %s",
        len(coordinators),
        [coordinator.device.mac_addr for coordinator in coordinators],
    )

    return coordinators


def has_single_config_entry(hass: HomeAssistant) -> bool:
    """Return if there is a single config entry for the integration."""
    return (
        hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, DOMAIN) is not None
    )


def async_get_legacy_entries(hass: HomeAssistant) -> list[ConfigEntry]:
    """Get the legacy config entry if it exists."""
    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.unique_id != DOMAIN
    ]


def hsbk_for_turn_on(
    current: tuple[int, int, int, int], **kwargs: Any
) -> tuple[int, int, int, int]:
    """Return merged HSBK tuple from current color and Home Assistant kwargs."""
    hue, saturation, brightness, kelvin = [None] * 4

    if (color_name := kwargs.get(ATTR_COLOR_NAME)) is not None:
        try:
            hue, saturation = color_util.color_RGB_to_hs(
                *color_util.color_name_to_rgb(color_name)
            )
        except ValueError:
            _LOGGER.warning(
                "Got unknown color %s, falling back to neutral white", color_name
            )
            hue, saturation = (0, 0)

    if ATTR_HS_COLOR in kwargs:
        hue, saturation = kwargs[ATTR_HS_COLOR]

    if hue is not None and saturation is not None:
        hue = int(hue / 360 * 65535)
        saturation = int(saturation / 100 * 65535)
        kelvin = 3500
    else:
        hue = current[HSBK_HUE]
        saturation = current[HSBK_SATURATION]

    if ATTR_COLOR_TEMP_KELVIN in kwargs:
        kelvin = kwargs.pop(ATTR_COLOR_TEMP_KELVIN)
        saturation = 0
    else:
        kelvin = current[HSBK_KELVIN]

    if ATTR_BRIGHTNESS in kwargs:
        scaled_brightness = kwargs[ATTR_BRIGHTNESS]
        brightness = (scaled_brightness << 8) | scaled_brightness

    if ATTR_BRIGHTNESS_PCT in kwargs:
        scaled_brightness = round(255 * kwargs[ATTR_BRIGHTNESS_PCT] / 100)
        brightness = (scaled_brightness << 8) | scaled_brightness

    if brightness is None:
        brightness = current[HSBK_BRIGHTNESS]

    if brightness == 0:
        brightness = 65535

    return hue, saturation, brightness, kelvin
