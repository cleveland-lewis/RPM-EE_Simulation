# Phase 2 Progress: Evidence Strengthening

**Status:** Tasks 2.2 & 2.3 Complete (Documentation Phase)  
**Date:** January 13-14, 2026  
**Time Invested:** ~3 hours

---

## Overview

Phase 2 focuses on strengthening the evidence base for clinical presets. We've completed all documentation and preparation tasks that can be done without library access. The remaining tasks (2.1 and 2.4) require accessing papers and expert consultation.

---

## Completed Tasks ✅

### Task 2.3: Document Scale Mappings ✅
**Status:** COMPLETE  
**File:** `docs/SCALE_MAPPINGS.md` (22KB, 704 lines)

**What We Did:**
- Documented explicit mapping functions for all 18 parameter types
- Provided Python code examples for each conversion
- Assigned confidence levels (🟢 Validated, 🟡 Estimated, 🔴 Theoretical)
- Identified which parameters lack empirical mappings

**Key Findings:**
- **🟢 5 parameters** have direct mappings (RT, WM capacity, accuracy)
- **🟡 7 parameters** use reasonable linear approximations (stress, affect, attention)
- **🔴 6 parameters** are theoretical with no clear empirical mapping

**Critical Discovery:**
Two parameters have **NO empirical measurement** in any study:
1. `exploration_rate` - Inferred from delay aversion/rumination
2. `prediction_error_gain` - No direct measurement exists

**Impact:**
- Transparency: Anyone can now understand and replicate parameter choices
- Extensibility: Clear formula for adding new clinical populations
- Validation Ready: Identifies which mappings need empirical testing

---

### Task 2.2: Evidence Extraction Template ✅
**Status:** COMPLETE (Template ready for extraction)  
**File:** `docs/EVIDENCE_TABLE.md` (15KB, 352 lines)

**What We Did:**
- Created systematic extraction protocol for all 72 parameters
- Assigned verification status (✅ Verified, 📋 Documented, 🔍 Needs Extraction, ❓ Uncertain)
- Prioritized papers by impact (HIGH/MEDIUM/LOW)
- Documented what to extract from each paper

**Current Verification Status:**
- ✅ Verified: 1/72 (1%) - Have accessed and extracted
- 📋 Documented: 8/72 (11%) - Have values from reviews
- 🔍 Needs Extraction: 48/72 (67%) - Have citation, need paper
- ❓ Uncertain: 15/72 (21%) - No clear source

**Top Priorities for Extraction:**
1. **Kofler et al. (2013)** - ADHD RT: Meta-analysis of 319 studies, g=0.76
2. **Burke et al. (2005)** - MDD cortisol: Meta-analysis of 361 studies, d=0.38
3. **Kasper et al. (2012)** - ADHD WM: Meta-analysis

**Expected Outcomes After Extraction:**
- Upgrade 15-20 parameters from LOW → MODERATE/HIGH confidence
- Document exact effect sizes for all meta-analyses
- Validate or revise current parameter values

---

## Remaining Tasks 🔄

### Task 2.1: Systematic Literature Search
**Status:** PENDING (Requires library access)  
**Timeline:** 2-3 weeks  
**Effort:** 40-60 hours

**What's Needed:**
1. Access all 24 cited papers (library, interlibrary loan, ResearchGate)
2. Extract quantitative values following EVIDENCE_TABLE protocol
3. Document effect sizes, confidence intervals, sample sizes
4. Update verification status in EVIDENCE_TABLE.md
5. Identify any discrepancies with current parameter values

**High-Priority Papers:**
- 3 meta-analyses (Kofler, Burke, Kasper) - Will significantly strengthen evidence
- 6 key single studies (Corbett, Huang-Pollock, Crawford, Steele, Yerys, Tsourtos)

**Search for New Literature:**
- Task-switching meta-analysis for `switch_cost` parameters
- Vigilance meta-analysis for `vigilance_decrement` rates
- Affect measures in clinical populations
- Stress recovery time-course studies

