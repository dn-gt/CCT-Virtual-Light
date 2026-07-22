"""Transition handling for CCT Virtual Light."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from .backend import ChannelLevels, LightBackend


class TransitionController:
    """Run software transitions between two warm/cold channel states."""

    def __init__(
        self,
        backend: LightBackend,
        *,
        steps_per_second: int = 20,
        maximum_steps: int = 40,
    ) -> None:
        self._backend = backend
        self._steps_per_second = max(1, steps_per_second)
        self._maximum_steps = max(2, maximum_steps)

    async def async_apply(
        self,
        start: ChannelLevels,
        target: ChannelLevels,
        duration: float,
        progress_callback: Callable[[ChannelLevels], None] | None = None,
    ) -> None:
        """Apply target levels immediately or using a software fade."""
        duration = max(0.0, float(duration))
        start = start.clamped()
        target = target.clamped()

        if duration <= 0 or start == target:
            await self._backend.async_apply(target)
            if progress_callback is not None:
                progress_callback(target)
            return

        steps = max(
            2,
            min(
                self._maximum_steps,
                round(max(duration, 0.1) * self._steps_per_second),
            ),
        )

        for step in range(1, steps + 1):
            ratio = step / steps
            levels = ChannelLevels(
                warm=round(start.warm + (target.warm - start.warm) * ratio),
                cold=round(start.cold + (target.cold - start.cold) * ratio),
            )
            await self._backend.async_apply(levels)

            if progress_callback is not None:
                progress_callback(levels)

            if step < steps:
                await asyncio.sleep(duration / steps)