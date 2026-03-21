"""Tests for LIFX Ceiling utility helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_COLOR_NAME,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
)

from custom_components.lifx_ceiling import util
from custom_components.lifx_ceiling.const import DOMAIN, LIFX_CEILING_PRODUCT_IDS
from custom_components.lifx_ceiling.util import (
    async_get_legacy_entries,
    find_lifx_coordinators,
    has_single_config_entry,
    hsbk_for_turn_on,
)


def test_hsbk_for_turn_on_uses_hs_color_and_percentage_brightness() -> None:
    """HS color and brightness percent should be scaled into LIFX values."""
    current = (1000, 2000, 3000, 3500)

    result = hsbk_for_turn_on(
        current,
        **{
            ATTR_HS_COLOR: (180.0, 50.0),
            ATTR_BRIGHTNESS_PCT: 25,
        },
    )

    assert result == (32767, 32767, 16448, 3500)


def test_hsbk_for_turn_on_color_temp_forces_white_mode() -> None:
    """Color temperature updates should clear saturation and preserve hue."""
    current = (1234, 4000, 5000, 3500)

    result = hsbk_for_turn_on(
        current,
        **{
            ATTR_COLOR_TEMP_KELVIN: 2700,
            ATTR_BRIGHTNESS: 10,
        },
    )

    assert result == (1234, 0, 2570, 2700)


def test_hsbk_for_turn_on_unknown_color_name_falls_back_to_white(caplog) -> None:
    """Unknown named colors should log and fall back to neutral white."""
    current = (100, 200, 300, 4000)

    result = hsbk_for_turn_on(
        current,
        **{ATTR_COLOR_NAME: "definitely-not-a-color"},
    )

    assert result == (0, 0, 300, 4000)
    assert "falling back to neutral white" in caplog.text


def test_hsbk_for_turn_on_zero_brightness_becomes_full_brightness() -> None:
    """Zero brightness means turn on at full brightness rather than staying off."""
    current = (100, 200, 300, 4000)

    result = hsbk_for_turn_on(current, **{ATTR_BRIGHTNESS: 0})

    assert result == (100, 200, 65535, 4000)


def test_find_lifx_coordinators_filters_non_ceiling_devices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return only supported LIFX ceiling coordinators."""

    class FakeLIFXUpdateCoordinator:
        """Minimal stand-in for the core LIFX coordinator."""

        def __init__(self, *, is_matrix: bool, product: int) -> None:
            """Initialise the fake coordinator."""
            self.is_matrix = is_matrix
            self.device = SimpleNamespace(product=product)

    monkeypatch.setattr(util, "LIFXUpdateCoordinator", FakeLIFXUpdateCoordinator)

    valid = FakeLIFXUpdateCoordinator(
        is_matrix=True,
        product=next(iter(LIFX_CEILING_PRODUCT_IDS)),
    )
    wrong_product = FakeLIFXUpdateCoordinator(
        is_matrix=True,
        product=999,
    )
    not_matrix = FakeLIFXUpdateCoordinator(
        is_matrix=False,
        product=next(iter(LIFX_CEILING_PRODUCT_IDS)),
    )
    missing_runtime_data = SimpleNamespace()

    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_loaded_entries=Mock(
                return_value=[
                    SimpleNamespace(runtime_data=valid),
                    SimpleNamespace(runtime_data=wrong_product),
                    SimpleNamespace(runtime_data=not_matrix),
                    missing_runtime_data,
                ]
            )
        )
    )

    assert find_lifx_coordinators(hass) == [valid]


def test_has_single_config_entry_reflects_existing_unique_id() -> None:
    """Single config entry helper should check for the domain unique id."""
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_entry_for_domain_unique_id=Mock(return_value=object())
        )
    )

    assert has_single_config_entry(hass) is True
    hass.config_entries.async_entry_for_domain_unique_id.assert_called_once_with(
        DOMAIN,
        DOMAIN,
    )


def test_async_get_legacy_entries_filters_out_singleton_entry() -> None:
    """Legacy entry helper should ignore the singleton config entry."""
    legacy_entry = SimpleNamespace(unique_id="legacy")
    singleton_entry = SimpleNamespace(unique_id=DOMAIN)
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_entries=Mock(return_value=[legacy_entry, singleton_entry])
        )
    )

    assert async_get_legacy_entries(hass) == [legacy_entry]
