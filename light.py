"""Light platform setup for CCT Virtual Light."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .backend import ChannelTarget, LightBackend
from .const import (
    CONF_COLD_ENTITY,
    CONF_COLD_KELVIN,
    CONF_COLD_SCALE,
    CONF_GAMMA,
    CONF_MIX_MODE,
    CONF_NAME,
    CONF_SCALE_UNIT,
    CONF_TRANSITION_SECONDS,
    CONF_WARM_ENTITY,
    CONF_WARM_KELVIN,
    CONF_WARM_SCALE,
    DEFAULT_COLD_KELVIN,
    DEFAULT_COLD_SCALE_PERCENT,
    DEFAULT_GAMMA,
    DEFAULT_MIX_MODE,
    DEFAULT_TRANSITION_SECONDS,
    DEFAULT_WARM_KELVIN,
    DEFAULT_WARM_SCALE_PERCENT,
    SCALE_UNIT_FACTOR,
)
from .entity import CctVirtualLight
from .mixer import CctMixer, MixerConfig


def _normalize_entity_id(raw: Any) -> str:
    """Normalize entity-selector output to a plain entity ID."""
    if isinstance(raw, str):
        return raw.strip()

    if isinstance(raw, dict):
        entity_id = raw.get("entity_id")
        if isinstance(entity_id, str):
            return entity_id.strip()

    return str(raw).strip()


def _as_float(value: Any, default: float) -> float:
    """Return a float value or the supplied default."""
    try:
        return float(default if value is None else value)
    except (TypeError, ValueError):
        return default


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one virtual CCT light from a config entry."""
    data = {**config_entry.data, **config_entry.options}

    warm_entity = _normalize_entity_id(data[CONF_WARM_ENTITY])
    cold_entity = _normalize_entity_id(data[CONF_COLD_ENTITY])
    warm_kelvin = int(data.get(CONF_WARM_KELVIN, DEFAULT_WARM_KELVIN))
    cold_kelvin = int(data.get(CONF_COLD_KELVIN, DEFAULT_COLD_KELVIN))
    warm_scale = _as_float(
        data.get(CONF_WARM_SCALE, DEFAULT_WARM_SCALE_PERCENT),
        DEFAULT_WARM_SCALE_PERCENT,
    )
    cold_scale = _as_float(
        data.get(CONF_COLD_SCALE, DEFAULT_COLD_SCALE_PERCENT),
        DEFAULT_COLD_SCALE_PERCENT,
    )
    scale_unit = str(data.get(CONF_SCALE_UNIT, SCALE_UNIT_FACTOR))
    mix_mode = str(data.get(CONF_MIX_MODE, DEFAULT_MIX_MODE))

    mixer = CctMixer(
        MixerConfig(
            warm_kelvin=warm_kelvin,
            cold_kelvin=cold_kelvin,
            warm_scale=warm_scale,
            cold_scale=cold_scale,
            scale_unit=scale_unit,
            mix_mode=mix_mode,
        )
    )
    backend = LightBackend(
        hass,
        ChannelTarget(warm_entity),
        ChannelTarget(cold_entity),
    )

    async_add_entities(
        [
            CctVirtualLight(
                name=str(data[CONF_NAME]),
                unique_id=config_entry.entry_id,
                backend=backend,
                mixer=mixer,
                warm_kelvin=warm_kelvin,
                cold_kelvin=cold_kelvin,
                mix_mode=mix_mode,
                gamma=_as_float(data.get(CONF_GAMMA, DEFAULT_GAMMA), DEFAULT_GAMMA),
                warm_scale=warm_scale,
                cold_scale=cold_scale,
                scale_unit=scale_unit,
                transition_seconds=_as_float(
                    data.get(CONF_TRANSITION_SECONDS, DEFAULT_TRANSITION_SECONDS),
                    DEFAULT_TRANSITION_SECONDS,
                ),
            )
        ]
    )