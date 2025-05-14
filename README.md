# LIFX Ceiling custom integration

This integration adds `light` entities for the uplight and downlight of a LIFX Ceiling, allowing you to control each independently.

It received a major refactoring in May 2025 with the first GA release of 2025.5.0.

## Upgrading from the pre-release version

The integration now only has a single configuration entry that is designed to check for LIFX Ceiling devices being added to the core LIFX integration. Any existing configuration entries will be migrated to a single entry during the first restart after the integration is upgraded.

You must have at least one LIFX Ceiling device already configured via the core LIFX integration for this work.

If the migration fails, the simplest fix is to remove any configuration entries, restart Home Assistant and then

## Fresh install

1. [Add this repository to HACS](https://hacs.xyz/docs/faq/custom_repositories).
2. The integration should appear in green ready to be installed, so:
3. Install the integration and as always:
4. Restart Home Assistant

Once Home Assistant has started, navigate to Settings -> Devices & Services and click "Add Integration". Search for and select "LIFX Ceiling" then click "Submit". It will automatically discover any LIFX Ceilings configured via the core LIFX integration.

You must have at least one LIFX Ceiling configured via the core LIFX integration to configure this integration. Any future LIFX Ceiling devices that are added should be automatically discovered and configured within about 10 minutes of being added to Home Assistant.

## The `set_state` action

This integration provides a `lifx_ceiling.set_state` action that allows you to set both downlight and uplight zones in a single action call, ignoring any existing state.

The UI configuration should allow you to select multiple devices for the `device_id` parameter.

The remaining parameters are defined in the following table:

| Parameter | Range | Unit | Default |
| --------- | ----- | ---- | ------- |
| `transition` | 0-3600 | seconds | 0 |
| `downlight_hue` | 0-360 | degrees | 0 |
| `downlight_saturation` | 0-100 | percent | 0 |
| `downlight_brightness`| 0-100 | percent | 100 |
| `downlight_kelvin` | 1500-9000 | kelvin | 3500 |
| `uplight_hue` | 0-360 | degrees | 0 |
| `uplight_saturation` | 0-100 | percent | 0 |
| `uplight_brightness`| 0-100 | percent | 100 |
| `uplight_kelvin` | 1500-9000 | kelvin | 3500 |


## Issues? Bugs?

Please use discussions and issues to check if the issue or bug is already known and if not, please report it.
