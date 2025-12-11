import random

import numpy as np
import pytest

from src.randomness import seed_everything
from src.sensory import SensoryInputSystem
from src.simulation import run_simulation


def test_seed_everything_streams_repeatable():
    first = seed_everything(123)
    second = seed_everything(123)

    assert first.master_seed == second.master_seed == 123
    assert first.python_seed == second.python_seed
    assert first.numpy_seed == second.numpy_seed
    assert abs(first.py_random.random() - second.py_random.random()) < 1e-9
    assert np.allclose(first.np_random.random(3), second.np_random.random(3))


def test_run_simulation_repeatable_with_seed():
    out1 = run_simulation(total_ticks=20, seed=777, bin_size=1)
    out2 = run_simulation(total_ticks=20, seed=777, bin_size=1)

    assert out1['diagnostics']['seed'] == 777
    assert out2['diagnostics']['seed'] == 777
    assert out1['logs'] == out2['logs']

    out3 = run_simulation(total_ticks=20, seed=778, bin_size=1)
    assert out1['logs'] != out3['logs']


def test_run_simulation_records_generated_seed():
    out = run_simulation(total_ticks=5, seed=None, bin_size=1)
    assert isinstance(out['diagnostics']['seed'], int)


def test_sensory_system_respects_provided_rngs():
    def _build():
        streams = seed_everything(2025)
        py_seed, np_seed = streams.spawn(2)
        return SensoryInputSystem(
            event_rate=2,
            senses_count_range=(2, 2),
            py_random=random.Random(py_seed),
            np_random=np.random.default_rng(np_seed),
        )

    sis1 = _build()
    sis2 = _build()

    res1 = sis1.tick()
    res2 = sis2.tick()

    numeric_keys = ('attunement_score', 'schema_stress', 'avg_affect_feedback')
    for key in numeric_keys:
        assert res1[key] == pytest.approx(res2[key])
    assert res1['short_term_size'] == res2['short_term_size']
    assert res1['long_term_size'] == res2['long_term_size']
