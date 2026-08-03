# Parameter Mappings: Literature → Simulation

**Purpose:** Canonical reference for how clinical/behavioral literature values map
to RPM-EE simulation parameters, and how confident each mapping is.
**Source of truth:** `src/presets.py` (`CLINICAL_PRESETS`, `PARAMETER_CONFIDENCE`).
This document is generated from, and must stay in sync with, that module --
if they disagree, `src/presets.py` wins.

Related, more granular references (conversion *functions*, worked examples,
extraction templates) predate this document and remain useful supplementary
detail, but may drift from `src/presets.py`'s current confidence levels over
time -- treat this file as the current summary:

- `docs/SCALE_MAPPINGS.md` -- literature→parameter conversion functions with
  worked examples (cortisol→stress, PANAS→affect, etc.)
- `docs/PARAMETER_SCALES.md` -- scale/range/clinical-interpretation reference
  per parameter
- `docs/EVIDENCE_TABLE.md` -- per-citation extraction status/effect sizes

## Confidence levels

- **HIGH**: meta-analytic support or multiple direct studies with quantitative values
- **MODERATE**: single study or indirect evidence with reasonable inference
- **LOW**: theoretical estimate, no direct empirical measurement, or an
  approximate scale conversion (e.g. cortisol → 0-1) with no validation

Confidence is assigned **per preset per parameter** -- the same parameter
(e.g. `wm_capacity`) can be HIGH confidence for one clinical group and LOW
for another, depending on what the cited literature actually measured for
that group. Values below are read directly from `src/presets.py`'s
`CLINICAL_PRESETS` and `PARAMETER_CONFIDENCE` dicts.

---

## Stress parameters

`stress_baseline`, `stress_reactivity`, `stress_recovery` — all normalized
to `[0, 1]`. None of the underlying literature reports directly on a 0-1
scale; every value here is a scale-mapping judgment call, which is why
confidence tops out at MODERATE across all four presets.

| Preset | stress_baseline | stress_reactivity | stress_recovery |
|---|---|---|---|
| neurotypical | 0.30 (LOW) | 0.50 (LOW) | 0.15 (LOW) |
| asd_typical | 0.50 (MODERATE) | 0.60 (MODERATE) | 0.08 (**HIGH**) |
| adhd_typical | 0.35 (MODERATE) | 0.75 (MODERATE) | 0.10 (LOW) |
| mdd_typical | 0.55 (**HIGH**) | 0.65 (MODERATE) | 0.06 (MODERATE) |

**Literature notes:**

- **neurotypical**: McEwen (1998) is a theoretical allostatic-load framework,
  not a source of quantitative baseline/reactivity numbers -- hence LOW on
  both. `stress_recovery` has no cited time-course data.
- **asd_typical**: Corbett et al. (2009)'s Fig. 4 does *not* show a clean
  ASD > NT ordering at baseline (downgraded from an earlier HIGH), and the
  reactivity increase (S1→S2) is a modest effect in ASD subgroups, not the
  paper's headline result -- both MODERATE. `stress_recovery` is the one HIGH
  confidence value in this table: Corbett et al. found a significant
  Diagnosis × Age interaction (p<0.0005) where older-ASD children fail to
  show the normal cortisol decline.
- **adhd_typical**: Lackschewitz et al. (2008) provides direct physiological
  stress-response data (MODERATE for baseline/reactivity), but does not
  quantify a recovery rate -- `stress_recovery` is LOW, "impaired regulation"
  noted qualitatively only.
- **mdd_typical**: Burke et al. (2005) is a 361-study cortisol meta-analysis
  -- the strongest evidence base in this table, hence HIGH for
  `stress_baseline`. Reactivity and recovery are documented (HPA
  dysregulation, prolonged elevation) but not with the same quantitative
  precision, hence MODERATE.

**Example mapping (illustrative, not validated)** -- basal cortisol (μg/dL)
to `stress_baseline`, linear against a 0-50 μg/dL range:

```python
def cortisol_to_stress_baseline(cortisol_ugdl: float) -> float:
    return min(1.0, max(0.0, cortisol_ugdl / 50.0))

cortisol_to_stress_baseline(15)    # 0.30 -- NT healthy baseline
cortisol_to_stress_baseline(27.5)  # 0.55 -- MDD elevated (Burke et al. 2005)
```

See `docs/SCALE_MAPPINGS.md` for the corresponding `stress_reactivity` and
`stress_recovery` conversion functions and an alternate Perceived Stress
Scale (PSS-10) mapping for `stress_baseline`.

---

## RT parameters

`base_rt` (ms), `rt_variability` (coefficient of variation), `rt_slowing`
(multiplier, 1.0 = no change vs. neurotypical).

| Preset | base_rt | rt_variability | rt_slowing |
|---|---|---|---|
| neurotypical | 500.0 (**HIGH**) | 0.15 (MODERATE) | 1.00 (n/a, baseline) |
| asd_typical | 575.0 (MODERATE) | 0.18 (MODERATE) | 1.15 (MODERATE) |
| adhd_typical | 520.0 (MODERATE) | 0.45 (**HIGH**) | 1.04 (MODERATE) |
| mdd_typical | 600.0 (MODERATE) | 0.20 (LOW) | 1.20 (MODERATE) |

