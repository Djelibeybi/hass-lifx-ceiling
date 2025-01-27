"""Constants for LIFX Ceiling."""

from datetime import timedelta
from logging import Logger, getLogger

_LOGGER: Logger = getLogger(__package__)

ATTR_UPLIGHT = "uplight"
ATTR_POWER = "power"
ATTR_DOWNLIGHT = "downlight"

CONF_SERIAL = "serial"

DOMAIN = "lifx_ceiling"

HSBK_HUE = 0
HSBK_SATURATION = 1
HSBK_BRIGHTNESS = 2
HSBK_KELVIN = 3

INVALID_DEVICE = "invalid_device"

LIFX_CEILING_PRODUCT_IDS = {176, 177, 201, 202}

SCAN_INTERVAL = timedelta(seconds=10)

UDP_BROADCAST_MAC = "00:00:00:00:00:00"
UDP_BROADCAST_PORT = 56700
