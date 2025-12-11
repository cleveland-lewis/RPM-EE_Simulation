# tests/test_arbiter.py
import os
import sys
import pytest

# Add src directory to path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.arbiter import SimulationClusterArbiter

@pytest.fixture
def arbiter():
    # use specific weights for clarity; keep defaults for other knobs
    return SimulationClusterArbiter(alpha=0.4, beta=0.4, gamma=0.2)

@pytest.fixture
def sample_sims():
    # Three sims with known values
    return [
        {'id': 's1', 'plausibility': 0.5, 'emotional_prediction': 0.8, 'reward_distortion': 0.2},
        {'id': 's2', 'plausibility': 0.9, 'emotional_prediction': 0.1, 'reward_distortion': 0.7},
        {'id': 's3', 'plausibility': 0.2, 'emotional_prediction': 0.4, 'reward_distortion': 0.9}
    ]

def test_score_simulations_basic(arbiter, sample_sims):
    scored = arbiter.score_simulations(list(sample_sims))
    # Engine now uses additive plausibility/emotion, penalized distortion, and an inertia bonus.
    for sim in scored:
        t1 = sim['plausibility']
        t2 = sim['emotional_prediction']
        t3 = sim['reward_distortion']
        expected = 0.4 * t1 + 0.4 * t2 - 0.2 * t3 + 0.03
        assert sim['final_score'] == pytest.approx(expected)


def test_score_simulations_with_fatigue_suppression(arbiter):
    sims = [
        {'id': 's4', 'plausibility': 0.3, 'emotional_prediction': 0.6, 'reward_distortion': 0.8, 'fatigue_flag': True},
    ]
    scored = arbiter.score_simulations(sims)
    sim = scored[0]
    # Under fatigue, reward_distortion is down-weighted before penalty is applied.
    rd_eff = 0.8 * (1.0 - arbiter.k_fatigue * 1.0)
    expected = 0.4 * 0.3 + 0.4 * 0.6 - 0.2 * rd_eff + 0.03
    assert sim['final_score'] == pytest.approx(expected)


def test_sort_simulations(arbiter):
    sims = [
        {'id': 'a', 'final_score': 0.1},
        {'id': 'b', 'final_score': 0.9},
        {'id': 'c', 'final_score': 0.5}
    ]
    sorted_sims = arbiter.sort_simulations(list(sims))
    # Should be b, c, a
    assert [s['id'] for s in sorted_sims] == ['b', 'c', 'a']
