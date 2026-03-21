"""Tests for config flow helpers."""

from __future__ import annotations

import pytest

from custom_components.lifx_ceiling import config_flow


@pytest.mark.asyncio
async def test_async_has_devices_returns_true_when_core_devices_exist(
    monkeypatch,
) -> None:
    """Discovery helper should report available devices."""
    monkeypatch.setattr(config_flow, "find_lifx_coordinators", lambda hass: [object()])

    assert await config_flow._async_has_devices(object()) is True


@pytest.mark.asyncio
async def test_async_has_devices_returns_false_when_no_devices_exist(
    monkeypatch,
) -> None:
    """Discovery helper should report when there are no devices."""
    monkeypatch.setattr(config_flow, "find_lifx_coordinators", lambda hass: [])

    assert await config_flow._async_has_devices(object()) is False
