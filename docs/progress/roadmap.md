# RPM-EE Project Roadmap

---

## 1. Vision, Scope, and Milestones

- **Core vision**
  - RPM‑EE (Recursive Predictive Modeling with Emotional Encoding) is a cognitively‑motivated simulation engine for studying relationships between:
    - External sensory load, working‑memory load, affect, and schema stress.
    - A latent attunement variable and downstream behavior (exploration vs exploitation, replay).
    - Clinical‑phenotype differences (NT, ADHD, ASD, MDD, etc.) via calibrated presets.
  - The project couples:
    - A time‑stepped simulation (`src/simulation.py`, `src/sensory.py`, `src/memory.py`, `src/arbiter.py`, `src/attunement.py`, `src/rpm.py`).
    - Batch/grid experimentation and trial‑level task simulators (`config/batch_runner.py`, `src/trial_wrapper.py`).
    - A preset system for clinical and theoretical regimes (`src/presets.py`).
    - Validation pipelines against empirical data (`src/validation_metrics.py`, `validation_output/`).
    - An NC‑MCM Bayesian model fitting layer (`config/nc_mcm_model.py`, `fit_nc_mcm` in `src/simulation.py`).

- [ ] **Near‑term milestones (0–3 months)**
  - [x] M1. Stabilize the **simulation API** (inputs/outputs, seed behavior, preset overrides) and document it thoroughly. {COMPLETE}
  - [x] M2. Harden the **batch runner** and **trial simulators** for reproducible experiments (config schemas, logging, result formats). {COMPLETE}
  - [x] M3. Define and document a **validation workflow** from raw simulation outputs → `validation_metrics` → preregistration‑aligned reports. {COMPLETE}
  - [x] M4. Draft a **scientific methods document** that maps code parameters to constructs and preregistered hypotheses. {COMPLETE}

- [ ] **Mid‑term milestones (3–9 months)**
  - [x] M5. Finalize **clinical presets** (NT, ADHD, ASD, MDD) with transparent parameter justification and references. {COMPLETE}
  - [x] M6. Integrate and document the **NC‑MCM fitting workflow** (synthetic → empirical) with saved models and PPC diagnostics. {COMPLETE}
  - [x] M7. Build a minimal **FastAPI + UI** surface for configuring and running simulations interactively, backed by reproducible config files. {COMPLETE}
  - [x] M8. Establish a **formal test suite & CI** that covers: {COMPLETE}
    - [ ] Core simulation invariants (no NaNs, bounded variables, monotonicities where expected).
    - [ ] Batch/grid behavior (reproducibility, pooling logic).
    - [ ] Validation metrics (regression tests on example datasets).

- [ ] **Long‑term milestones (9+ months)**
  - [x] M9. Provide **published benchmarks** and example analyses for: {COMPLETE}
    - [ ] Clinical group differences (RT distributions, stress, attunement).
    - [ ] Model‑empirical convergence (correlations, ROC/AUC, ICC, etc.).
  - [x] M10. Package RPM‑EE as a **reusable library/CLI**, including docstrings, type hints, and structured docs (e.g., Sphinx or MkDocs). {COMPLETE}
  - [x] M11. Extend to **multi‑agent or interactive tasks** if the theory calls for it; ensure the architecture can accommodate this. {COMPLETE}

---

## 2. Architecture and Module Responsibilities

- [x] **Simulation core (`src/simulation.py`)** {COMPLETE}
  - [x] Implements a time‑stepped simulation over `total_ticks` with:
    - [x] Vectorized input generation (`_generate_base_arrays` with NumPy / Numba / JAX backends).
    - [x] A `SensoryInputSystem` instance providing per‑tick affect feedback and memory metrics.
    - [x] Latent state variables: external load, memory load, affect volatility, schema stress, attunement.
    - [x] Diagnostic series: replay modes, prediction errors, action execution flags, etc.
    - [x] Optional features:
      - [x] Attunement gating of actions.
      - [x] Softmax‑based replay arbitration via `SimulationClusterArbiter`.
      - [x] Population mixture sampling (NT/ADHD/ASD, etc.) with stratification.
  - [x] Exposes:
    - [x] `run_simulation(...)` returning logs/stats/diagnostics.
    - [x] `parameter_sweep(...)` for basic sensitivity analysis.
    - [x] `fit_nc_mcm(...)` to drive the NC‑MCM Bayesian fitting pipeline.

