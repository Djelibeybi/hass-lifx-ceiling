# LIFX Ceiling Integration API Reference

## Table of Contents
- [Core Classes](#core-classes)
  - [LIFXCeiling](#lifxceiling)
  - [LIFXCeilingUpdateCoordinator](#lifxceilingupdatecoordinator)
  - [LIFXCeilingEntity](#lifxceilingentity)
  - [Light Entities](#light-entities)
- [Utility Functions](#utility-functions)
- [Constants](#constants)
- [Service API](#service-api)

---

## Core Classes

### LIFXCeiling

**Location**: `custom_components/lifx_ceiling/api.py:27-301`

Extended aiolifx `Light` class with zone-specific control for LIFX Ceiling devices.

#### Properties

##### Device Configuration
- **`total_zones`** → `int`
  Returns 64 for product IDs 176/177, or 128 for product IDs 201/202

- **`uplight_zone`** → `int`
  Returns index of uplight zone (63 for 64-zone, 127 for 128-zone devices)

- **`downlight_zones`** → `slice`
  Returns slice for all downlight zones (0:63 or 0:127)

- **`min_kelvin`** → `int`
  Minimum color temperature from product definition

- **`max_kelvin`** → `int`
  Maximum color temperature from product definition

- **`model`** → `str`
  Friendly product name from aiolifx products dictionary

##### Uplight State
- **`uplight_color`** → `tuple[int, int, int, int]`
  Returns (hue, saturation, brightness, kelvin) for uplight zone (all 0-65535)

- **`uplight_hs_color`** → `tuple[float, float]`
  Returns (hue, saturation) in Home Assistant scale (0-360°, 0-100%)

- **`uplight_brightness`** → `int`
  Returns uplight brightness (0-255 scale)

- **`uplight_kelvin`** → `int`
  Returns uplight color temperature in kelvin

- **`uplight_is_on`** → `bool`
  True if device power > 0 and uplight brightness > 0

##### Downlight State
- **`downlight_color`** → `tuple[int, int, int, int]`
  Returns zone 0 color with max brightness from all downlight zones

- **`downlight_hs_color`** → `tuple[float, float]`
  Returns zone 0 (hue, saturation) in Home Assistant scale

- **`downlight_brightness`** → `int`
  Returns maximum brightness across all downlight zones (0-255 scale)

- **`downlight_kelvin`** → `int`
  Returns zone 0 color temperature in kelvin

- **`downlight_is_on`** → `bool`
  True if device power > 0 and any downlight zone brightness > 0

#### Methods

##### `cast(device: Light) → LIFXCeiling`
**Class method** that casts a core LIFX `Light` object to `LIFXCeiling`.

Uses `__class__` replacement pattern to avoid recreating connections.

**Parameters:**
- `device`: aiolifx Light instance

**Returns:** The same object cast to LIFXCeiling type

**Example:**
```python
ceiling = LIFXCeiling.cast(coordinator.device)
```

##### `async turn_uplight_on(color: tuple[int, int, int, int], duration: int = 0) → None`
Turn on the uplight zone with specified color.

**Parameters:**
- `color`: HSBK tuple (hue, saturation, brightness, kelvin) all 0-65535
- `duration`: Transition time in milliseconds

**Behavior:**
- If device is off, sets downlight zones to brightness 0
- Preserves downlight zone colors if device is on
- Automatically powers on device if needed

##### `async turn_uplight_off(duration: int = 0) → None`
Turn off the uplight zone.

**Parameters:**
- `duration`: Transition time in milliseconds

**Behavior:**
- If downlight is on: Sets uplight brightness to 0
- If downlight is off: Powers off entire device

##### `async turn_downlight_on(color: tuple[int, int, int, int], duration: int = 0) → None`
Turn on all downlight zones with specified color.

**Parameters:**
- `color`: HSBK tuple (hue, saturation, brightness, kelvin) all 0-65535
- `duration`: Transition time in milliseconds

**Behavior:**
- Sets all downlight zones to the same color
- If device is off, sets uplight brightness to 0
- Preserves uplight color if device is on
- Automatically powers on device if needed

##### `async turn_downlight_off(duration: int = 0) → None`
Turn off all downlight zones.

**Parameters:**
- `duration`: Transition time in milliseconds

**Behavior:**
- If uplight is on: Sets downlight brightness to 0
- If uplight is off: Powers off entire device

##### `async async_set64(colors: list[tuple[int, int, int, int]], duration: int = 0, power_on: bool = False) → None`
Set all zone colors using LIFX framebuffer API.

**Parameters:**
- `colors`: List of HSBK tuples, must match `total_zones` length
- `duration`: Transition time in milliseconds
- `power_on`: Whether to power on device after setting colors

**Behavior:**
- For 128-zone devices: Splits into two 64-color batches (y=0 and y=4)
- For 64-zone devices: Single framebuffer operation
- Uses `set64()` to write to framebuffer 1
- Uses `copy_frame_buffer()` to transition to framebuffer 0
- If `power_on=True`, powers on device after transition

**Raises:** `LIFXCeilingError` if colors list length doesn't match `total_zones`

---

### LIFXCeilingUpdateCoordinator

**Location**: `custom_components/lifx_ceiling/coordinator.py:41-212`

Manages discovery, state tracking, and control for LIFX Ceiling devices.

Extends Home Assistant's `DataUpdateCoordinator[list[LIFXCeiling]]`.

#### Properties

- **`devices`** → `list[LIFXCeiling]`
  Returns list of discovered LIFX Ceiling devices

- **`discovery_callback`** → `Callable[[LIFXCeiling], None] | None`
  Returns current discovery callback (called when new devices found)

#### Methods

##### `__init__(hass: HomeAssistant, config_entry: LIFXCeilingConfigEntry) → None`
Initialize the coordinator.

**Parameters:**
- `hass`: Home Assistant instance
- `config_entry`: Integration config entry

**State Initialized:**
- `stop_discovery`: Cancellation callback for periodic discovery
- `_discovery_callback`: Callback for new device discoveries
- `_ceiling_coordinators`: Maps MAC addresses to core LIFX coordinators
- `_ceilings`: Set of discovered LIFXCeiling devices
- `_hass_version`: Current Home Assistant version

##### `set_discovery_callback(callback: Callable[[LIFXCeiling], None]) → Callable`
Set discovery callback and return previous callback.

Used by platform setup to register entity creation callback.

**Parameters:**
- `callback`: Function called when new LIFX Ceiling device discovered

**Returns:** Previous discovery callback (or None)

##### `async_add_core_listener(device: LIFXCeiling, callback: Callable[[], None]) → None`
Register listener on core LIFX coordinator for state updates.

Entities use this to receive updates from core integration.

**Parameters:**
- `device`: LIFXCeiling device
- `callback`: Function called when core coordinator updates

##### `async async_update(update_time: datetime | None = None) → None`
Discover new LIFX Ceiling devices from core LIFX integration.

Called every 5 minutes via `async_track_time_interval`.

**Behavior:**
1. Finds core LIFX coordinators with Ceiling products
2. Casts core Light objects to LIFXCeiling
3. Stores references to core coordinators
4. Calls discovery callback for new devices

##### `async async_set_state(call: ServiceCall) → None`
Handle `lifx_ceiling.set_state` service call.

Sets both uplight and downlight zones in single operation.

**Service Data:**
- `device_id`: Single device ID or list of device IDs
- `transition`: Transition time in seconds
- `downlight_hue`: 0-360° (optional, default 0)
- `downlight_saturation`: 0-100% (optional, default 0)
- `downlight_brightness`: 0-100% (optional, default 100)
- `downlight_kelvin`: 1500-9000K (optional, default 3500)
- `uplight_hue`: 0-360° (optional, default 0)
- `uplight_saturation`: 0-100% (optional, default 0)
- `uplight_brightness`: 0-100% (optional, default 100)
- `uplight_kelvin`: 1500-9000K (optional, default 3500)

**Behavior:**
- Converts HA scales to LIFX scales (0-65535)
- If both zones brightness 0: Powers off device
- Otherwise: Sets all zones with `async_set64()`

##### `async turn_uplight_on(device: LIFXCeiling, color: tuple, duration: int) → None`
Turn on uplight and request core coordinator refresh.

Wrapper around `device.turn_uplight_on()` with refresh.

##### `async turn_uplight_off(device: LIFXCeiling, duration: int) → None`
Turn off uplight and request core coordinator refresh.

##### `async turn_downlight_on(device: LIFXCeiling, color: tuple, duration: int) → None`
Turn on downlight and request core coordinator refresh.

##### `async turn_downlight_off(device: LIFXCeiling, duration: int) → None`
Turn off downlight and request core coordinator refresh.

---

### LIFXCeilingEntity

**Location**: `custom_components/lifx_ceiling/entity.py:18-38`

Base entity class for LIFX Ceiling entities.

Extends `CoordinatorEntity[LIFXCeilingUpdateCoordinator]`.

#### Properties

- **`_attr_has_entity_name = True`**
  Uses device name + entity name for full entity name

#### Device Info

Automatically populates device registry with:
- **Identifiers**: `{(DOMAIN, device.mac_addr)}`
- **Connections**: `{(CONNECTION_NETWORK_MAC, device.mac_addr)}`
- **Serial Number**: MAC address (lowercase, no colons)
- **Manufacturer**: "LIFX"
- **Name**: Device label
- **Model**: Friendly model name
- **SW Version**: Host firmware version
- **Suggested Area**: Device group name

---

### Light Entities

#### LIFXCeilingDownlight

**Location**: `custom_components/lifx_ceiling/light.py:55-99`

Light entity for downlight zones (all zones except last).

**Properties:**
- **Supported Features**: `LightEntityFeature.TRANSITION`
- **Color Modes**: `{ColorMode.COLOR_TEMP, ColorMode.HS}`
- **Name**: "Downlight"
- **Unique ID**: `{mac_address}_downlight`
- **Min/Max Kelvin**: From device properties

**State Properties** (updated via `_update_callback`):
- `is_on`: From `device.downlight_is_on`
- `brightness`: From `device.downlight_brightness` (0-255)
- `hs_color`: From `device.downlight_hs_color` (hue 0-360°, sat 0-100%)
- `color_temp_kelvin`: From `device.downlight_kelvin`
- `color_mode`: `HS` if saturation > 0, else `COLOR_TEMP`

**Methods:**
- `async async_turn_on(**kwargs)`: Calls `coordinator.turn_downlight_on()`
- `async async_turn_off(**kwargs)`: Calls `coordinator.turn_downlight_off()`

#### LIFXCeilingUplight

**Location**: `custom_components/lifx_ceiling/light.py:101-145` (inferred)

Light entity for uplight zone (last zone only).

Same structure as `LIFXCeilingDownlight` but for uplight zone.

**Properties:**
- **Name**: "Uplight"
- **Unique ID**: `{mac_address}_uplight`

**State Properties:**
- From `device.uplight_*` properties

**Methods:**
- Calls `coordinator.turn_uplight_on/off()`

---

## Utility Functions

**Location**: `custom_components/lifx_ceiling/util.py`

### `find_lifx_coordinators(hass: HomeAssistant) → list[LIFXUpdateCoordinator]`

Find all LIFX Ceiling coordinators from core LIFX integration.

**Filtering Logic:**
1. Loaded LIFX config entries
2. Has `runtime_data` attribute
3. `runtime_data` is `LIFXUpdateCoordinator`
4. Device `is_matrix` is True
5. Device product ID in `LIFX_CEILING_PRODUCT_IDS`

**Returns:** List of core LIFX coordinators for Ceiling devices

---

### `has_single_config_entry(hass: HomeAssistant) → bool`

Check if single config entry exists for this integration.

**Returns:** True if entry with `unique_id=DOMAIN` exists

---

### `async_get_legacy_entries(hass: HomeAssistant) → list[ConfigEntry]`

Get legacy per-device config entries (pre-2025.5.0).

**Returns:** Config entries where `unique_id != DOMAIN`

---

### `hsbk_for_turn_on(current: tuple[int, int, int, int], **kwargs) → tuple[int, int, int, int]`

Convert Home Assistant turn_on kwargs to LIFX HSBK tuple.

**Parameters:**
- `current`: Current HSBK values (0-65535 scale)
- `kwargs`: Home Assistant light attributes

**Supported kwargs:**
- `color_name`: CSS color name
- `hs_color`: (hue 0-360°, saturation 0-100%)
- `color_temp_kelvin`: 1500-9000K
- `brightness`: 0-255
- `brightness_pct`: 0-100%

**Conversion Logic:**
- If `hs_color` or `color_name` provided: Sets hue/sat, defaults kelvin to 3500
- If `color_temp_kelvin` provided: Sets kelvin, forces saturation to 0
- Otherwise: Preserves current hue/sat/kelvin
- Brightness converted from HA scale to LIFX scale (0-65535)
- If brightness would be 0, defaults to 65535 (full brightness)

**Returns:** HSBK tuple (all 0-65535)

---

### `async async_execute_lifx(methods: Callable | list[Callable], attempts: int = 3, overall_timeout: int = 5) → list[Message]`

Execute aiolifx methods with retry logic and timeout handling.

**Parameters:**
- `methods`: Single method or list of methods (using `functools.partial`)
- `attempts`: Number of retry attempts (default 3)
- `overall_timeout`: Total timeout in seconds (default 5)

**Behavior:**
1. Creates futures for each method
2. Calls methods with callback that resolves futures
3. Waits for futures with timeout per attempt
4. Retries incomplete requests up to max attempts
5. Collects results or raises TimeoutError

**Returns:** List of LIFX Message responses

**Raises:** `TimeoutError` if any method fails after all attempts

**Example:**
```python
from functools import partial

# Single method
await async_execute_lifx(partial(device.set_power, value="on"))

# Multiple methods
await async_execute_lifx([
    partial(device.set64, colors=colors1),
    partial(device.set64, colors=colors2),
])
```

---

## Constants

**Location**: `custom_components/lifx_ceiling/const.py`

### Domain & Integration
- **`DOMAIN = "lifx_ceiling"`**
- **`NAME = "LIFX Ceiling"`**

### Product IDs
- **`LIFX_CEILING_PRODUCT_IDS = {176, 177, 201, 202}`**
  All supported Ceiling product IDs

- **`LIFX_CEILING_64ZONES_PRODUCT_IDS = {176, 177}`**
  64-zone Ceiling models

- **`LIFX_CEILING_128ZONES_PRODUCT_IDS = {201, 202}`**
  128-zone Ceiling models

### Service Attributes
- **`ATTR_DOWNLIGHT_HUE`** = "downlight_hue"
- **`ATTR_DOWNLIGHT_SATURATION`** = "downlight_saturation"
- **`ATTR_DOWNLIGHT_BRIGHTNESS`** = "downlight_brightness"
- **`ATTR_DOWNLIGHT_KELVIN`** = "downlight_kelvin"
- **`ATTR_UPLIGHT_HUE`** = "uplight_hue"
- **`ATTR_UPLIGHT_SATURATION`** = "uplight_saturation"
- **`ATTR_UPLIGHT_BRIGHTNESS`** = "uplight_brightness"
- **`ATTR_UPLIGHT_KELVIN`** = "uplight_kelvin"

### HSBK Indices
- **`HSBK_HUE = 0`**
- **`HSBK_SATURATION = 1`**
- **`HSBK_BRIGHTNESS = 2`**
- **`HSBK_KELVIN = 3`**

### Discovery & Timeouts
- **`DISCOVERY_INTERVAL = timedelta(minutes=5)`**
  Periodic discovery interval

- **`DEFAULT_ATTEMPTS = 3`**
  Default retry attempts for LIFX commands

- **`OVERALL_TIMEOUT = 5`**
  Default total timeout in seconds

### Services
- **`SERVICE_LIFX_CEILING_SET_STATE = "set_state"`**

---

## Service API

### `lifx_ceiling.set_state`

Set both uplight and downlight zones in a single service call.

**Location**: Registered in `__init__.py:73-74`
**Handler**: `coordinator.async_set_state()`

#### Service Fields

| Field | Type | Range | Unit | Default |
|-------|------|-------|------|---------|
| `device_id` | device_id or list | N/A | N/A | **Required** |
| `transition` | float | 0-3600 | seconds | 0 |
| `downlight_hue` | float | 0-360 | degrees | 0 |
| `downlight_saturation` | float | 0-100 | percent | 0 |
| `downlight_brightness` | float | 0-100 | percent | 100 |
| `downlight_kelvin` | int | 1500-9000 | kelvin | 3500 |
| `uplight_hue` | float | 0-360 | degrees | 0 |
| `uplight_saturation` | float | 0-100 | percent | 0 |
| `uplight_brightness` | float | 0-100 | percent | 100 |
| `uplight_kelvin` | int | 1500-9000 | kelvin | 3500 |

#### Behavior

- Ignores current state and applies specified values
- Useful for scenes and automations where exact state is desired
- If both zones brightness = 0: Powers off device
- Otherwise: Sets all zones simultaneously

#### Example YAML

```yaml
service: lifx_ceiling.set_state
target:
  device_id:
    - abc123
    - def456
data:
  transition: 2
  downlight_hue: 240
  downlight_saturation: 100
  downlight_brightness: 80
  downlight_kelvin: 3500
  uplight_hue: 30
  uplight_saturation: 50
  uplight_brightness: 60
  uplight_kelvin: 2700
```

---

## Integration Flow

### Initialization Sequence

1. **`async_setup()`** - Migration from legacy entries
2. **`async_setup_entry()`** - Coordinator creation
3. **`coordinator.async_update()`** - Initial discovery
4. **Platform setup** - Entity creation
5. **Service registration** - Register `set_state` service
6. **Periodic discovery** - Every 5 minutes

### Discovery Flow

```
find_lifx_coordinators()
  → Filter matrix devices with Ceiling product IDs
    → LIFXCeiling.cast() core Light objects
      → Store coordinator references
        → Call discovery_callback()
          → Create light entities
```

### State Update Flow

```
Core LIFX device state changes
  → Core coordinator updates
    → Entity _update_callback() triggered
      → Extract zone-specific state
        → Update entity attributes
          → async_write_ha_state()
```

### Control Flow

```
User action (turn_on/turn_off)
  → Entity method
    → Coordinator method
      → LIFXCeiling API method
        → async_execute_lifx()
          → aiolifx protocol commands
            → Request core coordinator refresh
```

---

## Cross-References

- **Architecture Overview**: See `CLAUDE.md`
- **User Documentation**: See `README.md`
- **Contribution Guidelines**: See `CONTRIBUTING.md`
- **Code Style**: See `ruff.toml`
- **Integration Manifest**: See `custom_components/lifx_ceiling/manifest.json`
