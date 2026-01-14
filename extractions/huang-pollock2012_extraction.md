# Extraction Template: huang-pollock2012

**Paper:** Evaluating vigilance deficits in ADHD
**Date Extracted:** 2026-01-14
**Extractor:** [Your name]

---


KEY DATA TO EXTRACT:

1. Vigilance Decrement
   - Performance decline over time (slope)
   - RT increase per minute/block
   - Accuracy decline per minute/block
   
2. Overall Performance
   - Mean RT (ADHD vs control)
   - RT variability (SD or coefficient of variation)
   - Error rates (omission, commission)
   
3. Effect Sizes
   - Meta-analytic d for vigilance deficit
   - Meta-analytic d for RT variability
   
4. Sample Characteristics
   - Total N across studies
   - Age ranges
   - Task types (CPT, sustained attention)

LOOK FOR:
- Meta-analysis summary statistics table
- Forest plots with effect sizes
- Vigilance slope analyses
- Heterogeneity statistics
            

---

## Parameters to Extract

### adhd_attention_stability

**What to extract:**
- Mean/median values
- Standard deviations
- Sample sizes (n)
- Effect sizes (Cohen's d, Hedges' g, etc.)
- Confidence intervals
- p-values
- Group comparisons (if applicable)

**Location in paper:**
- [ ] Abstract
- [ ] Methods section
- [ ] Results section
- [ ] Tables (which table: ______)
- [ ] Figures (which figure: ______)

**Extracted Values:**
```
Control/Typical Group:
  Mean (SD): _____
  N: _____
  
Clinical/ASD/ADHD Group:
  Mean (SD): _____
  N: _____
  
Effect Size:
  Type: [Cohen's d / Hedges' g / other]
  Value: _____
  95% CI: [_____, _____]
  
Statistical Test:
  Test type: _____
  Statistic: _____
  p-value: _____
```

**Direct Quote (with page number):**
> "..." (p. ___)

**Notes/Caveats:**
- 

---

### adhd_vigilance_decrement

**What to extract:**
- Mean/median values
- Standard deviations
- Sample sizes (n)
- Effect sizes (Cohen's d, Hedges' g, etc.)
- Confidence intervals
- p-values
- Group comparisons (if applicable)

**Location in paper:**
- [ ] Abstract
- [ ] Methods section
- [ ] Results section
- [ ] Tables (which table: ______)
- [ ] Figures (which figure: ______)

**Extracted Values:**
```
Control/Typical Group:
  Mean (SD): _____
  N: _____
  
Clinical/ASD/ADHD Group:
  Mean (SD): _____
  N: _____
  
Effect Size:
  Type: [Cohen's d / Hedges' g / other]
  Value: _____
  95% CI: [_____, _____]
  
Statistical Test:
  Test type: _____
  Statistic: _____
  p-value: _____
```

**Direct Quote (with page number):**
> "..." (p. ___)

**Notes/Caveats:**
- 

---

### adhd_response_variability

**What to extract:**
- Mean/median values
- Standard deviations
- Sample sizes (n)
- Effect sizes (Cohen's d, Hedges' g, etc.)
- Confidence intervals
- p-values
- Group comparisons (if applicable)

**Location in paper:**
- [ ] Abstract
- [ ] Methods section
- [ ] Results section
- [ ] Tables (which table: ______)
- [ ] Figures (which figure: ______)

**Extracted Values:**
```
Control/Typical Group:
  Mean (SD): _____
  N: _____
  
Clinical/ASD/ADHD Group:
  Mean (SD): _____
  N: _____
  
Effect Size:
  Type: [Cohen's d / Hedges' g / other]
  Value: _____
  95% CI: [_____, _____]
  
Statistical Test:
  Test type: _____
  Statistic: _____
  p-value: _____
```

**Direct Quote (with page number):**
> "..." (p. ___)

**Notes/Caveats:**
- 

---

## Quality Assessment

- [ ] Sample size adequate (n > 20 per group)
- [ ] Control group included
- [ ] Effect size reported or calculable
- [ ] Replication of prior findings
- [ ] Clear measurement methodology

## Confidence Rating

After extraction, rate confidence:
- [ ] HIGH - Direct measurement, large sample, clear methodology
- [ ] MODERATE - Indirect measure, adequate sample, some ambiguity
- [ ] LOW - Small sample, unclear methods, high variability

## Update Required

Based on extraction:
- [ ] Current parameter value is CORRECT
- [ ] Current parameter value needs ADJUSTMENT to: _____
- [ ] Parameter needs RECALCULATION using: _____

---

## Conversion to Simulation Units

**Parameter:** {parameters[0] if parameters else "____"}
**Current Value:** _____
**Literature Value:** _____
**Scale/Units:** _____

**Conversion Formula:**
```
simulation_value = literature_value * conversion_factor
where conversion_factor = _____
```

**Justification for conversion:**


**New Recommended Value:** _____