- [x] **Presets and “learning edition” core loop (`src/presets.py`)** {IN_PROGRESS}
  - [ ] Defines a rich `PRESETS` dict with named parameter sets (default, explore_biased, converge_biased, stabilize_rest, asd_typical, adhd_typical, mdd_typical, etc.).
  - [ ] Contains its own pedagogical `run_simulation(...)` and vectorized input generation logic, overlapping conceptually with `src/simulation.py`.
  - [ ] Intended audience: readers learning Python + computational neuroscience; heavy inline commentary and theory mapping.
  - [ ] Roadmap:
    - [ ] Decide whether this module is a separate “teaching core” versus the production engine, and refactor accordingly.

- [ ] **Sensory and memory systems (`src/sensory.py`, `src/memory.py`, `src/salience.py`, `src/replay.py`, `src/replay_fsm.py`, `src/selfmodel.py`, `src/fatigue.py`)**
  - [ ] `SensoryInputSystem`:
    - [ ] Simulates modality‑specific events (vision, hearing, touch, smell, taste).
    - [ ] Handles state transitions (awake → fatigued → asleep).
    - [ ] Interacts with the memory system via a `MemoryBuffer` and long‑term storage hooks.
  - [ ] `MemoryBuffer` / `LongTermStorage`:
    - [ ] Manage salience, decay, spaced repetition, semanticization, consolidation thresholds, and pruning.
    - [ ] Provide replay of salient events and capacity management strategies (LRU‑like, salience weighted).
  - [ ] Replay / fatigue / self‑model modules:
    - [ ] Provide additional structure for replay policies, fatigue dynamics, and self‑model updating (not all are fully wired into `simulation.py` yet).

- [ ] **Arbiter and attunement interfaces (`src/arbiter.py`, `src/attunement.py`, `src/rpm.py`)**
  - [ ] `SimulationClusterArbiter`:
    - [ ] Computes utilities for candidate simulations using plausibility, emotional predictions, reward distortion, fatigue state, and optional softmax.
    - [ ] Supports adaptive weighting based on stress, volatility, salience, and confidence.
  - [ ] `SocialAttunementSystem`:
    - [ ] Scores predictions vs a moving “truth” and logs alignment/attunement history.
  - [ ] `RecursivePredictiveModeler`:
    - [ ] Constructs slot‑filled simulations from sensory events; currently simple but provides a place to plug in richer structured reasoning.

- [ ] **Batch and trial infrastructure (`config/batch_runner.py`, `src/trial_wrapper.py`, `src/trial_examples.py`, `src/stats_utils.py`)**
  - [ ] `batch_runner.py`:
    - [ ] Command‑line interface for:
      - [ ] Grid sweeps over simulation parameters.
      - [ ] Repeated runs with different seeds.
      - [ ] Optional interactive “wizard” for choosing presets and settings.
    - [ ] Handles pooling, summary statistics, JSON/CSV output, and simple plotting.
  - [ ] `trial_wrapper.py`:
    - [ ] Wraps the simulation into trial‑level tasks (e.g., reaction time paradigms).
    - [ ] Provides `TrialSimulator` and `DualTaskSimulator`, ex‑Gaussian RT fit, RT distribution validation, etc.
  - [ ] `stats_utils.py`:
    - [ ] Utilities for aggregation and writing batch/run summaries.

- [ ] **Validation and empirical alignment (`src/validation_metrics.py`, `validation_output/`)**
  - [ ] `validation_metrics.py`:
    - [ ] Implements preregistered endpoints for hypotheses H1–H5 (convergent, discriminant, predictive validity, etc.).
    - [ ] Encapsulates correlations, mixed‑effects‑style regression approximations, ROC/AUC, ICC, and predictive metrics.
  - [ ] `validation_output/`:
    - [ ] Stores empirical data, model outputs, and summary statistics, plus example plots (calibration, ROC, correlation matrix, etc.).