**Outcome:**
- Fill EVIDENCE_TABLE with ✅ verified values
- Upgrade PARAMETER_CONFIDENCE levels in src/presets.py
- Document any parameter revisions needed

---

### Task 2.4: Expert Consultation Prep
**Status:** PENDING (Can start once 2.1 complete)  
**Timeline:** 1 week prep, 2-4 weeks for consultations  
**Budget:** $800-1200 for 4 experts OR co-authorship offers

**What's Needed:**

**Materials to Prepare:**
1. **Expert Review Package:**
   - Parameter table with values, sources, confidence levels
   - EVIDENCE_TABLE with extracted effect sizes
   - SCALE_MAPPINGS documentation
   - 1-page summary of preset approach

2. **Consultation Protocol:**
   - 30-minute Zoom calls or email reviews
   - Structured questionnaire
   - Focus on their domain (ASD/ADHD/MDD)

3. **Recruit 3-4 Experts:**
   - ASD researcher (cortisol, sensory, WM)
   - ADHD researcher (RT variability, vigilance, WM)
   - Depression researcher (psychomotor, anhedonia, HPA)
   - Computational psychiatry expert (overall approach)

**Questions for Experts:**
1. Are parameter values reasonable for [population]?
2. Are there better/more recent sources we should use?
3. Any critical parameters we're missing?
4. Do scale mappings make sense?
5. Suggested ranges or confidence intervals?

**Outcome:**
- Expert validation of parameters
- Suggested improvements or revisions
- Potential co-authors for validation paper
- Documented expert review in `docs/EXPERT_REVIEWS.md`

---

## What We've Accomplished

### Documentation Infrastructure ✅
- ✅ Scale mappings fully documented
- ✅ Evidence extraction protocol established
- ✅ Verification status tracked
- ✅ Priorities clearly defined

### Transparency Improvements ✅
- ✅ All assumptions now explicit
- ✅ Confidence levels justified
- ✅ Parameters lacking empirical data identified
- ✅ Mapping formulas provided

### Validation-Ready ✅
- ✅ Template ready for systematic extraction
- ✅ Protocol for expert consultation defined
- ✅ Priorities clear for limited resources

---

## Critical Insights from Phase 2 So Far

### 1. Scale Mapping is a Major Challenge
**Problem:** Most simulation parameters use 0-1 scales, but literature uses various units.

**Our Solution:**
- Documented all mapping functions explicitly
- Assigned confidence to each mapping
- Identified mappings that need validation

**Example:**
```python
# Cortisol (μg/dL) → stress_baseline (0-1)
# Current: Linear mapping with arbitrary bounds
# Confidence: 🟡 Estimated, needs validation
stress = (cortisol - 0) / 50
```

**Impact:** Transparency about approximations, clear validation priorities.

---

### 2. Some Parameters Truly Lack Empirical Data
**Discovery:** 2 parameters have NO measurement paradigm:
- `exploration_rate` - No study measures "exploration" directly
- `prediction_error_gain` - No study quantifies this specific construct

**Our Response:**
- Documented as 🔴 Theoretical in all tables
- Will test sensitivity in Phase 3
- May remove if non-critical

**Lesson:** Not all conceptually reasonable parameters have empirical grounding. Need to be honest about this.

---

### 3. Meta-Analyses are Gold Standard
**Best Evidence:**
- Kofler et al. (2013): 319 studies, N=25,000+
- Burke et al. (2005): 361 studies
- These alone justify several HIGH confidence parameters

**Weakness:**
- Most parameters lack meta-analyses
- Relying on single studies or theory

**Strategy:** Prioritize meta-analytic evidence when available, acknowledge limitations when not.

---

### 4. Evidence Quality Varies Dramatically
**Current Distribution:**
- HIGH confidence: 15 parameters (21%)
- MODERATE: 32 parameters (44%)
- LOW: 25 parameters (35%)

**After Phase 2 extraction (projected):**
- HIGH: 25-30 parameters (35-42%)
- MODERATE: 30-35 parameters (42-49%)
- LOW: 12-17 parameters (17-24%)

