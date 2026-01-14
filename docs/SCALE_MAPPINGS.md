# Parameter Scale Mappings: Literature → Simulation

**Purpose:** Document how empirical measurements are converted to simulation parameters  
**Status:** v1.1.1-preliminary (Phase 2)  
**Date:** January 13, 2026

---

## Overview

Many simulation parameters use normalized 0-1 scales for computational convenience, while empirical literature reports values in various units (ms, μg/dL, scale scores, etc.). This document provides explicit mapping functions to ensure transparency and reproducibility.

**Confidence Levels:**
- 🟢 **Validated:** Mapping verified against multiple studies
- 🟡 **Estimated:** Reasonable linear approximation, needs validation
- 🔴 **Theoretical:** No clear mapping, arbitrary scaling

---

## Response Time Parameters

### base_rt (milliseconds)

**Literature Metric:** Mean RT in milliseconds  
**Simulation Scale:** Direct (milliseconds)  
**Mapping:** DIRECT - No conversion needed

**Confidence:** 🟢 Validated

```python
def literature_to_sim_rt(rt_ms: float) -> float:
    """Direct mapping - use RT value as-is"""
    return rt_ms

# Examples:
literature_to_sim_rt(500)  # 500.0 (NT)
literature_to_sim_rt(575)  # 575.0 (ASD +15%)
literature_to_sim_rt(600)  # 600.0 (MDD +20%)
```

**References:**
- Ratcliff & McKoon (2008): 400-600ms simple tasks
- Tsourtos et al. (2002): 15-20% slowing in MDD

---

### rt_variability (coefficient of variation)

**Literature Metric:** CV = SD/Mean or IIV (intra-individual variability)  
**Simulation Scale:** Direct (proportion, 0-1)  
**Mapping:** DIRECT - Use CV as-is

**Confidence:** 🟢 Validated

```python
def literature_to_sim_rt_variability(cv: float) -> float:
    """
    Convert coefficient of variation to rt_variability.
    CV = SD / Mean
    """
    return cv

# Examples (from Kofler et al. 2013):
literature_to_sim_rt_variability(0.15)  # 0.15 (NT typical)
literature_to_sim_rt_variability(0.45)  # 0.45 (ADHD - meta-analysis)
```

**References:**
- Kofler et al. (2013): ADHD CV = 0.35-0.50 (meta-analysis)
- Klein et al. (2006): NT CV ~0.15

---

### rt_slowing (multiplier)

**Literature Metric:** Percent change from control  
**Simulation Scale:** Multiplier (1.0 = no change)  
**Mapping:** Ratio

**Confidence:** 🟢 Validated

```python
def literature_to_sim_rt_slowing(percent_change: float) -> float:
    """
    Convert percent slowing to multiplier.
    
    Args:
        percent_change: Positive for slowing, negative for speeding
        e.g., 15 means 15% slower, -5 means 5% faster
    """
    return 1.0 + (percent_change / 100.0)

# Examples:
literature_to_sim_rt_slowing(0)    # 1.0 (NT - no change)
literature_to_sim_rt_slowing(15)   # 1.15 (ASD - 15% slower)
literature_to_sim_rt_slowing(20)   # 1.20 (MDD - 20% slower)
literature_to_sim_rt_slowing(4)    # 1.04 (ADHD - 4% slower)
```

---

## Working Memory Parameters

### wm_capacity (number of items)

**Literature Metric:** Memory span (digit span, spatial span)  
**Simulation Scale:** Direct (number of items)  
**Mapping:** DIRECT - Use span value

**Confidence:** 🟢 Validated

```python
def literature_to_sim_wm_capacity(span: float) -> float:
    """Direct mapping - use span as-is"""
    return span

# Examples (from Cowan 2001, Kasper 2012):
literature_to_sim_wm_capacity(4.0)   # 4.0 (NT - Cowan consensus)
literature_to_sim_wm_capacity(3.0)   # 3.0 (ADHD - 1 item deficit)
literature_to_sim_wm_capacity(3.5)   # 3.5 (MDD - 0.5 item deficit)
```

**References:**
- Cowan (2001): NT = 4±1 items
- Kasper et al. (2012): ADHD ~1-1.5 items below controls

---

