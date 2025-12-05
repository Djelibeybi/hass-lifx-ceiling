# LIFX Ceiling Development Guide

## Table of Contents
- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Architecture Deep Dive](#architecture-deep-dive)
- [Common Tasks](#common-tasks)
- [Testing](#testing)
- [Debugging](#debugging)
- [Contributing](#contributing)

---

## Quick Start

### Prerequisites
- Python 3.12 or higher
- Home Assistant 2025.8.0 or higher
- At least one LIFX Ceiling device configured in HA core LIFX integration

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Djelibeybi/hass-lifx-ceiling.git
cd hass-lifx-ceiling

# Install dependencies (using uv - recommended)
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt
```

### Running Tests

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Run Home Assistant with test config
hass -c config
```

---

## Development Environment

### Directory Structure

```
hass-lifx-ceiling/
├── custom_components/lifx_ceiling/  # Integration code
│   ├── __init__.py                  # Entry point, migration
│   ├── api.py                       # LIFXCeiling class
│   ├── coordinator.py               # State coordinator
│   ├── light.py                     # Light entities
│   ├── entity.py                    # Base entity
│   ├── util.py                      # Utilities
│   ├── const.py                     # Constants
│   ├── config_flow.py               # Config UI
│   ├── manifest.json                # Integration metadata
│   ├── services.yaml                # Service definitions
│   ├── strings.json                 # UI strings
│   └── translations/                # Localization
├── config/                          # Test HA config
├── docs/                            # Documentation
├── .github/workflows/               # CI/CD
├── requirements.txt                 # Dependencies
├── ruff.toml                        # Linting config
└── CLAUDE.md                        # AI assistant guide
```

### Tools

- **Ruff**: Linting and formatting (replaces black, isort, flake8)
- **Home Assistant**: Integration testing
- **Git**: Version control with conventional commits

---

## Architecture Deep Dive

### Object Casting Pattern

The integration uses an unusual but effective pattern to extend core LIFX objects:

```python
# In coordinator.py
ceiling = LIFXCeiling.cast(coordinator.device)
```

This works by:
1. Taking an existing `aiolifx` `Light` object from core integration
2. Replacing its `__class__` attribute to `LIFXCeiling`
3. Preserving the existing connection and state

**Why this pattern?**
- Avoids recreating UDP connections
- Reuses core integration's connection management
- Minimal memory overhead
- Transparent to `aiolifx` library

**Implementation:**
```python
@classmethod
def cast(cls, device: Light) -> LIFXCeiling:
    """Cast the device to LIFXCeiling."""
    assert isinstance(device, Light)
    device.__class__ = cls
    assert isinstance(device, LIFXCeiling)
    return device
```

### Zone Mapping

LIFX Ceiling devices use multizone API but with specific layout:

**64-Zone Devices (Product IDs 176, 177):**
```
Zones 0-62: Downlight (63 zones)
Zone 63:    Uplight (1 zone)
```

**128-Zone Devices (Product IDs 201, 202):**
```
Zones 0-126: Downlight (127 zones)
Zone 127:    Uplight (1 zone)
```

**Framebuffer Layout:**
- Width: 8 or 16 zones
- Height (64-zone): 8 rows with 8 zones per row
- Height (128-zone): 8 rows with 16 zones per row
- Uplight: Last zone in layout

### Framebuffer Operations

LIFX Ceiling uses tile/matrix framebuffer API:

```python
# 64-zone devices: Single operation
device.set64(
    tile_index=0,      # First (only) tile
    length=1,          # One tile
    fb_index=1,        # Write to buffer 1
    x=0, y=0,          # Start position
    width=16,          # Tile width
    colors=colors      # 64 HSBK tuples
)

# 128-zone devices: Two operations
device.set64(..., y=0, colors=colors[0:64])   # First 64 zones
device.set64(..., y=4, colors=colors[64:128]) # Second 64 zones
```

**Copy framebuffer to activate:**
```python
device.copy_frame_buffer(
    tile_index=0,
    length=1,
    src_fb_index=1,   # From buffer 1 (just written)
    dst_fb_index=0,   # To buffer 0 (active)
    src_x=0, src_y=0,
    dst_x=0, dst_y=0,
    width=16,
    duration=1000     # Transition time in ms
)
```

### Coordinator Pattern

Uses Home Assistant's `DataUpdateCoordinator` but with unique behavior:

**Traditional coordinator:**
```python
coordinator = DataUpdateCoordinator(
    hass,
    logger,
    name="sensor",
    update_method=async_update_data,  # Called on schedule
    update_interval=timedelta(seconds=30)
)
```

**LIFX Ceiling coordinator:**
```python
coordinator = LIFXCeilingUpdateCoordinator(
    hass,
    config_entry
    # No update_interval - doesn't poll
)

# Discovery runs separately
coordinator.stop_discovery = async_track_time_interval(
    hass,
    coordinator.async_update,
    timedelta(minutes=5)
)
```

**Why this pattern?**
- State comes from core LIFX coordinator (no polling needed)
- `async_update()` only discovers new devices
- Entities listen to core coordinator for state changes

### Entity State Flow

```python
# In light.py entity setup
coordinator.async_add_core_listener(device, self._update_callback)

# Core LIFX coordinator notifies all listeners
# → _update_callback() extracts zone-specific state
@callback
def _update_callback(self) -> None:
    self._attr_is_on = self._device.downlight_is_on
    self._attr_brightness = self._device.downlight_brightness
    # ... more state extraction
    self.async_write_ha_state()
```

**Flow:**
1. Core LIFX device state changes (via `aiolifx`)
2. Core coordinator updates its state
3. Core coordinator calls all listeners
4. Our entity callback extracts relevant zone data
5. Entity writes state to HA

### Color Scale Conversions

**Home Assistant scales:**
- Hue: 0-360 degrees
- Saturation: 0-255
- Brightness: 0-255
- Kelvin: 1500-9000

**LIFX scales:**
- Hue: 0-65535 (uint16)
- Saturation: 0-65535 (uint16)
- Brightness: 0-65535 (uint16)
- Kelvin: 1500-9000

**Conversion formulas:**
```python
# HA → LIFX
lifx_hue = int(ha_hue / 360 * 65535)
lifx_sat = int(ha_sat / 100 * 65535)
lifx_bri = (ha_bri << 8) | ha_bri  # Duplicate for precision

# LIFX → HA
ha_hue = lifx_hue / 65535 * 360
ha_sat = lifx_sat / 65535 * 100
ha_bri = lifx_bri >> 8  # High byte only
```

---

## Common Tasks

### Adding a New Property to LIFXCeiling

1. **Add property to api.py:**
```python
@property
def my_new_property(self) -> str:
    """Return my new property."""
    return self.chain[0][0][0]  # Example: hue from zone 0
```

2. **Use in entity (light.py):**
```python
@callback
def _update_callback(self) -> None:
    self._attr_my_attribute = self._device.my_new_property
    self.async_write_ha_state()
```

3. **Test:**
```bash
ruff check .
ruff format .
hass -c config
```

### Adding a New Service

1. **Define service in services.yaml:**
```yaml
my_service:
  name: My Service
  description: Does something useful
  fields:
    my_param:
      description: A parameter
      example: "value"
      required: true
```

2. **Add service handler in __init__.py:**
```python
async def async_setup_entry(...):
    # ... existing code

    async def handle_my_service(call: ServiceCall) -> None:
        """Handle my service call."""
        param = call.data.get("my_param")
        # Do something

    hass.services.async_register(
        DOMAIN,
        "my_service",
        handle_my_service
    )
```

3. **Add constants to const.py:**
```python
ATTR_MY_PARAM = "my_param"
SERVICE_MY_SERVICE = "my_service"
```

### Modifying Zone Control Logic

Zone control has specific power management requirements:

**Turning one zone on when device is off:**
```python
async def turn_uplight_on(self, color, duration):
    colors = self.chain[0][self.downlight_zones]  # Get current

    if self.power_level == 0:
        # Device is off - zero out other zones
        colors = [(h, s, 0, k) for h, s, _, k in colors]

    colors.append(color)  # Add uplight color
    await self.async_set64(colors, duration, power_on=True)
```

**Turning one zone off when both are on:**
```python
async def turn_uplight_off(self, duration):
    if self.downlight_is_on:
        # Keep downlight on, just zero uplight brightness
        colors = self.chain[0][self.downlight_zones]
        h, s, _, k = self.chain[0][self.uplight_zone]
        colors.append((h, s, 0, k))  # Brightness = 0
        await self.async_set64(colors, duration)
    else:
        # Both zones off - power off device
        await async_execute_lifx(
            partial(self.set_power, value="off", duration=duration * 1000)
        )
```

### Handling 128-Zone Devices

128-zone devices require splitting framebuffer operations:

```python
if self.product in LIFX_CEILING_128ZONES_PRODUCT_IDS:
    # Two 64-color batches
    await async_execute_lifx([
        partial(
            self.set64,
            tile_index=0, length=1, fb_index=1,
            x=0, y=0,  # First batch at y=0
            width=16,
            colors=colors[:64]
        ),
        partial(
            self.set64,
            tile_index=0, length=1, fb_index=1,
            x=0, y=4,  # Second batch at y=4
            width=16,
            colors=colors[64:]
        ),
    ])
else:
    # Single 64-color operation
    await async_execute_lifx(
        partial(
            self.set64,
            tile_index=0, length=1, fb_index=0,
            x=0, y=0,
            width=8,
            colors=colors
        )
    )
```

---

## Testing

### Manual Testing with Home Assistant

1. **Setup test environment:**
```bash
# Ensure HA not running
hass -c config
```

2. **Configure in HA:**
   - Navigate to Settings → Devices & Services
   - Add LIFX integration (if needed)
   - Add LIFX Ceiling integration
   - Should auto-discover Ceiling devices

3. **Test scenarios:**
   - Turn uplight on/off independently
   - Turn downlight on/off independently
   - Change colors on each zone
   - Test transitions
   - Test `set_state` service
   - Restart HA (test migration)

### Unit Testing

Currently no unit tests. Recommended additions:

```python
# tests/test_api.py
async def test_zone_mapping_64():
    """Test 64-zone device mapping."""
    device = create_mock_device(product=176)
    ceiling = LIFXCeiling.cast(device)

    assert ceiling.total_zones == 64
    assert ceiling.uplight_zone == 63
    assert ceiling.downlight_zones == slice(63)

async def test_zone_mapping_128():
    """Test 128-zone device mapping."""
    device = create_mock_device(product=201)
    ceiling = LIFXCeiling.cast(device)

    assert ceiling.total_zones == 128
    assert ceiling.uplight_zone == 127
    assert ceiling.downlight_zones == slice(127)
```

### Integration Testing

Test with actual hardware:
1. Connect to LIFX Ceiling device
2. Configure via HA core LIFX integration
3. Install this integration
4. Verify entities created
5. Test all control scenarios

---

## Debugging

### Enable Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.lifx_ceiling: debug
    aiolifx: debug
    bitstring: debug
```

### Common Issues

**Entities not appearing:**
- Check core LIFX integration is loaded
- Verify device is LIFX Ceiling (product ID 176, 177, 201, or 202)
- Check logs for discovery errors
- Ensure `is_matrix` is True on core device

**State not updating:**
- Verify entities registered core coordinator listener
- Check core LIFX coordinator is updating
- Examine callback registration in entity setup

**Control commands timing out:**
- Check network connectivity to device
- Verify UDP port 56700 is accessible
- Increase `OVERALL_TIMEOUT` in const.py (temporarily)
- Check for firewall issues

**Colors not matching:**
- Verify conversion formulas (see Color Scale Conversions)
- Check saturation > 0 for color mode vs kelvin mode
- Examine HSBK tuple values in logs

### Debugging Tools

**Check coordinator state:**
```python
# In Developer Tools → Template
{{ states.light.my_ceiling_downlight }}
{{ state_attr('light.my_ceiling_downlight', 'brightness') }}
{{ state_attr('light.my_ceiling_downlight', 'hs_color') }}
```

**Inspect device registry:**
```python
# In Developer Tools → Template
{% set device_id = 'abc123' %}
{{ device_attr(device_id, 'identifiers') }}
{{ device_attr(device_id, 'model') }}
```

**Call service manually:**
```yaml
# Developer Tools → Services
service: lifx_ceiling.set_state
target:
  device_id: abc123
data:
  transition: 0
  downlight_brightness: 100
  uplight_brightness: 0
```

---

## Contributing

### Before Submitting PR

1. **Format code:**
```bash
ruff format .
```

2. **Fix lint issues:**
```bash
ruff check . --fix
```

3. **Test with Home Assistant:**
```bash
hass -c config
# Verify all functionality works
```

4. **Update documentation:**
   - `API.md` for API changes
   - `DEVELOPMENT.md` for architecture changes
   - `CLAUDE.md` for significant patterns
   - `README.md` for user-facing features

5. **Commit with conventional commits and DCO sign-off:**
```bash
git commit -s -m "feat: add new zone control method"
git commit -s -m "fix: correct 128-zone framebuffer split"
git commit -s -m "docs: update API reference"
```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Scopes:**
- `api`: LIFXCeiling class
- `coordinator`: Coordinator changes
- `entity`: Entity changes
- `service`: Service changes
- `util`: Utility functions

### Code Review Checklist

- [ ] Ruff formatting passed
- [ ] Ruff linting passed
- [ ] Type annotations added
- [ ] Docstrings added/updated
- [ ] Manual testing completed
- [ ] Documentation updated
- [ ] CLAUDE.md updated (if architecture changed)
- [ ] Conventional commit message
- [ ] No debugging code left

---

## Advanced Topics

### Migration Strategy

The integration migrated from per-device to single config entry in v2025.5.0:

**Migration logic (in __init__.py):**
```python
async def async_setup(hass, config):
    legacy_entries = async_get_legacy_entries(hass)

    if not has_single_config_entry(hass) and legacy_entries:
        # Convert first legacy entry
        hass.config_entries.async_update_entry(
            legacy_entries[0],
            data={},
            options={},
            title=NAME,
            unique_id=DOMAIN
        )
        legacy_entries.pop(0)

    # Remove remaining legacy entries
    for entry in legacy_entries:
        await hass.config_entries.async_remove(entry.entry_id)
```

**Key points:**
- Runs once on first load after upgrade
- First legacy entry becomes the single entry
- Data/options cleared (no longer needed)
- `unique_id` set to `DOMAIN` for identification
- Other entries removed automatically

### Error Handling

**LIFX command retries:**
```python
async def async_execute_lifx(methods, attempts=3, overall_timeout=5):
    timeout_per_attempt = overall_timeout / attempts

    for _ in range(attempts):
        for method, future in methods_with_futures:
            if not future.done():
                method(callb=partial(_callback, future=future))

        _, pending = await asyncio.wait(futures, timeout=timeout_per_attempt)
        if not pending:
            break  # All completed

    # Check for failures
    if failed:
        raise TimeoutError(f"{len(failed)} requests timed out")
```

**Benefits:**
- Handles UDP packet loss
- Configurable retry count
- Parallel execution of multiple commands
- Clear error reporting

### Performance Optimization

**Parallel command execution:**
```python
# Good: Parallel execution
await async_execute_lifx([
    partial(device.set64, colors=batch1),
    partial(device.set64, colors=batch2),
])

# Bad: Sequential execution
await async_execute_lifx(partial(device.set64, colors=batch1))
await async_execute_lifx(partial(device.set64, colors=batch2))
```

**Minimize coordinator refreshes:**
```python
# Good: Refresh after control command
async def turn_uplight_on(self, device, color, duration):
    await device.turn_uplight_on(color, duration)
    await self._ceiling_coordinators[device.mac_addr].async_request_refresh()

# Bad: Refresh on every property access
```

---

## Resources

### Documentation
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [aiolifx Documentation](https://github.com/aiolifx/aiolifx)
- [LIFX LAN Protocol](https://lan.developer.lifx.com/)

### Related Projects
- [Home Assistant Core LIFX Integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/lifx)
- [aiolifx Library](https://github.com/aiolifx/aiolifx)

### Support
- [GitHub Issues](https://github.com/Djelibeybi/hass-lifx-ceiling/issues)
- [GitHub Discussions](https://github.com/Djelibeybi/hass-lifx-ceiling/discussions)