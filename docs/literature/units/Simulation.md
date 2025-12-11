# Key Points
- The engine for the entire model. 
- Receives a sensory_packet from sensory. 
- Transports the sensory_packet to salience for tagging. 
- Receives the tagged sensory_packet and processes tags. 

"""
    Run one RPM‑EE simulation and return logs + summary stats.

    PARAMETERS (simplified):
      total_ticks: how many time steps to simulate.
      salience_decay, event_rate, ...: knobs for how often/intensely inputs arrive.
      preset: name of a preset in `presets.PRESETS` to override defaults.
      seed: set for reproducibility.

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
    