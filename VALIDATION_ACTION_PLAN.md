# Clinical Presets Validation Action Plan

**Date:** January 13, 2026  
**Status:** v1.1 Literature Review Complete  
**Priority:** Address before claiming "empirically validated"

---

## Executive Summary

The clinical presets have a **mixed evidence base**:
- ✅ **Strong:** RT parameters, some WM/stress measures (ADHD variability, MDD cortisol)
- ⚠️ **Moderate:** Most attention/executive function parameters
- ❌ **Weak:** Exploration, prediction error, affect parameters, stress recovery rates

**Key Issue:** Parameters are presented as empirical but many are theoretical estimates.

---

## CRITICAL FIXES (Do Before Publishing)

### 1. Resolve Working Memory Contradiction ❌ BLOCKER
**Problem:** Neurotypical preset cites both:
- Miller (1956): 7±2 items → using 7.0
- Cowan (2001): 4±1 items → contradicts above

**Action:**
```python
# Option A: Use modern consensus (Cowan)
'neurotypical': {'wm_capacity': 4.0}
'asd_typical': {'wm_capacity': 4.0}  # adjust accordingly
'adhd_typical': {'wm_capacity': 3.0}  # was 4.5
'mdd_typical': {'wm_capacity': 3.5}  # was 5.5

# Option B: Keep Miller but remove Cowan citation
# Remove line: "2. Cowan (2001). The magical number 4..."
```

**Recommendation:** Use Option A (Cowan) - modern consensus

---

### 2. Verify/Fix Unconfirmed Citations ❌ BLOCKER

**Cannot verify these exist:**

#### Sanders (1998) - Elements of human performance
- **Issue:** Textbook, not peer-reviewed; no page number
- **Action:** Replace with empirical meta-analysis of accuracy, e.g.:
  - Luce (1986) Response Times
  - Palmer et al. (2011) "The effect of stimulus strength on accuracy"

#### Van Eylen et al. (2011) - Cognitive flexibility in ASD  
- **Issue:** Cannot confirm publication exists
- **Action:** Search PubMed/PsycINFO and either:
  - Provide full citation if found
  - Replace with verified study, e.g., Geurts et al. (2009) on ASD flexibility

#### Williams et al. (2006) - Memory profile in ASD
- **Issue:** Many "Williams et al." papers; ambiguous
- **Action:** Provide full citation with journal/DOI or replace with:
  - Steele et al. (2007) "Spatial working memory deficits in ASD"

---

### 3. Add Parameter Confidence Levels ⚠️ HIGH PRIORITY

Add to `src/presets.py`:

```python
# After CLINICAL_PRESETS definition, add:

PARAMETER_CONFIDENCE = {
    'neurotypical': {
        'base_rt': 'HIGH',  # Ratcliff & McKoon meta-review
        'rt_variability': 'MODERATE',  # typical CV estimates
        'wm_capacity': 'HIGH',  # Miller/Cowan classics
        'stress_baseline': 'LOW',  # theoretical estimate
        'stress_recovery': 'LOW',  # no direct data
        'exploration_rate': 'LOW',  # theoretical estimate
        'prediction_error_gain': 'LOW',  # no direct evidence
        # ... etc
    },
    # ... other presets
}

def get_parameter_confidence(preset: str, param: str) -> str:
    """Get confidence level for a parameter (HIGH/MODERATE/LOW)."""
    return PARAMETER_CONFIDENCE.get(preset, {}).get(param, 'UNKNOWN')
```

---

### 4. Document Scale Mappings ⚠️ HIGH PRIORITY

Create `docs/PARAMETER_MAPPINGS.md`:

