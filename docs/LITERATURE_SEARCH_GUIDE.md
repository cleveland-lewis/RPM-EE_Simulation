# Literature Search Guide: Strengthening Parameter Evidence

**Purpose:** Identify additional sources to upgrade LOW confidence parameters  
**Status:** Phase 2, Task 2.1  
**Target:** Upgrade 15-20 parameters from LOW → MODERATE/HIGH  
**Date:** January 14, 2026

---

## Search Strategy Overview

**Focus Areas:**
1. Meta-analyses for parameters currently using single studies
2. Task-switching studies for switch_cost parameters
3. Vigilance meta-analysis for decrement rates
4. Affect/reward measures in clinical populations
5. Stress recovery time-course studies

**Databases:**
- PubMed/MEDLINE
- PsycINFO
- Web of Science
- Google Scholar (for citation tracking)

**Search Period:** 2000-2025 (prefer recent meta-analyses)

---

## Priority 1: Parameters with LOW Confidence (Need Immediate Upgrade)

### 1.1 Task-Switching / Attentional Control

**Current Problem:**
- `switch_cost` parameters: All LOW confidence, theoretical estimates
- Based on Posner & Petersen (1990) framework only
- No quantitative values from task-switching literature

**Target:** Find task-switching meta-analysis

**Search Terms:**
```
PubMed: ("task switching"[Title/Abstract] OR "set shifting"[Title/Abstract] 
         OR "cognitive flexibility"[Title/Abstract]) 
        AND ("meta-analysis"[Title] OR "meta-analytic"[Title/Abstract])

Additional: "attentional control" AND "switch cost" AND (autism OR ADHD OR depression)
```

**Recommended Papers to Find:**

1. **Vandierendonck, A., Liefooghe, B., & Verbruggen, F. (2010)**
   - "Task switching: Interplay of reconfiguration and interference control"
   - *Psychological Bulletin*, 136(4), 601-626
   - Why: Comprehensive review of switch costs
   - Extract: Mean switch costs (ms or %), effect sizes by population

2. **Kiesel, A., et al. (2010)**
   - "Control and interference in task switching—A review"  
   - *Psychological Research*, 74(6), 525-529
   - Why: Recent synthesis of switch cost literature
   - Extract: Typical switch costs in healthy adults, clinical comparisons

3. **Meiran, N., Kessler, Y., & Adi-Japha, E. (2008)**
   - "Control by action representation and input selection (CARIS): A theoretical framework"
   - Why: Theoretical + empirical switch cost data
   - Extract: Quantitative models, typical ranges

**What to Extract:**
- Mean switch cost in NT: ____ ms or _____%
- Mean switch cost in ASD: ____ ms or _____ % (effect size: d=___)
- Mean switch cost in ADHD: ____ ms (predict: lower, hyper-switching)
- Mean switch cost in MDD: ____ ms (predict: higher, cognitive slowing)

**Expected Improvement:**
- `switch_cost` LOW → MODERATE (all 4 presets)
- If meta-analysis found: MODERATE → HIGH

---

### 1.2 Vigilance Decrements

**Current Problem:**
- `vigilance_decrement` rates: All LOW confidence
- No empirical time-course data
- Theoretical estimates: 0.01 (NT), 0.025 (ADHD), etc.

**Target:** Find vigilance meta-analysis with decline slopes

**Search Terms:**
```
PubMed: ("vigilance"[Title] OR "sustained attention"[Title]) 
        AND ("decrement"[Title/Abstract] OR "time on task"[Title/Abstract])
        AND ("meta-analysis"[Title] OR "review"[Title])

Additional: "continuous performance" AND "vigilance decline" AND slope
```

**Recommended Papers:**

1. **See, J. E., Howe, S. R., Warm, J. S., & Dember, W. N. (1995)**
   - "Meta-analysis of the sensitivity decrement in vigilance"
   - *Psychological Bulletin*, 117(2), 230-249
   - Why: Classic meta-analysis of vigilance decline
   - Extract: d' decline slopes per minute/block

2. **Thomson, D. R., Besner, D., & Smilek, D. (2015)**
   - "A resource-control account of sustained attention: Evidence from mind-wandering"
   - *Perspectives on Psychological Science*, 10(1), 82-96
   - Why: Modern synthesis with quantitative models
   - Extract: Performance decline rates