### wm_decay_rate (per-tick decay)

**Literature Metric:** None directly - inferred from load effects  
**Simulation Scale:** Rate of decay per simulation tick (0-1)  
**Mapping:** 🔴 THEORETICAL - Estimated from performance under load

**Confidence:** 🔴 Theoretical (needs validation)

```python
def literature_to_sim_wm_decay(load_effect_percent: float) -> float:
    """
    Estimate decay rate from performance decline under load.
    
    CAUTION: This is a rough approximation with no validation.
    
    Args:
        load_effect_percent: Performance decline (e.g., 10 = 10% worse)
    
    Returns:
        Estimated per-tick decay rate
    """
    # Heuristic: 10% load effect ≈ 0.01 decay rate
    # This is ARBITRARY and needs empirical validation
    return load_effect_percent / 1000.0

# Examples (THEORETICAL):
literature_to_sim_wm_decay(10)   # 0.01 (NT - estimated)
literature_to_sim_wm_decay(15)   # 0.015 (ASD - estimated)
literature_to_sim_wm_decay(18)   # 0.018 (ADHD - estimated)
literature_to_sim_wm_decay(22)   # 0.022 (MDD - estimated)
```

**⚠️ WARNING:** This mapping is purely theoretical. Literature does not provide per-tick decay rates. Values are estimated to produce realistic load effects but lack empirical grounding.

**TODO for Phase 3:** Validate decay rates against empirical load manipulation studies.

---

## Stress Parameters

### stress_baseline (0-1 normalized)

**Literature Metric:** Basal cortisol (μg/dL) or perceived stress scale  
**Simulation Scale:** Normalized 0-1 (0=none, 1=maximum)  
**Mapping:** Linear approximation

**Confidence:** 🟡 Estimated (needs validation)

```python
def cortisol_to_stress_baseline(cortisol_ugdl: float, 
                                  min_cortisol: float = 0.0,
                                  max_cortisol: float = 50.0) -> float:
    """
    Convert basal cortisol to normalized stress baseline.
    
    Args:
        cortisol_ugdl: Basal cortisol in μg/dL
        min_cortisol: Theoretical minimum (default 0)
        max_cortisol: Clinical severe (default 50)
        
    Returns:
        Normalized stress baseline (0-1)
        
    Rationale:
        - Healthy adults: 10-20 μg/dL → 0.20-0.40
        - Clinical populations: 25-40 μg/dL → 0.50-0.80
        - Extreme stress: >50 μg/dL → ~1.0
    """
    return min(1.0, max(0.0, (cortisol_ugdl - min_cortisol) / (max_cortisol - min_cortisol)))

# Examples (from Burke et al. 2005, Corbett et al. 2009):
cortisol_to_stress_baseline(15)   # 0.30 (NT - healthy baseline)
cortisol_to_stress_baseline(25)   # 0.50 (ASD - elevated)
cortisol_to_stress_baseline(17.5) # 0.35 (ADHD - moderate)
cortisol_to_stress_baseline(27.5) # 0.55 (MDD - elevated)
```

**Alternative:** Perceived Stress Scale (PSS)

```python
def pss_to_stress_baseline(pss_score: float) -> float:
    """
    Convert PSS-10 score to stress baseline.
    
    PSS-10 range: 0-40
    0-13: Low stress
    14-26: Moderate stress
    27-40: High stress
    """
    return min(1.0, pss_score / 40.0)

# Examples:
pss_to_stress_baseline(12)  # 0.30 (NT - low stress)
pss_to_stress_baseline(20)  # 0.50 (ASD - moderate-high)
pss_to_stress_baseline(22)  # 0.55 (MDD - high)
```

**References:**
- Burke et al. (2005): MDD cortisol meta-analysis
- Corbett et al. (2009): ASD cortisol elevation
- Cohen et al. (1983): Perceived Stress Scale

---

### stress_recovery (recovery rate, 0-1)

**Literature Metric:** Time to return to baseline cortisol (minutes)  
**Simulation Scale:** Per-tick recovery rate (higher = faster)  
**Mapping:** Inverse relationship

**Confidence:** 🟡 Estimated (needs validation)

