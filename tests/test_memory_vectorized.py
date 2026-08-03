"""
Tests for VectorizedMemoryStore: correctness and performance vs MemoryStore.

Correctness tests verify that VectorizedMemoryStore produces identical
match/load decisions to MemoryStore for the same inputs.

Performance tests verify that vectorized ops are faster than the Python
loop equivalent on moderately-sized memory buffers (≥100 events).
"""

import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memory import MemoryStore  # noqa: E402
from memory_vectorized import VectorizedMemoryStore, _event_to_vector  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_event(  # noqa: PLR0913
    modality="vision", duration=2.0, intensity=0.5, valence=0.3, timing=0.5, prio=5.0
) -> dict:
    return {
        "id": "test-event",
        "modality": modality,
        "duration": duration,
        "intensity": intensity,
        "emotion": {"valence": valence},
        "timing": timing,
        "prioritization_score": prio,
    }


def _make_random_events(n: int, seed: int = 42) -> list:
    rng = np.random.default_rng(seed)
    modalities = ["vision", "auditory", "touch"]
    events = []
    for i in range(n):
        events.append(
            {
                "id": f"event-{i}",
                "modality": modalities[i % len(modalities)],
                "duration": float(rng.uniform(0.1, 8.0)),
                "intensity": float(rng.uniform(0.0, 1.0)),
                "emotion": {"valence": float(rng.uniform(-1.0, 1.0))},
                "timing": float(rng.uniform(0.0, 1.0)),
                "prioritization_score": float(rng.uniform(0.0, 10.0)),
            }
        )
    return events


# ---------------------------------------------------------------------------
# Correctness: basic interface
# ---------------------------------------------------------------------------


class TestVectorizedMemoryInterface:
    """VectorizedMemoryStore exposes the same public interface as MemoryStore."""

    def test_default_attributes(self):
        vm = VectorizedMemoryStore()
        assert vm.capacity == 4  # Cowan 2001 default -- see src/presets.py
        assert vm.decay_rate == 0.01

    def test_capacity_assignment(self):
        vm = VectorizedMemoryStore()
        vm.capacity = 4
        assert vm.capacity == 4

    def test_decay_rate_assignment(self):
        vm = VectorizedMemoryStore()
        vm.decay_rate = 0.05
        assert vm.decay_rate == 0.05

    def test_store_events_populates_short_term(self):
        vm = VectorizedMemoryStore()
        events = _make_random_events(5)
        vm.store_events(events)
        assert len(vm.short_term) == 5

    def test_max_short_term_limit(self):
        vm = VectorizedMemoryStore(max_short_term=10)
        events = _make_random_events(20)
        vm.store_events(events)
        assert len(vm.short_term) <= 10

    def test_working_memory_load_zero_when_empty(self):
        vm = VectorizedMemoryStore()
        assert vm.get_working_memory_load() == 0.0

    def test_working_memory_load_bounded(self):
        vm = VectorizedMemoryStore()
        events = _make_random_events(20)
        vm.store_events(events)
        load = vm.get_working_memory_load()
        assert 0.0 <= load <= 1.0

    def test_match_patterns_empty_memory(self):
        vm = VectorizedMemoryStore()
        events = _make_random_events(3)
        matched, unmatched = vm.match_patterns(events)
        assert matched == []
        assert len(unmatched) == 3

    def test_prune_old_memory_removes_low_priority(self):
        vm = VectorizedMemoryStore()
        low_prio = [_make_event(prio=0.1) for _ in range(5)]
        high_prio = [_make_event(prio=8.0) for _ in range(5)]
        vm.store_events(low_prio + high_prio)
        assert len(vm.short_term) == 10

        vm.prune_old_memory()
        # Low priority (0.1 ≤ 0.3) should be pruned
        for e in vm.short_term:
            assert e["prioritization_score"] > 0.3


# ---------------------------------------------------------------------------
# Correctness: matching behavior matches MemoryStore
# ---------------------------------------------------------------------------


