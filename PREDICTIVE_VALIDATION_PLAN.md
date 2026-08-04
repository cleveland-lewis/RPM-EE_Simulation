# Predictive Validation Plan - Phase 3

**Date:** 2026-01-14  
**Status:** Ready to Execute  
**Script:** `scripts/predictive_validation.py`

---

## Overview

Predictive validation tests whether clinical preset simulations produce
behavioral outputs that match expected patterns from the literature. This
is the critical test of whether our parameter configurations are
reasonable.

---

## Methodology

### 1. Run Simulations

- **Presets:** Neurotypical, ADHD, ASD, MDD
- **Trials per preset:** 200
- **Task:** Simple RT task with WM load and attention demands

### 2. Extract Behavioral Metrics

From each simulation, extract:

- **RT metrics:** Mean RT, RT-CV (coefficient of variation)
- **Accuracy:** Mean accuracy, error rates
- **WM performance:** Working memory load handling
- **Attention:** Mean attention, lapses, sustained attention decline
- **Stress:** Baseline stress, reactivity to stressors
- **Reward learning:** Response to positive outcomes

### 3. Compare to Literature Patterns

For each clinical preset, validate against expected patterns:

#### ADHD Expected Patterns

1. **RT-CV:** 40% higher than NT (±15%)
   - Literature: Kofler et al., 2013 (35-50% higher)
2. **Attention lapses:** 2x higher than NT (±50%)
   - Literature: Huang-Pollock et al., 2012 (2-3x omission errors)
3. **WM performance:** 25% lower than NT (±10%)
   - Literature: Kasper et al., 2012 (~1 item reduction, d=-0.67)
4. **Sustained attention decline:** 15% decline over time (±8%)
   - Literature: Huang-Pollock et al., 2012 (vigilance decrements)

#### ASD Expected Patterns

1. **Switch cost:** 30% higher than NT (±15%)
   - Literature: Geurts et al., 2009 (reduced flexibility)
2. **Stress reactivity:** 50% higher than NT (±20%)
   - Literature: Corbett et al., 2009 (χ²(4)=22.76, P<0.0005)
3. **Mean RT:** 12.5% slower than NT (±7.5%)
   - Literature: Happé & Frith, 2006 (10-15% slower)

#### MDD Expected Patterns

1. **Mean RT:** 17.5% slower than NT (±7.5%)
   - Literature: Tsourtos et al., 2002 (15-20% psychomotor slowing)
2. **Accuracy:** 7.5% lower than NT (±2.5%)
   - Literature: Porter et al., 2003 (5-10% reduction)
3. **Reward learning:** 60% reduced vs NT (±20%)
   - Literature: Treadway & Zald, 2011 (anhedonia)
4. **WM performance:** 12.5% lower than NT (±7.5%)
   - Literature: Christopher & MacDonald, 2005 (~0.5 item reduction)

### 4. Validation Criteria

- **PASS:** Deviation within tolerance
- **MARGINAL:** Deviation within 1.5x tolerance  
- **FAIL:** Deviation exceeds 1.5x tolerance

**Preset passes if ≥75% of patterns validated**  
**Overall validation passes if ≥75% of presets pass**

---

## Execution Instructions

### Run the script

```bash
cd /Users/clevelandlewis/Documents/Academic/Research/RPM-EE
python scripts/predictive_validation.py
```

### Expected output

1. **Console:** Real-time progress and validation results
2. **JSON:** `results/validation/predictive_validation_results.json`
3. **Report:** `results/validation/predictive_validation_report.md`

### Estimated runtime

- ~2-3 minutes (200 trials × 4 presets = 800 trials)

---

## Expected Results

Based on our parameter configurations:

### Likely PASS

- **Neurotypical:** Baseline (by definition)
- **ADHD:** Strong literature support for all parameters
- **ASD:** Good support, minor stress reactivity uncertainty

### Potential Issues

- **MDD:** Reward sensitivity may need adjustment
  - Current: 0.35
  - Expected for validation: ~0.15
  - Already identified in face validation

---

## Interpreting Results

### If validation passes (≥75%)

✓ **Conclusion:** Parameter configurations are reasonable and produce expected clinical patterns

**Next steps:**

1. Proceed to confidence quantification
2. Document validation in main documentation
3. Consider Phase 3 complete (predictive validation done)

### If validation fails (<75%)

✗ **Conclusion:** Some parameter adjustments needed

**Next steps:**

1. Identify which patterns failed
2. Review literature for those specific parameters
3. Adjust parameters within evidence bounds
4. Re-run validation
5. Document adjustments and rationale

---

## Integration with Phase 3

**Phase 3 Progress:**

- ✅ Sensitivity analysis (100%)
- ✅ Parameter scale documentation (100%)
- ✅ Face validation (100%)
- ⏳ **Predictive validation (0%)** ← THIS STEP
- ⏳ Confidence quantification (0%)

**After predictive validation:**

- Phase 3 will be ~75% complete
- Only confidence quantification remains
- ~2-3 hours to full Phase 3 completion

---

## Technical Details

### Simulation Parameters

- **Trial structure:** Simple RT task
- **WM load:** Varies by capacity
- **Attention demands:** Sustained attention required
- **Stressors:** Periodic (every 20 trials)
- **Reward schedule:** Random 50%

### Metric Computation

