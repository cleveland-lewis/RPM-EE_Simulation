# RPM-EE Validation Infrastructure

**Version:** 1.0.0
**Date:** 2025-10-27
**Status:** Ready for empirical validation

---

## Overview

This document describes the complete validation infrastructure for the RPM-EE (Recursive Predictive Modeling with Emotional Encoding) computational framework. The infrastructure enables rigorous empirical validation against behavioral, physiological, and self-report measurements.

---

## Quick Start

```bash
# Run complete validation example (synthetic data)
python docs/validation_example.py

# Outputs:
#   - validation_output/<run_label>/validation_results.json
#   - validation_output/<run_label>/validation_summary.txt
#   - validation_output/<run_label>/validation_meta.json
#   - validation_output/<run_label>/plots/*.png
```

---

## Architecture

### 1. **Data Adapters** (`src/adapters.py`)

**Purpose**: Load real empirical data and align with simulation tick rate.

**Key Classes**:
- **`EmpiricalDataAdapter`**: Main adapter for CSV/pandas data
  - Time alignment (resample to uniform tick rate: '1s', '100ms', etc.)
  - Unit normalization (stress 0-10 → 0-1, affect -3/+3 → -1/+1)
  - Missing data interpolation (linear, max gap = 5 ticks)
  - Fast tick-level lookups via precomputed series

- **`EMAObserver`**: Delta-rule prediction error observer
- **`KalmanObserver`**: Bayesian Gaussian filter for PE

**Example**:
```python
from src.adapters import EmpiricalDataAdapter

# Load participant data
adapter = EmpiricalDataAdapter.from_csv(
    "participant_001.csv",
    tick_rate='1s',
    interpolate_missing=True
)

# Access data at specific ticks
affect = adapter.get_affect_feedback(tick=100)
stress = adapter.get_stress_rating(tick=100)
ext_load = adapter.get_external_load(tick=100)  # Returns dict: {vision, hearing, touch}
```

---

### 2. **Validation Metrics** (`src/validation_metrics.py`)

**Purpose**: Compute all preregistered hypotheses (H1-H5) from validation_protocol.md.

**Implemented Hypotheses**:

| Hypothesis | Test | Threshold | Function |
|------------|------|-----------|----------|
| **H1a** | Stress convergence (model ~ empirical) | r ≥ 0.30 | `compute_convergent_validity()` |
| **H1b** | HRV inverse correlation | r ≤ -0.25 | `compute_hrv_stress_convergence()` |
| **H2a** | Memory load → RT/accuracy | β > 0.20 | `compute_memory_load_prediction()` |
| **H3a** | Attunement → action execution | AUC ≥ 0.70 | `compute_action_execution_auc()` |
| **H3b** | Attunement ~ confidence | r ≥ 0.30 | `compute_confidence_correlation()` |
| **H4a** | Trait independence (ΔR²) | ΔR² < 0.02 | `compute_discriminant_validity()` |
| **H4b** | State variability (ICC) | ICC < 0.40 | `compute_icc()` |
| **H5a** | Lapse prediction (CV RMSE) | RMSE < 0.15 | `compute_lapse_prediction()` |
| **H5b** | Lagged omission (OR) | OR > 1.40 | `compute_lagged_omission_prediction()` |

**Master Function**:
```python
from src.validation_metrics import compute_all_endpoints

results = compute_all_endpoints(
    merged_df=aligned_data,           # Tick/trial-level
    trial_df=trial_data,              # For H2, H3a, H5b
    block_df=block_data,              # For H3b, H4
    participant_df=participant_data   # For H5a
)

# Check success rate
print(f"Success: {results['summary']['success_rate']:.1%}")

# Access individual hypotheses
h1a = results['hypotheses']['H1a_stress_corr']
print(f"H1a: r={h1a['r']:.3f}, p={h1a['p']:.3f}, pass={h1a['success']}")
```

---

### 3. **Integration Example** (`docs/validation_example.py`)

**Purpose**: End-to-end demonstration of complete validation pipeline.

**Pipeline Steps**:

1. **Generate/Load Empirical Data**
   - Synthetic data generator for testing
   - CSV loader for real participant data

2. **Run RPM-EE Simulation**
   - Currently: Post-hoc alignment (placeholder)
   - Future: Observation-conditioned mode with `data_adapter`

3. **Merge and Align**
   - Timestamp matching (tolerance: ±500ms)
   - Column suffixes: `_empirical`, `_model`

4. **Compute Validation Metrics**
   - All hypotheses H1-H5
   - Success/fail against preregistered thresholds

