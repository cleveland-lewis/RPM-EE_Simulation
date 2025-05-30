import os
import sys
import pytest

# Add src directory to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from src.simulation import run_simulation


def test_integration_smoke_run():
    """
    Integration smoke test: run the full RPM-EE simulation for a few episodes
    and verify it completes without errors and produces the correct logs.
    """
    sim = run_simulation()
    # Run a small number of episodes
    episodes = 3
    logs = sim.run(episodes=episodes)
    # Ensure run() returns a list
    assert isinstance(logs, list), "run() should return a list"
    # Ensure logs attribute also populated
    assert hasattr(sim, 'logs'), "sim.logs attribute should exist"
    # Both returned logs and sim.logs should have length equal to episodes
    assert len(logs) == episodes, f"Expected {episodes} log entries, got {len(logs)}"
    assert len(sim.logs) == episodes, f"Expected sim.logs length {episodes}, got {len(sim.logs)}"
    # Verify each entry contains minimal required keys
    required_keys = {'clock', 'attunement_score', 'schema_stress', 'replay_mode'}
    for entry in logs:
        assert isinstance(entry, dict), "Each log entry must be a dict"
        missing = required_keys - set(entry.keys())
        assert not missing, f"Missing keys in integration log entry: {missing}"

    # Call again to ensure simulation is reentrant
    sim2 = RPMEESimulation()
    logs2 = sim2.run(episodes=1)
    assert isinstance(logs2, list)
    assert len(logs2) == 1