3. **Warm, J. S., Parasuraman, R., & Matthews, G. (2008)**
   - "Vigilance requires hard mental work and is stressful"
   - *Human Factors*, 50(3), 433-441
   - Why: Comprehensive review with decline data
   - Extract: d' or accuracy decline per unit time

**What to Extract:**
- NT vigilance decline: ____% per minute (or per block)
- ADHD vigilance decline: ____% per minute (should be steeper)
- Linear vs. exponential decline?
- Effect sizes for clinical vs. control

**Conversion Formula:**
```python
vigilance_decrement = (percent_decline_per_minute / 100.0) / ticks_per_minute
```

**Expected Improvement:**
- `vigilance_decrement` LOW → MODERATE (all presets)
- If NT slope found: Can calculate clinical multiples (ADHD = 2.5x NT)

---

### 1.3 Stress Recovery Rates

**Current Problem:**
- `stress_recovery` rates: All LOW confidence
- Based on inverse time mapping (k=4.5/time)
- Calibration constant arbitrary

**Target:** Find studies with cortisol recovery time-courses

**Search Terms:**
```
PubMed: ("cortisol"[Title] OR "HPA axis"[Title]) 
        AND ("recovery"[Title/Abstract] OR "time course"[Title/Abstract])
        AND ("acute stress" OR "stressor")
        AND ("minutes" OR "trajectory")

Additional: "cortisol recovery" AND (autism OR ADHD OR depression) AND time
```

**Recommended Papers:**

1. **Dickerson, S. S., & Kemeny, M. E. (2004)**
   - "Acute stressors and cortisol responses: A theoretical integration"
   - *Psychological Bulletin*, 130(3), 355-391
   - Why: Meta-analysis with recovery trajectories
   - Extract: Mean time to baseline by stressor type

2. **Miller, R., et al. (2013)**
   - "The CIRCORT database: Reference ranges for cortisol in healthy subjects"
   - *Stress*, 16(3), 269-299
   - Why: Normative cortisol trajectories
   - Extract: Recovery slopes (μg/dL per minute)

3. **Het, S., Rohleder, N., Schoofs, D., Kirschbaum, C., & Wolf, O. T. (2009)**
   - "Neuroendocrine and psychometric evaluation of a placebo version of the TSST"
   - *Psychoneuroendocrinology*, 34(7), 1075-1086
   - Why: Detailed time-course data
   - Extract: Cortisol at 0, +10, +20, +30, +40, +60 min post-stress

**What to Extract:**
- NT recovery time: ____ minutes to baseline
- ASD recovery time: ____ minutes (predict: longer)
- MDD recovery time: ____ minutes (predict: much longer)
- Recovery slope: ____ μg/dL per minute

**Validation:**
- Plot actual recovery curves vs. simulation exponential decay
- Adjust k parameter to match empirical trajectories
- Test if linear rate matches exponential decay reasonably

**Expected Improvement:**
- `stress_recovery` LOW → MODERATE (all presets)
- Validated calibration constant (replace k=4.5 with empirical)

---

### 1.4 Affect Parameters in Clinical Populations

**Current Problem:**
- `positive_affect`, `negative_affect`: LOW confidence
- Based on general PANAS norms (Crawford & Henry 2004)
- Need clinical population PANAS data

**Target:** Find PANAS studies in ASD, ADHD, MDD samples

**Search Terms:**
```
PubMed: ("PANAS"[Title/Abstract] OR "positive affect"[Title/Abstract]) 
        AND ("autism" OR "ASD" OR "ADHD" OR "depression" OR "MDD")
        AND ("mean" OR "score")

PsycINFO: PANAS AND (autism OR ADHD OR depression) AND empirical
```

**Recommended Papers:**

1. **Samson, A. C., et al. (2015)**
   - "Emotion dysregulation and the core features of autism spectrum disorder"
   - *Journal of Autism and Developmental Disorders*, 45(5), 1405-1416
   - Why: PANAS in ASD sample
   - Extract: PANAS PA and NA means ± SD