5. **Generate Diagnostic Plots**
   - Correlation matrix (model vs. empirical)
   - ROC curve (attunement → action)
   - Calibration plot (probability alignment)
   - Scatter plots (stress, attunement, mem_load, confidence)
   - ICC visualization (within vs. between-subject variance)

6. **Save Reports**
   - JSON: Complete metrics with all statistics
   - TXT: Human-readable summary
   - PNG: Diagnostic visualizations

**Example Output**:
```
validation_output/
  └── <run_label>/                   # Timestamped run folder
      ├── empirical_data.csv         # Input: Empirical measurements
      ├── model_outputs.csv          # Output: RPM-EE simulation results
      ├── validation_results.json    # Metrics: All H1-H5 statistics + metadata
      ├── validation_summary.txt     # Report: Human-readable summary
      ├── validation_meta.json       # Traceability (preset/seed/version/data hashes/run_label)
      └── plots/
          ├── correlation_matrix.png
          ├── roc_curve_h3a.png
          ├── calibration_plot.png
          ├── scatter_plots.png
          └── icc_visualization.png
```

---

## Usage Workflows

### Workflow A: Lab Session Validation (Study 1)

```python
# Step 1: Load participant data
from src.adapters import EmpiricalDataAdapter

adapter = EmpiricalDataAdapter.from_csv(
    "data/study1/participant_001_session.csv",
    tick_rate='1s',  # 1-second ticks (2400 ticks for 40-min session)
    interpolate_missing=True
)

# Step 2: Run simulation (observation-conditioned mode)
# TODO: Once implemented in simulation.py
# from src.simulation import run_simulation
# result = run_simulation(
#     data_adapter=adapter,
#     observed_mode=1,
#     preset='default',
#     seed=42
# )

# Step 3: Compute validation metrics
from src.validation_metrics import compute_all_endpoints

results = compute_all_endpoints(
    merged_df=merged_data,
    trial_df=trial_data,
    block_df=block_data,
    participant_df=participant_data
)

# Step 4: Check results
print(f"Success rate: {results['summary']['success_rate']:.1%}")
for hyp, res in results['hypotheses'].items():
    status = "✓" if res['success'] else "✗"
    print(f"{status} {hyp}")
```

---

### Workflow B: Ambulatory EMA Validation (Study 2)

```python
# Load 7-day EMA data
adapter = EmpiricalDataAdapter.from_csv(
    "data/study2/participant_001_week1.csv",
    tick_rate='1min',  # 1-minute ticks (10,080 ticks for 7 days)
    interpolate_missing=True
)

# Participant has sparse EMA prompts (4-6/day)
# Model fills gaps via interpolation
# Validation focuses on within-day dynamics and day-level means

results = compute_all_endpoints(merged_df=merged_data)

# Focus on H1a (stress convergence) and H5a (day-level prediction)
print(f"H1a stress r={results['hypotheses']['H1a_stress_corr']['r']:.3f}")
print(f"H5a lapse RMSE={results['hypotheses']['H5a_lapse_prediction']['rmse_mean']:.3f}")
```

---

### Workflow C: Batch Validation (Multiple Participants)

```python
import pandas as pd
from pathlib import Path

participants = Path("data/study1/").glob("participant_*.csv")
all_results = []

for participant_file in participants:
    print(f"Processing {participant_file.name}...")

    # Load data
    adapter = EmpiricalDataAdapter.from_csv(participant_file)

    # Run simulation (placeholder)
    # result = run_simulation(data_adapter=adapter, observed_mode=1)

    # Compute metrics
    results = compute_all_endpoints(merged_df=merged_data)
    results['participant_id'] = participant_file.stem

    all_results.append(results)

# Aggregate across participants
success_rates = [r['summary']['success_rate'] for r in all_results]
print(f"Mean success rate: {np.mean(success_rates):.1%}")
```

---

## Data Format Requirements

### CSV Input Format

**Required columns**:
- `timestamp`: Unix milliseconds or relative time from session start

**Optional columns** (model will use defaults if missing):
- `affect_valence`: [-3, +3] or [-1, 1] (will auto-normalize)
- `stress_rating`: [0, 10] (will normalize to [0, 1])
- `arousal`: [1, 7] (will normalize to [0, 1])
- `hrv_rmssd`: HRV in ms (will inverse-normalize for stress proxy)
- `scl`: Skin conductance level in µS
- `vision_load`, `auditory_load`, `touch_load`: [0, 1] stimulus intensity
- `nback_accuracy`: [0, 1] for memory load inference
- `nback_rt`: Response time in ms
- `action_executed`: Binary (1=response, 0=omission)
- `confidence_rating`: [0, 100] (will normalize to [0, 1])
- `task_block`: Integer block ID
- `trial_number`: Integer trial ID within block

