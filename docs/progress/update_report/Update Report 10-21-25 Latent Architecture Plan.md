# Latent/Bounded Architecture Implementation Plan (2025-10-21)

## Status: PARTIAL - Preset Configured, Core Implementation Pending

## Objective

Adopt latent → bounded mapping for attunement/stress to:
- Allow internal dynamics to exceed [0,1] in latent space
- Apply configurable link functions (sigmoid with gain/offset) to map to [0,1]
- Enable calibration to achieve ~0.55-0.65 mean bounded attunement
- Maintain theoretical grounding while escaping sigmoid saturation

## Completed

### 1. Preset Configuration ✅
**File**: `src/presets.py` (lines 539-608)

Added `default_v2_calibrated` preset with full latent/bounded architecture parameters:

```python
# Latent space parameters
'theta0': 1.20,           # latent baseline (can be >1)
'theta_s_mult': 0.60,     # stress penalty multiplier
'stress_decay': 0.05,     # decay in latent space

# Link function parameters (NEW)
'att_gain': 2.0,          # attunement sigmoid slope
'att_offset': 1.0,        # attunement sigmoid center
'att_scale': 1.0,         # output scaling (1.0 = keep [0,1])
'stress_gain': 2.0,       # stress sigmoid slope
'stress_offset': 0.0,     # stress sigmoid center

# Latent thresholds
'att_gate_latent': 1.0,   # threshold for action gating in latent space
```

## Pending Implementation

### 2. Core Simulation Changes 🔄

**File**: `src/simulation.py`

**Required modifications**:

#### A. Add link function parameters to function signature (line ~273)
```python
def run_simulation(
    # ... existing params ...
    # --- Link function parameters ---
    att_gain: float = 2.0,
    att_offset: float = 1.0,
    att_scale: float = 1.0,
    stress_gain: float = 2.0,
    stress_offset: float = 0.0,
    att_gate_latent: float = 1.0,
    # ...
):
```

#### B. Initialize latent state variables (after line ~125)
```python
stress_latent = 0.0      # latent stress (can be >1)
att_latent = 0.0         # latent attunement (can be >1)
```

#### C. Load link function params from preset (after line ~226)
```python
if cfg:
    # ... existing preset loading ...
    att_gain = cfg.get('att_gain', att_gain)
    att_offset = cfg.get('att_offset', att_offset)
    att_scale = cfg.get('att_scale', att_scale)
    stress_gain = cfg.get('stress_gain', stress_gain)
    stress_offset = cfg.get('stress_offset', stress_offset)
    att_gate_latent = cfg.get('att_gate_latent', att_gate_latent)
```

#### D. Modify stress computation (line ~732-737)
**Current**:
```python
s_next = (1.0 - kappa) * s_drive + kappa * s_fast

# Apply optional stress decay
if stress_decay > 0.0:
    s_next = max(0.0, s_next * (1.0 - stress_decay))

stress_prev = s_next
schema_stress[i] = float(s_next)
```

**Proposed**:
```python
# Compute latent stress (unbounded)
stress_latent = (1.0 - kappa) * s_drive + kappa * s_fast

# Apply decay in latent space
if stress_decay > 0.0:
    stress_latent = stress_latent * (1.0 - stress_decay)

# Numerical guard for latent values
stress_latent = float(np.clip(stress_latent, -20.0, 20.0))

# Link function: latent → [0,1]
stress_bounded = 1.0 / (1.0 + np.exp(-stress_gain * (stress_latent - stress_offset)))

# Update state
stress_prev = stress_latent  # Continue tracking latent for next iteration
schema_stress[i] = float(stress_bounded)
```

#### E. Modify attunement computation (line ~506-516)
**Current**:
```python
z = (
    theta0
    + theta_a * (pi_aff * aff)
    - (theta_s * theta_s_mult) * (pi_str * s_term)
    - (theta_e * theta_e_mult) * (pi_ext * ext_term)
    - (theta_m * theta_m_mult) * (pi_mem * mem_term)
    - (theta_v * theta_v_mult) * (pi_vol * vol_term)
)
A_hat = 1.0 / (1.0 + np.exp(-z))
A = float(np.clip(A_hat, 0.0, 1.0))
attunement_scores[i] = A
```

**Proposed**:
```python
# Compute latent attunement (unbounded)
att_latent = (
    theta0
    + theta_a * (pi_aff * aff)
    - (theta_s * theta_s_mult) * (pi_str * s_term)
    - (theta_e * theta_e_mult) * (pi_ext * ext_term)
    - (theta_m * theta_m_mult) * (pi_mem * mem_term)
    - (theta_v * theta_v_mult) * (pi_vol * vol_term)
)

# Numerical guard
att_latent = float(np.clip(att_latent, -20.0, 20.0))

# Link function: latent → [0,1]
att_bounded = 1.0 / (1.0 + np.exp(-att_gain * (att_latent - att_offset)))

# Optional scaling (default 1.0 keeps in [0,1])
att_scaled = att_scale * att_bounded

attunement_scores[i] = float(att_bounded)
```

