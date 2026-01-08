# RPM-EE Model Equations

Canonical reference for the RPM-EE simulation math. Equations correspond to the implementation in `src/simulation.py::run_simulation` (canonical engine) and the pedagogical delegate in `src/presets.py::run_simulation`, which forwards into the same core. Parameter names match the shared schema (`SimulationConfig` in `src/config_schema.py`).

**Implementation anchors**
- Main loop and state updates: `src/simulation.py::run_simulation`
- Pedagogical wrapper (delegates to core): `src/presets.py::run_simulation`
- Config normalization: `src/config_schema.py::SimulationConfig.filtered/resolve_simulation_kwargs`

## 1. Core Latent Variables

At each tick `t` the model tracks:

- `ext_load_t` : external load (precision-weighted fusion of modalities)
- `mem_load_t` : working-memory load (capacity-limited, nonlinear)
- `aff_t` : affect level (mean affect feedback, approximately in [−1, 1])
- `aff_vol_t` : affect volatility (short-term standard deviation of affect)
- `stress_slow_t` : slow schema stress component (drive-based)
- `stress_fast_t` : fast schema stress component (surprisal-based)
- `stress_latent_t` : combined latent schema stress (unbounded, then linked to [0, 1])
- `att_latent_t` : latent attunement (unbounded, then linked to [0, 1])
- `stress_bounded_t` : bounded schema stress (after link function)
- `att_bounded_t` : bounded attunement (after link function)

Additional logged series include replay mode, selection confidence, prediction error, and various boolean flags (e.g., semanticization, suppression), but those are driven by the core latent variables above.

## 2. External Load

For each discrete sensory modality `m` in {vision, hearing, touch}:

- Raw input (normalized to [0, 1]):

  ```math
  x_{m,t} = \frac{\text{raw}_{m,t}}{x^{\max}_m}
  ```

- Exponential moving average (EMA) of the modality:

  ```math
  \mu_{m,t} = \mu_{m,t-1} + \rho_\text{mod} (x_{m,t} - \mu_{m,t-1})
  ```

- Exponential moving variance (EMA of squared residuals):

  ```math
  v_{m,t} = (1 - \lambda_\text{mod}) v_{m,t-1} + \lambda_\text{mod} (x_{m,t} - \mu_{m,t-1})^2
  ```

- Precision (inverse variance with small epsilon guard, bounded):

  ```math
  \pi_{m,t} = \text{clip}\left(\frac{1}{v_{m,t} + \varepsilon}, \pi_{\min}, \pi_{\max}\right)
  ```

The precision-weighted external load fuses modalities:

```math
\text{ext\_load}_t = \frac{\sum_m \pi_{m,t} x_{m,t}}{\sum_m \pi_{m,t} + \varepsilon}.
```

An additional EMA/variance pair (`ema_ext`, `var_ext`) tracks the marginal distribution of `ext_load_t` itself for optional online normalization.

## 3. Working-Memory Load

The sensory system returns a short-term memory size `\text{short\_term\_size}_t` with nominal maximum `\text{mem\_capacity}` (≈ 500). The model converts this to a normalized memory load and then applies a nonlinearity:

```math
r_t = \min\left(1, \max\left(0, \frac{\text{short\_term\_size}_t}{\text{mem\_capacity}}\right)\right),
```

```math
\text{mem\_load}_t = r_t^{\gamma_\text{mem}},
```

where `γ_mem = mem_gamma ≥ 1` (e.g., 1.25 for neurotypical) controls how sharply load rises as the buffer approaches capacity.

An EMA/variance pair (`ema_mem`, `var_mem`) tracks memory load for optional z-score normalization.

## 4. Affect and Volatility

Affect level is taken directly from the sensory system:

```math
\text{aff}_t = \text{avg\_affect\_feedback}_t \in [-1, 1].
```

An EMA and variance over affect residuals define volatility:

```math
\mu^{\text{aff}}_t = \mu^{\text{aff}}_{t-1} + \rho_\text{aff} (\text{aff}_t - \mu^{\text{aff}}_{t-1}),
```

```math
v^{\text{aff}}_t = (1 - \lambda_\text{aff}) v^{\text{aff}}_{t-1} + \lambda_\text{aff} (\text{aff}_t - \mu^{\text{aff}}_{t-1})^2,
```

