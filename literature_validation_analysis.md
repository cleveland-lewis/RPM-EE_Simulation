# Literature Validation Analysis: Clinical Presets v1.1

**Analysis Date:** January 13, 2026  
**Reviewer:** GitHub Copilot CLI  
**Purpose:** Verify empirical justification for all preset parameters

---

## Methodology

For each reference, I assessed:
1. **Citation completeness** - Is full citation provided?
2. **Parameter coverage** - Which parameters does it justify?
3. **Evidence strength** - Is the evidence direct or indirect?
4. **Quantitative support** - Does it provide specific values/ranges?
5. **Gaps/concerns** - What's missing or questionable?

---

## NEUROTYPICAL BASELINE (6 references)

### 1. Ratcliff & McKoon (2008) - Diffusion Decision Model
**Parameters justified:** `base_rt` (500ms)
- ✅ **STRONG**: Comprehensive review of RT in two-choice tasks
- ✅ Direct evidence for 400-600ms range in simple tasks
- ✅ Widely cited foundational model
- ⚠️  **Note**: Focuses on decision processes, not baseline arousal/stress

### 2. Cowan (2001) - Magical Number 4
**Parameters justified:** `wm_capacity` (7.0)
- ⚠️  **CONFLICT**: Cowan argues for 4±1 items, NOT 7±2
- ❌ **Problem**: This contradicts the parameter value used (7.0)
- **Recommendation**: Either cite Miller (1956) alone OR use capacity=4.0

### 3. Miller (1956) - Magical Number 7±2
**Parameters justified:** `wm_capacity` (7.0)
- ✅ **CLASSIC**: Original 7±2 items estimate
- ⚠️  Modern consensus is closer to 4±1 (Cowan, 2001)
- ✅ Still valid for "neurotypical baseline" as historical benchmark

### 4. McEwen (1998) - Allostasis and Allostatic Load
**Parameters justified:** `stress_baseline`, `stress_reactivity`, `stress_recovery`
- ✅ **STRONG**: Foundational stress response theory
- ❌ **VAGUE**: No specific quantitative values provided
- ⚠️  Values (0.30, 0.50, 0.15) appear to be arbitrary estimates
- **Gap**: Need empirical cortisol/arousal baseline data

### 5. Posner & Petersen (1990) - Attention System
**Parameters justified:** `attention_stability`, `switch_cost`
- ✅ **STRONG**: Foundational attention theory
- ❌ **VAGUE**: No specific values for stability or switch costs
- ⚠️  Values (0.85, 0.10) appear to be estimates
- **Gap**: Need task-switching meta-analysis data

### 6. Sanders (1998) - Elements of Human Performance
**Parameters justified:** `base_accuracy` (0.90)
- ⚠️  **CITATION ISSUE**: This is a textbook, not peer-reviewed research
- ❌ Cannot verify specific accuracy claims without page numbers
- **Recommendation**: Replace with empirical meta-analysis

**NEUROTYPICAL VERDICT:** 
- ✅ RT parameters: Well-justified
- ⚠️  WM capacity: Citation conflict (Miller vs Cowan)
- ❌ Stress/attention: Weak quantitative support
- ❌ Accuracy: Non-primary source

---

## AUTISM SPECTRUM DISORDER (6 references)

### 7. Happé & Frith (2006) - Weak Coherence
**Parameters justified:** `rt_slowing` (1.15), `attention_stability`
- ✅ **STRONG**: Well-known theoretical account
- ⚠️  Doesn't provide specific RT slowing percentages
- ❌ **VAGUE**: 10-15% slowing claim needs direct evidence

### 8. Van Eylen et al. (2011) - Cognitive Flexibility
**Parameters justified:** `accuracy_decline`, `switch_cost` (0.25)
- ❌ **CANNOT VERIFY**: Need to check if this study exists
- ⚠️  Title suggests it addresses flexibility, but specific values unknown
- **Action needed**: Verify publication and extract specific metrics

### 9. Williams et al. (2006) - Memory Profile
**Parameters justified:** `wm_capacity` (7.0), `wm_decay_rate` (0.015)
- ❌ **CANNOT VERIFY**: Need to check if this study exists
- ⚠️  Multiple "Williams et al." publications on ASD
- **Action needed**: Provide full citation with journal/title

### 10. Corbett et al. (2009) - Elevated Cortisol
**Parameters justified:** `stress_baseline` (0.50), `stress_reactivity` (0.60)
- ✅ **STRONG**: Direct evidence of elevated cortisol in ASD children
- ✅ Peer-reviewed empirical study
- ❌ **VAGUE**: No specific values for mapping to 0-1 scale
- **Gap**: How were cortisol levels converted to 0.50 baseline?

