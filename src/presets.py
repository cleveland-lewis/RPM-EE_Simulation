"""RPM-EE presets (research edition).

This module keeps the calibrated preset dictionaries and a thin wrapper that
delegates to the canonical engine in `src.simulation.run_simulation`.

The pedagogical/legacy teaching loop with extensive inline commentary has been
archived to `docs/teaching/learning_core.py` to keep the research runtime clean
while still providing a learning resource.
"""

from __future__ import annotations

from typing import Dict, List

from .config_schema import resolve_simulation_kwargs

__all__ = [
    'PRESETS',
    'get_preset_params',
    'list_presets',
    'run_simulation',
]

# -----------------------------------------------------------------------------
# Clinical calibration notes (retain contextual comments for the preset values)
# -----------------------------------------------------------------------------
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
# Full references are preserved in the teaching archive.
# -----------------------------------------------------------------------------

PRESETS: Dict[str, Dict[str, float]] = {
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


def get_preset_params(name: str) -> Dict[str, float]:
    """Return a copy of the preset overrides or an empty dict if missing."""
    return dict(PRESETS.get(name, {}))


def list_presets() -> List[str]:
    """Alphabetized list of available preset names."""
    return sorted(PRESETS.keys())


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
    **overrides: float,
) -> List[Dict]:
    """Delegate to the canonical simulation engine with preset-aware normalization."""
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


if __name__ == "__main__":
    print("Runtime presets module (research edition)")
    print("Teaching loop moved to docs/teaching/learning_core.py\n")
    print("Available presets:")
    for name in list_presets():
        print(f"  - {name}")
