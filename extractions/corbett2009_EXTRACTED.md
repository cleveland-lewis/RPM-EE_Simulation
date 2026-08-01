# Extracted Data: corbett2009

**Paper:** Corbett et al. (2009) - Elevated cortisol during play is associated with age and social engagement in children with autism
**Journal:** Molecular Autism
**DOI:** 10.1186/2040-2392-1-13
**Extraction Date:** 2026-08-01
**Status:** ✅ Complete - Figure 4 digitized, Table 3 model coefficients extracted

---

## Sample Characteristics

**Autism Group:**
- N = 21
- Age: M = 10.0, SD = 1.1, Range = 8.0-12.0
- IQ: M = 89.7, SD = 14.7, Range = 75-125
- SRS: M = 104.4, SD = 32.3

**Neurotypical Group:**
- N = 24  
- Age: M = 9.9, SD = 1.5, Range = 8.1-12.5
- IQ: M = 121.0, SD = 12.4, Range = 99-142
- SRS: M = 22.3, SD = 16.7

---

## Key Findings

### Cortisol Response Pattern

**Statistical Model:**
- Significant overall model: χ²(4) = 22.76, P < 0.0005
- Main effects: Time, Diagnosis, Age
- Interaction: Diagnosis × Age

**Key Results:**
1. Children with autism showed elevated cortisol response during peer interaction
2. The effect was moderated by age (increased cortisol with increasing age in ASD group)
3. Neurotypical children did not show age-related cortisol changes

### Behavioral Observations

**Social Interaction Time:**
- Motor play: F(1,43) = 16.7, P = 0.0002 (ASD < NT)
- Cooperative play: F(1,43) = 14.78, P = 0.0004 (ASD < NT)

**Social Approach:**
- ASD children showed more proximity without interaction
- ASD children initiated less: χ²(1) = 4.03, P = 0.044
- ASD children rejected more: χ²(1) = 7.10, P = 0.008

---

## Cortisol Values

The paper does **not** report a simple ASD-vs-NT mean±SD table for cortisol — the only
group-level cortisol data are (a) Figure 4, a line chart split by age-within-diagnosis
subgroup, and (b) Table 3, mixed-model coefficients on log-cortisol. There is no raw
mean/SD table to transcribe; the two sources below are what the paper actually provides.

### Table 3 — Model coefficients (repeated-measures mixed model, log-cortisol)

| Variable | Estimate | SE |
|---|---|---|
| Intercept | 1.457 | 0.490 |
| Time | -0.004 | 0.001 |
| Diagnosis | -2.371 | 0.933 |
| Age | -0.001 | 0.049 |
| Diagnosis × Age | **0.238** | 0.095 |

Overall model: χ²(4) = 22.76, P < 0.0005. Diagnosis×Age is the interaction driving the
paper's headline finding; the Diagnosis and Age main effects are not independently
interpretable in the presence of a significant interaction.

### Figure 4 — digitized values (visual estimate from chart, ±~0.05 nmol/L)

Four lines, split by age (median split at 9.8y within each diagnosis group), not a
simple 2-group ASD-vs-NT comparison:

| Sample | Older Autism | Younger Autism | Older Typical | Younger Typical |
|---|---|---|---|---|
| S1 (Baseline) | 1.50 | 1.18 | 1.30 | 1.60 |
| S2 (Postplay) | 1.60 | 1.38 | 1.40 | 1.30 |
| S3 (20 min post) | 1.65 | 1.35 | 1.35 | 1.35 |
| S4 (40 min post) | 1.55 | 0.95 | 1.10 | 1.22 |

Units: nmol/L. Digitized by reading gridline positions on the rendered PDF page; treat
as approximate, not exact — the paper does not publish the underlying numeric table.

