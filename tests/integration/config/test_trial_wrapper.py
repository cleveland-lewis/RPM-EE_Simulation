"""
Unit tests for trial_wrapper.py
"""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src import trial_wrapper, TrialSimulator, DualTaskSimulator, quick_trial


def test_single_trial():
    """Test basic trial execution."""
    sim = TrialSimulator(preset='default', seed=42)
    result = sim.run_trial(stimulus={'difficulty': 0.5}, duration=200)

    assert 'RT' in result
    assert 'accuracy' in result
    assert 'attunement_mean' in result
    assert result['RT'] > 0
    assert 0 <= result['accuracy'] <= 1


def test_RT_inversely_related_to_attunement():
    """Test that higher attunement → faster RT."""
    sim = TrialSimulator(preset='default', seed=42)

    # Easy trial (should have higher attunement, faster RT)
    easy = sim.run_trial(stimulus={'difficulty': 0.2}, duration=200)

    # Hard trial (should have lower attunement, slower RT)
    hard = sim.run_trial(stimulus={'difficulty': 0.9}, duration=200)

    # On average over many trials, easy should be faster
    # (single trials may vary, so we'll test with averages)
    easy_RTs = []
    hard_RTs = []

    for _ in range(20):
        easy_RTs.append(sim.run_trial(stimulus={'difficulty': 0.2}, duration=200)['RT'])
        hard_RTs.append(sim.run_trial(stimulus={'difficulty': 0.9}, duration=200)['RT'])

    assert np.mean(easy_RTs) < np.mean(hard_RTs), "Easy trials should be faster on average"


def test_reproducibility():
    """Test that same seed gives same results."""
    result1 = quick_trial(preset='default', difficulty=0.5, duration=200, seed=123)
    result2 = quick_trial(preset='default', difficulty=0.5, duration=200, seed=123)

    assert result1['RT'] == result2['RT']
    assert result1['accuracy'] == result2['accuracy']


def test_trial_history():
    """Test that trial history is tracked correctly."""
    sim = TrialSimulator(preset='default', seed=42)

    assert len(sim.trial_history) == 0

    sim.run_trial(stimulus={}, duration=200)
    sim.run_trial(stimulus={}, duration=200)
    sim.run_trial(stimulus={}, duration=200)

    assert len(sim.trial_history) == 3
    assert sim.trial_count == 3


def test_reset():
    """Test reset functionality."""
    sim = TrialSimulator(preset='default', seed=42)

    sim.run_trial(stimulus={}, duration=200)
    sim.run_trial(stimulus={}, duration=200)

    assert sim.trial_count == 2

    sim.reset()

    assert sim.trial_count == 0
    assert len(sim.trial_history) == 0


def test_summary_statistics():
    """Test summary statistics computation."""
    sim = TrialSimulator(preset='default', seed=42)

    for _ in range(10):
        sim.run_trial(stimulus={'difficulty': 0.5}, duration=200)

    stats = sim.summary_statistics()

    assert stats['n_trials'] == 10
    assert 'mean_RT' in stats
    assert 'mean_accuracy' in stats
    assert stats['mean_RT'] > 0


def test_dual_task_design():
    """Test dual-task trial design creation."""
    sim = DualTaskSimulator(preset='default', seed=42)

    trials = sim.create_trial_design(
        ext_load_levels=[0.3, 0.6],
        mem_load_levels=[0.3, 0.6],
        n_reps=2
    )

    # Should be 2 ext × 2 mem × 2 reps = 8 trials
    assert len(trials) == 8

    # Check structure
    assert all('stimulus' in t for t in trials)
    assert all('duration' in t for t in trials)


def test_clinical_presets_differ():
    """Test that different presets produce different behavior."""
    n_trials = 20
    difficulty = 0.7

    nt_RTs = []
    asd_RTs = []

    nt_sim = TrialSimulator(preset='default', seed=42)
    asd_sim = TrialSimulator(preset='asd_typical', seed=42)

    for _ in range(n_trials):
        nt_RTs.append(nt_sim.run_trial(stimulus={'difficulty': difficulty}, duration=200)['RT'])
        asd_RTs.append(asd_sim.run_trial(stimulus={'difficulty': difficulty}, duration=200)['RT'])

    # Distributions should be different (not necessarily mean, but variance or range)
    # Use Kolmogorov-Smirnov test if scipy available, otherwise just check variance
    try:
        from scipy import stats
        stat, p_value = stats.ks_2samp(nt_RTs, asd_RTs)
        # Some difference should be detectable
    except ImportError:
        # Fallback: just check that variance is different
        pass

    # At least variance should differ between presets
    assert np.std(nt_RTs) != np.std(asd_RTs), "Presets should produce different variability"


def test_run_experiment():
    """Test run_experiment method with trial list."""
    sim = TrialSimulator(preset='default', seed=42)

    trial_list = [
        {'stimulus': {'difficulty': 0.3}, 'duration': 200},
        {'stimulus': {'difficulty': 0.5}, 'duration': 200},
        {'stimulus': {'difficulty': 0.7}, 'duration': 200},
    ]

    results = sim.run_experiment(trial_list, progress=False)

    assert len(results) == 3
    assert all('RT' in r for r in results)
    assert all('accuracy' in r for r in results)


def test_RT_bounds():
    """Test that RTs stay within biologically plausible bounds."""
    sim = TrialSimulator(preset='default', seed=42)

    RTs = []
    for _ in range(50):
        result = sim.run_trial(stimulus={'difficulty': np.random.rand()}, duration=200)
        RTs.append(result['RT'])

    # All RTs should be between 200ms and 3000ms
    assert all(200 <= rt <= 3000 for rt in RTs), "RTs should be within [200, 3000]ms"


def test_accuracy_bounds():
    """Test that accuracy stays in [0,1] and is a probability, not arbitrary values."""
    sim = TrialSimulator(preset='default', seed=42)

    accs = []
    for _ in range(50):
        result = sim.run_trial(stimulus={'difficulty': np.random.rand()}, duration=200)
        accs.append(result['accuracy'])

    # All accuracies should be probabilities in [0,1]
    assert all(0.0 <= acc <= 1.0 for acc in accs), "Accuracy should be in [0,1]"
    # With continuous accuracy, we expect some values strictly between 0 and 1
    assert any(0.0 < acc < 1.0 for acc in accs), "Accuracy should not be purely binary under new model"


def test_trial_metadata():
    """Test that trial metadata is stored correctly."""
    sim = TrialSimulator(preset='default', seed=42)

    stimulus = {'difficulty': 0.6, 'test_param': 123}
    result = sim.run_trial(stimulus=stimulus, duration=250)

    assert result['trial_number'] == 1
    assert result['duration'] == 250
    assert result['preset'] == 'default'
    assert result['stimulus']['difficulty'] == 0.6
    assert result['stimulus']['test_param'] == 123


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
