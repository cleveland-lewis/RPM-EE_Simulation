# RPM-EE Validation Infrastructure: Implementation Status

**Last Updated:** 2025-10-27
**Version:** 1.0.0

---

## Summary

This document tracks the implementation status of code-level changes required for empirical validation of the RPM-EE framework. All blocking changes have been specified, and 3 of 7 are now implemented and tested.

---

## Blocking Changes for Validation

### ✅ 1. Real-Data Adapters (COMPLETED)

**Status:** Fully implemented and tested

**Implementation:** `src/adapters.py`

**Features:**
- ✅ `EmpiricalDataAdapter`: Main CSV/pandas loader
  - Time alignment and resampling (configurable tick rate: '1s', '100ms', etc.)
  - Automatic unit normalization (stress 0-10 → 0-1, affect -3/+3 → -1/+1, etc.)
  - Missing data interpolation (linear, max gap = 5 ticks)
  - Precomputed series for fast tick-level access
  - Protocol-compliant interface (`get_affect_feedback()`, `get_stress_rating()`, etc.)

- ✅ Prediction error observers:
  - `EMAObserver`: Delta-rule (exponential moving average)
  - `KalmanObserver`: Bayesian Gaussian filter with process/observation noise

- ✅ Helper utilities:
  - `align_model_to_empirical()`: Timestamp-based merging
  - `compute_memory_load_from_nback()`: Infer WM load from task performance

**Example:**
```python
from src.adapters import EmpiricalDataAdapter

adapter = EmpiricalDataAdapter.from_csv(
    "participant_001.csv",
    tick_rate='1s',
    interpolate_missing=True
)

# Access at any tick
affect = adapter.get_affect_feedback(tick=100)
stress = adapter.get_stress_rating(tick=100)
ext_load = adapter.get_external_load(tick=100)  # {vision, hearing, touch}
```