**Goal:** Get >40% HIGH confidence, <20% LOW confidence.

---

## Next Steps

### If Continuing Phase 2 (Recommended):

**Week 1-2: High-Priority Extraction**
- [ ] Access Kofler, Burke, Kasper meta-analyses
- [ ] Extract exact values, effect sizes, CIs
- [ ] Update EVIDENCE_TABLE with ✅ verified entries
- [ ] Test if parameter values need revision

**Week 3-4: Medium-Priority Extraction**
- [ ] Access Corbett, Huang-Pollock, Crawford papers
- [ ] Extract cortisol values, vigilance slopes, PANAS norms
- [ ] Fill in EVIDENCE_TABLE for these parameters

**Week 5: Expert Consultation Prep**
- [ ] Compile materials for expert review
- [ ] Identify and contact 3-4 experts
- [ ] Prepare consultation protocol

**Week 6: Expert Consultations**
- [ ] Conduct 30-min consultations
- [ ] Document feedback
- [ ] Revise parameters based on expert input

**Week 6 End: Phase 2 Complete**
- [ ] Update PARAMETER_CONFIDENCE in code
- [ ] Update clinical_presets_v1.1.md
- [ ] Create Phase 2 completion summary
- [ ] Tag v1.1.2-enhanced

---

### If Stopping Here:

**What We Have:**
- ✅ Complete documentation infrastructure
- ✅ Clear roadmap for extraction
- ✅ Transparent about limitations
- ✅ Validation-ready

**What's Missing:**
- Actual paper access and extraction
- Expert validation
- Parameter upgrades

**Defensibility:** 
- Still defensible for research (Phase 1 fixes remain)
- Documentation shows validation plan
- Can cite "extraction in progress"

---

## Resources Needed to Complete Phase 2

### Time:
- Literature extraction: 40-60 hours (RA or self)
- Expert consultation: 10-15 hours (prep + meetings)
- Documentation updates: 10-15 hours
- **Total: 60-90 hours over 6 weeks**

### Access:
- University library or interlibrary loan
- ResearchGate for author requests
- PubMed, PsycINFO databases

### Budget (If Paying Experts):
- 4 experts × $200-300 each = $800-1200
- OR offer co-authorship on methods paper

### Alternative (No Budget):
- Skip expert consultation for now
- Focus on literature extraction only
- Can do expert review before publication

---

## Recommendation

### Option A: Complete Phase 2 (6 weeks)
**Best if:** Planning publication in next 6 months  
**Outcome:** Significantly strengthened evidence, expert-validated  
**Effort:** 60-90 hours + $800-1200 (or co-authorship)

### Option B: Extract Meta-Analyses Only (2 weeks)
**Best if:** Limited time/resources  
**Outcome:** Top 3 parameters upgraded to HIGH  
**Effort:** 15-20 hours + library access

### Option C: Skip to Phase 3 (Validation)
**Best if:** Want to test simulation-to-data fit  
**Outcome:** Empirical validation, may reveal parameter issues  
**Effort:** Different skill set (statistical analysis)

---

## Current Status Summary

**Completed:**
- ✅ Task 2.3: Scale mappings documented
- ✅ Task 2.2: Evidence extraction template

**In Progress:**
- 🔄 Task 2.1: Literature extraction (pending access)
- 🔄 Task 2.4: Expert consultation (pending completion of 2.1)

**Deliverables:**
- `docs/SCALE_MAPPINGS.md` - 22KB, comprehensive
- `docs/EVIDENCE_TABLE.md` - 15KB, systematic template

**Impact:**
- Transparency significantly improved
- Validation roadmap established
- Critical gaps identified

**Next Decision Point:**
- Continue Phase 2 with literature access?
- Move to Phase 3 validation?
- Stop and use current state?

---

**Phase 2 Progress:** 50% complete (documentation done, extraction pending)  
**Overall Project:** Phase 1 complete, Phase 2 in progress  
**Status:** Defensible and transparent, further strengthening available
