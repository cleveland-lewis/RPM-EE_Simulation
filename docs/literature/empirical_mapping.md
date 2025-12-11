# RPM-EE Empirical Mapping Guide

**Version:** 1.0
**Date:** 2025-10-27
**Purpose:** Map computational model variables to measurable clinical/experimental counterparts for empirical validation

---

## Overview

This document provides concrete, feasible measurement approaches for each key variable in the RPM-EE (Recursive Predictive Modeling with Emotional Encoding) simulation framework. These mappings enable empirical validation and calibration of the model against real-world behavioral, physiological, and self-report data.

---

## 1. Affect (avg_affect_feedback, affect_volatility)

### Computational Variables
- **`avg_affect_feedback`**: Momentary affective valence, range [-1, 1]
- **`affect_volatility`**: Short-term variability in affect (rolling standard deviation)

### Measurement Options

#### **Option A: Ecological Momentary Assessment (EMA)**
- **Instrument**: 3-item brief affect scale
  - Valence: "How positive/negative do you feel right now?" (-3 to +3)
  - Arousal: "How activated/calm do you feel right now?" (1 to 7)
  - Intensity: "How strong is your current emotion?" (1 to 7)
- **Sampling**: 5-8 prompts per day, random within waking hours
- **Volatility calculation**: Within-day SD of valence scores
- **Mapping**: Valence → `avg_affect_feedback`; Within-day SD → `affect_volatility`

#### **Option B: Laboratory Affect Induction**
- **Paradigm**: IAPS image presentation (standardized valence/arousal ratings)
- **Rating frequency**: After each image (trial-level, ~3-6 seconds each)
- **Outcome**: Trial-wise valence ratings and within-block variance
- **Mapping**: Trial valence → `avg_affect_feedback`; Block variance → `affect_volatility`

#### **Option C: Standardized Self-Report**
- **Instrument**: PANAS-X (Positive and Negative Affect Schedule - Expanded)
  - State version: "How do you feel right now?"
  - Administer at multiple timepoints (e.g., every 15-30 minutes in lab)
- **Volatility**: Difference scores or SD across repeated administrations
- **Mapping**: Net affect score (PA - NA, normalized) → `avg_affect_feedback`

### Recommended Approach
**EMA (Option A)** for ecological validity in naturalistic settings; **Lab induction (Option B)** for controlled experimental manipulation with precise timing alignment.

---

## 2. Schema Stress (stress_bounded, stress_latent)

### Computational Variables
- **`stress_bounded`**: Bounded stress [0, 1] after link function
- **`stress_latent`**: Unbounded latent stress (drive + fast surprisal components)

### Measurement Options

#### **Option A: Momentary Stress EMA**
- **Single-item**: "How stressed do you feel right now?" (0-10 scale)
- **Sampling**: Same schedule as affect EMA (5-8 times/day)
- **Mapping**: Normalized score → `stress_bounded`

#### **Option B: Perceived Stress Scale - State Version (PSS-S)**
- **Instrument**: 4-item abbreviated PSS adapted for momentary assessment
  - "In the last [time window], how often have you felt overwhelmed?"
  - "...unable to control important things?"
  - "...nervous or stressed?"
  - "...that difficulties were piling up?"
- **Response scale**: 0 (never) to 4 (very often)
- **Administration**: Every 2-4 hours or at task transitions
- **Mapping**: Mean score (normalized) → `stress_bounded`

#### **Option C: State-Trait Anxiety Inventory - State (STAI-S)**
- **Short form**: 6-item STAI-S (Marteau & Bekker, 1992)
- **Administration**: Pre/post task blocks, or hourly
- **Mapping**: Sum score (normalized to [0,1]) → `stress_bounded`

#### **Option D: Physiological Proxies (Optional Add-ons)**
- **Heart Rate Variability (HRV)**:
  - Metric: RMSSD (root mean square of successive differences in IBI)
  - Window: 2-5 minute rolling windows
  - Mapping: Inverse-normalized RMSSD → `stress_bounded` (lower HRV = higher stress)
- **Electrodermal Activity (EDA)**:
  - Metric: Tonic skin conductance level (SCL)
  - Window: 30-60 second rolling average
  - Mapping: Normalized SCL → `stress_bounded`

### Recommended Approach
**Momentary EMA (Option A)** as primary measure for simplicity and alignment with model's tick-level updates; **HRV (Option D)** as validation/convergent measure if physiological recording is feasible.

---

## 3. External Load (ext_load)

