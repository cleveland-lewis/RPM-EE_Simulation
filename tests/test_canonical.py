import logging
import math
import random

import numpy as np
import pytest
import pandas as pd

from config import batch_runner
from src.memory import MemoryBuffer, LongTermStorage
from src.randomness import seed_everything
from src.simulation import run_simulation
from src.trial_wrapper import TrialSimulator
from src import nc_mcm_model
from src.simulation import _validate_fit_nc_mcm_inputs
from src.arbiter import SimulationClusterArbiter
from src.validation_metrics import validate_and_normalize_columns, ValidationSchemaError


def test_simulation_smoke_and_seed_recorded():
    out1 = run_simulation(total_ticks=15, seed=123, bin_size=1)
    out2 = run_simulation(total_ticks=15, seed=123, bin_size=1)

    assert out1["diagnostics"]["seed"] == 123, "Seed missing; run deeper: pytest tests/test_deep.py::test_simulation_signal_ranges_deep"
    assert out2["diagnostics"]["seed"] == 123, "Seed missing; run deeper: pytest tests/test_deep.py::test_simulation_signal_ranges_deep"
    assert out1["logs"] == out2["logs"], "Simulation not deterministic; run deeper: pytest tests/test_deep.py::test_simulation_signal_ranges_deep"
    assert len(out1["logs"]) == 15, "Unexpected log length; run deeper: pytest tests/test_deep.py::test_simulation_signal_ranges_deep"
    assert out1["stats"]["count"] == 15, "Stats count mismatch; run deeper: pytest tests/test_deep.py::test_simulation_signal_ranges_deep"
    assert {"mean_ext_load", "replay_mode_rates", "seed"} <= set(out1["diagnostics"].keys()), "Diagnostics incomplete; run deeper: pytest tests/test_deep.py::test_simulation_signal_ranges_deep"


def test_trial_wrapper_end_to_end():
    sim = TrialSimulator(preset="default", seed=321)
    result = sim.run_trial(
        stimulus={"ext_load_target": 0.5, "mem_load_target": 0.4},
        duration=25,
    )
    hint = "For behavior details run: pytest tests/test_deep.py::test_trial_wrapper_learning_deep"
    assert result["duration"] == 25, f"Duration mismatch. {hint}"
    assert result["preset"] == "default", f"Preset mismatch. {hint}"
    assert result["seed"] is not None, f"Seed missing. {hint}"
    assert "attunement_mean" in result and "stress_mean" in result, f"Missing trial metrics. {hint}"
    # Deterministic for the same seed/setup
    sim2 = TrialSimulator(preset="default", seed=321)
    result2 = sim2.run_trial(
        stimulus={"ext_load_target": 0.5, "mem_load_target": 0.4},
        duration=25,
    )
    assert result == result2, f"Trial wrapper not deterministic. {hint}"


def test_nc_mcm_helpers_validate_and_extract():
    _validate_fit_nc_mcm_inputs(
        runs=1,
        workers=1,
        draws=10,
        tune=10,
        chains=1,
        cores=1,
        target_accept=0.8,
        max_treedepth=5,
        sim_overrides=None,
    )

    logs, run_idx = nc_mcm_model.run_multiple_simulations(
        n_runs=1,
        workers=1,
        base_seed=seed_everything(999).master_seed,
    )
    data = nc_mcm_model.extract_data(logs, run_idx)
    hint = "For deeper NC-MCM coverage run: pytest tests/test_deep.py::test_nc_mcm_extract_data_full_shapes"
    assert "C_z" in data and data["C_z"].size > 0, f"Missing C_z data. {hint}"
    assert data["run_idx"].shape[0] == data["C_z"].shape[0], f"run_idx shape mismatch. {hint}"


def test_seed_everything_child_seeds_are_distinct():
    streams = seed_everything(555)
    children = streams.spawn(3)
    assert len(children) == 3, "Child seed count wrong; for RNG depth run pytest tests/test_deep.py::test_seed_everything_distribution"
    assert len(set(children)) == 3, "Child seeds not unique; for RNG depth run pytest tests/test_deep.py::test_seed_everything_distribution"