2. **Mitchell, R. L., & Phillips, L. H. (2007)**
   - "The psychological, neurochemical and functional neuroanatomical mediators of ADHD"
   - *Neuroscience & Biobehavioral Reviews*, 31(1), 42-59
   - Why: Review including affect measures
   - Extract: Any PANAS or affect scale data

3. **Khazanov, G. K., & Ruscio, A. M. (2016)**
   - "Is low positive emotionality a specific risk factor for depression?"
   - *Psychological Bulletin*, 142(9), 991-1015
   - Why: Meta-analysis of PA in depression
   - Extract: Meta-analytic mean PANAS PA in MDD vs. controls

**What to Extract:**
- NT PANAS PA: 33 ± 7 (Crawford & Henry, already have)
- ASD PANAS PA: ____ ± ____ (predict: lower, ~28-30)
- ADHD PANAS PA: ____ ± ____ (predict: moderate, ~30-32)
- MDD PANAS PA: ____ ± ____ (predict: very low, ~18-20, anhedonia)

- NT PANAS NA: 18 ± 6 (Crawford & Henry, already have)
- ASD PANAS NA: ____ ± ____ (predict: elevated, ~24-28)
- ADHD PANAS NA: ____ ± ____ (predict: moderate, ~22-24)
- MDD PANAS NA: ____ ± ____ (predict: high, ~28-35)

**Expected Improvement:**
- `positive_affect`, `negative_affect` LOW → MODERATE (all presets)

---

### 1.5 Reward Sensitivity

**Current Problem:**
- `reward_sensitivity`: All LOW confidence
- No clear BAS → simulation mapping
- Need probabilistic reward task data

**Target:** Find reward processing studies in clinical populations

**Search Terms:**
```
PubMed: ("reward sensitivity"[Title/Abstract] OR "probabilistic reward"[Title]) 
        AND ("autism" OR "ADHD" OR "depression")
        AND ("task" OR "behavioral")

Additional: "BAS" AND "behavioral activation" AND (ADHD OR depression)
```

**Recommended Papers:**

1. **Pizzagalli, D. A., et al. (2005)**
   - "Reduced hedonic capacity in major depressive disorder"
   - *American Journal of Psychiatry*, 162(12), 2381-2383
   - Why: Probabilistic reward task in MDD
   - Extract: Response bias, reward learning parameters

2. **Luman, M., Tripp, G., & Scheres, A. (2010)**
   - "Identifying the neurobiology of altered reinforcement sensitivity in ADHD"
   - *Neuroscience & Biobehavioral Reviews*, 34(5), 744-754
   - Why: Review of reward processing in ADHD
   - Extract: Reward sensitivity measures, effect sizes

3. **Kohls, G., et al. (2013)**
   - "The nucleus accumbens is involved in both the pursuit of social reward and avoidance of social punishment"
   - *Neuropsychologia*, 51(11), 2062-2069
   - Why: Reward processing in ASD
   - Extract: Behavioral reward sensitivity measures

**What to Extract:**
- Reward task performance: Hit rate, response bias
- BAS scale scores by population
- Learning rate from reward feedback
- Effect sizes vs. controls

**Expected Improvement:**
- `reward_sensitivity` LOW → MODERATE (MDD, ADHD presets)
- May remain LOW for ASD if data limited

---

## Priority 2: Strengthen MODERATE Confidence Parameters

### 2.1 RT Slowing in ASD and MDD

**Current Status:**
- ASD `rt_slowing`: MODERATE (Happé & Frith 2006, qualitative)
- MDD `rt_slowing`: MODERATE (Tsourtos et al. 2002)

**Target:** Find meta-analyses with exact RT effect sizes

**Search Terms:**
```
PubMed: ("reaction time"[Title] OR "response time"[Title]) 
        AND ("autism" OR "depression") 
        AND ("meta-analysis"[Title])
```

**Recommended Papers:**

1. **Patel, S. H., Azzam, P. N. (2005)**
   - "Characterization of N200 and P300: Selected studies of the Event-Related Potential"
   - *International Journal of Medical Sciences*, 2(4), 147-154
   - Why: RT measures in clinical populations
   - Extract: RT effect sizes

2. **For MDD - Look for:**
   - Recent psychomotor slowing meta-analyses
   - Extract: Cohen's d for RT difference
   - Calculate exact slowing percentage from d

