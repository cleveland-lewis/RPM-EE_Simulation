# Extracted Data: kofler2013

**Paper:** Kofler, M. J., Rapport, M. D., Sarver, D. E., Raiker, J. S., Orban, S. A.,
Friedman, L. M., & Kolomeyer, E. G. (2013). Reaction time variability in ADHD: A
meta-analytic review of 319 studies.
**Journal:** Clinical Psychology Review, 33(6), 795–811.
**DOI:** 10.1016/j.cpr.2013.06.001
**Source:** Open-access copy from author's lab site (FSU Children's Learning Clinic),
`papers/kofler2013.pdf`
**Extraction Date:** 2026-08-04
**Status:** ✅ Complete for `rt_variability`. **Correction:** this paper does NOT
report omission-error data — `base_accuracy`'s citation of Kofler in the current
docs/presets is wrong (see Notes).

---

## Key Findings (Tier II: ADHD vs. Typically Developing)

319 studies total across all tiers; Tier II (ADHD vs. TD) breakdown:

**Best-case (bias- and artifact-corrected) estimates, by age group:**

- Children/adolescents: **g = 0.76, 95% CI [0.68, 0.84]** — medium-to-large effect,
  ~55% population overlap (i.e., only 45% of ADHD children fall outside the TD range
  on RT variability).
- Adults: **g = 0.46, 95% CI [0.31, 0.61]** — ~70% population overlap.
- Age-group difference is itself significant (child/adolescent vs. adult, p < .01).
- After accounting for Age Group, no significant residual heterogeneity remained in
  either subsample — Age Group is effectively the only real moderator.

**By variability metric (moderator analysis, all ages pooled):**

- Spectral power-based metrics: g = 0.63 [0.35, 0.90], k = 9
- SD/SE: g = 0.70 [0.62, 0.77], k = 253
- CV (coefficient of variation): g = 0.78 [0.63, 0.93], k = 35
- Tau: g = 0.99 [0.64, 1.34], k = 8

**Tier III (ADHD vs. clinical control):** g = 0.25 [0.09, 0.41] for children (82%
overlap); adults/adolescents non-significant (95% CI includes 0).

**Medication effect:** stimulant-medicated ADHD children vs. TD — g = 0.12 [-0.09,
0.33], not significantly different from TD in 9/12 studies.

---

## Implications for Parameters

### rt_variability (ADHD preset, current value: 0.45)

- **Correction:** `docs/EVIDENCE_TABLE.md` and `src/presets.py` cite g = 0.76
  **[0.63, 0.88]** — the actual 95% CI in the paper is **[0.68, 0.84]** (child/
  adolescent best-case estimate, the age group most relevant to the preset). Fixed
  in EVIDENCE_TABLE.
- **Decision:** value unchanged (0.45) — this is a downstream simulation parameter,
  not a direct CV readout, so no scale-mapping claim is being verified here, only
  the citation's effect size and CI.
- **Confidence: HIGH, confirmed.** This is a large (319-study), robust, low-heterogeneity
  meta-analytic estimate — among the best-supported parameters in the whole preset
  collection.

### base_accuracy (ADHD preset, current value: 0.80) — MISCITED, see huang-pollock2012_EXTRACTED.md

- Kofler et al. (2013) is exclusively about RT variability (CV, SD/SE, tau, spectral
  power); it does not report omission-error rates or any accuracy metric. The
  "2-3x higher [omission errors]" claim attached to Kofler in `docs/EVIDENCE_TABLE.md`
  line 88 and the "Kofler meta-analysis - omission errors quantified" comment in
  `src/presets.py` PARAMETER_CONFIDENCE are both misattributed.
- The correct source for omission-error / accuracy data is Huang-Pollock et al.
  (2012), which does report exact hit rates (see that extraction file). Recommend
  re-citing `base_accuracy` to Huang-Pollock et al. (2012) instead of Kofler et al.
  (2013).

---

## Quality Assessment

- [x] Very large sample (319 studies; Tier II alone: thousands of participants)
- [x] Control group included (TD comparison, Tier II)
- [x] Bias correction performed (sampling error, measurement unreliability, publication bias)
- [x] Moderator analysis performed (age group explains nearly all heterogeneity)
- [x] Effect sizes and 95% CIs reported directly
- [x] Statistical significance established

**Overall Quality:** HIGH

---

## Notes

- The 95% CI correction above ([0.68, 0.84] not [0.63, 0.88]) should be propagated
  to `docs/EVIDENCE_TABLE.md`.
- The paper explicitly cautions that RT variability performs poorly as an individual
  diagnostic tool (100% negative predictive power but only 45% positive predictive
  power at a TD-range cutoff) — worth keeping in mind for any "appropriate use"
  language in project docs.