def test_run_multiple_simulations_is_deterministic_with_base_seed():
    base = seed_everything(2024).master_seed
    logs1, idx1 = nc_mcm_model.run_multiple_simulations(n_runs=2, workers=1, base_seed=base)
    logs2, idx2 = nc_mcm_model.run_multiple_simulations(n_runs=2, workers=1, base_seed=base)

    hint = "For full determinism check run: pytest tests/test_deep.py::test_run_multiple_simulations_isolates_runs"
    assert idx1.tolist() == idx2.tolist(), f"Run indices not deterministic. {hint}"
    # Use a small slice to avoid huge comparisons while still asserting determinism.
    assert logs1[:5] == logs2[:5], f"Logs differ across runs. {hint}"
    assert set(idx1.tolist()) == {0, 1}, f"Run labels unexpected. {hint}"


def test_sim_override_scope_restores_state_on_error():
    prev = dict(nc_mcm_model._SIM_OVERRIDES)

    with pytest.raises(RuntimeError):
        with nc_mcm_model.sim_override_scope({"new": 2}):
            assert nc_mcm_model._SIM_OVERRIDES == {"new": 2}
            raise RuntimeError("force failure")

    assert nc_mcm_model._SIM_OVERRIDES == prev


def _check_backend_arrays(arrs, total_ticks):
    att, stress, affect, vis, hear, touch, smell, taste, st_sz, lt_sz = arrs
    for arr in (att, stress, affect, vis, hear, touch, smell, taste, st_sz, lt_sz):
        assert arr.shape == (total_ticks,)
    assert np.all(att >= 0) and np.all(att <= 1)
    assert np.all(stress >= 0) and np.all(stress <= 1)
    assert np.all(affect >= -1) and np.all(affect <= 1)
    assert set(np.unique(vis)).issubset({0, 1, 2, 3})
    assert set(np.unique(hear)).issubset({0, 1, 2})
    assert set(np.unique(touch)).issubset({0, 1})
    assert np.all(smell == 0) and np.all(taste == 0)
    assert np.all(st_sz >= 0)
    assert np.all(lt_sz >= 0)


def _backend_means(arrs):
    att, stress, affect, *_ = arrs
    return float(att.mean()), float(stress.mean()), float(affect.mean())


def test_generate_base_arrays_fallback_when_no_accelerators():
    import src.simulation as sim

    prev_jax, prev_numba = sim.USE_JAX, sim.HAVE_NUMBA
    try:
        sim.USE_JAX = False
        sim.HAVE_NUMBA = False
        arrs = sim._generate_base_arrays(16, seed=123)
    finally:
        sim.USE_JAX, sim.HAVE_NUMBA = prev_jax, prev_numba

    _check_backend_arrays(arrs, 16)
    means = _backend_means(arrs)
    assert 0.3 < means[0] < 0.7 and 0.3 < means[1] < 0.7


def test_generate_base_arrays_numba_stats_match_numpy_when_available():
    import src.simulation as sim

    if not sim.HAVE_NUMBA:
        pytest.skip("Numba not installed; skip backend parity check.")

    total_ticks = 128
    rng = np.random.default_rng(999)
    numpy_arrs = sim._generate_base_arrays(total_ticks, seed=999, rng=rng)
    numpy_means = _backend_means(numpy_arrs)

    np.random.seed(999)
    numba_arrs = sim._generate_base_arrays(total_ticks, seed=None)
    numba_means = _backend_means(numba_arrs)

    _check_backend_arrays(numba_arrs, total_ticks)
    for a, b in zip(numpy_means, numba_means):
        assert math.isclose(a, b, rel_tol=0.2, abs_tol=0.1)


def test_generate_base_arrays_jax_stats_match_numpy_when_available():
    import src.simulation as sim

    if not sim.USE_JAX:
        pytest.skip("JAX not installed; skip backend parity check.")

    total_ticks = 128
    rng = np.random.default_rng(1234)
    numpy_arrs = sim._generate_base_arrays(total_ticks, seed=1234, rng=rng)
    numpy_means = _backend_means(numpy_arrs)

    jax_arrs = sim._generate_base_arrays_jax(total_ticks, seed=1234)
    _check_backend_arrays(jax_arrs, total_ticks)
    jax_means = _backend_means(jax_arrs)

    for a, b in zip(numpy_means, jax_means):
        assert math.isclose(a, b, rel_tol=0.2, abs_tol=0.1)


