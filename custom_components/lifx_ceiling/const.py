"""Constants for LIFX Ceiling."""

from datetime import timedelta
from logging import Logger, getLogger

_LOGGER: Logger = getLogger(__package__)

ATTR_UPLIGHT = "uplight"
ATTR_POWER = "power"
ATTR_DOWNLIGHT = "downlight"

CONF_SERIAL = "serial"

DOMAIN = "lifx_ceiling"
NAME = "LIFX Ceiling"

HSBK_HUE = 0
HSBK_SATURATION = 1
HSBK_BRIGHTNESS = 2
HSBK_KELVIN = 3

DISCOVERY_INTERVAL = timedelta(minutes=5)
