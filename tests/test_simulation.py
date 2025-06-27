from src.simulation import run_simulation
import pytest
from src import simulation

def test_run_populates_logs_list_and_correct_length():
    episodes = 5
    logs = run_simulation(total_ticks=episodes)
    assert isinstance(logs, list)
    assert len(logs) == episodes

def test_each_entry_has_required_keys():
    logs = run_simulation(total_ticks=1)
    entry = logs[0]
    required = {'clock', 'attunement_score', 'schema_stress', 'avg_affect_feedback', 'memory_config', 'memory_stats'}
    missing = required - set(entry.keys())
    assert not missing, f"Missing keys in log entry: {missing}"

def test_clock_indices_are_increasing():
    episodes = 4
    logs = run_simulation(total_ticks=episodes)
    clocks = [e.get('clock') for e in logs]
    assert all(isinstance(c, (int, float)) for c in clocks)
    assert clocks == sorted(clocks), f"Clock values not sorted: {clocks}"

def test_scores_non_negative_and_numeric():
    logs = run_simulation(total_ticks=10)
    for e in logs:
        att = e.get('attunement_score')
        stress = e.get('schema_stress')
        assert isinstance(att, (int, float)) and att >= 0.0
        assert isinstance(stress, (int, float)) and stress >= 0.0

def test_replay_mode_present_as_string_if_in_logs():
    logs = run_simulation(total_ticks=5)
    for e in logs:
        if 'replay_mode' in e:
            assert isinstance(e['replay_mode'], str)

def test_run_zero_episodes_returns_empty_list():
    logs = run_simulation(total_ticks=0)
    assert logs == []


# GPU integration test: ensure CuPy-based generator is used when appropriate
@pytest.mark.skipif(not simulation.USE_CUPY, reason="CuPy not installed; skipping GPU integration test")
def test_gpu_generator_used(monkeypatch):
    """
    Ensure that when total_ticks ≥ GPU_TICK_THRESHOLD and USE_CUPY=True,
    the CuPy-based generator `_generate_base_arrays_gpu` is invoked.
    """
    called = {"gpu": False}
    original_gpu = simulation._generate_base_arrays_gpu

    def fake_gpu(total_ticks):
        called["gpu"] = True
        return original_gpu(total_ticks)

    # Patch the GPU generator and force GPU path
    monkeypatch.setattr(simulation, "_generate_base_arrays_gpu", fake_gpu)
    monkeypatch.setattr(simulation, "USE_CUPY", True)

    # Run with just above the threshold
    simulation.run_simulation(total_ticks=simulation.GPU_TICK_THRESHOLD + 1)

    assert called["gpu"], "Expected _generate_base_arrays_gpu to be called for large total_ticks"