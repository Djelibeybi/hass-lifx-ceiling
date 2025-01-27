# LIFX Ceiling Extras

This integration adds `Light` entities for the uplight and downlight of a LIFX Ceiling, allowing you to control each independently.

> **NOTE:** this integration is in __alpha__ testing phase and _will_ have bugs, issues and unexpected user experiences. Folks who share their home with intolerant occupants are advised to _proceed with caution_.

## Installation

1. [Add this repository to HACS](https://hacs.xyz/docs/faq/custom_repositories).
2. The integration should appear in green ready to be installed, so:
3. Install the integration and as always:
4. Restart Home Assistant

Home Assistant should automatically discover your LIFX Ceiling(s) and prompt you to add them.
After you add them, two new light entities will be created for the uplight and downlight.

## Known issues/caveats

Adding the uplight or downlight to your Dashboard is discouraged as the state can be up to 10 seconds behind reality and may bounce between `off` and `on` a few times when the state changes.

To turn on just the uplight or downlight without any surprises, use the `light.turn_on` action and explicitly specify the brightness and color or color temp to use.

- If neither `brightness` nor `brightness_pct` are used, the light will turn on at full (100%) brightness.
- If neither `hs_color` nor `color_temp_kelvin` are used, the light will turn on in color temperature mode set to 3500K (neutral).
- I strongly encourage you to set `transition` to at least `0.25` (or higher) with both `light.turn_on` and `light.turn_off` to make the process less jarring.

Turning the main light entity on or off or using `light.turn_on` or `light.turn_off` is a good way to reset both to the same state.

## Issues? Bugs?

Please use discussions and issues to check if the issue or bug is already known and if not, please report it.
