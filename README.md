# RPM-EE v1.1.0 Simulation

Recursive Predictive Modeling with Emotional Encoding (RPM-EE) simulation architecture.

## Quick Start

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run simulation
python src/main.py

# Test clinical presets
python test_clinical_presets.py
```

## Clinical Presets (v1.1 - Preliminary Validation)

**Status:** Research models based on 24 peer-reviewed studies

Clinical population models for comparative simulation:
- **Neurotypical (NT)** - Baseline
- **ASD** - Sensory reactivity, attentional inflexibility  
- **ADHD** - High variability, poor sustained attention
- **MDD** - Psychomotor slowing, anhedonia

**Parameter Confidence:**
- HIGH (15 params): Meta-analytic support (e.g., ADHD RT variability, MDD stress)
- MODERATE (32 params): Single studies or indirect evidence
- LOW (25 params): Theoretical estimates pending validation

**Appropriate Use:**
✅ Exploratory research, hypothesis generation, educational demos  
❌ Clinical diagnosis, treatment decisions, individual predictions

```python
from src.simulation import RPMEESimulation

sim = RPMEESimulation(preset='adhd_typical')
sim.run(episodes=100)

# Check parameter confidence
from src.presets import get_preset_summary
summary = get_preset_summary('adhd_typical')
print(f"WM capacity: {summary['wm_capacity']}")  # {'value': 3.0, 'confidence': 'HIGH'}
```

See `docs/clinical_presets_v1.1.md` for complete documentation and
`literature_validation_analysis.md` for evidence review.

## Empirical Validation Against Real Data

Clinical presets were originally validated only against literature-derived
*expected magnitudes* (see `PREDICTIVE_VALIDATION_PLAN.md`) — a circular
check, since that's the same literature used to set the parameters. Work is
underway to validate against independent real datasets instead, starting
with [ds003500](https://openneuro.org/datasets/ds003500) (OpenNeuro, CC0,
no data-use agreement required): response inhibition and selective
attention in ADHD and control participants. See `src/adapters/` for the
dataset adapter and `scripts/validate_ds003500.py` for the comparison
harness. Tracked in GitHub issues #5–#13.

### DDM `load` vs. `difficulty`

`src/ddm.py`'s `DriftDiffusionModel.predict_action()` takes two separate
inputs that are easy to conflate but represent different cognitive
mechanisms, and produce **opposite** effects on reaction time:

- **`load`** (existing) — reduces the effective accuracy target, which
  shrinks the decision boundary, producing **faster, less accurate**
  responses. This is a speed-under-pressure / working-memory-interference
  account: rushing under load.
- **`difficulty`** (added while investigating
  [issue #6](https://github.com/cleveland-lewis/RPM-EE_Simulation/issues/6))
  — attenuates the drift rate directly, producing **slower, less
  accurate** responses. This is a stimulus/task-difficulty account:
  harder discriminations take longer to resolve, they aren't rushed.

Early empirical validation against ds003500 mapped "harder task condition"
(no-go blocks, array/visual-search blocks) onto `load`, which inverted the
expected RT ordering — the `adhd_typical` preset predicted **faster**
responses on the harder condition than the easier one, the opposite of
every real participant in the dataset. Root cause and fix are documented
in issue #6. The general rule going forward: if a real task manipulation
makes people *slower*, it belongs on `difficulty`, not `load`.

This is a deliberate, not yet fully resolved, area of active work — a
downstream accuracy-underestimation pattern (present even for the
neurotypical/control comparison, i.e. not ADHD-specific) is still open,
tracked in [issue #13](https://github.com/cleveland-lewis/RPM-EE_Simulation/issues/13).

## Pre-commit Hooks

Code quality, security, and consistency enforced on every commit:
- Black/isort formatting, Ruff linting, mypy type checking
- Security scanning (bandit, detect-secrets)
- TODO prevention (use GitHub issues instead)
- Clinical preset validation

```bash
pip install pre-commit && pre-commit install
```

See `docs/PRE_COMMIT_SETUP.md` for details.

## Structure

- `src/` - Simulation code (presets, memory, RPM, emotion, etc.)
- `test_clinical_presets.py` - Validation script
- `scripts/` - Validation utilities
- `docs/` - Documentation
- `.pre-commit-config.yaml` - Hook configuration
- `pyproject.toml` - Tool configuration

## Development

```bash
# Run all hooks manually
pre-commit run --all-files

# Validate presets
python scripts/validate_presets.py

# Run tests
pytest
```