**Remaining:**
- Integration with `run_simulation()` (see #2 below)

---

### ⏳ 2. Observation-Conditioned Mode (NOT YET IMPLEMENTED)

**Status:** Specified, awaiting implementation in `simulation.py`

**Required Changes:**

1. **Add parameter to `run_simulation()`**:
   ```python
   def run_simulation(
       ...,
       data_adapter: DataAdapter | None = None,
       observed_mode: int = 0,  # 0=synthetic, 1=observed
       ...
   ):
   ```

2. **Replace input generation** when `data_adapter` is provided:
   ```python
   if data_adapter is not None and observed_mode == 1:
       total_ticks = data_adapter.get_total_ticks()

       # Replace _generate_base_arrays() with adapter calls
       for i in range(total_ticks):
           avg_affect_feedback[i] = data_adapter.get_affect_feedback(i)

           # External load from observed modalities
           ext_load_dict = data_adapter.get_external_load(i)
           # Compute precision-weighted integration (existing code)

           # Memory load from observed N-back (if available)
           mem_load_obs = data_adapter.get_memory_load(i)
           if mem_load_obs is not None:
               mem_load = mem_load_obs  # Use observed instead of computed
           else:
               # Fall back to model's internal calculation
               mem_load = min(1.0, short_term_size / mem_capacity) ** mem_gamma
   ```

3. **Use learnable PE observer**:
   ```python
   if observed_mode == 1:
       # Initialize observer (EMA or Kalman)
       pe_observer = EMAObserver(learning_rate=0.1)

       for i in range(total_ticks):
           # Compute PE from observed external load
           prediction_error = pe_observer.update(ext_load)
   ```

4. **Observed action execution** (for validation only):
   ```python
   if observed_mode == 1:
       action_executed_obs = data_adapter.get_action_executed(i)
       if action_executed_obs is not None:
           # Log observed action (for validation)
           logs[i]['action_executed_observed'] = action_executed_obs
           # Model still predicts (for H3a validation)
           logs[i]['action_executed_predicted'] = action_executed
   ```

**Priority:** HIGH (blocking for Study 1 validation)

**Estimated Effort:** 2-4 hours (modify simulation.py, test with example adapter)

---

### ✅ 3. Endpoint Calculator (COMPLETED)

**Status:** Fully implemented and tested

**Implementation:** `src/validation_metrics.py`

**Features:**
- ✅ All preregistered hypotheses (H1-H5):
  - H1a/b: Convergent validity (stress, HRV)
  - H2a: Memory load prediction
  - H3a/b: Attunement → action execution (ROC/AUC), confidence correlation
  - H4a/b: Discriminant validity (trait independence, ICC)
  - H5a/b: Predictive validity (cross-validated regression, lagged omission)

- ✅ Statistical utilities:
  - Within-subject correlations (Fisher z-transform)
  - ROC analysis (per-participant + global)
  - ICC calculation (one-way random effects)
  - 10-fold cross-validation
  - Calibration plots (Expected Calibration Error)

- ✅ Master function:
  ```python
  from src.validation_metrics import compute_all_endpoints

  results = compute_all_endpoints(
      merged_df=aligned_data,
      trial_df=trial_data,
      block_df=block_data,
      participant_df=participant_data
  )

  # Automatic success/fail against preregistered thresholds
  print(f"Success rate: {results['summary']['success_rate']:.1%}")
  ```

**Example Output:**
```
H1a (Stress Convergence): r=0.441, p=0.000 ✓ PASS
H3a (Action AUC): AUC=0.652 ✗ FAIL
H4b (ICC): ICC=0.021 ✓ PASS
Overall Success Rate: 50.0% (4/8)
```

---

### ⏳ 4. Provenance & Schema (NOT YET IMPLEMENTED)

**Status:** Specified, awaiting implementation

**Required Changes:**

1. **Add schema version to outputs**:
   ```python
   # In run_simulation(), extend return dict
   return {
       'schema_version': '2.0.0',
       'provenance': {
           'timestamp': datetime.now().isoformat(),
           'git_commit': _get_git_commit_hash(),
           'preset': preset,
           'seed': seed,
           'parameters': {
               'theta0': theta0,
               'theta_s_mult': theta_s_mult,
               # ... all parameters
           },
       },
       'logs': logs,
       'stats': stats,
       'diagnostics': diagnostics,
   }
   ```

2. **Atomic file writes with locks**:
   ```python
   from filelock import FileLock
   import json

   def save_simulation_atomic(result: dict, output_path: Path):
       """Save simulation result with file locking."""
       lock_path = output_path.with_suffix('.lock')

       with FileLock(str(lock_path), timeout=10):
           # Write to temporary file first
           temp_path = output_path.with_suffix('.tmp')
           with open(temp_path, 'w') as f:
               json.dump(result, f, indent=2)

           # Atomic rename
           temp_path.replace(output_path)
   ```

3. **Git commit tracking**:
   ```python
   import subprocess

   def _get_git_commit_hash() -> str:
       """Get current git commit hash."""
       try:
           return subprocess.check_output(
               ['git', 'rev-parse', 'HEAD'],
               cwd=Path(__file__).parent
           ).decode('utf-8').strip()
       except Exception:
           return 'unknown'
   ```

**Priority:** MEDIUM (important for reproducibility, not blocking for pilot)

**Estimated Effort:** 2-3 hours

---

### ⏳ 5. Normalization Freeze (NOT YET IMPLEMENTED)

**Status:** Specified, awaiting implementation

**Required Changes:**

1. **Add freeze parameter**:
   ```python
   def run_simulation(
       ...,
       freeze_normalization: bool = False,
       normalization_stats: dict | None = None,  # Pre-computed μ/σ from train set
       ...
   ):
   ```

2. **Conditional normalization**:
   ```python
   if freeze_normalization and normalization_stats is not None:
       # Use frozen stats from train set
       ema_stress = normalization_stats['stress_mean']
       var_stress = normalization_stats['stress_var']
       # Don't update during simulation
   else:
       # Online normalization (current behavior)
       ema_stress += 0.05 * ds
       var_stress = (1.0 - 0.05) * var_stress + 0.05 * (ds * ds)
   ```

3. **Export normalization stats**:
   ```python
   # In diagnostics, add:
   'normalization_stats': {
       'stress_mean': float(ema_stress),
       'stress_var': float(var_stress),
       'ext_load_mean': float(ema_ext),
       'ext_load_var': float(var_ext),
       # ... all online statistics
   }
   ```

4. **Train/test workflow**:
   ```python
   # Train on 70% of participants
   train_results = []
   for participant in train_set:
       result = run_simulation(data_adapter=participant, observed_mode=1)
       train_results.append(result)

   # Compute pooled normalization stats
   pooled_stats = aggregate_normalization_stats(train_results)

   # Test on 30% (frozen normalization)
   for participant in test_set:
       result = run_simulation(
           data_adapter=participant,
           observed_mode=1,
           freeze_normalization=True,
           normalization_stats=pooled_stats
       )
   ```

**Priority:** MEDIUM-HIGH (essential for H5a out-of-sample validation)

**Estimated Effort:** 3-4 hours

---

### ⏳ 6. Parameter Identifiability (NOT YET IMPLEMENTED)

**Status:** Specified, awaiting implementation

**Required Changes:**

1. **Create unit tests** (`tests/test_identifiability.py`):
   ```python
   import pytest
   import numpy as np
   from src.simulation import run_simulation

   def test_theta_s_mult_monotonicity():
       """Test: Increasing theta_s_mult increases stress penalty on attunement."""
       base_params = {'total_ticks': 1000, 'seed': 42}

       results = []
       for mult in [0.5, 0.65, 0.80, 1.0]:
           result = run_simulation(**base_params, theta_s_mult=mult)
           mean_att = result['stats']['mean_attunement']
           results.append((mult, mean_att))

       # Check monotonicity: higher mult → lower attunement
       multipliers, attunements = zip(*results)
       for i in range(len(attunements) - 1):
           assert attunements[i] >= attunements[i+1], \
               f"Non-monotonic: theta_s_mult={multipliers[i]} → att={attunements[i]}, " \
               f"theta_s_mult={multipliers[i+1]} → att={attunements[i+1]}"

   def test_mem_load_penalty():
       """Test: Increasing mem_load decreases attunement."""
       # Use observation-conditioned mode with controlled mem_load
       # ... (similar to above)
       pass

   def test_stress_decay_effect():
       """Test: Increasing stress_decay decreases mean stress."""
       # ... (similar to above)
       pass
   ```

2. **Run tests**:
   ```bash
   pytest tests/test_identifiability.py -v
   ```

**Priority:** MEDIUM (important for calibration quality, not blocking for descriptive validation)

**Estimated Effort:** 2-3 hours

---

### ⏳ 7. Gating Policy Alignment (NOT YET IMPLEMENTED)

**Status:** Specified, awaiting implementation

**Required Changes:**

1. **Separate observed vs. predicted action**:
   ```python
   # In observation-conditioned mode
   if observed_mode == 1:
       # Get observed action from data
       action_executed_observed = data_adapter.get_action_executed(i)

       # Model prediction (for validation, not to constrain simulation)
       if gate_by_attunement:
           p_act = 1.0 / (1.0 + np.exp(-(att_latent / gate_temperature)))
           action_executed_predicted = (not early_dismissal) and (np.random.rand() < p_act)
       else:
           action_executed_predicted = (not early_dismissal) and (selection_confidence > 0.4)

       # Log both (don't let model define its own label)
       logs[i]['action_executed_observed'] = action_executed_observed
       logs[i]['action_executed_predicted'] = action_executed_predicted

       # Use PREDICTED for downstream model dynamics (policy evaluation)
       # Use OBSERVED only for validation (H3a)
       action_executed = action_executed_predicted  # Model's own policy
   ```

2. **Validation analysis**:
   ```python
   # In validation_metrics.py
   def compute_action_execution_auc(trial_df, ...):
       # Compare model PREDICTIONS to OBSERVATIONS
       auc = roc_auc_score(
           y_true=trial_df['action_executed_observed'],
           y_score=trial_df['attunement_score']  # or action_prob_predicted
       )
   ```

**Priority:** HIGH (critical for honest H3a validation)

**Estimated Effort:** 1-2 hours

---

## Integration Example Status

### ✅ Complete Validation Pipeline (COMPLETED)

**Implementation:** `docs/validation_example.py`

**Features:**
- ✅ Synthetic data generator (mimics Study 1 lab session)
- ✅ Post-hoc alignment (placeholder for observation-conditioned mode)
- ✅ Merge empirical + model outputs
- ✅ Compute all H1-H5 metrics
- ✅ Generate 5 diagnostic plots:
  - Correlation matrix
  - ROC curve (H3a)
  - Calibration plot
  - Scatter plots (stress, attunement, memory, confidence)
  - ICC visualization
- ✅ Save JSON + TXT reports

**Test Run:**
```bash
python docs/validation_example.py
```

**Output:**
```
Success rate: 50.0% (4/8)
  ✓ H1a (Stress): r=0.441
  ✗ H1b (HRV): r=-0.328 (failed threshold r ≤ -0.25)
  ✗ H3a (Action AUC): AUC=0.652 (below threshold 0.70)
  ✓ H4a (Trait independence): ΔR²=0.0006
  ✓ H4b (ICC): 0.021
  ✓ H5a (Lapse RMSE): 0.101
```

---

## Documentation Status

### ✅ Comprehensive Documentation (COMPLETED)

**Files:**
1. ✅ `docs/validation_protocol.md` (40 KB)
   - Study 1 (Lab): 2-3 hour session design
   - Study 2 (Ambulatory): 7-14 day EMA protocol
   - All hypotheses H1-H5 with exact thresholds
   - Power analysis (N=80 for Study 1, N=60 for Study 2)
   - Statistical analysis plan (R code provided)
   - Preregistration checklist
   - Timeline and budget ($37k total)

2. ✅ `docs/empirical_mapping.md` (25 KB)
   - Variable-to-measure mappings (affect, stress, ext_load, mem_load, PE, confidence, attunement)
   - 3 operational definitions for attunement (social-cognitive, task-engagement, interpersonal synchrony)
   - Instrument specifications (PANAS, PSS, gradCPT, etc.)
   - Recommended measurement approaches with pros/cons

3. ✅ `docs/VALIDATION_README.md` (18 KB)
   - Quick start guide
   - Architecture overview (adapters, metrics, integration)
   - Usage workflows (Lab, Ambulatory, Batch)
   - Data format requirements (CSV schema)
   - Validation metrics details (within-subject correlation, ROC, ICC, CV)
   - Diagnostic plots explained
   - Troubleshooting guide
   - Extension examples

4. ✅ `docs/VALIDATION_STATUS.md` (this file)
   - Implementation status tracker
   - Remaining tasks with priorities

---

## Recommended Implementation Order

### Phase 1: Core Validation Capability (Priority: HIGH)
**Estimated Time:** 1 week

1. **Observation-conditioned mode** (Task #2)
   - Modify `simulation.py` to accept `data_adapter`
   - Replace input generation with adapter calls
   - Use learnable PE observer
   - Test with example adapter
   - **Deliverable:** `run_simulation(data_adapter=adapter, observed_mode=1)` works

2. **Gating policy alignment** (Task #7)
   - Separate observed vs. predicted action
   - Ensure honest validation (no label leakage)
   - **Deliverable:** H3a validation uses observed labels

**Testing:**
- Run `validation_example.py` with real observation-conditioned mode (not placeholder)
- Verify all H1-H5 metrics compute correctly
- Check that plots look realistic

---

### Phase 2: Reproducibility & Robustness (Priority: MEDIUM)
**Estimated Time:** 3-5 days

3. **Provenance tracking** (Task #4)
   - Schema versioning
   - Git commit hash logging
   - Atomic file writes
   - **Deliverable:** All outputs include full provenance metadata

4. **Normalization freeze** (Task #5)
   - Add freeze parameter
   - Export/import normalization stats
   - **Deliverable:** Train/test split workflow works correctly

**Testing:**
- Verify provenance includes all parameters
- Test normalization freeze with train/test split
- Confirm out-of-sample prediction (H5a) uses frozen stats

---

### Phase 3: Quality Assurance (Priority: MEDIUM)
**Estimated Time:** 2-3 days

5. **Parameter identifiability tests** (Task #6)
   - Write unit tests for monotonicity
   - Test all key parameter effects
   - **Deliverable:** `pytest tests/test_identifiability.py` passes

**Testing:**
- Run full test suite: `pytest tests/ -v`
- Verify no degeneracies (e.g., increasing stress_mult actually increases penalty)

---

## Success Criteria

### Minimum Viable Validation (MVP):
- ✅ Data adapters work (Task #1) ← **DONE**
- ✅ Endpoint calculator works (Task #3) ← **DONE**
- ⏳ Observation-conditioned mode works (Task #2) ← **NEXT**
- ⏳ Gating policy aligned (Task #7) ← **NEXT**

**When MVP is complete:**
→ Ready for **pilot study** (N=10-20, real participant data)

### Full Validation-Ready:
- All 7 tasks completed
- Pilot study successful (metrics look reasonable)
- Preregistration on OSF submitted

**When fully ready:**
→ Ready for **Study 1** (N=80) and **Study 2** (N=60)

---

## Timeline Estimate

**Assuming 1 FTE developer:**

- **Week 1**: Tasks #2, #7 (observation-conditioned mode + gating alignment)
- **Week 2**: Tasks #4, #5 (provenance + normalization freeze)
- **Week 3**: Task #6 (identifiability tests) + pilot data collection
- **Week 4**: Pilot analysis + refinements

**Total: 1 month to validation-ready MVP**

---

## Notes

### Current Bottleneck:
- Observation-conditioned mode (Task #2) is blocking for real data validation
- All other infrastructure is ready and tested

### Quick Win:
- Tasks #2 and #7 are small (estimated 3-5 hours total) but unlock pilot study capability

### Risk Mitigation:
- Pilot study (N=10-20) before full data collection
- Allows debugging adapters with real participant data quirks
- Can refine thresholds if needed (with transparency in final preregistration)

---

## Contact & Updates

**Document Maintainer:** Cleveland Lewis
**Last Updated:** 2025-10-27 12:15 PM
**Next Review:** After Task #2 completion

**Questions?**
- Check GitHub Issues
- Email: [your email]

---

**End of Status Document**
