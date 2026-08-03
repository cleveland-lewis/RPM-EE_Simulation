# Confidence Quantification: mdd_typical

**Date:** 2026-08-03
**Method:** Normal-normal conjugate Bayesian update of a confidence-derived prior against literature-reported distributional data (mean/SD or 95% CI), where available.

---

## Bayesian Credible Intervals

| Parameter | Value | Confidence | 95% CI | Data-informed? | Source |
|---|---|---|---|---|---|
| base_rt | 600 | MODERATE | [453, 747] | No (prior only) | Prior only (no distributional literature data) |
| rt_variability | 0.2 | LOW | [0.05, 0.641] | No (prior only) | Prior only (no distributional literature data) |
| rt_slowing | 1.2 | MODERATE | [1.11, 1.29] | No (prior only) | Prior only (no distributional literature data) |
| base_accuracy | 0.82 | MODERATE | [0.644, 0.996] | No (prior only) | Prior only (no distributional literature data) |
| accuracy_decline | 0.1 | MODERATE | [0.0647, 0.12] | No (prior only) | Prior only (no distributional literature data) |
| wm_capacity | 3.5 | MODERATE | [2.32, 4.68] | No (prior only) | Prior only (no distributional literature data) |
| wm_decay_rate | 0.022 | LOW | [0.0073, 0.03] | No (prior only) | Prior only (no distributional literature data) |
| attention_stability | 0.65 | MODERATE | [0.488, 0.812] | No (prior only) | Prior only (no distributional literature data) |
| switch_cost | 0.18 | MODERATE | [0.0918, 0.268] | No (prior only) | Prior only (no distributional literature data) |
| vigilance_decrement | 0.02 | LOW | [0.005, 0.035] | No (prior only) | Prior only (no distributional literature data) |
| stress_baseline | 0.55 | HIGH | [0.532, 0.641] | Yes | Burke et al. (2005) -- Basal cortisol, MDD vs. control (meta-analysis; μg/dL, mapped via /50.0) (361 studies) |
| stress_reactivity | 0.65 | MODERATE | [0.43, 0.8] | No (prior only) | Prior only (no distributional literature data) |
| stress_recovery | 0.06 | MODERATE | [0.02, 0.113] | No (prior only) | Prior only (no distributional literature data) |
| positive_affect | 0.25 | HIGH | [0.181, 0.319] | No (prior only) | Prior only (no distributional literature data) |
| negative_affect | 0.55 | MODERATE | [0.374, 0.7] | No (prior only) | Prior only (no distributional literature data) |
| reward_sensitivity | 0.15 | MODERATE | [0.05, 0.385] | No (prior only) | Prior only (no distributional literature data) |
| prediction_error_gain | 0.7 | LOW | [0.05, 1.2] | No (prior only) | Prior only (no distributional literature data) |
| exploration_rate | 0.08 | LOW | [0.05, 0.345] | No (prior only) | Prior only (no distributional literature data) |

---

## Confidence-Weighted Sensitivity & Risk Matrix

`risk_score = max_sensitivity_index * (1 - confidence_weight)`. High risk_score means a parameter both moves outcomes a lot *and* rests on weak evidence.

| Parameter | Max SI | Confidence | Weight | Weighted SI | Risk Score | Category |
|---|---|---|---|---|---|---|
| rt_variability | 1.000 | LOW | 0.25 | 0.250 | 0.750 | **CRITICAL** |
| prediction_error_gain | 1.000 | LOW | 0.25 | 0.250 | 0.750 | **CRITICAL** |
| reward_sensitivity | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| wm_capacity | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| base_accuracy | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| base_rt | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| attention_stability | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| vigilance_decrement | 0.429 | LOW | 0.25 | 0.107 | 0.321 | **MONITOR** |
| wm_decay_rate | 0.220 | LOW | 0.25 | 0.055 | 0.165 | **LOW-RISK** |
| stress_reactivity | 0.405 | MODERATE | 0.60 | 0.243 | 0.162 | **LOW-RISK** |
| stress_baseline | 0.595 | HIGH | 1.00 | 0.595 | 0.000 | **LOW-RISK** |
| exploration_rate | 0.000 | LOW | 0.25 | 0.000 | 0.000 | **LOW-RISK** |

### Flagged Parameters (CRITICAL / WATCH)

- **rt_variability** (CRITICAL): SI=1.00, confidence=LOW -- prioritize evidence strengthening.
- **prediction_error_gain** (CRITICAL): SI=1.00, confidence=LOW -- prioritize evidence strengthening.
- **reward_sensitivity** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.
- **wm_capacity** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.
- **base_accuracy** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.
- **base_rt** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.
- **attention_stability** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.

