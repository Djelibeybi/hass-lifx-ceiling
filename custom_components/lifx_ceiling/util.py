"""Helpful methods."""

from __future__ import annotations

from typing import Any

import homeassistant.util.color as color_util
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_COLOR_NAME,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
)

from .const import _LOGGER, HSBK_BRIGHTNESS, HSBK_HUE, HSBK_KELVIN, HSBK_SATURATION


def hsbk_for_turn_on(
    current: tuple[int, int, int, int],
    *,
    override_brightness: int | None = None,
    **kwargs: Any
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

    if override_brightness is not None:
        # Adjust the override brightness from 0-255 to 0-65535
        brightness = (override_brightness << 8) | override_brightness

    return hue, saturation, brightness, kelvin
