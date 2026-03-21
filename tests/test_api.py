"""Tests for the LIFX Ceiling device wrapper."""

from __future__ import annotations

import asyncio
from functools import partial
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from aiolifx.aiolifx import Light
from aiolifx.products import products_dict

from custom_components.lifx_ceiling import api
from custom_components.lifx_ceiling.api import LIFXCeiling, LIFXCeilingError


def _make_ceiling(
    *,
    product: int,
    power_level: int = 65535,
    downlight_color: tuple[int, int, int, int] = (1000, 2000, 3000, 3500),
    uplight_color: tuple[int, int, int, int] = (4000, 5000, 6000, 6500),
) -> LIFXCeiling:
    """Create a partially initialised ceiling device for property tests."""
    ceiling = object.__new__(LIFXCeiling)
    ceiling.product = product
    ceiling.power_level = power_level
    ceiling.tile_device_width = 8 if product in {176, 177} else 16
    ceiling.set64 = Mock()
    ceiling.copy_frame_buffer = Mock()
    ceiling.set_power = Mock()

    downlight_count = 63 if product in {176, 177} else 127
    ceiling.chain = [[downlight_color] * downlight_count + [uplight_color]]
    return ceiling


def test_lifx_ceiling_init_sets_up_base_light_state() -> None:
    """Initialising the ceiling should delegate to the base aiolifx light."""
    loop = asyncio.new_event_loop()
    try:
        ceiling = LIFXCeiling(loop, "aa:bb:cc:dd:ee:ff", "127.0.0.1")
    finally:
        loop.close()

    assert isinstance(ceiling, Light)
    assert ceiling.mac_addr == "aa:bb:cc:dd:ee:ff"
    assert ceiling.ip_addr == "127.0.0.1"


def test_cast_reuses_existing_light_instance() -> None:
    """Casting should mutate the existing Light instance into a LIFXCeiling."""
    loop = asyncio.new_event_loop()
    try:
        light = Light(loop, "aa:bb:cc:dd:ee:ff", "127.0.0.1")
        ceiling = LIFXCeiling.cast(light)
    finally:
        loop.close()

    assert ceiling is light
    assert isinstance(ceiling, LIFXCeiling)


def test_zone_mapping_for_64_zone_ceiling() -> None:
    """64-zone ceilings should expose the correct zone layout."""
    ceiling = _make_ceiling(product=176)

    assert ceiling.total_zones == 64
    assert ceiling.uplight_zone == 63
    assert ceiling.downlight_zones == slice(63)


def test_zone_mapping_for_128_zone_ceiling() -> None:
    """128-zone ceilings should expose the correct zone layout."""
    ceiling = _make_ceiling(product=201)

    assert ceiling.total_zones == 128
    assert ceiling.uplight_zone == 127
    assert ceiling.downlight_zones == slice(127)


def test_downlight_and_uplight_properties_scale_from_hsbk() -> None:
    """Device properties should expose Home Assistant-friendly values."""
    ceiling = _make_ceiling(
        product=176,
        downlight_color=(32767, 32767, 25700, 4000),
        uplight_color=(16384, 65535, 51400, 6500),
    )

    assert ceiling.downlight_brightness == 100
    assert ceiling.downlight_kelvin == 4000
    assert ceiling.downlight_is_on is True
    assert ceiling.uplight_brightness == 200
    assert ceiling.uplight_kelvin == 6500
    assert ceiling.uplight_is_on is True
    assert ceiling.downlight_hs_color == pytest.approx((180.0, 50.0), abs=0.01)
    assert ceiling.uplight_hs_color == pytest.approx((90.0, 100.0), abs=0.01)


def test_product_metadata_and_zone_colors_are_exposed() -> None:
    """Metadata and direct color accessors should proxy the device state."""
    downlight_zones = [(100, 200, 500, 2700), (100, 200, 1000, 2700)] * 31 + [
        (100, 200, 500, 2700)
    ]
    ceiling = _make_ceiling(
        product=176,
        downlight_color=(100, 200, 1000, 2700),
        uplight_color=(400, 500, 600, 6500),
    )
    ceiling.chain = [[*downlight_zones, (400, 500, 600, 6500)]]

    assert ceiling.min_kelvin == products_dict[176].min_kelvin
    assert ceiling.max_kelvin == products_dict[176].max_kelvin
    assert ceiling.model == products_dict[176].name
    assert ceiling.uplight_color == (400, 500, 600, 6500)
    assert ceiling.downlight_color == (100, 200, 1000, 2700)