### Computational Variable
- **`ext_load`**: Precision-weighted combination of sensory channels (vision, auditory, touch), range [0, 1]

### Measurement Options

#### **Option A: Multi-Modal Oddball Task**
- **Paradigm**:
  - Present simultaneous visual + auditory stimuli with varying reliability (signal-to-noise ratio)
  - Standard (80%) vs. Oddball (20%) in each modality independently
- **Manipulation**: Vary stimulus reliability by adding noise (e.g., Gaussian noise on images; white noise on tones)
- **Observable**: Trial-level surprise = |stimulus intensity - running expectation|
- **Precision estimate**: Inverse variance of within-modality noise
- **Mapping**:
  - Weighted combination of modality-specific surprise → `ext_load`
  - Modality precision → `pi_vision`, `pi_auditory`, etc. in model

#### **Option B: Multisensory Integration Task**
- **Paradigm**: Audio-visual temporal binding window task (simultaneity judgment)
- **Manipulation**: Vary temporal asynchrony (SOA) and sensory reliability (blur, noise)
- **Observable**: PSE (point of subjective simultaneity) and slope of psychometric curve
- **Mapping**: Trial-level multisensory conflict → `ext_load`

#### **Option C: Continuous Performance Task (CPT-AX)**
- **Paradigm**: Monitor stream of letters; respond only to 'X' following 'A'
- **Load manipulation**: Vary presentation rate, add distractors, or introduce dual-task
- **Observable**: RT, accuracy, omissions, false alarms
- **Mapping**: Trial-level task demand (rate × distractor presence) → `ext_load`

### Recommended Approach
**Multi-modal oddball (Option A)** with explicit reliability manipulation, allowing direct estimation of precision-weighting parameters in the model.

---

## 4. Working Memory Load (mem_load)

### Computational Variable
- **`mem_load`**: Normalized WM buffer occupancy with capacity limit and nonlinearity (gamma), range [0, 1]

### Measurement Options

