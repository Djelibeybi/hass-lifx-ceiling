"""Tests for the LIFX Ceiling coordinator."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from homeassistant.components.light import ATTR_TRANSITION
from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.exceptions import HomeAssistantError

from custom_components.lifx_ceiling import coordinator as coordinator_module
from custom_components.lifx_ceiling.api import LIFXCeiling
from custom_components.lifx_ceiling.const import (
    ATTR_DOWNLIGHT_BRIGHTNESS,
    ATTR_DOWNLIGHT_HUE,
    ATTR_DOWNLIGHT_KELVIN,
    ATTR_DOWNLIGHT_SATURATION,
    ATTR_UPLIGHT_BRIGHTNESS,
    ATTR_UPLIGHT_HUE,
    ATTR_UPLIGHT_KELVIN,
    ATTR_UPLIGHT_SATURATION,
    DOMAIN,
)
from custom_components.lifx_ceiling.coordinator import LIFXCeilingUpdateCoordinator


def _make_config_entry() -> SimpleNamespace:
    """Create a minimal config entry stub."""
    return SimpleNamespace(
        entry_id="abc123",
        async_on_unload=MagicMock(),
    )


def _make_lifx_ceiling(*, mac_addr: str = "aa:bb:cc:dd:ee:ff") -> LIFXCeiling:
    """Create a partially initialised LIFX ceiling device."""
    device = object.__new__(LIFXCeiling)
    device.mac_addr = mac_addr
    device.product = 176
    device.power_level = 0
    device.async_set64 = AsyncMock()
    device.set_power = MagicMock()
    device.turn_uplight_on = AsyncMock()
    device.turn_uplight_off = AsyncMock()
    device.turn_downlight_on = AsyncMock()
    device.turn_downlight_off = AsyncMock()
    return device


@pytest.mark.asyncio
async def test_async_update_discovers_new_ceiling_and_calls_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Coordinator discovery should cast and store new LIFX ceiling devices."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())
    core_device = SimpleNamespace(mac_addr="aa:bb")
    core_coordinator = SimpleNamespace(device=core_device)
    ceiling = _make_lifx_ceiling(mac_addr="aa:bb")
    discovered: list[LIFXCeiling] = []

    monkeypatch.setattr(
        coordinator_module,
        "find_lifx_coordinators",
        lambda hass: [core_coordinator],
    )
    monkeypatch.setattr(
        coordinator_module.LIFXCeiling,
        "cast",
        lambda device: ceiling,
    )
    coordinator.set_discovery_callback(discovered.append)

    await coordinator.async_update()

    assert coordinator.devices == [ceiling]
    assert coordinator._ceiling_coordinators["aa:bb"] is core_coordinator
    assert discovered == [ceiling]


@pytest.mark.asyncio
async def test_coordinator_accessors_and_listener_helpers() -> None:
    """Basic coordinator accessors should proxy internal state."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())
    device = _make_lifx_ceiling(mac_addr="aa:bb")
    core_coordinator = SimpleNamespace(async_add_listener=MagicMock())
    coordinator._ceilings.add(device)
    coordinator._ceiling_coordinators["aa:bb"] = core_coordinator

    def callback(device: object) -> None:
        return None

    assert coordinator.discovery_callback is None
    assert coordinator.set_discovery_callback(callback) is None
    assert coordinator.discovery_callback is callback
    assert coordinator.devices == [device]
    assert await coordinator._async_update_data() == [device]

    listener = MagicMock()
    coordinator.async_add_core_listener(device, listener)
    core_coordinator.async_add_listener.assert_called_once_with(listener)


