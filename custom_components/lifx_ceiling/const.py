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

DEFAULT_ATTEMPTS = 3
OVERALL_TIMEOUT = 5

DOMAIN = "lifx_ceiling"
NAME = "LIFX Ceiling"

HSBK_HUE = 0
HSBK_SATURATION = 1
HSBK_BRIGHTNESS = 2
HSBK_KELVIN = 3

DISCOVERY_INTERVAL = timedelta(minutes=5)

LIFX_CEILING_PRODUCT_IDS = {176, 177, 201, 202}
LIFX_CEILING_64ZONES_PRODUCT_IDS = {176, 177}
LIFX_CEILING_128ZONES_PRODUCT_IDS = {201, 202}

SERVICE_LIFX_CEILING_SET_STATE = "set_state"

RUNTIME_DATA_HASS_VERSION = "2025.7.0"