```math
\text{aff\_vol}_t = \sqrt{\max\left(v^{\text{aff}}_t, \varepsilon\right)}.
```

A separate EMA/variance pair (`ema_vol`, `var_vol`) tracks the distribution of `aff_vol_t` for optional z-score normalization.

## 5. Stress Dynamics (Latent and Bounded)

### 5.1 Drive-based slow component

The slow “drive” blends internal and external load using coefficients `alpha`, `beta`, `gamma`:

```math
\text{drive}_t = \alpha \cdot \text{int\_load}_t + \beta \cdot \text{ext\_load}_t + \gamma,
```

where internal load `int_load_t` is a normalized short-term size (e.g., `short_term_size_t / max_raw_st`).

Two variants exist in the code:

1. **Legacy double-sigmoid path (`stress_inner_sigmoid = 1`):**

   ```math
   s^{\text{drive}}_t = \sigma(\text{drive}_t)
   \quad\text{where } \sigma(x) = \frac{1}{1 + e^{-x}},
   ```

   ```math
   s^{\text{slow}}_{t}
   = \left(1 - \frac{1}{\tau}\right) s^{\text{slow}}_{t-1}
     + \frac{1}{\tau} s^{\text{drive}}_t.
   ```

2. **Latent-only path (`stress_inner_sigmoid = 0`, recommended):**

   ```math
   s^{\text{slow}}_{t}
   = \left(1 - \frac{1}{\tau}\right) s^{\text{slow}}_{t-1}
     + \frac{1}{\tau} \text{drive}_t.
   ```

Here `τ = tau` is the slow time constant; larger `τ` makes stress change more slowly.

### 5.2 Fast surprisal micro-loop

The fast channel integrates prediction error between `ext_load_t` and an EMA expectation `e_ema_t` over `K_micro` micro-iterations with parameters `alpha_u`, `beta_u`:

```math
u_t = 0
\quad\text{(initialize)}
```

For `k = 1..K_micro`:

```math
\text{pe}_t = \text{ext\_load}_t - e^{\text{ema}}_{t-1}
```

```math
u_t \leftarrow u_t + \alpha_u (\pi^{\text{ext}}_t \cdot \text{pe}_t) - \beta_u u_t,
```

where `π_ext_t` is a precision term derived from modality precisions.

The external-load EMA is updated as:

```math
e^{\text{ema}}_t = (1 - \rho_e) e^{\text{ema}}_{t-1} + \rho_e \cdot \text{ext\_load}_t.
```

The fast latent stress contribution is either passed through a sigmoid (legacy path) or used directly, then filtered by a fast time constant `τ_fast`:

- Legacy:

  ```math
  s^{\text{fast}}_{\text{raw}, t} = \sigma(u_t).
  ```

- Latent path:

  ```math
  s^{\text{fast}}_{\text{raw}, t} = u_t.
  ```

  ```math
  s^{\text{fast}}_t
  = \left(1 - \frac{1}{\tau_{\text{fast}}}\right) s^{\text{fast}}_{t-1}
    + \frac{1}{\tau_{\text{fast}}} s^{\text{fast}}_{\text{raw}, t}.
  ```

### 5.3 Blending, decay, and bounding

The final latent stress before bounding blends slow and fast components with `kappa`:

```math
\text{stress\_latent}_t
= (1 - \kappa) s^{\text{slow}}_{t} + \kappa s^{\text{fast}}_{t}.
```

Optional decay in latent space applies a per-tick factor `1 - stress_decay`:

```math
\text{stress\_latent}_t \leftarrow (1 - \text{stress\_decay}) \cdot \text{stress\_latent}_t.
```

Finally, the bounded stress is produced by a single link function with gain and offset:

```math
\text{stress\_bounded}_t = \sigma\big( g_s (\text{stress\_latent}_t - o_s) \big),
```

where `g_s = stress_gain`, `o_s = stress_offset`, `σ` is the logistic, and numerical clipping ensures `stress_latent_t` remains in a safe range.

An EMA/variance pair (`ema_stress`, `var_stress`) tracks `stress_bounded_t` for optional normalization.

## 6. Attunement Equation

