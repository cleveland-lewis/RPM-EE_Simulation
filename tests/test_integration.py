import os
import sys

# Add src directory to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from src.simulation import run_simulation


def test_integration_smoke_run():
    episodes = 3
    logs = run_simulation(total_ticks=episodes)

    # Should return a list of dicts with length equal to episodes
    assert isinstance(logs, list), "run_simulation() should return a list"
    assert len(logs) == episodes, f"Expected {episodes} log entries, got {len(logs)}"

    required_keys = {'clock', 'attunement_score', 'schema_stress', 'avg_affect_feedback', 'memory_config', 'memory_stats'}
    for entry in logs:
        assert isinstance(entry, dict), "Each log entry must be a dict"
        missing = required_keys - set(entry.keys())
        assert not missing, f"Missing keys in integration log entry: {missing}"

    # Run again with different number of episodes
    logs2 = run_simulation(total_ticks=5)
    assert isinstance(logs2, list)
    assert len(logs2) == 5