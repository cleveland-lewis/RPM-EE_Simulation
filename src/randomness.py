"""
Centralized RNG helpers to keep RPM-EE runs reproducible.

We fan out a single master seed into independent streams for:
- Python's `random`
- NumPy (legacy global RNG and `default_rng`)
- JAX (when available)

Using a single entry point avoids fragmented seeding across modules and keeps
backends consistent.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, List, Optional

import numpy as np

try:  # Optional JAX; we only create keys when the import works.
    from jax import random as jax_random

    HAVE_JAX = True
except ImportError:  # pragma: no cover - guarded optional dependency
    HAVE_JAX = False
    jax_random = None  # type: ignore


def _spawn_seeds(master_seed: int, n: int) -> List[int]:
    """Derive `n` deterministic child seeds from a master seed."""
    seq = np.random.SeedSequence(master_seed)
    return [int(child.generate_state(1)[0]) for child in seq.spawn(n)]


@dataclass
class RNGStreams:
    """Bundle of reproducible RNG streams derived from one master seed."""

    master_seed: int
    python_seed: int
    numpy_seed: int
    jax_seed: Optional[int]
    py_random: random.Random
    np_random: np.random.Generator
    jax_key: Any | None = None

    def spawn(self, n: int) -> List[int]:
        """Generate deterministic child seeds (useful for multi-run sweeps)."""
        return _spawn_seeds(self.master_seed, n)


def seed_everything(seed: Optional[int]) -> RNGStreams:
    """
    Create aligned RNG streams (python, numpy, jax) from a single seed.

    When `seed` is None, generates a time-based master seed so the value can
    be recorded and reused for exact replication.
    """
    master_seed = int(seed) if seed is not None else int(time.time_ns() % (2**32 - 1))
    py_seed, np_seed, jax_seed = _spawn_seeds(master_seed, 3)

    # Seed global states for modules that rely on the global RNGs.
    random.seed(py_seed)
    np.random.seed(np_seed)

    py_rng = random.Random(py_seed)
    np_rng = np.random.default_rng(np_seed)
    jax_key = jax_random.PRNGKey(jax_seed) if HAVE_JAX else None

    return RNGStreams(
        master_seed=master_seed,
        python_seed=py_seed,
        numpy_seed=np_seed,
        jax_seed=jax_seed if HAVE_JAX else None,
        py_random=py_rng,
        np_random=np_rng,
        jax_key=jax_key,
    )
