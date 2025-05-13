"""Support for LIFX Ceiling lights."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LIFXCeilingUpdateCoordinator

if TYPE_CHECKING:
    from .api import LIFXCeiling


class LIFXCeilingEntity(CoordinatorEntity[LIFXCeilingUpdateCoordinator]):
    """Representation of a LIFX Ceiling entity with a coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: LIFXCeilingUpdateCoordinator, device: LIFXCeiling
    ) -> None:
        """Initialise the light."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.mac_addr)},
            connections={(dr.CONNECTION_NETWORK_MAC, device.mac_addr)},
            serial_number=device.mac_addr.replace(":", "").lower(),
            manufacturer="LIFX",
            name=device.label,
            model=device.model,
            sw_version=device.host_firmware_version,
            suggested_area=device.group,
        )
