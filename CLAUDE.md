# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration that adds independent light entities for the uplight and downlight zones of LIFX Ceiling devices. The integration depends on the core LIFX integration and discovers LIFX Ceiling devices already configured in Home Assistant.

## Development Commands

### Linting and Formatting
```bash
# Run Ruff linter
ruff check .

# Run Ruff formatter
ruff format .

# Check formatting without making changes
ruff format . --check
```

### Testing with Home Assistant
The `config/` directory contains a minimal Home Assistant configuration for testing the integration. To run Home Assistant with this integration for testing:

```bash
# Run Home Assistant directly (from the repository root)
hass -c config
```

### Installation
```bash
# Install dependencies (use uv as per user preferences)
uv pip install -r requirements.txt
```

## Architecture

### Core Components

**LIFXCeiling (api.py)**: Extended Light class from aiolifx that adds uplight/downlight zone control. Key implementation details:
- LIFX Ceiling products have either 64 zones (product IDs 176, 177) or 128 zones (product IDs 201, 202)
- The last zone (index 63 or 127) is the uplight
- All preceding zones are downlight zones
- Uses framebuffer operations (`set64`, `copy_frame_buffer`) to set zone colors
- For 128-zone devices, colors are set in two 64-color batches (y=0 and y=4)

**LIFXCeilingUpdateCoordinator (coordinator.py)**: Manages discovery and state coordination
- Discovers LIFX Ceiling devices from core LIFX integration using `find_lifx_coordinators()`
- Maintains references to core LIFX coordinators for each ceiling device
- Casts core LIFX Light objects to LIFXCeiling objects using `LIFXCeiling.cast()`
- Provides high-level control methods (turn_uplight_on/off, turn_downlight_on/off)
- Handles the `lifx_ceiling.set_state` service call

**Light Entities (light.py)**: Two entities per device
- `LIFXCeilingDownlight`: Controls zones 0-62 (or 0-126 for 128-zone)
- `LIFXCeilingUplight`: Controls the last zone (63 or 127)
- Each entity listens to the core LIFX coordinator for state updates
- Supports ColorMode.HS and ColorMode.COLOR_TEMP

### Integration Flow

1. **Setup**: `async_setup()` migrates legacy per-device entries to a single config entry
2. **Discovery**: Coordinator uses `find_lifx_coordinators()` to find LIFX Ceiling devices from core integration
3. **Casting**: Core LIFX `Light` objects are cast to `LIFXCeiling` using class replacement pattern
4. **Entity Creation**: Two light entities created per device via discovery callback
5. **State Updates**: Entities listen to core LIFX coordinators for state changes

### Key Utilities (util.py)

- `find_lifx_coordinators()`: Finds LIFX Ceiling coordinators by checking `is_matrix` and product IDs
- `async_execute_lifx()`: Executes aiolifx methods with retry logic and timeout handling
- `hsbk_for_turn_on()`: Converts Home Assistant color attributes to LIFX HSBK tuples (0-65535 scale)

### Migration Logic

The integration transitioned from per-device config entries to a single config entry. Migration happens in `async_setup()`:
- First legacy entry is updated to be the single config entry
- Additional legacy entries are removed
- Uses `unique_id=DOMAIN` and `single_config_entry: true` in manifest

## Code Style

This project follows Home Assistant's coding standards:
- Ruff for linting/formatting (config in `ruff.toml`)
- Target Python 3.12+
- Type annotations required (uses `from __future__ import annotations`)
- `TYPE_CHECKING` blocks for import-time vs runtime types
- Async-first architecture

## Home Assistant Integration Requirements

- Minimum HA version: 2025.8.0 (specified in manifest.json and hacs.json)
- Dependencies: `lifx` and `network` integrations
- Integration type: `hub` (manages multiple devices from one config entry)
- IoT class: `local_polling` (periodic discovery every 5 minutes)
- Single config entry pattern (migrated from per-device entries in 2025.5.0)

## LIFX Protocol Details

LIFX Ceiling devices use special multizone messages:
- `set64()`: Sets up to 64 zone colors at once (tile-based framebuffer API)
- `copy_frame_buffer()`: Copies framebuffer with optional transition duration
- Color values are HSBK tuples: (hue, saturation, brightness, kelvin) all 0-65535
- Power control uses duration in milliseconds
- Zone color transitions use duration in milliseconds

## Common Patterns

### Turning zones on/off
- If power is off and turning one zone on, the other zone's brightness must be set to 0
- If one zone is on and turning the other off, only adjust brightness to 0
- If both zones off, use device-level power control

### Color handling
- Home Assistant uses: hue (0-360°), saturation (0-100%), brightness (0-255), kelvin (1500-9000)
- LIFX uses: hue (0-65535), saturation (0-65535), brightness (0-65535), kelvin (1500-9000)
- Conversion factor: `value / max * 65535` or `value / 65535 * max`

### State updates
- Core LIFX coordinator owns device state
- This integration's entities listen to core coordinator updates via `async_add_listener()`
- After zone operations, request refresh from core coordinator: `coordinator.async_request_refresh()`