```python
def recovery_time_to_rate(time_minutes: float, 
                          simulation_ticks_per_minute: float = 1.0) -> float:
    """
    Convert cortisol recovery time to per-tick recovery rate.
    
    Args:
        time_minutes: Time to return to baseline
        simulation_ticks_per_minute: Temporal resolution
        
    Returns:
        Per-tick recovery rate
        
    Rationale:
        If recovery takes T minutes, each tick should reduce stress by ~1/T
        to reach baseline in T ticks.
        
        Formula: rate ≈ k / time_minutes
        where k is calibration constant (default: 4.5)
    """
    k = 4.5  # Calibration constant to produce reasonable values
    return k / time_minutes

# Examples (from Dickerson & Kemeny 2004):
recovery_time_to_rate(30)   # 0.15 (NT - fast recovery)
recovery_time_to_rate(40)   # 0.11 (ADHD - moderate)
recovery_time_to_rate(60)   # 0.075 (ASD - slow)
recovery_time_to_rate(75)   # 0.06 (MDD - very slow)
```

**⚠️ WARNING:** The calibration constant (k=4.5) is empirically tuned to produce values in the 0.05-0.15 range. This needs validation against actual recovery trajectories.

**References:**
- Dickerson & Kemeny (2004): Stress recovery meta-analysis
- Miller et al. (2013): HPA recovery in depression

---

### stress_reactivity (0-1 normalized)

**Literature Metric:** Peak cortisol response to stressor (μg/dL increase)  
**Simulation Scale:** Sensitivity multiplier (0-1)  
**Mapping:** Linear approximation

**Confidence:** 🟡 Estimated

```python
def cortisol_response_to_reactivity(peak_increase_ugdl: float,
                                     max_response: float = 20.0) -> float:
    """
    Convert peak cortisol response to reactivity parameter.
    
    Args:
        peak_increase_ugdl: Peak cortisol increase from baseline
        max_response: Maximum expected response (default 20)
        
    Returns:
        Reactivity parameter (0-1)
    """
    return min(1.0, peak_increase_ugdl / max_response)

# Examples:
cortisol_response_to_reactivity(10)   # 0.50 (NT - moderate)
cortisol_response_to_reactivity(12)   # 0.60 (ASD - elevated)
cortisol_response_to_reactivity(15)   # 0.75 (ADHD - high)
cortisol_response_to_reactivity(13)   # 0.65 (MDD - elevated)
```

---

## Attention / Executive Function Parameters

### attention_stability (0-1 normalized)

**Literature Metric:** Sustained attention performance over time  
**Simulation Scale:** Proportion of stable attention (0-1)  
**Mapping:** 🟡 ESTIMATED from vigilance task performance

**Confidence:** 🟡 Estimated

```python
def vigilance_performance_to_stability(accuracy_percent: float) -> float:
    """
    Convert vigilance task accuracy to attention stability.
    
    Args:
        accuracy_percent: Mean accuracy on sustained attention task
        
    Returns:
        Stability parameter (0-1)
    """
    return accuracy_percent / 100.0

# Examples:
vigilance_performance_to_stability(85)  # 0.85 (NT)
vigilance_performance_to_stability(80)  # 0.80 (ASD)
vigilance_performance_to_stability(60)  # 0.60 (ADHD)
vigilance_performance_to_stability(65)  # 0.65 (MDD)
```

**References:**
- Huang-Pollock et al. (2012): ADHD vigilance performance

---

### switch_cost (0-1 normalized)

**Literature Metric:** RT switch cost (ms or %)  
**Simulation Scale:** Normalized cost (0-1)  
**Mapping:** 🟡 ESTIMATED - percent increase normalized

**Confidence:** 🟡 Estimated

```python
def rt_switch_cost_to_param(switch_cost_percent: float,
                              max_cost: float = 50.0) -> float:
    """
    Convert RT switch cost to parameter.
    
    Args:
        switch_cost_percent: RT increase on switch trials (%)
        max_cost: Maximum expected cost (default 50%)
        
    Returns:
        Switch cost parameter (0-1)
    """
    return min(1.0, switch_cost_percent / max_cost)

# Examples:
rt_switch_cost_to_param(10)   # 0.10 (NT - 10% cost)
rt_switch_cost_to_param(25)   # 0.25 (ASD - high cost)
rt_switch_cost_to_param(8)    # 0.08 (ADHD - low cost, hyper-switching)
rt_switch_cost_to_param(18)   # 0.18 (MDD - moderate-high)
```

