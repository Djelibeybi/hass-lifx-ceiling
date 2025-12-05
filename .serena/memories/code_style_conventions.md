# Code Style and Conventions

## Linting & Formatting
- Uses **Ruff** for both linting and formatting
- Configuration in `ruff.toml` based on Home Assistant core standards
- Ruff target version: Python 3.12

## Type Annotations
- **Required** for all functions and methods
- Use `from __future__ import annotations` for forward references
- Use `TYPE_CHECKING` blocks to avoid circular imports at runtime
- Example:
  ```python
  if TYPE_CHECKING:
      from homeassistant.core import HomeAssistant
  ```

## Naming Conventions
- Classes: PascalCase (e.g., `LIFXCeiling`, `LIFXCeilingUpdateCoordinator`)
- Functions/methods: snake_case (e.g., `async_setup_entry`, `turn_uplight_on`)
- Constants: UPPER_SNAKE_CASE (e.g., `DOMAIN`, `LIFX_CEILING_PRODUCT_IDS`)
- Private methods: Prefix with underscore (e.g., `_update_callback`)

## Docstrings
- Use triple-quoted strings for all public functions/classes
- Keep docstrings concise and focused on "what" and "why"
- Parameters and return types are documented via type annotations

## Async Patterns
- Prefix async functions with `async_`
- Use `@callback` decorator for synchronous callbacks in async context
- Use `partial()` for binding arguments to callbacks

## Import Organization
- Standard library imports first
- Third-party imports second
- Home Assistant imports third
- Local imports last
- Within each group, separate conditional `TYPE_CHECKING` imports

## Code Quality Rules
- Maximum complexity: 25 (McCabe)
- Specific ignores in ruff.toml for Home Assistant compatibility
- No unused arguments in callbacks (ARG001, ARG002 ignored)
- Boolean arguments allowed (FBT001, FBT002 ignored)
