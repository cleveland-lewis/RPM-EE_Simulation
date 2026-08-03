# Confidence Quantification: adhd_typical

**Date:** 2026-08-03
**Method:** Normal-normal conjugate Bayesian update of a confidence-derived prior against literature-reported distributional data (mean/SD or 95% CI), where available.

---

## Bayesian Credible Intervals

| Parameter | Value | Confidence | 95% CI | Data-informed? | Source |
|---|---|---|---|---|---|
| base_rt | 520 | MODERATE | [373, 667] | No (prior only) | Prior only (no distributional literature data) |
| rt_variability | 0.45 | HIGH | [0.398, 0.502] | Yes | Kofler et al. (2013) -- RT coefficient of variation, ADHD vs. control (meta-analysis) (319 studies, N=13,233 ADHD / 11,842 control) |
| rt_slowing | 1.04 | MODERATE | [1, 1.13] | No (prior only) | Prior only (no distributional literature data) |
| base_accuracy | 0.8 | HIGH | [0.741, 0.859] | No (prior only) | Prior only (no distributional literature data) |
| accuracy_decline | 0.12 | MODERATE | [0.0847, 0.12] | No (prior only) | Prior only (no distributional literature data) |
| wm_capacity | 3 | HIGH | [2.61, 3.39] | No (prior only) | Prior only (no distributional literature data) |
| wm_decay_rate | 0.018 | LOW | [0.005, 0.03] | No (prior only) | Prior only (no distributional literature data) |
| attention_stability | 0.6 | HIGH | [0.546, 0.654] | No (prior only) | Prior only (no distributional literature data) |
| switch_cost | 0.08 | MODERATE | [0.05, 0.168] | No (prior only) | Prior only (no distributional literature data) |
| vigilance_decrement | 0.025 | MODERATE | [0.0162, 0.0338] | No (prior only) | Prior only (no distributional literature data) |
| stress_baseline | 0.35 | MODERATE | [0.144, 0.556] | No (prior only) | Prior only (no distributional literature data) |
| stress_reactivity | 0.75 | MODERATE | [0.53, 0.8] | No (prior only) | Prior only (no distributional literature data) |
| stress_recovery | 0.1 | LOW | [0.02, 0.2] | No (prior only) | Prior only (no distributional literature data) |
| positive_affect | 0.55 | LOW | [0.138, 0.8] | No (prior only) | Prior only (no distributional literature data) |
| negative_affect | 0.3 | LOW | [0.1, 0.653] | No (prior only) | Prior only (no distributional literature data) |
| reward_sensitivity | 0.85 | MODERATE | [0.615, 0.85] | No (prior only) | Prior only (no distributional literature data) |
| prediction_error_gain | 1.2 | LOW | [0.524, 1.2] | No (prior only) | Prior only (no distributional literature data) |
| exploration_rate | 0.4 | MODERATE | [0.268, 0.5] | No (prior only) | Prior only (no distributional literature data) |

---

## Confidence-Weighted Sensitivity & Risk Matrix

`risk_score = max_sensitivity_index * (1 - confidence_weight)`. High risk_score means a parameter both moves outcomes a lot *and* rests on weak evidence.

| Parameter | Max SI | Confidence | Weight | Weighted SI | Risk Score | Category |
|---|---|---|---|---|---|---|
| prediction_error_gain | 1.000 | LOW | 0.25 | 0.250 | 0.750 | **CRITICAL** |
| reward_sensitivity | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| base_rt | 1.000 | MODERATE | 0.60 | 0.600 | 0.400 | **WATCH** |
| stress_baseline | 0.595 | MODERATE | 0.60 | 0.357 | 0.238 | **LOW-RISK** |
| vigilance_decrement | 0.429 | MODERATE | 0.60 | 0.257 | 0.171 | **LOW-RISK** |
| wm_decay_rate | 0.220 | LOW | 0.25 | 0.055 | 0.165 | **LOW-RISK** |
| stress_reactivity | 0.405 | MODERATE | 0.60 | 0.243 | 0.162 | **LOW-RISK** |
| rt_variability | 1.000 | HIGH | 1.00 | 1.000 | 0.000 | **WELL-SUPPORTED** |
| attention_stability | 1.000 | HIGH | 1.00 | 1.000 | 0.000 | **WELL-SUPPORTED** |
| wm_capacity | 1.000 | HIGH | 1.00 | 1.000 | 0.000 | **WELL-SUPPORTED** |
| base_accuracy | 1.000 | HIGH | 1.00 | 1.000 | 0.000 | **WELL-SUPPORTED** |
| exploration_rate | 0.000 | MODERATE | 0.60 | 0.000 | 0.000 | **LOW-RISK** |

### Flagged Parameters (CRITICAL / WATCH)

- **prediction_error_gain** (CRITICAL): SI=1.00, confidence=LOW -- prioritize evidence strengthening.
- **reward_sensitivity** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.
- **base_rt** (WATCH): SI=1.00, confidence=MODERATE -- prioritize evidence strengthening.