**TODO Phase 2:** Find task-switching meta-analysis for validated values.

---

### vigilance_decrement (per-tick rate)

**Literature Metric:** Performance decline slope over time  
**Simulation Scale:** Per-tick decrement rate  
**Mapping:** 🔴 THEORETICAL

**Confidence:** 🔴 Theoretical

```python
def vigilance_slope_to_decrement(accuracy_decline_per_minute: float,
                                   ticks_per_minute: float = 1.0) -> float:
    """
    Convert vigilance decline slope to per-tick decrement.
    
    CAUTION: Highly theoretical, no direct empirical mapping.
    
    Args:
        accuracy_decline_per_minute: Accuracy loss per minute (%)
        ticks_per_minute: Temporal resolution
        
    Returns:
        Per-tick decrement rate
    """
    return accuracy_decline_per_minute / 100.0 / ticks_per_minute

# Examples (THEORETICAL):
vigilance_slope_to_decrement(1)    # 0.01 (NT - slow decline)
vigilance_slope_to_decrement(0.8)  # 0.008 (ASD - slower)
vigilance_slope_to_decrement(2.5)  # 0.025 (ADHD - fast decline)
vigilance_slope_to_decrement(2.0)  # 0.02 (MDD - moderate-fast)
```

**⚠️ WARNING:** No empirical studies provide per-minute decline slopes. These values are tuned to produce realistic behavior over simulation runs.

---

## Affect / Emotional Parameters

### positive_affect / negative_affect (0-1 normalized)

**Literature Metric:** PANAS (Positive and Negative Affect Schedule)  
**Simulation Scale:** Normalized 0-1  
**Mapping:** Linear from PANAS scale

**Confidence:** 🟡 Estimated (mapping reasonable but unvalidated)

```python
def panas_to_affect(panas_score: float,
                     min_score: float = 10.0,
                     max_score: float = 50.0) -> float:
    """
    Convert PANAS score to normalized affect parameter.
    
    PANAS scale:
    - Range: 10-50 for each subscale (Positive, Negative)
    - 10 items, each rated 1-5
    
    Args:
        panas_score: PANAS subscale score (10-50)
        min_score: Scale minimum (10)
        max_score: Scale maximum (50)
        
    Returns:
        Normalized affect (0-1)
    """
    return (panas_score - min_score) / (max_score - min_score)

# Positive Affect Examples (from Watson et al. 1988, Crawford & Henry 2004):
panas_to_affect(35)   # 0.625 ≈ 0.60 (NT - moderate-high positive)
panas_to_affect(30)   # 0.50 (ASD - moderate)
panas_to_affect(32)   # 0.55 (ADHD - moderate)
panas_to_affect(18)   # 0.20 (MDD - anhedonia, very low)

# Negative Affect Examples:
panas_to_affect(18)   # 0.20 (NT - low negative)
panas_to_affect(24)   # 0.35 (ASD - elevated)
panas_to_affect(22)   # 0.30 (ADHD - moderate)
panas_to_affect(32)   # 0.55 (MDD - high negative)
```

**References:**
- Watson et al. (1988): PANAS development and validation
- Crawford & Henry (2004): UK norms, NT mean PA=33, NA=18
- Khazanov & Ruscio (2016): Anhedonia in depression meta-analysis

---

### reward_sensitivity (0-1 normalized)

**Literature Metric:** BAS (Behavioral Activation System) scales, probabilistic reward task  
**Simulation Scale:** Normalized 0-1  
**Mapping:** 🔴 THEORETICAL - no clear conversion

**Confidence:** 🔴 Theoretical

```python
def bas_to_reward_sensitivity(bas_score: float,
                                min_score: float = 13.0,
                                max_score: float = 52.0) -> float:
    """
    Convert BAS total score to reward sensitivity.
    
    BAS total range: 13-52 (sum of 3 subscales)
    
    CAUTION: This mapping is theoretical and unvalidated.
    """
    return (bas_score - min_score) / (max_score - min_score)

# Examples (THEORETICAL):
bas_to_reward_sensitivity(40)   # 0.69 ≈ 0.70 (NT)
bas_to_reward_sensitivity(35)   # 0.56 ≈ 0.55 (ASD - reduced)
bas_to_reward_sensitivity(45)   # 0.82 ≈ 0.85 (ADHD - elevated)
bas_to_reward_sensitivity(28)   # 0.38 ≈ 0.35 (MDD - blunted)
```

