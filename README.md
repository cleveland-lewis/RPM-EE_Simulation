# RPM-EE v1.1.0 Simulation

This directory contains the skeleton code for the Recursive Predictive Modeling with Emotional Encoding (RPM-EE) simulation architecture.

## ✨ New in v1.1: Clinical Presets

**Empirically-grounded clinical population models** based on 25 peer-reviewed studies. Simulate cognitive and behavioral patterns for:
- **Neurotypical (NT)** - Baseline control
- **Autism Spectrum Disorder (ASD)** - Sensory reactivity, attentional inflexibility
- **ADHD** - High variability, poor sustained attention
- **Major Depressive Disorder (MDD)** - Psychomotor slowing, anhedonia

### Quick Start with Clinical Presets

```python
from src.simulation import RPMEESimulation

# Run simulation with ADHD preset
sim = RPMEESimulation(preset='adhd_typical')
sim.run(episodes=100)

# Access metrics
print(f"Mean stress: {sim.logs[-1]['schema_stress']}")
```

### Test All Presets

```bash
# Compare all clinical presets
python test_clinical_presets.py

# Test specific preset
python test_clinical_presets.py --preset adhd_typical --episodes 200
```

See `docs/clinical_presets_v1.1.md` for full documentation.

## Structure

- `src/` - Python source code for the simulation
  - `presets.py` - Clinical preset definitions (NEW in v1.1)
  - `simulation.py` - Main simulation loop with preset support
  - `memory.py` - Working memory with clinical parameters
- `test_clinical_presets.py` - Validation and comparison script
- `config/` - YAML configuration for logging
- `logs/` - Output folder for logs and data
- `docs/` - Model architecture, clinical presets documentation

## How to Run

```bash
python src/main.py
```

## Next Steps

Implement subsystems in `simulation.py`:
- [ ] Sensory input 
- [ ]Tagging + prioritization
- [ ] Pattern matching
- [ ] Recursive simulation
- [ ] Emotional encoding 
- [ ] Replay mode arbitration
- [ ] Action decision
- [ ] Logging + visualization
