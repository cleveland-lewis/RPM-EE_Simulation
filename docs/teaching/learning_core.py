"""
RPM-EE Simulation — Presets & Core Loop (Learning Edition)
==========================================================
Purpose
-------
This module is the *beginner-friendly* entry point for running an RPM‑EE
(Recursive Predictive Modeling with Emotional Encoding) simulation. It mixes:
  • Declarative **PRESETS** (parameter sets for different cognitive modes)
  • A **vectorized input generator** (NumPy/Numba/JAX backends)
  • The **core simulation loop** `run_simulation(...)`
  • A tiny **parameter_sweep(...)** helper

**Archive notice:** This file is now an educational artifact only. The research
runtime uses `src/presets.py` + `src/simulation.py`; keep changes here isolated
from the production engine.

What you will learn by reading the comments
-------------------------------------------
• Python/programming: module layout, optional accelerators, docstrings, type hints,
  exponential moving averages (EMA), variance, and simple functional utilities.
• Math: precision weighting (precision ≈ 1/variance), logistic and softmax ideas,
  normalization, and timescales (fast/slow dynamics via EMA and blending).
• Cognitive neuroscience: how *external load*, *working‑memory load*, *affect level*
  and *affect volatility* drive a latent **schema stress**, which then influences a
  precision‑weighted **attunement** signal (a logistic of a linear combination).

> Delegation note: the runtime `run_simulation(...)` below now forwards to the
> authoritative engine in `src.simulation`. The original teaching loop is
> preserved as `_legacy_run_simulation(...)` for readers who want to study the
> vectorized implementation in this module.

Map from theory → code
----------------------
External load      → precision‑weighted fusion of sensory modalities (vision, hearing, touch)
Affect level/vol   → EMA and variance of affect; volatility (stdev) penalizes stability
Memory load        → capacity‑limited, nonlinear transform of short‑term size
Stress (schema)    → slow drive (homeostatic/allostatic) + fast surprisal (PE‑driven) micro‑loop
Attunement         → sigmoid( θ0 + Σ weights × contributors × precisions )

Reading tips
------------
• PRESETS only change *behavioral flavor*; they do not change the **structure**.
• Backends (JAX/Numba/NumPy) are interchangeable; outputs have the same shapes.
• Comments are written for someone new to Python and computational cog‑neuro.
"""
# -----------------------------------------------------------------------------
# Standard library imports:
#   - os, time, random: file operations, timing, and standard random numbers
#   - multiprocessing: concurrency support for parallel simulations
#   - json, glob, datetime, typing, math: data handling, file matching, time, type hints, and math
# -----------------------------------------------------------------------------
import time
import random
from typing import Any, Dict, List
import math

"""
# Python import notes:
# - Standard library modules (time, random, typing, math) are always available.
# - Third-party modules (numpy, jax, numba) are optional; we guard their imports
#   so the code still runs even if they are not installed. This is a common
#   Python pattern when you want an accelerated path but require a safe fallback.
"""

# -----------------------------------------------------------------------------
# Third-party library imports:
#   - numpy: core array operations and numerical computing
#   - jax / jax.numpy: accelerated computations on CPU/GPU/TPU with JIT support
#   - numba: optional JIT compilation for CPU performance
#   - fastapi, pydantic: building and validating web API endpoints
#   - filelock: file locking for safe concurrent access
# -----------------------------------------------------------------------------
import numpy as np

# Optional acceleration path: JAX (NumPy-like API with JIT on CPU/GPU/TPU).
# We set `USE_JAX` only if the import succeeds; otherwise we fall back.
try:
    import jax
    import jax.numpy as jnp
    from jax import random as jax_random

    USE_JAX = True
except ImportError:
    USE_JAX = False

# Optional CPU JIT: Numba compiles selected NumPy functions to fast machine code.
# We set `HAVE_NUMBA` to True only if import succeeds; the code uses it to pick
# a faster generator for large arrays.
try:
    import numba as nb

    HAVE_NUMBA = True
except ModuleNotFoundError:
    HAVE_NUMBA = False

# -----------------------------------------------------------------------------
# Project-specific imports
# -----------------------------------------------------------------------------
from .config_schema import resolve_simulation_kwargs

# Mocking the SensoryInputSystem for standalone execution
class SensoryInputSystem:
    """Minimal stand‑in for the real sensory system so this module can run standalone.
    It exposes `tick(...)` that returns a small bundle of signals used by the simulation.
    Cognitive rationale: this is a synthetic *environment* and *interoception* source.
    We provide:
      • short_term_size  → proxy for working‑memory occupancy (0..~500)
      • avg_affect_feedback → proxy for affect level (−1..1, cosine‑like drift)
      • attunement_score → placeholder not used by the core loop here
    """
    def __init__(self, **kwargs):
        """# Internal counters/state used to synthesize plausible signals"""
        self.tick_count = 0
        self.short_term_size = 50
        self.avg_affect = 0.5

    def tick(self, memory_prune_threshold: float = 0.2) -> Dict[str, Any]:
        """Advance synthetic sensors by one step and emit a measurement bundle.
        Args:
          memory_prune_threshold: float controlling how aggressively memory is pruned
                                  (passed through from the core loop; not used internally here).
        Returns:
          Dict with keys: 'attunement_score' (placeholder), 'short_term_size', 'avg_affect_feedback'.
        """
        self.tick_count += 1
        self.short_term_size = 50 + 10 * np.sin(self.tick_count / 10)
        self.avg_affect = 0.5 + 0.5 * np.cos(self.tick_count / 20)
        return {
            "attunement_score": np.random.rand(),
            "short_term_size": self.short_term_size,
            "avg_affect_feedback": self.avg_affect,
        }

"""
# WHY CONSTANTS?
# These cap plotting density and select acceleration thresholds. They are *engineering*
# settings, not theoretical parameters: changing them should not change results_trials in
# principle, only performance/visualization.
"""
# -----------------------------------------------------------------------------
# Constants: tune plotting/downsampling behavior without touching core math
# -----------------------------------------------------------------------------
MAX_PLOT_POINTS = 1500
JAX_TICK_THRESHOLD = 1_000_000
MISSING_VALUE = -999.0  # Sentinel for missing data in downsampling

# -----------------------------------------------------------------------------
# Backend smoke tests: we proactively check JAX availability and that a trivial
# computation works, then pre-compile the numba generator with a 1-tick warm-up
# so first real calls are fast. This is a common Python JIT warm-up pattern.
# -----------------------------------------------------------------------------
if USE_JAX:
    try:
        arr = jnp.arange(100)
        s = int(jnp.sum(arr).item())
        dev = jax.devices()[0]
        print(f"[JAX TEST] JAX on device {dev} OK (sum={s})")
    except Exception as e:
        print(f"[JAX TEST] ERROR initializing JAX backend: {e}. Disabling JAX path.")
        USE_JAX = False

if HAVE_NUMBA:
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
def _generate_base_arrays_jax(total_ticks: int):
    """Generate synthetic arrays using JAX and return them as NumPy arrays.
    API parity: callers get the same shapes regardless of backend. Fields include
    continuous (att, stress, affect) and discrete multimodal streams (vision/hearing/touch).
    Theory link: these streams approximate exteroceptive inputs and internal states.
    """
    seed = int(time.time() * 1000)
    key = jax_random.PRNGKey(seed)
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

