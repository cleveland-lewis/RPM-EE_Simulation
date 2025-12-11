# -----------------------------------------------------------------------------
# Standard library imports:
#   - os, time, random: file operations, timing, and standard random numbers
#   - multiprocessing: concurrency support for parallel simulations
#   - json, glob, datetime, typing, math: data handling, file matching, time, type hints, and math
# -----------------------------------------------------------------------------
import time
import random
import os
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import math

# -----------------------------------------------------------------------------
# Third-party library imports:
#   - numpy: core array operations and numerical computing
#   - jax / jax.numpy: accelerated computations on CPU/GPU/TPU with JIT support
#   - numba: optional JIT compilation for CPU performance
#   - fastapi, pydantic: building and validating web API endpoints
#   - filelock: file locking for safe concurrent access
# -----------------------------------------------------------------------------
import numpy as np

try:
    import jax
    import jax.numpy as jnp
    from jax import random as jax_random

    USE_JAX = True
except ImportError:
    USE_JAX = False

try:
    import numba as nb

    HAVE_NUMBA = True
except ModuleNotFoundError:
    HAVE_NUMBA = False

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# -----------------------------------------------------------------------------
# Project-specific imports
# -----------------------------------------------------------------------------
try:
    # When imported as part of the src package
    from .sensory import SensoryInputSystem
    from .randomness import RNGStreams, seed_everything
    from .path_utils import ensure_dir
except ImportError:
    # Fallback when running as a loose script (no package context)
    from sensory import SensoryInputSystem
    from randomness import RNGStreams, seed_everything
    from path_utils import ensure_dir

# Arbiter (modular replay selection)
try:
    from .arbiter import SimulationClusterArbiter
except ImportError:
    from arbiter import SimulationClusterArbiter

# --- Optional preset import ---
try:
    from src.presets import PRESETS as _PRESETS
except ImportError:
    _PRESETS = {}

"""
# WHY CONSTANTS?
# These set safe defaults for plotting, performance, and sentinel values.
# They do not affect theory — they just keep memory/plots manageable.
# MAX_PLOT_POINTS caps visualization density; JAX_TICK_THRESHOLD selects a backend.
# MISSING_VALUE is a sentinel we can filter out later.
"""
# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
MAX_PLOT_POINTS = 1500
JAX_TICK_THRESHOLD = 1_000_000
MISSING_VALUE = -999.0  # Sentinel for missing data in downsampling

# -----------------------------------------------------------------------------
# JAX/Numba Backend Verification and Warm-up
# -----------------------------------------------------------------------------
if USE_JAX:
    try:
        arr = jnp.arange(100)
        s = int(jnp.sum(arr).item())
        dev = jax.devices()[0]
        logger.info("[JAX TEST] JAX on device %s OK (sum=%s)", dev, s)
    except Exception as e:
        logger.warning("[JAX TEST] ERROR initializing JAX backend: %s. Disabling JAX path.", e)
        USE_JAX = False

