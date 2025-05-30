# tests/test_simulation.py
import os
import sys

import pytest

# Add src directory to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from src.simulation import run_simulation

@pytest.fixture
def system():
    return run_simulation()

def test_run_populates_logs_list_and_correct_length():
    sim = run_simulation()
    sim.run(episodes=5)
    logs = getattr(sim, 'logs', None)
    assert isinstance(logs, list), "sim.logs should be a list after run()"
    assert len(logs) == 5, f"Expected 5 log entries, got {len(logs)}"


def test_each_entry_has_required_keys():
    sim = run_simulation()
    sim.run(episodes=1)
    logs = sim.logs
    entry = logs[0]
    assert isinstance(entry, dict), "Each log entry must be a dict"
    # Core keys expected in each log
    required = {'clock', 'attunement_score', 'schema_stress'}
    missing = required - set(entry.keys())
    assert not missing, f"Missing keys in log entry: {missing}"


def test_clock_indices_are_increasing():
    sim = run_simulation()
    sim.run(episodes=4)
    logs = sim.logs
    clocks = [e.get('clock') for e in logs]
    # Ensure clock values are present and non-decreasing
    assert all(isinstance(c, (int, float)) for c in clocks), "Clock values must be numeric"
    assert clocks == sorted(clocks), f"Clock values not non-decreasing: {clocks}"


def test_scores_non_negative_and_numeric():
    sim = run_simulation()
    sim.run(episodes=10)
    logs = sim.logs
    for e in logs:
        att = e.get('attunement_score')
        stress = e.get('schema_stress')
        assert isinstance(att, (int, float)), f"attunement_score should be numeric, got {type(att)}"
        assert att >= 0.0, f"attunement_score {att} must be >= 0"
        assert isinstance(stress, (int, float)), f"schema_stress should be numeric, got {type(stress)}"
        assert stress >= 0.0, f"schema_stress {stress} must be >= 0"


def test_replay_mode_present_as_string_if_in_logs():
    sim = run_simulation()
    sim.run(episodes=5)
    logs = sim.logs
    for e in logs:
        if 'replay_mode' in e:
            mode = e['replay_mode']
            assert isinstance(mode, str), f"replay_mode should be a string, got {type(mode)}"


def test_run_zero_episodes_returns_empty_list_and_logs_attr_empty():
    sim = run_simulation()
    logs = sim.run(episodes=0)
    # run() should return an empty list
    assert logs == [], "Expected no log entries when episodes=0"
    # sim.logs attribute should also be empty list
    assert hasattr(sim, 'logs'), "sim.logs attribute should exist"
    assert sim.logs == [], "sim.logs should be empty when episodes=0"