#### **Option A: N-Back Task (2-back or 3-back)**
- **Paradigm**: Continuous stream of stimuli; respond when current stimulus matches N items back
- **Observable**:
  - Accuracy (d' or percent correct)
  - RT (mean and variability)
  - Lapse rate (trials with RT > 2.5 SD above mean)
- **Load estimate**: Running buffer occupancy inferred from trial-level accuracy and RT
- **Mapping**: Trial-level load estimate → `mem_load`

#### **Option B: Complex Span (Operation Span, Reading Span)**
- **Paradigm**: Interleaved processing (math verification) and storage (remember letters)
- **Observable**:
  - Span score (total correctly recalled items)
  - Processing accuracy
  - Inter-response intervals during recall
- **Load estimate**: Current buffer occupancy = items encoded so far / capacity
- **Mapping**: Within-trial buffer occupancy → `mem_load`

#### **Option C: Dual-Task Paradigm**
- **Primary task**: Simple RT or choice RT
- **Secondary task**: Concurrent digit span or tone counting
- **Observable**:
  - Dual-task cost = (RT_dual - RT_single) / RT_single
  - Secondary task accuracy
- **Mapping**: Dual-task cost (normalized) → `mem_load`

#### **Option D: Model-Based Latent WM Load**
- **Approach**: Fit drift-diffusion model (DDM) or linear ballistic accumulator (LBA) to choice RT data
- **Latent variable**: Boundary separation (a) or drift rate (v) as proxy for cognitive resources
- **Mapping**: Trial-level boundary separation (normalized) → `mem_load`

### Recommended Approach
**N-back (Option A)** for continuous, trial-level load tracking; **Model-based DDM (Option D)** to derive principled latent load estimates.

---

## 5. Prediction Error (prediction_error)

### Computational Variable
- **`prediction_error`**: Absolute surprise on external load: |ext_load - expected|, range [0, 1]

### Measurement Options

#### **Option A: Visual/Auditory Oddball**
- **Paradigm**: Standard-oddball sequence (80/20 or 70/30 ratio)
- **Observable**:
  - Trial-level surprise (oddball trials)
  - P3b ERP amplitude (if EEG available)
- **Computational observer**: Running delta-rule or Kalman filter to estimate expectations
- **PE calculation**: |stimulus - prediction_t|
- **Mapping**: Trial PE → `prediction_error`

#### **Option B: Probabilistic Reversal Learning**
- **Paradigm**: Choose between two options; reward probabilities reverse periodically (unannounced)
- **Observable**:
  - Choice switches after reversal
  - RT increases following unexpected outcomes
- **Computational model**: Rescorla-Wagner or hierarchical Bayesian learner
- **PE**: δ_t = reward_t - Q_t (value prediction error)
- **Mapping**: Absolute δ_t → `prediction_error`

#### **Option C: Sequence Learning (Serial RT Task)**
- **Paradigm**: Repeating vs. random sequences of stimuli
- **Observable**:
  - RT slowing on sequence violations
  - Accuracy drops on unexpected transitions
- **PE**: Transition surprisal = -log P(stimulus_t | history)
- **Mapping**: Normalized surprisal → `prediction_error`

### Recommended Approach
**Auditory oddball (Option A)** with computational observer (delta-rule) for simple, direct PE estimation aligned with model architecture.

---

## 6. Selection Confidence (selection_confidence)

### Computational Variable
- **`selection_confidence`**: Proxy for decision certainty, computed as 1 - 0.5*stress - 0.5*volatility, range [0, 1]

### Measurement Options

#### **Option A: Post-Decision Confidence Ratings**
- **Paradigm**: After each choice/decision, ask "How confident are you in your response?"
- **Scale**: 0 (not at all confident) to 100 (completely confident)
- **Mapping**: Rating / 100 → `selection_confidence`

#### **Option B: Post-Decision Wagering (PDW)**
- **Paradigm**: After each decision, allow participant to wager points (low/medium/high stake)
- **Observable**: Proportion of high-confidence wagers
- **Mapping**: Wager amount (normalized) → `selection_confidence`

#### **Option C: Model-Based Confidence (DDM Posterior)**
- **Approach**: Fit drift-diffusion model to choice RT data
- **Confidence proxy**: P(correct | RT, choice) from DDM posterior
- **Mapping**: DDM confidence → `selection_confidence`

#### **Option D: Reaction Time as Confidence Proxy**
- **Empirical finding**: Faster RT often correlates with higher confidence (within-subject)
- **Mapping**: Inverse-normalized RT → `selection_confidence` (faster = more confident)
- **Caution**: This is noisier; use only if explicit ratings are infeasible

### Recommended Approach
**Post-decision confidence ratings (Option A)** as gold standard; **DDM confidence (Option C)** as model-based validation measure.

---

## 7. Attunement (att_bounded, att_latent)

### Computational Variables
- **`att_bounded`**: Bounded attunement score [0, 1], primary readout of cognitive-affective engagement
- **`att_latent`**: Latent attunement (unbounded), before link function

### **Critical Note**: Attunement is the model's **primary novel construct** and requires operational definition before data collection. Below are three complementary operationalizations.

---

### **Option A: Social-Cognitive Attunement**

#### Definition
Accuracy and speed in recognizing/interpreting socially-relevant affective information.

#### Paradigm
- **Task**: Dynamic emotion recognition (morphing faces/voices, 0-100% intensity)
- **Observable**:
  - Accuracy in labeling emotional expressions
  - RT to correct identification
  - Sensitivity (d') at threshold intensities
- **Eye-tracking add-on (optional)**: Dwell time on socially informative regions (eyes, mouth)
- **Mapping**:
  - Composite score (accuracy × inverse RT, z-scored) → `att_bounded`
  - Eye-tracking dwell proportion → validation measure

#### Strengths
- Aligns with "attunement" as interpersonal sensitivity
- Well-validated tasks (e.g., Emotion Hexagon, Penn Emotion Recognition Test)

#### Weaknesses
- Assumes attunement = social cognition (may be narrower than model intends)

---

### **Option B: Task-Engagement Attunement**

#### Definition
Sustained readiness to engage with task demands; indexed by action execution, attention stability, and omission rate.

#### Paradigm
- **Task**: Gradual-onset Continuous Performance Task (gradCPT) or sustained attention to response task (SART)
- **Observable**:
  - Proportion of on-task responses (commission/omission rates)
  - RT variability (SDRT, coefficient of variation)
  - Lapses (RT > 2.5 SD above mean)
- **Composite**:
  - Engagement index = (1 - omission_rate) × (1 - RTCV)
- **Mapping**: Engagement index → `att_bounded`

#### Strengths
- Direct measure of sustained attention and task readiness
- Maps well to `action_executed` series in model

#### Weaknesses
- May confound with general vigilance/arousal
- Does not capture affective component explicitly

---

### **Option C: Interpersonal Synchrony (Dyadic Attunement)**

#### Definition
Temporal coordination and affective alignment during social interaction.

#### Paradigm
- **Task**: Cooperative or conversational dyadic interaction (e.g., joint problem-solving, storytelling)
- **Recording**: Audio/video for speech and movement analysis
- **Observable**:
  - **Speech synchrony**: Cross-correlation lag in turn-taking (optimal lag ~0-500ms)
  - **Prosody alignment**: Pitch and intensity mimicry (cross-wavelet coherence)
  - **Movement synchrony**: Head nod, gesture mirroring (motion energy correlation)
- **Composite**: Mean synchrony index across modalities
- **Mapping**: Synchrony index → `att_bounded`

#### Strengths
- Naturalistic, ecologically valid
- Captures interpersonal "attunement" directly

#### Weaknesses
- Computationally intensive (automated annotation)
- Requires dyadic setup and partner control
- Noisier due to partner variability

---

### **Recommended Approach: Multi-Method Triangulation**

**Primary Definition (preregister one):**
→ **Option B (Task-Engagement)** as primary operational definition for initial validation, due to:
- Direct alignment with `action_executed` and `selection_confidence` in model
- Established tasks (gradCPT) with normative data
- Feasible in solo-participant lab or ambulatory settings

**Convergent Validation:**
→ Add **Option A (Social-Cognitive)** as secondary measure to test whether model-predicted attunement generalizes to social domain.

**Exploratory Extension:**
→ Use **Option C (Interpersonal Synchrony)** in a subset of participants (if resources permit) to validate ecological generalization.

---

## 8. Additional Model Outputs

### Replay Mode (REPLAY_EXPLORE, REPLAY_CONVERGE, REPLAY_STABILIZE)

#### Measurement Approach
- **Self-report (post-block)**: "During the last block, were you mostly: (a) exploring new strategies, (b) refining/confirming your approach, or (c) consolidating/resting?"
- **Behavioral proxies**:
  - Explore: High switch rate, broad sampling
  - Converge: Low switch rate, repetition
  - Stabilize: Low engagement, slower RT, more omissions

#### Mapping
- Proportion of trials in each mode → model's `replay_mode_series` distribution

---

### Action Execution (action_executed)

#### Direct Observable
- Binary: Did participant respond on this trial? (yes/no)
- Omission rate inversely tracks action execution rate

---

### Memory Operations (episodic_write, semantic_micro_update, semanticization)

#### Measurement Approach (Indirect)
- **Free recall test (post-task)**:
  - Items recalled from recent trials → episodic writes
  - Gist/pattern knowledge → semanticization
- **Recognition memory test**:
  - d' for studied items → episodic write strength
  - Lure rejection based on schema → semantic consolidation

---

## 9. Validation Pipeline

### Step 1: Pilot Study (N=10-20)
- Collect all primary measures (affect, stress, task performance, confidence)
- Compute model-predicted time series from pilot data
- Check basic correlations between measured and modeled variables
- **Goal**: Establish feasibility and identify noise sources

### Step 2: Parameter Calibration (N=50-100)
- Fit model parameters to individual-level data using Bayesian inference (PyMC/Stan)
- Optimize preset configurations to match empirical distributions
- **Goal**: Validate that model can reproduce individual differences (e.g., ASD, ADHD profiles match clinical samples)

### Step 3: Prospective Validation (N=100-200)
- Use calibrated model to generate predictions for held-out participants
- Test key hypotheses (e.g., stress × volatility interaction predicts attunement drops)
- **Goal**: Demonstrate out-of-sample predictive validity

---

## 10. Data Collection Recommendations

### Timing Alignment
- **Critical**: Synchronize all measurements to a common clock (Unix timestamp or relative time from session start)
- Use event markers to align task events, physiological signals, and self-reports

### Sampling Rate
- **EMA**: 5-8 prompts/day for naturalistic studies
- **Lab tasks**: Trial-level (every 2-6 seconds) or block-level (every 2-5 minutes)
- **Physiology**: HRV (1-5 min windows), EDA (30-60 sec windows)

### Missing Data Handling
- Use linear interpolation for brief gaps (<5% of series)
- Apply principled imputation (e.g., Kalman smoothing, multiple imputation) for longer gaps
- Report missingness rates and sensitivity analyses

---

## 11. Statistical Analysis Plan

### Primary Analyses
1. **Correlation matrices**: Measured vs. modeled variables (Pearson, Spearman)
2. **Time-lagged cross-correlation**: Check for temporal leads/lags (e.g., does stress predict future attunement drops?)
3. **Multilevel models**: Account for within-subject repeated measures
   - Level 1: Time (ticks, trials, or EMA prompts)
   - Level 2: Participants
   - Level 3: Clinical groups (NT, ASD, ADHD)

### Model Comparison
- Compare RPM-EE predictions to simpler baselines:
  - Linear regression (no dynamics)
  - Vector autoregression (VAR)
  - Simpler RL models (e.g., Rescorla-Wagner only)
- Metrics: AIC, BIC, out-of-sample RMSE, explained variance (R²)

---

## 12. Preregistration Checklist

To ensure rigor and transparency, preregister the following before data collection:

- [ ] **Primary attunement definition** (choose Option A, B, or C above)
- [ ] **Stress and affect instruments** (EMA items, scales, sampling schedule)
- [ ] **Task paradigms** (oddball, N-back, etc.)
- [ ] **Hypothesized model parameters** (e.g., theta0 range, stress_decay range for NT vs. clinical)
- [ ] **Primary outcome**: Correlation between measured and modeled attunement (r > 0.40 as success threshold)
- [ ] **Secondary outcomes**: Stress-attunement coupling, prediction error effects
- [ ] **Sample size justification** (power analysis for correlation: N=64 for r=0.35, α=0.05, power=0.80)
- [ ] **Exclusion criteria** (e.g., incomplete data >20%, technical failures)

---

## 13. References & Resources

### Recommended Instruments
- **PANAS**: Watson, D., Clark, L. A., & Tellegen, A. (1988). *Psychological Assessment*.
- **PSS**: Cohen, S., Kamarck, T., & Mermelstein, R. (1983). *Journal of Health and Social Behavior*.
- **STAI-S Short**: Marteau, T. M., & Bekker, H. (1992). *British Journal of Clinical Psychology*.
- **gradCPT**: Esterman, M., Noonan, S. K., Rosenberg, M., & DeGutis, J. (2013). *Neuropsychologia*.
- **Penn ER-40**: Gur, R. C., et al. (2010). *Schizophrenia Research*.

### Physiological Signal Processing
- **HRV**: Tarvainen, M. P., et al. (2014). *Computer Methods and Programs in Biomedicine*. (Kubios HRV software)
- **EDA**: Benedek, M., & Kaernbach, C. (2010). *Behavior Research Methods*. (Ledalab toolbox)

### Computational Modeling
- **DDM fitting**: Wiecki, T. V., Sofer, I., & Frank, M. J. (2013). *Frontiers in Neuroinformatics*. (HDDM toolbox)
- **Bayesian inference**: Salvatier, J., Wiecki, T. V., & Fonnesbeck, C. (2016). *PeerJ Computer Science*. (PyMC3)

---

## 14. Summary Table: Variable-to-Measure Mapping

| **Model Variable**       | **Primary Measure**                          | **Secondary/Validation**              | **Sampling Rate**       |
|--------------------------|----------------------------------------------|---------------------------------------|-------------------------|
| `avg_affect_feedback`    | EMA valence rating (-3 to +3)                | PANAS-X, IAPS ratings                 | 5-8/day or trial-level  |
| `affect_volatility`      | Within-day SD of valence                     | Block-level variance                  | Daily or per-block      |
| `stress_bounded`         | EMA stress item (0-10)                       | PSS-S, STAI-S, HRV (RMSSD)            | 5-8/day or trial-level  |
| `ext_load`               | Multi-modal oddball surprise                 | CPT-AX task demand                    | Trial-level             |
| `mem_load`               | N-back accuracy + RT; DDM boundary           | Operation span, dual-task cost        | Trial-level             |
| `prediction_error`       | Oddball PE (delta-rule observer)             | Reversal learning δ, P3b amplitude    | Trial-level             |
| `selection_confidence`   | Post-decision rating (0-100)                 | Wagering, DDM confidence, RT          | Trial-level             |
| `att_bounded`            | Task-engagement index (1 - omission - RTCV)  | Emotion recognition, synchrony        | Trial or block-level    |
| `replay_mode`            | Post-block self-report (explore/converge/rest)| Switch rate, RT variability           | Block-level             |
| `action_executed`        | Binary response (yes/no)                     | Omission rate                         | Trial-level             |

---

## Contact & Version Control

- **Document Owner**: Cleveland Lewis
- **Last Updated**: 2025-10-27
- **Version History**:
  - v1.0 (2025-10-27): Initial draft with comprehensive mapping options
- **Feedback**: Please submit questions or suggestions via GitHub Issues or project wiki

---

**End of Document**
