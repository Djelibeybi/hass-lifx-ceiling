# Tech Stack

## Language & Runtime
- Python 3.12+ (target version specified in ruff.toml)
- Async/await architecture (asyncio)
- Type annotations with `from __future__ import annotations`

## Core Dependencies
- **homeassistant** >= 2025.8.0 - Home Assistant core
- **aiolifx** >= 1.2.1 - Async LIFX protocol library
- **aiolifx-effects** >= 0.3.2 - LIFX effects support
- **aiolifx-themes** >= 0.6.4 - LIFX themes support
- **awesomeversion** - Version comparison utilities

## Development Tools
- **ruff** >= 0.6.1 - Linting and code formatting
- **colorlog** >= 6.8.2 - Colored logging for development

## Home Assistant Integration APIs
- ConfigEntry API (config_flow.py)
- DataUpdateCoordinator pattern
- Entity Platform API
- Service registration
- Device registry integration