@pytest.mark.asyncio
async def test_async_set64_rejects_wrong_number_of_colors() -> None:
    """async_set64 should validate the provided zone count."""
    ceiling = _make_ceiling(product=176)

    with pytest.raises(LIFXCeilingError, match="Expected 64 colors, got 63"):
        await ceiling.async_set64(colors=[(0, 0, 0, 3500)] * 63)


@pytest.mark.asyncio
async def test_async_set64_splits_128_zone_updates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """128-zone ceilings should send two framebuffer writes before copying."""
    ceiling = _make_ceiling(product=201)
    calls: list[Any] = []

    async def _fake_async_execute_lifx(
        methods: Any, *_args: Any, **_kwargs: Any
    ) -> list[Any]:
        calls.append(methods)
        return []

    monkeypatch.setattr(api, "async_execute_lifx", _fake_async_execute_lifx)

    colors = [(index, index, index, 3500) for index in range(128)]
    await ceiling.async_set64(colors=colors, duration=2, power_on=True)

    assert len(calls) == 3

    set64_calls = calls[0]
    assert isinstance(set64_calls, list)
    assert len(set64_calls) == 2

    first_write, second_write = set64_calls
    assert isinstance(first_write, partial)
    assert first_write.keywords["y"] == 0
    assert first_write.keywords["width"] == 16
    assert first_write.keywords["colors"] == colors[:64]

    assert isinstance(second_write, partial)
    assert second_write.keywords["y"] == 4
    assert second_write.keywords["width"] == 16
    assert second_write.keywords["colors"] == colors[64:]

    copy_call = calls[1]
    assert isinstance(copy_call, partial)
    assert copy_call.keywords["duration"] == 0

    power_call = calls[2]
    assert isinstance(power_call, partial)
    assert power_call.keywords["value"] == "on"
    assert power_call.keywords["duration"] == 2000


@pytest.mark.asyncio
async def test_async_set64_writes_single_batch_for_64_zone_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """64-zone ceilings should send one framebuffer write and copy with duration."""
    ceiling = _make_ceiling(product=176)
    calls: list[Any] = []

    async def _fake_async_execute_lifx(
        methods: Any, *_args: Any, **_kwargs: Any
    ) -> list[Any]:
        calls.append(methods)
        return []

    monkeypatch.setattr(api, "async_execute_lifx", _fake_async_execute_lifx)

    colors = [(index, index, index, 3500) for index in range(64)]
    await ceiling.async_set64(colors=colors, duration=7)

    assert len(calls) == 2
    set_call = calls[0]
    assert isinstance(set_call, partial)
    assert set_call.keywords["y"] == 0
    assert set_call.keywords["width"] == 8
    assert set_call.keywords["colors"] == colors

    copy_call = calls[1]
    assert isinstance(copy_call, partial)
    assert copy_call.keywords["duration"] == 7


@pytest.mark.asyncio
async def test_turn_uplight_on_preserves_existing_downlight_when_powered() -> None:
    """Turning the uplight on while powered should keep the current downlight state."""
    ceiling = _make_ceiling(product=176, power_level=65535)
    ceiling.async_set64 = AsyncMock()
    color = (1, 2, 3, 4)

    await ceiling.turn_uplight_on(color, duration=5)

    expected_colors = ceiling.chain[0][ceiling.downlight_zones] + [color]
    ceiling.async_set64.assert_awaited_once_with(
        colors=expected_colors,
        duration=5,
        power_on=False,
    )


