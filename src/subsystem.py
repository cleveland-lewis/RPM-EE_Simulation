"""Subsystem interface for simulation components."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Subsystem(Protocol):
    """Minimal contract for simulation subsystems."""

    def reset(self) -> None:
        """Reset internal state for a new run."""

    def step(self, tick: int) -> None:
        """Advance subsystem by one simulation tick."""

    def snapshot(self) -> dict:
        """Return a serializable view of subsystem state."""


__all__ = ["Subsystem"]