#### F. Update action gating to use latent threshold (line ~526-532)
**Current**:
```python
if gate_by_attunement:
    p_act = 1.0 / (1.0 + np.exp(-(z / max(1e-6, float(gate_temperature)))))
    action_executed = (not early_dismissal) and (np.random.rand() < p_act)
```

**Proposed**:
```python
if gate_by_attunement:
    # Option 1: Use latent threshold
    if att_latent > att_gate_latent:
        p_act = 1.0 / (1.0 + np.exp(-(att_latent / max(1e-6, float(gate_temperature)))))
        action_executed = (not early_dismissal) and (np.random.rand() < p_act)
    else:
        action_executed = False

    # Option 2: Use bounded value directly
    # p_act = att_bounded
    # action_executed = (not early_dismissal) and (np.random.rand() < p_act)
```

#### G. Update logging to include latent values (line ~576-607)
Add to log entry:
```python
logs.append({
    # ... existing fields ...
    'att_latent': float(att_latent),          # NEW
    'stress_latent': float(stress_latent),    # NEW
    'att_bounded': float(att_bounded),         # NEW (redundant with attunement_score but clear)
    'stress_bounded': float(stress_bounded),   # NEW (redundant with schema_stress but clear)
    # ...
})
```

#### H. Add link function params to diagnostics (line ~688-710)
```python
'knobs': {
    # ... existing knobs ...
    'att_gain': float(att_gain),
    'att_offset': float(att_offset),
    'att_scale': float(att_scale),
    'stress_gain': float(stress_gain),
    'stress_offset': float(stress_offset),
    'att_gate_latent': float(att_gate_latent),
}
```

### 3. Batch Runner Updates 🔄

**File**: `config/batch_runner.py`

No changes needed - batch runner already uses bounded values from logs.

### 4. Stats Utils Updates 🔄

**File**: `src/stats_utils.py`

No changes needed - operates on bounded values.

### 5. Testing 🔄

**File**: `config/tests/test_links.py` (NEW)

```python
import numpy as np
import pytest

def test_att_link_function():
    """Test that attunement link function is monotonic and bounded."""
    att_gain = 2.0
    att_offset = 1.0

    z = np.linspace(-6, 6, 1000)
    a = 1.0 / (1.0 + np.exp(-att_gain * (z - att_offset)))

    # Check bounds
    assert np.all(a >= 0.0) and np.all(a <= 1.0), "Attunement must be in [0,1]"

    # Check monotonicity
    assert np.all(np.diff(a) > 0), "Attunement must be monotonically increasing"

    # Check center point
    a_at_offset = 1.0 / (1.0 + np.exp(-att_gain * (att_offset - att_offset)))
    assert np.isclose(a_at_offset, 0.5), "Sigmoid should be 0.5 at offset"

def test_stress_link_function():
    """Test that stress link function is monotonic and bounded."""
    stress_gain = 2.0
    stress_offset = 0.0

    z = np.linspace(-6, 6, 1000)
    s = 1.0 / (1.0 + np.exp(-stress_gain * (z - stress_offset)))

    assert np.all(s >= 0.0) and np.all(s <= 1.0), "Stress must be in [0,1]"
    assert np.all(np.diff(s) > 0), "Stress must be monotonically increasing"

def test_stress_decay_latent():
    """Test that stress decay operates in latent space."""
    stress_latent = 2.0  # Above bounded range
    stress_decay = 0.05

    # After decay
    stress_after = stress_latent * (1.0 - stress_decay)
    assert stress_after == 1.9, "Decay should operate on latent value"

    # Bounded value should still be valid
    stress_bounded = 1.0 / (1.0 + np.exp(-2.0 * stress_after))
    assert 0.0 <= stress_bounded <= 1.0, "Bounded stress must be in [0,1]"
```

### 6. Documentation 🔄

**File**: `docs/THEORY.md` (NEW)

