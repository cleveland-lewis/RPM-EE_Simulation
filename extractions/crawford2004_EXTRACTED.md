# Extracted Data: crawford2004

**Paper:** Crawford, J. R., & Henry, J. D. (2004). The Positive and Negative Affect
Schedule (PANAS): Construct validity, measurement properties and normative data in
a large non-clinical sample.
**Journal:** British Journal of Clinical Psychology, 43(3), 245–265.
**DOI:** 10.1348/0144665031752934
**Source:** Author's own hosted copy, University of Aberdeen
(`papers/crawford2004.pdf`)
**Extraction Date:** 2026-08-04
**Status:** ✅ Complete

---

## Normative Data (Table, "past week" time-frame, N = 1,003, UK general population)

- **Positive Affect (PA): M = 31.3, SD = 7.7**
- **Negative Affect (NA): M = 16.0, SD = 5.9**

For comparison, Watson, Clark & Tellegen's (1988) original US student-sample norms
("past few days" time-frame): PA M = 33.3 (SD 7.2), NA M = 17.4 (SD 6.2). Crawford &
Henry's UK general-population sample runs a bit lower on both scales than the
original student-sample norms — expected given the shift from a student sample to a
general adult population.

Internal consistency: PA α = .85–.90, NA α = .84–.87 (consistent with prior
literature). Two-factor (PA/NA) structure confirmed via CFA (robust CFI = .94).

Demographic effects (age, gender, education, occupation) were all statistically
significant (large N) but of negligible effect size (0.20%–2.25% variance
explained) — practically ignorable for scoring purposes.

---

## Implications for Parameters

### positive_affect (Neurotypical preset, current value: 0.60)

- **Correction:** `docs/EVIDENCE_TABLE.md` cites "PANAS PA ~33/50" — that number is
  actually Watson et al.'s (1988) *original* student-sample figure, not Crawford &
  Henry's own reported value (PA = 31.3, SD 7.7) from the paper actually being cited.
- **Recomputed mapping** using the table's existing formula, `(value − 10) / 40`
  (PANAS subscale range is 10–50): (31.3 − 10) / 40 = **0.5325** ≈ 0.53.
- **Decision:** current preset value (0.60) is ~0.07 above the literature-derived
  midpoint (0.53) — a modest but real discrepancy, not within-rounding. Flagging
  for consideration; not changed here since it affects simulation behavior and
  should be a deliberate decision, not a side effect of a citation-accuracy pass.
- **Confidence: MODERATE** (up from LOW) — now backed by an exact number from the
  cited paper, but the value itself doesn't match the preset as closely as first
  documented.

### negative_affect (Neurotypical preset, current value: 0.20)

- Same correction: EVIDENCE_TABLE's "PANAS NA ~18/50" is Watson et al.'s student
  figure; Crawford & Henry's own value is NA = 16.0 (SD 5.9).
- **Recomputed mapping:** (16.0 − 10) / 40 = **0.15**.
- **Decision:** current preset value (0.20) is ~0.05 above the literature-derived
  value (0.15). Flagged, not changed.
- **Confidence: MODERATE** (up from LOW), same caveat as positive_affect.

---

## Quality Assessment

- [x] Very large sample (N = 1,003, broadly representative of UK adult population)
- [x] Exact M/SD reported directly in text (no digitization needed)
- [x] Validated measure with established psychometrics (α = .84–.90)
- [x] Directly the paper cited in the preset docs (no substitution needed, unlike
      Huang-Pollock/Kasper)
- [ ] Not a clinical-population comparison — this is general-population normative
      data only, so it constrains the *neurotypical* baseline, not clinical presets

**Overall Quality:** HIGH

---

## Notes

- Unlike the Huang-Pollock and Kasper citations, Crawford & Henry (2004)'s title and
  content in `papers/bibliography.md` and `docs/EVIDENCE_TABLE.md` were already
  correct — only the specific M/SD numbers quoted in EVIDENCE_TABLE.md were from the
  wrong source (Watson et al. 1988, not this paper).
- Recommend a follow-up decision (separate from this extraction pass) on whether to
  adjust `positive_affect`/`negative_affect` preset values to match Crawford &
  Henry's exact normative numbers (0.53/0.15) or keep the current values (0.60/0.20)
  with the discrepancy documented.