@pytest.mark.asyncio
async def test_async_update_ignores_existing_devices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Coordinator discovery should skip already-known devices."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())
    existing = _make_lifx_ceiling(mac_addr="aa:bb")
    coordinator._ceilings.add(existing)
    coordinator._ceiling_coordinators["aa:bb"] = SimpleNamespace(device=existing)

    core_coordinator = SimpleNamespace(device=SimpleNamespace(mac_addr="aa:bb"))
    cast = MagicMock()
    monkeypatch.setattr(
        coordinator_module,
        "find_lifx_coordinators",
        lambda hass: [core_coordinator],
    )
    monkeypatch.setattr(coordinator_module.LIFXCeiling, "cast", cast)

    await coordinator.async_update()

    cast.assert_not_called()
    assert coordinator.devices == [existing]


@pytest.mark.asyncio
async def test_async_update_logs_homeassistant_errors(
    monkeypatch: pytest.MonkeyPatch,
    caplog,
) -> None:
    """Coordinator discovery should swallow Home Assistant lookup errors."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())

    def _raise_error(hass: object) -> list[object]:
        msg = "boom"
        raise HomeAssistantError(msg)

    monkeypatch.setattr(coordinator_module, "find_lifx_coordinators", _raise_error)

    await coordinator.async_update()

    assert "Error updating LIFX Ceiling coordinators: boom" in caplog.text


@pytest.mark.asyncio
async def test_async_set_state_turns_device_off_when_both_brightness_values_are_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service handler should power off a device when both zones are set to zero."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())
    device = _make_lifx_ceiling(mac_addr="aa:bb")
    coordinator._ceiling_coordinators["aa:bb"] = SimpleNamespace(device=device)
    fake_registry = SimpleNamespace(
        async_get=lambda device_id: SimpleNamespace(identifiers={(DOMAIN, "aa:bb")})
    )
    execute = AsyncMock()
    monkeypatch.setattr(coordinator_module.dr, "async_get", lambda hass: fake_registry)
    monkeypatch.setattr(coordinator_module, "async_execute_lifx", execute)

    call_data = {
        ATTR_DEVICE_ID: ["device-1"],
        ATTR_DOWNLIGHT_BRIGHTNESS: 0,
        ATTR_UPLIGHT_BRIGHTNESS: 0,
        ATTR_TRANSITION: 3,
    }
    await coordinator.async_set_state(SimpleNamespace(data=call_data))

    execute.assert_awaited_once()
    method = execute.await_args.args[0]
    assert method.keywords["value"] == "off"
    assert method.keywords["duration"] == 3
    device.async_set64.assert_not_awaited()


@pytest.mark.asyncio
async def test_async_set_state_updates_zone_colors_for_matching_device(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service handler should write both zone colors through async_set64."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())
    device = _make_lifx_ceiling(mac_addr="aa:bb")
    device.power_level = 65535
    coordinator._ceiling_coordinators["aa:bb"] = SimpleNamespace(device=device)
    fake_registry = SimpleNamespace(
        async_get=lambda device_id: SimpleNamespace(identifiers={(DOMAIN, "aa:bb")})
    )
    monkeypatch.setattr(coordinator_module.dr, "async_get", lambda hass: fake_registry)

    call_data = {
        ATTR_DEVICE_ID: "device-1",
        ATTR_TRANSITION: 4,
        ATTR_DOWNLIGHT_HUE: 180,
        ATTR_DOWNLIGHT_SATURATION: 50,
        ATTR_DOWNLIGHT_BRIGHTNESS: 25,
        ATTR_DOWNLIGHT_KELVIN: 2700,
        ATTR_UPLIGHT_HUE: 90,
        ATTR_UPLIGHT_SATURATION: 10,
        ATTR_UPLIGHT_BRIGHTNESS: 100,
        ATTR_UPLIGHT_KELVIN: 4000,
    }
    await coordinator.async_set_state(SimpleNamespace(data=call_data))

    expected_downlight = (32767, 32767, 16383, 2700)
    expected_uplight = (16383, 6553, 65535, 4000)
    device.async_set64.assert_awaited_once_with(
        colors=[expected_downlight] * 63 + [expected_uplight],
        duration=4,
        power_on=False,
    )


@pytest.mark.asyncio
async def test_async_set_state_defaults_transition_to_zero_when_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service handler should not require an explicit transition value."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())
    device = _make_lifx_ceiling(mac_addr="aa:bb")
    coordinator._ceiling_coordinators["aa:bb"] = SimpleNamespace(device=device)
    fake_registry = SimpleNamespace(
        async_get=lambda device_id: SimpleNamespace(identifiers={(DOMAIN, "aa:bb")})
    )
    monkeypatch.setattr(coordinator_module.dr, "async_get", lambda hass: fake_registry)

    await coordinator.async_set_state(
        SimpleNamespace(data={ATTR_DEVICE_ID: "device-1"})
    )

    device.async_set64.assert_awaited_once_with(
        colors=[(0, 0, 65535, 3500)] * 63 + [(0, 0, 65535, 3500)],
        duration=0,
        power_on=True,
    )


@pytest.mark.asyncio
async def test_async_set_state_ignores_unknown_device_ids(
    monkeypatch: pytest.MonkeyPatch,
    caplog,
) -> None:
    """Service handler should ignore device ids missing from the registry."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())
    fake_registry = SimpleNamespace(async_get=lambda device_id: None)
    monkeypatch.setattr(coordinator_module.dr, "async_get", lambda hass: fake_registry)

    await coordinator.async_set_state(
        SimpleNamespace(data={ATTR_DEVICE_ID: "missing", ATTR_TRANSITION: 0})
    )

    assert "Device ID missing not found in the device registry" in caplog.text