**Example CSV**:
```csv
timestamp,affect_valence,stress_rating,vision_load,action_executed,confidence_rating
0,0.5,3,0.3,1,75
1000,0.2,4,0.5,1,65
2000,-0.1,5,0.4,0,50
```

---

## Validation Metrics Details

### Within-Subject vs. Pooled Correlations

**Within-subject** (default for H1, H3b):
- Compute correlation per participant
- Fisher z-transform, average, inverse transform
- Tests if mean r > 0 (one-sample t-test)
- More conservative, accounts for between-subject heterogeneity

**Pooled** (optional):
- Single correlation across all observations
- Faster, but ignores clustering
- May inflate Type I error if not accounting for repeated measures

### ROC Analysis (H3a)

**Procedure**:
1. Compute per-participant AUC (attunement → action execution)
2. Average across participants (mean ± SD)
3. One-sample t-test: AUC > 0.50 (chance)
4. Success: mean AUC ≥ 0.70 and p < 0.05

**Global ROC curve**:
- Pooled across all trials (for visualization)
- Reports global AUC as reference

### ICC Calculation (H4b)

**One-way random effects ANOVA**:
```
ICC = (MS_between - MS_within) / (MS_between + (k-1) * MS_within)
```
where k = mean observations per participant

**Interpretation**:
- ICC > 0.60: Trait-like (stable across time)
- ICC < 0.40: State-like (varies within-subject) ← Target for attunement

### Cross-Validated Prediction (H5a)

**10-Fold CV**:
- Split participants into 10 folds
- Train on 9 folds, predict on 1 held-out fold
- Repeat 10 times (each fold held out once)
- Report mean RMSE across folds

**Why cross-validation?**
- Prevents overfitting
- Tests out-of-sample generalization
- Essential for predictive validity

---

## Diagnostic Plots

### 1. Correlation Matrix
- **Purpose**: Overview of model-empirical alignment
- **Content**: Heatmap of Pearson r for all variable pairs
- **Key comparisons**:
  - `schema_stress` ~ `stress_rating`
  - `attunement_score` ~ `attunement_ground_truth` (if available)
  - `mem_load` ~ `mem_load_empirical`

### 2. ROC Curve (H3a)
- **Purpose**: Visualize attunement's ability to predict action execution
- **X-axis**: False positive rate (predicted action, actual omission)
- **Y-axis**: True positive rate (predicted action, actual action)
- **Threshold line**: AUC = 0.70 (preregistered minimum)

### 3. Calibration Plot
- **Purpose**: Check if attunement probabilities are well-calibrated
- **X-axis**: Predicted action probability (attunement score)
- **Y-axis**: Observed action frequency
- **Ideal**: Points fall on diagonal (predicted = observed)
- **Metric**: Expected Calibration Error (ECE)

### 4. Scatter Plots (Model vs. Empirical)
- **Grid**: 2×2 scatter plots
  - Stress (H1a)
  - Attunement
  - Memory load (H2)
  - Confidence (H3b)
- **Color**: Different participants (first 5 for clarity)
- **Diagonal**: Perfect alignment reference line

### 5. ICC Visualization
- **Purpose**: Show within vs. between-subject variance
- **Format**: Error bars (participant mean ± within-subject SD)
- **Horizontal line**: Grand mean across all participants
- **Interpretation**: Large error bars + low grand mean variation → low ICC (state variable)

---

## Extending the Infrastructure

### Adding New Hypotheses

1. **Define hypothesis** in `validation_protocol.md`
2. **Implement test function** in `validation_metrics.py`:
   ```python
   def compute_new_hypothesis(df, model_col, empirical_col) -> Dict:
       # Compute statistic
       r, p = pearsonr(df[model_col], df[empirical_col])

       # Check success
       success = r >= THRESHOLD and p < 0.05

       return {
           'r': r,
           'p': p,
           'success': success,
           'hypothesis': 'H6_new_test',
       }
   ```
3. **Add to `compute_all_endpoints()`**:
   ```python
   results['hypotheses']['H6_new_test'] = compute_new_hypothesis(...)
   ```

### Adding New Data Sources

**Example: Wearable accelerometer data**

```python
# Extend EmpiricalDataAdapter
class AccelerometerAdapter(EmpiricalDataAdapter):
    def get_movement_load(self, tick: int) -> float:
        """Return movement intensity from accelerometer."""
        if 0 <= tick < self.total_ticks:
            return float(self.movement_series[tick])
        return 0.0
```

### Adding New Plots

