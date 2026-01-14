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