@pytest.mark.asyncio
async def test_async_set_state_warns_when_called_without_device_id(caplog) -> None:
    """Service handler should ignore calls missing device ids."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())

    await coordinator.async_set_state(SimpleNamespace(data={ATTR_TRANSITION: 0}))

    assert "Set state called with no device ID; ignoring" in caplog.text


@pytest.mark.asyncio
async def test_async_set_state_warns_for_invalid_matched_coordinator(
    monkeypatch: pytest.MonkeyPatch,
    caplog,
) -> None:
    """Service handler should warn when identifiers resolve to invalid coordinators."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())
    coordinator._ceiling_coordinators["aa:bb"] = SimpleNamespace(device=object())
    fake_registry = SimpleNamespace(
        async_get=lambda device_id: SimpleNamespace(
            identifiers={("other_domain", "ignored"), (DOMAIN, "aa:bb")}
        )
    )
    monkeypatch.setattr(coordinator_module.dr, "async_get", lambda hass: fake_registry)

    await coordinator.async_set_state(
        SimpleNamespace(data={ATTR_DEVICE_ID: "device-1", ATTR_TRANSITION: 0})
    )

    assert "matched identifier aa:bb but coordinator is invalid" in caplog.text
    assert "No valid LIFX Ceiling device found for device ID device-1" in caplog.text


@pytest.mark.asyncio
async def test_turn_helpers_refresh_after_device_calls() -> None:
    """Zone turn helper methods should request refresh after device updates."""
    hass = MagicMock()
    coordinator = LIFXCeilingUpdateCoordinator(hass, _make_config_entry())
    device = _make_lifx_ceiling(mac_addr="aa:bb")
    refresh = AsyncMock()
    coordinator._ceiling_coordinators["aa:bb"] = SimpleNamespace(
        async_request_refresh=refresh
    )

    await coordinator.turn_uplight_on(device, (1, 2, 3, 4), 5)
    await coordinator.turn_uplight_off(device, 6)
    await coordinator.turn_downlight_on(device, (7, 8, 9, 10), 11)
    await coordinator.turn_downlight_off(device, 12)

    device.turn_uplight_on.assert_awaited_once_with((1, 2, 3, 4), 5)
    device.turn_uplight_off.assert_awaited_once_with(6)
    device.turn_downlight_on.assert_awaited_once_with((7, 8, 9, 10), 11)
    device.turn_downlight_off.assert_awaited_once_with(12)
    assert refresh.await_args_list == [call(), call(), call(), call()]