```python
# In validation_example.py, add to generate_validation_plots()

def plot_new_diagnostic(merged_df, output_dir):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(merged_df['model_var'], merged_df['empirical_var'])
    ax.set_xlabel('Model Variable')
    ax.set_ylabel('Empirical Variable')
    ax.set_title('New Diagnostic Plot')
    plt.savefig(output_dir / 'new_plot.png', dpi=150)
    plt.close()
```

---

## Troubleshooting

### Low Correlations (H1, H2, H3b)

**Possible causes**:
- **Measurement noise**: Empirical measures have low reliability
- **Model miscalibration**: Parameters need tuning (run calibration step first)
- **Time misalignment**: Check timestamp matching tolerance
- **Missing data**: Too many interpolated values (check interpolation limit)

**Solutions**:
- Increase sample size (more participants, more trials/participant)
- Calibrate model parameters to individual baselines (fit theta0, stress_decay per person)
- Use robust correlation (Spearman instead of Pearson)
- Aggregate to block level (reduce trial-level noise)

### Low AUC (H3a)

**Possible causes**:
- **Attunement not predictive**: Model attunement doesn't capture action readiness
- **Behavioral task issue**: Action execution is random (no cognitive control)
- **Threshold issue**: Binary outcome loses information (use continuous confidence instead)

**Solutions**:
- Check base rate (if >90% or <10% actions, AUC will be low)
- Use calibrated probability instead of binary prediction
- Stratify by difficulty (AUC may be high within difficulty level but low overall)

### High ICC (H4b)

**Possible causes**:
- **Too trait-like**: Attunement is stable across time (contradicts theory)
- **Small within-subject variance**: Not enough state manipulation in task

**Solutions**:
- Check task manipulations (is stress/load actually varying?)
- Increase number of trials per participant
- Use longer time windows (EMA over days, not just single session)

### High RMSE (H5a)

**Possible causes**:
- **Weak predictors**: Block 1 stress/attunement don't forecast Block 2 lapses
- **Non-linear relationships**: Linear regression may be insufficient
- **Overfitting**: Model is too complex for sample size

**Solutions**:
- Add non-linear terms (polynomial, interaction effects)
- Use regularized regression (Ridge, Lasso) to reduce overfitting
- Increase participant sample size
- Check for outliers (Winsorize extreme lapse rates)

---

## Next Steps

### Immediate (Ready to Use):
1. ✓ Data adapters implemented
2. ✓ Validation metrics implemented
3. ✓ Integration example working
4. ✓ Diagnostic plots functional

### Short-Term (Weeks 1-4):
5. **Implement observation-conditioned mode in `simulation.py`**
   - Modify `run_simulation()` to accept `data_adapter` parameter
   - Replace `_generate_base_arrays()` with `adapter.get_*()`
   - Use `EMAObserver` or `KalmanObserver` for observed PE

6. **Add provenance tracking**
   - Schema versioning in outputs
   - Git commit hash, timestamp, all parameters logged
   - Atomic file writes with locks

7. **Implement normalization freeze**
   - Compute μ/σ on train set
   - Apply frozen stats to test set (for H5a out-of-sample validation)

### Medium-Term (Weeks 5-12):
8. **Parameter identifiability tests**
   - Unit tests for monotonicity (increasing theta_s_mult → higher stress penalty)
   - Prevent degeneracies during calibration

9. **Pilot Study (N=10-20)**
   - Collect real data (Study 1 lab session)
   - Run validation pipeline
   - Refine adapters based on real data quirks

10. **Calibration procedure**
    - Bayesian inference (PyMC) to fit individual parameters
    - Optimize presets to match empirical distributions

### Long-Term (Months 3-12):
11. **Full Study 1 (Lab, N=80)**
    - Preregister on OSF
    - Collect data (2-hour sessions × 80 participants)
    - Full validation battery (H1-H5)

12. **Full Study 2 (Ambulatory, N=60)**
    - Mobile app development
    - 7-14 day EMA collection
    - Replication of H1a, H5a with ecological data

---

## References

- **`validation_protocol.md`**: Complete study designs (Lab + Ambulatory)
- **`empirical_mapping.md`**: Variable-to-measurement mappings
- **`src/adapters.py`**: Data adapter implementation
- **`src/validation_metrics.py`**: Endpoint calculator
- **`docs/validation_example.py`**: End-to-end integration example

---

## Contact

**Questions or issues?**
- Check GitHub Issues: [link to repo issues]
- Email: [your email]

**Contributing:**
- Fork repo, create branch, submit PR
- All new hypotheses must be preregistered before data collection

---

**End of Documentation**
