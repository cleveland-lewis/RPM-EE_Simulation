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

## Clinical Presets

Empirically-grounded models for 4 populations (based on 25 peer-reviewed studies):
- **Neurotypical (NT)** - Baseline
- **ASD** - Sensory reactivity, attentional inflexibility  
- **ADHD** - High variability, poor sustained attention
- **MDD** - Psychomotor slowing, anhedonia

```python
from src.simulation import RPMEESimulation

sim = RPMEESimulation(preset='adhd_typical')
sim.run(episodes=100)
```

See `docs/clinical_presets_v1.1.md` for details.

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
