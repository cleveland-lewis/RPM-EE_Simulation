# Face Validation Report: Clinical Presets

**Date:** 2026-01-14
**Validation Method:** Compare preset parameters to expected clinical patterns

---

## Summary

- **Total Presets Validated:** 4
- **Presets Passing:** 4 ✅
- **Presets Needing Review:** 0 ⚠️

---

## Neurotypical ✅

**Overall Status:** PASS
**Pass Rate:** 100.0% (3/3)

| Parameter | Expectation | Value | Status | Rationale |
|-----------|-------------|-------|--------|-----------|
| wm_capacity | normal | 4.000 | ✅ | Cowan (2001): 4±1 items... |
| rt_variability | low | 0.150 | ✅ | Typical CV ~0.10-0.20... |
| stress_baseline | low | 0.300 | ✅ | Healthy resting cortisol... |

---

## Asd Typical ✅

**Overall Status:** PASS
**Pass Rate:** 100.0% (3/3)

| Parameter | Expectation | Value | Status | Rationale |
|-----------|-------------|-------|--------|-----------|
| stress_reactivity | elevated | 0.600 | ✅ | Corbett et al. (2009): ASD shows 2x cortisol response to soc... |
| attention_stability | inflexible_but_sustained | 0.870 | ✅ | ASD shows hyperfocus, difficulty disengaging (see v1.1 doc)... |
| switch_cost | high | 0.250 | ✅ | Set-shifting deficits in ASD (Hill 2004)... |

---

## Adhd Typical ✅

**Overall Status:** PASS
**Pass Rate:** 100.0% (4/4)

| Parameter | Expectation | Value | Status | Rationale |
|-----------|-------------|-------|--------|-----------|
| rt_variability | very_high | 0.450 | ✅ | Kofler et al. (2013) meta-analysis: 3x variability vs contro... |
| attention_stability | low | 0.600 | ✅ | Sustained attention deficits core to ADHD... |
| vigilance_decrement | steep | 0.025 | ✅ | Rapid performance decline over time (Huang-Pollock 2012)... |
| wm_capacity | reduced | 3.000 | ✅ | Kasper et al. (2012): ~1 SD below controls... |

---

## Mdd Typical ✅

**Overall Status:** PASS
**Pass Rate:** 100.0% (4/4)

| Parameter | Expectation | Value | Status | Rationale |
|-----------|-------------|-------|--------|-----------|
| base_rt | slowed | 600.000 | ✅ | Tsourtos et al. (2002): 15-20% psychomotor slowing... |
| positive_affect | very_low | 0.250 | ✅ | Treadway & Zald (2011): Anhedonia core symptom... |
| stress_baseline | elevated | 0.550 | ✅ | Burke et al. (2005) meta-analysis: Chronic HPA dysregulation... |
| reward_sensitivity | blunted | 0.150 | ✅ | Treadway & Zald (2011): Reduced reward responsiveness in dep... |

---

## Interpretation

### Passing Criteria
- **PASS:** ≥80% of expected patterns matched
- **NEEDS_REVIEW:** <80% match rate

### What This Validates
✅ **Face validity** - Parameters align with clinical expectations from literature
✅ **Pattern consistency** - Each preset shows appropriate clinical profile
✅ **Clinical plausibility** - Values fall within realistic ranges

### What This Does NOT Validate
❌ **Simulation behavior** - Need to run actual simulations (next step)
❌ **Quantitative accuracy** - Need empirical data comparison
❌ **Scale mappings** - Conversion formulas need separate validation

---

## Next Steps

1. **For PASS presets:** Proceed to simulation validation
2. **For NEEDS_REVIEW presets:**
   - Review failed parameters
   - Check literature support
   - Adjust values if needed
   - Re-run validation

---

## Recommendations
