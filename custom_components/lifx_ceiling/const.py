"""Constants for LIFX Ceiling."""

from datetime import timedelta
from logging import Logger, getLogger

_LOGGER: Logger = getLogger(__package__)

ATTR_DOWNLIGHT_HUE = "downlight_hue"
ATTR_DOWNLIGHT_SATURATION = "downlight_saturation"
ATTR_DOWNLIGHT_BRIGHTNESS = "downlight_brightness"
ATTR_DOWNLIGHT_KELVIN = "downlight_kelvin"

ATTR_UPLIGHT_HUE = "uplight_hue"
ATTR_UPLIGHT_SATURATION = "uplight_saturation"
ATTR_UPLIGHT_BRIGHTNESS = "uplight_brightness"
ATTR_UPLIGHT_KELVIN = "uplight_kelvin"

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

SERVICE_LIFX_CEILING_SET_STATE = "set_state"

RUNTIME_DATA_HASS_VERSION = "2025.7.0"