```markdown
# Latent/Bounded Architecture Theory

## Overview

RPM-EE v2 adopts a **latent/bounded** architecture where:
- **Latent variables** operate in unbounded R space (can exceed [0,1])
- **Link functions** map latent → [0,1] bounded space
- **Outputs/APIs** expose bounded values
- **Diagnostics** log both latent and bounded

## Motivation

**Problem**: Sigmoid saturation
- Previous architecture: z (linear combo) → sigmoid(z) → always [0,1]
- Issue: Hard to achieve moderate engagement (~0.6) without extreme parameter tuning
- Penalties quickly saturate sigmoid, collapsing attunement to near-zero

**Solution**: Separate latent and bounded spaces
- Latent space allows flexible dynamics (stress can be 2.0, attunement 1.5, etc.)
- Link functions provide smooth, interpretable mapping to [0,1]
- Tunable gain/offset allows calibration without breaking model structure

## Architecture

### Attunement

```
latent_att = θ₀ + Σ(w_i * x_i)     [can be >1, in R]
            ↓ link function
bounded_att = σ(gain * (latent - offset))    [in [0,1]]
```

**Parameters**:
- `att_gain`: Sigmoid slope (higher = steeper transition)
- `att_offset`: Sigmoid center (shifts curve left/right)
- `att_scale`: Optional output scaling (default 1.0)

**Example**:
- latent_att = 1.2, gain = 2.0, offset = 1.0
- bounded_att = σ(2.0 * (1.2 - 1.0)) = σ(0.4) ≈ 0.599

### Stress

```
latent_stress = blend(drive, surprisal)    [can be >1]
              ↓ decay (in latent space)
latent_stress *= (1 - decay_rate)
              ↓ link function
bounded_stress = σ(gain * (latent - offset))    [in [0,1]]
```

**Key insight**: Decay operates on latent values before bounding
- Allows stress to naturally return to baseline
- Prevents chronic elevation from sigmoid saturation

## Usage in Code

### Thresholds
- Use **latent values** for fixed thresholds:
  ```python
  if att_latent > att_gate_latent:  # e.g., 1.0
      enable_action()
  ```

### Probabilities
- Use **bounded values** for stochastic policies:
  ```python
  p_act = att_bounded  # Already in [0,1]
  if random() < p_act:
      execute_action()
  ```

### Penalties/Couplings
- Compute in **latent space**:
  ```python
  att_latent = baseline - penalty_mult * stress_latent
  ```

## Calibration Heuristic

Target: bounded_att_mean ≈ 0.60

**Step 1**: Set offset to latent baseline
```python
att_offset = theta0  # e.g., 1.2
```

**Step 2**: Choose gain from desired slope
```python
# Max slope of sigmoid ≈ gain/4 at midpoint
# For slope ≈ 0.45 → gain ≈ 1.8-2.0
att_gain = 2.0
```

**Step 3**: Verify empirically
```python
# Run simulation and check: mean(bounded_att) ≈ 0.60
# Adjust offset ±0.1 to tune mean
# Adjust gain to tune spread/responsiveness
```

## Acceptance Criteria

With calibrated preset:
- [ ] mean(att_bounded) in 0.55–0.65
- [ ] percentile(att_bounded, 95) ≥ 0.75
- [ ] percentile(att_bounded, 5) ≤ 0.35
- [ ] mean(stress_bounded) ≤ 0.58
- [ ] corr(att_bounded, action_executed) > 0.30
- [ ] std(att_bounded) > 0.15 (not collapsed)
- [ ] distribution_summary.json contains nontrivial percentiles

## References

- Link functions: McElreath (2020) Statistical Rethinking Ch. 10
- Latent variable models: Bishop (2006) Pattern Recognition Ch. 12
- Predictive coding with precision: Friston et al. (2012) Nature Reviews Neuroscience
```

## Implementation Checklist

- [x] Configure preset with link function parameters
- [ ] Add parameters to simulation.py function signature
- [ ] Initialize latent state variables
- [ ] Load link function params from preset
- [ ] Modify stress computation (latent + link)
- [ ] Modify attunement computation (latent + link)
- [ ] Update action gating to use latent threshold
- [ ] Add latent values to logging
- [ ] Add link params to diagnostics
- [ ] Create test file for link functions
- [ ] Write THEORY.md documentation
- [ ] Run validation batch (5 runs × 5000 ticks)
- [ ] Validate against acceptance criteria
- [ ] Update main documentation (README, CLAUDE.md)

## Estimated Effort

- Core implementation: 2-3 hours
- Testing: 1 hour
- Documentation: 1 hour
- Validation: 30 minutes
- **Total**: 4-5 hours

## Notes

- This is a **non-breaking change** for existing presets (they continue to work with identity link)
- Link functions are mathematically equivalent to previous sigmoid when gain=1, offset=0
- Provides path to future enhancements (e.g., softplus, inverse-probit links)
- Enables principled calibration without parameter explosion

---

**Status**: Ready for implementation
**Next step**: Implement changes in simulation.py following sections 2A-2H above
**Contact**: See main repo docs for questions
