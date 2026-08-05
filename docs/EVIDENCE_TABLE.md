# Evidence Table: Parameter Justification with Effect Sizes

**Purpose:** Document specific quantitative values from literature supporting each parameter  
**Status:** Phase 2 - Template with known values, needs full literature extraction  
**Date:** January 13, 2026

> Stress parameters (`stress_baseline`, `stress_reactivity`, `stress_recovery`)
> and Bayesian-PE precision parameters below are consumed by `src/selfmodel.py`.
> See [`SELFMODEL_OPTIMIZATION_PLAN.md`](SELFMODEL_OPTIMIZATION_PLAN.md) for
> why they're tracked separately (a dual stress-update pathway needs fixing
> before the stress rows here can be usefully strengthened) and for the
> precision parameters' validation status, which this table doesn't cover yet.

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
| ----------- | ------- | ---------- | -------- | -------- | ------------- | --------- | ------------ |
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
| positive_affect | 0.60 | Crawford & Henry (2004) | ✅ | PANAS PA = 31.3 (SD 7.7), N=1,003 | N/A | (31.3-10)/40 = 0.53 | MODERATE |
| negative_affect | 0.20 | Crawford & Henry (2004) | ✅ | PANAS NA = 16.0 (SD 5.9), N=1,003 | N/A | (16.0-10)/40 = 0.15 | MODERATE |
| reward_sensitivity | 0.70 | None | ❓ | Theoretical | N/A | Estimated | LOW |

---

## ASD (Autism Spectrum Disorder)

| Parameter | Value | Evidence | Status | Metric | Effect Size | Mapping | Confidence |
| ----------- | ------- | ---------- | -------- | -------- | ------------- | --------- | ------------ |
| base_rt | 575.0 | Happé & Frith (2006) | 🔍 | 10-15% slower | Need d | 500 * 1.15 | MODERATE |
| rt_slowing | 1.15 | Happé & Frith (2006) | 🔍 | 15% slower claim | Need d | 1 + 0.15 | MODERATE |
| wm_capacity | 4.0 | Steele et al. (2007) | 🔍 | Intact capacity | Need values | Same as NT | MODERATE |
| wm_decay_rate | 0.015 | Steele et al. (2007) | 🔍 | Impaired manipulation | Need effect | Estimated | LOW |
| switch_cost | 0.25 | Yerys et al. (2009); Geurts et al. (2009) | 🔍 | Set-shifting deficit | Need d | 2.5x NT | MODERATE |
| stress_baseline | 0.50 | Corbett et al. (2009) | ✅ | No clean ASD>NT ordering at baseline (Fig 4) | n.s. (t(19)=0.54, P=0.60 vs. own home baseline) | Population simplification | MODERATE |
| stress_reactivity | 0.60 | Corbett et al. (2009) | ✅ | Modest S1→S2 rise in ASD subgroups | Qualitative only | Directionally supported | MODERATE |
| stress_recovery | 0.08 | Corbett et al. (2009) | ✅ | Older-ASD fails normal post-peak decline | Diagnosis×Age: β=0.238, SE=0.095 (model χ²(4)=22.76, P<0.0005) | Digitized Fig 4 (older-ASD ~flat S2→S4) | HIGH |
| positive_affect | 0.50 | Robertson & Baron-Cohen (2017) | 🔍 | Indirect inference | N/A | Estimated | LOW |
| negative_affect | 0.35 | Robertson & Baron-Cohen (2017) | 🔍 | Sensory reactivity | N/A | Estimated | LOW |

**NEEDS Phase 2 Extraction:**

- ~~Corbett et al. (2009): Extract exact cortisol values~~ ✅ Done (see
  `extractions/corbett2009_EXTRACTED.md` — paper reports model coefficients + Figure 4
  trajectories, not a raw mean/SD table; digitized and documented)
- Yerys et al. (2009): Extract WCST or DCCS switch cost effect sizes
- Steele et al. (2007): Extract WM span values and load manipulation effects
- Geurts et al. (2009): Extract cognitive flexibility effect sizes