if HAVE_NUMBA:
    # NUMBA PATH (optional JIT)
    # Same outputs as the NumPy/JAX versions, just faster. We keep logic identical.
    @nb.njit
    def _generate_base_arrays_numba(total_ticks: int):
        att = np.random.rand(total_ticks).astype(np.float32)
        stress = np.random.rand(total_ticks).astype(np.float32)
        affect = (np.random.rand(total_ticks) * 2 - 1).astype(np.float32)
        vis = np.random.randint(0, 4, total_ticks).astype(np.int16)
        hear = np.random.randint(0, 3, total_ticks).astype(np.int16)
        touch = np.random.randint(0, 2, total_ticks).astype(np.int16)
        smell = np.zeros(total_ticks, dtype=np.int16)
        taste = np.zeros(total_ticks, dtype=np.int16)
        ticks = np.arange(total_ticks, dtype=np.int32)
        st_sz = np.maximum(0, 500 - (ticks % 500)).astype(np.int32)
        lt_sz = (ticks // 1000).astype(np.int32)
        return (att, stress, affect, vis, hear, touch, smell, taste, st_sz, lt_sz)

    _ = _generate_base_arrays_numba(1)  # Warm-up compile

# -----------------------------------------------------------------------------
# Vectorized Input Generation Functions
# -----------------------------------------------------------------------------
def _generate_base_arrays_jax(total_ticks: int, seed: int | None = None, key: Any | None = None):
    """
    Generate base random input series using JAX.
    - Returns arrays for affect, stress, and modality events.
    - Uses a PRNG key (seeded) so runs can be reproducible.
    Cognitive rationale: these series stand in for streams of sensory events and
    internal signals. In a full model they would be produced by environment/task code.
    """
    # Use provided key/seed if given; otherwise time-based seed
    if key is None:
        if seed is None:
            seed = int(time.time() * 1000)
        key = jax_random.PRNGKey(int(seed))
    keys = jax_random.split(key, 7)

    att = jax_random.uniform(keys[0], (total_ticks,), dtype=jnp.float32)
    stress = jax_random.uniform(keys[1], (total_ticks,), dtype=jnp.float32)
    affect = (jax_random.uniform(keys[2], (total_ticks,), dtype=jnp.float32) * 2 - 1)
    vis = jax_random.randint(keys[3], (total_ticks,), 0, 4, dtype=jnp.int16)
    hear = jax_random.randint(keys[4], (total_ticks,), 0, 3, dtype=jnp.int16)
    touch = jax_random.randint(keys[5], (total_ticks,), 0, 2, dtype=jnp.int16)
    smell = jnp.zeros((total_ticks,), dtype=jnp.int16)
    taste = jnp.zeros((total_ticks,), dtype=jnp.int16)
    ticks = jnp.arange(total_ticks, dtype=jnp.int32)
    st_sz = jnp.maximum(0, 500 - (ticks % 500)).astype(jnp.int32)
    lt_sz = (ticks // 1000).astype(jnp.int32)

    return tuple(np.array(arr) for arr in [att, stress, affect, vis, hear, touch, smell, taste, st_sz, lt_sz])

if USE_JAX:
    _generate_base_arrays_jax = jax.jit(_generate_base_arrays_jax, static_argnums=(0,))

def _generate_base_arrays(
    total_ticks: int,
    seed: int | None = None,
    *,
    rng: np.random.Generator | None = None,
    jax_key: Any | None = None,
):
    """
    Unified array generator that selects between JAX, Numba, or NumPy.
    For beginners: you can ignore the backend choice — the outputs are the same
    shape either way. A seed makes the randomness repeatable for testing.
    """
    if USE_JAX and total_ticks >= JAX_TICK_THRESHOLD:
        logger.info("[JAX] Using JAX backend for %s ticks.", total_ticks)
        return _generate_base_arrays_jax(total_ticks, seed=seed, key=jax_key)

    # If a seed is provided, prefer deterministic NumPy path (skip numba RNG)
    if seed is None and HAVE_NUMBA:
        try:
            return _generate_base_arrays_numba(total_ticks)
        except Exception as e:
            logger.warning("[Numba] Execution failed: %s. Falling back to NumPy.", e)
            globals()['HAVE_NUMBA'] = False

    rng = rng or np.random.default_rng(seed)
    att = rng.random(total_ticks, dtype=np.float32)
    stress = rng.random(total_ticks, dtype=np.float32)
    affect = (rng.random(total_ticks, dtype=np.float32) * 2 - 1)
    vis = rng.integers(0, 4, total_ticks, dtype=np.int16)
    hear = rng.integers(0, 3, total_ticks, dtype=np.int16)
    touch = rng.integers(0, 2, total_ticks, dtype=np.int16)
    smell = np.zeros(total_ticks, dtype=np.int16)
    taste = np.zeros(total_ticks, dtype=np.int16)
    ticks = np.arange(total_ticks, dtype=np.int32)
    st_sz = np.maximum(0, 500 - (ticks % 500)).astype(np.int32)
    lt_sz = (ticks // 1000).astype(np.int32)

    return (att, stress, affect, vis, hear, touch, smell, taste, st_sz, lt_sz)

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------
def downsample_logs(logs: List[Dict], bin_size: int) -> List[Dict]:
    """
    Average every `bin_size` consecutive log entries so plots/tables stay small.
    Only a few numeric keys are averaged; others (like replay_mode) take the last
    value in each bin. This does not change the simulation, only the output size.
    """
    if bin_size <= 1 or not logs:
        return logs
    keys_to_avg = ['attunement_score', 'schema_stress', 'avg_affect_feedback']
    all_keys = set(logs[0].keys())
    result = []
    n = len(logs)
    for i in range(0, n, bin_size):
        bin_logs = logs[i: i + bin_size]
        avg_entry = {}
        for k in all_keys:
            if k in keys_to_avg:
                vals = [entry.get(k) for entry in bin_logs if entry.get(k) not in (None, MISSING_VALUE)]
                avg_entry[k] = float(np.mean(vals)) if vals else MISSING_VALUE
            else:
                avg_entry[k] = bin_logs[-1].get(k)
        result.append(avg_entry)
    return result

def _thin_logs(logs: List[Dict], max_points: int = MAX_PLOT_POINTS) -> List[Dict]:
    """
    Keep at most `max_points` evenly spaced entries. This is another visualization
    helper and does not affect underlying statistics computed earlier.
    """
    n = len(logs)
    if n <= max_points or max_points <= 0:
        return logs
    step = math.ceil(n / max_points)
    thinned = logs[::step]
    if thinned and logs and thinned[-1] is not logs[-1]:
        thinned.append(logs[-1])
    return thinned

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    Flatten nested dictionaries using dotted keys. Useful when saving JSON/CSV so
    that nested structures become one level deep (e.g., diagnostics.knobs.theta0).
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

@dataclass
class SimulationState:
    stress_prev: float = 0.0
    e_ema: float = 0.0
    ema_aff: float = 0.0
    var_aff: float = 1e-6
    ema_ext: float = 0.0
    var_ext: float = 1e-6
    ema_mem: float = 0.0
    var_mem: float = 1e-6
    ema_vol: float = 0.0
    var_vol: float = 1e-6
    ema_stress: float = 0.0
    var_stress: float = 1e-6
    high_pe_streak: int = 0
    similar_win_streak: int = 0
    selection_confidence: float = 0.0


@dataclass
class TickOutputs:
    dynamic_prune: float
    avg_affect_feedback: float
    mem_load: float
    ext_load: float
    pi_ext: float
    aff_vol: float
    salience: float
    replay_mode: str
    stress_latent: float
    stress_bounded: float
    att_latent: float
    att_bounded: float
    att_terms: tuple[float, float, float, float]
    selection_confidence: float
    action_executed: bool
    prediction_error: float
    episodic_write: bool
    semantic_micro_update: bool
    semanticization: bool
    decay_step: bool
    self_model_update: bool
    suppression_applied: bool
    early_dismissal: bool


@dataclass
class PerTickSeries:
    attunement_scores: np.ndarray
    schema_stress: np.ndarray
    avg_affect_feedback: np.ndarray
    dynamic_prunes: np.ndarray
    ext_load_series: np.ndarray
    mem_load_series: np.ndarray
    affect_vol_series: np.ndarray
    replay_mode_series: List[str]
    selection_conf_series: np.ndarray
    action_exec_series: np.ndarray
    prediction_error_series: np.ndarray
    episodic_write_series: np.ndarray
    semantic_micro_update_series: np.ndarray
    semanticization_series: np.ndarray
    decay_step_series: np.ndarray
    self_model_update_series: np.ndarray
    suppression_applied_series: np.ndarray
    early_dismissal_series: np.ndarray


def _update_running_stats(value: float, ema: float, var: float, step: float = 0.05) -> tuple[float, float]:
    delta = value - ema
    ema += step * delta
    var = (1.0 - step) * var + step * (delta * delta)
    return ema, var


def _init_modalities(vis_arr: np.ndarray, hear_arr: np.ndarray, touch_arr: np.ndarray) -> dict:
    return {
        'vision': {
            'arr': vis_arr.astype(np.float32),
            'max': 3.0,
            'ema': 0.0,
            'var': 1e-6,
            'pi': 1.0,
        },
        'hearing': {
            'arr': hear_arr.astype(np.float32),
            'max': 2.0,
            'ema': 0.0,
            'var': 1e-6,
            'pi': 1.0,
        },
        'touch': {
            'arr': touch_arr.astype(np.float32),
            'max': 1.0,
            'ema': 0.0,
            'var': 1e-6,
            'pi': 1.0,
        },
    }


def _compute_dynamic_prune(base_prune_threshold: float, stress_prev: float) -> float:
    return base_prune_threshold + 0.25 * (1.0 / (1.0 + np.exp(-stress_prev)) - 0.5)


def _compute_memory_load(short_term_size: float, mem_capacity: float, mem_gamma: float, state: SimulationState) -> float:
    mem_load = min(1.0, max(0.0, short_term_size / mem_capacity)) ** mem_gamma
    state.ema_mem, state.var_mem = _update_running_stats(mem_load, state.ema_mem, state.var_mem)
    return mem_load


def _compute_external_load(modalities: dict, idx: int, rho_mod: float, lam_mod: float, state: SimulationState) -> tuple[float, float]:
    weighted_sum = 0.0
    pi_sum = 0.0
    for md in modalities.values():
        raw = float(md['arr'][idx]) / md['max'] if md['max'] > 0 else 0.0
        resid = raw - md['ema']
        md['ema'] += rho_mod * resid
        md['var'] = (1.0 - lam_mod) * md['var'] + lam_mod * (resid * resid)
        md['pi'] = 1.0 / (md['var'] + 1e-6)
        weighted_sum += md['pi'] * raw
        pi_sum += md['pi']

    ext_load = weighted_sum / (pi_sum + 1e-9)
    state.ema_ext, state.var_ext = _update_running_stats(ext_load, state.ema_ext, state.var_ext)
    pi_ext = pi_sum / max(len(modalities), 1)
    return ext_load, pi_ext


def _compute_affect_volatility(aff: float, rho_aff: float, lam_aff: float, state: SimulationState) -> float:
    d_aff = aff - state.ema_aff
    state.ema_aff += rho_aff * d_aff
    state.var_aff = (1.0 - lam_aff) * state.var_aff + lam_aff * (d_aff * d_aff)
    aff_vol = float(np.sqrt(max(state.var_aff, 1e-12)))
    state.ema_vol, state.var_vol = _update_running_stats(aff_vol, state.ema_vol, state.var_vol)
    return aff_vol


def _select_replay_mode(
    selection_confidence: float,
    aff_vol: float,
    aff: float,
    salience: float,
    pe_now: float,
    mem_load: float,
    prior_stress: float,
    replay_softmax: int,
    softmax_temp: float,
    explore_error_gain: float,
    explore_floor: float,
) -> str:
    def _to01(x):
        return float(np.clip(x, 0.0, 1.0))

    load_cost = _to01(0.5 * mem_load + 0.5 * prior_stress)
    vol_cost = _to01(aff_vol)

    candidates = [
        {
            "name": 'Explore',
            "plausibility": _to01(pe_now),
            "emotional_prediction": _to01(salience),
            "reward_distortion": _to01(0.4 * mem_load + 0.3 * prior_stress + 0.3 * aff_vol),
        },
        {
            "name": 'Converge',
            "plausibility": _to01(selection_confidence),
            "emotional_prediction": _to01(0.5 + 0.5 * aff),
            "reward_distortion": _to01(0.3 * aff_vol + 0.2 * prior_stress),
        },
        {
            "name": 'Stabilize',
            "plausibility": _to01(load_cost),
            "emotional_prediction": _to01(1.0 - vol_cost),
            "reward_distortion": _to01(0.1 + 0.2 * vol_cost),
        },
    ]

    _arb = SimulationClusterArbiter(
        adaptive=True,
        penalize_distortion=True,
        use_softmax=bool(replay_softmax),
        base_temp=float(max(1e-6, softmax_temp)),
    )
    scored = _arb.score_simulations(
        candidates,
        stress=float(prior_stress),
        volatility=float(aff_vol),
        salience=float(salience),
        confidence=float(selection_confidence),
    )
    best = SimulationClusterArbiter.sort_simulations(scored)[0]
    return str(best.get("name", 'Converge'))


def _update_stress(
    *,
    ext_load: float,
    int_load: float,
    pi_ext: float,
    state: SimulationState,
    alpha: float,
    beta: float,
    gamma: float,
    tau: float,
    stress_inner_sigmoid: int,
    K_micro: int,
    alpha_u: float,
    beta_u: float,
    rho_e: float,
    kappa: float,
    stress_decay: float,
    stress_gain: float,
    stress_offset: float,
) -> tuple[float, float]:
    if int(stress_inner_sigmoid):
        new_s = 1.0 / (1.0 + np.exp(-(alpha * int_load + beta * ext_load + gamma)))
        s_drive_latent = (1.0 - 1.0 / tau) * state.stress_prev + (1.0 / tau) * new_s
    else:
        drive = alpha * int_load + beta * ext_load + gamma
        s_drive_latent = (1.0 - 1.0 / tau) * state.stress_prev + (1.0 / tau) * drive

    u = 0.0
    for _ in range(K_micro):
        pe = ext_load - state.e_ema
        u += alpha_u * (pi_ext * pe) - beta_u * u
    state.e_ema = (1.0 - rho_e) * state.e_ema + rho_e * ext_load

    if int(stress_inner_sigmoid):
        s_fast_latent = 1.0 / (1.0 + np.exp(-u))
    else:
        s_fast_latent = u

    stress_latent = (1.0 - kappa) * s_drive_latent + kappa * s_fast_latent
    if stress_decay > 0.0:
        stress_latent *= (1.0 - stress_decay)
    stress_latent = float(np.clip(stress_latent, -20.0, 20.0))
    stress_bounded = 1.0 / (1.0 + np.exp(-stress_gain * (stress_latent - stress_offset)))

    state.stress_prev = stress_latent
    state.ema_stress, state.var_stress = _update_running_stats(stress_bounded, state.ema_stress, state.var_stress)
    return stress_latent, float(stress_bounded)


def _compute_selection_confidence(stress_bounded: float, aff_vol: float) -> float:
    return float(np.clip(1.0 - 0.5 * stress_bounded - 0.5 * aff_vol, 0.0, 1.0))


def _compute_attunement_latent(
    *,
    aff: float,
    stress_value: float,
    ext_load: float,
    mem_load: float,
    aff_vol: float,
    params: dict,
    state: SimulationState,
    norm_stress: int,
    norm_ext_load: int,
    norm_mem_load: int,
    norm_aff_vol: int,
) -> tuple[float, tuple[float, float, float, float]]:
    def _zscore(x, mu, var):
        return (x - mu) / (np.sqrt(max(var, 1e-9)))

    s_term = _zscore(stress_value, state.ema_stress, state.var_stress) if norm_stress else stress_value
    ext_term = _zscore(ext_load, state.ema_ext, state.var_ext) if norm_ext_load else ext_load
    mem_term = _zscore(mem_load, state.ema_mem, state.var_mem) if norm_mem_load else mem_load
    vol_term = _zscore(aff_vol, state.ema_vol, state.var_vol) if norm_aff_vol else aff_vol

    att_latent = (
        params['theta0']
        + params['theta_a'] * aff
        - (params['theta_s'] * params['theta_s_mult']) * s_term
        - (params['theta_e'] * params['theta_e_mult']) * ext_term
        - (params['theta_m'] * params['theta_m_mult']) * mem_term
        - (params['theta_v'] * params['theta_v_mult']) * vol_term
    )
    return float(np.clip(att_latent, -20.0, 20.0)), (s_term, ext_term, mem_term, vol_term)


def _decide_action_executed(
    *,
    gate_by_attunement: int,
    att_latent: float,
    gate_temperature: float,
    att_gate_latent: float,
    selection_confidence: float,
    early_dismissal: bool,
    rng: np.random.Generator,
) -> bool:
    if gate_by_attunement:
        if att_latent > att_gate_latent:
            p_act = 1.0 / (1.0 + np.exp(-(att_latent / max(1e-6, float(gate_temperature)))))
            return (not early_dismissal) and (rng.random() < p_act)
        return False
    return (not early_dismissal) and (selection_confidence > 0.4)


def _update_high_pe_streak(prediction_error: float, state: SimulationState) -> int:
    if prediction_error > 0.3:
        state.high_pe_streak += 1
    else:
        state.high_pe_streak = 0
    return state.high_pe_streak


def _update_similar_win_streak(replay_mode: str, selection_confidence: float, state: SimulationState) -> int:
    if replay_mode == 'Converge' and selection_confidence > 0.75:
        state.similar_win_streak += 1
    else:
        state.similar_win_streak = max(0, state.similar_win_streak - 1)
    return state.similar_win_streak


def _apply_preset_overrides(
    effective_preset: str | None,
    params: dict,
    knobs: dict,
    rng: np.random.Generator,
    within_stratum_theta0_jitter: float | None,
) -> tuple[dict, dict]:
    if effective_preset and _PRESETS:
        cfg = _PRESETS.get(effective_preset)
        if cfg is None and effective_preset == 'default' and 'default_theory' in _PRESETS:
            cfg = _PRESETS.get('default_theory')
        if cfg:
            for key in ('theta_a', 'theta_s', 'theta_e', 'theta_m', 'theta_v'):
                params[key] = cfg.get(key, params[key])
            for key in ('rho_mod', 'lam_mod', 'rho_aff', 'lam_aff', 'rho_e', 'K_micro', 'alpha_u', 'beta_u', 'kappa', 'mem_gamma', 'tau', 'alpha', 'beta', 'gamma', 'stress_decay', 'stress_inner_sigmoid'):
                knobs[key] = cfg.get(key, knobs[key])
            for key in ('SALIENCE_DROP', 'VOL_HIGH', 'STRESS_HIGH', 'LOAD_HIGH'):
                knobs[key] = cfg.get(key, knobs[key])
            for key in ('theta0', 'theta_s_mult', 'gate_by_attunement', 'gate_temperature', 'replay_softmax', 'explore_error_gain', 'softmax_temp', 'explore_floor', 'theta_e_mult', 'theta_m_mult', 'theta_v_mult', 'norm_stress', 'norm_ext_load', 'norm_mem_load', 'norm_aff_vol', 'att_gain', 'att_offset', 'att_scale', 'stress_gain', 'stress_offset', 'att_gate_latent'):
                params[key] = cfg.get(key, params.get(key, None))
            if within_stratum_theta0_jitter and within_stratum_theta0_jitter > 0.0:
                try:
                    params['theta0'] = float(params['theta0']) + float(rng.normal(0.0, within_stratum_theta0_jitter))
                except (ValueError, TypeError):
                    pass
    return params, knobs


def _init_rngs(seed: Optional[int]):
    """
    Initialize RNG streams for Python/NumPy/JAX and sensory subsystems.
    Returns tuple: (rng_streams, rng, sensory_py_rng, sensory_np_rng, sensory_py_seed, sensory_np_seed).
    """
    rng_streams: RNGStreams = seed_everything(seed)
    rng = rng_streams.np_random
    sensory_py_seed, sensory_np_seed = rng_streams.spawn(2)
    sensory_py_rng = random.Random(sensory_py_seed)
    sensory_np_rng = np.random.default_rng(sensory_np_seed)
    return rng_streams, rng, sensory_py_rng, sensory_np_rng, sensory_py_seed, sensory_np_seed


def _draw_from_mixture(weights: dict[str, float], rng: np.random.Generator) -> str:
    names = list(weights.keys())
    probs = np.array([float(weights[n]) for n in names], dtype=np.float64)
    probs = probs / (probs.sum() + 1e-12)
    r = float(rng.random())
    c = 0.0
    for n, p in zip(names, probs):
        c += p
        if r <= c:
            return n
    return names[-1]


def _deterministic_stratified_choice(weights: dict[str, float], index: int, total: int) -> str:
    names = list(weights.keys())
    raw = np.array([float(weights[n]) for n in names], dtype=np.float64)
    probs = raw / (raw.sum() + 1e-12)
    exact_counts = probs * max(1, int(total))
    base_counts = np.floor(exact_counts).astype(int)
    remainder = int(total) - int(base_counts.sum())
    fracs = exact_counts - base_counts
    order = np.argsort(-fracs)  # descending
    for k in range(remainder):
        base_counts[order[k % len(order)]] += 1
    roster: list[str] = []
    for name, cnt in zip(names, base_counts):
        roster.extend([name] * int(cnt))
    if len(roster) == 0:
        return names[0]
    j = int(index) % len(roster)
    return roster[j]


def _resolve_preset_choice(
    preset: str | None,
    use_population_mixture: int,
    mixture_weights: dict | None,
    stratify_index: int | None,
    stratify_total: int | None,
    rng: np.random.Generator,
) -> Dict[str, Any]:
    effective_preset = preset
    mixture_used = False
    mixture_mode = 'off'
    chosen_subgroup = None
    provided_mixture_weights = mixture_weights
    weights = provided_mixture_weights if (isinstance(provided_mixture_weights, dict) and provided_mixture_weights) else {}

    if preset and _PRESETS:
        if use_population_mixture and preset in ('default', 'default_theory'):
            mix = weights if weights else {
                'default': 0.935,
                'adhd_typical': 0.045,
                'asd_typical': 0.020,
            }
            if 'default_theory' in mix:
                mix['default'] = mix.get('default', 0.0) + float(mix.pop('default_theory'))
            if (stratify_index is not None) and (stratify_total is not None):
                chosen = _deterministic_stratified_choice(mix, int(stratify_index), int(stratify_total))
                mixture_mode = 'stratified'
            else:
                chosen = _draw_from_mixture(mix, rng)
                mixture_mode = 'random'
            if chosen == 'default' and 'default' not in _PRESETS and 'default_theory' in _PRESETS:
                effective_preset = 'default_theory'
            elif chosen in _PRESETS:
                effective_preset = chosen
            mixture_used = True
            chosen_subgroup = chosen
            weights = mix

        if (effective_preset == 'default') and ('default' not in _PRESETS) and ('default_theory' in _PRESETS):
            effective_preset = 'default_theory'

    return {
        'effective_preset': effective_preset,
        'mixture_used': mixture_used,
        'mixture_mode': mixture_mode,
        'chosen_subgroup': chosen_subgroup,
        'mixture_weights': weights,
    }


def _build_tick_log(
    *,
    tick: int,
    att_latent: float,
    stress_latent: float,
    att_bounded: float,
    stress_bounded: float,
    theta_params: dict,
    pi_aff: float,
    pi_str: float,
    pi_ext: float,
    pi_mem: float,
    pi_vol: float,
    aff: float,
    s_term: float,
    ext_term: float,
    mem_term: float,
    vol_term: float,
    ext_load: float,
    mem_load: float,
    aff_vol: float,
    salience: float,
    replay_mode: str,
    selection_confidence: float,
    action_executed: bool,
    prediction_error: float,
    episodic_write: bool,
    semantic_micro_update: bool,
    semanticization: bool,
    decay_step: bool,
    self_model_update: bool,
    suppression_applied: bool,
    early_dismissal: bool,
    dynamic_prune: float,
    attunement_score: float,
    schema_stress_value: float,
) -> Dict:
    theta0 = float(theta_params.get('theta0', 0.0))
    theta_a = float(theta_params.get('theta_a', 0.0))
    theta_s = float(theta_params.get('theta_s', 0.0))
    theta_e = float(theta_params.get('theta_e', 0.0))
    theta_m = float(theta_params.get('theta_m', 0.0))
    theta_v = float(theta_params.get('theta_v', 0.0))
    theta_s_mult = float(theta_params.get('theta_s_mult', 1.0))
    theta_e_mult = float(theta_params.get('theta_e_mult', 1.0))
    theta_m_mult = float(theta_params.get('theta_m_mult', 1.0))
    theta_v_mult = float(theta_params.get('theta_v_mult', 1.0))

    return {
        'att_latent': float(att_latent),
        'stress_latent': float(stress_latent),
        'att_bounded': float(att_bounded),
        'stress_bounded': float(stress_bounded),
        'logit_theta0': theta0,
        'logit_aff_term': float(theta_a * (pi_aff * aff)),
        'logit_stress_term': float(-(theta_s * theta_s_mult) * (pi_str * s_term)),
        'logit_ext_term': float(-(theta_e * theta_e_mult) * (pi_ext * ext_term)),
        'logit_mem_term': float(-(theta_m * theta_m_mult) * (pi_mem * mem_term)),
        'logit_vol_term': float(-(theta_v * theta_v_mult) * (pi_vol * vol_term)),
        'logit_z': float(att_latent),
        'clock': tick,
        'attunement_score': float(attunement_score),
        'schema_stress': float(schema_stress_value),
        'avg_affect_feedback': float(aff),
        'dynamic_prune': float(dynamic_prune),
        'ext_load': float(ext_load),
        'mem_load': float(mem_load),
        'affect_volatility': float(aff_vol),
        'stage_2_salience': float(salience),
        'stage_3_wm_load_effective': float(mem_load),
        'replay_mode': replay_mode,
        'selection_confidence': float(selection_confidence),
        'action_executed': bool(action_executed),
        'prediction_error': float(prediction_error),
        'episodic_write': bool(episodic_write),
        'semantic_micro_update': bool(semantic_micro_update),
        'semanticization': bool(semanticization),
        'decay_step': bool(decay_step),
        'self_model_update': bool(self_model_update),
        'suppression_applied': bool(suppression_applied),
        'early_dismissal': bool(early_dismissal),
        'arbiter_top_mode': replay_mode,
    }


def _rate_bool(arr) -> float:
    try:
        arr_np = np.asarray(arr, dtype=np.float32)
        return float(np.mean(arr_np)) if arr_np.size else float('nan')
    except (ValueError, TypeError):
        return float('nan')


def _safe_percentile(x, p: float) -> float:
    try:
        return float(np.percentile(x, p))
    except (ValueError, TypeError, IndexError):
        return float('nan')


def _compute_replay_mode_rates(replay_mode_series: List[str]) -> Dict[str, float]:
    if not replay_mode_series:
        return {'Explore': float('nan'), 'Converge': float('nan'), 'Stabilize': float('nan')}

    rm = np.array(replay_mode_series, dtype=object)
    n = len(rm)
    return {
        'Explore': float(np.sum(rm == 'Explore')) / n,
        'Converge': float(np.sum(rm == 'Converge')) / n,
        'Stabilize': float(np.sum(rm == 'Stabilize')) / n,
    }


def _compute_action_rate_by_attunement(attunement_scores: np.ndarray, action_exec_series: np.ndarray) -> List[float]:
    try:
        att = np.asarray(attunement_scores, dtype=np.float32)
        acts = np.asarray(action_exec_series, dtype=np.bool_)
        if att.size >= 10:
            qs = np.quantile(att, np.linspace(0.0, 1.0, 11))
            dec_rates: list[float] = []
            for d in range(10):
                lo, hi = qs[d], qs[d + 1]
                mask = (att >= lo) & (att <= hi) if d == 9 else (att >= lo) & (att < hi)
                dec_rates.append(float(np.mean(acts[mask].astype(np.float32))) if mask.any() else float('nan'))
        else:
            dec_rates = [float('nan')] * 10
    except (ValueError, TypeError, IndexError):
        dec_rates = [float('nan')] * 10
    return dec_rates


def _build_diagnostics(
    *,
    attunement_scores: np.ndarray,
    schema_stress: np.ndarray,
    selection_conf_series: np.ndarray,
    ext_load_series: np.ndarray,
    mem_load_series: np.ndarray,
    affect_vol_series: np.ndarray,
    action_exec_series: np.ndarray,
    semantic_micro_update_series: np.ndarray,
    semanticization_series: np.ndarray,
    self_model_update_series: np.ndarray,
    suppression_applied_series: np.ndarray,
    early_dismissal_series: np.ndarray,
    replay_mode_series: List[str],
    effective_preset: str | None,
    stratify_index: int | None,
    stratify_total: int | None,
    mixture_used: bool,
    mixture_mode: str | None,
    mixture_weights: dict | None,
    chosen_subgroup: str | None,
    effective_seed: int,
    rng_streams: RNGStreams,
    sensory_py_seed: int,
    sensory_np_seed: int,
    params: dict,
    knobs: dict,
) -> Dict[str, Any]:
    action_rates_by_decile = _compute_action_rate_by_attunement(attunement_scores, action_exec_series)
    replay_mode_rates = _compute_replay_mode_rates(replay_mode_series)

    return {
        'effective_preset': str(effective_preset),
        'stratify_index': stratify_index if stratify_index is not None else None,
        'stratify_total': stratify_total if stratify_total is not None else None,
        'population_mixture': {
            'used': bool(mixture_used),
            'mode': mixture_mode if isinstance(mixture_mode, str) else 'off',
            'weights': mixture_weights,
            'chosen': chosen_subgroup if mixture_used else None,
            'target_counts': (
                {k: int(round(float(mixture_weights.get(k, 0.0)) * int(stratify_total))) for k in mixture_weights}
                if (mixture_used and isinstance(mixture_weights, dict) and stratify_total is not None) else None
            ),
        },
        'rng': {
            'master': int(effective_seed),
            'python': int(rng_streams.python_seed),
            'numpy': int(rng_streams.numpy_seed),
            'jax': int(rng_streams.jax_seed) if rng_streams.jax_seed is not None else None,
            'sensory_python': int(sensory_py_seed),
            'sensory_numpy': int(sensory_np_seed),
        },
        'attunement_p5': _safe_percentile(attunement_scores, 5),
        'attunement_p50': _safe_percentile(attunement_scores, 50),
        'attunement_p95': _safe_percentile(attunement_scores, 95),
        'stress_p5': _safe_percentile(schema_stress, 5),
        'stress_p50': _safe_percentile(schema_stress, 50),
        'stress_p95': _safe_percentile(schema_stress, 95),
        'mean_selection_confidence': float(np.mean(selection_conf_series)) if len(selection_conf_series) else float('nan'),
        'mean_ext_load': float(np.mean(ext_load_series)) if len(ext_load_series) else float('nan'),
        'mean_mem_load': float(np.mean(mem_load_series)) if len(mem_load_series) else float('nan'),
        'mean_affect_volatility': float(np.mean(affect_vol_series)) if len(affect_vol_series) else float('nan'),
        'rate_action_executed': _rate_bool(action_exec_series),
        'rate_semantic_micro_update': _rate_bool(semantic_micro_update_series),
        'rate_semanticization': _rate_bool(semanticization_series),
        'rate_self_model_update': _rate_bool(self_model_update_series),
        'rate_suppression_applied': _rate_bool(suppression_applied_series),
        'rate_early_dismissal': _rate_bool(early_dismissal_series),
        'seed': int(effective_seed),
        'replay_mode_rates': replay_mode_rates,
        'action_rate_by_attunement_decile': action_rates_by_decile,
        'knobs': {
            'theta0': float(params.get('theta0', 0.0)),
            'theta_s_mult': float(params.get('theta_s_mult', 1.0)),
            'gate_by_attunement': int(knobs.get('gate_by_attunement', 0)),
            'gate_temperature': float(knobs.get('gate_temperature', 1.0)),
            'replay_softmax': int(knobs.get('replay_softmax', 0)),
            'explore_error_gain': float(knobs.get('explore_error_gain', 0.0)),
            'softmax_temp': float(knobs.get('softmax_temp', 1.0)),
            'explore_floor': float(knobs.get('explore_floor', 0.0)),
            'theta_e_mult': float(params.get('theta_e_mult', 1.0)),
            'theta_m_mult': float(params.get('theta_m_mult', 1.0)),
            'theta_v_mult': float(params.get('theta_v_mult', 1.0)),
            'norm_stress': int(knobs.get('norm_stress', 0)),
            'norm_ext_load': int(knobs.get('norm_ext_load', 0)),
            'norm_mem_load': int(knobs.get('norm_mem_load', 0)),
            'norm_aff_vol': int(knobs.get('norm_aff_vol', 0)),
            'alpha': float(knobs.get('alpha', 0.0)),
            'beta': float(knobs.get('beta', 0.0)),
            'gamma': float(knobs.get('gamma', 0.0)),
            'kappa': float(knobs.get('kappa', 0.0)),
            'tau': float(knobs.get('tau', 0.0)),
            'stress_decay': float(knobs.get('stress_decay', 0.0)),
            'att_gain': float(params.get('att_gain', 1.0)),
            'att_offset': float(params.get('att_offset', 0.0)),
            'att_scale': float(params.get('att_scale', 1.0)),
            'stress_gain': float(params.get('stress_gain', 1.0)),
            'stress_offset': float(params.get('stress_offset', 0.0)),
            'att_gate_latent': float(params.get('att_gate_latent', 1.0)),
            'stress_inner_sigmoid': int(knobs.get('stress_inner_sigmoid', 0)),
            'seed': int(effective_seed),
        }
    }


def _run_single_tick(
    idx: int,
    *,
    sim: SensoryInputSystem,
    modalities: dict,
    state: SimulationState,
    base_prune_threshold: float,
    mem_capacity: float,
    mem_gamma: float,
    rho_mod: float,
    lam_mod: float,
    rho_aff: float,
    lam_aff: float,
    salience_drop: float,
    max_raw_st: float,
    K_micro: int,
    alpha_u: float,
    beta_u: float,
    rho_e: float,
    kappa: float,
    alpha: float,
    beta: float,
    gamma: float,
    tau: float,
    stress_inner_sigmoid: int,
    stress_decay: float,
    stress_gain: float,
    stress_offset: float,
    pi_aff: float,
    pi_str: float,
    pi_mem: float,
    pi_vol: float,
    theta_params: dict,
    gate_by_attunement: int,
    gate_temperature: float,
    att_gate_latent: float,
    norm_stress: int,
    norm_ext_load: int,
    norm_mem_load: int,
    norm_aff_vol: int,
    replay_softmax: int,
    softmax_temp: float,
    explore_error_gain: float,
    explore_floor: float,
    rng: np.random.Generator,
    schema_stress_prev: float,
) -> TickOutputs:
    dynamic_prune = _compute_dynamic_prune(base_prune_threshold, state.stress_prev)
    tick_result = sim.tick(memory_prune_threshold=dynamic_prune)
    aff = float(tick_result["avg_affect_feedback"])
    short_term_size = float(tick_result["short_term_size"])

    mem_load = _compute_memory_load(short_term_size, mem_capacity, mem_gamma, state)
    ext_load, pi_ext = _compute_external_load(modalities, idx, rho_mod, lam_mod, state)
    aff_vol = _compute_affect_volatility(aff, rho_aff, lam_aff, state)

    salience = float(np.clip(0.6 * ext_load + 0.4 * abs(aff), 0.0, 1.0))
    early_dismissal = salience < salience_drop

    pe_now = float(np.clip(abs(ext_load - state.e_ema), 0.0, 1.0))
    replay_mode = _select_replay_mode(
        state.selection_confidence if idx > 0 else 0.0,
        aff_vol,
        aff,
        salience,
        pe_now,
        mem_load,
        schema_stress_prev,
        replay_softmax,
        softmax_temp,
        explore_error_gain,
        explore_floor,
    )

    int_load = short_term_size / max_raw_st
    stress_latent, stress_bounded = _update_stress(
        ext_load=ext_load,
        int_load=int_load,
        pi_ext=pi_ext,
        state=state,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        tau=tau,
        stress_inner_sigmoid=stress_inner_sigmoid,
        K_micro=K_micro,
        alpha_u=alpha_u,
        beta_u=beta_u,
        rho_e=rho_e,
        kappa=kappa,
        stress_decay=stress_decay,
        stress_gain=stress_gain,
        stress_offset=stress_offset,
    )

    att_latent, att_terms = _compute_attunement_latent(
        aff=aff,
        stress_value=stress_bounded,
        ext_load=ext_load,
        mem_load=mem_load,
        aff_vol=aff_vol,
        params=theta_params,
        state=state,
        norm_stress=norm_stress,
        norm_ext_load=norm_ext_load,
        norm_mem_load=norm_mem_load,
        norm_aff_vol=norm_aff_vol,
    )
    att_gain = float(theta_params['att_gain'])
    att_offset = float(theta_params['att_offset'])
    att_scale = float(theta_params['att_scale'])
    att_bounded = 1.0 / (1.0 + np.exp(-att_gain * (att_latent - att_offset)))
    _ = att_scale * att_bounded  # retained for clarity; currently unused

    selection_confidence = _compute_selection_confidence(stress_bounded, aff_vol)
    action_executed = _decide_action_executed(
        gate_by_attunement=gate_by_attunement,
        att_latent=att_latent,
        gate_temperature=gate_temperature,
        att_gate_latent=att_gate_latent,
        selection_confidence=selection_confidence,
        early_dismissal=early_dismissal,
        rng=rng,
    )

    prediction_error = float(np.clip(abs(ext_load - state.e_ema), 0.0, 1.0))
    high_pe_streak = _update_high_pe_streak(prediction_error, state)

    episodic_write = bool(action_executed)
    semantic_micro_update = bool(selection_confidence > 0.7)

    similar_win_streak = _update_similar_win_streak(replay_mode, selection_confidence, state)
    semanticization = bool(similar_win_streak >= 3)
    decay_step = True

    suppression_applied = bool(high_pe_streak >= 4)
    self_model_update = bool(prediction_error > 0.3 or semantic_micro_update)

    return TickOutputs(
        dynamic_prune=dynamic_prune,
        avg_affect_feedback=aff,
        mem_load=mem_load,
        ext_load=ext_load,
        pi_ext=pi_ext,
        aff_vol=aff_vol,
        salience=salience,
        replay_mode=replay_mode,
        stress_latent=stress_latent,
        stress_bounded=float(stress_bounded),
        att_latent=att_latent,
        att_bounded=float(att_bounded),
        att_terms=att_terms,
        selection_confidence=selection_confidence,
        action_executed=action_executed,
        prediction_error=prediction_error,
        episodic_write=episodic_write,
        semantic_micro_update=semantic_micro_update,
        semanticization=semanticization,
        decay_step=decay_step,
        self_model_update=self_model_update,
        suppression_applied=suppression_applied,
        early_dismissal=early_dismissal,
    )


def _record_tick_series(
    idx: int,
    tick_out: TickOutputs,
    *,
    dynamic_prunes: np.ndarray,
    avg_affect_feedback: np.ndarray,
    mem_load_series: np.ndarray,
    ext_load_series: np.ndarray,
    affect_vol_series: np.ndarray,
    schema_stress: np.ndarray,
    attunement_scores: np.ndarray,
    replay_mode_series: List[str],
    selection_conf_series: np.ndarray,
    action_exec_series: np.ndarray,
    prediction_error_series: np.ndarray,
    episodic_write_series: np.ndarray,
    semantic_micro_update_series: np.ndarray,
    semanticization_series: np.ndarray,
    decay_step_series: np.ndarray,
    self_model_update_series: np.ndarray,
    suppression_applied_series: np.ndarray,
    early_dismissal_series: np.ndarray,
):
    dynamic_prunes[idx] = tick_out.dynamic_prune
    avg_affect_feedback[idx] = tick_out.avg_affect_feedback
    mem_load_series[idx] = tick_out.mem_load
    ext_load_series[idx] = tick_out.ext_load
    affect_vol_series[idx] = tick_out.aff_vol
    schema_stress[idx] = tick_out.stress_bounded
    attunement_scores[idx] = tick_out.att_bounded

    replay_mode_series[idx] = tick_out.replay_mode
    selection_conf_series[idx] = tick_out.selection_confidence
    action_exec_series[idx] = tick_out.action_executed
    prediction_error_series[idx] = tick_out.prediction_error
    episodic_write_series[idx] = tick_out.episodic_write
    semantic_micro_update_series[idx] = tick_out.semantic_micro_update
    semanticization_series[idx] = tick_out.semanticization
    decay_step_series[idx] = tick_out.decay_step
    self_model_update_series[idx] = tick_out.self_model_update
    suppression_applied_series[idx] = tick_out.suppression_applied
    early_dismissal_series[idx] = tick_out.early_dismissal


def _init_per_tick_series(total_ticks: int) -> PerTickSeries:
    return PerTickSeries(
        attunement_scores=np.zeros(total_ticks, dtype=np.float32),
        schema_stress=np.zeros(total_ticks, dtype=np.float32),
        avg_affect_feedback=np.zeros(total_ticks, dtype=np.float32),
        dynamic_prunes=np.zeros(total_ticks, dtype=np.float32),
        ext_load_series=np.zeros(total_ticks, dtype=np.float32),
        mem_load_series=np.zeros(total_ticks, dtype=np.float32),
        affect_vol_series=np.zeros(total_ticks, dtype=np.float32),
        replay_mode_series=["" for _ in range(total_ticks)],
        selection_conf_series=np.zeros(total_ticks, dtype=np.float32),
        action_exec_series=np.zeros(total_ticks, dtype=np.bool_),
        prediction_error_series=np.zeros(total_ticks, dtype=np.float32),
        episodic_write_series=np.zeros(total_ticks, dtype=np.bool_),
        semantic_micro_update_series=np.zeros(total_ticks, dtype=np.bool_),
        semanticization_series=np.zeros(total_ticks, dtype=np.bool_),
        decay_step_series=np.ones(total_ticks, dtype=np.bool_),
        self_model_update_series=np.zeros(total_ticks, dtype=np.bool_),
        suppression_applied_series=np.zeros(total_ticks, dtype=np.bool_),
        early_dismissal_series=np.zeros(total_ticks, dtype=np.bool_),
    )


def _compute_full_stats(attunement_scores: np.ndarray, schema_stress: np.ndarray) -> Dict[str, float]:
    full_count = int(attunement_scores.size)
    full_mean_att = float(np.mean(attunement_scores)) if full_count > 0 else float('nan')
    full_std_att = float(np.std(attunement_scores)) if full_count > 0 else float('nan')
    full_mean_str = float(np.mean(schema_stress)) if full_count > 0 else float('nan')
    full_std_str = float(np.std(schema_stress)) if full_count > 0 else float('nan')
    return {
        'count': full_count,
        'mean_attunement': full_mean_att,
        'std_attunement': full_std_att,
        'mean_stress': full_mean_str,
        'std_stress': full_std_str,
    }


# -----------------------------------------------------------------------------
# Core Simulation Logic
# -----------------------------------------------------------------------------
def run_simulation(
        total_ticks: int = 2400,
        salience_decay: float = 0.01,
        highly_variable_rate: float = 0.1,
        event_rate: int = 3,
        memory_buffer_size: int = 1000,
        memory_decay: float = 0.01,
        memory_prune_threshold: float = 0.2,
        low_salience_var_rate: float = 0.1,
        bin_size: int = 1,
        preset: str | None = None,
        seed: int | None = None,
        # --- Optional behavior knobs (default = no change) ---
        theta0: float = 0.07,                # additive bias to lift attunement
        theta_s_mult: float = 0.65,          # scales stress weight in attunement
        gate_by_attunement: int = 0,         # 0=off (legacy), 1=gate actions by attunement
        gate_temperature: float = 1.0,       # temperature for gating probability
        replay_softmax: int = 0,             # 0=heuristic (legacy), 1=softmax arbitration
        explore_error_gain: float = 2.0,     # how strongly PE boosts Explore utility
        softmax_temp: float = 1.0,           # temperature for replay softmax
        explore_floor: float = 0.0,          # minimum probability for Explore (0..1)
        # --- Additional optional multipliers (default = 1.0, no change) ---
        theta_e_mult: float = 0.85,          # scales external load weight in attunement
        theta_m_mult: float = 0.90,          # scales memory load weight in attunement
        theta_v_mult: float = 0.90,          # scales affect volatility weight in attunement
        # --- Optional normalization toggles for contributors (default off) ---
        norm_stress: int = 0,                # 1 = z-score schema stress online before attunement
        norm_ext_load: int = 0,              # 1 = z-score external load online before attunement
        norm_mem_load: int = 0,              # 1 = z-score memory load online before attunement
        norm_aff_vol: int = 0,               # 1 = z-score affect volatility online before attunement
        use_population_mixture: int = 0,     # DISABLED by default; 1 = randomly draw NT/ADHD/ASD mix per run (must be explicitly enabled)
        mixture_weights: dict | None = None,  # optional override for population proportions
        stratify_index: int | None = None,    # if provided with stratify_total → deterministic subgroup assignment
        stratify_total: int | None = None,
        within_stratum_theta0_jitter: float | None = None,
        # --- Stress drive / blending knobs (now directly overrideable) ---
        alpha: float = 1.0,
        beta: float = 1.0,
        gamma: float = 0.0,
        kappa: float = 0.3,
        tau: float = 5.0,
        stress_decay: float = 0.0,          # per-tick stress decay rate (0.0 = no decay)
        # --- Link function parameters (latent → bounded mapping) ---
        att_gain: float = 2.0,              # attunement sigmoid slope
        att_offset: float = 1.0,            # attunement sigmoid center
        att_scale: float = 1.0,             # attunement output scaling (1.0 = keep [0,1])
        stress_gain: float = 2.0,           # stress sigmoid slope
        stress_offset: float = 0.0,         # stress sigmoid center
        att_gate_latent: float = 1.0,      # latent threshold for action gating
        stress_inner_sigmoid: int = 0,     # 1=use legacy inner sigmoids (double-sigmoid); 0=latent-only then link
    ) -> dict | List[Dict]:
    # Default tuning note: baseline parameters are set to approximate a "typical neurotypical"
    # profile with mean attunement around ~1% across ordinary environments.
    """
    Run one RPM‑EE simulation and return logs + summary stats.

    PARAMETERS (simplified):
      total_ticks: how many time steps to simulate.
      salience_decay, event_rate, ...: knobs for how often/intensely inputs arrive.
      preset: name of a preset in `presets.PRESETS` to override defaults.
      seed: set for reproducibility. If None, a seed is generated and recorded.

      theta0, theta_*_mult: weights in the attunement equation (see below).
      norm_* toggles: online z‑scoring of contributors (stabilizes scales).

    RETURNS:
      {
        'logs': [ per‑tick dicts ],
        'stats': { mean/std of attunement and stress },
        'diagnostics': { rates, percentiles, knobs used }
      }

    COGNITIVE MAP:
      • External load (ext_load): precision‑weighted combination of sensory channels
        (vision/hearing/touch). “Precision” ~ reliability (inverse variance), matching
        predictive‑processing accounts where reliable channels carry more weight.
      • Memory load (mem_load): working‑memory occupancy with a capacity limit and
        nonlinearity (gamma). Higher load impairs attunement.
      • Affect & volatility: mean affect (−1..1) and short‑term variability. High
        volatility reduces selection confidence and attunement.
      • Schema stress: blend of a slow drive component (task/internal load) and a
        fast surprisal component (prediction error on external load). Both track
        predictive‑processing ideas: stress rises with persistent load and with
        unpredicted input.

    ATTUNEMENT EQUATION (logit then logistic):
        z = theta0
            +  theta_a * (pi_aff * affect)
            -  theta_s * (pi_str * stress)
            -  theta_e * (pi_ext * external)
            -  theta_m * (pi_mem * memory)
            -  theta_v * (pi_vol * volatility)
        A = sigmoid(z) = 1 / (1 + exp(−z))
    OPTIONAL RESEARCH TOGGLES ADDED:
      • use_arousal_precision: arousal-driven precision & policy temperature coupling.
      • use_efe_arbiter: Expected Free Energy softmax over replay modes.
      • use_hier_pe: hierarchical (slow) prediction error blended into stress.
      • use_kalman_ext: Kalman uncertainty tracking for external load precision.
      • use_wm_gate: striato-thalamo-cortical-like WM gate policy.
      • use_drift_bias: slow stochastic coding drift bias per replay mode.
      • use_precision_anneal: precision annealing conditioned on action outcomes.
    Signs reflect the intuition: affect helps; stress, high load, and volatility
    hurt. Optional multipliers let you sweep sensitivities per study/preset.
    """
    if total_ticks <= 0:
        return []

    requested_seed: Optional[int] = seed
    rng_streams, rng, sensory_py_rng, sensory_np_rng, sensory_py_seed, sensory_np_seed = _init_rngs(requested_seed)
    effective_seed = rng_streams.master_seed

    start_time = time.perf_counter()

    pi_aff = 1.0
    pi_str = 1.0
    pi_mem = 1.0
    pi_vol = 1.0

    params = {
        'theta0': theta0,
        'theta_a': 2.0,
        'theta_s': 2.0,
        'theta_e': 2.0,
        'theta_m': 1.5,
        'theta_v': 1.0,
        'theta_s_mult': theta_s_mult,
        'theta_e_mult': theta_e_mult,
        'theta_m_mult': theta_m_mult,
        'theta_v_mult': theta_v_mult,
        'att_gain': att_gain,
        'att_offset': att_offset,
        'att_scale': att_scale,
        'stress_gain': stress_gain,
        'stress_offset': stress_offset,
        'att_gate_latent': att_gate_latent,
    }
    knobs = {
        'rho_mod': 0.1,
        'lam_mod': 0.1,
        'rho_aff': 0.1,
        'lam_aff': 0.1,
        'rho_e': 0.05,
        'K_micro': 3,
        'alpha_u': 0.8,
        'beta_u': 0.3,
        'kappa': 0.3,
        'mem_gamma': 1.25,
        'SALIENCE_DROP': 0.15,
        'VOL_HIGH': 0.20,
        'STRESS_HIGH': 0.65,
        'LOAD_HIGH': 0.80,
        'tau': tau,
        'alpha': alpha,
        'beta': beta,
        'gamma': gamma,
        'stress_decay': stress_decay,
        'gate_by_attunement': gate_by_attunement,
        'gate_temperature': gate_temperature,
        'replay_softmax': replay_softmax,
        'explore_error_gain': explore_error_gain,
        'softmax_temp': softmax_temp,
        'explore_floor': explore_floor,
        'norm_stress': norm_stress,
        'norm_ext_load': norm_ext_load,
        'norm_mem_load': norm_mem_load,
        'norm_aff_vol': norm_aff_vol,
        'stress_inner_sigmoid': stress_inner_sigmoid,
    }

    max_raw_st = 500.0
    mem_capacity = max_raw_st
    base_prune_threshold = memory_prune_threshold

    # --- Apply preset overrides if requested ---
    preset_choice = _resolve_preset_choice(
        preset=preset,
        use_population_mixture=use_population_mixture,
        mixture_weights=mixture_weights,
        stratify_index=stratify_index,
        stratify_total=stratify_total,
        rng=rng,
    )
    effective_preset = preset_choice['effective_preset']
    mixture_used = preset_choice['mixture_used']
    mixture_mode = preset_choice['mixture_mode']
    chosen_subgroup = preset_choice['chosen_subgroup']
    mixture_weights = preset_choice['mixture_weights']

    params, knobs = _apply_preset_overrides(
        effective_preset=effective_preset,
        params=params,
        knobs=knobs,
        rng=rng,
        within_stratum_theta0_jitter=within_stratum_theta0_jitter,
    )

    rho_mod = knobs['rho_mod']
    lam_mod = knobs['lam_mod']
    rho_aff = knobs['rho_aff']
    lam_aff = knobs['lam_aff']
    rho_e = knobs['rho_e']
    K_micro = knobs['K_micro']
    alpha_u = knobs['alpha_u']
    beta_u = knobs['beta_u']
    kappa = knobs['kappa']
    mem_gamma = knobs['mem_gamma']
    SALIENCE_DROP = knobs['SALIENCE_DROP']
    VOL_HIGH = knobs['VOL_HIGH']
    STRESS_HIGH = knobs['STRESS_HIGH']
    LOAD_HIGH = knobs['LOAD_HIGH']
    tau = knobs['tau']
    alpha = knobs['alpha']
    beta = knobs['beta']
    gamma = knobs['gamma']
    stress_decay = knobs['stress_decay']
    gate_by_attunement = knobs['gate_by_attunement']
    gate_temperature = knobs['gate_temperature']
    replay_softmax = knobs['replay_softmax']
    explore_error_gain = knobs['explore_error_gain']
    softmax_temp = knobs['softmax_temp']
    explore_floor = knobs['explore_floor']
    theta_s_mult = params['theta_s_mult']
    theta_e_mult = params['theta_e_mult']
    theta_m_mult = params['theta_m_mult']
    theta_v_mult = params['theta_v_mult']
    norm_stress = knobs['norm_stress']
    norm_ext_load = knobs['norm_ext_load']
    norm_mem_load = knobs['norm_mem_load']
    norm_aff_vol = knobs['norm_aff_vol']
    stress_inner_sigmoid = knobs['stress_inner_sigmoid']
    att_gain = params['att_gain']
    att_offset = params['att_offset']
    att_scale = params['att_scale']
    stress_gain = params['stress_gain']
    stress_offset = params['stress_offset']
    theta0 = params['theta0']
    att_gate_latent = params['att_gate_latent']
    theta_a = params['theta_a']
    theta_s = params['theta_s']
    theta_e = params['theta_e']
    theta_m = params['theta_m']
    theta_v = params['theta_v']

    sim = SensoryInputSystem(
        low_salience_threshold=sensory_py_rng.uniform(0.3, 0.7),
        high_salience_threshold=sensory_py_rng.uniform(0.7, 0.95),
        salience_decay=salience_decay,
        highly_variable_rate=highly_variable_rate,
        low_salience_var_rate=low_salience_var_rate,
        event_rate=event_rate,
        memory_buffer_size=memory_buffer_size,
        memory_decay=memory_decay,
        memory_prune_threshold=memory_prune_threshold,
        py_random=sensory_py_rng,
        np_random=sensory_np_rng,
    )

    _, _, _, vis_arr, hear_arr, touch_arr, smell_arr, taste_arr, _, _ = _generate_base_arrays(
        total_ticks,
        seed=rng_streams.numpy_seed,
        rng=rng,
        jax_key=rng_streams.jax_key,
    )

    modalities = _init_modalities(vis_arr, hear_arr, touch_arr)
    state = SimulationState()

    series = _init_per_tick_series(total_ticks)

    # Collected logs
    logs: List[Dict] = []

    # Rolling counters for branch conditions
    for i in range(total_ticks):
        tick_out = _run_single_tick(
            i,
            sim=sim,
            modalities=modalities,
            state=state,
            base_prune_threshold=base_prune_threshold,
            mem_capacity=mem_capacity,
            mem_gamma=mem_gamma,
            rho_mod=rho_mod,
            lam_mod=lam_mod,
            rho_aff=rho_aff,
            lam_aff=lam_aff,
            salience_drop=SALIENCE_DROP,
            max_raw_st=max_raw_st,
            K_micro=K_micro,
            alpha_u=alpha_u,
            beta_u=beta_u,
            rho_e=rho_e,
            kappa=kappa,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            tau=tau,
            stress_inner_sigmoid=stress_inner_sigmoid,
            stress_decay=stress_decay,
            stress_gain=stress_gain,
            stress_offset=stress_offset,
            pi_aff=pi_aff,
            pi_str=pi_str,
            pi_mem=pi_mem,
            pi_vol=pi_vol,
            theta_params=params,
            gate_by_attunement=gate_by_attunement,
            gate_temperature=gate_temperature,
            att_gate_latent=att_gate_latent,
            norm_stress=norm_stress,
            norm_ext_load=norm_ext_load,
            norm_mem_load=norm_mem_load,
                norm_aff_vol=norm_aff_vol,
                replay_softmax=replay_softmax,
                softmax_temp=softmax_temp,
                explore_error_gain=explore_error_gain,
                explore_floor=explore_floor,
                rng=rng,
                schema_stress_prev=series.schema_stress[i-1] if i > 0 else 0.0,
            )

        _record_tick_series(
            i,
            tick_out=tick_out,
            dynamic_prunes=series.dynamic_prunes,
            avg_affect_feedback=series.avg_affect_feedback,
            mem_load_series=series.mem_load_series,
            ext_load_series=series.ext_load_series,
            affect_vol_series=series.affect_vol_series,
            schema_stress=series.schema_stress,
            attunement_scores=series.attunement_scores,
            replay_mode_series=series.replay_mode_series,
            selection_conf_series=series.selection_conf_series,
            action_exec_series=series.action_exec_series,
            prediction_error_series=series.prediction_error_series,
            episodic_write_series=series.episodic_write_series,
            semantic_micro_update_series=series.semantic_micro_update_series,
            semanticization_series=series.semanticization_series,
            decay_step_series=series.decay_step_series,
            self_model_update_series=series.self_model_update_series,
            suppression_applied_series=series.suppression_applied_series,
            early_dismissal_series=series.early_dismissal_series,
        )

        s_term, ext_term, mem_term, vol_term = tick_out.att_terms

        # Build and append the per-tick log entry
        logs.append(_build_tick_log(
            tick=i,
            att_latent=tick_out.att_latent,
            stress_latent=tick_out.stress_latent,
            att_bounded=tick_out.att_bounded,
            stress_bounded=tick_out.stress_bounded,
            theta_params=params,
            pi_aff=pi_aff,
            pi_str=pi_str,
            pi_ext=tick_out.pi_ext,
            pi_mem=pi_mem,
            pi_vol=pi_vol,
            aff=tick_out.avg_affect_feedback,
            s_term=s_term,
            ext_term=ext_term,
            mem_term=mem_term,
            vol_term=vol_term,
            ext_load=tick_out.ext_load,
            mem_load=tick_out.mem_load,
            aff_vol=tick_out.aff_vol,
            salience=tick_out.salience,
            replay_mode=tick_out.replay_mode,
            selection_confidence=tick_out.selection_confidence,
            action_executed=tick_out.action_executed,
            prediction_error=tick_out.prediction_error,
            episodic_write=tick_out.episodic_write,
            semantic_micro_update=tick_out.semantic_micro_update,
            semanticization=tick_out.semanticization,
            decay_step=tick_out.decay_step,
            self_model_update=tick_out.self_model_update,
            suppression_applied=tick_out.suppression_applied,
            early_dismissal=tick_out.early_dismissal,
            dynamic_prune=tick_out.dynamic_prune,
            attunement_score=series.attunement_scores[i],
            schema_stress_value=series.schema_stress[i],
        ))
        state.selection_confidence = tick_out.selection_confidence

    # --- Full‑tick stats before any thinning ---
    full_stats = _compute_full_stats(series.attunement_scores, series.schema_stress)

    # --- Diagnostics (non-invasive summaries for saved results_trials) ---
    diagnostics = _build_diagnostics(
        attunement_scores=series.attunement_scores,
        schema_stress=series.schema_stress,
        selection_conf_series=series.selection_conf_series,
        ext_load_series=series.ext_load_series,
        mem_load_series=series.mem_load_series,
        affect_vol_series=series.affect_vol_series,
        action_exec_series=series.action_exec_series,
        semantic_micro_update_series=series.semantic_micro_update_series,
        semanticization_series=series.semanticization_series,
        self_model_update_series=series.self_model_update_series,
        suppression_applied_series=series.suppression_applied_series,
        early_dismissal_series=series.early_dismissal_series,
        replay_mode_series=series.replay_mode_series,
        effective_preset=effective_preset,
        stratify_index=stratify_index,
        stratify_total=stratify_total,
        mixture_used=mixture_used,
        mixture_mode=mixture_mode,
        mixture_weights=mixture_weights,
        chosen_subgroup=chosen_subgroup,
        effective_seed=int(effective_seed),
        rng_streams=rng_streams,
        sensory_py_seed=int(sensory_py_seed),
        sensory_np_seed=int(sensory_np_seed),
        params=params,
        knobs=knobs,
    )

    end_time = time.perf_counter()
    logger.info("[PROFILE] Total simulation time: %.3f seconds for %s ticks.", end_time - start_time, total_ticks)

    if bin_size > 1:
        logs = downsample_logs(logs, bin_size)
    logs = _thin_logs(logs, MAX_PLOT_POINTS)

    return {
        'logs': logs,
        'stats': full_stats,
        'diagnostics': diagnostics,
    }

# -----------------------------------------------------------------------------
# Analysis and Execution
# -----------------------------------------------------------------------------
def parameter_sweep(
        param_name: str = "salience_decay",
        param_min: float = 0.001,
        param_max: float = 0.1,
        steps: int = 20,
        other_params: Dict = None
):
    """
    Sweep a single parameter across a range and print mean attunement/stress.
    This is an example of *computational phenomenology*: you vary a knob and see
    how summary behavior shifts. It helps beginners see cause→effect.
    """
    if other_params is None:
        other_params = {
            "total_ticks": 2000, "highly_variable_rate": 0.1, "event_rate": 3,
            "memory_buffer_size": 500, "memory_decay": 0.02,
            "memory_prune_threshold": 0.3, "low_salience_var_rate": 0.1
        }

    param_values = np.linspace(param_min, param_max, steps)
    logger.info("Sweeping '%s' from %s to %s", param_name, param_min, param_max)
    logger.info("%s,mean_attunement,mean_stress", param_name)

    results_att = []
    results_stress = []

    for val in param_values:
        current_params = other_params.copy()
        current_params[param_name] = val
        out = run_simulation(**current_params)
        if not out:
            continue
        if isinstance(out, dict):
            entries = out.get('logs', [])
        else:
            entries = out
        if not entries:
            continue
        att = [entry.get('attunement_score', 0.0) for entry in entries]
        stress = [entry.get('schema_stress', 0.0) for entry in entries]
        mean_att = np.mean(att)
        mean_stress = np.mean(stress)
        results_att.append(mean_att)
        results_stress.append(mean_stress)
        logger.info("%s,%s,%s", f"{val:.5f}", f"{mean_att:.5f}", f"{mean_stress:.5f}")

    for name, data in [('Attunement', results_att), ('Stress', results_stress)]:
        arr = np.array(data)
        if arr.size == 0:
            continue
        logger.info("%s Stats:", name)
        logger.info("  Std Dev: %.4f, Min: %.4f, Max: %.4f", np.std(arr), np.min(arr), np.max(arr))
        logger.info("  5th Pctl: %.4f, 95th Pctl: %.4f", np.percentile(arr, 5), np.percentile(arr, 95))

# Fitting (NC-MCM)

"""
RPM-EE Simulation Engine (learning edition)
-------------------------------------------------
This module implements a cognitively‑motivated simulation used by the RPM‑EE framework.
It is written to be readable for beginners learning Python and computational cognitive
neuroscience. Comments explain:
  • What each function does (plain English)
  • The logic and math (equations, why a logistic/softmax/etc.)
  • The cognitive neuroscience rationale (working memory, prediction error, precision)
"""

def _validate_fit_nc_mcm_inputs(
    runs: int,
    workers: int,
    draws: int,
    tune: int,
    chains: int,
    cores: int,
    target_accept: float,
    max_treedepth: int,
    sim_overrides,
) -> None:
    """Validate NC-MCM fit arguments and raise ValueError when out of contract."""
    if runs <= 0:
        raise ValueError("runs must be a positive integer.")
    if workers <= 0:
        raise ValueError("workers must be a positive integer.")
    if draws < 0 or tune < 0:
        raise ValueError("draws and tune must be non-negative.")
    if chains < 1 or cores < 1:
        raise ValueError("chains and cores must be at least 1.")
    if not (0.0 < target_accept < 1.0):
        raise ValueError("target_accept must be between 0 and 1.")
    if max_treedepth <= 0:
        raise ValueError("max_treedepth must be positive.")
    if sim_overrides is not None and not isinstance(sim_overrides, dict):
        raise ValueError("sim_overrides must be a dict if provided.")


def _check_rhat(trace, threshold: float = 1.01) -> float:
    """Return max R-hat from an ArviZ trace and log if convergence is poor."""
    import arviz as az
    rhat = az.rhat(trace)
    max_rhat = float(np.nanmax(rhat.to_array()))
    if max_rhat > threshold:
        logger.warning("Max R-hat %.4f exceeds threshold %.3f", max_rhat, threshold)
    else:
        logger.info("Convergence OK: Max R-hat = %.4f", max_rhat)
    return max_rhat


def _compute_rmse_ci(ppc, observed) -> tuple[float, np.ndarray]:
    """Compute mean RMSE and central 95% interval from posterior predictive samples."""
    C_pp = ppc.posterior_predictive["C_obs"]  # xarray (chain, draw, obs)
    C_pp_samples = C_pp.values
    obs = np.asarray(observed, dtype=float).reshape(-1)
    if C_pp_samples.shape[-1] != obs.shape[0]:
        raise ValueError(f"PPC samples length {C_pp_samples.shape[-1]} does not match observed length {obs.shape[0]}")
    rmse_per_chain = np.array([
        float(np.sqrt(np.mean((C_pp_samples[i].mean(axis=0) - obs) ** 2)))
        for i in range(C_pp_samples.shape[0])
    ])
    rmse_mean = float(rmse_per_chain.mean())
    rmse_ci = np.quantile(rmse_per_chain, [0.025, 0.975])
    return rmse_mean, rmse_ci


def _save_artifacts(trace, ppc, output_dir: str, prefix: str = "nc_mcm") -> dict:
    """Persist ArviZ trace and PPC arrays to disk; return paths as strings."""
    import pickle
    out_dir = ensure_dir(output_dir)
    trace_path = out_dir / f"{prefix}_trace.pkl"
    ppc_path = out_dir / f"{prefix}_ppc.pkl"
    with open(trace_path, "wb") as f:
        pickle.dump(trace, f)
    with open(ppc_path, "wb") as f:
        pickle.dump(ppc, f)
    logger.info("Saved artifacts: %s, %s", trace_path, ppc_path)
    return {"trace_path": str(trace_path), "ppc_path": str(ppc_path)}


def _export_fit_results_json(path: str, payload: dict) -> str:
    """Write fit summary JSON to the given path and return the written path."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    logger.info("Exported fit results to %s", out_path)
    return str(out_path)


def _make_ppc_plot(C_z_true, C_pp, output_dir: str, prefix: str = "ppc_cognition", show: bool = False) -> str:
    """Render PPC plot (png/pdf) for cognition series and return png path."""
    import matplotlib.pyplot as plt

    C_pp_mean = C_pp.mean(("chain", "draw")).values.reshape(-1)
    lo = np.quantile(C_pp, 0.05, axis=(0, 1))
    hi = np.quantile(C_pp, 0.95, axis=(0, 1))
    x = np.arange(len(C_z_true))

    plt.figure(figsize=(7, 5))
    plt.plot(C_z_true, label="True C_z")
    plt.plot(C_pp_mean, label="PPC mean")
    plt.fill_between(x, lo, hi, alpha=0.2, label="PPC 90% CI")
    plt.xlabel("Tick")
    plt.ylabel("Cognition (C_z)")
    plt.title("Posterior Predictive Check: Cognition (C_z)")
    plt.legend()
    plt.tight_layout()

    out_dir = ensure_dir(output_dir)
    png_path = out_dir / f"{prefix}.png"
    pdf_path = out_dir / f"{prefix}.pdf"
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, bbox_inches="tight")
    logger.info("Saved PPC plots to %s and %s", png_path, pdf_path)
    if show:
        plt.show()
    plt.close()
    return str(png_path)


def fit_nc_mcm(
    runs: int = 10,
    workers: int = 1,
    seed: int | None = None,
    draws: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    cores: int = 4,
    target_accept: float = 0.99,
    max_treedepth: int = 15,
    sim_overrides: dict | None = None,
    show: bool = False,
    output_dir: str = "results",
    results_prefix: str = "nc_mcm",
):
    """
    Fit the NC‑MCM (Neuro‑Cognitive Mixed Components Model) to synthetic data.

    Parameters
    ----------
    runs : int
        Number of simulation runs used to generate synthetic observations.
    workers : int
        Parallel workers for simulation generation.
    seed : int | None
        Base random seed applied to simulations and sampling.
    draws : int
        Posterior draws per chain.
    tune : int
        Tuning iterations per chain.
    chains : int
        Number of MCMC chains.
    cores : int
        Number of CPU cores provided to the sampler.
    target_accept : float
        Target acceptance probability for NUTS.
    max_treedepth : int
        Maximum treedepth for NUTS.
    sim_overrides : dict | None
        Simulation parameter overrides passed through to the generator.
    show : bool
        Whether to display plots interactively.
    output_dir : str
        Directory where artifacts (trace, PPC, plots, JSON) are written.
    results_prefix : str
        Prefix used when naming saved artifacts.

    Returns
    -------
    tuple
        (model, trace, ppc, data) from the PyMC fitting pipeline.
    """
    import matplotlib
    matplotlib.use("Agg", force=True)
    import numpy as np
    import arviz as az
    # Local import to avoid circular dependencies and to set module-level overrides
    from . import nc_mcm_model as _mcm
    from .nc_mcm_model import run_multiple_simulations, extract_data, build_nc_mcm

    _validate_fit_nc_mcm_inputs(
        runs=runs,
        workers=workers,
        draws=draws,
        tune=tune,
        chains=chains,
        cores=cores,
        target_accept=target_accept,
        max_treedepth=max_treedepth,
        sim_overrides=sim_overrides,
    )

    # Normalize naming/path to avoid overwriting artifacts when falsey values are passed
    output_dir = str(ensure_dir(output_dir or "results"))
    results_prefix = results_prefix or "nc_mcm"

    with _mcm.sim_override_scope(sim_overrides):
        logs, run_idx = run_multiple_simulations(
            n_runs=runs,
            workers=workers,
            base_seed=seed,
        )
        data = extract_data(logs, run_idx)

        model, trace, ppc = build_nc_mcm(
            data,
            n_runs=runs,
            draws=draws,
            tune=tune,
            chains=chains,
            cores=cores,
            target_accept=target_accept,
            max_treedepth=max_treedepth,
            random_seed=seed,
        )

        logger.info("=== NC-MCM Fit Summary ===")
        summary = az.summary(trace, var_names=["mu_alpha", "sigma_alpha", "mu_beta", "sigma_beta", "sigma_C"])
        logger.info("%s", summary)

        max_rhat = _check_rhat(trace)
        C_z_true = data["C_z"]
        rmse_mean, rmse_ci = _compute_rmse_ci(ppc, C_z_true)
        logger.info(
            "Posterior-predictive RMSE on C_z: %.4f [95%% CI: %.4f, %.4f]",
            rmse_mean,
            float(rmse_ci[0]),
            float(rmse_ci[1]),
        )

        C_pp = ppc.posterior_predictive["C_obs"]
        plot_path = _make_ppc_plot(C_z_true, C_pp, output_dir=output_dir, prefix=f"{results_prefix}_ppc", show=show)
        artifacts = _save_artifacts(trace, ppc, output_dir=output_dir, prefix=results_prefix)

        results_json = {
            "rmse_mean": float(rmse_mean),
            "rmse_ci": [float(rmse_ci[0]), float(rmse_ci[1])],
            "max_rhat": float(max_rhat),
            "draws": int(draws),
            "tune": int(tune),
            "chains": int(chains),
            "runs": int(runs),
            "workers": int(workers),
            "seed": None if seed is None else int(seed),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "artifacts": artifacts,
            "ppc_plot": plot_path,
        }
        json_path = os.path.join(output_dir, f"{results_prefix}_fit_results.json")
        _export_fit_results_json(json_path, results_json)

    return model, trace, ppc, data

if __name__ == "__main__":
    logger.info("--- Running Self-Test Simulation ---")
    try:
        test_out = run_simulation(total_ticks=100)
        if isinstance(test_out, dict):
            test_logs = test_out.get('logs', [])
        else:
            test_logs = test_out
        logger.info("Self-test PASSED. Generated %s log entries.", len(test_logs))
    except Exception as e:
        logger.exception("Self-test FAILED: %s", e)

    logger.info("--- Running Parameter Sweep Example ---")
    parameter_sweep(
        param_name="salience_decay",
        param_min=0.001,
        param_max=0.1,
        steps=10
    )
