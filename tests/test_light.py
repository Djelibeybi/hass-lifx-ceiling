"""Tests for the LIFX Ceiling light entities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.light import (
    ATTR_BRIGHTNESS_PCT,
    ATTR_TRANSITION,
    ColorMode,
)

from custom_components.lifx_ceiling.light import (
    LIFXCeilingDownlight,
    LIFXCeilingUplight,
    async_setup_entry,
)


@dataclass
class FakeCeilingDevice:
    """Test double for a LIFX ceiling device."""

    mac_addr: str = "AA:BB:CC:DD:EE:FF"
    label: str = "Kitchen"
    group: str = "Kitchen"
    host_firmware_version: str = "1.0"
    model: str = "Ceiling"
    min_kelvin: int = 1500
    max_kelvin: int = 9000
    downlight_is_on: bool = True
    downlight_brightness: int = 120
    downlight_hs_color: tuple[float, float] = (120.0, 75.0)
    downlight_kelvin: int = 3500
    downlight_color: tuple[int, int, int, int] = (2000, 3000, 4000, 3500)
    uplight_is_on: bool = True
    uplight_brightness: int = 180
    uplight_hs_color: tuple[float, float] = (45.0, 0.0)
    uplight_kelvin: int = 4000
    uplight_color: tuple[int, int, int, int] = (5000, 0, 6000, 4000)


class FakeCoordinator:
    """Test double for the integration coordinator."""

    def __init__(self, devices: list[FakeCeilingDevice]) -> None:
        """Initialise the fake coordinator."""
        self.devices = devices
        self.listeners: list[tuple[FakeCeilingDevice, object]] = []
        self.data = None
        self.last_update_success = True
        self.name = "LIFX Ceiling"
        self.set_discovery_callback = MagicMock(
            side_effect=self._set_discovery_callback
        )
        self.turn_downlight_on = AsyncMock()
        self.turn_downlight_off = AsyncMock()
        self.turn_uplight_on = AsyncMock()
        self.turn_uplight_off = AsyncMock()
        self.discovery_callback = None

    def async_add_listener(self, update_callback: object) -> Callable[[], None]:
        """Provide the minimal interface CoordinatorEntity expects."""
        del update_callback

        def _remove_listener() -> None:
            return None

        return _remove_listener

    def async_add_core_listener(
        self, device: FakeCeilingDevice, callback: object
    ) -> None:
        """Record listeners registered by light entities."""
        self.listeners.append((device, callback))

    def _set_discovery_callback(self, callback: object) -> None:
        """Store the discovery callback registered during setup."""
        self.discovery_callback = callback


@pytest.mark.asyncio
async def test_async_setup_entry_adds_both_zone_entities() -> None:
    """Setup should create both zone entities for each discovered ceiling."""
    device = FakeCeilingDevice()
    coordinator = FakeCoordinator([device])
    entry = SimpleNamespace(runtime_data=coordinator)
    entities = []

    def _async_add_entities(new_entities: list[object]) -> None:
        entities.extend(new_entities)

    await async_setup_entry(
        hass=MagicMock(),
        entry=entry,
        async_add_entities=_async_add_entities,
    )

    assert len(entities) == 2
    assert isinstance(entities[0], LIFXCeilingDownlight)
    assert isinstance(entities[1], LIFXCeilingUplight)
    assert coordinator.discovery_callback is not None


def test_downlight_update_callback_sets_hs_mode() -> None:
    """The downlight should expose HS mode when saturation is non-zero."""
    coordinator = FakeCoordinator([FakeCeilingDevice()])
    entity = LIFXCeilingDownlight(coordinator, coordinator.devices[0])
    entity.async_write_ha_state = MagicMock()

    entity._update_callback()

    assert entity.is_on is True
    assert entity.brightness == 120
    assert entity.hs_color == (120.0, 75.0)
    assert entity.color_temp_kelvin == 3500
    assert entity.color_mode is ColorMode.HS
    entity.async_write_ha_state.assert_called_once()


def test_downlight_update_callback_sets_color_temp_mode() -> None:
    """The downlight should expose color temperature mode when saturation is zero."""
    coordinator = FakeCoordinator([FakeCeilingDevice(downlight_hs_color=(120.0, 0.0))])
    entity = LIFXCeilingDownlight(coordinator, coordinator.devices[0])
    entity.async_write_ha_state = MagicMock()

    entity._update_callback()

    assert entity.color_mode is ColorMode.COLOR_TEMP
    entity.async_write_ha_state.assert_called_once()


def test_uplight_update_callback_sets_color_temp_mode() -> None:
    """The uplight should expose color temperature mode when saturation is zero."""
    coordinator = FakeCoordinator([FakeCeilingDevice()])
    entity = LIFXCeilingUplight(coordinator, coordinator.devices[0])
    entity.async_write_ha_state = MagicMock()

    entity._update_callback()

    assert entity.is_on is True
    assert entity.brightness == 180
    assert entity.hs_color == (45.0, 0.0)
    assert entity.color_temp_kelvin == 4000
    assert entity.color_mode is ColorMode.COLOR_TEMP
    entity.async_write_ha_state.assert_called_once()


def test_uplight_update_callback_sets_hs_mode() -> None:
    """The uplight should expose HS mode when saturation is non-zero."""
    coordinator = FakeCoordinator([FakeCeilingDevice(uplight_hs_color=(45.0, 25.0))])
    entity = LIFXCeilingUplight(coordinator, coordinator.devices[0])
    entity.async_write_ha_state = MagicMock()

    entity._update_callback()

    assert entity.color_mode is ColorMode.HS
    entity.async_write_ha_state.assert_called_once()


@pytest.mark.asyncio
async def test_downlight_turn_off_defaults_transition_to_zero() -> None:
    """Turning off the downlight without a transition should use zero seconds."""
    device = FakeCeilingDevice()
    coordinator = FakeCoordinator([device])
    entity = LIFXCeilingDownlight(coordinator, device)

    await entity.async_turn_off()

    coordinator.turn_downlight_off.assert_awaited_once_with(device, 0)


@pytest.mark.asyncio
async def test_downlight_turn_on_passes_merged_hsbk_to_coordinator() -> None:
    """Turning on the downlight should use the helper-generated HSBK tuple."""
    device = FakeCeilingDevice()
    coordinator = FakeCoordinator([device])
    entity = LIFXCeilingDownlight(coordinator, device)
    entity.async_write_ha_state = MagicMock()

    await entity.async_turn_on(**{ATTR_BRIGHTNESS_PCT: 25, ATTR_TRANSITION: 3})

    coordinator.turn_downlight_on.assert_awaited_once_with(
        device,
        (2000, 3000, 16448, 3500),
        3,
    )
    entity.async_write_ha_state.assert_called_once()


@pytest.mark.asyncio
async def test_uplight_turn_off_uses_transition_duration() -> None:
    """Turning off the uplight should forward the transition to the coordinator."""
    device = FakeCeilingDevice()
    coordinator = FakeCoordinator([device])
    entity = LIFXCeilingUplight(coordinator, device)
    entity.async_write_ha_state = MagicMock()

    await entity.async_turn_off(**{ATTR_TRANSITION: 5})

    coordinator.turn_uplight_off.assert_awaited_once_with(device, 5)
    entity.async_write_ha_state.assert_called_once()


@pytest.mark.asyncio
async def test_uplight_turn_on_defaults_transition_to_zero() -> None:
    """Turning on the uplight without a transition should default to zero."""
    device = FakeCeilingDevice()
    coordinator = FakeCoordinator([device])
    entity = LIFXCeilingUplight(coordinator, device)
    entity.async_write_ha_state = MagicMock()

    await entity.async_turn_on()

    coordinator.turn_uplight_on.assert_awaited_once_with(
        device,
        device.uplight_color,
        0,
    )
    entity.async_write_ha_state.assert_called_once()