def test_metadata_builders_include_required_fields_and_hash():
    base_config = {'total_ticks': 5, 'event_rate': 1}
    batch_meta = batch_runner._build_batch_metadata(
        preset='default',
        grid_keys=['event_rate'],
        grid_spec={'event_rate': [1, 2]},
        runs_per_combo=2,
        workers=1,
        base_seed=777,
        run_label='demo_000',
        base_config=base_config,
        mode='continuous',
        metadata_date='2025-11-20T00:00:00Z',
    )
    for key in batch_runner.REQUIRED_METADATA_KEYS:
        assert key in batch_meta and batch_meta[key] not in ("", None)

    grid_params = {'event_rate': 2}
    run_kwargs = {'seed': 778, 'total_ticks': 5, 'event_rate': 2}
    run_meta = batch_runner._build_run_metadata(
        preset_name='default',
        batch_id=123456,
        run_idx=0,
        grid_params=grid_params,
        run_kwargs=run_kwargs,
        run_label='demo_000',
        metadata_date='2025-11-20T00:00:00Z',
        diagnostics={'seed': 778},
    )
    for key in batch_runner.REQUIRED_METADATA_KEYS:
        assert key in run_meta and run_meta[key] not in ("", None)

    expected_run_hash = batch_runner._stable_config_hash({
        'preset': 'default',
        'grid_params': grid_params,
        'run_kwargs': run_kwargs,
    })
    assert run_meta['config_hash'] == expected_run_hash


def test_stable_config_hash_is_deterministic_with_numpy_values():
    payload1 = {'a': np.int64(1), 'b': [np.float64(0.5), np.array([1, 2])]}
    payload2 = {'b': [0.5, np.array([1, 2])], 'a': 1}
    assert batch_runner._stable_config_hash(payload1) == batch_runner._stable_config_hash(payload2)


def test_population_mixture_random_draw_is_reproducible():
    kwargs = {
        'total_ticks': 5,
        'seed': 101,
        'preset': 'default',
        'use_population_mixture': 1,
        'mixture_weights': {'default': 0.4, 'adhd_typical': 0.6},
    }
    out1 = run_simulation(**kwargs)
    out2 = run_simulation(**kwargs)
    diag1 = out1['diagnostics']['population_mixture']
    diag2 = out2['diagnostics']['population_mixture']
    hint = "Mixture sampling should be stable given a seed; for deeper checks run a sweep in config/batch_runner."
    assert diag1['used'] is True and diag2['used'] is True, f"Mixture disabled unexpectedly. {hint}"
    assert diag1['chosen'] == diag2['chosen'], f"Chosen subgroup not reproducible. {hint}"
    assert diag1 == diag2, f"Diagnostics differ across identical runs. {hint}"


def test_population_mixture_stratified_choice_matches_expected_roster():
    weights = {'default': 0.5, 'adhd_typical': 0.3, 'asd_typical': 0.2}
    total = 10

    def expected_choice(idx: int) -> str:
        names = list(weights.keys())
        raw = np.array([float(weights[n]) for n in names], dtype=np.float64)
        probs = raw / (raw.sum() + 1e-12)
        exact = probs * max(1, int(total))
        base_counts = np.floor(exact).astype(int)
        remainder = int(total) - int(base_counts.sum())
        fracs = exact - base_counts
        order = np.argsort(-fracs)
        for k in range(remainder):
            base_counts[order[k % len(order)]] += 1
        roster: list[str] = []
        for name, cnt in zip(names, base_counts):
            roster.extend([name] * int(cnt))
        return roster[int(idx) % len(roster)]

    for idx in range(total):
        out = run_simulation(
            total_ticks=3,
            preset='default',
            use_population_mixture=1,
            mixture_weights=weights,
            stratify_index=idx,
            stratify_total=total,
        )
        chosen = out['diagnostics']['population_mixture']['chosen']
        counts = out['diagnostics']['population_mixture']['target_counts']
        hint = "Stratified mixture should allocate subgroups proportionally; see run_simulation mixture block."
        assert chosen == expected_choice(idx), f"Stratified choice mismatch at index {idx}. {hint}"
        assert counts is not None and sum(counts.values()) == total, f"Stratified counts missing or wrong. {hint}"


