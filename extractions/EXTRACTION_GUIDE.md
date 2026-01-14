# Extraction Guide

## How to Extract Data

### Step 1: Open the PDF
- Use preview/Acrobat to open the PDF
- Have the extraction template open alongside

### Step 2: Locate Key Information

**For Cortisol/Stress Papers (corbett2009):**
1. Find the Methods section - note measurement details
2. Look for Results tables with cortisol values
3. Find figures showing cortisol trajectories
4. Extract: Mean, SD, N for each group and timepoint
5. Note statistical tests and p-values

**For Meta-Analysis Papers (huang-pollock2012):**
1. Find the meta-analysis summary table
2. Look for forest plots with effect sizes
3. Extract: Overall effect size (d or g), 95% CI, N studies
4. Note heterogeneity statistics (I², Q)
5. Look for moderator analyses

### Step 3: Fill in Template
- Copy exact values from paper
- Include page numbers
- Quote key sentences
- Note any caveats or limitations

### Step 4: Quality Check
- Verify sample sizes are reasonable
- Check if control group is comparable
- Ensure units are clear
- Confirm calculations if doing conversions

### Step 5: Recommend Updates
- Compare extracted value to current parameter
- Calculate conversion if needed (see SCALE_MAPPINGS.md)
- Recommend new value with justification

## Common Pitfalls

❌ **Wrong units:** Cortisol can be in μg/dL, nmol/L, or ng/mL
❌ **Missing context:** Always note baseline, condition, timepoint
❌ **Pooling inappropriately:** Don't average across incompatible conditions
❌ **Ignoring moderators:** Age, medication status matter

## Example Extraction

```markdown
### asd_stress_baseline

**Extracted Values:**
Control/Typical Group:
  Mean (SD): 0.45 (0.18) μg/dL
  N: 28
  
ASD Group:
  Mean (SD): 0.68 (0.24) μg/dL
  N: 38
  
Effect Size:
  Type: Cohen's d
  Value: 1.08
  95% CI: [0.54, 1.62]
  
Statistical Test:
  Test type: Independent t-test
  Statistic: t(64) = 3.89
  p-value: p < .001

**Direct Quote:**
> "Children with ASD showed significantly elevated cortisol 
> at baseline (M = 0.68, SD = 0.24) compared to typically 
> developing children (M = 0.45, SD = 0.18), t(64) = 3.89, 
> p < .001, d = 1.08" (p. 8)

**Notes:**
- Measured in morning (9-11am)
- Children ages 8-12
- ASD diagnosis confirmed by ADOS
- Saliva samples, assayed by ELISA
```

## Converting to Simulation Units

See `docs/SCALE_MAPPINGS.md` for conversion formulas.

Example:
```python
# Cortisol literature value: 0.68 μg/dL (ASD)
# Baseline for NT: 0.45 μg/dL
# Simulation needs stress level (0-1 scale)

# Convert to relative elevation
elevation_ratio = 0.68 / 0.45  # = 1.51 (51% higher)

# Map to stress scale (0-1, where 0.5 = typical baseline)
asd_stress_baseline = 0.5 * elevation_ratio  # = 0.76

# Round to 2 decimals
asd_stress_baseline = 0.76
```

## After Extraction

1. Save completed extraction file
2. Update `docs/EVIDENCE_TABLE.md` with status ✅
3. Update `src/rpm_ee/clinical/presets.py` if values change
4. Document changes in git commit
5. Run tests to ensure no breaking changes
