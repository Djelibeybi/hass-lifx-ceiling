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

## Using the `set_state` action

The `set_state` can be used to set any combination of hue, saturation, brightness and kelvin to both uplight and downlight at the same time, regardless of their current state.

The default values result in both zones being reset to neutral white at 100% brightness.

To turn off either zone, set the brightness for that zone to 0.

The following table lists the available fields and allowed range of values for each:

| Field name   | Unit | Value |
| ------------ | ---- | -------------
| `config_entry` |      | Use Developer Tools to select the config entry, then switch to YAML view. |
| `downlight_hue`| degree | 0 - 360 |
| `downlight_saturation` | % | 0 - 100 |
| `downlight_brightness` | % | 0 - 100 |
| `downlight_kelvin` | K | 1500 - 9000 |
| `uplight_hue`| degree | 0 - 360 |
| `uplight_saturation` | % | 0 - 100 |
| `uplight_brightness` | % | 0 - 100 |
| `uplight_kelvin` | K | 1500 - 9000 |
| `transition` | seconds | 0 - 3600 |

Sample YAML to turn the downlight off and turn the uplight on at full brightness in red:

```yaml
action: lifx_ceiling.set_state
data:
  config_entry: XXXXXXXXXXXXXX
  downlight_hue: 0
  downlight_saturation: 0
  downlight_brightness: 0
  downlight_kelvin: 3500
  uplight_hue: 0
  uplight_saturation: 100
  uplight_brightness: 100
  uplight_kelvin: 3500
  transition: 1
```

## Known issues/caveats

1. To turn on just the uplight or downlight without any surprises, use the `lifx_ceiling.set_state` action with the brightness
   of the zone you don't want to turn on set to 0.

1. If you use the `light.turn_on` action, you should explicitly specify the brightness and color or color temp to use.
    - If neither `brightness` nor `brightness_pct` are  used, the light will turn on at full (100%) brightness.
    - If neither `hs_color` nor `color_temp_kelvin` are used, the light will turn on in color temperature mode set to 3500K (neutral).
    - I strongly encourage you to set `transition` to at least `0.25` (or higher) with both `light.turn_on` and `light.turn_off` to make the process less jarring.

1. Turning the main light entity on or off or using `light.turn_on` or `light.turn_off` is a good way to reset both to the same state.

1. Scenes should work with version `2025.2.0-beta1` and higher if the scene is recreated.
    ~~Scenes created in homeHome Assistant are unlikely to work at all, let alone reliably.~~

1. Light state should be reflected correctly when a change is made within 10 seconds for the uplight and downlight from version `2025.2.0-beta1`.
  ~~Adding the uplight or downlight to your Dashboard is discouraged as the state can be up to 10 seconds behind reality and may bounce between `off` and `on` a few times when the state changes.~~


## Issues? Bugs?

Please use discussions and issues to check if the issue or bug is already known and if not, please report it.
