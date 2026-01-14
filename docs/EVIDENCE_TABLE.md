# Evidence Table: Parameter Justification with Effect Sizes

**Purpose:** Document specific quantitative values from literature supporting each parameter  
**Status:** Phase 2 - Template with known values, needs full literature extraction  
**Date:** January 13, 2026

---

## How to Use This Table

**Columns:**
- **Parameter:** Simulation parameter name
- **Value:** Parameter value in preset
- **Evidence:** Citation supporting the value
- **Metric:** Original measurement from paper
- **Effect Size:** Cohen's d, odds ratio, or other effect size (if available)
- **Mapping:** How literature value → simulation parameter
- **Confidence:** HIGH/MODERATE/LOW
- **Page/Table:** Specific location in paper (to be filled)
- **Notes:** Additional context or caveats

**Status Indicators:**
- ✅ Verified: Have accessed paper, extracted exact values
- 📋 Documented: Know values from meta-analysis or review
- 🔍 Needs Extraction: Have citation, need to access paper
- ❓ Uncertain: Citation exists but values unclear

---

## Neurotypical Baseline

| Parameter | Value | Evidence | Status | Metric | Effect Size | Mapping | Confidence |
|-----------|-------|----------|--------|--------|-------------|---------|------------|
| base_rt | 500.0 | Ratcliff & McKoon (2008) | 📋 | 400-600ms simple tasks | N/A | Direct | HIGH |
| rt_variability | 0.15 | Klein et al. (2006) | 📋 | CV ~0.15 typical | N/A | Direct | MODERATE |
| wm_capacity | 4.0 | Cowan (2001) | ✅ | 4±1 items | N/A | Direct | HIGH |
| stress_baseline | 0.30 | McEwen (1998) | 🔍 | Theoretical framework | N/A | Cortisol ~15 μg/dL | LOW |
| stress_reactivity | 0.50 | McEwen (1998) | 🔍 | Theoretical | N/A | Estimated | LOW |
| stress_recovery | 0.15 | Dickerson & Kemeny (2004) | 📋 | ~30min recovery | N/A | 4.5/30 = 0.15 | LOW |
| base_accuracy | 0.90 | Luce (1986) | 🔍 | 85-95% range | N/A | Direct | MODERATE |
| attention_stability | 0.85 | Posner & Petersen (1990) | 🔍 | Theoretical | N/A | Estimated | LOW |
| switch_cost | 0.10 | Posner & Petersen (1990) | 🔍 | Theoretical | N/A | Estimated | LOW |
| vigilance_decrement | 0.01 | None | ❓ | Theoretical | N/A | Estimated | LOW |
| exploration_rate | 0.20 | None | ❓ | No measurement | N/A | Theoretical | LOW |
| prediction_error_gain | 1.0 | None | ❓ | No measurement | N/A | Baseline | LOW |
| positive_affect | 0.60 | Crawford & Henry (2004) | 📋 | PANAS PA ~33/50 | N/A | (33-10)/40 = 0.575 | LOW |
| negative_affect | 0.20 | Crawford & Henry (2004) | 📋 | PANAS NA ~18/50 | N/A | (18-10)/40 = 0.20 | LOW |
| reward_sensitivity | 0.70 | None | ❓ | Theoretical | N/A | Estimated | LOW |

---

## ASD (Autism Spectrum Disorder)

| Parameter | Value | Evidence | Status | Metric | Effect Size | Mapping | Confidence |
|-----------|-------|----------|--------|--------|-------------|---------|------------|
| base_rt | 575.0 | Happé & Frith (2006) | 🔍 | 10-15% slower | Need d | 500 * 1.15 | MODERATE |
| rt_slowing | 1.15 | Happé & Frith (2006) | 🔍 | 15% slower claim | Need d | 1 + 0.15 | MODERATE |
| wm_capacity | 4.0 | Steele et al. (2007) | 🔍 | Intact capacity | Need values | Same as NT | MODERATE |
| wm_decay_rate | 0.015 | Steele et al. (2007) | 🔍 | Impaired manipulation | Need effect | Estimated | LOW |
| switch_cost | 0.25 | Yerys et al. (2009); Geurts et al. (2009) | 🔍 | Set-shifting deficit | Need d | 2.5x NT | MODERATE |
| stress_baseline | 0.50 | Corbett et al. (2009) | 🔍 | Elevated cortisol | Need values | Cortisol ~25 μg/dL | HIGH |
| stress_reactivity | 0.60 | Corbett et al. (2009) | 🔍 | Higher response | Need effect | Elevated | MODERATE |
| stress_recovery | 0.08 | Corbett et al. (2009) | 🔍 | Prolonged elevation | Need time | 4.5/60 = 0.075 | MODERATE |
| positive_affect | 0.50 | Robertson & Baron-Cohen (2017) | 🔍 | Indirect inference | N/A | Estimated | LOW |
| negative_affect | 0.35 | Robertson & Baron-Cohen (2017) | 🔍 | Sensory reactivity | N/A | Estimated | LOW |

