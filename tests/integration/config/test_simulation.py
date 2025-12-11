import numpy as np
import pytest
from src.simulation import run_simulation


def _get_logs(result, expected_len: int | None = None):
    """Helper to unwrap run_simulation output into a list of per-tick dicts."""
    if isinstance(result, dict):
        logs = result.get("logs", [])
    else:
        logs = result
    assert isinstance(logs, list), "run_simulation should return a list or a dict with 'logs'"
    if expected_len is not None:
        assert len(logs) == expected_len, f"Expected {expected_len} log entries, got {len(logs)}"
    return logs


def test_run_populates_logs_list_and_correct_length():
    episodes = 5
    result = run_simulation(total_ticks=episodes)
    logs = _get_logs(result, expected_len=episodes)
    assert len(logs) == episodes


def test_each_entry_has_required_keys():
    result = run_simulation(total_ticks=10)
    logs = _get_logs(result, expected_len=10)
    entry = logs[0]
    # Minimal schema that should remain stable even as engine evolves
    required = {
        "clock",
        "attunement_score",
        "schema_stress",
        "avg_affect_feedback",
    }
    missing = required - set(entry.keys())
    assert not missing, f"Missing keys in log entry: {missing}"


def test_clock_indices_are_increasing():
    episodes = 8
    result = run_simulation(total_ticks=episodes)
    logs = _get_logs(result, expected_len=episodes)
    clocks = [e.get("clock") for e in logs]
    assert all(isinstance(c, (int, float)) for c in clocks)
    assert clocks == sorted(clocks), f"Clock values not sorted: {clocks}"


def test_scores_bounded_and_numeric():
    result = run_simulation(total_ticks=50)
    logs = _get_logs(result)
    for e in logs:
        att = e.get("attunement_score")
        stress = e.get("schema_stress")
        # Accept numpy scalar types in addition to Python scalars
        assert isinstance(att, (int, float, np.floating))
        assert isinstance(stress, (int, float, np.floating))
        # Engine now uses bounded link functions → values should live in [0,1]
        assert 0.0 <= att <= 1.0
        assert 0.0 <= stress <= 1.0


def test_replay_mode_present_as_string_if_in_logs():
    result = run_simulation(total_ticks=20)
    logs = _get_logs(result)
    for e in logs:
        if "replay_mode" in e:
            assert isinstance(e["replay_mode"], str)


def test_run_zero_episodes_returns_empty_list():
    result = run_simulation(total_ticks=0)
    assert result == []


def test_event_rate_affects_stress_profile():
    """Sanity check: changing event_rate should measurably change stress statistics.

    We do not assert a specific formula (the stress model is now multi-component),
    only that the engine is sensitive to this key knob.
    """
    seed = 123
    low = run_simulation(total_ticks=300, event_rate=1, seed=seed)
    high = run_simulation(total_ticks=300, event_rate=6, seed=seed)
    logs_low = _get_logs(low)
    logs_high = _get_logs(high)
    mean_low = np.mean([e["schema_stress"] for e in logs_low])
    mean_high = np.mean([e["schema_stress"] for e in logs_high])
    # Not necessarily ordered, but should not be numerically identical
    assert not np.isclose(mean_low, mean_high), "Stress should respond to event_rate changes"
