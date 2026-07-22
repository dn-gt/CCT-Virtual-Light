"""CCT mixing algorithms.

This module contains the complete mathematical conversion from

    Brightness + Kelvin

to

    Warm PWM + Cold PWM

No Home Assistant code should exist in this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.util import color as color_util

from .const import (
    MIX_MODE_CONSTANT_BRIGHTNESS,
    MIX_MODE_MAX_BRIGHTNESS,
    SCALE_UNIT_PERCENT,
)


PWM_MAX = 255.0


@dataclass(slots=True)
class MixerConfig:
    """Configuration for one virtual CCT light."""

    warm_kelvin: int
    cold_kelvin: int

    warm_scale: float
    cold_scale: float
    scale_unit: str

    mix_mode: str


class CctMixer:
    """Converts brightness + kelvin into WW/CW PWM values."""

    def __init__(self, config: MixerConfig) -> None:
        self._cfg = config

        self._warm_mired = color_util.color_temperature_kelvin_to_mired(
            config.warm_kelvin
        )

        self._cold_mired = color_util.color_temperature_kelvin_to_mired(
            config.cold_kelvin
        )

        self._warm_scale = self._scale_to_factor(config.warm_scale)
        self._cold_scale = self._scale_to_factor(config.cold_scale)

    @staticmethod
    def _scale_to_factor(scale: float) -> float:
        """Convert configuration scale into factor."""
        if scale > 5:
            # Stored as percent
            return scale / 100.0

        return scale

    def calculate(
        self,
        brightness: int,
        kelvin: int,
    ) -> tuple[int, int]:
        """Return warm/cold PWM levels."""

        color_position = self._color_position(kelvin)

        brightness = float(max(0, min(255, brightness)))

        if self._cfg.mix_mode == MIX_MODE_MAX_BRIGHTNESS:
            warm_share, cold_share = self._max_brightness(color_position)

            warm = (
                brightness
                * warm_share
                * self._warm_scale
            )

            cold = (
                brightness
                * cold_share
                * self._cold_scale
            )

        else:
            warm_share = 1.0 - color_position
            cold_share = color_position

            warm_weight = warm_share * self._warm_scale
            cold_weight = cold_share * self._cold_scale

            total = warm_weight + cold_weight

            if total <= 0:
                return 0, 0

            warm = brightness * warm_weight / total
            cold = brightness * cold_weight / total

        return (
            round(max(0.0, min(PWM_MAX, warm))),
            round(max(0.0, min(PWM_MAX, cold))),
        )

    def _color_position(self, kelvin: int) -> float:
        """Return position between warm and cold in mired space."""

        kelvin = max(
            min(kelvin, self._cfg.cold_kelvin),
            self._cfg.warm_kelvin,
        )

        target = color_util.color_temperature_kelvin_to_mired(
            kelvin
        )

        if self._warm_mired == self._cold_mired:
            return 0.0

        return max(
            0.0,
            min(
                1.0,
                (
                    self._warm_mired - target
                )
                / (
                    self._warm_mired - self._cold_mired
                ),
            ),
        )

    @staticmethod
    def _max_brightness(
        color_position: float,
    ) -> tuple[float, float]:
        """Brightness model for max_brightness mode."""

        if color_position <= 0.5:
            return (
                1.0,
                color_position / 0.5,
            )

        return (
            (1.0 - color_position) / 0.5,
            1.0,
        )