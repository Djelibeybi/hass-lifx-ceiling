# Design Patterns and Guidelines

## Home Assistant Integration Patterns

### Config Entry Migration
The integration migrated from per-device entries to a single config entry in v2025.5.0:
- Migration logic in `async_setup()` handles conversion on first load
- Uses `unique_id=DOMAIN` for the single entry
- Legacy entries identified by `unique_id != DOMAIN` and removed

### Coordinator Pattern
Uses Home Assistant's `DataUpdateCoordinator`:
- `LIFXCeilingUpdateCoordinator` manages discovery and state
- Does NOT fetch data on schedule (no `update_interval`)
- Instead, listens to core LIFX coordinator updates
- Discovery runs every 5 minutes via `async_track_time_interval`

### Entity Pattern
- Entities extend `CoordinatorEntity[LIFXCeilingUpdateCoordinator]`
- Use `@callback` for state update handlers
- Set `_attr_has_entity_name = True` for proper entity naming
- Device info includes identifiers, connections, and metadata

## LIFX-Specific Patterns

### Object Casting Pattern
Core LIFX `Light` objects are cast to `LIFXCeiling`:
```python
ceiling = LIFXCeiling.cast(coordinator.device)
```
This uses `__class__` replacement to avoid recreating connections.

### Zone Control Logic
**When turning zones on/off:**
1. If device is off and turning one zone on → set other zone brightness to 0
2. If one zone is on and turning other off → only adjust brightness
3. If both zones would be off → use device-level power control

**Color operations:**
- Always set all zones in one operation using `async_set64()`
- For 128-zone devices, split into two 64-color batches
- Use `copy_frame_buffer()` for transitions
- Power on separately after framebuffer update if needed

### Async Execution Pattern
Uses `async_execute_lifx()` wrapper for all LIFX protocol calls:
- Retries failed operations (default 3 attempts)
- Handles timeouts (default 5 seconds total)
- Uses `partial()` to bind callback parameter
- Returns list of responses or raises TimeoutError

## Color Conversion Pattern
Home Assistant ↔ LIFX conversions via `hsbk_for_turn_on()`:
- **Hue**: HA (0-360°) ↔ LIFX (0-65535)
- **Saturation**: HA (0-100%) ↔ LIFX (0-65535)
- **Brightness**: HA (0-255) ↔ LIFX (0-65535)
- **Kelvin**: Both use 1500-9000K

## Service Pattern
Custom service `lifx_ceiling.set_state`:
- Takes device_id (single or list)
- Accepts all uplight/downlight color parameters
- Directly manipulates all zones, ignoring current state
- Useful for scenes and automations

## State Update Pattern
1. Entities listen to core LIFX coordinator via `async_add_listener()`
2. Core coordinator updates when device state changes
3. Entity `_update_callback()` extracts zone-specific state
4. Entity calls `async_write_ha_state()` to update HA
5. After control operations, request core refresh: `coordinator.async_request_refresh()`
