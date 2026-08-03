# Confidence Quantification: neurotypical

**Date:** 2026-08-03
**Method:** Normal-normal conjugate Bayesian update of a confidence-derived prior against literature-reported distributional data (mean/SD or 95% CI), where available.

---

## Bayesian Credible Intervals

| Parameter | Value | Confidence | 95% CI | Data-informed? | Source |
|---|---|---|---|---|---|
| base_rt | 500 | HIGH | [451, 549] | No (prior only) | Prior only (no distributional literature data) |
| rt_variability | 0.15 | MODERATE | [0.05, 0.37] | No (prior only) | Prior only (no distributional literature data) |
| rt_slowing | 1 | HIGH | [1, 1.03] | No (prior only) | Prior only (no distributional literature data) |
| base_accuracy | 0.9 | MODERATE | [0.724, 1] | No (prior only) | Prior only (no distributional literature data) |
| accuracy_decline | 0.05 | MODERATE | [0.0147, 0.0853] | No (prior only) | Prior only (no distributional literature data) |
| wm_capacity | 4 | HIGH | [3.61, 4.39] | No (prior only) | Prior only (no distributional literature data) |
| wm_decay_rate | 0.01 | LOW | [0.005, 0.0247] | No (prior only) | Prior only (no distributional literature data) |
| attention_stability | 0.85 | LOW | [0.527, 0.95] | No (prior only) | Prior only (no distributional literature data) |
| switch_cost | 0.1 | LOW | [0.05, 0.276] | No (prior only) | Prior only (no distributional literature data) |
| vigilance_decrement | 0.01 | LOW | [0.005, 0.0276] | No (prior only) | Prior only (no distributional literature data) |
| stress_baseline | 0.3 | LOW | [0.1, 0.712] | No (prior only) | Prior only (no distributional literature data) |
| stress_reactivity | 0.5 | LOW | [0.059, 0.8] | No (prior only) | Prior only (no distributional literature data) |
| stress_recovery | 0.15 | LOW | [0.0442, 0.2] | No (prior only) | Prior only (no distributional literature data) |
| positive_affect | 0.6 | LOW | [0.188, 0.8] | No (prior only) | Prior only (no distributional literature data) |
| negative_affect | 0.2 | LOW | [0.1, 0.553] | No (prior only) | Prior only (no distributional literature data) |
| reward_sensitivity | 0.7 | LOW | [0.23, 0.85] | No (prior only) | Prior only (no distributional literature data) |
| prediction_error_gain | 1 | LOW | [0.324, 1.2] | No (prior only) | Prior only (no distributional literature data) |
| exploration_rate | 0.2 | LOW | [0.05, 0.465] | No (prior only) | Prior only (no distributional literature data) |

---

## Confidence-Weighted Sensitivity & Risk Matrix

`risk_score = max_sensitivity_index * (1 - confidence_weight)`. High risk_score means a parameter both moves outcomes a lot *and* rests on weak evidence.

| Parameter | Max SI | Confidence | Weight | Weighted SI | Risk Score | Category |
|---|---|---|---|---|---|---|
| reward_sensitivity | 1.000 | LOW | 0.25 | 0.250 | 0.750 | **CRITICAL** |
| prediction_error_gain | 1.000 | LOW | 0.25 | 0.250 | 0.750 | **CRITICAL** |
| attention_stability | 1.000 | LOW | 0.25 | 0.250 | 0.750 | **CRITICAL** |
| stress_baseline | 0.595 | LOW | 0.25 | 0.149 | 0.446 | **MONITOR** |
| base_accuracy | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| rt_variability | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| vigilance_decrement | 0.429 | LOW | 0.25 | 0.107 | 0.321 | **MONITOR** |
| stress_reactivity | 0.405 | LOW | 0.25 | 0.101 | 0.304 | **MONITOR** |
| wm_decay_rate | 0.220 | LOW | 0.25 | 0.055 | 0.165 | **LOW-RISK** |
| wm_capacity | 1.000 | HIGH | 1.00 | 1.000 | 0.000 | **WELL-SUPPORTED** |
| base_rt | 1.000 | HIGH | 1.00 | 1.000 | 0.000 | **WELL-SUPPORTED** |
| exploration_rate | 0.000 | LOW | 0.25 | 0.000 | 0.000 | **LOW-RISK** |

### Flagged Parameters (CRITICAL / WATCH)

- **reward_sensitivity** (CRITICAL): SI=1.00, confidence=LOW -- prioritize evidence strengthening.
- **prediction_error_gain** (CRITICAL): SI=1.00, confidence=LOW -- prioritize evidence strengthening.
- **attention_stability** (CRITICAL): SI=1.00, confidence=LOW -- prioritize evidence strengthening.
- **base_accuracy** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.
- **rt_variability** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.

