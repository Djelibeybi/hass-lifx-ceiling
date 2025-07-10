"""Helpful methods."""

from __future__ import annotations

import asyncio
from functools import partial
from typing import TYPE_CHECKING, Any

import homeassistant.util.color as color_util
from homeassistant.components.lifx.const import DOMAIN as LIFX_DOMAIN
from homeassistant.components.lifx.coordinator import LIFXUpdateCoordinator
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_COLOR_NAME,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
)

from .const import (
    _LOGGER,
    DEFAULT_ATTEMPTS,
    DOMAIN,
    HSBK_BRIGHTNESS,
    HSBK_HUE,
    HSBK_KELVIN,
    HSBK_SATURATION,
    LIFX_CEILING_PRODUCT_IDS,
    OVERALL_TIMEOUT,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from aiolifx.aiolifx import Light
    from aiolifx.message import Message
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


def find_lifx_coordinators(hass: HomeAssistant) -> list[LIFXUpdateCoordinator]:
    """Find all LIFX coordinators in Home Assistant's device registry."""
    coordinators: list[LIFXUpdateCoordinator] = [
        entry.runtime_data
        for entry in hass.config_entries.async_loaded_entries(LIFX_DOMAIN)
        if hasattr(entry, "runtime_data")
        and isinstance(entry.runtime_data, LIFXUpdateCoordinator)
        and entry.runtime_data.is_matrix
        and entry.runtime_data.device.product in LIFX_CEILING_PRODUCT_IDS
    ]
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


async def async_execute_lifx(
    methods: Callable | list[Callable],
    attempts: int = DEFAULT_ATTEMPTS,
    overall_timeout: int = OVERALL_TIMEOUT,
) -> list[Message]:
    """Execute LIFX methods with retries."""
    loop = asyncio.get_running_loop()

    if not isinstance(methods, list):
        methods = [methods]

    futures: list[asyncio.Future] = [
        loop.create_future() for method in methods if callable(method)
    ]

    def _callback(
        bulb: Light, message: Message | None, future: asyncio.Future[Message]
    ) -> None:
        """Handle the response from LIFX methods."""
        if message and not future.done():
            future.set_result(message)

    timeout_per_attempt = overall_timeout / attempts

    for _ in range(attempts):
        for idx, method in enumerate(methods):
            if not callable(method):
                _LOGGER.warning("Method at index %d is not callable: %s", idx, method)
                continue
            future = futures[idx]
            if not future.done():
                method(callb=partial(_callback, future=future))

        _, pending = await asyncio.wait(futures, timeout=timeout_per_attempt)
        if not pending:
            break

    results: list[Message] = []
    failed: list[str] = []
    for idx, future in enumerate(futures):
        if not future.done() or not (result := future.result()):
            method = methods[idx]
            failed.append(str(getattr(method, "__name__", method)))
        else:
            results.append(result)

    if failed:
        msg = f"{len(failed)} requests timed out after {overall_timeout} seconds."
        raise TimeoutError(msg)
