"""Tests for integration setup and unload."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import custom_components.lifx_ceiling as integration
from custom_components.lifx_ceiling.const import (
    DISCOVERY_INTERVAL,
    DOMAIN,
    NAME,
)


@pytest.mark.asyncio
async def test_async_setup_skips_migration_without_legacy_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Setup should do nothing when no legacy entries exist."""
    hass = SimpleNamespace()
    monkeypatch.setattr(integration, "async_get_legacy_entries", lambda hass: [])

    assert await integration.async_setup(hass, {}) is True


@pytest.mark.asyncio
async def test_async_setup_migrates_first_legacy_entry_and_removes_rest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Setup should migrate one entry and remove any remaining legacy entries."""
    entry_one = SimpleNamespace(entry_id="entry-1", title="Old one")
    entry_two = SimpleNamespace(entry_id="entry-2", title="Old two")
    legacy_entries = [entry_one, entry_two]

    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_update_entry=MagicMock(return_value=True),
            async_remove=AsyncMock(),
        )
    )
    monkeypatch.setattr(
        integration,
        "async_get_legacy_entries",
        lambda hass: legacy_entries,
    )
    monkeypatch.setattr(integration, "has_single_config_entry", lambda hass: False)

    assert await integration.async_setup(hass, {}) is True

    hass.config_entries.async_update_entry.assert_called_once_with(
        entry_one,
        data={},
        options={},
        title=NAME,
        unique_id=DOMAIN,
    )
    hass.config_entries.async_remove.assert_awaited_once_with("entry-2")


@pytest.mark.asyncio
async def test_async_setup_entry_registers_services_and_periodic_updates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Entry setup should initialise the coordinator and service handler."""

    class FakeCoordinator:
        """Minimal coordinator test double."""

        def __init__(self, hass: object, config_entry: object) -> None:
            self.hass = hass
            self.config_entry = config_entry
            self.stop_discovery = None
            self.async_update = AsyncMock()
            self.async_set_state = AsyncMock()

    stop_discovery = MagicMock()
    tracked: dict[str, object] = {}

    def _fake_track_time_interval(
        hass: object,
        action: object,
        interval: object,
    ) -> MagicMock:
        tracked["hass"] = hass
        tracked["action"] = action
        tracked["interval"] = interval
        return stop_discovery

    monkeypatch.setattr(integration, "LIFXCeilingUpdateCoordinator", FakeCoordinator)
    monkeypatch.setattr(
        integration,
        "async_track_time_interval",
        _fake_track_time_interval,
    )

    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_forward_entry_setups=AsyncMock()),
        services=SimpleNamespace(async_register=MagicMock()),
    )
    entry = SimpleNamespace(runtime_data=None)

    assert await integration.async_setup_entry(hass, entry) is True

    coordinator = entry.runtime_data
    assert isinstance(coordinator, FakeCoordinator)
    coordinator.async_update.assert_awaited_once_with()
    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        entry,
        integration.PLATFORMS,
    )
    hass.services.async_register.assert_called_once()
    assert coordinator.stop_discovery is stop_discovery
    assert tracked["hass"] is hass
    assert tracked["interval"] == DISCOVERY_INTERVAL

    handler = hass.services.async_register.call_args.args[2]
    call = SimpleNamespace(data={"example": "value"})
    await handler(call)
    coordinator.async_set_state.assert_awaited_once_with(call)

    periodic_update = tracked["action"]
    now = object()
    await periodic_update(now)
    coordinator.async_update.assert_awaited_with(now)


@pytest.mark.asyncio
async def test_async_unload_entry_stops_discovery_and_unloads_platforms() -> None:
    """Unload should stop discovery callbacks and unload platforms."""
    stop_discovery = MagicMock()
    coordinator = SimpleNamespace(stop_discovery=stop_discovery)
    entry = SimpleNamespace(runtime_data=coordinator)
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_unload_platforms=AsyncMock(return_value=True)
        )
    )

    assert await integration.async_unload_entry(hass, entry) is True

    stop_discovery.assert_called_once_with()
    hass.config_entries.async_unload_platforms.assert_awaited_once_with(
        entry,
        integration.PLATFORMS,
    )