- **RT-CV:** std(RT) / mean(RT)
- **Attention lapses:** Proportion of trials with attention < 0.5
- **Sustained attention decline:** (first_half - second_half) / first_half
- **Stress reactivity:** max(stress) - min(stress)
- **WM performance:** Mean normalized load handled

### Statistical Approach

- Compare each clinical preset to neurotypical baseline
- Compute relative magnitude: (clinical - baseline) / baseline
- Compare to expected magnitude from literature
- Tolerance bands allow for simulation noise

---

## Advantages of This Approach

1. **Empirically grounded:** Every expectation has literature citation
2. **Quantitative:** Specific magnitudes and tolerances
3. **Tolerant:** Allows for simulation noise and approximation
4. **Comprehensive:** Tests multiple behavioral dimensions
5. **Interpretable:** Clear pass/fail criteria

---

## Limitations

1. **Simplified task:** Real clinical tasks are more complex
2. **Group means:** Individual differences not captured
3. **No external data:** Validation against simulation, not real clinical data
4. **Parameter interdependence:** Changes to one parameter affect others

---

## Real-Data Validation (Non-Circular, Separate From the Above)

Everything above compares simulation output to *literature-derived*
expectations -- the same magnitudes used to set the parameters in the first
place, so it's a circular consistency check, not independent validation
(see the note in README.md's Quick Start).

A separate, non-circular validation track runs the simulation against
*real downloaded behavioral data* instead:

- **`src/adapters/`** -- `TaskAdapter`s that parse a dataset's raw files
  into `(evidence, load, difficulty)` inputs the DDM understands
  (`src/adapters/base.py`).
- **`ds003500`** (OpenNeuro, CC0) -- response inhibition / selective
  attention, ADHD vs. control. Adapter: `src/adapters/ds003500.py`.
  Validation script: `scripts/validate_ds003500.py` (feeds real blocks
  through the matched clinical preset's DDM, compares real vs. simulated
  RT/accuracy distributions with a two-sample KS test).
- **`ds005356`** (OpenNeuro, MEG probabilistic selection task) -- adapter
  only (`src/adapters/ds005356.py`); no validation script yet, since the
  public `participants.tsv` has no per-subject MDD/control label in this
  release.

Download and run instructions are in README.md, "Empirical Validation
Against Real Data".

### Stated limitations of the ds003500 validation

These are modeling/data constraints inherent to the dataset, not bugs, and
they should be repeated wherever ds003500 validation results are reported
(full detail in `src/adapters/ds003500.py`'s module docstring, which is the
source of truth -- this is a summary, not a replacement):

1. **Block-level, not trial-level, granularity.** `events.tsv` rows are
   18-trial blocks with pre-aggregated `response_time_avg`/`correct_total`,
   not individual trials -- there's no way to recover single-trial
   RT/accuracy from this dataset. The DDM's per-trial `predict_action()` is
   therefore run `TRIALS_PER_BLOCK` (18) times and averaged per block, so
   both sides of the comparison represent a block-level mean rather than a
   real trial vs. one noisy simulated draw. Effective sample size is n=12
   blocks per subject per task family, not n=18×12 trials.
2. **Evidence/load mapping is a modeling choice, not a direct measurement.**
   The dataset gives a confirmed task manipulation (go/no-go for Inh,
   single/array for Sel), but mapping "harder condition" to the DDM's
   `difficulty` input (rather than `load`) is a deliberate choice grounded
   in which input produces the correct slower-and-less-accurate direction
   (see `src/ddm.py`'s `predict_action` docstring and GitHub issue #6) --
   it is not something read off the data. `load` is left at 0.0 throughout
   this adapter, since ds003500 has no independent working-memory-load
   manipulation to map it to.
3. **Inh and Sel are never pooled.** Response inhibition (Inh) and
   visual-search/feature-selection (Sel) are different cognitive demands
   funneled through the DDM's single `difficulty` axis -- a real limitation
   of comparing against a DDM with only one difficulty dimension, not an
   oversight to silently fix. Results are always reported per task family.

## Future Enhancements

After Phase 3 completion:

1. **Task diversity:** Test on multiple cognitive tasks
2. **Developmental trajectories:** Age-related changes
3. **Individual differences:** Within-population variability
4. **Treatment effects:** Parameter changes under intervention

---

## Success Criteria

**Minimum for Phase 3:**

- ✓ Predictive validation implemented
- ✓ At least 75% of presets pass validation
- ✓ Results documented in JSON and markdown
- ✓ Any failures explained and addressed

**Ideal outcome:**

- ✓ 100% of presets pass validation
- ✓ All patterns within expected ranges
- ✓ Publication-quality validation report
- ✓ Clear documentation of methodology

---

## Action Items

**Immediate (this session):**

1. ☐ Run `scripts/predictive_validation.py`
2. ☐ Review validation results
3. ☐ Adjust any failing parameters (if needed)
4. ☐ Re-run validation if adjustments made
5. ☐ Update PHASE3_PROGRESS.md

**Next session:**

1. ☐ Implement confidence quantification
2. ☐ Complete Phase 3 documentation
3. ☐ Prepare for Phase 4 (documentation updates)

---

**Status:** Script ready, awaiting execution  
**Estimated completion:** <15 minutes (including review)  
**Blocker:** None - script is complete and tested structure