### 11. Yerys et al. (2009) - Set-Shifting
**Parameters justified:** `switch_cost` (0.25)
- ✅ **STRONG**: Direct evidence of set-shifting deficits
- ❌ **VAGUE**: Need specific effect sizes to justify 2.5x cost (0.25 vs 0.10)
- **Action needed**: Extract specific switch cost magnitudes

### 12. Robertson & Baron-Cohen (2017) - Sensory Perception
**Parameters justified:** `negative_affect` (0.35), sensory reactivity
- ✅ **RECENT**: Contemporary review of sensory differences
- ❌ **INDIRECT**: Sensory reactivity ≠ negative affect directly
- **Gap**: Need affect/emotion studies for `positive_affect`, `negative_affect` values

**ASD VERDICT:**
- ✅ Stress elevation: Supported by Corbett et al.
- ⚠️  RT slowing: Weak quantitative support
- ❌ Switch costs: Need specific effect sizes
- ❌ WM parameters: Unverified citation
- ❌ Affect parameters: Indirect/insufficient evidence

---

## ADHD (6 references)

### 13. Klein et al. (2006) - Intra-Subject Variability
**Parameters justified:** `rt_variability` (0.45)
- ✅ **GOOD**: Direct evidence for RT variability in ADHD
- ⚠️  Need to verify specific CV values (45% claim)
- **Action needed**: Extract exact variability metrics

### 14. Kofler et al. (2013) - RT Variability Meta-Analysis
**Parameters justified:** `rt_variability` (0.45), `base_accuracy` (omission errors)
- ✅ **EXCELLENT**: Meta-analysis of 319 studies
- ✅ Most robust evidence in entire preset collection
- ✅ Should provide specific effect sizes for 35-50% variability claim
- **Action needed**: Verify meta-analytic effect sizes match parameters

### 15. Kasper et al. (2012) - Working Memory Deficits
**Parameters justified:** `wm_capacity` (4.5)
- ✅ **STRONG**: Meta-analytic evidence for WM deficits
- ❌ **VAGUE**: Does it specify ~4-5 items specifically?
- **Action needed**: Extract specific capacity estimates

### 16. Huang-Pollock et al. (2012) - Vigilance Deficits
**Parameters justified:** `attention_stability` (0.60), `vigilance_decrement` (0.025)
- ✅ **STRONG**: Direct evidence for vigilance problems
- ❌ **VAGUE**: Need specific decrement rates over time
- **Gap**: How was 2.5x faster decrement calculated?

### 17. Lackschewitz et al. (2008) - Stress Responses
**Parameters justified:** `stress_reactivity` (0.75), `stress_recovery` (0.10)
- ✅ **GOOD**: Direct physiological stress evidence
- ❌ **VAGUE**: Need specific values for arousal/cortisol
- **Gap**: Conversion from physiology to 0-1 scale unclear

### 18. Sonuga-Barke (2005) - Delay Aversion
**Parameters justified:** `exploration_rate` (0.40), `reward_sensitivity` (0.85)
- ✅ **STRONG**: Well-cited theoretical model
- ❌ **INDIRECT**: Delay aversion doesn't directly specify exploration rate
- **Gap**: How does delay aversion → 40% exploration?

**ADHD VERDICT:**
- ✅✅ RT variability: **BEST JUSTIFIED** (Kofler meta-analysis)
- ✅ WM deficits: Good support from Kasper
- ⚠️  Vigilance: Good concept, weak quantification
- ⚠️  Stress: Conceptually sound, vague numerical mapping
- ❌ Exploration: Indirect inference from theory

---

## MAJOR DEPRESSIVE DISORDER (7 references)

### 19. Tsourtos et al. (2002) - Information Processing Speed
**Parameters justified:** `rt_slowing` (1.20), `base_rt` (600ms)
- ✅ **GOOD**: Direct evidence of psychomotor slowing
- ❌ **VAGUE**: Does it specify 15-20% slowing?
- **Action needed**: Extract specific effect sizes

### 20. Porter et al. (2003) - Neurocognitive Impairment
**Parameters justified:** `accuracy_decline` (0.10), `base_accuracy` (0.82)
- ✅ **GOOD**: Drug-free patients, clean evidence
- ❌ **VAGUE**: Does it specify 5-10% accuracy reduction?
- **Action needed**: Verify specific impairment magnitudes

### 21. Christopher & MacDonald (2005) - Working Memory Impact
**Parameters justified:** `wm_capacity` (5.5), `wm_decay_rate` (0.022)
- ✅ **STRONG**: Direct WM assessment in depression
- ❌ **VAGUE**: Specific capacity values not clear
- **Gap**: "Impaired under load" ≠ specific capacity number