**What to Extract:**
- Mean RT MDD: ____ ms (SD: ____), Control: ____ ms (SD: ____)
- Effect size: Cohen's d = ____
- Slowing percentage: ____% (calculate from means)

**Expected Improvement:**
- If exact values found: MODERATE → HIGH

---

### 2.2 Working Memory Decay Rates

**Current Status:** ALL LOW (theoretical)

**Reality Check:** 
- Per-tick WM decay is NOT measured in any paradigm
- Literature reports: Capacity (span), interference effects, load manipulation
- But NOT: decay rate per unit time

**Options:**
1. **Keep as LOW, justify theoretically**
   - Document it's derived from load effects
   - Show it produces realistic behavior
   - Mark for sensitivity analysis (Phase 3)

2. **Find decay time-course studies:**
   - Search for: "working memory" AND "decay" AND "time course"
   - Primacy/recency effects
   - Delay manipulation studies
   - Extract: Performance drop per second of delay

3. **Consider simplifying:**
   - Remove decay altogether (capacity-only model)
   - Or: Make decay constant across populations
   - Test if differentiation is necessary

**Recommended Approach:**
- Search for delay manipulation studies
- If no clear time-course data: Keep as LOW
- Document in limitations
- Test sensitivity in Phase 3

---

## Priority 3: The "Unresolvable" Parameters

### 3.1 Exploration Rate

**Hard Truth:** No measurement paradigm exists for "exploration rate" as defined

**What literature HAS:**
- Explore-exploit tasks (specific paradigms, not general rate)
- Iowa Gambling Task (risk-taking, not exploration)
- Delay discounting (temporal, not exploration)
- Curiosity scales (questionnaire, not behavioral)

**Options:**

**Option A: Search for Explore-Exploit Studies**
```
PubMed: ("explore exploit"[Title] OR "exploration exploitation"[Title])
        AND ("autism" OR "ADHD" OR "depression")
```
- Extract: Exploration percentage from specific tasks
- Problem: Task-specific, may not generalize

**Option B: Use Computational Models**
```
Search: "computational model" AND "exploration" AND (autism OR ADHD OR depression)
        AND ("reinforcement learning" OR "Bayesian")
```
- Look for fitted RL models with exploration parameter (ε, temperature)
- Extract parameter values from model fits

**Option C: Acknowledge as Theoretical**
- Keep as LOW confidence
- Document inference chain:
  - ADHD: Delay aversion → preference for novel options → high exploration
  - MDD: Rumination → stuck in patterns → low exploration
  - ASD: Reduced flexibility → lower exploration
- Test sensitivity (Phase 3): Does this parameter matter?

**Recommendation:** Try Option B first, fall back to Option C

---

### 3.2 Prediction Error Gain

**Hard Truth:** "Prediction error gain" is model-specific construct

**What literature HAS:**
- Learning rates from RL models (α parameter)
- Prediction error signals (fMRI, EEG)
- But: These are from specific computational models

**Search Strategy:**
```
PubMed: ("reinforcement learning"[Title] OR "prediction error"[Title])
        AND ("learning rate" OR "alpha")
        AND ("autism" OR "ADHD" OR "depression")
        AND ("computational model" OR "model-based")
```

**Recommended Papers:**

1. **Daw, N. D., et al. (2011)**
   - "Model-based influences on humans' choices and striatal prediction errors"
   - Why: Computational models with learning parameters

2. **Huys, Q. J., et al. (2013)**
   - "Disentangling the roles of approach, activation and valence in depression"
   - Why: RL models fitted to depression data
   - Extract: Learning rate parameters

**What to Extract:**
- Learning rate (α) in NT: ____ (typical: 0.1-0.3)
- Learning rate in MDD: ____ (predict: lower)
- Learning rate in ADHD: ____ (predict: higher, more reactive)

**Mapping:**
```python
# Learning rate (0-1) → prediction_error_gain (0-2)
# gain = learning_rate * 2 / 0.2  # Scale to ~1.0 baseline
```

**Reality:** This may remain LOW due to model-specificity

---

## Search Execution Plan

### Week 1: Meta-Analyses (HIGH PRIORITY)

**Day 1-2: Task-Switching**
- [ ] Search PubMed, Web of Science for switch cost meta-analyses
- [ ] Download Vandierendonck (2010), Kiesel (2010)
- [ ] Extract switch cost values

