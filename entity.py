"""Light entity for CCT Virtual Light."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.const import STATE_ON
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import color as color_util

from .backend import ChannelLevels, LightBackend
from .const import (
    ATTR_COLD_LEVEL,
    ATTR_EFFECTIVE_BRIGHTNESS,
    ATTR_MIX_MODE,
    ATTR_WARM_LEVEL,
    SCALE_UNIT_PERCENT,
)
from .mixer import CctMixer
from .transition import TransitionController


class CctVirtualLight(RestoreEntity, LightEntity):
    """Mix two dimmable white channels into one CCT light."""

    _attr_has_entity_name = True
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(
        self,
        *,
        name: str,
        unique_id: str,
        backend: LightBackend,
        mixer: CctMixer,
        warm_kelvin: int,
        cold_kelvin: int,
        mix_mode: str,
        gamma: float,
        warm_scale: float,
        cold_scale: float,
        scale_unit: str,
        transition_seconds: float,
    ) -> None:
        """Initialize the virtual CCT light."""
        self._attr_name = name
        self._attr_unique_id = unique_id

        self._backend = backend
        self._mixer = mixer
        self._transition = TransitionController(backend)

        self._warm_kelvin = warm_kelvin
        self._cold_kelvin = cold_kelvin
        self._warm_mired = color_util.color_temperature_kelvin_to_mired(warm_kelvin)
        self._cold_mired = color_util.color_temperature_kelvin_to_mired(cold_kelvin)
        self._min_kelvin = min(warm_kelvin, cold_kelvin)
        self._max_kelvin = max(warm_kelvin, cold_kelvin)

        self._mix_mode = mix_mode
        self._gamma = gamma
        self._warm_scale_input = warm_scale
        self._cold_scale_input = cold_scale
        self._scale_unit = scale_unit
        self._warm_scale_factor = self._scale_to_factor(warm_scale, scale_unit)
        self._cold_scale_factor = self._scale_to_factor(cold_scale, scale_unit)
        self._transition_seconds = max(0.0, transition_seconds)

        self._is_on = False
        self._brightness = 255
        self._color_temp_kelvin = self._max_kelvin
        self._last_brightness = 255
        self._last_color_temp_kelvin = self._max_kelvin
        self._current_levels = ChannelLevels(0, 0)

    @staticmethod
    def _scale_to_factor(scale: float, scale_unit: str) -> float:
        """Convert a stored scale value to a factor for diagnostics."""
        if scale_unit == SCALE_UNIT_PERCENT:
            return max(0.0, scale) / 100.0
        return max(0.0, scale)

    @property
    def is_on(self) -> bool:
        """Return whether the virtual light is on."""
        return self._is_on

    @property
    def brightness(self) -> int | None:
        """Return the current Home Assistant brightness."""
        return self._brightness if self._is_on else None

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the current color temperature in Kelvin."""
        return self._color_temp_kelvin if self._is_on else None

    @property
    def min_color_temp_kelvin(self) -> int:
        """Return the warmest configured channel temperature."""
        return self._min_kelvin

    @property
    def max_color_temp_kelvin(self) -> int:
        """Return the coldest configured channel temperature."""
        return self._max_kelvin

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic attributes."""
        return {
            "warm_entity": self._backend.warm_entity_id,
            "cold_entity": self._backend.cold_entity_id,
            "warm_kelvin": self._warm_kelvin,
            "cold_kelvin": self._cold_kelvin,
            "warm_mired": self._warm_mired,
            "cold_mired": self._cold_mired,
            "warm_scale_percent": round(self._warm_scale_input, 3),
            "cold_scale_percent": round(self._cold_scale_input, 3),
            "warm_scale_factor": round(self._warm_scale_factor, 5),
            "cold_scale_factor": round(self._cold_scale_factor, 5),
            "scale_unit": self._scale_unit,
            "transition_seconds": self._transition_seconds,
            "gamma": self._gamma,
            ATTR_MIX_MODE: self._mix_mode,
            ATTR_WARM_LEVEL: self._current_levels.warm,
            ATTR_COLD_LEVEL: self._current_levels.cold,
            ATTR_EFFECTIVE_BRIGHTNESS: self._brightness if self._is_on else 0,
            "last_brightness": self._last_brightness,
            "last_color_temp_kelvin": self._last_color_temp_kelvin,
        }

    async def async_added_to_hass(self) -> None:
        """Restore the last known state when Home Assistant starts."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        self._is_on = last_state.state == STATE_ON

        last_brightness = last_state.attributes.get(ATTR_BRIGHTNESS)
        if last_brightness is not None:
            self._brightness = int(last_brightness)
            self._last_brightness = self._brightness

        last_kelvin = last_state.attributes.get(ATTR_COLOR_TEMP_KELVIN)
        if last_kelvin is not None:
            self._color_temp_kelvin = self._clamp_kelvin(int(last_kelvin))
            self._last_color_temp_kelvin = self._color_temp_kelvin

        target = self._calculate_levels()
        self._current_levels = target if self._is_on else ChannelLevels(0, 0)

        if self._is_on:
            await self._backend.async_apply(target)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on or adjust the virtual light."""
        was_on = self._is_on
        start_levels = self._current_levels if was_on else ChannelLevels(0, 0)

        brightness = int(
            kwargs.get(
                ATTR_BRIGHTNESS,
                self._brightness if self._brightness is not None else self._last_brightness or 255,
            )
        )
        kelvin = int(
            kwargs.get(
                ATTR_COLOR_TEMP_KELVIN,
                self._color_temp_kelvin
                if self._color_temp_kelvin is not None
                else self._last_color_temp_kelvin,
            )
        )

        self._brightness = max(1, min(255, brightness))
        self._last_brightness = self._brightness
        self._color_temp_kelvin = self._clamp_kelvin(kelvin)
        self._last_color_temp_kelvin = self._color_temp_kelvin
        self._is_on = True

        target = self._calculate_levels()
        await self._transition.async_apply(
            start_levels,
            target,
            self._resolve_transition(kwargs),
            self._set_current_levels,
        )

        self._current_levels = target
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off both backend channels."""
        start_levels = self._current_levels
        target = ChannelLevels(0, 0)

        await self._transition.async_apply(
            start_levels,
            target,
            self._resolve_transition(kwargs),
            self._set_current_levels,
        )

        self._current_levels = target
        self._is_on = False
        self.async_write_ha_state()

    def _calculate_levels(self) -> ChannelLevels:
        """Calculate current warm and cold levels through the CCT mixer."""
        warm, cold = self._mixer.calculate(
            self._brightness,
            self._color_temp_kelvin,
        )
        return ChannelLevels(warm, cold)

    def _set_current_levels(self, levels: ChannelLevels) -> None:
        """Update the internally tracked backend levels."""
        self._current_levels = levels

    def _resolve_transition(self, kwargs: dict[str, Any]) -> float:
        """Resolve a requested or configured transition duration."""
        transition = kwargs.get(ATTR_TRANSITION, self._transition_seconds)
        try:
            return max(0.0, float(transition))
        except (TypeError, ValueError):
            return self._transition_seconds

    def _clamp_kelvin(self, kelvin: int) -> int:
        """Clamp Kelvin to the configured channel range."""
        return max(self._min_kelvin, min(self._max_kelvin, kelvin))