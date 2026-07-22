"""Backend channel control for CCT Virtual Light."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.core import HomeAssistant


@dataclass(frozen=True, slots=True)
class ChannelTarget:
    """A dimmable Home Assistant light used as one CCT channel."""

    entity_id: str


@dataclass(frozen=True, slots=True)
class ChannelLevels:
    """Brightness levels for the warm and cold channels."""

    warm: int
    cold: int

    def clamped(self) -> "ChannelLevels":
        """Return levels clamped to Home Assistant's 0..255 range."""
        return ChannelLevels(
            warm=max(0, min(255, int(self.warm))),
            cold=max(0, min(255, int(self.cold))),
        )


class LightBackend:
    """Apply calculated CCT levels to two Home Assistant light entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        warm: ChannelTarget,
        cold: ChannelTarget,
    ) -> None:
        self._hass = hass
        self._warm = warm
        self._cold = cold

    @property
    def warm_entity_id(self) -> str:
        """Return the warm-channel entity ID."""
        return self._warm.entity_id

    @property
    def cold_entity_id(self) -> str:
        """Return the cold-channel entity ID."""
        return self._cold.entity_id

    async def async_apply(self, levels: ChannelLevels) -> None:
        """Apply both channel levels in parallel."""
        levels = levels.clamped()
        await asyncio.gather(
            self._async_set_channel(self._warm.entity_id, levels.warm),
            self._async_set_channel(self._cold.entity_id, levels.cold),
        )

    async def _async_set_channel(self, entity_id: str, level: int) -> None:
        """Set one backend channel."""
        if level <= 0:
            await self._hass.services.async_call(
                "light",
                "turn_off",
                target={"entity_id": entity_id},
                blocking=True,
            )
            return

        await self._hass.services.async_call(
            "light",
            "turn_on",
            {ATTR_BRIGHTNESS: level},
            target={"entity_id": entity_id},
            blocking=True,
        )