def test_population_mixture_jitter_is_seeded_and_effective():
    base = run_simulation(
        total_ticks=5,
        preset='default',
        use_population_mixture=1,
        stratify_index=0,
        stratify_total=3,
        seed=222,
        within_stratum_theta0_jitter=0.0,
    )
    jittered1 = run_simulation(
        total_ticks=5,
        preset='default',
        use_population_mixture=1,
        stratify_index=0,
        stratify_total=3,
        seed=222,
        within_stratum_theta0_jitter=0.1,
    )
    jittered2 = run_simulation(
        total_ticks=5,
        preset='default',
        use_population_mixture=1,
        stratify_index=0,
        stratify_total=3,
        seed=222,
        within_stratum_theta0_jitter=0.1,
    )

    base_theta0 = base['diagnostics']['knobs']['theta0']
    jit_theta0 = jittered1['diagnostics']['knobs']['theta0']
    hint = "Within-stratum jitter should deterministically shift theta0 under the same seed."
    assert jit_theta0 != base_theta0, f"Jitter had no effect on theta0. {hint}"
    assert jittered1['diagnostics']['knobs']['theta0'] == jittered2['diagnostics']['knobs']['theta0'], f"Jitter not reproducible. {hint}"
def test_arbiter_handles_missing_fields_and_keeps_determinism_for_ties():
    arb = SimulationClusterArbiter()
    sims = [{'id': 'a'}, {'id': 'b'}]
    scored = arb.score_simulations(list(sims))
    assert all('final_score' in s for s in scored)
    assert scored[0]['final_score'] == pytest.approx(arb.inertia_bonus)
    assert scored[1]['final_score'] == pytest.approx(arb.inertia_bonus)
    # Stable order for identical utilities (stable sort preserves input ordering)
    sorted_sims = SimulationClusterArbiter.sort_simulations(scored)
    assert [s['id'] for s in sorted_sims] == ['a', 'b']


def test_arbiter_fatigue_modulates_reward_distortion_penalty():
    arb = SimulationClusterArbiter()
    base_fields = {
        'plausibility': 0.5,
        'emotional_prediction': 0.4,
        'reward_distortion': 0.6,
    }
    relaxed = dict(base_fields, fatigue_level=0.0)
    fatigued = dict(base_fields, fatigue_level=1.0)
    scored = arb.score_simulations([relaxed, fatigued])
    u_relaxed = scored[0]['final_score']
    u_fatigued = scored[1]['final_score']
    assert u_fatigued > u_relaxed, "Fatigue should reduce distortion penalty and raise utility."
    # Explicit expected baseline utility for regression anchoring
    expected_relaxed = 0.5 * 0.5 + 0.3 * 0.4 - 0.2 * 0.6 + arb.inertia_bonus
    assert u_relaxed == pytest.approx(round(expected_relaxed, 6))


def test_arbiter_softmax_is_deterministic_for_equal_scores():
    arb = SimulationClusterArbiter(use_softmax=True, base_temp=0.8)
    sims = [{'id': 'x', 'plausibility': 0.2}, {'id': 'y', 'plausibility': 0.2}]
    scored1 = arb.score_simulations([dict(s) for s in sims], confidence=0.9, volatility=0.1)
    scored2 = arb.score_simulations([dict(s) for s in sims], confidence=0.9, volatility=0.1)
    probs1 = [s['select_prob'] for s in scored1]
    probs2 = [s['select_prob'] for s in scored2]
    assert probs1 == pytest.approx(probs2)
    assert probs1[0] == pytest.approx(0.5)
    assert probs1[1] == pytest.approx(0.5)


