# Extracted Data: huang-pollock2012

**Paper:** Huang-Pollock, C. L., Karalunas, S. L., Tam, H., & Moore, A. N. (2012).
Evaluating vigilance deficits in ADHD: A meta-analysis of CPT performance.
**Journal:** Journal of Abnormal Psychology, 121(2), 360–371.
**DOI:** 10.1037/a0027205
**Source:** Wayback Machine archive of PMC3664643 (`papers/huang-pollock2012.pdf`)
**Extraction Date:** 2026-08-04
**Status:** ✅ Complete

**Important correction:** the PDF previously saved at this path
(`papers/huang-pollock2012.pdf`) was the wrong paper (Ansell et al., 2012,
"Cumulative Adversity and Smaller Gray Matter Volume..." — unrelated). It has been
replaced with the correct paper. The bibliography title was also wrong
("Omission errors in ADHD: Evidence of a response execution deficit" does not
match any real Huang-Pollock (2012) publication) and has been corrected in
`papers/bibliography.md`.

---

## Meta-Analytic Results (Table 1)

Population δ (bias- and artifact-corrected, i.e. best-case estimate), children with
ADHD vs. non-ADHD controls on Continuous Performance Test (CPT) measures:

| Measure | k (studies) | N | δ bare-bones (SD) | δ corrected (SD) | 95% CI | % var. artifact |
|---|---|---|---|---|---|---|
| Commissions | 33 | 3,165 | 0.55 (0.18) | **0.98** (0.27) | 0.63–1.32 | 77.06% |
| Omissions | 39 | 3,192 | 0.62 (0.21) | **1.34** (0.28) | 0.98–1.69 | 90.30% |
| RT | 26 | 1,342 | 0.37 (0.44) | **0.61** (0.73) | -0.33–1.55 | 32.10% |
| SDRT | 16 | 930 | 0.56 (0.23) | **0.93** (0.38) | 0.45–1.41 | — |
| POT Commissions | 5 | 431 | 0.17 (0) | 0.24 (0) | — | 206.01% |
| POT Omissions | 7 | 488 | 0.38 (0.37) | **0.54** (0.53) | — | — |
| POT RT | 5 | 338 | 0.19 (0) | 0.27 (0) | — | — |
| POT SDRT | 4 | 299 | 0.16 (0) | 0.22 (0) | — | 146.96% |

(Positive δ = worse performance by ADHD group. POT = "performance over time" —
the standardized vigilance-decrement effect, i.e. how much more steeply the ADHD
group's performance declines across task blocks relative to controls, not a raw
per-minute slope.)

**Signal detection / accuracy (raw rates, not standardized):**

- Mean hit rate (SD): **ADHD 0.79 (0.17)** vs. **non-ADHD control 0.89 (0.12)**
- Mean false alarm rate (SD): ADHD 0.07 (0.07) vs. control 0.04 (0.06)
- Perceptual sensitivity d′: controls > ADHD, t(30) = 10.45, p < .001, d = 0.98
- No group difference in response bias (lnβ): t(30) = 0.49, p = .62, d = 0.04

**Diffusion-model decomposition (n = 12 studies with raw RT/accuracy data):**

- Drift rate v: controls faster than ADHD, t(11) = 4.55, p = .001, d = 0.75
- Boundary separation a: no group difference, t(11) = 1.71, p = .11, d = 0.16
- Non-decision time Ter: no group difference, t(11) = -0.27, p = .79, d = -0.06

**Publication bias:** file-drawer analysis indicates the corrected δs are robust
(281–1,006 missing studies needed to null the effect, depending on measure).
Trim-and-fill found moderate bias for Omissions (1.34→0.97 corrected) and
Commissions (0.98→0.83), but all remained large.

---

## Implications for Parameters

### base_accuracy (ADHD preset, current value: 0.80)

- **Correct citation:** should be Huang-Pollock et al. (2012), not Kofler et al.
  (2013) — see kofler2013_EXTRACTED.md Notes. Kofler doesn't report accuracy data.
- **Finding:** mean hit rate ADHD = 0.79 (SD 0.17) vs. control = 0.89 (SD 0.12).
- **Mapping:** hit rate ≈ accuracy directly. 0.79 vs. current preset value 0.80 is
  an almost exact match (0.01 off).
- **Decision:** value unchanged (0.80) — well supported, essentially confirmed.
- **Confidence: HIGH**, now backed by a direct, exact empirical match rather than a
  qualitative "2-3x higher [errors]" claim. Re-cite to Huang-Pollock et al. (2012)
  in `docs/EVIDENCE_TABLE.md` and update the `src/presets.py` comment.

### attention_stability (ADHD preset, current value: 0.60)

- **Finding:** the paper does not report a raw "sustained attention" score;
  the closest construct is the POT (performance-over-time) effects, which the
  authors describe as "small/moderate" — moderate for omissions (δ = 0.54),
  small for commissions (δ = 0.24), RT (δ = 0.27), SDRT (δ = 0.22).
- **Decision:** value unchanged (0.60) — no direct 0–1 scale mapping exists from a
  δ effect size to this parameter; the mapping remains a qualitative judgment call
  ("poor sustained attention" ⇒ below-midpoint value), now anchored to specific
  numbers instead of an unquantified claim.
- **Confidence: kept HIGH is not fully justified by this paper alone** — the
  overall CPT deficit (commissions/omissions/RT, δ = 0.6–1.3) is HIGH-quality
  evidence, but the POT (decrement-over-time) component specifically supporting
  *this* parameter is only small-to-moderate and less robust (fewer studies,
  k = 5–7, no CI reported). Recommend downgrading `attention_stability` confidence
  to MODERATE to reflect that the strongest evidence in this paper (omissions/
  commissions/RT deficits) supports `base_accuracy`, not `attention_stability`
  directly.

### vigilance_decrement (ADHD preset, current value: 0.025 per unit time)

- **Finding:** no raw per-minute/per-block slope is reported — only the
  standardized POT effect sizes above (δ = 0.22–0.54, moderate at best for
  omissions).
- **Decision:** value unchanged (0.025) — cannot be directly derived from a
  standardized effect size without an assumed variance/task-length scale, so the
  "2.5x NT" mapping in EVIDENCE_TABLE remains a judgment call rather than a
  literature-derived multiplier.
- **Confidence: MODERATE, confirmed as-is** — matches current rating. The paper
  supports "vigilance decrements exist and are more pronounced in ADHD" directionally
  (moderate POT-omissions effect) but not the specific rate value.

---

## Quality Assessment

- [x] Large, multi-study meta-analysis (k = 16–39 depending on measure)
- [x] Bias/artifact correction applied (comparable rigor to Kofler 2013)
- [x] Both standardized (δ) and raw (hit/FA rate) metrics reported
- [x] Publication-bias analysis performed
- [ ] POT (vigilance-decrement) component has fewer studies and no CIs reported —
      weaker evidence than the overall CPT-deficit component

**Overall Quality:** HIGH (overall CPT deficits); MODERATE (POT/decrement component specifically)