- [ ] **Configuration and API surface (`src/config.py`, `config/__init__.py`, `config/pytest.ini`, `config/tests/`)**
  - [ ] `src/config.py`:
    - [ ] Light FastAPI app with `/config` GET/POST for reading/writing simulation configuration files (`config.json`).
    - [ ] Currently minimal; a future UI can consume this API.
  - [ ] `config/tests`:
    - [ ] Secondary test suite around configuration, batch, and simulation behavior.

---

## 3. Scientific / Modeling Roadmap

- [ ] **3.1 Clarify “canonical” attunement and stress definitions**
  - [ ] Decide whether the canonical implementation lives in `src/simulation.py` or `src/presets.py` (or unify them).
  - [ ] Document the mathematically precise definitions of:
    - [ ] External load (and how precision weights are computed).
    - [ ] Memory load (capacity curve and exponent `mem_gamma`).
    - [ ] Affect volatility (EMA/variance details, timescales).
    - [ ] Schema stress (slow drive vs fast surprisal, role of `alpha`, `beta`, `gamma`, `kappa`, `tau`, `stress_decay`).
    - [ ] Attunement (latent linear combination, link function, any normalization options).
  - [ ] Add a dedicated theory document (e.g., `docs/model_equations.md`) with equations and code references.

- [ ] **3.2 Clinical preset calibration and documentation**
  - [ ] For each clinical preset (`asd_typical`, `adhd_typical`, `mdd_typical`, etc.):
    - [ ] Add a short narrative description of symptom dimensions being modeled (e.g., load sensitivity, volatility, exploration, baseline attunement).
    - [ ] Link parameter differences to specific empirical phenomena (e.g., RT distributions, HRV, stress reactivity).
    - [ ] Store calibration metadata (e.g., JSON sidecar with sources, data versions, date of calibration).
  - [ ] Build small scripts/notebooks to:
    - [ ] Run parameter sweeps within each preset and confirm qualitative expectations.
    - [ ] Generate synthetic RT and attunement distributions for comparison to empirical datasets.

- [ ] **3.3 NC‑MCM fitting workflow**
  - [ ] Refine `fit_nc_mcm`:
    - [ ] Make the API explicit (inputs, random seeds, output directory structure).
    - [ ] Ensure that `_SIM_OVERRIDES` is reset or scoped properly to avoid cross‑run contamination.
  - [ ] Document and test `config/nc_mcm_model.py`:
    - [ ] `run_multiple_simulations`, `extract_data`, `build_nc_mcm` interfaces.
    - [ ] Expected shapes and variable names (e.g., `C_z`, `C_obs`).
  - [ ] Provide:
    - [ ] Example scripts (e.g., `config/run_nc_mcm_example.py`).
    - [ ] Standard output artifacts (ArviZ summaries, PPC plots, RMSE metrics) with canned interpretation.

- [ ] **3.4 Validation and preregistration alignment**
  - [ ] Finish or update `validation_protocol.md` / `empirical_mapping.md` so they match:
    - [ ] Column names used in `validation_metrics.py`.
    - [ ] Thresholds encoded in `THRESHOLDS`.
  - [ ] Define a standard workflow:
    - [ ] `simulation` or `trial_wrapper` → model outputs in a standardized long‑form CSV.
    - [ ] Merge with empirical data via a documented `merge` script.
    - [ ] Call `compute_all_endpoints` (to be added) to generate a full validation report.
  - [ ] Add small regression tests:
    - [ ] Use `validation_output/model_outputs.csv` and `validation_output/empirical_data.csv` as fixtures.
    - [ ] Confirm that computed endpoints are stable across code changes.

---

## 4. Software Engineering Roadmap

- [ ] **4.1 Public API and module boundaries**
  - [ ] Define a small, stable surface for external users:
    - [ ] `src.simulation.run_simulation`
    - [ ] `src.presets.PRESETS` (+ a helper `get_preset_params(name)`).
    - [ ] `config.batch_runner.main` (CLI).
    - [ ] `src.trial_wrapper.TrialSimulator` / `DualTaskSimulator`.
    - [ ] `src.validation_metrics.*` for validation pipelines.
  - [ ] Add docstrings and type hints to all public functions/methods.
  - [ ] Avoid circular imports between `src` and `config`; ensure import paths are explicit and consistent.