**Literature notes:**

- `base_rt` and `rt_variability` map directly onto the DDM's inputs (see
  `src/ddm.py`'s EZ-diffusion parameter recovery) -- no scale conversion, so
  confidence here tracks the strength of the underlying study, not a mapping
  judgment call.
- **neurotypical** `base_rt`: Ratcliff & McKoon (2008) is a comprehensive
  review of two-choice RT tasks (400-600ms simple tasks) -- HIGH.
- **adhd_typical** `rt_variability`: Kofler et al. (2013) is a meta-analysis
  across 319 studies specifically quantifying RT variability (IIV) in ADHD
  -- the strongest single data point in this document, HIGH.
- **mdd_typical** `rt_variability`: no meta-analytic CV data for depression
  specifically was found; 0.20 is a moderate upward adjustment from the NT
  baseline reflecting general psychomotor slowing literature, not a direct
  CV measurement -- LOW.
- `rt_slowing` is derived as `1 + percent_slowing/100` from each preset's
  cited percent-slowing claim (e.g. ASD "+15%" → 1.15, MDD "+20%" → 1.20);
  see `docs/SCALE_MAPPINGS.md` for the conversion function. Confidence
  tracks the underlying percent-slowing claim's evidence quality, not the
  arithmetic (which is exact).

---

## Working memory

`wm_capacity` (items), `wm_decay_rate` (per-tick decay, no direct literature
correlate).

| Preset | wm_capacity | wm_decay_rate |
|---|---|---|
| neurotypical | 4.0 (**HIGH**) | 0.010 (LOW) |
| asd_typical | 4.0 (MODERATE) | 0.015 (LOW) |
| adhd_typical | 3.0 (**HIGH**) | 0.018 (LOW) |
| mdd_typical | 3.5 (MODERATE) | 0.022 (LOW) |

**Miller (1956) vs. Cowan (2001):** earlier versions of this module cited
both Miller's "magical number seven" (7±2 items) and Cowan's "magical number
four" (4±1 items) for the same `neurotypical` baseline -- an internal
contradiction (see the resolved WM-capacity-contradiction issue). All
presets are now standardized on **Cowan (2001)**'s 4±1 modern consensus;
Miller's 7±2 has been removed as a citation throughout, including from the
runtime defaults in `src/memory.py`/`src/memory_vectorized.py`, which
previously carried a stale `capacity = 7` fallback unrelated to
`src/presets.py`'s already-correct values.

**Literature notes:**

- **neurotypical**: Cowan (2001) is seminal and widely replicated -- HIGH.
- **asd_typical**: Steele et al. (2007) directly studied spatial WM in
  autism and found *intact capacity* with impaired manipulation -- the
  capacity value (unchanged from NT) is MODERATE because it's a direct WM
  study, even though the finding is "no difference."
- **adhd_typical**: Kasper et al. (2012) is a meta-analysis of WM deficit
  moderators in ADHD, giving the ~1-item-below-NT estimate -- HIGH.
- **mdd_typical**: Christopher & MacDonald (2005) is a single direct WM
  study (not a meta-analysis) -- MODERATE.
- `wm_decay_rate` has no literature correlate in any preset (no study
  reports a "per-simulation-tick" WM decay rate) -- LOW across the board,
  values are tuned to produce plausible relative decay ordering rather than
  derived from data. See `docs/SCALE_MAPPINGS.md` for the explicit
  disclaimer and heuristic used.

---

## Affective and exploration-related parameters

`positive_affect`, `negative_affect`, `reward_sensitivity`,
`prediction_error_gain`, `exploration_rate` -- all normalized to `[0, 1]`
(`prediction_error_gain` extends above 1.0 as a gain multiplier).

| Preset | positive_affect | negative_affect | reward_sensitivity | prediction_error_gain | exploration_rate |
|---|---|---|---|---|---|
| neurotypical | 0.60 (LOW) | 0.20 (LOW) | 0.70 (LOW) | 1.00 (LOW) | 0.20 (LOW) |
| asd_typical | 0.50 (LOW) | 0.35 (LOW) | 0.55 (LOW) | 0.90 (LOW) | 0.12 (LOW) |
| adhd_typical | 0.55 (LOW) | 0.30 (LOW) | 0.85 (MODERATE) | 1.20 (LOW) | 0.40 (MODERATE) |
| mdd_typical | 0.25 (**HIGH**) | 0.55 (MODERATE) | 0.15 (MODERATE) | 0.70 (LOW) | 0.08 (LOW) |

**Literature notes:**

- **mdd_typical** `positive_affect`: Treadway & Zald (2011) is a
  comprehensive anhedonia review specifically addressing blunted positive
  affect in depression -- the one HIGH-confidence value in this table.
  `reward_sensitivity` (also Treadway & Zald) and `negative_affect` are
  MODERATE, supported by the same and related depression literature but
  less directly quantified for the 0-1 scale used here.