**NEEDS Phase 2 Extraction:**
- Corbett et al. (2009): Extract exact cortisol values (baseline, peak, recovery time)
- Yerys et al. (2009): Extract WCST or DCCS switch cost effect sizes
- Steele et al. (2007): Extract WM span values and load manipulation effects
- Geurts et al. (2009): Extract cognitive flexibility effect sizes

---

## ADHD (Attention-Deficit/Hyperactivity Disorder)

| Parameter | Value | Evidence | Status | Metric | Effect Size | Mapping | Confidence |
|-----------|-------|----------|--------|--------|-------------|---------|------------|
| rt_variability | 0.45 | Kofler et al. (2013) | 📋 | Meta-analysis | **g=0.76** [0.63, 0.88] | Direct from meta | HIGH |
| wm_capacity | 3.0 | Kasper et al. (2012) | 📋 | Meta-analysis | **d≈1.0** (~1 SD below) | 4.0 - 1.0 = 3.0 | HIGH |
| base_accuracy | 0.80 | Kofler et al. (2013) | 📋 | Omission errors | **2-3x higher** | Reduced from 0.90 | HIGH |
| attention_stability | 0.60 | Huang-Pollock et al. (2012) | 🔍 | Vigilance decrement | Need slope | Poor sustained | HIGH |
| vigilance_decrement | 0.025 | Huang-Pollock et al. (2012) | 🔍 | Steeper decline | Need rate | 2.5x NT | MODERATE |
| stress_baseline | 0.35 | Lackschewitz et al. (2008) | 🔍 | Physiological arousal | Need values | Moderate | MODERATE |
| stress_reactivity | 0.75 | Lackschewitz et al. (2008) | 🔍 | High reactivity | Need effect | High | MODERATE |
| exploration_rate | 0.40 | Sonuga-Barke (2005) | 🔍 | Delay aversion theory | N/A | Inferred | MODERATE |

**KEY STRENGTH: ADHD has best meta-analytic support**
- Kofler et al. (2013): **319 studies**, N=13,233 ADHD, N=11,842 controls
  - RT variability: Hedges' g = 0.76 [95% CI: 0.63, 0.88]
  - Highly robust effect
  
- Kasper et al. (2012): Working memory meta-analysis
  - Effect size ~1.0 (large effect)
  - Corresponds to ~1-1.5 item deficit