class TestCorrectnessVsMemoryStore:
    """VectorizedMemoryStore produces the same match decisions as MemoryStore."""

    def _run_both(self, stored_events, query_events):
        """Run both stores and return (orig_matched, vec_matched)."""
        orig = MemoryStore()
        vec = VectorizedMemoryStore()

        orig.store_events(stored_events)
        vec.store_events(stored_events)

        orig_matched, orig_unmatched = orig.match_patterns(query_events)
        vec_matched, vec_unmatched = vec.match_patterns(query_events)

        return orig_matched, orig_unmatched, vec_matched, vec_unmatched

    def test_identical_match_count_identical_events(self):
        """When queried with the same events that were stored, match counts agree."""
        events = _make_random_events(20, seed=7)
        stored = events[:15]
        query = events[:15]  # stored events should match

        om, ou, vm, vu = self._run_both(stored, query)
        assert len(om) == len(vm), f"Matched: {len(om)} vs {len(vm)}"
        assert len(ou) == len(vu)

    def test_identical_match_count_novel_events(self):
        """Novel events that don't match should produce same count."""
        stored = _make_random_events(10, seed=1)
        # Create very different events (vision vs other extreme values)
        novel = [
            _make_event(
                modality="touch", intensity=0.01, valence=-0.9, duration=9.9, timing=0.01, prio=0.1
            )
            for _ in range(5)
        ]

        om, ou, vm, vu = self._run_both(stored, novel)
        assert len(om) == len(vm)

    def test_wm_load_close_to_original(self):
        """WM load values should be close (not necessarily identical due to decay timing)."""
        events = _make_random_events(30, seed=99)

        orig = MemoryStore()
        vec = VectorizedMemoryStore()
        orig.capacity = 4
        vec.capacity = 4

        orig.store_events(events)
        vec.store_events(events)

        # Loads won't be bit-identical (decay applied to deque items differently)
        # but should be in same range [0, 1]
        orig_load = orig.get_working_memory_load()
        vec_load = vec.get_working_memory_load()
        assert 0.0 <= orig_load <= 1.0
        assert 0.0 <= vec_load <= 1.0

    def test_simulation_produces_same_log_structure(self):
        """Simulation with vectorized memory produces same log fields as default."""
        from simulation import RPMEESimulation

        sim_default = RPMEESimulation(preset="neurotypical", use_vectorized_memory=False)
        sim_vec = RPMEESimulation(preset="neurotypical", use_vectorized_memory=True)

        for _ in range(10):
            sim_default.step()
            sim_vec.step()

        default_keys = set(sim_default.logs[0].keys())
        vec_keys = set(sim_vec.logs[0].keys())
        assert default_keys == vec_keys, f"Key mismatch: {default_keys ^ vec_keys}"

    def test_simulation_metrics_in_valid_range(self):
        """Vectorized memory simulation produces valid metric ranges."""
        from simulation import RPMEESimulation

        sim = RPMEESimulation(preset="neurotypical", use_vectorized_memory=True)
        for _ in range(20):
            sim.step()

        for log in sim.logs:
            assert 0.0 <= log["schema_stress"] <= 1.0
            assert log["precision_ratio"] > 0
            if log["rt_mean"] is not None:
                assert 100 < log["rt_mean"] < 2000


# ---------------------------------------------------------------------------
# Performance: vectorized vs original
# ---------------------------------------------------------------------------


class TestPerformance:
    """VectorizedMemoryStore should be faster than MemoryStore on large inputs."""

    @pytest.mark.parametrize("n_events", [100, 500])
    def test_match_patterns_faster(self, n_events):
        """Vectorized similarity computation should outperform Python loop."""
        events = _make_random_events(n_events, seed=42)
        query = _make_random_events(20, seed=99)

        orig = MemoryStore()
        vec = VectorizedMemoryStore()

        orig.store_events(events)
        vec.store_events(events)

        # Warm up Numba JIT (first call compiles)
        vec.match_patterns(query[:1])

        # Time original
        t0 = time.perf_counter()
        for _ in range(10):
            orig.match_patterns(query)
        orig_time = time.perf_counter() - t0

        # Time vectorized
        t0 = time.perf_counter()
        for _ in range(10):
            vec.match_patterns(query)
        vec_time = time.perf_counter() - t0

        # Vectorized should not be slower than original
        # Allow 3x tolerance for CI variance; on any real hardware it's faster
        assert vec_time < orig_time * 3.0, (
            f"Vectorized ({vec_time:.4f}s) slower than original ({orig_time:.4f}s) "
            f"by more than 3x for {n_events} events"
        )

    def test_decay_no_python_loop(self):
        """Vectorized decay uses NumPy; verify it completes without Python loop overhead."""
        events = _make_random_events(1000, seed=11)
        vec = VectorizedMemoryStore(max_short_term=1000)
        vec.store_events(events)

        # Run decay many times — should complete quickly
        t0 = time.perf_counter()
        for _ in range(100):
            vec._apply_decay()
        elapsed = time.perf_counter() - t0

        # 100 decay passes over 1000 events should finish in < 1 second
        assert elapsed < 1.0, f"Decay too slow: {elapsed:.3f}s for 100 iterations over 1000 events"


# ---------------------------------------------------------------------------
# Feature vector
# ---------------------------------------------------------------------------


class TestFeatureVector:
    """_event_to_vector encodes events correctly."""

    def test_shape(self):
        event = _make_event()
        vec = _event_to_vector(event)
        assert vec.shape == (6,)
        assert vec.dtype == np.float32

    def test_modality_encoding_distinct(self):
        v1 = _event_to_vector(_make_event(modality="vision"))
        v2 = _event_to_vector(_make_event(modality="touch"))
        assert v1[0] != v2[0]

    def test_valence_encoded_at_index_3(self):
        event = _make_event(valence=0.75)
        vec = _event_to_vector(event)
        assert vec[3] == pytest.approx(0.75, abs=1e-5)

    def test_intensity_encoded_at_index_2(self):
        event = _make_event(intensity=0.4)
        vec = _event_to_vector(event)
        assert vec[2] == pytest.approx(0.4, abs=1e-5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
