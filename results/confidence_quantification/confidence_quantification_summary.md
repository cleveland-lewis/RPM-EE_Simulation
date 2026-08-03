# Confidence Quantification Summary (All Presets)

**Date:** 2026-08-03
**Related:** Issue #19, PHASE3_PROGRESS.md "Confidence Quantification" milestone

---

## Global Risk Matrix (High Sensitivity + Low Confidence)

Top 15 parameter/preset combinations by risk score:

| Preset | Parameter | Max SI | Confidence | Risk Score | Category |
|---|---|---|---|---|---|
| neurotypical | reward_sensitivity | 1.000 | LOW | 0.750 | **CRITICAL** |
| asd_typical | reward_sensitivity | 1.000 | LOW | 0.750 | **CRITICAL** |
| neurotypical | prediction_error_gain | 1.000 | LOW | 0.750 | **CRITICAL** |
| asd_typical | prediction_error_gain | 1.000 | LOW | 0.750 | **CRITICAL** |
| adhd_typical | prediction_error_gain | 1.000 | LOW | 0.750 | **CRITICAL** |
| mdd_typical | rt_variability | 1.000 | LOW | 0.750 | **CRITICAL** |
| mdd_typical | prediction_error_gain | 1.000 | LOW | 0.750 | **CRITICAL** |
| neurotypical | attention_stability | 1.000 | LOW | 0.750 | **CRITICAL** |
| neurotypical | stress_baseline | 0.595 | LOW | 0.446 | **MONITOR** |
| adhd_typical | reward_sensitivity | 1.000 | MODERATE | 0.400 | **WATCH** |
| mdd_typical | reward_sensitivity | 1.000 | MODERATE | 0.400 | **WATCH** |
| asd_typical | wm_capacity | 1.000 | MODERATE | 0.400 | **WATCH** |
| mdd_typical | wm_capacity | 1.000 | MODERATE | 0.400 | **WATCH** |
| neurotypical | base_accuracy | 1.000 | MODERATE | 0.400 | **WATCH** |
| asd_typical | base_accuracy | 1.000 | MODERATE | 0.400 | **WATCH** |

### CRITICAL / WATCH Parameters Across All Presets

- **reward_sensitivity** (neurotypical): CRITICAL
- **reward_sensitivity** (asd_typical): CRITICAL
- **prediction_error_gain** (neurotypical): CRITICAL
- **prediction_error_gain** (asd_typical): CRITICAL
- **prediction_error_gain** (adhd_typical): CRITICAL
- **rt_variability** (mdd_typical): CRITICAL
- **prediction_error_gain** (mdd_typical): CRITICAL
- **attention_stability** (neurotypical): CRITICAL
- **reward_sensitivity** (adhd_typical): WATCH
- **reward_sensitivity** (mdd_typical): WATCH
- **wm_capacity** (asd_typical): WATCH
- **wm_capacity** (mdd_typical): WATCH
- **base_accuracy** (neurotypical): WATCH
- **base_accuracy** (asd_typical): WATCH
- **base_accuracy** (mdd_typical): WATCH
- **rt_variability** (neurotypical): WATCH
- **rt_variability** (asd_typical): WATCH
- **base_rt** (asd_typical): WATCH
- **base_rt** (adhd_typical): WATCH
- **base_rt** (mdd_typical): WATCH
- **attention_stability** (asd_typical): WATCH
- **attention_stability** (mdd_typical): WATCH

### Comparison to PHASE3_VALIDATION_FINDINGS.md

The findings document previously named `reward_sensitivity` and `prediction_error_gain` as the highest-priority high-sensitivity / low-confidence parameters (based on manual review). The table above recomputes this from the actual sensitivity-analysis + confidence data and should be treated as the current source of truth.

---

## Methodology

See module docstring in `scripts/confidence_quantification.py` for full detail. In short:

1. Every parameter gets a prior Normal(preset value, sd) where sd scales with (LOW/MODERATE/HIGH) evidence confidence as a fraction of the parameter's documented range (docs/PARAMETER_SCALES.md).
2. Where a cited meta-analysis reports a mean/SD or explicit 95% CI on the same (or a linearly mappable) scale, that is combined with the prior via conjugate normal-normal Bayesian updating to get a genuine posterior credible interval. Currently: `rt_variability` (ADHD, Kofler et al. 2013) and `stress_baseline` (MDD, Burke et al. 2005).
3. All other parameters report a prior-only interval, explicitly labeled as not data-informed.
4. Confidence-weighted sensitivity multiplies each parameter's max sensitivity index (from `scripts/sensitivity_analysis.py`) by a confidence weight (HIGH=1.0, MODERATE=0.6, LOW=0.25); `risk_score` uses the complement, so it is highest for parameters that matter a lot but are weakly supported.