### 6.1 Optional normalization

Each contributor can be used either in raw form or as a z-score using the running mean/variance trackers:

```math
z(x; \mu, v) = \frac{x - \mu}{\sqrt{\max(v, \varepsilon)}}.
```

Define terms:

```math
s^{*}_t   = \begin{cases}
  z(\text{stress\_bounded}_t; \mu_s, v_s), & \text{if norm\_stress = 1} \\
  \text{stress\_bounded}_t, & \text{otherwise}
\end{cases}
```

```math
\text{ext}^{*}_t = \begin{cases}
  z(\text{ext\_load}_t; \mu_e, v_e), & \text{if norm\_ext\_load = 1} \\
  \text{ext\_load}_t, & \text{otherwise}
\end{cases}
```

```math
\text{mem}^{*}_t = \begin{cases}
  z(\text{mem\_load}_t; \mu_m, v_m), & \text{if norm\_mem\_load = 1} \\
  \text{mem\_load}_t, & \text{otherwise}
\end{cases}
```

```math
\text{vol}^{*}_t = \begin{cases}
  z(\text{aff\_vol}_t; \mu_v, v_v), & \text{if norm\_aff\_vol = 1} \\
  \text{aff\_vol}_t, & \text{otherwise}
\end{cases}
```

Here `(μ_s, v_s)`, `(μ_e, v_e)`, `(μ_m, v_m)`, `(μ_v, v_v)` are running means/variances for stress, external load, memory load, and volatility respectively.

### 6.2 Latent attunement

Let `θ_a, θ_s, θ_e, θ_m, θ_v` be base weights and `θ_s_mult`, `θ_e_mult`, `θ_m_mult`, `θ_v_mult` be multipliers that re-scale penalties for stress, external load, memory load, and volatility. Let `π_aff, π_str, π_mem, π_vol` be precision-like weights tracked online from running variances. Then the latent attunement `z_t = att_latent_t` is:

```math
z_t = \theta_0
  + \theta_a  \cdot (\pi_\text{aff} \cdot \text{aff}_t)
  - (\theta_s \theta_{s,\text{mult}}) \cdot (\pi_\text{str} \cdot s^{*}_t)
  - (\theta_e \theta_{e,\text{mult}}) \cdot (\pi_\text{ext} \cdot \text{ext}^{*}_t)
  - (\theta_m \theta_{m,\text{mult}}) \cdot (\pi_\text{mem} \cdot \text{mem}^{*}_t)
  - (\theta_v \theta_{v,\text{mult}}) \cdot (\pi_\text{vol} \cdot \text{vol}^{*}_t).
```

Here `θ_0 = theta0` is the global bias. Signs enforce the intuition that positive affect improves attunement, while stress, high external/memory load, and volatility reduce it.

The implementation clips `z_t` to a finite range (e.g., [−20, 20]) for numerical stability.

### 6.3 Link function and scaling

The bounded attunement is obtained via a logistic link with parameters `att_gain`, `att_offset`, and scale `att_scale`:

```math
A_t = \sigma\big( g_a (z_t - o_a) \big),
```

```math
\text{att\_bounded}_t = \text{clip}(s_a \cdot A_t, 0, 1),
```

where `g_a = att_gain`, `o_a = att_offset`, `s_a = att_scale`. By default `att_scale = 1.0` so `att_bounded_t ∈ (0, 1)` is used directly in logs and diagnostics.

## 7. Action Gating and Replay (High-Level)

### 7.1 Selection confidence

A heuristic “selection confidence” combines stress and volatility:

```math
\text{selection\_conf}_t
= \operatorname{clip}\big(1 - 0.5 \cdot \text{stress\_bounded}_t - 0.5 \cdot \text{aff\_vol}_t,\; 0,\; 1\big).
```

This is used as an input to the replay arbiter and as a proxy for decision confidence.

### 7.2 Action gating

Two policies are available:

1. **Legacy confidence threshold (`gate_by_attunement = 0`):**

   ```math
   \text{action\_executed}_t = \neg \text{early\_dismissal}_t \wedge (\text{selection\_conf}_t > 0.4).
   ```