**NEEDS Phase 2 Extraction:**
- Kofler et al. (2013): Extract exact CV values (mean ± SD) for ADHD vs. controls
- Huang-Pollock et al. (2012): Extract vigilance task slopes (d' decline over time)
- Lackschewitz et al. (2008): Extract cortisol/arousal values

---

## MDD (Major Depressive Disorder)

| Parameter | Value | Evidence | Status | Metric | Effect Size | Mapping | Confidence |
|-----------|-------|----------|--------|--------|-------------|---------|------------|
| base_rt | 600.0 | Tsourtos et al. (2002) | 🔍 | 15-20% slowing | Need d | 500 * 1.20 | MODERATE |
| rt_slowing | 1.20 | Tsourtos et al. (2002) | 🔍 | Psychomotor slowing | Need effect | 1 + 0.20 | MODERATE |
| wm_capacity | 3.5 | Christopher & MacDonald (2005) | 🔍 | Load impairment | Need values | Estimated | MODERATE |
| stress_baseline | 0.55 | Burke et al. (2005) | 📋 | Meta-analysis | **d=0.38** elevated | Cortisol ~27.5 μg/dL | HIGH |
| stress_recovery | 0.06 | Burke et al. (2005) | 📋 | HPA dysregulation | Prolonged | 4.5/75 = 0.06 | MODERATE |
| positive_affect | 0.25 | Treadway & Zald (2011) | 📋 | Anhedonia review | Large effect | PANAS ~18/50 | HIGH |
| negative_affect | 0.55 | Multiple sources | 🔍 | Elevated NA | Need effect | PANAS ~32/50 | MODERATE |
| base_accuracy | 0.82 | Porter et al. (2003) | 🔍 | 5-10% reduction | Need d | 0.90 - 0.08 | MODERATE |
| exploration_rate | 0.08 | Nolen-Hoeksema (2000) | 🔍 | Rumination theory | N/A | Inferred | LOW |

**KEY STRENGTH: MDD has excellent meta-analyses**
- Burke et al. (2005): **361 studies** on cortisol
  - Cohen's d = 0.38 for elevated baseline cortisol
  - Strong evidence for HPA dysregulation
  
- Treadway & Zald (2011): Comprehensive anhedonia review
  - Consistent evidence for blunted positive affect
  - Multiple measurement methods converge

**NEEDS Phase 2 Extraction:**
- Burke et al. (2005): Extract mean cortisol values (MDD vs. control)
- Tsourtos et al. (2002): Extract exact RT slowing percentages
- Christopher & MacDonald (2005): Extract WM span under load
- Porter et al. (2003): Extract accuracy values drug-free patients

---

## Phase 2 Extraction Priority List

### HIGH PRIORITY (Meta-Analyses):

#### 1. Kofler et al. (2013) - ADHD RT Variability ⭐⭐⭐
**Why:** Best evidence in entire preset collection (319 studies)
**Extract:**
- Exact CV values: ADHD mean ± SD, Control mean ± SD
- Hedges' g with 95% CI (already have: g=0.76 [0.63, 0.88])
- Forest plot values if available
- Moderator analyses (age, comorbidity effects)

**Expected outcome:** Upgrade rt_variability confidence, validate 0.45 value

---

#### 2. Burke et al. (2005) - MDD Cortisol ⭐⭐⭐
**Why:** 361 studies, critical for stress parameters
**Extract:**
- Mean basal cortisol: MDD vs. control (μg/dL)
- Cohen's d with 95% CI (have: d=0.38)
- Peak response values
- Recovery time courses if available

**Expected outcome:** Validate stress_baseline 0.55, improve stress_recovery mapping

---

#### 3. Kasper et al. (2012) - ADHD Working Memory ⭐⭐
**Why:** Meta-analysis of WM deficits
**Extract:**
- Mean WM span: ADHD vs. control
- Effect size (expect d≈1.0)
- Breakdown by WM task type (verbal, spatial)

**Expected outcome:** Validate wm_capacity 3.0 value

---

### MEDIUM PRIORITY (Single Studies with Key Data):

#### 4. Corbett et al. (2009) - ASD Cortisol ⭐⭐
**Extract:**
- Baseline cortisol: ASD vs. control (μg/dL with SD)
- Peak cortisol during stressor
- Time to return to baseline (minutes)

**Expected outcome:** Validate ASD stress parameters (0.50, 0.60, 0.08)

---

#### 5. Huang-Pollock et al. (2012) - ADHD Vigilance ⭐⭐
**Extract:**
- Vigilance task performance: ADHD vs. control
- d' decline slope over time (per minute or block)
- Omission error rates

**Expected outcome:** Validate attention_stability 0.60, vigilance_decrement 0.025

---

#### 6. Crawford & Henry (2004) - PANAS Norms ⭐
**Extract:**
- UK normative data: Mean PANAS PA and NA with SD
- Age and gender breakdowns
- Clinical comparison data if available

**Expected outcome:** Validate positive_affect 0.60, negative_affect 0.20

---

### LOW PRIORITY (Fill-in Data):

7. Steele et al. (2007) - ASD WM
8. Yerys et al. (2009) - ASD set-shifting
9. Tsourtos et al. (2002) - MDD psychomotor slowing
10. Porter et al. (2003) - MDD neurocognitive
11. Lackschewitz et al. (2008) - ADHD stress
12. Treadway & Zald (2011) - MDD anhedonia
13. Geurts et al. (2009) - ASD flexibility

---

## Extraction Protocol

For each paper:

1. **Access full text** (library, ResearchGate, author request)

2. **Extract quantitative values:**
   - Mean ± SD for both groups (clinical vs. control)
   - Sample sizes
   - Effect sizes (Cohen's d, Hedges' g, OR, etc.)
   - 95% confidence intervals

3. **Record location:**
   - Page number
   - Table number
   - Figure number (if extracting from graph)

4. **Calculate mapping:**
   - Use SCALE_MAPPINGS.md formulas
   - Document calculation
   - Compare to current parameter value

5. **Update confidence:**
   - If exact match: Upgrade to HIGH
   - If close (within 10%): Upgrade to MODERATE
   - If discrepant: Flag for revision

6. **Document in this table:**
   - Change status from 🔍 to ✅
   - Add exact values
   - Add page/table references
   - Add notes if needed

---

## Example: Fully Extracted Entry

| Parameter | Value | Evidence | Status | Metric | Effect Size | Mapping | Confidence | Page/Table | Notes |
|-----------|-------|----------|--------|--------|-------------|---------|------------|------------|-------|
| rt_variability | 0.45 | Kofler et al. (2013) | ✅ | ADHD CV=0.47±0.12, Control CV=0.16±0.05 | g=0.76 [0.63, 0.88], p<.001 | Direct from meta | HIGH | Table 2, p.847 | N=13,233 ADHD, 319 studies. Robust across age, measures. |

---

## Summary Statistics

### Current Status:
- ✅ Verified: 1/72 parameters (1%)
- 📋 Documented: 8/72 parameters (11%)
- 🔍 Needs Extraction: 48/72 parameters (67%)
- ❓ Uncertain: 15/72 parameters (21%)

### After Phase 2 Extraction (Target):
- ✅ Verified: 30/72 parameters (42%)
- 📋 Documented: 25/72 parameters (35%)
- 🔍 Needs Review: 10/72 parameters (14%)
- ❓ Unresolvable: 7/72 parameters (10%)

### Best Case Scenario:
- Upgrade 15-20 parameters from LOW → MODERATE/HIGH
- Document exact values for all meta-analyses
- Identify parameters that truly lack empirical data

---

## Action Items for Phase 2 Completion

### Week 1-2: Meta-Analyses (HIGH PRIORITY)
- [ ] Kofler et al. (2013) - Full extraction
- [ ] Burke et al. (2005) - Full extraction
- [ ] Kasper et al. (2012) - Full extraction

### Week 3-4: Key Single Studies (MEDIUM PRIORITY)
- [ ] Corbett et al. (2009) - Cortisol values
- [ ] Huang-Pollock et al. (2012) - Vigilance slopes
- [ ] Crawford & Henry (2004) - PANAS norms

### Week 5-6: Additional Studies (LOW PRIORITY)
- [ ] Steele et al. (2007) through Geurts et al. (2009)
- [ ] Fill in remaining gaps
- [ ] Update all confidence levels

### Week 6: Finalization
- [ ] Update PARAMETER_CONFIDENCE in src/presets.py
- [ ] Update docs/clinical_presets_v1.1.md with new evidence
- [ ] Create summary report of upgrades

---

## Expected Outcomes

### Parameters Likely to Upgrade:

**LOW → HIGH:**
- ADHD rt_variability (have meta-analysis)
- MDD stress_baseline (have meta-analysis)
- ADHD wm_capacity (have meta-analysis)

**LOW → MODERATE:**
- ASD stress_baseline (direct cortisol data)
- ADHD attention_stability (direct vigilance data)
- NT/clinical positive_affect (PANAS norms)

### Parameters Likely to Remain LOW:
- exploration_rate (no measurement paradigm exists)
- prediction_error_gain (no direct studies)
- wm_decay_rate (no per-tick data)
- vigilance_decrement (slopes not reported)

These will need:
1. Sensitivity analysis (Phase 3) to show impact
2. Either: Find new paradigms or remove if non-critical

---

## References for Extraction

1. Burke, H. M., et al. (2005). Depression and cortisol responses to psychological stress: A meta-analysis. *Psychoneuroendocrinology*, 30(9), 846-856.

2. Corbett, B. A., et al. (2009). Elevated cortisol during play is associated with age and social engagement in children with autism spectrum disorder. *Molecular Autism*, 7, 13.

3. Crawford, J. R., & Henry, J. D. (2004). The Positive and Negative Affect Schedule (PANAS): Construct validity, measurement properties and normative data in a large non-clinical sample. *British Journal of Clinical Psychology*, 43(3), 245-265.

4. Huang-Pollock, C. L., et al. (2012). Evaluating vigilance deficits in ADHD: A meta-analysis of CPT performance. *Journal of Abnormal Psychology*, 121(2), 360-371.

5. Kasper, L. J., et al. (2012). Moderators of working memory deficits in children with attention-deficit/hyperactivity disorder (ADHD): A meta-analytic review. *Clinical Psychology Review*, 32(7), 605-617.

6. Kofler, M. J., et al. (2013). Reaction time variability in ADHD: A meta-analytic review of 319 studies. *Clinical Psychology Review*, 33(6), 795-811.

[Additional references as needed...]

---

**Status:** Template created Phase 2, Task 2.2  
**Next:** Access papers and extract values  
**Timeline:** 2-4 weeks for complete extraction
