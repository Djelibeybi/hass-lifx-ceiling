# Project Overview

## Purpose
This is a Home Assistant custom integration that provides independent control of uplight and downlight zones for LIFX Ceiling devices.

## Key Features
- Creates two separate light entities per LIFX Ceiling device (uplight and downlight)
- Allows independent control of each zone with full color/brightness/kelvin support
- Provides a `lifx_ceiling.set_state` service to set both zones simultaneously
- Automatically discovers LIFX Ceiling devices from the core LIFX integration
- Supports both 64-zone (product IDs 176, 177) and 128-zone (product IDs 201, 202) models

## Dependencies
- Depends on Home Assistant's core LIFX integration
- Requires at least one LIFX Ceiling device configured via core LIFX integration
- Uses aiolifx library for LIFX protocol communication

## Distribution
- Distributed via HACS (Home Assistant Community Store)
- Minimum Home Assistant version: 2025.8.0
- Integration type: hub (single config entry for all devices)
