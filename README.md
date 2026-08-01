# RPM-EE v1.1.0 Simulation

Recursive Predictive Modeling with Emotional Encoding (RPM-EE) simulation
architecture: a cognitive-affective simulation combining a drift-diffusion
decision model (DDM), Bayesian predictive-error precision weighting,
TD-learning-based emotional encoding, and clinically-parameterized presets
(neurotypical, ADHD, ASD, MDD).

## Quick Start

```bash
# Install dependencies (dev tools + scientific stack: numpy, scipy, pandas, matplotlib)
pip install -r requirements-dev.txt

# Install pre-commit hooks (runs formatting/lint/security/tests on every commit)
pre-commit install

# Run the default simulation (1000 episodes, neurotypical preset)
python src/main.py

# Run a quick demo comparing all four clinical presets
python test_clinical_presets.py
```

## Running Simulations

### Programmatically

```python
from src.simulation import RPMEESimulation

sim = RPMEESimulation(preset='adhd_typical')  # 'neurotypical' | 'asd_typical' | 'adhd_typical' | 'mdd_typical'
sim.run(episodes=100)

print(sim.logs[-1])  # per-episode dict: clock, rt_mean, accuracy, precision_ratio, volatility, ...
```

`RPMEESimulation(use_vectorized_memory=True)` swaps in a NumPy+Numba-accelerated
memory store (`src/memory_vectorized.py`) for large memory sizes — same
results, better performance.

### Interactive dashboard (Streamlit)

```bash
pip install streamlit altair  # not in requirements-dev.txt
./app.sh                      # equivalent to: streamlit run app.py
```

Runs simulations from the browser, plots the resulting logs, and lets you
export or save runs to `saved_logs/`.

### Inspecting a preset

```python
from src.presets import get_preset, get_preset_summary, list_presets

list_presets()                        # ['neurotypical', 'asd_typical', 'adhd_typical', 'mdd_typical']
get_preset('adhd_typical')            # raw parameter dict (base_rt, wm_capacity, stress_baseline, ...)
get_preset_summary('adhd_typical')    # per-parameter {'value': ..., 'confidence': 'HIGH'|'MODERATE'|'LOW'}
```

## Clinical Presets (v1.1 — Preliminary Validation)

**Status:** Research models based on 24 peer-reviewed studies

Clinical population models for comparative simulation:

- **Neurotypical (NT)** — Baseline
- **ASD** — Sensory reactivity, attentional inflexibility
- **ADHD** — High variability, poor sustained attention
- **MDD** — Psychomotor slowing, anhedonia

**Parameter Confidence:**

- HIGH (15 params): Meta-analytic support (e.g., ADHD RT variability, MDD stress)
- MODERATE (32 params): Single studies or indirect evidence
- LOW (25 params): Theoretical estimates pending validation

**Appropriate Use:**
✅ Exploratory research, hypothesis generation, educational demos
❌ Clinical diagnosis, treatment decisions, individual predictions

See `docs/clinical_presets_v1.1.md` for complete documentation,
`literature_validation_analysis.md` for the evidence review behind each
parameter, and `docs/PARAMETER_SCALES.md` / `docs/SCALE_MAPPINGS.md` for how
literature measurements were converted into simulation-ready values.

## Validating Presets and Parameters

```bash
# Structural check: every preset has all required parameters, valid ranges
python scripts/validate_presets.py

# Face validation: do preset behaviors match the qualitative clinical
# pattern each is supposed to represent? (e.g. ADHD = high RT-CV)
python scripts/face_validation.py

# Literature-magnitude check: simulated effect sizes vs. expected magnitudes
# from the literature used to set the parameters (see caveat below)
python scripts/predictive_validation.py

# Which parameters most affect simulation outcomes (one-at-a-time sweep)
python scripts/sensitivity_analysis.py
```

`scripts/predictive_validation.py` is a **circular** check — it validates
against the same literature-derived expected magnitudes used to set the
parameters in the first place. See `PREDICTIVE_VALIDATION_PLAN.md` for why,
and the next section for the independent-data alternative.

## Empirical Validation Against Real Data

Work is underway to validate against independent real datasets instead of
literature-derived expectations, starting with
[ds003500](https://openneuro.org/datasets/ds003500) (OpenNeuro, CC0, no
data-use agreement required): response inhibition and selective attention
in ADHD and control participants. Tracked in GitHub issues #5–#13, #20–#23.

```bash
# 1. Download behavioral files only (no imaging) into data/ds003500/
python -c "
import openneuro
openneuro.download(
    dataset='ds003500', target_dir='data/ds003500',
    include=['participants.tsv', 'task-*.json', '**/*_events.tsv'],
)"

# 2. Confirm the actual column names before trusting the adapter
python scripts/inspect_ds003500_schema.py data/ds003500

# 3. Run each clinical preset's DDM against the real blocks
python scripts/validate_ds003500.py
```