- [ ] **4.2 Refactoring and deduplication**
  - [ ] Resolve overlapping implementations between:
    - [ ] `src/simulation.py` and the “learning edition” in `src/presets.py`.
    - [ ] Vectorized input generation utilities (currently duplicated patterns).
  - [ ] Factor shared logic into:
    - [ ] A dedicated `src/core.py` or `src/engine.py` (hidden behind stable public APIs).
  - [ ] Audit for unused functions/flags (e.g., experimental knobs not referenced anywhere) and:
    - [ ] Remove, or
    - [ ] Move under clearly marked “experimental” sections with tests.

- [ ] **4.3 Configuration management**
  - [ ] Define a configuration schema:
    - [ ] YAML/JSON spec for simulation, presets, batch sweeps, and trial tasks.
    - [ ] Versioning for config files, including compatibility checks.
  - [ ] Enhance `src/config.py`:
    - [ ] Strongly‑typed Pydantic models for config payloads.
    - [ ] Validation and helpful error messages when configs are incomplete or inconsistent.
  - [ ] Make all CLI scripts (e.g., `config/batch_runner.py`, `config/run_simulation.sh`, `config/run_nc-mcm.sh`) consume configs through a single path.

- [ ] **4.4 Testing and CI**
  - [ ] Consolidate tests:
    - [ ] `config/tests/` and `src/test_*.py` into a consistent structure (e.g., `tests/unit`, `tests/integration`).
  - [ ] Ensure tests cover:
    - [ ] Edge cases in `MemoryBuffer` (capacity, salience thresholds, semanticization).
    - [ ] Sensory state transitions and event generation patterns.
    - [ ] Arbiter scoring behaviors (softmax probabilities, fatigue effects).
    - [ ] Validation metrics (e.g., known toy datasets where analytic answers are known).
  - [ ] Add minimal CI configuration (GitHub Actions or similar) to:
    - [ ] Run unit tests.
    - [ ] Optionally run a subset of longer simulations with reduced `total_ticks` for smoke tests.

- [ ] **4.5 Performance and resource management**
  - [ ] Evaluate:
    - [ ] When JAX vs Numba vs pure NumPy is beneficial; document recommended hardware.
    - [ ] Memory footprint for large `total_ticks` and large batch sweeps.
  - [ ] Add user‑level controls:
    - [ ] Global random seed handling for reproducibility across JAX/NumPy/Numba.
    - [ ] Max workers and environment variable controls for `ProcessPoolExecutor`.
  - [ ] Profiling and optimization:
    - [ ] Identify hotspots in `run_simulation` and `SensoryInputSystem`.
    - [ ] Reduce redundant per‑tick allocations and Python overhead where possible without harming readability.

---

## 5. UX, Documentation, and Teaching

- [ ] **5.1 User‑facing docs**
  - [ ] Create a `docs/` structure with:
    - [ ] `getting_started.md` (install, run basic simulation, inspect outputs).
    - [ ] `simulation_api.md` (parameters, defaults, presets, outputs).
    - [ ] `batch_and_trials.md` (grid sweeps, trial tasks, RT analyses).
    - [ ] `validation_workflow.md` (from simulation to preregistered metrics).
    - [ ] `clinical_presets.md` (interpretation and caveats).
  - [ ] Add a single “map of the codebase” diagram and short narrative.

- [ ] **5.2 Teaching materials**
  - [ ] Refine “learning edition” comments and ensure they’re consistent with current code.
  - [ ] Provide small, self‑contained notebooks/markdown examples:
    - [ ] Exploring individual components (memory, sensory, arbiter).
    - [ ] Incrementally building from simple toy simulations to full presets.

- [ ] **5.3 Result visualization**
  - [ ] Standardize plotting utilities:
    - [ ] Integrate or wrap existing plotting in `config/batch_runner.py` and `validation_output/plots`.
    - [ ] Provide convenience functions for:
      - [ ] Time series (attunement, stress).
      - [ ] Histograms and RT distributions.
      - [ ] Correlation matrices and ROC curves.
  - [ ] Ensure plots can be reproduced programmatically, including saving them with metadata (preset, config hash, date).

---