def _generate_base_arrays(total_ticks: int):
    """Dispatch to JAX/Numba/NumPy generators based on availability and size.
    Prefer JAX for very large `total_ticks`, then Numba; else pure NumPy. Same shapes out.
    """
    if USE_JAX and total_ticks >= JAX_TICK_THRESHOLD:
        print(f"[INFO] Using JAX backend for {total_ticks} ticks.")
        return _generate_base_arrays_jax(total_ticks)

    if HAVE_NUMBA:
        try:
            return _generate_base_arrays_numba(total_ticks)
        except Exception as e:
            print(f"[WARN] Numba execution failed: {e}. Falling back to NumPy.")
            globals()['HAVE_NUMBA'] = False

    rng = np.random.default_rng()
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
    """Average numeric keys over fixed bins to reduce log size for plotting.
    We only average a whitelist of numeric keys; categorical/meta keys use the last
    value in each bin. This preserves trends while shrinking data. Purely cosmetic.
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
    """Stride‑sample the logs to cap total points (keeps last point intact).
    This does not change statistics; it only reduces plotting/IO load.
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
    """Flatten nested dictionaries using dotted keys (e.g., 'a.b.c').
    Useful for writing tabular CSV rows from nested metadata and diagnostics.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# =============================================================================
# PRESETS: Parameter Configurations for RPM-EE Simulation
# =============================================================================
#
# PRESET SELECTION GUIDE
# ----------------------
# Choose a preset based on your experimental or theoretical goal:
#
# BASELINE / NEUROTYPICAL PRESETS:
#   • 'default'                       → Unified neurotypical baseline (latent-space architecture)
#
# BEHAVIORAL MODE PRESETS (theoretical regimes):
#   • 'explore_biased'                → Fast exploration, high reactivity
#   • 'converge_biased'               → Focused selection, smoother dynamics
#   • 'stabilize_rest'                → Consolidation, low-energy mode
#
# CLINICAL POPULATION PRESETS (empirically calibrated):
#   • 'asd_typical'                   → Autism Spectrum Disorder profile
#   • 'adhd_typical'                  → ADHD profile (high variability)
#   • 'mdd_typical'                   → Major Depressive Disorder profile
#
# PARAMETER REFERENCE (what each parameter controls):
# ---------------------------------------------------
# ATTUNEMENT WEIGHTS (theta_*):
#   theta_a   → affect gain (positive affect ↑ attunement)
#   theta_s   → stress penalty (stress ↓ attunement)
#   theta_e   → external load penalty (sensory load ↓ attunement)
#   theta_m   → memory load penalty (WM load ↓ attunement)
#   theta_v   → affect volatility penalty (volatility ↓ attunement)
#   theta0    → baseline bias (shifts overall attunement level)
#
# ADAPTATION RATES (rho_*, lam_*):
#   rho_mod   → EMA step size for modality means
#   lam_mod   → EMA step size for modality variances
#   rho_aff   → EMA step size for affect mean
#   lam_aff   → EMA step size for affect variance
#   rho_e     → EMA step size for external load
#
# FAST SURPRISAL MICRO-LOOP:
#   K_micro   → number of micro-iterations (PE integration steps)
#   alpha_u   → prediction error gain (PE sensitivity)
#   beta_u    → leak rate (decay of fast stress)
#   kappa     → blend factor (0=slow drive, 1=fast surprisal)
#
# MEMORY DYNAMICS:
#   mem_gamma → nonlinearity exponent (>1 = steeper near capacity)
#
# STRESS DYNAMICS:
#   tau           → time constant (higher = slower stress changes)
#   stress_decay  → per-tick decay rate (prevents chronic elevation)
#
# DIAGNOSTIC THRESHOLDS (for logging/analysis):
#   SALIENCE_DROP → threshold for salience drops
#   VOL_HIGH      → threshold for high volatility
#   STRESS_HIGH   → threshold for high stress
#   LOAD_HIGH     → threshold for high load
#
# GATING & ARBITRATION (advanced):
#   gate_by_attunement → enable attunement-based action gating
#   gate_temperature   → softmax temperature for gating
#   replay_softmax     → use softmax for replay mode selection
#   softmax_temp       → temperature for replay softmax
#   explore_error_gain → PE gain for exploration mode
#   explore_floor      → minimum exploration probability
#
# MULTIPLIERS (fine-tuning):
#   theta_s_mult → stress penalty multiplier
#   theta_e_mult → external load penalty multiplier
#   theta_m_mult → memory load penalty multiplier
#   theta_v_mult → volatility penalty multiplier
#
# LATENT SPACE PARAMETERS (default_v2_calibrated only):
#   att_gain     → sigmoid slope for attunement link function
#   att_offset   → sigmoid center for attunement link function
#   att_scale    → output scaling for attunement
#   stress_gain  → sigmoid slope for stress link function
#   stress_offset → sigmoid center for stress link function
#   att_gate_latent → latent threshold for action gating
#
# =============================================================================
# CLINICAL CALIBRATION NOTES (Updated 2025-10-15)
# =============================================================================
# Clinical presets are calibrated to match empirical data from neurotypical
# and clinical populations. Parameters are grounded in peer-reviewed literature
# on attention, working memory, affect regulation, and stress reactivity.
#
# EMPIRICAL BENCHMARKS:
#
# NEUROTYPICAL (NT):
#   • RT: 400-600ms (simple), 600-900ms (complex) [Ratcliff & McKoon, 2008]
#   • Accuracy: 85-95% [Ratcliff & McKoon, 2008]
#   • Working memory: 7±2 items [Cowan, 2001]
#   • Stress: moderate reactivity, adaptive recovery
#   • Attunement: stable, moderate variability
#
# AUTISM SPECTRUM DISORDER (ASD):
#   • RT: 10-15% slower than NT [Happé & Frith, 2006]
#   • Accuracy: comparable but higher variability [Van Eylen et al., 2011]
#   • Sensory reactivity: heightened [Robertson & Baron-Cohen, 2017]
#   • Working memory: intact span, impaired manipulation [Williams et al., 2006]
#   • Stress: elevated baseline, prolonged recovery [Corbett et al., 2009]
#   • Attentional switching: reduced flexibility [Yerys et al., 2009]
#
# ADHD (ATTENTION-DEFICIT/HYPERACTIVITY DISORDER):
#   • RT: 35-50% higher variability (IIV) [Klein et al., 2006]
#   • Omission errors: 2-3x higher [Kofler et al., 2013]
#   • Working memory: reduced capacity (~4-5 items) [Kasper et al., 2012]
#   • Sustained attention: decrement over time [Huang-Pollock et al., 2012]
#   • Stress: impaired regulation, faster reactivity [Lackschewitz et al., 2008]
#   • Delay aversion: heightened temporal discounting [Sonuga-Barke, 2005]
#
# MDD (MAJOR DEPRESSIVE DISORDER):
#   • RT: 15-20% slower (psychomotor slowing) [Tsourtos et al., 2002]
#   • Accuracy: 5-10% reduction [Porter et al., 2003]
#   • Working memory: impaired, especially under load [Christopher & MacDonald, 2005]
#   • Affect: anhedonia (blunted positive affect) [Treadway & Zald, 2011]
#   • Stress: elevated cortisol, HPA dysregulation [Burke et al., 2005]
#   • Cognitive control: impaired, higher error rates [Snyder, 2013]
#   • Rumination: increased internal focus, reduced engagement [Nolen-Hoeksema, 2000]
#
# Full references listed at end of file.
# =============================================================================

PRESETS = {
    # =========================================================================
    # BASELINE / NEUROTYPICAL PRESETS
    # =========================================================================

    'default': {
        # CALIBRATED PRESET (2025-10-27 - Unified Neurotypical Baseline)
        # Target: moderate bounded attunement (~0.55-0.65 mean) with reduced chronic stress (~0.58)
        # Architecture: Latent variables → link functions → [0,1] bounded values
        #
        # Key features:
        # - Separate latent space (can be >1) from bounded output space [0,1]
        # - Latent attunement computed via linear combination of contributors
        # - Link function (sigmoid with gain/offset) maps latent → [0,1]
        # - Stress decay operates in latent space before bounding
        # - Gating/policies use latent values for thresholds, bounded for probabilities

        # Core attunement weights (latent space)
        'theta_a': 2.0,   # affect contribution
        'theta_s': 2.0,   # stress penalty (base)
        'theta_e': 2.0,   # external load penalty
        'theta_m': 1.5,   # memory load penalty
        'theta_v': 1.0,   # affect volatility penalty

        # Adaptation rates
        'rho_mod': 0.10, 'lam_mod': 0.10,
        'rho_aff': 0.10, 'lam_aff': 0.10,
        'rho_e': 0.05,

        # Fast surprisal micro-loop
        'K_micro': 3,
        'alpha_u': 0.8,
        'beta_u': 0.3,
        'kappa': 0.30,

        # Memory nonlinearity
        'mem_gamma': 1.25,

        # Diagnostic thresholds
        'SALIENCE_DROP': 0.15,
        'VOL_HIGH': 0.20,
        'STRESS_HIGH': 0.60,
        'LOAD_HIGH': 0.80,

        # Stress dynamics (latent space)
        'tau': 5.5,
        'stress_decay': 0.30,  # Aggressive decay to reduce chronic stress to ~0.58

        # --- LATENT SPACE PARAMETERS ---
        'theta0': 9.00,  # latent attunement baseline (fine-tuned for bounded mean ~0.60)
        'theta_s_mult': 0.10,  # stress penalty multiplier (reduced to compensate for lower stress)
        'theta_e_mult': 0.21,  # external load multiplier (reduced by ~75%)
        'theta_m_mult': 0.23,  # memory load multiplier (reduced by ~75%)
        'theta_v_mult': 0.23,  # volatility multiplier (reduced by ~75%)

        # --- LINK FUNCTION PARAMETERS ---
        # Attunement: latent → [0,1] via sigmoid
        'att_gain': 0.25,     # sigmoid slope (gentle for wide normal distribution)
        'att_offset': 0.0,    # sigmoid center (0.0 → sigmoid(0)=0.5)
        'att_scale': 1.0,     # output scaling (1.0 = keep in [0,1])

        # Stress: latent → [0,1] via sigmoid
        'stress_gain': 0.3,   # sigmoid slope (gentler to keep bounded stress ~0.50-0.55)
        'stress_offset': 0.65, # sigmoid center (tuned to yield bounded ~0.50)

        # --- LATENT THRESHOLDS ---
        'att_gate_latent': 0.0,  # latent threshold for action gating

        # Gating/arbitration (uses bounded values for probabilities)
        'gate_by_attunement': 1,
        'gate_temperature': 1.20,
        'replay_softmax': 0,
        'softmax_temp': 1.0,
        'explore_error_gain': 2.0,
        'explore_floor': 0.00,
    },

    # =========================================================================
    # BEHAVIORAL MODE PRESETS (theoretical regimes)
    # =========================================================================

    'explore_biased': {
        # Reacts quickly; volatility more likely to trigger Explore
        'theta_a': 2.5, 'theta_s': 1.6, 'theta_e': 1.6, 'theta_m': 1.2, 'theta_v': 0.8,
        'rho_mod': 0.15, 'lam_mod': 0.15, 'rho_aff': 0.15, 'lam_aff': 0.15, 'rho_e': 0.08,
        'K_micro': 5, 'alpha_u': 1.0, 'beta_u': 0.25, 'kappa': 0.5,
        'mem_gamma': 1.1, 'SALIENCE_DROP': 0.10, 'VOL_HIGH': 0.15, 'STRESS_HIGH': 0.75, 'LOAD_HIGH': 0.90,
        'tau': 4.0
    },
    'converge_biased': {
        # Prefers selecting and refining over exploring; smoother dynamics
        'theta_a': 1.8, 'theta_s': 2.4, 'theta_e': 2.2, 'theta_m': 1.7, 'theta_v': 1.3,
        'rho_mod': 0.07, 'lam_mod': 0.08, 'rho_aff': 0.07, 'lam_aff': 0.08, 'rho_e': 0.03,
        'K_micro': 3, 'alpha_u': 0.6, 'beta_u': 0.45, 'kappa': 0.25,
        'mem_gamma': 1.35, 'SALIENCE_DROP': 0.18, 'VOL_HIGH': 0.25, 'STRESS_HIGH': 0.60, 'LOAD_HIGH': 0.75,
        'tau': 6.0
    },
    'stabilize_rest': {
        # Consolidation, semanticization; sensitive to load/stress; emphasizes rest-like behavior
        'theta_a': 1.6, 'theta_s': 2.6, 'theta_e': 2.4, 'theta_m': 1.9, 'theta_v': 1.4,
        'rho_mod': 0.05, 'lam_mod': 0.10, 'rho_aff': 0.05, 'lam_aff': 0.10, 'rho_e': 0.02,
        'K_micro': 2, 'alpha_u': 0.5, 'beta_u': 0.6, 'kappa': 0.15,
        'mem_gamma': 1.6, 'SALIENCE_DROP': 0.20, 'VOL_HIGH': 0.30, 'STRESS_HIGH': 0.55, 'LOAD_HIGH': 0.65,
        'tau': 7.0
    },

    # =========================================================================
    # CLINICAL POPULATION PRESETS (empirically calibrated)
    # =========================================================================

    'asd_typical': {
        # Weights: stronger penalties from stress/external load, modest affect gain
        'theta_a': 2.0,   # affect
        'theta_s': 2.6,   # stress (↑)
        'theta_e': 2.5,   # external load (↑)
        'theta_m': 1.8,   # memory load (↑)
        'theta_v': 1.35,  # affect volatility (↑)

        # Adaptation rates: slightly slower than default
        'rho_mod': 0.06, 'lam_mod': 0.08,
        'rho_aff': 0.06, 'lam_aff': 0.08,
        'rho_e':   0.04,

        # Fast surprisal micro-loop: present but not dominant
        'K_micro': 3,
        'alpha_u': 0.8,
        'beta_u':  0.35,
        'kappa':   0.20,  # blend toward slower drive

        # Memory capacity & nonlinearity
        'mem_gamma': 1.5,  # ↑ nonlinearity

        # Thresholds: earlier “high” flags; slightly larger drop
        'SALIENCE_DROP': 0.22,
        'VOL_HIGH':      0.25,
        'STRESS_HIGH':   0.60,
        'LOAD_HIGH':     0.72,

        # Stress time constant: longer persistence
        'tau': 7.0,
        'theta0': 0.055,
        'theta_s_mult': 0.80,
        'theta_e_mult': 1.00,
        'theta_m_mult': 0.95,
        'theta_v_mult': 1.05
    },
    'adhd_typical': {
        # Higher reactivity/variability with intact mean near NT
        'theta_a': 2.2,   # affect gain (slightly higher)
        'theta_s': 2.0,   # stress penalty
        'theta_e': 2.0,   # external load penalty
        'theta_m': 1.4,   # memory load penalty (slightly lower)
        'theta_v': 1.2,   # volatility penalty (a bit higher than NT)

        # Adaptation / fast loop: more PE reactivity, slightly quicker environment tracking
        'rho_mod': 0.12, 'lam_mod': 0.12,
        'rho_aff': 0.12, 'lam_aff': 0.12,
        'rho_e':   0.08,

        'K_micro': 4,
        'alpha_u': 0.9,
        'beta_u':  0.25,  # slower leak → longer bursts
        'kappa':   0.45,  # tilt toward fast surprisal

        # Memory nonlinearity (slightly gentler than default)
        'mem_gamma': 1.2,

        # Thresholds tuned for more exploratory switching
        'SALIENCE_DROP': 0.12,
        'VOL_HIGH':      0.18,
        'STRESS_HIGH':   0.65,
        'LOAD_HIGH':     0.85,

        # Timescale: slightly faster stress dynamics than NT
        'tau': 4.5,

        # Gating/arbitration to allow more exploratory actions
        'replay_softmax': 1,
        'softmax_temp': 1.0,
        'explore_error_gain': 2.5,
        'explore_floor': 0.05,

        # Baseline/multipliers to keep mean near NT but allow higher variance
        'theta0': 0.07,
        'theta_s_mult': 0.65,
        'theta_e_mult': 0.85,
        'theta_m_mult': 0.90,
        'theta_v_mult': 1.00
    },
    'mdd_typical': {
        # MAJOR DEPRESSIVE DISORDER preset
        # Characterized by: psychomotor slowing, anhedonia (blunted affect), elevated stress,
        # impaired cognitive control, and rumination (internal focus).

        # Attunement weights: blunted affect gain, heightened stress/load sensitivity
        'theta_a': 1.4,   # affect gain (↓ 30% - anhedonia, blunted positive affect)
        'theta_s': 2.8,   # stress penalty (↑ 40% - HPA dysregulation, elevated cortisol)
        'theta_e': 2.4,   # external load penalty (↑ 20% - impaired cognitive control)
        'theta_m': 2.2,   # memory load penalty (↑ 45% - WM impairment under load)
        'theta_v': 1.6,   # volatility penalty (↑ 60% - affective instability)

        # Adaptation rates: slower than NT (psychomotor slowing, reduced reactivity)
        'rho_mod': 0.06,  # slower modality adaptation
        'lam_mod': 0.08,  # slower variance tracking
        'rho_aff': 0.04,  # markedly slower affect adaptation (rumination, perseveration)
        'lam_aff': 0.06,  # reduced affective flexibility
        'rho_e':   0.03,  # slower external load tracking

        # Fast surprisal micro-loop: present but dampened (blunted reactivity)
        'K_micro': 2,     # reduced micro-iterations (slowed processing)
        'alpha_u': 0.6,   # reduced PE gain (blunted error sensitivity)
        'beta_u':  0.50,  # higher leak (difficulty sustaining fast dynamics)
        'kappa':   0.20,  # tilt toward slow drive (reduced fast reactivity)

        # Memory nonlinearity: steeper (greater impairment near capacity)
        'mem_gamma': 1.65,  # ↑ from 1.25 (40% increase - steeper WM load curve)

        # Thresholds: lower tolerance for stress/load, higher salience drop
        'SALIENCE_DROP': 0.28,  # higher (reduced salience persistence)
        'VOL_HIGH':      0.30,  # lower threshold (higher volatility sensitivity)
        'STRESS_HIGH':   0.50,  # lower threshold (elevated baseline stress)
        'LOAD_HIGH':     0.60,  # lower threshold (earlier load saturation)

        # Stress time constant: longer persistence (impaired recovery, HPA dysregulation)
        'tau': 8.5,  # ↑ from 5.5 (~55% increase - prolonged stress recovery)

        # Baseline & multipliers
        'theta0': 0.025,  # much lower baseline (↓ 77% from default - anhedonia, reduced engagement)
        'theta_s_mult': 1.20,  # amplify stress penalty
        'theta_e_mult': 1.10,  # amplify external load penalty
        'theta_m_mult': 1.15,  # amplify memory load penalty
        'theta_v_mult': 1.25,  # amplify volatility penalty

        # Gating/arbitration: reduced exploratory behavior
        'gate_by_attunement': 1,
        'gate_temperature': 0.80,  # lower temperature (more deterministic, less exploration)
        'replay_softmax': 0,  # heuristic mode (reduced flexibility)
        'softmax_temp': 1.0,
        'explore_error_gain': 1.5,  # reduced from 2.0 (lower error-driven exploration)
        'explore_floor': 0.00,  # no forced exploration
    },
}

# -----------------------------------------------------------------------------
# Wrapper to canonical engine
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
        **overrides,
) -> List[Dict]:
    """
    Pedagogical entry point that delegates to the canonical engine in
    `src.simulation.run_simulation`. Keeps the learning-focused presets module
    aligned with the production core while preserving the same public signature.
    The legacy, standalone teaching loop remains available as
    `_legacy_run_simulation` below for readers.
    """
    from . import simulation as _core_sim

    forwarded = {
        "total_ticks": total_ticks,
        "salience_decay": salience_decay,
        "highly_variable_rate": highly_variable_rate,
        "event_rate": event_rate,
        "memory_buffer_size": memory_buffer_size,
        "memory_decay": memory_decay,
        "memory_prune_threshold": memory_prune_threshold,
        "low_salience_var_rate": low_salience_var_rate,
        "bin_size": bin_size,
        "preset": preset,
        "seed": seed,
    }
    forwarded.update(overrides)
    clean_kwargs = resolve_simulation_kwargs(forwarded, preset=forwarded.get("preset"))
    return _core_sim.run_simulation(**clean_kwargs)

# --- Helper to apply preset overrides ---
def _apply_preset(locals_dict, preset_name: str):
    cfg = PRESETS.get(preset_name)
    if not cfg:
        return {}
    # return a dict of overrides to set explicitly in the function scope
    return cfg

# -----------------------------------------------------------------------------
# Legacy standalone simulation core (kept for teaching/reference)
# -----------------------------------------------------------------------------
def _legacy_run_simulation(
        total_ticks: int = 2400,
        salience_decay: float = 0.01,
        highly_variable_rate: float = 0.1,
        event_rate: int = 3,
        memory_buffer_size: int = 1000,
        memory_decay: float = 0.01,
        memory_prune_threshold: float = 0.2,
        low_salience_var_rate: float = 0.1,
        bin_size: int = 1,
        preset: str = None,
        **overrides,
) -> List[Dict]:
    """Legacy standalone loop retained for pedagogical reading. The authoritative
    engine now lives in `src.simulation.run_simulation`; prefer that entry point
    for any runtime use. Run the RPM-EE core simulation for `total_ticks` and
    return a list of log dicts.

    Programming overview:
      - This function is a classic *time-stepped state update* (a for-loop over ticks).
      - We keep state in local variables/arrays (fast, cache-friendly) and only materialize
        a list of small dicts at the end for human-readable logs/plots.

    **Cognitive map (theory → code snippets)**
      • *External load* = precision‑weighted fusion of modalities → see loop (4).
      • *Affect volatility* = online stdev of affect EMA residuals → see (5).
      • *Memory load* = capacity‑limited transform (normalize, then ^mem_gamma) → see (3).
      • *Stress* = blend of slow drive (EMA of logistic(drive)) and fast surprisal (micro‑loop on PE) → see (6)–(8).
      • *Attunement* = logistic of weighted contributors with optional precisions → see (9).

    Key model concepts (mapped to code blocks below):
      1) **Preset overrides**: read-only dict of hyperparameters applied early to keep the
         loop simple. This mirrors ML "config injection" patterns.
      2) **External load**: precision-weighted fusion of discrete modalities. We maintain
         an EMA and a variance per modality to compute precision = 1/(var+eps).
      3) **Affect volatility**: online variance of affect EMA residuals → used as a penalty.
      4) **Memory load**: normalized short-term size with a nonlinearity (mem_gamma).
      5) **Stress dynamics**: slow drive (homeostatic) + fast surprisal micro-loop (PE-driven),
         then blended via kappa. tau controls homeostatic inertia.
      6) **Attunement**: logistic of a precision-weighted linear combination of contributors.

    Python concepts used:
      - Generator selection via feature flags (USE_JAX/HAVE_NUMBA) and graceful fallback.
      - Numpy vector ops for per-tick arithmetic; scalar Python floats for clarity where needed.
      - Guarding against divide-by-zero with small epsilons (e.g., 1e-6).
      - Structured logs: list[dict] so JSON/CSV export is trivial.
    Args:
      total_ticks: number of simulation steps
      salience_decay, highly_variable_rate, event_rate, ...: knobs passed to the mock sensory system
      bin_size: optional downsampling of returned logs
      preset: optional key into PRESETS for behavior selection
    Returns:
      List of dicts, one per tick, with attunement/stress and helper series for analysis.
    """
    if total_ticks <= 0:
        return []

    start_time = time.perf_counter()

    # --- Parameter group: attunement weights (θ*) control how each signal contributes ---
    theta0 = 0.0
    theta_a = 2.0  # affect (positive -> higher attunement)
    theta_s = 2.0  # stress (higher -> lower attunement)
    theta_e = 2.0  # external load (higher -> lower attunement)
    theta_m = 1.5  # memory load (higher -> lower attunement)
    theta_v = 1.0  # affect volatility (higher -> lower attunement)

    # Precisions (can be adapted online; start at 1.0)
    pi_aff = 1.0
    pi_str = 1.0
    pi_mem = 1.0
    pi_vol = 1.0

    # --- Online statistics: EMAs (rho_*) and variance EMAs (lam_*) for precision estimates ---
    rho_mod = 0.1       # modality EMA step
    lam_mod = 0.1       # modality variance EMA step
    rho_aff = 0.1       # affect EMA step
    lam_aff = 0.1       # affect var EMA step
    rho_e = 0.05        # external load EMA step

    # --- Fast micro-loop parameters: miniature dynamical system for short-timescale PE ---
    K_micro = 3
    alpha_u = 0.8
    beta_u = 0.3
    kappa = 0.3         # blend between drive-based slow stress and fast surprisal

    # --- Memory load model: capacity + nonlinearity; maps short-term size → [0,1] ---
    max_raw_st = 500.0
    mem_capacity = max_raw_st  # reuse existing max_raw_st (500)
    mem_gamma = 1.25

    alpha = 1.0
    beta = 1.0
    gamma = 0.0
    tau = 5.0
    stress_prev = 0.0
    stress_decay = 0.0  # NEW: optional per-tick stress decay rate

    # --- Diagnostic thresholds: used for flags/plotting; do not drive core math directly ---
    SALIENCE_DROP = 0.15
    VOL_HIGH = 0.20
    STRESS_HIGH = 0.65
    LOAD_HIGH = 0.80

    base_prune_threshold = memory_prune_threshold

    # Apply a preset by copying only the known keys. This avoids silently accepting typos.
    # (We intentionally do not `locals().update(...)` to keep the surface explicit.)
    if preset:
        _cfg = _apply_preset(locals(), preset)
        if _cfg:
            # Explicitly set known keys to ensure clarity
            theta_a = _cfg.get('theta_a', theta_a)
            theta_s = _cfg.get('theta_s', theta_s)
            theta_e = _cfg.get('theta_e', theta_e)
            theta_m = _cfg.get('theta_m', theta_m)
            theta_v = _cfg.get('theta_v', theta_v)
            rho_mod = _cfg.get('rho_mod', rho_mod)
            lam_mod = _cfg.get('lam_mod', lam_mod)
            rho_aff = _cfg.get('rho_aff', rho_aff)
            lam_aff = _cfg.get('lam_aff', lam_aff)
            rho_e = _cfg.get('rho_e', rho_e)
            K_micro = _cfg.get('K_micro', K_micro)
            alpha_u = _cfg.get('alpha_u', alpha_u)
            beta_u = _cfg.get('beta_u', beta_u)
            kappa = _cfg.get('kappa', kappa)
            mem_gamma = _cfg.get('mem_gamma', mem_gamma)
            SALIENCE_DROP = _cfg.get('SALIENCE_DROP', SALIENCE_DROP)
            VOL_HIGH = _cfg.get('VOL_HIGH', VOL_HIGH)
            STRESS_HIGH = _cfg.get('STRESS_HIGH', STRESS_HIGH)
            LOAD_HIGH = _cfg.get('LOAD_HIGH', LOAD_HIGH)
            tau = _cfg.get('tau', tau)
            theta0 = _cfg.get('theta0', theta0)
            stress_decay = _cfg.get('stress_decay', stress_decay)

    # --- Explicit override hook (for parameter_sweep and direct callers) ---
    if overrides:
        if 'theta0' in overrides: theta0 = float(overrides['theta0'])
        if 'theta_a' in overrides: theta_a = float(overrides['theta_a'])
        if 'theta_s' in overrides: theta_s = float(overrides['theta_s'])
        if 'theta_e' in overrides: theta_e = float(overrides['theta_e'])
        if 'theta_m' in overrides: theta_m = float(overrides['theta_m'])
        if 'theta_v' in overrides: theta_v = float(overrides['theta_v'])
        if 'tau' in overrides:      tau    = float(overrides['tau'])

    sim = SensoryInputSystem(
        low_salience_threshold=random.uniform(0.3, 0.7),
        high_salience_threshold=random.uniform(0.7, 0.95),
        salience_decay=salience_decay,
        highly_variable_rate=highly_variable_rate,
        low_salience_var_rate=low_salience_var_rate,
        event_rate=event_rate,
        memory_buffer_size=memory_buffer_size,
        memory_decay=memory_decay,
        memory_prune_threshold=memory_prune_threshold
    )

    _, ext_stress_arr, _, vis_arr, hear_arr, touch_arr, smell_arr, taste_arr, _, _ = _generate_base_arrays(total_ticks)

    # Modality configurations: normalize to [0,1] using their known max values
    modalities = {
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
        # smell and taste are zeros in current generator; omit or include with max=1 to keep flexible
    }

    # External load trackers
    e_ema = 0.0

    # Affect volatility trackers
    ema_aff = 0.0
    var_aff = 1e-6

    attunement_scores = np.zeros(total_ticks, dtype=np.float32)
    schema_stress = np.zeros(total_ticks, dtype=np.float32)
    avg_affect_feedback = np.zeros(total_ticks, dtype=np.float32)
    dynamic_prunes = np.zeros(total_ticks, dtype=np.float32)

    ext_load_series = np.zeros(total_ticks, dtype=np.float32)
    mem_load_series = np.zeros(total_ticks, dtype=np.float32)
    affect_vol_series = np.zeros(total_ticks, dtype=np.float32)

    for i in range(total_ticks):
        # (1) Tie memory pruning threshold to current stress via a smooth sigmoid
        dynamic_prune = base_prune_threshold + 0.25 * (1.0 / (1.0 + np.exp(-stress_prev)) - 0.5)
        dynamic_prunes[i] = dynamic_prune

        # (2) Advance synthetic sensors and read current affect + short-term size
        tick_result = sim.tick(memory_prune_threshold=dynamic_prune)
        avg_affect_feedback[i] = float(tick_result["avg_affect_feedback"])  # a_i in [-1,1]

        # (3) Compute capacity-limited memory load and record the series
        # Memory as bounded resource: normalize to [0,1], then apply nonlinearity (gamma>1 makes load bite near capacity).
        short_term_size = float(tick_result["short_term_size"])  # raw units up to ~500
        mem_load = min(1.0, max(0.0, short_term_size / mem_capacity)) ** mem_gamma
        mem_load_series[i] = mem_load

        # (4) Fuse modalities with precision weighting (variance → precision)
        # Precision weighting: precision ≈ 1/variance. More reliable modalities (lower variance)
        # get higher weight. We track EMA and variance per modality to update precision online.
        # This mirrors predictive‑processing where precision gates prediction‑error influence.
        weighted_sum = 0.0
        pi_sum = 0.0
        for name, md in modalities.items():
            # Normalize raw modality to [0,1]
            raw = float(md['arr'][i]) / md['max'] if md['max'] > 0 else 0.0
            # Online EMA and variance for precision
            resid = raw - md['ema']
            md['ema'] += rho_mod * resid
            md['var'] = (1.0 - lam_mod) * md['var'] + lam_mod * (resid * resid)
            md['pi'] = 1.0 / (md['var'] + 1e-6)
            weighted_sum += md['pi'] * raw
            pi_sum += md['pi']
        ext_load = weighted_sum / (pi_sum + 1e-9)
        ext_load_series[i] = ext_load
        pi_ext = pi_sum / max(len(modalities), 1)

        # (5) Track affect EMA + variance; stdev becomes a volatility penalty
        # Affect volatility = sqrt(variance of EMA residuals). High volatility penalizes attunement stability.
        aff = avg_affect_feedback[i]
        d_aff = aff - ema_aff
        ema_aff += rho_aff * d_aff
        var_aff = (1.0 - lam_aff) * var_aff + lam_aff * (d_aff * d_aff)
        aff_vol = float(np.sqrt(max(var_aff, 1e-12)))
        affect_vol_series[i] = aff_vol

        # (6) Slow drive-based stress (homeostatic component)
        # Slow (homeostatic) stress: logistic of combined internal/external load, then EMA with time constant tau.
        int_load = short_term_size / max_raw_st
        drive = alpha * int_load + beta * ext_load + gamma
        new_s = 1.0 / (1.0 + np.exp(-drive))
        s_drive = (1.0 - 1.0 / tau) * stress_prev + (1.0 / tau) * new_s

        # (7) Fast surprisal micro-loop: integrate prediction error with leak
        # Fast surprisal loop: integrate precision‑scaled prediction error with leak, producing a quick stress spike.
        u = 0.0  # local fast state; could also be carried over if desired
        for _ in range(K_micro):
            pe = ext_load - e_ema
            u += alpha_u * (pi_ext * pe) - beta_u * u
        e_ema = (1.0 - rho_e) * e_ema + rho_e * ext_load
        s_fast = 1.0 / (1.0 + np.exp(-u))

        # (8) Blend slow and fast stress components
        # Blend fast/slow stress: kappa→0 favors slow stability; kappa→1 favors reactivity.
        s_next = (1.0 - kappa) * s_drive + kappa * s_fast

        # (8b) Apply optional stress decay to prevent chronic elevation
        # Stress decay: s_next = s_next * (1 - decay_rate)
        # This prevents chronic stress accumulation by introducing a per-tick decay.
        # Example: stress_decay=0.05 means 5% decay per tick.
        if stress_decay > 0.0:
            s_next = max(0.0, s_next * (1.0 - stress_decay))

        stress_prev = s_next
        schema_stress[i] = float(s_next)

        # (9) Precision-weighted logistic attunement
        # Attunement logit (then passed through sigmoid):
        #   + theta0                : baseline bias
        #   + theta_a * (pi_aff*aff): affect helps engagement
        #   − theta_s * (pi_str*s)  : stress lowers engagement
        #   − theta_e * (pi_ext*e)  : external load consumes bandwidth
        #   − theta_m * (pi_mem*m)  : memory load consumes bandwidth
        #   − theta_v * (pi_vol*v)  : affect volatility destabilizes selection
        z = (
            theta0
            + theta_a * (pi_aff * aff)
            - theta_s * (pi_str * s_next)
            - theta_e * (pi_ext * ext_load)
            - theta_m * (pi_mem * mem_load)
            - theta_v * (pi_vol * aff_vol)
        )
        A_hat = 1.0 / (1.0 + np.exp(-z))

        # Optional: prediction-error correction toward an observed cue y_i
        # If you define y_i later, enable the following with a nonzero pi_y and learning rate eta
        # eta = 0.0
        # pi_y = 0.0
        # y_i = A_hat
        # A = np.clip(A_hat + eta * pi_y * (y_i - A_hat), 0.0, 1.0)
        A = np.clip(A_hat, 0.0, 1.0)
        attunement_scores[i] = float(A)

    logs = [
        {
            'clock': i,
            'attunement_score': attunement_scores[i],
            'schema_stress': schema_stress[i],
            'avg_affect_feedback': avg_affect_feedback[i],
            'dynamic_prune': dynamic_prunes[i],
            'ext_load': ext_load_series[i],
            'mem_load': mem_load_series[i],
            'affect_volatility': affect_vol_series[i],
        }
        for i in range(total_ticks)
    ]

    end_time = time.perf_counter()
    print(f"[PROFILE] Total simulation time: {end_time - start_time:.3f} seconds for {total_ticks} ticks.")

    if bin_size > 1:
        logs = downsample_logs(logs, bin_size)

    return _thin_logs(logs, MAX_PLOT_POINTS)

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
    """Sweep one parameter over a range, run the simulation, and print mean attunement/stress.
    This is *computational phenomenology*: vary a knob and observe system‑level behavior.
    Use with presets to see coherent regime shifts (e.g., explore↔converge).
    """
    if other_params is None:
        # You can pass {"preset": "explore_biased"} or any available preset to forward to run_simulation.
        other_params = {
            "total_ticks": 2000, "highly_variable_rate": 0.1, "event_rate": 3,
            "memory_buffer_size": 500, "memory_decay": 0.02,
            "memory_prune_threshold": 0.3, "low_salience_var_rate": 0.1
        }

    param_values = np.linspace(param_min, param_max, steps)
    print(f"Sweeping '{param_name}' from {param_min} to {param_max}")
    print(f"{param_name},mean_attunement,mean_stress")

    results_att = []
    results_stress = []

    for val in param_values:
        current_params = other_params.copy()
        current_params[param_name] = val
        logs = run_simulation(**current_params)
        if not logs:
            continue
        att = [entry.get('attunement_score', 0.0) for entry in logs]
        stress = [entry.get('schema_stress', 0.0) for entry in logs]
        mean_att = np.mean(att)
        mean_stress = np.mean(stress)
        results_att.append(mean_att)
        results_stress.append(mean_stress)
        print(f"{val:.5f},{mean_att:.5f},{mean_stress:.5f}")

    for name, data in [('Attunement', results_att), ('Stress', results_stress)]:
        arr = np.array(data)
        if arr.size == 0:
            continue
        print(f"\n{name} Stats:")
        print(f"  Std Dev: {np.std(arr):.4f}, Min: {np.min(arr):.4f}, Max: {np.max(arr):.4f}")
        print(f"  5th Pctl: {np.percentile(arr, 5):.4f}, 95th Pctl: {np.percentile(arr, 95):.4f}")

# -----------------------------------------------------------------------------
# Calibration utilities
# -----------------------------------------------------------------------------

from statistics import mean
# Prefer the advanced simulator if available (aligns calibration with wizard path)
try:
    from simulation import run_simulation as _SIM_RUN
    _HAS_SIM_ADV = True
except Exception:
    _SIM_RUN = None
    _HAS_SIM_ADV = False

def _evaluate_means(preset_name: str,
                    total_ticks: int,
                    seeds: list[int],
                    **overrides) -> tuple[float, float]:
    """Run multiple seeds and return (mean_attunement, mean_stress)."""
    att_vals, str_vals = [], []
    for s in seeds:
        runner = _SIM_RUN if _HAS_SIM_ADV else run_simulation
        logs = runner(total_ticks=total_ticks, preset=preset_name, seed=int(s), **overrides)
        if not logs:
            continue
        att = [row.get('attunement_score', 0.0) for row in logs]
        st  = [row.get('schema_stress', 0.0) for row in logs]
        att_vals.append(float(np.mean(att)))
        str_vals.append(float(np.mean(st)))
    return (float(mean(att_vals)), float(mean(str_vals)))

def _binary_search(param_name: str,
                   lo: float,
                   hi: float,
                   target: float,
                   monotonic: str,
                   eval_fn) -> tuple[float, dict]:
    """Generic binary search over a single override parameter to hit a scalar target.
    Returns (best_value, metrics_dict) where metrics_dict includes traces.
    monotonic: 'up' means increasing the param increases the metric; 'down' opposite.
    eval_fn(val) must return the current metric value to compare to target.
    """
    traces = []
    best = None
    for _ in range(12):  # 12 iters → resolution ~1/4096 of interval
        mid = 0.5 * (lo + hi)
        metric = float(eval_fn(mid))
        traces.append((mid, metric))
        if (monotonic == 'up' and metric < target) or (monotonic == 'down' and metric > target):
            lo = mid
        else:
            hi = mid
        best = mid
        if abs(metric - target) <= 1e-4:  # early stop
            break
    return float(best if best is not None else mid), {'traces': traces}

def calibrate_default(target_att: float = 0.010,
                      target_stress: float = 0.620,
                      total_ticks: int = 5000,
                      seeds: list[int] | None = None,
                      verbose: int = 1) -> dict:
    """Coordinate-descent calibration for the 'default' preset.

    Strategy:
      1) Tune theta0 (monotonic ↑ on attunement) to hit mean attunement target.
      2) Tune tau (monotonic ↓ on stress volatility; typically ↑ pushes mean stress ↑ modestly)
         to hit mean stress target with theta0 fixed.
      3) Iterate steps (1)-(2) twice for convergence.

    Returns a dict with final overrides and observed means.
    """
    if seeds is None:
        seeds = [321, 654, 987]

    # Start from current preset values
    base = PRESETS.get('default', {})
    theta0_cur = float(base.get('theta0', 0.08))
    tau_cur    = float(base.get('tau', 5.0))

    # Search ranges (wider, still safe for this model)
    t0_lo, t0_hi = max(-0.50, theta0_cur - 0.30), theta0_cur + 0.30
    tau_lo, tau_hi = 3.0, 12.0

    def eval_att_for_theta0(val: float) -> float:
        att, _ = _evaluate_means('default', total_ticks, seeds, theta0=float(val), tau=float(tau_cur))
        return att

    def eval_str_for_tau(val: float) -> float:
        _, st = _evaluate_means('default', total_ticks, seeds, theta0=float(theta0_cur), tau=float(val))
        return st

    traces = {'theta0': [], 'tau': []}
    hit_theta0_bound = False
    hit_tau_bound = False

    for _ in range(2):  # two coordinate passes are usually enough
        # Step 1: theta0 ↑ raises attunement (monotonic up)
        theta0_cur, info0 = _binary_search('theta0', t0_lo, t0_hi, target_att, 'up', eval_att_for_theta0)
        hit_theta0_bound = (abs(theta0_cur - t0_lo) < 1e-6) or (abs(theta0_cur - t0_hi) < 1e-6)
        traces['theta0'].extend(info0['traces'])
        # Step 2: tau tuning to hit stress (empirically monotonic; adjust if your dynamics differ)
        tau_cur, info1 = _binary_search('tau', tau_lo, tau_hi, target_stress, 'up', eval_str_for_tau)
        hit_tau_bound = (abs(tau_cur - tau_lo) < 1e-6) or (abs(tau_cur - tau_hi) < 1e-6)
        traces['tau'].extend(info1['traces'])

    # Final evaluation
    mean_att, mean_str = _evaluate_means('default', total_ticks, seeds, theta0=theta0_cur, tau=tau_cur)
    result = {
        'targets': {'attunement': target_att, 'stress': target_stress},
        'final_overrides': {'theta0': float(theta0_cur), 'tau': float(tau_cur)},
        'observed_means': {'attunement': float(mean_att), 'stress': float(mean_str)},
        'traces': traces,
        'notes': {
            'used_advanced_sim': bool(_HAS_SIM_ADV),
            'hit_bounds': {'theta0': bool(hit_theta0_bound), 'tau': bool(hit_tau_bound)},
        },
    }

    if verbose:
        print("\n[Calibration Result]")
        print(f"  Overrides → theta0={theta0_cur:.3f}, tau={tau_cur:.3f}")
        print(f"  Observed  → att={mean_att:.5f}, stress={mean_str:.5f}")
        print(f"  Targets   → att={target_att:.5f}, stress={target_stress:.5f}")
        if hit_theta0_bound or hit_tau_bound:
            print("  [warn] Calibration hit search bounds → consider widening ranges or adding a second knob (e.g., theta_s_mult).")
    return result

if __name__ == "__main__":
    """# Self-test ensures this module can run on its own and prints available presets."""
    print("--- Running Self-Test Simulation ---")
    try:
        test_logs = run_simulation(total_ticks=100, preset='default')
        print(f"Self-test PASSED. Generated {len(test_logs)} log entries.")
    except Exception as e:
        print(f"Self-test FAILED: {e}")

    print("\nAvailable presets:")
    for name in PRESETS.keys():
        print("  -", name)

    print("\n--- Running Parameter Sweep Example (Converge-biased) ---")
    parameter_sweep(
        param_name="theta_e",
        param_min=0.8,
        param_max=3.0,
        steps=6,
        other_params={"total_ticks": 400, "preset": "converge_biased"}
    )
    print("\n--- Running One-Shot Calibration (default) ---")
    calibrate_default(target_att=0.010, target_stress=0.620, total_ticks=1000, seeds=[111,222,333])