def test_validation_schema_normalizes_aliases_and_checks_finite():
    df = pd.DataFrame({
        'memory_load': [0.1, 0.2],
        'response_time': [1.0, 1.2],
        'acc': [1, 0],
        'subject': [1, 1],
        'extra': [5, 6],
    })
    norm = validate_and_normalize_columns(df)
    assert set(['mem_load', 'rt', 'accuracy', 'participant']).issubset(norm.columns)
    assert norm['mem_load'].tolist() == [0.1, 0.2]
    assert norm['rt'].tolist() == [1.0, 1.2]
    assert norm['accuracy'].tolist() == [1, 0]
    assert norm['participant'].tolist() == [1, 1]


def test_validation_schema_missing_required_column_raises():
    df = pd.DataFrame({
        'response_time': [1.0],
        'acc': [1],
        'subject': [1],
    })
    with pytest.raises(ValidationSchemaError):
        validate_and_normalize_columns(df)


def test_validation_schema_rejects_nonfinite():
    df = pd.DataFrame({
        'memory_load': [0.1, np.inf],
        'rt': [1.0, 1.1],
        'accuracy': [1, 0],
        'participant': [1, 1],
    })
    with pytest.raises(ValidationSchemaError):
        validate_and_normalize_columns(df)


def _calc_thresholds_and_half_life(seed: int, low: float, high: float, salience: float, *, spacing_gain: float = 0.0, repeats: float = 0.0):
    rng = random.Random(seed)
    jitter = rng.uniform(-0.05, 0.05)
    dyn_low = min(max(low + jitter, 0.0), 1.0)
    dyn_high = min(max(high + jitter, 0.0), 1.0)
    if salience < dyn_low:
        base_half_life = rng.uniform(1200, 2400)
    elif salience > dyn_high:
        base_half_life = rng.uniform(4800, 7200)
    else:
        base_half_life = rng.uniform(2400, 4800)
    half_life = base_half_life
    if spacing_gain != 0.0 and repeats > 0.0:
        half_life = half_life * (1.0 + spacing_gain * math.log1p(repeats))
    return dyn_low, dyn_high, round(half_life, 4), base_half_life


def test_memory_buffer_encoding_defaults_are_neutral():
    seed = 1234
    low, high = 0.4, 0.8
    base_event = {
        'salience': 0.55,
        'valence': 0.9,
        'arousal': 0.8,
        'meaningfulness': 0.7,
        'color_richness': 0.6,
        'exposure_mode': 'vr',
        'repeat_count': 3,
    }
    expected_low, expected_high, expected_half_life, _ = _calc_thresholds_and_half_life(seed, low, high, base_event['salience'])
    random.seed(seed)
    buf = MemoryBuffer(low_salience_threshold=low, high_salience_threshold=high)
    buf.store_events([dict(base_event)])
    stored = buf.short_term[0]

    assert stored['initial_salience'] == pytest.approx(base_event['salience'])
    assert stored['salience'] == pytest.approx(base_event['salience'])
    assert stored['dynamic_low_salience_threshold'] == pytest.approx(expected_low)
    assert stored['dynamic_high_salience_threshold'] == pytest.approx(expected_high)
    assert stored['half_life'] == pytest.approx(expected_half_life)


def test_memory_buffer_encoding_knobs_scale_salience_and_spacing_gain():
    seed = 2025
    low, high = 0.3, 0.7
    base_event = {
        'salience': 0.45,
        'valence': 0.8,
        'arousal': 0.6,
        'meaningfulness': 0.5,
        'color_richness': 0.2,
        'exposure_mode': 'vr',
        'repeat_count': 2,
    }
    coeffs = {'c_valence': 0.2, 'c_arousal': 0.3, 'c_meaning': 0.1, 'spacing_gain': 0.5}
    exposure = {'vr': 1.4}
    enc_mult = 1.0 + abs(base_event['valence']) * coeffs['c_valence'] + base_event['arousal'] * coeffs['c_arousal'] + base_event['meaningfulness'] * coeffs['c_meaning'] + base_event['color_richness'] * 0.0
    total_mult = enc_mult * exposure['vr']
    scaled_salience = base_event['salience'] * total_mult

    _, _, baseline_half_life, base_draw = _calc_thresholds_and_half_life(seed, low, high, scaled_salience, spacing_gain=0.0, repeats=base_event['repeat_count'])
    expected_low, expected_high, expected_half_life, _ = _calc_thresholds_and_half_life(
        seed,
        low,
        high,
        scaled_salience,
        spacing_gain=coeffs['spacing_gain'],
        repeats=base_event['repeat_count'],
    )

    random.seed(seed)
    buf = MemoryBuffer(low_salience_threshold=low, high_salience_threshold=high)
    buf.set_encoding_policy(coeffs=coeffs, exposure_multipliers=exposure)
    buf.store_events([dict(base_event)])
    stored = buf.short_term[0]

    assert stored['initial_salience'] == pytest.approx(scaled_salience)
    assert stored['salience'] == pytest.approx(scaled_salience)
    assert stored['dynamic_low_salience_threshold'] == pytest.approx(expected_low)
    assert stored['dynamic_high_salience_threshold'] == pytest.approx(expected_high)
    assert stored['half_life'] == pytest.approx(expected_half_life)
    assert expected_half_life > baseline_half_life, "Spacing gain should lengthen the half-life draw compared to baseline."
    assert stored['half_life'] > base_draw, "Spacing gain should boost half-life above the base draw."