```markdown
# How Literature Values Map to Simulation Parameters

## Stress Parameters (0-1 scale)

### stress_baseline
- **Literature:** Cortisol levels (μg/dL), ACTH, HPA axis measures
- **Mapping:** 
  - Neurotypical basal cortisol ~10-20 μg/dL → 0.30
  - ASD elevated ~25-35 μg/dL → 0.50
  - MDD elevated ~30-40 μg/dL → 0.55
- **Formula:** `stress = (cortisol - 10) / 50` (approximate)
- **Confidence:** LOW - no validated conversion

### stress_recovery
- **Literature:** Cortisol recovery time (minutes)
- **Mapping:**
  - Fast recovery (30 min) → 0.15
  - Slow recovery (60 min) → 0.08
  - Very slow (90+ min) → 0.06
- **Formula:** `recovery = 5 / time_minutes` (approximate)
- **Confidence:** LOW - theoretical estimate

## Response Time Parameters

### rt_variability (Coefficient of Variation)
- **Literature:** CV = SD/Mean from RT distributions
- **Mapping:** DIRECT - use CV from studies
  - NT: CV ~0.15 (Klein et al.)
  - ADHD: CV ~0.45 (Kofler meta-analysis)
- **Confidence:** HIGH - direct empirical match

## Working Memory Parameters

### wm_capacity (items)
- **Literature:** Span tasks (digit span, spatial span)
- **Mapping:** DIRECT - use mean span
  - NT: 7±2 (Miller) or 4±1 (Cowan)
  - ADHD: Reduced by ~1.5-2 items
- **Confidence:** HIGH for NT, MODERATE for clinical

## Affect Parameters (0-1 scale)

### positive_affect
- **Literature:** PANAS positive scale (10-50 points)
- **Mapping:** 
  - NT average ~33/50 → 0.60
  - MDD anhedonia ~15/50 → 0.25
- **Formula:** `positive_affect = (PANAS_pos - 10) / 40`
- **Confidence:** LOW - needs validation

### reward_sensitivity
- **Literature:** Probabilistic reward task, BAS scales
- **Mapping:** ??? - NO CLEAR MAPPING
- **Confidence:** LOW - theoretical estimate

## Exploration/Learning Parameters

### exploration_rate (0-1)
- **Literature:** ??? - NO DIRECT MEASURE
- **Theoretical basis:** 
  - Delay aversion (ADHD) → high exploration
  - Rumination (MDD) → low exploration
- **Confidence:** LOW - inference only

### prediction_error_gain
- **Literature:** ??? - NO DIRECT MEASURE
- **Theoretical basis:** Learning rate from RL models
- **Confidence:** LOW - no empirical grounding
```

---

## VALIDATION TASKS (Before v1.2)

### Phase 1: Citation Verification (1-2 weeks)
- [ ] Access all 25 papers and verify they say what's claimed
- [ ] Replace unverified citations (Sanders, Van Eylen, Williams)
- [ ] Extract exact effect sizes/values from each paper
- [ ] Create evidence table with page numbers and quotes

### Phase 2: Parameter Justification (2-4 weeks)
- [ ] For each parameter, document:
  - Source study/meta-analysis
  - Original metric and value
  - Conversion formula to simulation scale
  - Confidence level (HIGH/MODERATE/LOW)
- [ ] Identify parameters with NO direct evidence
- [ ] Create "theoretical estimates" list

### Phase 3: Literature Gaps (4-6 weeks)
- [ ] Conduct PubMed searches for missing evidence:
  - Task-switching effect sizes (switch_cost)
  - Vigilance decrement rates (vigilance_decrement)
  - Affect measures in clinical populations
  - Stress recovery time courses
- [ ] Consider commissioning systematic reviews for critical gaps
- [ ] Update citations with better evidence

### Phase 4: Sensitivity Analysis (2-3 weeks)
- [ ] Test simulation with ±20% parameter variations
- [ ] Identify which parameters matter most for outcomes
- [ ] Flag parameters where weak evidence is critical
- [ ] Document robustness of findings

### Phase 5: Expert Review (4-8 weeks)
- [ ] Send to clinical researchers in each domain:
  - ASD researcher for ASD parameters
  - ADHD researcher for ADHD parameters
  - Depression researcher for MDD parameters
- [ ] Incorporate feedback and revise
- [ ] Get endorsements if possible

---

## DOCUMENTATION UPDATES NEEDED

### 1. Update `docs/clinical_presets_v1.1.md`

Add section before "Usage":

```markdown
## Evidence Quality & Limitations

### Parameter Confidence Levels

**HIGH CONFIDENCE (meta-analytic support):**
- ADHD rt_variability: Kofler et al. (2013) - 319 studies
- MDD stress_baseline: Burke et al. (2005) - 361 studies
- NT base_rt: Ratcliff & McKoon (2008) - comprehensive review

**MODERATE CONFIDENCE (single studies or indirect):**
- ADHD wm_capacity: Kasper et al. (2012) meta-analysis
- ASD stress_baseline: Corbett et al. (2009) empirical study
- Most attention/executive function parameters

**LOW CONFIDENCE (theoretical estimates):**
- ALL exploration_rate values - inferred from related constructs
- ALL prediction_error_gain values - no direct measurement
- Most vigilance_decrement rates - slopes not quantified
- Most stress_recovery rates - no time-course data
- Several affect parameters - indirect mapping

### Known Limitations

1. **Scale mapping:** Many parameters use 0-1 scales not directly
   measured in literature. Conversions are approximate.

2. **Missing data:** Some parameters (exploration, prediction error)
   lack direct empirical studies and are theoretical estimates.

3. **Individual differences:** Presets represent "typical" profiles
   but real populations show high variability.

4. **Context effects:** Literature values from specific tasks may
   not generalize to RPM-EE simulation context.

5. **Citation verification:** Some references need better documentation
   or replacement with stronger evidence.

### Appropriate Use

✅ **Good for:**
- Exploratory modeling of clinical populations
- Hypothesis generation for empirical studies
- Comparative simulations (relative differences)
- Educational demonstrations of clinical profiles

❌ **Not appropriate for:**
- Clinical diagnosis or assessment
- Treatment decisions
- Claiming "validated model" of disorders
- Precise quantitative predictions without validation

### Validation Status

**v1.1 Status:** PRELIMINARY - Parameters are research estimates
pending comprehensive validation.

**Needed for "validated":**
- Independent simulation-to-data comparisons
- Parameter sensitivity analyses
- Expert review by clinical researchers
- Replication across multiple simulation contexts
```

