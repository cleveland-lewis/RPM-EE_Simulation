# Confidence Quantification: asd_typical

**Date:** 2026-08-03
**Method:** Normal-normal conjugate Bayesian update of a confidence-derived prior against literature-reported distributional data (mean/SD or 95% CI), where available.

---

## Bayesian Credible Intervals

| Parameter | Value | Confidence | 95% CI | Data-informed? | Source |
|---|---|---|---|---|---|
| base_rt | 575 | MODERATE | [428, 722] | No (prior only) | Prior only (no distributional literature data) |
| rt_variability | 0.18 | MODERATE | [0.05, 0.4] | No (prior only) | Prior only (no distributional literature data) |
| rt_slowing | 1.15 | MODERATE | [1.06, 1.24] | No (prior only) | Prior only (no distributional literature data) |
| base_accuracy | 0.88 | MODERATE | [0.704, 1] | No (prior only) | Prior only (no distributional literature data) |
| accuracy_decline | 0.08 | LOW | [0.00944, 0.12] | No (prior only) | Prior only (no distributional literature data) |
| wm_capacity | 4 | MODERATE | [2.82, 5.18] | No (prior only) | Prior only (no distributional literature data) |
| wm_decay_rate | 0.015 | LOW | [0.005, 0.0297] | No (prior only) | Prior only (no distributional literature data) |
| attention_stability | 0.87 | MODERATE | [0.708, 0.95] | No (prior only) | Prior only (no distributional literature data) |
| switch_cost | 0.25 | MODERATE | [0.162, 0.338] | No (prior only) | Prior only (no distributional literature data) |
| vigilance_decrement | 0.008 | LOW | [0.005, 0.0256] | No (prior only) | Prior only (no distributional literature data) |
| stress_baseline | 0.5 | MODERATE | [0.294, 0.706] | No (prior only) | Prior only (no distributional literature data) |
| stress_reactivity | 0.6 | MODERATE | [0.38, 0.8] | No (prior only) | Prior only (no distributional literature data) |
| stress_recovery | 0.08 | HIGH | [0.0624, 0.0976] | No (prior only) | Prior only (no distributional literature data) |
| positive_affect | 0.5 | LOW | [0.1, 0.8] | No (prior only) | Prior only (no distributional literature data) |
| negative_affect | 0.35 | LOW | [0.1, 0.7] | No (prior only) | Prior only (no distributional literature data) |
| reward_sensitivity | 0.55 | LOW | [0.0796, 0.85] | No (prior only) | Prior only (no distributional literature data) |
| prediction_error_gain | 0.9 | LOW | [0.224, 1.2] | No (prior only) | Prior only (no distributional literature data) |
| exploration_rate | 0.12 | LOW | [0.05, 0.385] | No (prior only) | Prior only (no distributional literature data) |

---

## Confidence-Weighted Sensitivity & Risk Matrix

`risk_score = max_sensitivity_index * (1 - confidence_weight)`. High risk_score means a parameter both moves outcomes a lot *and* rests on weak evidence.

| Parameter | Max SI | Confidence | Weight | Weighted SI | Risk Score | Category |
|---|---|---|---|---|---|---|
| reward_sensitivity | 1.000 | LOW | 0.25 | 0.250 | 0.750 | **CRITICAL** |
| prediction_error_gain | 1.000 | LOW | 0.25 | 0.250 | 0.750 | **CRITICAL** |
| wm_capacity | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| base_accuracy | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| rt_variability | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| base_rt | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| attention_stability | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| vigilance_decrement | 0.429 | LOW | 0.25 | 0.107 | 0.321 | **MONITOR** |
| stress_baseline | 0.595 | MODERATE | 0.60 | 0.357 | 0.238 | **LOW-RISK** |
| wm_decay_rate | 0.220 | LOW | 0.25 | 0.055 | 0.165 | **LOW-RISK** |
| stress_reactivity | 0.405 | MODERATE | 0.60 | 0.243 | 0.162 | **LOW-RISK** |
| exploration_rate | 0.000 | LOW | 0.25 | 0.000 | 0.000 | **LOW-RISK** |

### Flagged Parameters (CRITICAL / WATCH)

- **reward_sensitivity** (CRITICAL): SI=1.00, confidence=LOW -- prioritize evidence strengthening.
- **prediction_error_gain** (CRITICAL): SI=1.00, confidence=LOW -- prioritize evidence strengthening.
- **wm_capacity** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.
- **base_accuracy** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.
- **rt_variability** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.
- **base_rt** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.
- **attention_stability** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.