---

## ADHD (Attention-Deficit/Hyperactivity Disorder)

| Parameter | Value | Evidence | Status | Metric | Effect Size | Mapping | Confidence |
| ----------- | ------- | ---------- | -------- | -------- | ------------- | --------- | ------------ |
| rt_variability | 0.45 | Kofler et al. (2013) | ✅ | Meta-analysis, children/adolescents | **g=0.76** [0.68, 0.84] | Direct from meta | HIGH |
| wm_capacity | 3.0 | Kasper et al. (2012) | 🔍 | Meta-analysis (paper inaccessible — no OA copy found) | **d≈1.0** (~1 SD below, unverified) | 4.0 - 1.0 = 3.0 | MODERATE |
| base_accuracy | 0.80 | Huang-Pollock et al. (2012) | ✅ | Mean hit rate: ADHD 0.79 (SD 0.17) vs. control 0.89 (SD 0.12) | δ_omissions=1.34 [0.98,1.69]; d(d′)=0.98 | Hit rate ≈ direct | HIGH |
| attention_stability | 0.60 | Huang-Pollock et al. (2012) | ✅ | POT (performance-over-time) omissions | δ=0.54, small/moderate, k=7, no CI reported | Poor sustained (qualitative) | MODERATE |
| vigilance_decrement | 0.025 | Huang-Pollock et al. (2012) | ✅ | POT omissions/commissions/RT/SDRT | δ=0.22–0.54 (standardized, not a raw slope) | 2.5x NT (qualitative judgment call, no literature slope exists) | MODERATE |
| stress_baseline | 0.35 | Lackschewitz et al. (2008) | 🔍 | Physiological arousal | Need values | Moderate | MODERATE |
| stress_reactivity | 0.75 | Lackschewitz et al. (2008) | 🔍 | High reactivity | Need effect | High | MODERATE |
| exploration_rate | 0.40 | Sonuga-Barke (2005) | 🔍 | Delay aversion theory | N/A | Inferred | MODERATE |

### KEY STRENGTH: ADHD has best meta-analytic support

- Kofler et al. (2013): 319 studies (Tier II: ADHD vs. TD)
  - RT variability: children/adolescents Hedges' g = 0.76 [95% CI: 0.68, 0.84]; adults g = 0.46 [0.31, 0.61]
  - Highly robust effect; age group explains nearly all between-study heterogeneity
  - **Correction (2026-08-04):** CI was previously misquoted as [0.63, 0.88]

- Huang-Pollock et al. (2012): CPT meta-analysis, k=16–39 studies per measure
  - Omissions δ=1.34, commissions δ=0.98, RT δ=0.61, SDRT δ=0.93 (all large)
  - Raw hit rate: ADHD 0.79 (SD 0.17) vs. control 0.89 (SD 0.12) — directly validates base_accuracy
  - POT (vigilance decrement) component weaker: δ=0.22–0.54, fewer studies, no CIs

- Kasper et al. (2012): Working memory meta-analysis — **still unverified**, paper is
  paywalled and no open-access copy could be located. wm_capacity's "d≈1.0" figure
  is unconfirmed pending access (library ILL or author request).

**NEEDS Phase 2 Extraction:**

- ~~Kofler et al. (2013): Extract exact CV values~~ ✅ Done — see
  `extractions/kofler2013_EXTRACTED.md` (note: paper reports only standardized effect
  sizes, not raw mean±SD CV values)