2. **Attunement-gated policy (`gate_by_attunement = 1`):**

   - If `z_t > att_gate_latent`, define a probability:

     ```math
     p^{\text{act}}_t = \sigma\left(\frac{z_t}{T_\text{gate}}\right),
     ```

     where `T_gate = gate_temperature`.

   - Then draw a Bernoulli action (conceptually):

     ```math
     \text{action\_executed}_t \sim \text{Bernoulli}\big(p^{\text{act}}_t\big)
     \quad\text{subject to } \neg \text{early\_dismissal}_t.
     ```

In the code, randomness is implemented via `np.random.rand() < p_act` when the gate is active and the event is not early-dismissed.

### 7.3 Replay arbiter (qualitative)

The `SimulationClusterArbiter` scores three candidate replay modes — Explore, Converge, Stabilize — using fields:

- plausibility
- emotional_prediction
- reward_distortion

Each candidate’s score is a function of stress, volatility, salience, and confidence. When `replay_softmax = 0`, the highest-scoring mode is chosen deterministically. When `replay_softmax = 1`, scores are converted to a softmax distribution with temperature `softmax_temp`, and the implementation uses the argmax of softmax-scored utilities for the logged mode label.

This arbiter affects which replay mode is active but does not directly change the core attunement equation.

**Edge-case guards and regression coverage**
- Missing fields default to zeroed contributors and still produce deterministic ties (stable ordering); regression: `tests/test_canonical.py::test_arbiter_handles_missing_fields_and_keeps_determinism_for_ties`.
- Fatigue attenuates the reward-distortion penalty via `rd_eff = rd_raw * (1 - k_fatigue * fatigue_level)`; regression: `test_arbiter_fatigue_modulates_reward_distortion_penalty`.
- Softmax mode is deterministic for equal utilities (no RNG); probabilities are computed from scores only; regression: `test_arbiter_softmax_is_deterministic_for_equal_scores`.

### 7.4 Validation schema guardrails (contract drift)

- `validate_and_normalize_columns` enforces required validation inputs with aliases: `mem_load` (`memory_load`, `mem_load_z`), `rt` (`response_time`, `rt_ms`), `accuracy` (`acc`, `correct`), `participant` (`subject`, `participant_id`). Non-finite values raise `ValidationSchemaError` early.
- `compute_memory_load_prediction` now routes through the schema guard to prevent silent column drift before computing H2a endpoints.
- Regression coverage: `tests/test_canonical.py::test_validation_schema_normalizes_aliases_and_checks_finite`, `::test_validation_schema_missing_required_column_raises`, `::test_validation_schema_rejects_nonfinite`.

### 7.4 MemoryBuffer encoding and semanticization knobs (regression notes)

- Encoding multipliers are neutral by default: coefficients are zeroed, exposure multipliers are 1.0, and `spacing_gain` is 0. Regression test `tests/test_canonical.py::test_memory_buffer_encoding_defaults_are_neutral` fixes RNG seed and confirms `initial_salience`, dynamic thresholds, and half-life draws are unchanged by optional affect/context fields.
- Turning on encoding knobs scales `initial_salience` multiplicatively (valence/arousal/meaning coefficients × exposure multiplier), and `spacing_gain` extends the drawn half-life sublinearly via `log1p(repeat_count)`; see `tests/test_canonical.py::test_memory_buffer_encoding_knobs_scale_salience_and_spacing_gain`.
- Semanticization is opt-in: defaults (`auto=False`, `gain=0`) leave episodic context intact. When enabled with age/repeat thresholds, `_semanticize_event` attenuates timing/duration/novelty and `episodic_context_strength` up to `max_bleach`; covered by `tests/test_canonical.py::test_semanticization_defaults_do_not_modify_events` and `::test_semanticization_policy_applies_when_thresholds_met`.

## 8. Summary

- **External load**: precision-weighted fusion of sensory modalities.
- **Memory load**: normalized short-term size with exponent `mem_gamma`.
- **Affect & volatility**: affect level and volatility from EMA/variance of affect.
- **Stress**: latent drive plus fast surprisal micro-loop blended by `kappa`, then mapped to [0, 1] via a logistic link with gain/offset and optional decay.
- **Attunement**: logistic of a linear combination of contributors with explicit signs and scaling multipliers, optionally normalized to z-scores.
- **Policies (gating, replay)**: use attunement, stress, volatility, and prediction error to decide whether to act and how to replay.