This produces `results/validation/ds003500_validation_results.json` and
`ds003500_validation_report.md`: real vs. simulated RT/accuracy per task
family (Inh = response inhibition, Sel = visual-search load) and diagnostic
group, compared with a two-sample Kolmogorov-Smirnov test (not just mean
deviation — see issue #7) so differences in distribution shape/spread are
caught, not just differences in the mean.

See `src/adapters/ds003500.py`'s module docstring for important caveats
before extending this to other analyses:

- **Block-level, not trial-level.** ds003500's `events.tsv` rows are
  18-trial block aggregates; there's no way to recover single-trial
  RT/accuracy from this dataset.
- **Inh and Sel are never pooled** — they're different cognitive
  manipulations (inhibition vs. visual search) funneled through the same
  DDM inputs, and pooling them would be scientifically wrong.
- **Only ADHD/control are validated** — ds003500 has no ASD or MDD
  diagnostic labels (see issues #9, #10 for other datasets under
  consideration for those).

### DDM `load` vs. `difficulty`

`src/ddm.py`'s `DriftDiffusionModel.predict_action()` takes two separate
inputs that are easy to conflate but represent different cognitive
mechanisms, and produce **opposite** effects on reaction time:

- **`load`** — reduces the effective accuracy target, which shrinks the
  decision boundary, producing **faster, less accurate** responses. This is
  a speed-under-pressure / working-memory-interference account: rushing
  under load.
- **`difficulty`** — attenuates the drift rate directly, producing
  **slower, less accurate** responses. This is a stimulus/task-difficulty
  account: harder discriminations take longer to resolve, they aren't
  rushed.

The general rule: if a real task manipulation makes people *slower*, it
belongs on `difficulty`, not `load`. Getting this backwards inverted the
expected RT ordering during early ds003500 validation — see
[issue #6](https://github.com/cleveland-lewis/RPM-EE_Simulation/issues/6)
for the root cause and fix.

This is a deliberate, not yet fully resolved, area of active work — a
downstream accuracy-underestimation pattern (present even for the
neurotypical/control comparison, i.e. not ADHD-specific) is still open,
tracked in [issue #13](https://github.com/cleveland-lewis/RPM-EE_Simulation/issues/13),
with a related per-task-family calibration gap in
[issue #23](https://github.com/cleveland-lewis/RPM-EE_Simulation/issues/23).

## Testing

```bash
pytest                    # full suite (src/{ddm,bayesian_pe,td_learning,memory_vectorized}, integration)
pytest tests/test_ddm.py  # a single module
pytest -k "adhd"          # by keyword
```

Test files live in `tests/` (`pyproject.toml` sets `testpaths = ["tests"]`).
`test_clinical_presets.py` at the repo root is a runnable demo/comparison
script, not a pytest suite.

## Pre-commit Hooks

Code quality, security, and consistency enforced on every commit:

- Black/isort formatting, Ruff linting, mypy type checking
- Security scanning (bandit, detect-secrets)
- TODO prevention (use GitHub issues instead)
- Clinical preset / experiment-config / doc-reference validation
- `pytest` quick smoke tests

```bash
pip install pre-commit && pre-commit install

# Run all hooks manually, without committing
pre-commit run --all-files
```

See `docs/PRE_COMMIT_SETUP.md` for details. If a hook fails on a change
that's genuinely unrelated to what it's checking (e.g. a pre-existing
failure on a file you didn't touch), fix the root cause rather than
skipping the hook — `--no-verify` should be the exception, not the norm.

## Structure

```text
src/                    Simulation core
  simulation.py           RPMEESimulation — orchestrates one episode/step
  presets.py               CLINICAL_PRESETS + accessors (get_preset, list_presets, ...)
  ddm.py                    DriftDiffusionModel (EZ-diffusion + Euler-Maruyama)
  bayesian_pe.py            Bayesian predictive-error / precision weighting
  td_learning.py            TD-learning for emotional/reward encoding
  rpm.py                    RecursivePredictiveModeler (wraps DDM per event)
  emotion.py, selfmodel.py, memory.py, memory_vectorized.py,
  salience.py, sensory.py, replay.py, fatigue.py, arbiter.py, attunement.py
                             other subsystems (see module docstrings)
  adapters/                Real-dataset adapters for empirical validation
    base.py                  Trial dataclass + TaskAdapter protocol
    ds003500.py               OpenNeuro ds003500 (ADHD/control, Inh/Sel tasks)
  main.py                  CLI entry point (python src/main.py)

scripts/                Validation, literature-extraction, and dataset utilities
  validate_presets.py, face_validation.py, predictive_validation.py,
  sensitivity_analysis.py    preset/parameter validation (literature-relative)
  validate_ds003500.py, inspect_ds003500_schema.py
                             empirical validation against real data
  validate_experiment_config.py, check_doc_references.py
                             pre-commit hook backends
  paper_downloader.py, aggressive_downloader.py, paper_finder.py,
  extract_paper_data.py     literature-acquisition pipeline (see papers/, author_requests/)

tests/                  pytest suite (unit + integration)
docs/                   Parameter documentation, evidence tables, setup guides
data/                   Downloaded datasets (e.g. ds003500/) — not committed (see issue #12: not yet gitignored)
results/                Validation output (JSON + markdown reports)
app.py, app.sh          Streamlit dashboard
test_clinical_presets.py  Standalone demo/comparison script
.pre-commit-config.yaml  Hook configuration
pyproject.toml           Tool configuration (black, isort, ruff, mypy, pytest)
requirements-dev.txt      All dependencies (dev tooling + numpy/scipy/pandas/matplotlib)
```

## Development

```bash
# Run all hooks manually
pre-commit run --all-files

# Validate presets
python scripts/validate_presets.py

# Run tests
pytest
```

Work is tracked in [GitHub issues](https://github.com/cleveland-lewis/RPM-EE_Simulation/issues),
not TODO comments (a pre-commit hook enforces this). Longer-running
initiatives (e.g. the empirical-validation push, parameter confidence
upgrades) are broken into individual issues rather than tracked in a single
planning doc — check open issues for current priorities before starting new
work in an area covered by `PHASE*`, `VALIDATION_ACTION_PLAN.md`, or
`FOUR_PHASE_REMEDIATION_PLAN.md`, since those snapshot a point in time and
may be superseded by issue discussion.