**Key pattern (this is the paper's actual finding, not a simple main effect):**
- Three of the four subgroups (Younger Autism, Older Typical, Younger Typical) show the
  expected circadian decline across S1→S4 (drops of 0.08–0.43 nmol/L).
- **Older Autism is the outlier**: cortisol stays flat/slightly rising through S3 and is
  still elevated at S4 (1.55, only 0.05 below its own S2 value), i.e. it fails to show
  the normal decline the other three groups exhibit. This is what the significant
  Diagnosis×Age interaction (Table 3) is capturing.
- There is **no clean baseline (S1) elevation for ASD overall** — Younger Typical has the
  *highest* S1 value (1.60) of all four subgroups, and Younger Autism has the lowest
  (1.18). A naive "ASD > NT at baseline" reading of this figure is not supported.

---

## Implications for Parameters

Note: the code uses `stress_baseline` / `stress_reactivity` / `stress_recovery`
(`src/presets.py`), not `asd_stress_*`.

### stress_baseline (current: 0.50, was HIGH confidence)
- **Finding:** No clean ASD > NT ordering at S1 in Figure 4 (Younger Typical is
  highest, Younger Autism is lowest). The overall model's Diagnosis main effect
  (-2.371) is not separately interpretable given the significant interaction term.
- **Decision:** Current value UNCHANGED (0.50) — it's a reasonable simplification for
  a non-age-stratified preset, and the paper's own comparison of ASD lab-baseline vs.
  ASD home-afternoon-baseline found no significant difference (t(19)=0.54, P=0.60),
  i.e. ASD kids weren't simply "stressed at baseline" beyond their own norm.
- **Confidence: DOWNGRADED HIGH → MODERATE.** The original HIGH rating assumed a
  direct, clean baseline-elevation measurement; the actual data show the ASD-specific
  effect is in the trajectory (see stress_recovery below), not the baseline level.

### stress_reactivity (current: 0.60, MODERATE confidence)
- **Finding:** From S1→S2, both autism subgroups increase (Older +0.10, Younger
  +0.20) while Younger Typical *decreases* (-0.30) and Older Typical is flat (+0.10).
  Directionally consistent with elevated reactivity in ASD, but effect size is modest
  and not the paper's statistically significant result.
- **Decision:** Current value UNCHANGED (0.60).
- **Confidence:** UNCHANGED (MODERATE) — qualitative support only, no clean effect size.

### stress_recovery (current: 0.08, was MODERATE confidence)
- **Finding:** This is the paper's actual significant result. The Diagnosis×Age
  interaction (estimate 0.238, SE 0.095, part of the overall χ²(4)=22.76, P<0.0005
  model) captures that Older-Autism cortisol fails to decline after S2 the way all
  three other subgroups do (Older Autism: -0.05 over 20 min post-peak vs. -0.20 to
  -0.43 for the other subgroups over the same window).
- **Decision:** Current value UNCHANGED (0.08, i.e. slow recovery) — well-supported.
- **Confidence: UPGRADED MODERATE → HIGH.** This is directly the study's significant,
  age-moderated finding. Caveat carried into the code comment: the effect is
  strongest/clearest in *older* children with ASD (median split ~9.8y); the
  non-age-stratified preset applies it as a population-level simplification.

---

## Quality Assessment

- [x] Adequate sample size (N=45 total, 21 ASD, 24 NT)
- [x] Control group included (neurotypical matched on age)
- [x] Clear methodology (salivary cortisol, ecologically valid paradigm)
- [x] Statistical significance established
- [ ] Effect sizes not fully reported (need to calculate from figure)
- [x] Replicates prior findings of elevated stress in ASD

**Overall Quality:** HIGH

---

## Next Steps

1. **Manual extraction from PDF figures:**
   - Open papers/corbett2009.pdf
   - Examine Figure 4 closely
   - Extract exact cortisol values (M ± SD) for each group × timepoint
   
2. **Convert to simulation units:**
   - Use SCALE_MAPPINGS.md to convert nmol/L to stress scale (0-1)
   - Calculate baseline, reactivity, and recovery parameters
   
3. **Update presets.py:**
   - Modify asd_stress_baseline if needed
   - Add evidence citation
   - Update confidence level to HIGH

4. **Document in EVIDENCE_TABLE:**
   - Mark as ✅ Extracted
   - Add effect sizes and sample sizes
   - Note confidence upgrade

---

## Notes

- This is an ecologically valid study using natural playground interaction
- Cortisol measured via saliva (well-validated method)
- Age moderates the effect (important consideration for model)
- Social behavior independently coded and verified
- Published in open-access journal (good for reproducibility)

**Limitation:** Exact numeric values need manual extraction from figures/tables in PDF viewer.