### 2. Update README.md

Change from:
> Empirically-grounded models for 4 populations (based on 25 peer-reviewed studies)

To:
> Research models for 4 populations based on 25 peer-reviewed studies (preliminary validation)

### 3. Add to `src/presets.py` docstring:

```python
"""
Clinical Presets for RPM-EE v1.1

VALIDATION STATUS: PRELIMINARY
These presets are research estimates based on clinical literature.
Parameter confidence levels vary from HIGH (meta-analytic support) to
LOW (theoretical estimates). See docs/clinical_presets_v1.1.md for
evidence quality assessment.

NOT FOR CLINICAL USE - Research and educational purposes only.
"""
```

---

## RISK ASSESSMENT

### If validation issues are NOT addressed:

**Academic Risks:**
- ❌ Reviewers will identify weak citations
- ❌ "Empirically-grounded" claim is overselling
- ❌ Credibility damage if parameters are challenged
- ❌ Difficult to publish without validation studies

**Scientific Risks:**
- ❌ Results may not generalize to real clinical populations
- ❌ Weakly-supported parameters could drive spurious findings
- ❌ Unable to distinguish model errors from parameter errors

**Legal/Ethical Risks:**
- ❌ If someone uses for clinical decisions (despite warnings)
- ❌ Misrepresentation of evidence base

### If validation is done properly:

**Benefits:**
- ✅ First principled simulation of clinical cognitive profiles
- ✅ Transparent about uncertainty
- ✅ Research agenda for validation studies
- ✅ Foundation for grant applications
- ✅ Educational value even without full validation

---

## RESOURCES NEEDED

### Minimal (DIY):
- 40-60 hours: Literature verification and documentation
- Library access: Verify all 25 citations
- No cost

### Moderate (Enhanced):
- 2-3 months part-time RA: Systematic literature search
- $5-10K: RA salary
- Meta-analysis software: Free (R, Python)

### Comprehensive (Gold Standard):
- 6-12 months postdoc: Full validation study
- $50-80K: Postdoc + empirical data collection
- Clinical collaborators: 3-4 experts (co-authors)
- Simulation-to-data validation: New behavioral studies

---

## RECOMMENDED PATH FORWARD

### Option A: Quick Fix (1 month) - For immediate use
1. Fix WM contradiction (use Cowan)
2. Verify/replace 3 problematic citations
3. Add confidence levels to documentation
4. Add "preliminary validation" disclaimers
5. Release as "v1.1-preliminary"

### Option B: Thorough Validation (3-6 months) - For publication
1. All of Option A
2. Systematic literature review for each parameter
3. Create detailed evidence tables
4. Document all scale mappings
5. Run sensitivity analyses
6. Expert review
7. Release as "v1.1-validated"

### Option C: Academic Gold Standard (1-2 years) - For major paper
1. All of Option B
2. Commission systematic reviews/meta-analyses for gaps
3. Collect new empirical data for validation
4. Compare simulation outputs to holdout datasets
5. Iterate and refine parameters
6. Multi-site expert consensus
7. Release as "v2.0"

---

## RECOMMENDATION

**For immediate needs:** Execute Option A (Quick Fix)
- Addresses critical issues
- Honest about limitations  
- Usable for research
- Lays groundwork for deeper validation

**For publication goals:** Plan Option B (Thorough Validation)
- Include in grant application
- Timeline: Begin now, complete before submission
- Budget: RA time or collaborator contribution

**For career-defining work:** Consider Option C (Gold Standard)
- Make this THE reference implementation
- Multi-paper opportunity
- Establish field standard

---

## NEXT IMMEDIATE STEPS

1. **Review this analysis with advisor/collaborators** (this week)
2. **Decide on path forward** (Option A/B/C)
3. **Fix WM contradiction** (1 day)
4. **Verify 3 problematic citations** (3-5 days)
5. **Add confidence levels** (2-3 days)
6. **Update documentation** (2-3 days)

Total time for Option A: **2-3 weeks part-time**

---

**Status:** Awaiting decision on path forward
**Contact:** [Your name/email]
**Last updated:** January 13, 2026