## 6. Data, Reproducibility, and Archiving

- [ ] **6.1 Result structure**
  - [ ] Standardize the layout of `results/` and `archive/results_trials/`:
    - [ ] Consistent naming for runs, batches, combos, seeds.
    - [ ] Metadata files (`run_config.json`, `batch_meta.json`) with schema and version.
  - [ ] Add a small indexer utility to:
    - [ ] Scan folders and summarize available experiments.
    - [ ] Produce an index CSV/JSON for quick filtering by preset, date, or hypothesis.

- [ ] **6.2 Reproducibility guarantees**
  - [ ] Global guidelines:
    - [ ] Always set seeds when reproducibility is required.
    - [ ] Log software versions (Python, dependency versions) into meta files.
  - [ ] Provide a “reproduction script” pattern:
    - [ ] Given a `run_config.json` and seed, re‑run the exact simulation.
    - [ ] Optionally bundle into a `reproduce_run.py` CLI utility.

- [ ] **6.3 Long‑term archiving**
  - [ ] Decide on:
    - [ ] What level of aggregation is saved by default (per‑tick vs downsampled).
    - [ ] How large raw logs are pruned or compressed.
  - [ ] Provide helpers for:
    - [ ] Converting between per‑tick logs and summary tables.
    - [ ] Regenerating derived plots and metrics from archived raw data.

---

## 7. Governance and Contribution Practices

- [ ] Define contributor guidelines:
  - [ ] Coding style (type hints, docstring style, logging vs print).
  - [ ] Testing expectations for new features.
  - [ ] How to add new presets or tasks without breaking existing analyses.
- [ ] Establish versioning:
  - [ ] Semantic versioning for the simulation API and presets.
  - [ ] Change log documenting any alteration to behavior relevant for scientific results.

---

# Phase-Based Development Plan

### Phase 0: Foundational Setup & Calibration (Approx. 1–2 Months)

- [ ] **0.1 Understand & Refine Core Parameters**

- [ ] **Task**: Thoroughly document the theoretical meaning and expected range/impact of all parameters in `src/simulation.py` and `src/presets.py`.
- [ ] **Dependency**: None.
- [ ] **Output**: Updated `docs/model_equations.md` and `docs/parameters.md` (or similar) with clear explanations.
- [ ] **Benefit**: Ensures everyone understands what each "knob" does.

- [ ] **0.2 Develop Core Neurotype Presets (NT, ADHD, ASD)**

- [ ] **Task**: Based on the literature, define initial parameter sets (e.g., `theta_e_mult` for ADHD, `rho_mod` for ASD sensory processing, `theta_v_mult` for affect volatility) for Neurotypical, ADHD, and ASD profiles within `src/presets.py`.
- [ ] **Dependency**: Task 0.1 (parameter understanding).
- [ ] **Output**: Initial `default`, `adhd_typical`, `asd_typical` presets.
- [ ] **Benefit**: Establishes distinct baseline "individuals" for simulation.

- [ ] **0.3 Implement & Refine Continuous Emotional Dysregulation Dimension**

- [ ] **Task**: Integrate a single, continuous `emotional_dysregulation` parameter (0.0–1.0) into `src/simulation.py`. This parameter should scale relevant internal factors like `affect_volatility`, `stress_recovery_rate`, and potentially `memory_load_under_stress` (e.g., a higher `emotional_dysregulation` value could directly increase `base_affect_volatility`, decrease `stress_decay`, or increase `theta_m_mult` under stress).
- [ ] **Dependency**: Task 0.1 (parameter understanding).
- [ ] **Output**: Modified `run_simulation` function to accept `emotional_dysregulation` and map it to internal parameters.
- [ ] **Benefit**: Allows for nuanced modeling of emotional impact without discrete diagnoses, and enables population-level sampling.

- [ ] **0.4 Identify & Prepare Empirical Datasets for Calibration**

- [ ] **Task**: Select 2–3 specific empirical datasets (e.g., RT distributions from an ADHD study, stress-response curves from an ASD study, attentional control measures from NT controls). Ensure these datasets provide observable metrics that the RPM‑EE model can generate (e.g., RT variance, mean stress, attunement fluctuations).
- [ ] **Dependency**: Needs a clear understanding of model outputs.
- [ ] **Output**: `docs/empirical_mapping.md` with links to data sources (DOIs) and a description of how model outputs will be compared to empirical data.
- [ ] **Benefit**: Provides concrete targets for model validation.