**⚠️ WARNING:** Reward sensitivity is complex and multifaceted. BAS scores don't directly map to simulation parameters. These values are rough estimates.

**TODO Phase 2:** Find probabilistic reward task meta-analysis for better quantification.

---

## Prediction / Learning Parameters

### exploration_rate (0-1 proportion)

**Literature Metric:** NONE - No direct measurement exists  
**Simulation Scale:** Proportion of exploratory actions (0-1)  
**Mapping:** 🔴 THEORETICAL - Inferred from related constructs

**Confidence:** 🔴 Theoretical (no empirical grounding)

```python
# NO EMPIRICAL MAPPING EXISTS

# Values are theoretical estimates based on:
# - ADHD: Delay aversion → high exploration
# - MDD: Rumination → low exploration
# - ASD: Inflexibility → low exploration
# - NT: Balanced

exploration_rate_estimates = {
    'neurotypical': 0.20,  # Moderate, balanced
    'asd_typical': 0.12,   # Low (reduced flexibility)
    'adhd_typical': 0.40,  # High (impulsivity, delay aversion)
    'mdd_typical': 0.08,   # Very low (rumination, anhedonia)
}
```

**⚠️ CRITICAL:** This parameter has NO direct empirical measurement in any cited study. Values are educated guesses based on:
- Delay aversion in ADHD (Sonuga-Barke, 2005)
- Rumination in MDD (Nolen-Hoeksema, 2000)
- Cognitive inflexibility in ASD (Geurts et al., 2009)

**TODO Phase 3:** Develop paradigm to measure exploration rate directly, or remove parameter if not critical.

---

### prediction_error_gain (learning rate multiplier)

**Literature Metric:** NONE - No direct measurement exists  
**Simulation Scale:** Learning rate multiplier (0-2)  
**Mapping:** 🔴 THEORETICAL

**Confidence:** 🔴 Theoretical

```python
# NO EMPIRICAL MAPPING EXISTS

# Values are theoretical estimates based on:
# - ADHD: Over-reactivity → high gain
# - MDD: Blunted learning → low gain
# - Others: Near baseline

prediction_error_gain_estimates = {
    'neurotypical': 1.0,   # Baseline
    'asd_typical': 0.90,   # Slightly reduced (detail focus)
    'adhd_typical': 1.20,  # Elevated (over-reactivity)
    'mdd_typical': 0.70,   # Reduced (blunted learning)
}
```

**⚠️ CRITICAL:** This parameter has NO direct empirical grounding. It's inferred from general learning impairments but no study quantifies "prediction error gain" specifically.

**TODO Phase 3:** Either:
1. Find computational psychiatry studies with RL model fits
2. Conduct validation study with prediction error paradigm
3. Remove parameter if sensitivity analysis shows low impact

---

## Accuracy Parameters

### base_accuracy (0-1 proportion correct)

**Literature Metric:** Mean accuracy on cognitive tasks (%)  
**Simulation Scale:** Proportion (0-1)  
**Mapping:** DIRECT

**Confidence:** 🟢 Validated

```python
def accuracy_percent_to_proportion(accuracy_percent: float) -> float:
    """Direct conversion from percent to proportion"""
    return accuracy_percent / 100.0

# Examples:
accuracy_percent_to_proportion(90)  # 0.90 (NT)
accuracy_percent_to_proportion(88)  # 0.88 (ASD)
accuracy_percent_to_proportion(80)  # 0.80 (ADHD - higher errors)
accuracy_percent_to_proportion(82)  # 0.82 (MDD - reduced)
```

---

### accuracy_decline (proportion, 0-1)

**Literature Metric:** Performance decline under load (%)  
**Simulation Scale:** Proportion decline (0-1)  
**Mapping:** Direct

**Confidence:** 🟡 Estimated

