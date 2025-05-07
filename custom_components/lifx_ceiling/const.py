"""Constants for LIFX Ceiling."""

from datetime import timedelta
from logging import Logger, getLogger

_LOGGER: Logger = getLogger(__package__)

CONF_SERIAL = "serial"

DEFAULT_ATTEMPTS = 5
DOMAIN = "lifx_ceiling"

HSBK_HUE = 0
HSBK_SATURATION = 1
HSBK_BRIGHTNESS = 2
HSBK_KELVIN = 3

INVALID_DEVICE = "invalid_device"

LIFX_CEILING_PRODUCT_IDS = {176, 177, 201, 202}

OVERALL_TIMEOUT = 15

SCAN_INTERVAL = timedelta(seconds=10)

SERVICE_LIFX_CEILING_SET_STATE = "set_state"

UDP_BROADCAST_MAC = "00:00:00:00:00:00"
UDP_BROADCAST_PORT = 56700
