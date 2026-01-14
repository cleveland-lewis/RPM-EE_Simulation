# Sensitivity Analysis: mdd_typical

**Date:** 2026-01-14
**Method:** One-At-a-Time (OAT) perturbation analysis
**Perturbations:** ±10%, ±20%

---

## Executive Summary

- **High-Impact Parameters:** 7
- **Moderate-Impact Parameters:** 3
- **Total Parameters Tested:** 18

### High-Priority Parameters (Need Strong Validation)

- **reward_sensitivity**: 2 high-impact outcomes (max sensitivity: 1.00)
- **rt_variability**: 2 high-impact outcomes (max sensitivity: 1.00)
- **attention_stability**: 2 high-impact outcomes (max sensitivity: 1.00)
- **wm_capacity**: 1 high-impact outcomes (max sensitivity: 1.00)
- **base_accuracy**: 1 high-impact outcomes (max sensitivity: 1.00)

---

## Detailed Results

### reward_sensitivity

- **Baseline Value:** 0.7
- **Max Sensitivity Index:** 1.000
- **Avg Sensitivity Index:** 0.143
- **HIGH Impact Outcomes:** reward_learning
- **MODERATE Impact Outcomes:** reward_learning

### rt_variability

- **Baseline Value:** 0.45
- **Max Sensitivity Index:** 1.000
- **Avg Sensitivity Index:** 0.143
- **HIGH Impact Outcomes:** rt_cv
- **MODERATE Impact Outcomes:** rt_cv

### attention_stability

- **Baseline Value:** 0.6
- **Max Sensitivity Index:** 1.000
- **Avg Sensitivity Index:** 0.143
- **HIGH Impact Outcomes:** sustained_attention
- **MODERATE Impact Outcomes:** sustained_attention

### wm_capacity

- **Baseline Value:** 3.0
- **Max Sensitivity Index:** 1.000
- **Avg Sensitivity Index:** 0.143
- **HIGH Impact Outcomes:** wm_performance
- **MODERATE Impact Outcomes:** wm_performance

### base_accuracy

- **Baseline Value:** 0.85
- **Max Sensitivity Index:** 1.000
- **Avg Sensitivity Index:** 0.139
- **HIGH Impact Outcomes:** mean_accuracy
- **MODERATE Impact Outcomes:** mean_accuracy

### base_rt

- **Baseline Value:** 0.45
- **Max Sensitivity Index:** 1.000
- **Avg Sensitivity Index:** 0.143
- **HIGH Impact Outcomes:** mean_rt
- **MODERATE Impact Outcomes:** mean_rt

### prediction_error_gain

- **Baseline Value:** 0.8
- **Max Sensitivity Index:** 1.000
- **Avg Sensitivity Index:** 0.143
- **HIGH Impact Outcomes:** reward_learning
- **MODERATE Impact Outcomes:** reward_learning

### stress_baseline

- **Baseline Value:** 0.55
- **Max Sensitivity Index:** 0.595
- **Avg Sensitivity Index:** 0.107
- **MODERATE Impact Outcomes:** stress_response

### vigilance_decrement

- **Baseline Value:** 0.015
- **Max Sensitivity Index:** 0.429
- **Avg Sensitivity Index:** 0.061
- **MODERATE Impact Outcomes:** sustained_attention

### stress_reactivity

- **Baseline Value:** 0.75
- **Max Sensitivity Index:** 0.405
- **Avg Sensitivity Index:** 0.058
- **MODERATE Impact Outcomes:** stress_response

### wm_decay_rate

- **Baseline Value:** 0.018
- **Max Sensitivity Index:** 0.220
- **Avg Sensitivity Index:** 0.031

### rt_slowing_rate

- **Baseline Value:** 0.002
- **Max Sensitivity Index:** 0.000
- **Avg Sensitivity Index:** 0.000

### accuracy_decline_rate

- **Baseline Value:** 0.001
- **Max Sensitivity Index:** 0.000
- **Avg Sensitivity Index:** 0.000

### task_switch_cost

- **Baseline Value:** 0.35
- **Max Sensitivity Index:** 0.000
- **Avg Sensitivity Index:** 0.000

### stress_recovery_rate

- **Baseline Value:** 0.015
- **Max Sensitivity Index:** 0.000
- **Avg Sensitivity Index:** 0.000

### positive_affect_baseline

- **Baseline Value:** 0.55
- **Max Sensitivity Index:** 0.000
- **Avg Sensitivity Index:** 0.000

### negative_affect_baseline

- **Baseline Value:** 0.55
- **Max Sensitivity Index:** 0.000
- **Avg Sensitivity Index:** 0.000

### exploration_rate

- **Baseline Value:** 0.25
- **Max Sensitivity Index:** 0.000
- **Avg Sensitivity Index:** 0.000


---

## Interpretation

**Sensitivity Index Interpretation:**
- SI > 1.0: HIGH impact (1% parameter change → >1% outcome change)
- 0.3 < SI < 1.0: MODERATE impact
- SI < 0.3: LOW impact

**Validation Priority:**
1. HIGH-impact parameters need strongest evidence (meta-analyses, large N)
2. MODERATE-impact parameters need good evidence (published studies)
3. LOW-impact parameters can use estimates or theoretical values