@pytest.mark.asyncio
async def test_turn_uplight_on_zeroes_downlight_when_device_is_off() -> None:
    """Turning the uplight on from off should zero the downlight zones first."""
    ceiling = _make_ceiling(product=176, power_level=0)
    ceiling.async_set64 = AsyncMock()
    color = (1, 2, 3, 4)

    await ceiling.turn_uplight_on(color, duration=5)

    expected_downlight = [
        (h, s, 0, k) for h, s, _, k in ceiling.chain[0][ceiling.downlight_zones]
    ]
    ceiling.async_set64.assert_awaited_once_with(
        colors=[*expected_downlight, color],
        duration=5,
        power_on=True,
    )


@pytest.mark.asyncio
async def test_turn_uplight_off_dim_only_when_downlight_is_on() -> None:
    """Turning the uplight off should keep the downlight powered when active."""
    ceiling = _make_ceiling(product=176, power_level=65535)
    ceiling.async_set64 = AsyncMock()

    await ceiling.turn_uplight_off(duration=2)

    expected_colors = [
        *ceiling.chain[0][ceiling.downlight_zones],
        (4000, 5000, 0, 6500),
    ]
    ceiling.async_set64.assert_awaited_once_with(colors=expected_colors, duration=2)


@pytest.mark.asyncio
async def test_turn_uplight_off_powers_device_down_when_downlight_is_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Turning the uplight off should power the whole device off if needed."""
    ceiling = _make_ceiling(
        product=176,
        power_level=65535,
        downlight_color=(1000, 2000, 0, 3500),
    )
    execute = AsyncMock()
    monkeypatch.setattr(api, "async_execute_lifx", execute)

    await ceiling.turn_uplight_off(duration=2)

    execute.assert_awaited_once()
    method = execute.await_args.args[0]
    assert isinstance(method, partial)
    assert method.keywords["value"] == "off"
    assert method.keywords["duration"] == 2000


@pytest.mark.asyncio
async def test_turn_downlight_on_preserves_uplight_when_powered() -> None:
    """Turning the downlight on while powered should keep the uplight color."""
    ceiling = _make_ceiling(product=176, power_level=65535)
    ceiling.async_set64 = AsyncMock()
    color = (1, 2, 3, 4)

    await ceiling.turn_downlight_on(color, duration=6)

    ceiling.async_set64.assert_awaited_once_with(
        colors=[color] * 63 + [ceiling.chain[0][ceiling.uplight_zone]],
        duration=6,
        power_on=False,
    )


@pytest.mark.asyncio
async def test_turn_downlight_on_zeroes_uplight_when_device_is_off() -> None:
    """Turning the downlight on from off should zero the uplight first."""
    ceiling = _make_ceiling(product=176, power_level=0)
    ceiling.async_set64 = AsyncMock()
    color = (1, 2, 3, 4)

    await ceiling.turn_downlight_on(color, duration=6)

    ceiling.async_set64.assert_awaited_once_with(
        colors=[color] * 63 + [(4000, 5000, 0, 6500)],
        duration=6,
        power_on=True,
    )


@pytest.mark.asyncio
async def test_turn_downlight_off_dim_only_when_uplight_is_on() -> None:
    """Turning the downlight off should keep the uplight lit when active."""
    ceiling = _make_ceiling(product=176, power_level=65535)
    ceiling.async_set64 = AsyncMock()

    await ceiling.turn_downlight_off(duration=4)

    expected_downlight = [
        (h, s, 0, k) for h, s, _, k in ceiling.chain[0][ceiling.downlight_zones]
    ]
    ceiling.async_set64.assert_awaited_once_with(
        colors=[*expected_downlight, ceiling.chain[0][ceiling.uplight_zone]],
        duration=4,
    )


@pytest.mark.asyncio
async def test_turn_downlight_off_powers_device_down_when_uplight_is_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Turning the downlight off should power the device down when nothing is lit."""
    ceiling = _make_ceiling(
        product=176,
        power_level=65535,
        uplight_color=(4000, 5000, 0, 6500),
    )
    execute = AsyncMock()
    monkeypatch.setattr(api, "async_execute_lifx", execute)

    await ceiling.turn_downlight_off(duration=4)

    execute.assert_awaited_once()
    method = execute.await_args.args[0]
    assert isinstance(method, partial)
    assert method.keywords["value"] == "off"
    assert method.keywords["duration"] == 4000