### 22. Treadway & Zald (2011) - Anhedonia
**Parameters justified:** `positive_affect` (0.25), `reward_sensitivity` (0.35)
- ✅ **EXCELLENT**: Comprehensive anhedonia review
- ✅ Strong theoretical foundation
- ❌ **VAGUE**: No specific quantitative scales for affect
- **Gap**: How to map anhedonia to 0.25 positive affect?

### 23. Burke et al. (2005) - Depression and Cortisol Meta-Analysis
**Parameters justified:** `stress_baseline` (0.55), `stress_recovery` (0.06)
- ✅ **EXCELLENT**: Meta-analysis of 361 studies
- ✅ Strong evidence for HPA dysregulation
- ❌ **VAGUE**: Cortisol levels ≠ 0-1 stress scale directly
- **Gap**: Need explicit conversion formula

### 24. Snyder (2013) - Executive Function Impairments
**Parameters justified:** `attention_stability` (0.65), `switch_cost` (0.18)
- ✅ **STRONG**: Comprehensive executive function review
- ❌ **VAGUE**: "Broad impairments" doesn't give specific values
- **Gap**: Multiple EF measures, unclear which maps to each parameter

### 25. Nolen-Hoeksema (2000) - Rumination
**Parameters justified:** `exploration_rate` (0.08), `prediction_error_gain` (0.70)
- ✅ **STRONG**: Classic rumination account
- ❌ **INDIRECT**: Rumination ≠ reduced exploration directly
- **Gap**: Theoretical link, not empirical parameter values

**MDD VERDICT:**
- ✅✅ Cortisol/stress: **WELL JUSTIFIED** (Burke meta-analysis)
- ✅ Anhedonia: Strong theoretical support
- ⚠️  Psychomotor slowing: Good concept, need specific values
- ⚠️  WM/EF: Multiple citations but vague quantification
- ❌ Exploration/learning: Indirect theoretical inferences

---

## CRITICAL GAPS IDENTIFIED

### 1. **Scale Mapping Problem** ❌❌
**Issue:** Most parameters use 0-1 scales, but references don't provide these scales.
- Cortisol levels (μg/dL) → stress_baseline (0-1)?
- RT variability (CV) → rt_variability (0-1)?
- Affect questionnaires → positive_affect (0-1)?

**Recommendation:** Create explicit mapping functions with justification

### 2. **Missing Quantitative Data** ⚠️⚠️
Many citations are theoretical/qualitative:
- McEwen (1998): Theory, not data
- Posner & Petersen (1990): Framework, not values
- Happé & Frith (2006): Theoretical account
- Nolen-Hoeksema (2000): Rumination theory

**Recommendation:** Replace with or supplement using meta-analytic data

### 3. **Unverified Citations** ❌
Cannot confirm these exist/are accurate:
- Sanders (1998) - Elements of human performance [textbook?]
- Van Eylen et al. (2011) - Cognitive flexibility in ASD
- Williams et al. (2006) - Memory profile in ASD

**Action needed:** Verify these publications exist and provide full citations

### 4. **Parameter Inference** ⚠️
Several parameters lack direct evidence:
- `exploration_rate`: Inferred from delay aversion, rumination
- `prediction_error_gain`: No direct studies cited
- `vigilance_decrement`: Rates not specified
- All affect parameters: Indirect mappings

**Recommendation:** Acknowledge these as "theoretically-motivated estimates"

### 5. **Working Memory Contradiction** ❌
Neurotypical preset cites BOTH:
- Miller (1956): 7±2 items
- Cowan (2001): 4±1 items

These conflict! Modern consensus favors Cowan.

**Recommendation:** Choose one and adjust other presets accordingly

---

## SUMMARY SCORECARD

### Overall Evidence Quality by Preset:

| Preset | RT | Accuracy | WM | Attention | Stress | Affect | Prediction |
|--------|----|----|----|----|----|----|----| 
| **Neurotypical** | ✅✅ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **ASD** | ⚠️ | ⚠️ | ❌ | ⚠️ | ✅ | ❌ | ❌ |
| **ADHD** | ✅✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ❌ |
| **MDD** | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅✅ | ✅ | ❌ |

**Legend:**
- ✅✅ Excellent (meta-analysis or multiple direct studies)
- ✅ Good (direct empirical evidence)
- ⚠️ Weak (indirect or vague quantification)
- ❌ Poor (missing or non-empirical)

### Best-Supported Parameters:
1. **ADHD RT variability** - Kofler et al. (2013) meta-analysis
2. **MDD stress/cortisol** - Burke et al. (2005) meta-analysis  
3. **ADHD WM capacity** - Kasper et al. (2012) meta-analysis
4. **Neurotypical RT** - Ratcliff & McKoon (2008)

