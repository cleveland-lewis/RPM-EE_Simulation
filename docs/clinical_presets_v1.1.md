# Clinical Presets Documentation

## Overview

RPM-EE v1.1 includes empirically-grounded clinical presets for simulating cognitive and behavioral patterns characteristic of different clinical populations. All parameters are based on **clinical observables only** - behavioral measures from peer-reviewed literature.

## Available Presets

### 1. Neurotypical (NT)
**Preset name:** `neurotypical`

Baseline profile representing typical cognitive function:
- **Response time:** ~500ms (simple tasks)
- **Accuracy:** ~90%
- **Working memory:** 7±2 items
- **Stress response:** Moderate reactivity, adaptive recovery
- **Attention:** Stable, flexible, goal-directed

**Use cases:**
- Control condition for clinical comparisons
- Baseline for intervention studies
- General population modeling

---

### 2. Autism Spectrum Disorder (ASD)
**Preset name:** `asd_typical`

Characterized by differences in sensory processing and attentional flexibility:
- **Response time:** 15% slower than NT
- **Sensory reactivity:** Heightened sensitivity
- **Attentional switching:** Reduced flexibility (25% higher switch cost)
- **Stress:** Elevated baseline (0.50 vs 0.30), slower recovery
- **Working memory:** Normal capacity, faster decay under manipulation

**Key features:**
- Good sustained attention but difficulty switching
- Heightened stress reactivity and prolonged recovery
- Comparable accuracy but higher variability
- Intact working memory span, impaired manipulation

**References:**
- Happé & Frith (2006) - Weak coherence account
- Robertson & Baron-Cohen (2017) - Sensory perception
- Yerys et al. (2009) - Set-shifting deficits
- Corbett et al. (2009) - Stress/cortisol elevation

---

### 3. Attention-Deficit/Hyperactivity Disorder (ADHD)
**Preset name:** `adhd_typical`

Characterized by high variability and poor sustained attention:
- **Response time variability:** 3x higher than NT (45% CV vs 15%)
- **Omission errors:** 2-3x higher
- **Working memory:** Reduced capacity (~4-5 items vs 7)
- **Sustained attention:** Poor (60% stability vs 85%)
- **Vigilance decrement:** Steep decline over time (2.5x faster)

**Key features:**
- Normal mean RT but extreme variability (intra-individual variability)
- High impulsivity and exploration (40% vs 20%)
- Difficulty sustaining attention over time
- High stress reactivity, impaired regulation
- Intact switching (low switch cost due to hyper-switching)

**References:**
- Kofler et al. (2013) - RT variability meta-analysis
- Kasper et al. (2012) - Working memory deficits
- Huang-Pollock et al. (2012) - Vigilance decrements
- Lackschewitz et al. (2008) - Stress dysregulation

---

### 4. Major Depressive Disorder (MDD)
**Preset name:** `mdd_typical`

Characterized by psychomotor slowing and anhedonia:
- **Response time:** 20% slower (psychomotor slowing)
- **Accuracy:** 8% reduction
- **Anhedonia:** Severely reduced positive affect (0.25 vs 0.60)
- **Stress:** Elevated baseline (0.55), very slow recovery
- **Cognitive control:** Impaired (higher switch cost, lower stability)
- **Exploration:** Markedly reduced (8% vs 20%)

**Key features:**
- Global psychomotor slowing
- Blunted positive affect (anhedonia) and reward sensitivity
- Elevated and persistent stress (HPA dysregulation)
- Impaired working memory especially under load
- Reduced exploration and learning from errors
- Higher vigilance decrement

**References:**
- Tsourtos et al. (2002) - Psychomotor slowing
- Treadway & Zald (2011) - Anhedonia
- Burke et al. (2005) - HPA dysregulation
- Snyder (2013) - Executive function impairments
- Nolen-Hoeksema (2000) - Rumination

---

## Usage

### Python API

```python
from src.simulation import RPMEESimulation

# Create simulation with clinical preset
sim = RPMEESimulation(preset='adhd_typical')

# Run simulation
sim.run(episodes=100)

# Access logs
for log in sim.logs:
    print(f"Stress: {log['schema_stress']}, Mode: {log['replay_mode']}")
```

### Command Line

```bash
# Test all presets
python test_clinical_presets.py

# Test specific preset
python test_clinical_presets.py --preset mdd_typical

# Run longer simulation
python test_clinical_presets.py --preset asd_typical --episodes 500
```

### Accessing Preset Parameters

```python
from src.presets import get_preset, list_presets, get_preset_description

# List available presets
presets = list_presets()
print(presets)  # ['adhd_typical', 'asd_typical', 'mdd_typical', 'neurotypical']

# Get preset parameters
params = get_preset('adhd_typical')
print(params['wm_capacity'])  # 4.5
print(params['rt_variability'])  # 0.45

# Get description
desc = get_preset_description('adhd_typical')
print(desc)
```

