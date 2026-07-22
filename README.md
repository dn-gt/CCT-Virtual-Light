# CCT Virtual Lights

A Home Assistant custom integration that exposes a real color-temperature light entity and mixes two backend white channels.

## What is included

- `manifest.json`
- `__init__.py`
- `config_flow.py`
- `const.py`
- `light.py`
- translations for the setup form

## Current scope

This version already:

- creates a `ColorMode.COLOR_TEMP` light entity
- supports brightness and Kelvin color temperature
- uses Kelvin as the user-facing input while converting internally to Mired
- restores the last state after restart
- forwards the configured backend channel entities via `light.turn_on` / `light.turn_off`
- includes the two requested brightness modes:
  - `constant_brightness`
  - `max_brightness`
- supports Options Flow for later editing
- allows calibration as percent values with one decimal place
- supports a default transition time in seconds with one decimal place

## Folder layout

Place the `cct_virtual_lights` folder inside your Home Assistant `custom_components` directory.

```text
config/
└── custom_components/
    └── cct_virtual_lights/
        ├── __init__.py
        ├── config_flow.py
        ├── const.py
        ├── light.py
        ├── manifest.json
        └── translations/
            └── en.json
```

## Example configuration

Create one config entry in the UI and point it to two backend light entities, for example:

- warm: `light.kueche_ww`
- cold: `light.kueche_cw`

Suggested anchors:

- warm white: `2400 K`
- cold white: `5500 K`

Suggested calibration:

- warm channel scale: `100.0 %`
- cold channel scale: `100.0 %`
- default transition: `0.5 s`

## Next steps

Typical follow-up improvements are:

- calibration assistant
- additional curve options
- synchronization with externally changed backend channels
- HACS packaging and repository setup