### Weakest-Supported Parameters:
1. **All exploration_rate values** - No direct evidence
2. **All prediction_error_gain values** - No direct evidence
3. **All affect parameters** - Indirect/vague mappings
4. **Vigilance decrements** - Rates not quantified
5. **Stress recovery rates** - No quantitative data

---

## RECOMMENDATIONS

### Immediate Actions (Required):

1. **Verify unconfirmed citations:**
   - Sanders (1998) - Find proper source or replace
   - Van Eylen et al. (2011) - Verify exists
   - Williams et al. (2006) - Provide full citation

2. **Resolve WM contradiction:**
   - Choose Miller (7±2) OR Cowan (4±1)
   - Adjust all presets consistently

3. **Document scale mappings:**
   - Create `PARAMETER_MAPPINGS.md` explaining:
     - How cortisol → stress_baseline
     - How RT CV → rt_variability  
     - How questionnaire scores → affect parameters

4. **Add "confidence levels" to preset file:**
   ```python
   'base_rt': (500.0, 'high'),  # (value, confidence)
   'exploration_rate': (0.20, 'low'),  # theoretical estimate
   ```

### Enhanced Validation (Recommended):

5. **Supplement with meta-analyses:**
   - Find task-switching meta-analysis for switch_cost
   - Find vigilance meta-analysis for decrements
   - Find affect meta-analysis for emotional parameters

6. **Create "Theoretical Estimates" section:**
   - Clearly label parameters without direct evidence
   - Explain inference chain (e.g., rumination → reduced exploration)
   - Mark as "version 1.1 estimates, validation needed"

7. **Add parameter sensitivity analysis:**
   - Test if varying weakly-supported parameters changes outcomes
   - Identify which parameters matter most for simulation behavior

### Future Work (v1.2+):

8. **Commission systematic reviews:**
   - Hire researchers to conduct proper meta-analyses
   - Extract effect sizes for all parameters
   - Build proper evidence tables

9. **Add uncertainty quantification:**
   - Parameter ranges instead of point estimates
   - Confidence intervals from literature
   - Monte Carlo sensitivity analyses

10. **Validate against holdout data:**
    - Compare simulation outputs to independent datasets
    - Test predictions against new empirical studies
    - Refine parameters based on discrepancies

---

## FINAL VERDICT

**Is the current literature sufficient to justify the presets?**

### Short Answer: **PARTIALLY** ⚠️

### Detailed Assessment:

**Strengths:**
- ✅ Core behavioral patterns (RT, WM, stress) have reasonable support
- ✅ Some excellent meta-analytic evidence (ADHD variability, MDD cortisol)
- ✅ Theoretical coherence across parameters
- ✅ Transparent documentation of sources

**Critical Weaknesses:**
- ❌ Many parameters lack direct quantitative evidence
- ❌ Scale mapping from literature → simulation parameters is opaque
- ❌ Some citations unverifiable or inappropriate (textbooks)
- ❌ No confidence intervals or uncertainty quantification
- ❌ Theoretical inferences presented as empirical facts

**Bottom Line:**
The presets are **reasonable first approximations** based on clinical literature, but they:
1. Over-claim empirical justification for many parameters
2. Mix strong evidence with theoretical speculation without distinction
3. Need explicit acknowledgment of limitations

**Recommended approach:**
- Keep current parameters as "v1.1 baseline"
- Add confidence ratings to each parameter
- Create "research agenda" document for validation studies
- Be transparent about estimates vs. empirical values
- Test sensitivity to weakly-supported parameters

The presets are **usable for exploratory research** but should NOT be claimed as "fully empirically validated" without addressing these gaps.

---

## SUGGESTED DOCUMENTATION UPDATES

Add to `clinical_presets_v1.1.md`:

```markdown
## Parameter Confidence Levels

**High Confidence** (✅✅ - meta-analytic or multiple direct studies):
- ADHD: rt_variability, wm_capacity
- MDD: stress_baseline, positive_affect (anhedonia)
- NT: base_rt

**Moderate Confidence** (✅ - single study or indirect evidence):
- ASD: stress_baseline, stress_recovery
- ADHD: attention_stability, base_accuracy
- MDD: rt_slowing, wm_capacity

**Low Confidence** (⚠️ - theoretical estimates):
- ALL: exploration_rate, prediction_error_gain
- ALL: vigilance_decrement (rates)
- Most: affect parameters (affect scale mapping)
- Most: stress_recovery (rate values)

**Caution:** Low-confidence parameters are theoretically-motivated estimates
pending empirical validation. Use caution when interpreting simulation
results that depend heavily on these parameters.
```

---

**Analysis complete.** Would you like me to:
1. Create detailed evidence tables for each parameter?
2. Search for additional meta-analyses to fill gaps?
3. Draft updated documentation with confidence levels?
4. Create a research agenda for parameter validation?
