# tests/test_fatigue.py
import os
import sys
import pytest

# Add src directory to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from fatigue import ReplayFatigueSuppressor

@pytest.fixture
def suppressor():
    # default threshold=5, suppression_factor=0.5
    return ReplayFatigueSuppressor(fatigue_threshold=2, suppression_factor=0.5)

@pytest.fixture
def sample_simulations():
    # create two simulations with distinct ids
    return [
        {"id": "sim1", "replay_weight": 1.0},
        {"id": "sim2", "replay_weight": 2.0}
    ]


def test_no_suppression_below_threshold(suppressor, sample_simulations):
    # apply_fatigue first time: counts =1 <= threshold, no suppression
    sims = suppressor.apply_fatigue(list(sample_simulations))
    for sim, orig in zip(sims, sample_simulations):
        assert sim["fatigue_flag"] is False
        assert sim["replay_weight"] == orig["replay_weight"]


def test_suppression_after_threshold_exceeded(suppressor, sample_simulations):
    # apply threshold+1 times to trigger suppression
    threshold = suppressor.fatigue_threshold
    # operate on a fresh copy of simulations
    sims = list(sample_simulations)
    # record original weights
    orig_weights = [sim["replay_weight"] for sim in sims]
    for _ in range(threshold + 1):
        sims = suppressor.apply_fatigue(sims)
    # now fatigue_flag True and weight suppressed once
    for idx, sim in enumerate(sims):
        assert sim["fatigue_flag"] is True
        expected_weight = orig_weights[idx] * suppressor.suppression_factor
        assert sim["replay_weight"] == pytest.approx(expected_weight)



def test_reset_fatigue(suppressor, sample_simulations):
    # trigger fatigue for sim1
    sims = list(sample_simulations)
    for _ in range(suppressor.fatigue_threshold + 1):
        sims = suppressor.apply_fatigue(sims)
    # reset sim1\
    suppressor.reset_fatigue("sim1")
    # next apply should not suppress sim1 again
    sims = suppressor.apply_fatigue(sims)
    # sim1 count reset, so flag False again
    sim1 = next(s for s in sims if s["id"] == "sim1")
    assert sim1["fatigue_flag"] is False


def test_counts_are_tracked_separately(suppressor, sample_simulations):
    sims = list(sample_simulations)
    # apply once: both at count=1
    suppressor.apply_fatigue(sims)
    # apply with only sim1: count only for sim1 increments
    suppressor.apply_fatigue([sims[0]])
    assert suppressor.replay_counts["sim1"] == 2
    assert suppressor.replay_counts["sim2"] == 1