def test_semanticization_defaults_do_not_modify_events():
    buf = MemoryBuffer()
    lt = LongTermStorage()
    base_event = {
        'id': 'evt_default',
        'salience': 0.75,
        'initial_salience': 0.75,
        'tag_age': 5,
        'repeat_count': 2,
        'timing': 1.2,
        'duration': 2.5,
        'novelty': 0.8,
        'episodic_context_strength': 1.0,
    }
    buf.short_term.append(dict(base_event))
    buf.consolidate_to(lt, threshold=0.5)
    stored = lt.long_term[base_event['id']]

    assert stored.get('semanticized', False) is False
    assert stored['timing'] == base_event['timing']
    assert stored['duration'] == base_event['duration']
    assert stored['novelty'] == base_event['novelty']
    assert stored['episodic_context_strength'] == base_event['episodic_context_strength']


def test_semanticization_policy_applies_when_thresholds_met():
    buf = MemoryBuffer()
    buf.set_semanticization_policy(auto=True, gain=0.6, min_age=2, min_repeats=1, max_bleach=0.5)
    lt = LongTermStorage()
    base_event = {
        'id': 'evt_semantic',
        'salience': 0.9,
        'initial_salience': 0.9,
        'tag_age': 3,
        'repeat_count': 2,
        'timing': 1.5,
        'duration': 3.0,
        'novelty': 0.6,
        'episodic_context_strength': 1.0,
    }
    buf.short_term.append(dict(base_event))
    buf.consolidate_to(lt, threshold=0.5)
    stored = lt.long_term[base_event['id']]

    assert stored.get('semanticized', False) is True
    assert stored['semanticize_factor'] > 0.0
    assert stored['semanticize_factor'] <= 0.5
    assert stored['timing'] < base_event['timing']
    assert stored['duration'] < base_event['duration']
    assert stored['novelty'] < base_event['novelty']
    assert stored['episodic_context_strength'] < base_event['episodic_context_strength']


def test_memory_buffer_pre_store_hook_failure_logs_warning(caplog):
    def failing_hook(_):
        raise RuntimeError("hook exploded")

    random.seed(123)
    buf = MemoryBuffer(pre_store_hook=failing_hook)
    with caplog.at_level(logging.WARNING):
        buf.store_events([{'salience': 0.4}])

    assert "pre_store_hook failed" in caplog.text
    assert len(buf.short_term) == 1, "Event should still be stored even if hook fails"


def test_consolidate_transform_failure_logs_warning_and_stores_event(caplog):
    def failing_transform(_):
        raise RuntimeError("transform failed")

    buf = MemoryBuffer()
    lt = LongTermStorage()
    buf.short_term.append({'id': 'evt_warn', 'salience': 0.6, 'initial_salience': 0.6})

    with caplog.at_level(logging.WARNING):
        buf.consolidate_to(lt, threshold=0.5, transform=failing_transform)

    assert "consolidate_to transform failed" in caplog.text
    assert 'evt_warn' in lt.long_term, "Event should still be consolidated on transform failure"
