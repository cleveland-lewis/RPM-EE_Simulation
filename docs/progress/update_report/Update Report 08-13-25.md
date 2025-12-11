# Simulation Update Report

## Grounding in Theory & Best Practices

- **Meta-control and Exploration–Exploitation Dynamics**  
  Cognitive control structures modulate the explore–exploit balance via hierarchical inference of meta-control states across time scales. This mirrors your gating and `explore_error_gain` mechanisms.  
  ([ccn.studentorg.berkeley.edu](https://ccn.studentorg.berkeley.edu/pdfs/papers/BaribaultCollins_2023_matstanlib.pdf?utm_source=chatgpt.com), [journals.sagepub.com](https://journals.sagepub.com/doi/10.1080/17470218.2017.1358292?utm_source=chatgpt.com))

- **Hierarchical Models & Active Inference**  
  Predictive coding—where prediction error drives adaptation—aligns with your model’s precision-weighted logit logic.  
  ([en.wikipedia.org](https://en.wikipedia.org/wiki/Predictive_coding?utm_source=chatgpt.com))

- **Reparameterization & Funnel Geometry**  
  Divergences in hierarchical models often trace back to funnel-shaped posterior geometry (e.g., Neal’s Funnel). Non-centered parameterizations dramatically improve sampling stability. This underpins your model changes and tighter priors.  
  ([mc-stan.org](https://mc-stan.org/docs/2_18/stan-users-guide/reparameterization-section.html?utm_source=chatgpt.com), [occasionaldivergences.com](https://occasionaldivergences.com/posts/non-centered/?utm_source=chatgpt.com))

- **Bayesian Troubleshooting Workflow**  
  Robust Bayesian modeling requires iterative diagnostics (e.g., divergences, r̂, ESS, prior checks). Your pipeline—tightening priors, increasing `target_accept`, using Student‑t likelihood—is aligned with best practices in hierarchical model safety.  
  ([arxiv.org](https://arxiv.org/pdf/1904.12765?utm_source=chatgpt.com))

## Project Description, Purpose, and Scope

This simulation project aims to develop a flexible and extensible framework for running complex simulations involving sensory inputs, memory management, and result analysis. The purpose is to enable detailed experimentation with various simulation parameters and configurations, facilitating comprehensive data collection and insightful analysis. The scope includes designing a modular architecture that supports batch processing, parameter sweeps, and efficient result storage.

## Simulation Architecture

The simulation framework is composed of several core components:

- **Sensory Input System:** Handles the acquisition and processing of sensory data required for the simulation.
- **Memory Handling:** Manages the storage and retrieval of simulation state information to support continuity and complex interactions.
- **Simulation Engine:** Executes the core simulation logic, integrating sensory inputs and memory to model dynamic behaviors.
- **Batch Runner:** Facilitates running multiple simulations in batches, supporting parameter sweeps and preset configurations.
- **Result Storage:** Organizes and saves simulation outputs efficiently, supporting multiple formats such as CSV and JSON with grouping capabilities.

## Recent Updates

### Today's Additions (2025-08-13)

**Batch Runner & Orchestration**
- Parallel execution via `ProcessPoolExecutor` with a new `--workers` flag.
- Randomized 6‑digit **batch IDs** used everywhere (folder names, filenames, printed output, and the `batch` field).
- Deterministic runs supported with a new `--seed` (per‑task seeds derived as `base + 100000*batch + 1000*combo + run`).
- Per‑combo aggregate printout added in the terminal for quick interpretation.
- **Per‑run artifacts:** `summary.csv`, `summary.json`, and a new `run_config.json` (effective parameters for that run).
- **Per‑batch artifact:** new `batch_meta.json` (batch metadata: id, grid, workers, base seed, timestamp).
- CSV headers expanded to include visibility metrics and the new knobs (see below).
- Bug fix: `_load_grid_json` now correctly calls `_load_params_json(maybe_path)`.

**Simulation Core (no behavioral change unless knobs are used)**
- `run_simulation(..., seed=None)` now returns a dict with:
  - `stats`: **full‑tick** moments (`count`, mean/SD for attunement & stress), computed before thinning.
  - `logs`: thinned entries for plotting/inspection (unchanged behavior for plots).
  - `diagnostics`: p5/50/95 for attunement & stress; mean selection confidence, external & memory loads, affect volatility; boolean event rates (action executed, micro‑updates, semanticization, self‑model, suppression, early dismissal); replay‑mode mix; plus an echoed `knobs` section for provenance.
- Base‑array generators accept an optional seed; JAX path uses the provided PRNG key when enabled.

**New Optional Knobs (default off; legacy behavior preserved when omitted)**
- `theta0`: additive bias in the attunement logit.
- `theta_s_mult`: multiplier on the stress term in the attunement logit.
- `gate_by_attunement` and `gate_temperature`: optional stochastic action gate tied to attunement.
- `replay_softmax`, `explore_error_gain`, `softmax_temp`, `explore_floor`: optional softmax‑based replay arbitration with an exploration floor.
- `theta_e_mult`, `theta_m_mult`, `theta_v_mult`: optional multipliers on external load, memory load, and affect volatility in the attunement logit.
- `norm_stress`, `norm_ext_load`, `norm_mem_load`, `norm_aff_vol`: optional online z‑scoring of contributors before they enter the logit.

**Visibility Metrics Added to CSVs**
- Means from logs: `mean_selection_confidence`, `mean_prediction_error`, `mean_ext_load`, `mean_mem_load`, `mean_affect_volatility`, `mean_salience`.
- Boolean rates: `rate_action_executed`, `rate_semantic_micro_update`, `rate_semanticization`, `rate_self_model_update`, `rate_suppression_applied`, `rate_early_dismissal`.
- New diagnostics: **action‑rate by attunement decile** (10‑bin table) to show behavioral coupling.
- Knob columns: `theta0`, `theta_s_mult`, `gate_by_attunement`, `gate_temperature`, `replay_softmax`, `explore_error_gain`, `softmax_temp`, `explore_floor`, **`theta_e_mult`, `theta_m_mult`, `theta_v_mult`, `norm_stress`, `norm_ext_load`, `norm_mem_load`, `norm_aff_vol`**.

**Predictive Model (NC‑MCM) Status & Interpretation**
- Latest fit: 2 chains × (800 tune + 800 draws) ≈ 15s; **22 divergences** remain.
- Convergence good overall (r̂≈1.00–1.01); residual noise **σ_C≈0.66** on z‑scale; **RMSE(C_z)≈0.663** (~56% variance explained relative to null ≈1.0).
- Strong effects: stress linear negative (μβ[N]≈−2.26), memory load negative (μβ[L]≈−0.64); small/weak: ext load, lagged ext load, periodic phase.
- Action items: raise `target_accept` and simplify geometry (orthogonalize N², drop weak terms, tighten random‑effect scales) to remove remaining divergences.

**NC‑MCM Changes Implemented (2025‑08‑13)**
- Reparameterized with **non‑centered** per‑run intercepts/slopes for better HMC geometry.
- **Orthogonalized quadratic**: replaced raw \(N^2\) with per‑run centered square of \(N_z\) → `N2c_z`.
- **Added predictors**: standardized `selection_confidence` (`SC_z`) and `stage_2_salience` (`SA_z`).
- **Trimmed predictors**: removed `G_prev` and `P` from the design matrix (kept `G`, `L`).
- **Tighter priors** on random‑effect scales: `sigma_beta ~ HalfNormal(0.3)`.
- Posterior predictive now samples **C_obs** only; robust handling in code to avoid PPC shape errors.
- Expected impact: fewer divergences, cleaner r̂/ESS, and lower RMSE given richer, less collinear features.

**Citation for these changes**: The modeling strategies (tight priors, robust likelihood, reparameterization) are validated in Bayesian methodology and workflow literature.  
([pubmed.ncbi.nlm.nih.gov](https://pubmed.ncbi.nlm.nih.gov/36972080/?utm_source=chatgpt.com), [benslack19.github.io](https://benslack19.github.io/data%20science/statistics/devilsfunnel_cnc_param/?utm_source=chatgpt.com))

**Example (deterministic small run)**
```bash
python batch_runner.py \
  --batches 1 --runs 3 --total-ticks 3000 \
  --grid '{"event_rate":[2,4], "salience_decay":[0.01,0.03], "theta0":[0,2], "theta_s_mult":[1.0,0.5]}' \
  --workers 4 --seed 42
```

Several important features and improvements have been recently integrated:

- Introduction of **pre_store** and **post_store** hooks to allow custom processing before and after data storage.
- Implementation of **grid sweep functionality** enabling systematic exploration of parameter spaces.
- Support for **batch runs with presets**, allowing easy reuse of predefined simulation configurations.
- Enhanced **result saving** with options for CSV and JSON grouped formats to improve data organization.
- Addition of **terminal output statistics** to provide immediate feedback and summary during simulation runs.
- Added **multi-batch run support** with configurable number of batches and runs per batch.
- Implemented **summary statistics output** after each batch, including total and per-run averages and standard deviations for attunement and stress scores.
- Integrated **preset support** into batch runs, allowing presets to be used directly in multi-batch mode from the terminal.
- Enhanced **result organization** by grouping CSV and JSON outputs for each run into a dedicated run-specific folder within the results directory.
- Updated **README and How-To instructions** to explain multi-batch functionality, parameter grid sweeps, and the use of presets in batch mode.

## Testing Status and Next Steps

- **Testing Status:** Initial tests confirm the stability of core simulation components and batch processing features. Data storage and output formatting have been validated for basic use cases.
- **Planned Next Steps:**
  - Expand metrics collection and analysis capabilities to capture more detailed simulation insights.
  - Develop additional presets to cover a wider range of scenarios and use cases.
  - Implement multi-batch analytics to enable comparative studies across different simulation runs.
  - Add per‑combo aggregate CSVs (one file per grid combo) to mirror terminal per‑combo means.
  - Wire optional gates/softmax knobs into standard presets and create a preset that lifts attunement out of ~0 for visibility tests.
  - Add correlation diagnostics (e.g., corr(attunement, stress/ext_load/affect)) to the diagnostics payload. (**action‑rate‑by‑attunement‑decile is implemented**)
  - Provide a small "analysis notebook" template that loads `batch_meta.json`, per‑run `run_config.json`, and batch CSVs to generate comparison plots.

  - Continue refining the user interface and documentation to enhance usability and accessibility.

### Actionable Next Steps by Mode

#### Programming
- **Per-combo CSVs**: Emit `combo_<key>_<val>..._summary.csv` per grid combo alongside the terminal per‑combo printout.
- **Preset wiring**: Add `theta0`, `theta_s_mult`, `gate_by_attunement`, `replay_softmax`, `explore_floor`, `gate_temperature`, `softmax_temp`, `explore_error_gain` to at least one new preset (e.g., `VISIBLE_ATTUNEMENT`) with conservative defaults.
- **CLI & headers**: Expose the above knobs via CLI `--params` and ensure they surface in all CSV headers (already added) and `run_config.json`.
- **Diagnostics**: Log correlations `corr(attunement, stress)`, `corr(attunement, ext_load)`, `corr(attunement, affect)` and an **action‑rate by attunement decile** table into `diagnostics`.
- **Seed determinism test**: Add a quick test script that runs two identical jobs with the same seeds and asserts identical `stats` and CSV rows.
- **Performance**: Add a warm‑up pass sized to the actual `total_ticks` to stabilize timing before measuring `[PROFILE]`.
- **CI checks**: Lint + minimal unit test for `_pooled_stats`, `_expand_grid`, seed derivation, and CSV header integrity.
- **Analysis notebook**: Provide a ready‑to‑run Jupyter notebook that loads `batch_meta.json`, per‑run `run_config.json`, and batch CSVs and produces comparison plots.

#### Research
- **Gating policies**: Review probabilistic gating (Bernoulli on logits, temperature scaling) and compare with threshold rules; consider entropy regularization.
- **Exploration strategies**: Survey UCB, Thompson sampling, and uncertainty‑guided replay; map to current `replay_softmax` formulation.
- **Stress–attunement coupling**: Identify normative ranges/transformations (e.g., z‑scoring stress per run, clamping) to avoid saturation.
- **Memory dynamics**: Read on consolidation/semanticization and practical proxies for `semantic_micro_update` and `semanticization` rates.
- **Seeding best practices**: Confirm JAX/NumPy/Numba seeding equivalence and edge cases for parallel PRNG streams.

#### Reading
- Papers/chapters on: action selection under uncertainty, replay prioritization, exploration–exploitation trade‑offs, and computational models of affect/stress.
- Library docs: JAX PRNG design notes; NumPy Generator seeding; Python `concurrent.futures` process forking caveats.

#### Thinking
- **Targets**: Define quantitative acceptance targets (e.g., attunement mean 0.3–0.6 when `theta0>0`; Explore ≥10–20% under high error).
- **Ablations**: Plan ablation runs toggling one knob at a time to attribute effects.
- **Robustness**: Decide how to report sensitivity to seeds and grid spacing.
- **Usability**: Decide minimal report a reader needs to reproduce/understand a batch (which is now mostly covered by `batch_meta.json` and `run_config.json`).

## Simulation ↔ Analysis Alignment (to lower RMSE)

Goal: make the statistical model a faithful analyzer of what the simulation actually uses, and reduce unmodeled noise so the model can predict more accurately.

### Changes in `simulation.py` (behavior + logging)
- **Normalization toggles (ON by default in tuning runs):** enable `norm_stress=1`, consider `norm_ext_load=1` and `norm_mem_load=1` so contributors share scale.
- **Extra multipliers:** expose `theta_e_mult`, `theta_m_mult`, `theta_v_mult` to balance negative terms; keep legacy default = 1.0.
- **Log the attunement logit terms:** record per‑tick `{theta0, stress_term, ext_term, mem_term, vol_term, aff_term, z_logit}` *after* normalization/multipliers. This makes analysis features 1‑to‑1 with the generator.
- **Exploration coupling:** use nonzero `explore_floor` (e.g., 0.05) but primarily drive Explore from prediction error via `explore_error_gain`; log a binary Explore/Exploit flag each tick.
- **Gating (optional):** if `gate_by_attunement=1`, log gate input and effective threshold/temperature; include a `gate_active` boolean.

### Changes in `arbiter.py` (decision transparency)
- **Action softmax trace:** log per‑tick action scores *before* temperature, temperature used that tick, and the chosen action index; include the resulting softmax entropy.
- **Mode diagnostics:** log `mode ∈ {Explore, Converge, Stabilize}` per tick and a one‑hot (or binary Explore flag) feature for analysis.
- **Noise controls:** expose `softmax_temp` as a knob; consider lowering during tuning passes to reduce irreducible noise, then restore.

### Changes in `nc_mcm_model.py` (analysis spec)
- **Orthogonalize quadratic:** replace raw `N²` with per‑run centered square `N2c = (N_z² − E[N_z²|run])`, then z‑score → reduces curvature‑induced divergences.
- **Trim weak/collinear predictors:** drop `G_prev` and `P` from the design matrix; re‑add only if they improve out‑of‑sample error.
- **Tighten random‑effect scales:** set `sigma_beta ~ HalfNormal(0.3)` to tame funnels; keep non‑centered parameterization.
- **Add missing drivers:** include `selection_confidence` (SC), `stage_2_salience` (SA), and the Explore flag as standardized predictors to better match the generator.
- **Sampler settings for cleanliness:** use `--target_accept 0.97` (or 0.99) and `--max_treedepth 12–15` when needed.

### Quant targets & LLN guidance
- On z‑scale: **Excellent RMSE < 0.2**, **Good 0.2–0.4**, **OK ~0.4–0.6**. Current ≈0.663.
- Averaging strategy (LLN): to reach RMSE≈0.10 with σ≈0.66, need ~44 effective samples; with AR(1) ρ≈0.5 that’s ~132 raw ticks; with ρ≈0.8 that’s ~396. Increase bin/window size and/or thin to reduce autocorrelation.


### Quick presets (commands)
- **Clean geometry fit:**
  ```bash
  python nc_mcm_model.py --runs 6 --workers 3 \
    --draws 800 --tune 800 --chains 3 --cores 2 \
    --target_accept 0.97 --max_treedepth 12
  ```
- **Behavioral tuning sweep (example):**
  ```bash
  python batch_runner.py --batches 1 --runs 3 --total-ticks 3000 \
    --grid '{"event_rate":[2,4], "salience_decay":[0.01,0.03], "theta0":[4,6,8], "theta_s_mult":[0.5,0.25],
             "theta_e_mult":[1.0,0.5], "theta_m_mult":[1.0,0.7], "norm_stress":[1], "explore_floor":[0.05]}' \
    --workers 3 --seed 42
  ```

- **ASD preset batch (5×5×5000):** Conservative gating, modest exploration, elevated baseline load.
  ```bash
  python batch_runner.py \
    --batches 5 --runs 5 --workers 4 --total-ticks 5000 \
    --grid '{
      "event_rate": [3],
      "salience_decay": [0.005],
      "theta0": [4.5],
      "theta_s_mult": [0.55],
      "theta_e_mult": [0.65],
      "norm_stress": [1.2],
      "norm_ext_load": [1.3],
      "gate_by_attunement": [0],
      "gate_temperature": [1.0],
      "replay_softmax": [0.2],
      "explore_error_gain": [1.5]
    }'
  ```

## Recommended Next Steps (with Research Alignment)

1. **Add-lit references**
   - *Meta-control models*: Marković et al. (2021); Eppinger et al. (2021) — cognitive policies adapt to context.  
     ([link.springer.com](https://link.springer.com/article/10.3758/s13415-021-00919-4?utm_source=chatgpt.com))  
   - *Neural decision-making mechanisms*: propositional-predictor-critic frameworks that mirror your gating.  
     ([arxiv.org](https://arxiv.org/abs/1912.07660?utm_source=chatgpt.com))

2. **Extend Logging**
   - Log uncertainty, gating probabilities, and replay decisions akin to RL prioritization heuristics.  
     ([arxiv.org](https://arxiv.org/abs/2205.00824?utm_source=chatgpt.com))

3. **Bayesian Model Comparison**
   - Use PSIS-LOO rather than RMSE alone for comparing ablations.  
     ([arxiv.org](https://arxiv.org/abs/1611.00113?utm_source=chatgpt.com))

4. **Residual & Sensitivity Checks**
   - Conduct residual autocorrelation/heteroskedasticity diagnostics.
   - Confirm inference robustness under moderate prior loosening.  
     ([researchgate.net](https://www.researchgate.net/publication/369558255_Troubleshooting_Bayesian_cognitive_models?utm_source=chatgpt.com), [arxiv.org](https://arxiv.org/abs/2002.06467?utm_source=chatgpt.com))

5. **Reproducibility**
   - Document seeds, commit hashes, and configs per run; supports reproducibility and lineage tracking.