- ~~Huang-Pollock et al. (2012): Extract vigilance task slopes~~ ✅ Done — see
  `extractions/huang-pollock2012_EXTRACTED.md` (note: paper reports standardized POT
  effect sizes, not raw d' decline slopes)
- Kasper et al. (2012): still needs PDF acquisition (paywalled, no OA copy found;
  requires library access or author request)
- Lackschewitz et al. (2008): Extract cortisol/arousal values

---

## MDD (Major Depressive Disorder)

| Parameter | Value | Evidence | Status | Metric | Effect Size | Mapping | Confidence |
| ----------- | ------- | ---------- | -------- | -------- | ------------- | --------- | ------------ |
| base_rt | 600.0 | Tsourtos et al. (2002) | 🔍 | 15-20% slowing | Need d | 500 * 1.20 | MODERATE |
| rt_slowing | 1.20 | Tsourtos et al. (2002) | 🔍 | Psychomotor slowing | Need effect | 1 + 0.20 | MODERATE |
| wm_capacity | 3.5 | Christopher & MacDonald (2005) | 🔍 | Load impairment | Need values | Estimated | MODERATE |
| stress_baseline | 0.55 | Burke et al. (2005) | 📋 | Meta-analysis | **d=0.38** elevated | Cortisol ~27.5 μg/dL | HIGH |
| stress_recovery | 0.06 | Burke et al. (2005) | 📋 | HPA dysregulation | Prolonged | 4.5/75 = 0.06 | MODERATE |
| positive_affect | 0.25 | Treadway & Zald (2011) | 📋 | Anhedonia review | Large effect | PANAS ~18/50 | HIGH |
| negative_affect | 0.55 | Multiple sources | 🔍 | Elevated NA | Need effect | PANAS ~32/50 | MODERATE |
| base_accuracy | 0.82 | Porter et al. (2003) | 🔍 | 5-10% reduction | Need d | 0.90 - 0.08 | MODERATE |
| exploration_rate | 0.08 | Nolen-Hoeksema (2000) | 🔍 | Rumination theory | N/A | Inferred | LOW |

### KEY STRENGTH: MDD has excellent meta-analyses

- Burke et al. (2005): **361 studies** on cortisol — **still unverified**, paper is
  paywalled everywhere checked and no open-access copy could be located
  (ScienceDirect abstract-only; ResearchGate request-only; CiteSeerX unreachable
  from this environment). The d=0.38 figure is unconfirmed pending access.
  - Cohen's d = 0.38 for elevated baseline cortisol (as reported secondhand)
  - Strong evidence for HPA dysregulation (as reported secondhand)

- Treadway & Zald (2011): Comprehensive anhedonia review
  - Consistent evidence for blunted positive affect
  - Multiple measurement methods converge

**NEEDS Phase 2 Extraction:**

- Burke et al. (2005): still needs PDF acquisition (paywalled, no OA copy found;
  requires library access or author request) before mean cortisol values can be extracted
- Tsourtos et al. (2002): Extract exact RT slowing percentages
- Christopher & MacDonald (2005): Extract WM span under load
- Porter et al. (2003): Extract accuracy values drug-free patients

---

## Phase 2 Extraction Priority List

### HIGH PRIORITY (Meta-Analyses)

#### 1. Kofler et al. (2013) - ADHD RT Variability ⭐⭐⭐ ✅ DONE

**Extracted (2026-08-04, see `extractions/kofler2013_EXTRACTED.md`):**

- Paper reports only standardized effect sizes (g), not a raw CV mean±SD table
- Children/adolescents: g=0.76, 95% CI [0.68, 0.84] (corrected from the previously
  misquoted [0.63, 0.88]); adults: g=0.46, 95% CI [0.31, 0.61]
- Paper does NOT report omission-error/accuracy data — the "base_accuracy" citation
  to Kofler was a misattribution; correct source is Huang-Pollock et al. (2012)

**Outcome:** rt_variability confidence confirmed HIGH, CI corrected; base_accuracy
re-cited to Huang-Pollock et al. (2012).

---

#### 2. Burke et al. (2005) - MDD Cortisol ⭐⭐⭐ ❌ STILL BLOCKED

**Status (2026-08-04):** Paper remains inaccessible — paywalled on ScienceDirect,
request-only on ResearchGate, CiteSeerX unreachable from this environment. No
open-access copy located via automated search. d=0.38 and the 361-study count
remain unverified secondhand claims until the paper can be accessed via library
ILL or direct author request.

---

#### 3. Kasper et al. (2012) - ADHD Working Memory ⭐⭐ ❌ STILL BLOCKED

**Status (2026-08-04):** Title/topic in bibliography.md was fabricated (see
corrected citation above) — the real paper ("Moderators of working memory deficits
in children with ADHD: A meta-analytic review", Clin Psychol Rev 32(7):605-617) is
paywalled with no open-access copy found. d≈1.0 remains unverified pending access.

---

### MEDIUM PRIORITY (Single Studies with Key Data)

#### 4. Corbett et al. (2009) - ASD Cortisol ⭐⭐ ✅ DONE

**Extracted (2026-08-01, see `extractions/corbett2009_EXTRACTED.md`):**

- Paper has no raw mean/SD table; only Figure 4 (age×diagnosis trajectories) and
  Table 3 (mixed-model coefficients on log-cortisol)
- No clean baseline elevation for ASD overall — the real effect is age-moderated
  recovery/decline failure in older ASD children (Diagnosis×Age interaction,
  P<0.0005)

**Outcome:** stress_baseline confidence downgraded HIGH→MODERATE (values unchanged);
stress_recovery confidence upgraded MODERATE→HIGH (values unchanged); stress_reactivity
unchanged. See `src/presets.py` PARAMETER_CONFIDENCE comments for rationale.

---

#### 5. Huang-Pollock et al. (2012) - ADHD Vigilance ⭐⭐ ✅ DONE

**Extracted (2026-08-04, see `extractions/huang-pollock2012_EXTRACTED.md`):**

- The previously saved PDF was the wrong paper (Ansell et al. 2012); replaced with
  the correct one via a Wayback Machine archive of PMC3664643
- Hit rate: ADHD 0.79 (SD 0.17) vs. control 0.89 (SD 0.12) — directly validates
  base_accuracy=0.80
- POT (vigilance decrement) effects only small/moderate (δ=0.22-0.54, k=5-7, no CIs)
  — weaker evidence than the overall CPT-deficit component

**Outcome:** base_accuracy re-cited here and upgraded to ✅/HIGH; attention_stability
downgraded HIGH→MODERATE (the strongest evidence in this paper supports
base_accuracy, not attention_stability); vigilance_decrement confirmed MODERATE.

---

#### 6. Crawford & Henry (2004) - PANAS Norms ⭐ ✅ DONE

**Extracted (2026-08-04, see `extractions/crawford2004_EXTRACTED.md`):**

- PA = 31.3 (SD 7.7), NA = 16.0 (SD 5.9), N=1,003 UK general population
- The previously documented "~33/50" and "~18/50" figures were actually Watson et
  al.'s (1988) US student-sample norms, not this paper's own reported values

**Outcome:** positive_affect/negative_affect upgraded to ✅/MODERATE. Recomputed
mapping values (0.53, 0.15) differ modestly from current preset values (0.60, 0.20)
— flagged for a separate decision on whether to adjust the preset.

---

### LOW PRIORITY (Fill-in Data)

1. Steele et al. (2007) - ASD WM
2. Yerys et al. (2009) - ASD set-shifting
3. Tsourtos et al. (2002) - MDD psychomotor slowing
4. Porter et al. (2003) - MDD neurocognitive
5. Lackschewitz et al. (2008) - ADHD stress
6. Treadway & Zald (2011) - MDD anhedonia
7. Geurts et al. (2009) - ASD flexibility

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

An example of a fully extracted row for `rt_variability` (ADHD preset):

- **Value:** 0.45 · **Evidence:** Kofler et al. (2013) · **Status:** ✅
- **Metric:** Meta-analysis, children/adolescents best-case estimate
- **Effect Size:** g=0.76 [0.68, 0.84] · **Mapping:** Direct from meta
- **Confidence:** HIGH · **Page/Table:** Sec. 3.3.4 "Best case estimation"
- **Notes:** 319 studies (Tier II: ADHD vs. TD). Paper reports only standardized
  effect sizes, not a raw CV mean±SD table — earlier drafts of this table showed
  fabricated mean±SD figures that were not in the source paper; they have been removed.

---

## Summary Statistics

### Current Status

- ✅ Verified: 1/72 parameters (1%)
- 📋 Documented: 8/72 parameters (11%)
- 🔍 Needs Extraction: 48/72 parameters (67%)
- ❓ Uncertain: 15/72 parameters (21%)

### After Phase 2 Extraction (Target)

- ✅ Verified: 30/72 parameters (42%)
- 📋 Documented: 25/72 parameters (35%)
- 🔍 Needs Review: 10/72 parameters (14%)
- ❓ Unresolvable: 7/72 parameters (10%)

### Best Case Scenario

- Upgrade 15-20 parameters from LOW → MODERATE/HIGH
- Document exact values for all meta-analyses
- Identify parameters that truly lack empirical data

---

## Action Items for Phase 2 Completion

### Week 1-2: Meta-Analyses (HIGH PRIORITY)

- [x] Kofler et al. (2013) - Full extraction (2026-08-04)
- [ ] Burke et al. (2005) - Full extraction — BLOCKED, paywalled, no OA copy found
- [ ] Kasper et al. (2012) - Full extraction — BLOCKED, paywalled, no OA copy found
      (title also had to be corrected first — see papers/bibliography.md)

### Week 3-4: Key Single Studies (MEDIUM PRIORITY)

- [x] Corbett et al. (2009) - Cortisol values (2026-08-01)
- [x] Huang-Pollock et al. (2012) - Vigilance slopes (2026-08-04; previously-saved PDF
      was the wrong paper and title was corrected — see papers/bibliography.md)
- [x] Crawford & Henry (2004) - PANAS norms (2026-08-04)

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

### Parameters Likely to Upgrade

**LOW → HIGH:**

- ADHD rt_variability (have meta-analysis)
- MDD stress_baseline (have meta-analysis)
- ADHD wm_capacity (have meta-analysis)

**LOW → MODERATE:**

- ASD stress_baseline (direct cortisol data)
- ADHD attention_stability (direct vigilance data)
- NT/clinical positive_affect (PANAS norms)

### Parameters Likely to Remain LOW

- exploration_rate (no measurement paradigm exists)
- prediction_error_gain (no direct studies)
- wm_decay_rate (no per-tick data)
- vigilance_decrement (slopes not reported)

These will need:

1. Sensitivity analysis (Phase 3) to show impact
2. Either: Find new paradigms or remove if non-critical

---

## References for Extraction

1. Burke, H. M., et al. (2005). Depression and cortisol responses to psychological
   stress: A meta-analysis. *Psychoneuroendocrinology*, 30(9), 846-856.

2. Corbett, B. A., et al. (2009). Elevated cortisol during play is associated with age
   and social engagement in children with autism spectrum disorder. *Molecular
   Autism*, 7, 13.

3. Crawford, J. R., & Henry, J. D. (2004). The Positive and Negative Affect Schedule
   (PANAS): Construct validity, measurement properties and normative data in a large
   non-clinical sample. *British Journal of Clinical Psychology*, 43(3), 245-265.

4. Huang-Pollock, C. L., et al. (2012). Evaluating vigilance deficits in ADHD: A
   meta-analysis of CPT performance. *Journal of Abnormal Psychology*, 121(2), 360-371.

5. Kasper, L. J., et al. (2012). Moderators of working memory deficits in children with
   attention-deficit/hyperactivity disorder (ADHD): A meta-analytic review. *Clinical
   Psychology Review*, 32(7), 605-617.

6. Kofler, M. J., et al. (2013). Reaction time variability in ADHD: A meta-analytic
   review of 319 studies. *Clinical Psychology Review*, 33(6), 795-811.

[Additional references as needed...]

---

**Status:** Template created Phase 2, Task 2.2  
**Next:** Access papers and extract values  
**Timeline:** 2-4 weeks for complete extraction
