# Codebase Structure

## Root Directory
```
.
├── custom_components/lifx_ceiling/  # Integration code
├── config/                           # Test Home Assistant config
├── .github/workflows/                # CI/CD workflows
├── CLAUDE.md                         # Claude Code guidance
├── README.md                         # User documentation
├── CONTRIBUTING.md                   # Contribution guidelines
├── requirements.txt                  # Python dependencies
├── ruff.toml                         # Ruff configuration
└── hacs.json                         # HACS metadata
```

## Integration Structure (`custom_components/lifx_ceiling/`)

### Core Files
- **`__init__.py`** - Integration setup, entry point, migration logic
- **`manifest.json`** - Integration metadata (domain, dependencies, version)
- **`const.py`** - Constants (domain, attributes, product IDs, intervals)
- **`coordinator.py`** - `LIFXCeilingUpdateCoordinator` for state management
- **`api.py`** - `LIFXCeiling` class extending aiolifx Light
- **`light.py`** - Light entities (`LIFXCeilingUplight`, `LIFXCeilingDownlight`)
- **`entity.py`** - Base `LIFXCeilingEntity` class
- **`util.py`** - Helper functions (discovery, HSBK conversion, execution)
- **`config_flow.py`** - Configuration flow UI
- **`services.yaml`** - Service definitions
- **`strings.json`** - UI strings
- **`translations/`** - Localization files

## Architecture Overview

### Data Flow
1. **Discovery**: Coordinator finds LIFX Ceiling devices from core LIFX integration
2. **Casting**: Core `Light` objects cast to `LIFXCeiling` using class replacement
3. **Entity Creation**: Two light entities created per device via discovery callback
4. **State Management**: Entities listen to core LIFX coordinator for updates
5. **Control**: User actions → entity methods → coordinator → `LIFXCeiling` API → aiolifx

### Key Classes
- **`LIFXCeiling`**: Extended aiolifx Light with zone-specific methods
- **`LIFXCeilingUpdateCoordinator`**: Discovery and state coordination
- **`LIFXCeilingUplight`**: Light entity for uplight zone (last zone)
- **`LIFXCeilingDownlight`**: Light entity for downlight zones (all except last)
- **`LIFXCeilingEntity`**: Base entity with device info

### Zone Mapping
- **64-zone devices** (176, 177): Zones 0-62 = downlight, Zone 63 = uplight
- **128-zone devices** (201, 202): Zones 0-126 = downlight, Zone 127 = uplight

### Integration Pattern
- Single config entry for all devices (`single_config_entry: true`)
- Periodic discovery every 5 minutes
- Depends on core LIFX integration coordinators
- Uses framebuffer API (`set64`, `copy_frame_buffer`) for zone control