### Phase 1: Initial Calibration & Basic Validation (Approx. 2–3 Months)

- [ ] **1.1 Develop Calibration Workflow**

- [ ] **Task**: Create or adapt scripts (e.g., in `config/nc_mcm_model.py` or new `src/calibration.py`) to systematically adjust RPM‑EE parameters to fit the empirical data identified in Task 0.4. This will likely involve Bayesian inference (as suggested by `fit_nc_mcm`) or optimization algorithms.
- [ ] **Dependency**: Tasks 0.2, 0.3, 0.4.
- [ ] **Output**: Working calibration scripts and initial "calibrated presets" for specific clinical populations (e.g., `adhd_calibrated`, `asd_calibrated`).
- [ ] **Benefit**: Empirically grounds the model's parameters.

- [ ] **1.2 Basic Validation & Sensitivity Analysis**

- [ ] **Task**: Run simulations using the calibrated presets (from Task 1.1) and compare the model's output (e.g., RT distributions, stress time series) against the empirical data. Perform sensitivity analyses on key parameters to understand their impact.
- [ ] **Dependency**: Task 1.1.
- [ ] **Output**: `docs/VALIDATION_STATUS.md` with initial results (plots, statistical comparisons), and updated `src/presets.py` with refined parameters.
- [ ] **Benefit**: Builds confidence that the model can reproduce known phenomena.

### Phase 2: Population Simulation & Mechanistic Exploration (Approx. 3–6 Months)

**2.1 Implement Population Generation**

- **Task**: Create a function (e.g., in `src/population.py` or an extension of `simulation.py`) to generate synthetic populations of individuals by sampling neurotypes (NT, ADHD, ASD based on prevalence) and drawing `emotional_dysregulation` values from a continuous distribution (e.g., a normal distribution, perhaps with different means/SDs for different neurotypes, if empirically justified).
- **Dependency**: Tasks 0.2, 0.3, 1.2.
- [ ] **Output**: A robust function for generating diverse simulated populations.
- [ ] **Benefit**: Enables large-scale simulations to study individual differences.

**2.2 Explore RPM–Emotion Interactions**

- **Task**: Run simulations across generated populations (from Task 2.1) and systematically vary task demands (e.g., high vs. low sensory load, predictable vs. unpredictable environments). Analyze how RPM efficiency, attunement, and stress interact with both neurotype and emotional dysregulation.
- **Dependency**: Task 2.1.
- **Output**: New analysis scripts, visualizations (e.g., 3D plots of RPM efficiency ~ neurotype × dysregulation), and preliminary findings on the "combination" aspect of the research question.
- **Benefit**: Directly addresses the core research question about how RPM combines with emotions in diverse individuals.

### Phase 3: Advanced Features & Dissemination (Approx. 6–9+ Months)

**3.1 Expand Neurotype Presets & Comorbidity**

- **Task**: Develop additional presets (e.g., MDD-like profiles, or more nuanced ADHD/ASD subtypes) and explicitly model comorbidity within population generation, drawing on genetic correlation data.
- **Dependency**: Phase 1 calibration, Phase 2 exploration.
- **Output**: Enriched `src/presets.py` and updated population generation logic.

**3.2 Formal Testing & CI**

- **Task**: Implement a robust test suite for all modules and integrate continuous integration (CI) to ensure code stability and reproducibility.
- **Dependency**: Ongoing throughout development.
- **Output**: Comprehensive test files and a configured CI pipeline.

**3.3 Documentation & Publication**

- **Task**: Write a detailed scientific methods document, user-facing documentation, and prepare findings for publication.
- **Dependency**: All previous phases.
- **Output**: Manuscripts, comprehensive `docs/` folder, reusable library.

---

## 8. Mapping to `issues.md` and Tracking

### 8.1 One-to-one linkage from roadmap items to issues