- **adhd_typical** `reward_sensitivity` and `exploration_rate`: both
  MODERATE, inferred from Sonuga-Barke (2005)'s delay-aversion theory --
  a specific, citable theoretical account, but not a direct psychometric
  measurement of "reward sensitivity" or "exploration rate" as scaled here.
- **All other cells are LOW.** `prediction_error_gain` and
  `exploration_rate` in particular have **no direct empirical measure in
  any cited study, for any preset** -- every value is a theoretical estimate
  from qualitatively related constructs (e.g. ADHD impulsivity → higher
  `exploration_rate`; MDD rumination → lower `exploration_rate`). Treat
  simulation outputs that are primarily driven by these two parameters as
  hypothesis-generating only, not literature-validated predictions. See
  `docs/SCALE_MAPPINGS.md`'s `exploration_rate` section for the full
  caveat and a suggested validation paradigm.

---

## Other parameters (not in the issue's scope, included for completeness)

`src/presets.py` also defines confidence levels for parameters this
document's source issue didn't call out explicitly. Summarized briefly
since the same "check `src/presets.py` for current values" principle
applies:

- **Accuracy** (`base_accuracy`, `accuracy_decline`): mostly MODERATE, from
  Luce (1986)'s general cognitive-psych baselines, with one HIGH exception:
  `adhd_typical.base_accuracy`, via the Kofler et al. (2013) meta-analysis
  quantifying omission errors directly.
- **Attention/executive function** (`attention_stability`, `switch_cost`,
  `vigilance_decrement`): ADHD's `attention_stability` and
  `vigilance_decrement` are HIGH/MODERATE respectively via Huang-Pollock et
  al. (2012)'s direct vigilance-task measurement; everything else in this
  group is LOW-MODERATE, mostly theoretical estimates from qualitative
  flexibility/switching claims.
- **Bayesian precision parameters** (`sensory_precision`, `prior_precision`,
  `volatile_precision`, `precision_learning_rate`) and **TD-learning
  parameters** (`td_alpha`, `td_gamma`, `td_initial_value`): almost entirely
  LOW, with a handful of MODERATE values inferred from related qualitative
  literature (e.g. ASD `sensory_precision`/`prior_precision` from Robertson
  & Baron-Cohen 2017 and Pellicano & Burr 2012's weak-central-coherence
  account). These are the newest parameter groups (Phase 3/4 additions) and
  have the least direct empirical grounding of any group in this document --
  treat comparisons that hinge on them as illustrative of the computational
  mechanism (precision-weighting, TD value learning), not as validated
  clinical predictions.

---

## Full per-parameter, per-preset confidence table

For completeness, this is the exact content of `PARAMETER_CONFIDENCE` in
`src/presets.py` at time of writing -- use `get_parameter_confidence(preset,
param)` or `get_preset_summary(preset)` to query it programmatically instead
of trusting this table to stay current indefinitely.

| Parameter | neurotypical | asd_typical | adhd_typical | mdd_typical |
|---|---|---|---|---|
| base_rt | HIGH | MODERATE | MODERATE | MODERATE |
| rt_variability | MODERATE | MODERATE | HIGH | LOW |
| rt_slowing | HIGH | MODERATE | MODERATE | MODERATE |
| base_accuracy | MODERATE | MODERATE | HIGH | MODERATE |
| accuracy_decline | MODERATE | LOW | MODERATE | MODERATE |
| wm_capacity | HIGH | MODERATE | HIGH | MODERATE |
| wm_decay_rate | LOW | LOW | LOW | LOW |
| attention_stability | LOW | MODERATE | HIGH | MODERATE |
| switch_cost | LOW | MODERATE | MODERATE | MODERATE |
| vigilance_decrement | LOW | LOW | MODERATE | LOW |
| stress_baseline | LOW | MODERATE | MODERATE | HIGH |
| stress_reactivity | LOW | MODERATE | MODERATE | MODERATE |
| stress_recovery | LOW | HIGH | LOW | MODERATE |
| positive_affect | LOW | LOW | LOW | HIGH |
| negative_affect | LOW | LOW | LOW | MODERATE |
| reward_sensitivity | LOW | LOW | MODERATE | MODERATE |
| prediction_error_gain | LOW | LOW | LOW | LOW |
| exploration_rate | LOW | LOW | MODERATE | LOW |
| sensory_precision | LOW | MODERATE | LOW | LOW |
| prior_precision | LOW | MODERATE | LOW | MODERATE |
| volatile_precision | LOW | LOW | LOW | LOW |
| precision_learning_rate | LOW | LOW | LOW | LOW |
| td_alpha | LOW | LOW | MODERATE | MODERATE |
| td_gamma | LOW | LOW | MODERATE | LOW |
| td_initial_value | LOW | LOW | LOW | MODERATE |

**Tally:** 10 HIGH, 39 MODERATE, 51 LOW, out of 100 preset×parameter cells
(4 presets × 25 parameters each). See `src/presets.py`'s module docstring
for its own aggregate confidence-level summary (counted per-parameter
rather than per-preset×parameter).
