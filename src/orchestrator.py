"""Simulation orchestrator for coordinating subsystems."""

from __future__ import annotations

from typing import Iterable, Sequence

try:
    from .subsystem import Subsystem
except ImportError:
    from subsystem import Subsystem


class SimulationOrchestrator:
    """Lightweight coordinator for subsystem lifecycle and ticks."""

    def __init__(self, subsystems: Sequence[Subsystem]) -> None:
        self.subsystems = list(subsystems)

    def reset(self) -> None:
        for subsystem in self.subsystems:
            subsystem.reset()

    def step(self, tick: int) -> None:
        for subsystem in self.subsystems:
            subsystem.step(tick)

    def snapshot(self) -> dict:
        snapshot: dict = {}
        for idx, subsystem in enumerate(self.subsystems):
            key = getattr(subsystem, "name", None) or subsystem.__class__.__name__
            if key in snapshot:
                key = f"{key}_{idx}"
            snapshot[key] = subsystem.snapshot()
        return snapshot


__all__ = ["SimulationOrchestrator"]