- Every roadmap item MUST have at least one corresponding issue entry in `issues.md`. This includes:
  - Milestones M1–M11 in Section 1.
  - Module and engineering work in Sections 2–7.
  - Phase-based tasks 0.1–3.3 in the Phase-Based Development Plan.
- The issue title MUST clearly reference its roadmap source, for example:
  - `M1: Stabilize simulation API`
  - `0.2: Develop core neurotype presets`
  - `2.2: Explore RPM–emotion interactions`

### 8.2 Required `issues.md` fields

Each issue in `issues.md` is represented in a table or structured list with at least the following fields:

- **ID** – short unique identifier (e.g., `[A1]`, `[M2]`, `[I5]`).
- **Title** – MUST include the roadmap reference (M#, 0.x, 1.x, etc.).
- **Tier** – priority label (`T1` = Critical, `T2` = Important, `T3` = Lower-priority).
- **Phase** – one of `0`, `1`, `2`, `3`, or `Maintenance`.
- **Status** – one of `{TODO}`, `{IN_PROGRESS}`, `{COMPLETE}`, `{BLOCKED - EXTERNAL DATA}`.
- **Dependencies** – list of other issue IDs that must be `{COMPLETE}` first.
- **Blocks** – list of issue IDs that are blocked by this item.
- **Target Date** – planned completion date or `—` if not time-bound.
- **Acceptance Criteria** – concrete “definition of done” (tests, docs, artifacts).

### 8.3 Phase and tier mapping

- `Phase` in `issues.md` MUST be consistent with this roadmap:
  - `0` → Phase 0: Foundational Setup & Calibration
  - `1` → Phase 1: Initial Calibration & Basic Validation
  - `2` → Phase 2: Population Simulation & Mechanistic Exploration
  - `3` → Phase 3: Advanced Features & Dissemination
- Issues that are not tied to specific roadmap phases (e.g., logging cleanup, CI plumbing, refactors) MUST use:
  - `Phase: Maintenance`.

`Tier` remains an orthogonal priority dimension (`T1`/`T2`/`T3`) and does not replace `Phase`.

### 8.4 Dependencies, blockers, and external data

- If the roadmap text describes a dependency (e.g., “1.1 depends on 0.2, 0.3, 0.4”), the corresponding issues MUST:
  - List `[0.2, 0.3, 0.4]` in **Dependencies** for `1.1`.
  - Optionally list `1.1` in **Blocks** for `0.2`, `0.3`, `0.4`.
- If an issue requires external data or resources (datasets, APIs, user input), it MUST:
  - Set `Status: {BLOCKED - EXTERNAL DATA}`.
  - Record the missing resource and source in **Acceptance Criteria** or **Dependencies**.

### 8.5 Test coverage and validation mapping

For any roadmap item that mentions tests, validation, or NC-MCM diagnostics (e.g., Sections 3.3–3.4, 4.4, Phase 1.2, 2.2, 3.2):

- The corresponding issues MUST list required tests in **Acceptance Criteria**, such as:
  - “Canonical test suite (`tests/test_canonical.py`) passes.”
  - “Validation metrics regression fixtures produce stable ROC/AUC/ICC within tolerance.”
  - “NC-MCM fitting smoke tests complete without errors on example data.”

### 8.6 Timelines and empirical datasets

- Phase duration estimates in this roadmap (e.g., “Phase 0: 1–2 months”) MUST be reflected in **Target Date** fields for all Phase-0 issues.
- Phase 0.4 (“Identify & Prepare Empirical Datasets for Calibration”) MUST be implemented as:
  - At least one issue per dataset (acquisition, cleaning, integration).
  - Clear **Acceptance Criteria** describing:
    - Data location (path/DOI).
    - Format/schema.
    - Which model outputs and metrics will be used for comparison.

### 8.7 Alignment invariants

The following invariants keep `roadmap.md` and `issues.md` in sync:

- No roadmap checkbox should be marked as completed unless all linked issues are `{COMPLETE}`.
- No issue with `Phase != Maintenance` should exist without a corresponding roadmap reference in its Title.
- Maintenance items (logging, CI, small refactors) MUST be either:
  - Explicitly grouped under a “Maintenance / Engineering Debt” category in `issues.md`, or
  - Listed in **Acceptance Criteria** as part of a parent roadmap item.

---