**Day 3-4: Vigilance**
- [ ] Search for vigilance decrement meta-analyses
- [ ] Download See et al. (1995), Thomson et al. (2015)
- [ ] Extract decline slopes

**Day 5: Stress Recovery**
- [ ] Search cortisol recovery literature
- [ ] Download Dickerson & Kemeny (2004)
- [ ] Extract recovery time courses

---

### Week 2: Clinical Population Data (MEDIUM PRIORITY)

**Day 6-7: Affect Measures**
- [ ] Search PANAS in ASD, ADHD, MDD
- [ ] Extract mean scores and SDs

**Day 8-9: Reward Sensitivity**
- [ ] Search reward processing in clinical populations
- [ ] Extract behavioral measures

**Day 10: RT Effect Sizes**
- [ ] Search for ASD, MDD RT meta-analyses
- [ ] Extract exact effect sizes

---

### Week 3: Computational Models (LOW PRIORITY)

**Day 11-12: Exploration**
- [ ] Search explore-exploit studies
- [ ] Search computational models with exploration

**Day 13-14: Prediction Error**
- [ ] Search RL models in clinical populations
- [ ] Extract learning rate parameters

**Day 15: Synthesis**
- [ ] Update EVIDENCE_TABLE with all findings
- [ ] Recalculate confidence levels
- [ ] Document any parameter revisions needed

---

## Expected Outcomes

### Best Case Scenario:
- Upgrade 18-22 parameters from LOW → MODERATE/HIGH
- Final distribution: 40% HIGH, 45% MODERATE, 15% LOW
- All major parameters well-justified

### Realistic Scenario:
- Upgrade 12-15 parameters
- Final distribution: 35% HIGH, 45% MODERATE, 20% LOW
- Some parameters remain theoretical but documented

### Worst Case Scenario:
- Upgrade 6-8 parameters
- Final distribution: 28% HIGH, 42% MODERATE, 30% LOW
- Still improved transparency and documentation

---

## Literature Access Resources

### Free/Low-Cost:
1. **PubMed Central** - Open access full texts
2. **ResearchGate** - Request full texts from authors
3. **Google Scholar** - Find open access versions
4. **Sci-Hub** - (Use at your own ethical discretion)
5. **Author emails** - Directly request PDFs

### Institutional:
1. University library access
2. Interlibrary loan (ILL)
3. Alumni access to databases
4. Collaborate with someone who has access

### Paid:
1. DeepDyve ($40/month, unlimited rentals)
2. Individual article purchase ($20-40 per paper)
3. Society memberships (often include journal access)

---

## Documentation Protocol

For each paper accessed:

1. **Create entry in EVIDENCE_TABLE.md:**
   ```markdown
   | Parameter | Value | Evidence | Status | Metric | Effect Size | Confidence |
   |-----------|-------|----------|--------|--------|-------------|------------|
   | switch_cost | 0.25 | Yerys et al. (2009) | ✅ | WCST switch cost: 250ms vs 100ms NT | d=1.2 | MODERATE |
   ```

2. **Update SCALE_MAPPINGS.md if needed:**
   - Add new conversion formulas
   - Update confidence levels
   - Add references

3. **Flag for parameter revision:**
   - If extracted value differs from current by >20%
   - Document discrepancy
   - Recommend revision

4. **Create summary document:**
   - `docs/LITERATURE_EXTRACTION_RESULTS.md`
   - What was found
   - What was upgraded
   - What remains unresolved

---

## Summary

**Goals:**
- Access 20-30 papers over 3 weeks
- Extract quantitative values for 40+ parameters
- Upgrade 12-18 parameters to higher confidence
- Document all findings systematically

**Priorities:**
1. **Must have:** Task-switching, vigilance, affect meta-analyses
2. **Should have:** Stress recovery, reward sensitivity studies
3. **Nice to have:** Computational models for exploration/PE

**Success Criteria:**
- >35% parameters at HIGH confidence
- <25% parameters at LOW confidence
- All mappings documented with formulas
- Clear justification for all values

---

**Status:** Search strategy documented  
**Next:** Begin literature access and extraction  
**Timeline:** 3 weeks systematic extraction
