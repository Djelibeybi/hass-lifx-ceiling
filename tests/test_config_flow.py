"""Tests for config flow helpers."""

from __future__ import annotations

import pytest

from custom_components.lifx_ceiling import config_flow
from custom_components.lifx_ceiling.const import ISSUE_REPLACED_BY_CORE


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


@pytest.mark.asyncio
async def test_user_step_aborts_when_replaced_by_core(monkeypatch) -> None:
    """The config flow should refuse setup on Home Assistant 2026.10+."""
    monkeypatch.setattr(config_flow, "is_replaced_by_core", lambda: True)
    flow = config_flow.LIFXCeilingConfigFlow()
    flow.async_abort = lambda *, reason: {"type": "abort", "reason": reason}

    result = await flow.async_step_user()

    assert result == {"type": "abort", "reason": ISSUE_REPLACED_BY_CORE}
