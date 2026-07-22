"""Config flow for CCT Virtual Lights."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

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
    DOMAIN,
    MIX_MODE_CONSTANT_BRIGHTNESS,
    MIX_MODE_MAX_BRIGHTNESS,
    SCALE_UNIT_PERCENT,
)

MIX_MODE_OPTIONS = [MIX_MODE_CONSTANT_BRIGHTNESS, MIX_MODE_MAX_BRIGHTNESS]


def _entity_selector() -> EntitySelector:
    return EntitySelector(EntitySelectorConfig(domain="light"))


def _normalize_entity_id(raw: Any) -> str:
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        entity_id = raw.get("entity_id")
        if isinstance(entity_id, str):
            return entity_id.strip()
    return str(raw).strip()


def _is_percent_mode(defaults: dict[str, Any]) -> bool:
    return defaults.get(CONF_SCALE_UNIT) == SCALE_UNIT_PERCENT


def _scale_default(defaults: dict[str, Any], key: str) -> float:
    value = defaults.get(key)
    if value is None:
        return DEFAULT_WARM_SCALE_PERCENT if key == CONF_WARM_SCALE else DEFAULT_COLD_SCALE_PERCENT

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return DEFAULT_WARM_SCALE_PERCENT if key == CONF_WARM_SCALE else DEFAULT_COLD_SCALE_PERCENT

    if _is_percent_mode(defaults):
        return numeric

    # Legacy entries stored calibration as a multiplier (1.0 == 100%).
    return round(numeric * 100.0, 3)


def _base_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "CCT Light")): str,
            vol.Required(CONF_WARM_ENTITY, default=_normalize_entity_id(defaults.get(CONF_WARM_ENTITY, ""))): _entity_selector(),
            vol.Required(CONF_COLD_ENTITY, default=_normalize_entity_id(defaults.get(CONF_COLD_ENTITY, ""))): _entity_selector(),
            vol.Required(CONF_WARM_KELVIN, default=defaults.get(CONF_WARM_KELVIN, DEFAULT_WARM_KELVIN)): vol.All(
                vol.Coerce(int), vol.Range(min=1000, max=10000)
            ),
            vol.Required(CONF_COLD_KELVIN, default=defaults.get(CONF_COLD_KELVIN, DEFAULT_COLD_KELVIN)): vol.All(
                vol.Coerce(int), vol.Range(min=1000, max=10000)
            ),
            vol.Required(CONF_MIX_MODE, default=defaults.get(CONF_MIX_MODE, DEFAULT_MIX_MODE)): vol.In(
                MIX_MODE_OPTIONS
            ),
            vol.Required(CONF_GAMMA, default=defaults.get(CONF_GAMMA, DEFAULT_GAMMA)): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=5.0)
            ),
            vol.Required(CONF_WARM_SCALE, default=_scale_default(defaults, CONF_WARM_SCALE)): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=100.0)
            ),
            vol.Required(CONF_COLD_SCALE, default=_scale_default(defaults, CONF_COLD_SCALE)): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=100.0)
            ),
            vol.Required(CONF_TRANSITION_SECONDS, default=defaults.get(CONF_TRANSITION_SECONDS, DEFAULT_TRANSITION_SECONDS)): vol.All(
                vol.Coerce(float), vol.Range(min=0.0, max=60.0)
            ),
        }
    )


class CctVirtualLightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for one virtual CCT light."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show the user form."""
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized_input = {
                **user_input,
                CONF_WARM_ENTITY: _normalize_entity_id(user_input[CONF_WARM_ENTITY]),
                CONF_COLD_ENTITY: _normalize_entity_id(user_input[CONF_COLD_ENTITY]),
                CONF_SCALE_UNIT: SCALE_UNIT_PERCENT,
            }
            if normalized_input[CONF_WARM_KELVIN] >= normalized_input[CONF_COLD_KELVIN]:
                errors["base"] = "warm_must_be_colder_than_cold"
            else:
                return self.async_create_entry(title=normalized_input[CONF_NAME], data=normalized_input)

        return self.async_show_form(step_id="user", data_schema=_base_schema({}), errors=errors)


class CctVirtualLightsOptionsFlow(OptionsFlowWithReload):
    """Manage options for a configured virtual CCT light."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized_input = {
                **user_input,
                CONF_WARM_ENTITY: _normalize_entity_id(user_input[CONF_WARM_ENTITY]),
                CONF_COLD_ENTITY: _normalize_entity_id(user_input[CONF_COLD_ENTITY]),
                CONF_SCALE_UNIT: SCALE_UNIT_PERCENT,
            }
            if normalized_input[CONF_WARM_KELVIN] >= normalized_input[CONF_COLD_KELVIN]:
                errors["base"] = "warm_must_be_colder_than_cold"
            else:
                return self.async_create_entry(data=normalized_input)

        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_base_schema(defaults),
            errors=errors,
        )


@callback
def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlowWithReload:
    """Create the options flow."""
    return CctVirtualLightsOptionsFlow(config_entry)