```python
def load_effect_to_decline(decline_percent: float) -> float:
    """Convert percent decline under load to parameter"""
    return decline_percent / 100.0

# Examples:
load_effect_to_decline(5)   # 0.05 (NT - 5% decline)
load_effect_to_decline(8)   # 0.08 (ASD)
load_effect_to_decline(12)  # 0.12 (ADHD - steep decline)
load_effect_to_decline(10)  # 0.10 (MDD)
```

---

## Summary: Confidence by Parameter Type

### 🟢 HIGH CONFIDENCE (Direct Mappings):
- ✅ base_rt - Direct from literature (ms)
- ✅ rt_variability - Direct CV from meta-analyses
- ✅ rt_slowing - Direct percent change
- ✅ wm_capacity - Direct span values
- ✅ base_accuracy - Direct accuracy percentages

### 🟡 MODERATE CONFIDENCE (Estimated Linear Mappings):
- ⚠️ stress_baseline - Cortisol/PSS with linear mapping (needs validation)
- ⚠️ stress_recovery - Inverse time mapping (needs validation)
- ⚠️ stress_reactivity - Peak response mapping
- ⚠️ attention_stability - From vigilance performance
- ⚠️ switch_cost - Percent cost normalized
- ⚠️ positive/negative_affect - PANAS linear mapping
- ⚠️ accuracy_decline - Load effect percentages

### 🔴 LOW CONFIDENCE (Theoretical / No Clear Mapping):
- ❌ wm_decay_rate - NO direct measure, tuned empirically
- ❌ vigilance_decrement - NO slope data, theoretical
- ❌ reward_sensitivity - NO clear mapping from BAS
- ❌ exploration_rate - NO empirical measurement
- ❌ prediction_error_gain - NO empirical measurement

---

## Validation Priorities (Phase 3)

### High Priority:
1. **Validate stress mappings** - Compare cortisol→stress against PSS data
2. **Validate affect mappings** - Test PANAS→affect against simulation behavior
3. **Find exploration paradigm** - Or demonstrate parameter is non-critical

### Medium Priority:
4. Validate switch cost mapping against task-switching meta-analysis
5. Validate recovery rate against empirical recovery trajectories
6. Document attention stability from multiple vigilance studies

### Low Priority (or remove):
7. wm_decay_rate - Consider removing or simplifying
8. vigilance_decrement - Test if constant rate is sufficient
9. prediction_error_gain - Sensitivity analysis, remove if low impact

---

## Usage

```python
from docs.SCALE_MAPPINGS import cortisol_to_stress_baseline, panas_to_affect

# Example: New empirical data for hypothetical disorder
new_disorder_cortisol = 32  # μg/dL
new_disorder_panas_positive = 25  # PANAS PA score

stress_baseline = cortisol_to_stress_baseline(new_disorder_cortisol)
positive_affect = panas_to_affect(new_disorder_panas_positive)

print(f"Stress baseline: {stress_baseline:.2f}")  # 0.64
print(f"Positive affect: {positive_affect:.2f}")   # 0.38
```

---

## References

### Stress / HPA Axis:
- Burke et al. (2005). Depression and cortisol responses to psychological stress: A meta-analysis
- Dickerson & Kemeny (2004). Acute stressors and cortisol responses: A theoretical integration and synthesis of laboratory research
- Cohen et al. (1983). A global measure of perceived stress
- Corbett et al. (2009). Elevated cortisol during play in children with autism

### Affect:
- Watson et al. (1988). Development and validation of brief measures of positive and negative affect: The PANAS scales
- Crawford & Henry (2004). The positive and negative affect schedule (PANAS): Construct validity, measurement properties and normative data in a large non-clinical sample
- Khazanov & Ruscio (2016). Is low positive emotionality a specific risk factor for depression? A meta-analysis of longitudinal studies

### Working Memory:
- Cowan (2001). The magical number 4 in short-term memory
- Kasper et al. (2012). Moderators of working memory deficits in children with ADHD

### Attention:
- Huang-Pollock et al. (2012). Evaluating vigilance deficits in ADHD
- Kofler et al. (2013). Reaction time variability in ADHD: A meta-analytic review

---

**Last Updated:** January 13, 2026 (Phase 2, Task 2.3)  
**Next Update:** After Phase 3 validation studies