Together, these equations implement a recursive predictive-processing style model where precision-weighted inputs and multi-timescale stress dynamics modulate a global attunement state, which in turn shapes action, replay, and memory dynamics.

## 9. Parameter → Equation Map (canonical engine)

| Parameter | Equation / role | Code anchor |
| --- | --- | --- |
| `total_ticks` | Loop length; determines number of ticks simulated | `run_simulation` loop guard |
| `salience_decay`, `highly_variable_rate`, `event_rate`, `low_salience_var_rate` | Control sensory stream variability and salience decay | `src/sensory.py::SensoryInputSystem.tick` |
| `memory_buffer_size`, `memory_decay`, `memory_prune_threshold` | Memory buffer capacity/decay/pruning thresholds | `src/memory.py::MemoryBuffer`, `run_simulation` pruning call |
| `bin_size` | Downsampling factor for returned logs | `run_simulation` (log thinning) |
| `seed` | Master RNG seed for deterministic streams | `src.randomness.seed_everything` |
| `theta0` | Additive bias in attunement logit `z_t` | Eq. 6.2, `run_simulation` attunement block |
| `theta_s_mult`, `theta_e_mult`, `theta_m_mult`, `theta_v_mult` | Multipliers on stress/ext/mem/vol penalties in `z_t` | Eq. 6.2, attunement block |
| `theta_a`, `theta_s`, `theta_e`, `theta_m`, `theta_v` | Base weights (preset-controlled) in `z_t` | Eq. 6.2, attunement block |
| `rho_mod`, `lam_mod` | EMA/variance rates for modality means/vars | Eq. 2, modality EMAs |
| `rho_aff`, `lam_aff` | EMA/variance rates for affect mean/variance | Eq. 4, affect volatility |
| `rho_e` | EMA rate for external-load expectation | Eq. 5.2, `e_ema_t` |
| `alpha`, `beta`, `gamma` | Coefficients for slow drive in stress | Eq. 5.1 |
| `kappa` | Blend weight between slow drive and fast surprisal | Eq. 5.3 |
| `tau` | Time constant for slow stress dynamics | Eq. 5.1 |
| `stress_decay` | Per-tick decay in latent stress | Eq. 5.3 |
| `K_micro`, `alpha_u`, `beta_u` | Micro-loop iterations and PE update rates | Eq. 5.2 |
| `mem_gamma` | Exponent for working-memory load nonlinearity | Eq. 3 |
| `norm_stress`, `norm_ext_load`, `norm_mem_load`, `norm_aff_vol` | Toggle z-scoring of contributors before attunement | Eq. 6.1 |
| `att_gain`, `att_offset`, `att_scale` | Attunement link function parameters | Eq. 6.3 |
| `stress_gain`, `stress_offset` | Stress link function parameters | Eq. 5.3 |
| `gate_by_attunement`, `gate_temperature`, `att_gate_latent` | Action gating policy on attunement latent | §7.2 |
| `replay_softmax`, `softmax_temp` | Softmax vs deterministic replay arbitration | §7.3 |
| `explore_error_gain`, `explore_floor` | Replay heuristic: Explore utility vs PE | `run_simulation` replay scoring |
| `use_population_mixture`, `mixture_weights`, `stratify_index`, `stratify_total`, `within_stratum_theta0_jitter` | Population mixture selection and stratified jitter of `theta0` | `run_simulation` preset/mixture block |
| `preset` | Named preset overrides for any of the above knobs | `run_simulation` preset block, `src/presets.py::PRESETS` |

These mappings track the canonical implementation; any change to parameters or equations in `run_simulation` should update this table to preserve traceability between theory and code.

**Population mixture reproducibility**
- Random draws are driven by the master RNG seed; the chosen subgroup is repeatable for a given `seed`.
- Setting `stratify_index`/`stratify_total` produces deterministic subgroup assignment with counts proportional to `mixture_weights` (ties resolved by largest fractional remainder).
- `within_stratum_theta0_jitter` applies seeded Gaussian jitter to `theta0` after preset application; the perturbed value is deterministic for a given seed and jitter magnitude.