# -----------------------------------------------------------------------------
# REFERENCES FOR CLINICAL CALIBRATION
# -----------------------------------------------------------------------------
"""
NEUROTYPICAL (NT) REFERENCES:

1. Ratcliff, R., & McKoon, G. (2008). The diffusion decision model: Theory and data 
   for two-choice decision tasks. Neural Computation, 20(4), 873-922.

2. Cowan, N. (2001). The magical number 4 in short-term memory: A reconsideration 
   of mental storage capacity. Behavioral and Brain Sciences, 24(1), 87-114.


AUTISM SPECTRUM DISORDER (ASD) REFERENCES:

3. Happé, F., & Frith, U. (2006). The weak coherence account: Detail-focused 
   cognitive style in autism spectrum disorders. Journal of Autism and 
   Developmental Disorders, 36(1), 5-25.

4. Van Eylen, L., Boets, B., Steyaert, J., Evers, K., Wagemans, J., & Noens, I. 
   (2011). Cognitive flexibility in autism spectrum disorder: Explaining the 
   inconsistencies? Research in Autism Spectrum Disorders, 5(4), 1390-1401.

5. Robertson, C. E., & Baron-Cohen, S. (2017). Sensory perception in autism. 
   Nature Reviews Neuroscience, 18(11), 671-684.

6. Williams, D. L., Goldstein, G., & Minshew, N. J. (2006). The profile of memory 
   function in children with autism. Neuropsychology, 20(1), 21-29.

7. Corbett, B. A., Mendoza, S., Abdullah, M., Wegelin, J. A., & Levine, S. (2006). 
   Cortisol circadian rhythms and response to stress in children with autism. 
   Psychoneuroendocrinology, 31(1), 59-68.

8. Yerys, B. E., Hepburn, S. L., Pennington, B. F., & Rogers, S. J. (2007). 
   Executive function in preschoolers with autism: Evidence consistent with a 
   secondary deficit. Journal of Autism and Developmental Disorders, 37(6), 1068-1079.


ATTENTION-DEFICIT/HYPERACTIVITY DISORDER (ADHD) REFERENCES:

9. Klein, C., Wendling, K., Huettner, P., Ruder, H., & Peper, M. (2006). 
   Intra-subject variability in attention-deficit hyperactivity disorder. 
   Biological Psychiatry, 60(10), 1088-1097.

10. Kofler, M. J., Rapport, M. D., Sarver, D. E., Raiker, J. S., Orban, S. A., 
    Friedman, L. M., & Kolomeyer, E. G. (2013). Reaction time variability in 
    ADHD: A meta-analytic review of 319 studies. Clinical Psychology Review, 
    33(6), 795-811.

11. Kasper, L. J., Alderson, R. M., & Hudec, K. L. (2012). Moderators of working 
    memory deficits in children with attention-deficit/hyperactivity disorder 
    (ADHD): A meta-analytic review. Clinical Psychology Review, 32(7), 605-617.

12. Huang-Pollock, C. L., Karalunas, S. L., Tam, H., & Moore, A. N. (2012). 
    Evaluating vigilance deficits in ADHD: A meta-analysis of CPT performance. 
    Journal of Abnormal Psychology, 121(2), 360-371.

13. Lackschewitz, H., Hüther, G., & Kröner-Herwig, B. (2008). Physiological and 
    psychological stress responses in adults with attention-deficit/hyperactivity 
    disorder (ADHD). Psychoneuroendocrinology, 33(5), 612-624.

14. Sonuga-Barke, E. J. S. (2005). Causal models of attention-deficit/hyperactivity 
    disorder: From common simple deficits to multiple developmental pathways. 
    Biological Psychiatry, 57(11), 1231-1238.


MAJOR DEPRESSIVE DISORDER (MDD) REFERENCES:

15. Tsourtos, G., Thompson, J. C., & Stough, C. (2002). Evidence of an early 
    information processing speed deficit in unipolar major depression. 
    Psychological Medicine, 32(2), 259-265.

16. Porter, R. J., Gallagher, P., Thompson, J. M., & Young, A. H. (2003). 
    Neurocognitive impairment in drug-free patients with major depressive 
    disorder. British Journal of Psychiatry, 182(3), 214-220.

17. Christopher, G., & MacDonald, J. (2005). The impact of clinical depression on 
    working memory. Cognitive Neuropsychiatry, 10(5), 379-399.

18. Treadway, M. T., & Zald, D. H. (2011). Reconsidering anhedonia in depression: 
    Lessons from translational neuroscience. Neuroscience & Biobehavioral Reviews, 
    35(3), 537-555.

19. Burke, H. M., Davis, M. C., Otte, C., & Mohr, D. C. (2005). Depression and 
    cortisol responses to psychological stress: A meta-analysis. 
    Psychoneuroendocrinology, 30(9), 846-856.

20. Snyder, H. R. (2013). Major depressive disorder is associated with broad 
    impairments on neuropsychological measures of executive function: A 
    meta-analysis and review. Psychological Bulletin, 139(1), 81-132.

21. Nolen-Hoeksema, S. (2000). The role of rumination in depressive disorders and 
    mixed anxiety/depressive symptoms. Journal of Abnormal Psychology, 109(3), 
    504-511.


GENERAL COGNITIVE NEUROSCIENCE REFERENCES:

22. Friston, K. (2010). The free-energy principle: A unified brain theory? 
    Nature Reviews Neuroscience, 11(2), 127-138.

23. Heathcote, A., Popiel, S. J., & Mewhort, D. J. (1991). Analysis of response 
    time distributions: An example using the Stroop task. Psychological Bulletin, 
    109(2), 340-347.

24. Logan, G. D. (1988). Toward an instance theory of automatization. 
    Psychological Review, 95(4), 492-527.

25. Arnsten, A. F. T. (2009). Stress signalling pathways that impair prefrontal 
    cortex structure and function. Nature Reviews Neuroscience, 10(6), 410-422.
"""