---

## Parameter Descriptions

### Response Time Parameters
- **base_rt** (ms): Baseline response time for simple tasks
- **rt_variability** (CV): Coefficient of variation (SD/mean)
- **rt_slowing** (multiplier): Overall slowing factor

### Accuracy Parameters
- **base_accuracy** (0-1): Baseline accuracy in unloaded conditions
- **accuracy_decline** (0-1): Performance decline under cognitive load

### Working Memory
- **wm_capacity** (items): Number of items that can be held
- **wm_decay_rate** (per-tick): Rate of memory decay

### Attention/Executive Function
- **attention_stability** (0-1): Sustained attention capacity
- **switch_cost** (0-1): Cost of switching attention between tasks
- **vigilance_decrement** (per-tick): Rate of vigilance decline over time

### Stress and Regulation
- **stress_baseline** (0-1): Resting stress level
- **stress_reactivity** (0-1): Sensitivity to stressors
- **stress_recovery** (0-1): Rate of stress reduction (higher = faster)

### Emotional/Motivational
- **positive_affect** (0-1): Baseline positive emotional state
- **negative_affect** (0-1): Baseline negative emotional state
- **reward_sensitivity** (0-1): Responsiveness to rewards

### Prediction/Learning
- **prediction_error_gain** (multiplier): Learning rate from errors
- **exploration_rate** (0-1): Tendency for exploratory behavior

---

## Validation

### Expected Behavioral Patterns

**Stress Dynamics:**
- NT: Moderate baseline (~0.30), good recovery
- ASD: Elevated baseline (~0.50), slow recovery
- ADHD: Moderate baseline, high reactivity, moderate recovery
- MDD: High baseline (~0.55), very slow recovery

**Vigilance/Attention:**
- NT: Stable (~0.85), minimal decrement
- ASD: Stable but inflexible (high switch cost)
- ADHD: Poor initial (~0.60), steep decrement
- MDD: Moderate initial (~0.65), moderate decrement

**Working Memory Load:**
- NT: Capacity 7, low decay
- ASD: Capacity 7, moderate decay
- ADHD: Capacity 4.5, high decay
- MDD: Capacity 5.5, high decay

### Running Validation Tests

```bash
python test_clinical_presets.py
```

Expected output includes:
- Stress level comparisons
- Vigilance/attention metrics
- Attunement scores
- Working memory patterns

---

## Implementation Notes

### What is Modeled
✅ **Clinical observables:**
- Response time distributions
- Accuracy patterns
- Working memory capacity
- Attention/executive function
- Stress reactivity and recovery
- Behavioral variability

### What is NOT Modeled
❌ **Not included:**
- Brain imaging data (fMRI, EEG)
- Neurotransmitter levels
- Genetic factors
- Medication effects
- Comorbidities
- Developmental trajectories

These can be added in future versions but are excluded from v1.1 to maintain focus on **behavioral/clinical measures only**.

---

## Literature Support

All parameters are grounded in peer-reviewed literature. See `src/presets.py` for complete references (25 citations).

### Key Meta-Analyses Used:
- **ADHD RT variability:** Kofler et al. (2013) - meta-analysis of 319 studies
- **MDD cortisol:** Burke et al. (2005) - meta-analysis of 361 studies
- **MDD executive function:** Snyder (2013) - comprehensive review

---

## Future Extensions (v1.2+)

Planned enhancements:
1. **Medication effects**: Modifiers for SSRI, stimulants, etc.
2. **Comorbidity presets**: ASD+ADHD, MDD+Anxiety, etc.
3. **Individual differences**: Within-group variability
4. **Developmental trajectories**: Age-dependent parameters
5. **Trial-level RT generation**: Ex-Gaussian distributions
6. **Learning/adaptation**: Cross-trial effects

---

## Contributing

To add new presets or modify existing ones:

1. Edit `src/presets.py`
2. Add empirical justification with references
3. Update this documentation
4. Run validation tests
5. Submit pull request

**Requirements for new presets:**
- Must be based on published clinical/behavioral data
- No neuroimaging or biomarker data
- Include at least 3 peer-reviewed references
- Provide parameter justification

---

## Citation

If you use these clinical presets in research, please cite:

```
RPM-EE Clinical Presets v1.1 (2026)
Empirically-grounded clinical population parameters
Based on 25 peer-reviewed behavioral studies
```

---

## Contact

For questions or issues with clinical presets:
- Open an issue on GitHub
- See `docs/clinical_presets_v1.1.md` for additional documentation
- Review references in `src/presets.py`
