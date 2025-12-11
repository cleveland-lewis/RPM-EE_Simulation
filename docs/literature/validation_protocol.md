# RPM-EE Validation Protocol: Study Designs & Endpoints

**Version:** 1.0
**Date:** 2025-10-27
**Status:** Pre-registration draft
**Principal Investigator:** Cleveland Lewis

---

## Executive Summary

This protocol outlines two complementary validation studies for the RPM-EE (Recursive Predictive Modeling with Emotional Encoding) computational framework:

1. **Study 1 (Lab)**: Within-subject, 2-3 hour intensive session with continuous physiological monitoring and cognitive tasks
2. **Study 2 (Ambulatory)**: Ecological momentary assessment (EMA) over 7-14 days with mobile micro-tasks

**Primary Goal**: Establish convergent, discriminant, and predictive validity of model-derived variables against empirical measurements.

---

## Table of Contents

1. [Primary Endpoints & Hypotheses](#1-primary-endpoints--hypotheses)
2. [Study 1: Laboratory Validation](#2-study-1-laboratory-validation)
3. [Study 2: Ambulatory Validation](#3-study-2-ambulatory-validation)
4. [Power Analysis & Sample Size](#4-power-analysis--sample-size)
5. [Data Processing & Analysis Plan](#5-data-processing--analysis-plan)
6. [Preregistration Specification](#6-preregistration-specification)
7. [Timeline & Resources](#7-timeline--resources)

---

## 1. Primary Endpoints & Hypotheses

### 1.1 Convergent Validity

#### **H1: Schema Stress**
**Hypothesis**: Model-derived `schema_stress` converges with empirical stress measures.

**H1a (Self-Report)**:
`schema_stress` correlates positively with momentary stress EMA ratings within-subject.
- **Effect size**: r ≥ 0.30 (within-subject correlation, averaged across participants)
- **Statistical test**: Mixed-effects correlation (Level 1: timepoints; Level 2: participants)

**H1b (Physiological)**:
`schema_stress` correlates inversely with HRV (RMSSD) within-subject.
- **Effect size**: r ≤ -0.25 (within-subject correlation)
- **Rationale**: Higher stress → lower HRV (parasympathetic withdrawal)

---

#### **H2: Memory Load**
**Hypothesis**: Model-derived `mem_load` tracks trial-wise working memory demand.

**H2a (Behavioral)**:
Trial-level `mem_load` predicts N-back accuracy (logistic regression) and RT (linear regression).
- **Effect size**: Standardized β > 0.20 for RT; OR > 1.30 for accuracy
- **Statistical test**: Mixed-effects generalized linear model (GLMM):
  ```
  Accuracy ~ mem_load + (1 + mem_load | participant)
  RT ~ mem_load + (1 + mem_load | participant)
  ```

**H2b (Model-Based)**:
`mem_load` correlates with DDM boundary separation parameter (a) extracted from N-back trials.
- **Effect size**: r ≥ 0.35 (across-participant correlation at block level)

---

#### **H3: Attunement Score**
**Hypothesis**: Model-derived `attunement_score` predicts action execution and engagement.

**H3a (Action Execution)**:
Trial-level `attunement_score` predicts binary action execution (response vs. omission).
- **Effect size**: AUC ≥ 0.70 (ROC curve for binary classification)
- **Statistical test**: Logistic GLMM:
  ```
  Action_Executed ~ attunement_score + (1 + attunement_score | participant)
  ```

**H3b (Confidence/Engagement)**:
Block-level `attunement_score` correlates with:
- Post-decision confidence ratings (r ≥ 0.30)
- Task engagement composite: (1 - omission_rate) × (1 - RTCV) (r ≥ 0.35)
- **Statistical test**: Within-subject correlation (averaged across participants)

---

### 1.2 Discriminant Validity

#### **H4: Specificity of Attunement**
**Hypothesis**: `attunement_score` reflects state engagement, not stable trait factors.

**H4a (Trait Independence)**:
After controlling for momentary affect and stress, `attunement_score` does **not** correlate with trait personality measures (Big Five Openness, Conscientiousness).
- **Null hypothesis**: Partial r ≤ 0.15 (non-significant after controlling for affect/stress)
- **Statistical test**: Hierarchical regression:
  ```
  attunement ~ affect + stress + trait_openness + trait_conscientiousness
  ```
  Test if trait predictors add <2% variance (ΔR² < 0.02).

**H4b (State Sensitivity)**:
`attunement_score` shows greater within-subject variance than between-subject variance (ICC < 0.40).
- **Rationale**: Confirms attunement is predominantly a dynamic state variable, not a trait.

---

### 1.3 Predictive Validity

#### **H5: Prospective Prediction**
**Hypothesis**: Early-block model outputs predict subsequent performance decrements.

**H5a (Lapse Prediction)**:
Mean `attunement_score` and `schema_stress` in Block 1 (trials 1-50) predict lapse rate in Block 2 (trials 51-100).
- **Effect size**: β > 0.25 for stress; β < -0.25 for attunement (standardized coefficients)
- **Statistical test**: Cross-validated regression:
  ```
  Lapse_Rate_Block2 ~ mean_stress_Block1 + mean_attunement_Block1
  ```
  Train on 70% of participants, test on held-out 30% (repeat 10-fold CV).

**H5b (Omission Prediction)**:
Trial-level `attunement_score` at t predicts omission probability at t+1 (next trial).
- **Effect size**: OR > 1.40 per 0.1-unit decrease in attunement
- **Statistical test**: Lagged logistic GLMM:
  ```
  Omission_{t+1} ~ attunement_t + (1 | participant)
  ```

---

## 2. Study 1: Laboratory Validation

### 2.1 Design Overview

- **Design**: Within-subject, single-session (2-3 hours)
- **N**: 80 participants (see power analysis)
- **Setting**: Lab with physiological monitoring (ECG, EDA) and desktop computer tasks
- **Components**:
  1. Baseline physiological recording (5 min rest)
  2. Battery of cognitive tasks (oddball, N-back, sustained attention)
  3. Continuous HR/EDA recording throughout
  4. Affect/stress EMA prompts every 3-5 minutes (8-12 prompts total)
  5. Post-block confidence ratings and engagement self-report

---

### 2.2 Participant Inclusion/Exclusion

#### Inclusion Criteria
- Age 18-65 years
- Fluent in English
- Normal or corrected-to-normal vision and hearing
- Capable of providing informed consent

#### Exclusion Criteria
- Current substance use disorder (past 6 months)
- Current psychotic disorder
- Acute medical condition affecting cardiovascular function (uncontrolled hypertension, arrhythmia)
- Medications known to affect HRV (beta-blockers, anticholinergics) unless stable dose >3 months
- Seizure disorder (due to visual stimuli in oddball task)

#### Clinical Subgroups (Optional Oversampling)
- **Neurotypical (NT)**: No clinical diagnosis (N=40)
- **ADHD**: DSM-5 diagnosis, confirmed by DIVA-5 or CAADID interview (N=20)
- **ASD**: DSM-5 diagnosis, confirmed by ADOS-2 or clinical records (N=20)

---

### 2.3 Procedure Timeline

| **Time** | **Activity** | **Duration** | **Measures** |
|----------|-------------|-------------|-------------|
| 0:00-0:10 | Consent, demographics, trait questionnaires | 10 min | OCEAN-20 (Big Five), DASS-21 (trait affect) |
| 0:10-0:15 | Sensor setup (ECG, EDA) | 5 min | — |
| 0:15-0:20 | Baseline rest (eyes open, fixation cross) | 5 min | HRV baseline, EDA baseline |
| 0:20-0:22 | **EMA Prompt 1** | 2 min | Stress (0-10), Affect (-3 to +3), Arousal (1-7) |
| 0:22-0:35 | **Task 1: Auditory Oddball** | 13 min | Trial-level: RT, accuracy, confidence |
| 0:35-0:37 | **EMA Prompt 2** | 2 min | Stress, Affect, Arousal |
| 0:37-0:50 | **Task 2: N-Back (2-back)** | 13 min | Trial-level: RT, accuracy, confidence |
| 0:50-0:52 | **EMA Prompt 3** | 2 min | Stress, Affect, Arousal |
| 0:52-1:05 | **Task 3: Sustained Attention (gradCPT)** | 13 min | Trial-level: RT, omissions, d' |
| 1:05-1:07 | **EMA Prompt 4** | 2 min | Stress, Affect, Arousal |
| 1:07-1:10 | Short break (optional water/restroom) | 3 min | — |
| 1:10-1:12 | **EMA Prompt 5** | 2 min | Stress, Affect, Arousal |
| 1:12-1:25 | **Repeat: Task 1 (Oddball, Block 2)** | 13 min | Trial-level: RT, accuracy, confidence |
| 1:25-1:27 | **EMA Prompt 6** | 2 min | Stress, Affect, Arousal |
| 1:27-1:40 | **Repeat: Task 2 (N-Back, Block 2)** | 13 min | Trial-level: RT, accuracy, confidence |
| 1:40-1:42 | **EMA Prompt 7** | 2 min | Stress, Affect, Arousal |
| 1:42-1:55 | **Repeat: Task 3 (gradCPT, Block 2)** | 13 min | Trial-level: RT, omissions, d' |
| 1:55-1:57 | **EMA Prompt 8 (Final)** | 2 min | Stress, Affect, Arousal |
| 1:57-2:05 | Post-session questionnaire | 8 min | NASA-TLX (workload), engagement ratings |
| 2:05-2:10 | Sensor removal, debrief | 5 min | — |

**Total Duration**: ~2 hours 10 minutes

---

### 2.4 Task Specifications

#### **Task 1: Auditory Oddball**
- **Stimuli**: Pure tones (500 Hz standard, 1000 Hz oddball)
- **Ratio**: 80% standard, 20% oddball
- **ISI**: Jittered 1000-1500 ms (uniform distribution)
- **Trials**: 200 per block (40 oddballs)
- **Response**: Keypress only to oddballs (go/no-go variant)
- **Confidence**: After each oddball detection, "How confident? (0-100)"
- **Model alignment**:
  - Prediction error = oddball trials (|stimulus - expectation|)
  - Running delta-rule observer to estimate expected stimulus

#### **Task 2: N-Back (2-Back)**
- **Stimuli**: Consonant letters (B, C, D, F, G, H, J, K, L, M, N, P, Q, R, S, T, V, W, X, Z)
- **Presentation**: 500 ms on, 2000 ms ISI
- **Trials**: 150 per block (~6 min active + pauses)
- **Targets**: ~30% (letter matches 2 positions back)
- **Response**: Keypress for targets, no response for non-targets
- **Confidence**: Post-block rating (average confidence, 0-100)
- **Model alignment**:
  - Memory load = running buffer occupancy (0-2 items in 2-back)
  - Trial-level load estimate via accuracy/RT pattern

#### **Task 3: Sustained Attention (gradCPT)**
- **Stimuli**: Grayscale city/mountain scene images, gradually morphing
- **Presentation**: 800 ms per image, 90% city (frequent), 10% mountain (rare)
- **Trials**: 360 per block (~5 min active)
- **Response**: Keypress to city (frequent-go task)
- **Withhold**: No response to mountain (rare no-go)
- **Model alignment**:
  - Attunement = engagement composite (1 - omission_rate) × (1 - RTCV)
  - Action execution = commission/omission tracking

---

### 2.5 Physiological Recording

#### **Electrocardiogram (ECG)**
- **Placement**: Lead II configuration (right clavicle, left lower rib)
- **Sampling rate**: 1000 Hz
- **Preprocessing**:
  - R-peak detection (Pan-Tompkins algorithm)
  - Artifact correction (Kubios HRV Premium or equivalent)
  - Extract IBI (inter-beat interval) series
- **HRV metrics** (5-minute rolling windows):
  - **RMSSD**: Root mean square of successive differences (primary parasympathetic index)
  - **SDNN**: Standard deviation of NN intervals (overall variability)
  - **LF/HF ratio**: Low-frequency/high-frequency power (sympathovagal balance, exploratory)

#### **Electrodermal Activity (EDA)**
- **Placement**: Medial phalanges of index and middle fingers (non-dominant hand)
- **Sampling rate**: 64 Hz
- **Preprocessing**:
  - Bandpass filter (0.05-5 Hz)
  - Decompose into tonic (SCL) and phasic (SCR) components (Ledalab toolbox)
- **Metrics** (30-60 sec rolling windows):
  - **SCL**: Tonic skin conductance level (arousal proxy)
  - **SCR frequency**: Phasic response count per minute (event-related arousal)

#### **Synchronization**
- Use lab streaming layer (LSL) or equivalent to timestamp all events (task trials, EMA prompts, physio samples)
- Align to Unix millisecond precision

---

### 2.6 Self-Report Measures

#### **Ecological Momentary Assessment (EMA) Prompts**
Administered 8 times during session (every 3-5 minutes):

1. **Stress**: "How stressed do you feel right now?" (0 = Not at all, 10 = Extremely)
2. **Affect Valence**: "How positive/negative do you feel?" (-3 = Very negative, 0 = Neutral, +3 = Very positive)
3. **Arousal**: "How activated/energized do you feel?" (1 = Very calm, 7 = Very activated)

#### **Post-Block Engagement Rating**
After each task block:
- "How engaged were you during that task?" (0 = Not at all, 10 = Completely absorbed)

#### **Trait Questionnaires (Pre-Session)**
- **OCEAN-20**: Brief Big Five personality (for discriminant validity H4)
- **DASS-21**: Depression, Anxiety, Stress Scales (trait baseline)

#### **Post-Session Workload**
- **NASA-TLX**: 6-item workload scale (mental demand, physical demand, temporal demand, performance, effort, frustration)

---

### 2.7 Data Outputs

#### **Per-Participant Outputs**
1. **Behavioral**: Trial-level CSV (RT, accuracy, confidence, trial type)
2. **Physiological**: Continuous IBI and SCL time series (CSV)
3. **Self-Report**: EMA time-stamped responses (CSV)
4. **Model Simulation**: RPM-EE outputs using participant-specific inputs (logs.json)

#### **Aggregate Outputs**
- Summary statistics per participant (mean attunement, stress, HRV, etc.)
- Mixed-effects model results (convergent validity tests)
- ROC curves and AUC for attunement → action execution

---

## 3. Study 2: Ambulatory Validation

### 3.1 Design Overview

- **Design**: Ecological momentary assessment (EMA) with mobile micro-tasks
- **Duration**: 7-14 days per participant (pilot: 7 days; full study: 14 days)
- **N**: 60 participants (see power analysis)
- **Setting**: Naturalistic (daily life) with smartphone app
- **Components**:
  1. 4-6 EMA prompts per day (stress, affect, engagement)
  2. Optional passive HRV monitoring (if wearable available, e.g., Polar H10, Garmin)
  3. Brief mobile cognitive micro-tasks (2-min oddball, 1-min N-back) delivered 1-2×/day

---

### 3.2 Participant Requirements

#### Inclusion
- Own iOS or Android smartphone
- Willing to install study app and respond to prompts for 7-14 days
- Age 18-65, fluent in English

#### Exclusion
- Current severe psychiatric crisis requiring immediate care
- Inability to use smartphone (e.g., severe motor impairment)

#### Clinical Subgroups (Optional)
- NT: N=30
- ADHD: N=15
- ASD: N=15

---

### 3.3 EMA Sampling Schedule

#### **Prompt Timing**
- **Frequency**: 4-6 random prompts per day
- **Window**: 9am-9pm (12-hour waking window)
- **Constraint**: Minimum 90 minutes between prompts
- **Compliance target**: ≥70% response rate (≥28/40 prompts over 7 days)

#### **EMA Items** (30 seconds per prompt)
1. **Stress**: "How stressed are you right now?" (0-10 slider)
2. **Affect**: "How positive/negative is your mood?" (-3 to +3 slider)
3. **Engagement**: "How focused/engaged are you in what you're doing?" (0-10 slider)
4. **Context** (optional): "What are you doing?" (dropdown: work, socializing, leisure, transit, other)

---

### 3.4 Mobile Micro-Tasks

#### **Micro-Task 1: Mobile Oddball (2 minutes)**
- **Frequency**: 1-2×/day (random timing, not overlapping with EMA)
- **Stimuli**: Visual oddball (blue circle = standard 80%, red triangle = oddball 20%)
- **Trials**: 60 total (12 oddballs)
- **ISI**: 1500 ms fixed
- **Response**: Tap screen for oddballs only
- **Outputs**: RT, accuracy, prediction error estimate

#### **Micro-Task 2: Mobile N-Back (1 minute)**
- **Frequency**: 1×/day (alternates with oddball)
- **Stimuli**: Single-digit numbers (1-9)
- **Load**: 1-back (simple) or 2-back (adaptive difficulty)
- **Trials**: 30 total
- **Outputs**: Accuracy, RT, memory load estimate

---

### 3.5 Passive Physiological Monitoring (Optional)

#### **Wearable HRV**
- **Device**: Polar H10 chest strap or Garmin Fenix 7 (validated for HRV)
- **Protocol**: Wear during waking hours (≥8 hr/day)
- **Metrics**: 5-minute rolling RMSSD, exported via Polar Flow or Garmin Connect API
- **Alignment**: Timestamp HRV windows to match nearest EMA prompt (±2 min)

#### **Feasibility Note**
Passive HRV may reduce compliance; pilot test with N=10 before full deployment.

---

### 3.6 Data Processing & Model Alignment

#### **Daily Workflow**
1. Participant completes EMAs + micro-tasks throughout day
2. End-of-day: Data synced to secure server (encrypted upload)
3. Nightly batch processing:
   - Run RPM-EE simulation using daily inputs (affect, stress, task events)
   - Generate model-predicted attunement and stress time series
   - Align with EMA timestamps (linear interpolation for missing data)

#### **Model Inputs (Per Day)**
- `total_ticks`: 1440 (one tick per minute, 24 hours)
- `affect_feedback`: Interpolated from EMA valence ratings
- `ext_load`: Baseline low (0.2) + spikes during micro-task trials
- `mem_load`: Baseline low (0.1) + spikes during N-back
- `preset`: Individualized based on Day 1 calibration (fit theta0, stress_decay to match baseline)

#### **Validation Metrics**
- **Within-day**: Correlation between model stress and EMA stress (lagged cross-correlation)
- **Between-day**: Day-level mean attunement predicts next-day engagement ratings
- **Micro-task**: Model-predicted `prediction_error` during oddball matches trial-level surprise

---

## 4. Power Analysis & Sample Size

### 4.1 Study 1 (Lab)

#### **Primary Endpoint (H1a): Within-Subject Correlation**
- **Effect size**: r = 0.30 (within-subject stress correlation)
- **Alpha**: 0.05 (two-tailed)
- **Power**: 0.80
- **Timepoints per participant**: 8 EMA prompts
- **Calculation**: Using multilevel power analysis (Schönbrodt & Perugini, 2013)
  - Required N ≈ **64 participants** to detect r = 0.30 at Level 1 (within-subject)
- **Attrition buffer**: 20% → **N = 80 recruited**

#### **Secondary Endpoint (H3a): Binary Prediction (AUC)**
- **Effect size**: AUC = 0.70
- **Null**: AUC = 0.50 (chance)
- **Alpha**: 0.05
- **Power**: 0.80
- **Trials per participant**: ~150 (sustained attention task)
- **Calculation**: Using pROC power analysis (Robin et al., 2011)
  - Required N ≈ **50 participants** (conservative, accounting for within-subject clustering)
- **Conclusion**: N=80 provides adequate power for both primary and secondary endpoints

---

### 4.2 Study 2 (Ambulatory)

#### **Primary Endpoint (H1a Replication): Daily EMA Correlation**
- **Effect size**: r = 0.30 (within-subject, daily stress)
- **Timepoints per participant**: 7 days × 5 prompts = 35 observations
- **Power**: 0.80
- **Alpha**: 0.05
- **Calculation**: Multilevel power (Level 1: days, Level 2: participants)
  - Required N ≈ **50 participants**
- **Attrition buffer**: 20% → **N = 60 recruited**

#### **Compliance Adjustment**
- Assume 70% response rate → effective observations = 35 × 0.70 ≈ 25 per participant
- Still sufficient for within-subject correlation (minimum 20 observations recommended)

---

### 4.3 Clinical Subgroup Comparisons (Exploratory)

#### **Group Differences (ANOVA)**
- **Design**: Compare NT vs. ADHD vs. ASD on mean attunement, stress reactivity, HRV
- **Effect size**: Cohen's d = 0.60 (medium-large, based on prior ASD/ADHD literature)
- **Power**: 0.80
- **Alpha**: 0.05
- **Groups**: 3 (NT, ADHD, ASD)
- **Calculation**: One-way ANOVA power (G*Power)
  - Required N ≈ **21 per group** (total N=63)
- **Study 1 Allocation**: NT=40, ADHD=20, ASD=20 (powered for pairwise NT vs. clinical)

---

## 5. Data Processing & Analysis Plan

### 5.1 Preprocessing Pipeline

#### **Step 1: Data Cleaning**
1. **Behavioral**: Remove outlier trials (RT < 100 ms or > 3000 ms)
2. **Physiological**: Artifact correction (Kubios HRV, Ledalab for EDA)
3. **Self-Report**: Flag incomplete EMA responses (missing items coded as NA)

#### **Step 2: Timestamp Alignment**
- Convert all data to Unix millisecond timestamps
- Align behavioral events, EMA prompts, and physiological windows to common timeline
- Create master CSV per participant with 1-row-per-timepoint structure:
  ```
  timestamp, ema_stress, ema_affect, rt_oddball, accuracy, hrv_rmssd, scl, model_stress, model_attunement
  ```

#### **Step 3: Model Simulation**
- For each participant, run `run_simulation()` with:
  - `total_ticks` = session duration in seconds (lab) or minutes (ambulatory)
  - `preset` = individualized (fit to baseline data if available, else 'default')
  - `seed` = participant ID (for reproducibility)
- Extract model time series: `attunement_score`, `schema_stress`, `mem_load`, `prediction_error`
- Downsample or upsample model outputs to match empirical sampling rate

#### **Step 4: Feature Engineering**
- **Within-subject centering**: For each participant, z-score all continuous variables (stress, affect, attunement, HRV)
- **Lagged variables**: Create t-1 lags for predictive models (e.g., attunement_t predicts omission_t+1)
- **Block-level aggregates**: Compute mean, SD, min, max per task block for block-level analyses

---

### 5.2 Statistical Models

#### **Model 1: Convergent Validity (H1a, H2a, H3b)**
Mixed-effects correlation via multilevel model:
```r
library(lme4)
library(lmerTest)

# H1a: Stress convergence
m1 <- lmer(ema_stress ~ model_stress + (1 + model_stress | participant), data=df)
summary(m1)  # Test β for model_stress (should be positive, p < .05)

# Compute within-subject correlation
library(correlation)
cor_within <- correlation(df, select=c("ema_stress", "model_stress"), multilevel=TRUE)
```

#### **Model 2: Action Execution Prediction (H3a)**
Logistic mixed-effects model:
```r
library(lme4)

# Binary outcome: action executed (1) vs. omission (0)
m2 <- glmer(action_executed ~ attunement_score + (1 + attunement_score | participant),
            data=df_trials, family=binomial)
summary(m2)

# Compute AUC per participant, then average
library(pROC)
auc_by_subj <- df_trials %>%
  group_by(participant) %>%
  summarise(auc = as.numeric(auc(action_executed, attunement_score)))
mean(auc_by_subj$auc)  # Should be ≥ 0.70
```

#### **Model 3: Discriminant Validity (H4a)**
Hierarchical regression to test trait independence:
```r
# Step 1: State predictors only
m3a <- lm(attunement ~ ema_affect + ema_stress, data=df_block_level)
summary(m3a)  # Extract R²

# Step 2: Add trait predictors
m3b <- lm(attunement ~ ema_affect + ema_stress + trait_openness + trait_conscientiousness,
          data=df_block_level)
summary(m3b)  # Test ΔR² (should be < 0.02)
anova(m3a, m3b)  # F-test for model comparison
```

#### **Model 4: Predictive Validity (H5a)**
Cross-validated regression for out-of-sample prediction:
```r
library(caret)

# Prepare data: early block predictors, late block outcome
df_pred <- df %>%
  group_by(participant) %>%
  summarise(
    stress_block1 = mean(model_stress[block==1]),
    attunement_block1 = mean(attunement_score[block==1]),
    lapse_rate_block2 = sum(omission[block==2]) / sum(block==2)
  )

# 10-fold cross-validation
set.seed(123)
train_control <- trainControl(method="cv", number=10)
m4 <- train(lapse_rate_block2 ~ stress_block1 + attunement_block1,
            data=df_pred, method="lm", trControl=train_control)
print(m4)  # Check RMSE and R² on held-out folds
```

#### **Model 5: Lagged Prediction (H5b)**
Time-lagged logistic regression:
```r
# Create lagged attunement variable
df_trials <- df_trials %>%
  group_by(participant) %>%
  mutate(attunement_lag1 = lag(attunement_score, 1))

# Predict next-trial omission
m5 <- glmer(omission ~ attunement_lag1 + (1 | participant),
            data=df_trials, family=binomial)
summary(m5)  # Test OR for attunement_lag1 (should be > 1.40 for 0.1-unit decrease)
```

---

### 5.3 Sensitivity Analyses

#### **Missing Data**
- **Primary**: Complete-case analysis (exclude participants with >20% missing EMA)
- **Sensitivity**: Multiple imputation (10 imputations, pool results via Rubin's rules)

#### **Outliers**
- **Primary**: Winsorize extreme values (95th/5th percentiles)
- **Sensitivity**: Robust regression (Huber M-estimator) for continuous outcomes

#### **HRV Preprocessing Variants**
- Compare artifact correction methods (Kubios automatic vs. manual, threshold-based)
- Test both RMSSD and SDNN as stress proxies (primary = RMSSD, sensitivity = SDNN)

---

## 6. Preregistration Specification

### 6.1 Preregistration Platform
- **OSF (Open Science Framework)**: https://osf.io/registries
- **Template**: Preregistration Template for Quantitative Research in Psychology (AsPredicted alternative)

---

### 6.2 Required Preregistration Elements

#### **1. Study Information**
- Title: "Validation of the RPM-EE Computational Framework: Convergent, Discriminant, and Predictive Validity"
- Authors: Cleveland Lewis, [Co-investigators]
- Institution: [Your affiliation]
- Funding: [If applicable]

#### **2. Hypotheses (Exact Wording)**
Copy from Section 1.1-1.3 above (H1a, H1b, H2a, H2b, H3a, H3b, H4a, H4b, H5a, H5b).

#### **3. Sampling Plan**
- **Study 1**: N=80 (64 + 20% attrition), recruited via [specify: university subject pool, Prolific, clinical referrals]
- **Study 2**: N=60 (50 + 20% attrition)
- **Stopping rule**: Data collection ends when N is reached OR [date], whichever comes first
- **Exclusion criteria**: As listed in Sections 2.2 and 3.2

#### **4. Variables**
- **Independent variables (model-derived)**: attunement_score, schema_stress, mem_load, prediction_error
- **Dependent variables (empirical)**: EMA stress/affect, HRV (RMSSD), N-back accuracy/RT, action execution (binary), confidence ratings
- **Covariates**: Age, sex, clinical group (NT/ADHD/ASD)

#### **5. Analysis Plan**
- Copy Section 5.2 models (R code included in supplementary materials on OSF)
- **Alpha**: 0.05 (two-tailed) for all tests
- **Multiple comparisons correction**: Benjamini-Hochberg FDR for exploratory subgroup analyses (not applied to preregistered H1-H5)

#### **6. Success Criteria (Confirmatory vs. Exploratory)**
**Confirmatory (preregistered):**
- H1a: r ≥ 0.30, p < .05
- H3a: AUC ≥ 0.70
- H5a: Out-of-sample RMSE < 0.15 (lapse rate prediction)

**Exploratory (not preregistered, reported separately):**
- Clinical subgroup differences (NT vs. ADHD vs. ASD)
- EDA correlations (SCL vs. stress)
- Replay mode self-report validation

#### **7. Timeline**
- **Preregistration submission**: [Date, before any data collection]
- **Data collection start**: [Date]
- **Data collection end**: [Date]
- **Analysis completion**: [Date]

---

### 6.3 Preregistration Checklist

- [ ] All hypotheses specified with exact effect sizes and statistical tests
- [ ] Sample size justified via power analysis
- [ ] Inclusion/exclusion criteria fully enumerated
- [ ] All variables defined (measurement instruments, units, preprocessing)
- [ ] Analysis code uploaded to OSF (R scripts with placeholder data)
- [ ] Success criteria for each hypothesis (effect size thresholds)
- [ ] Distinction between confirmatory and exploratory analyses
- [ ] Plan for handling missing data, outliers, and violations of assumptions
- [ ] Data sharing plan (de-identified data on OSF after publication)

---

## 7. Timeline & Resources

### 7.1 Study 1 (Lab) Timeline

| **Phase** | **Duration** | **Activities** |
|-----------|-------------|---------------|
| **Preparation** | 2 months | Ethics approval, task programming (PsychoPy), sensor testing, pilot N=5 |
| **Data Collection** | 4 months | Recruit and run 80 participants (5/week average) |
| **Data Processing** | 1 month | Preprocessing, artifact correction, model simulations |
| **Analysis** | 1 month | Mixed-effects models, ROC curves, figures |
| **Manuscript** | 2 months | Drafting, revision, submission |
| **Total** | **10 months** | From ethics to submission |

---

### 7.2 Study 2 (Ambulatory) Timeline

| **Phase** | **Duration** | **Activities** |
|-----------|-------------|---------------|
| **Preparation** | 3 months | Ethics, app development (React Native or Flutter), pilot N=10 (7 days) |
| **Data Collection** | 6 months | Recruit 60 participants, 14 days each (staggered start) |
| **Data Processing** | 1 month | EMA aggregation, model simulations, HRV alignment |
| **Analysis** | 1 month | Multilevel models, lagged analyses |
| **Manuscript** | 2 months | Drafting, revision, submission |
| **Total** | **13 months** | From ethics to submission |

---

### 7.3 Resource Requirements

#### **Personnel**
- **PI**: 20% effort (design, analysis, writing)
- **Research Coordinator**: 0.5 FTE (recruitment, data collection, participant payments)
- **Programmer**: 0.25 FTE (task development, app maintenance)
- **Data Analyst**: 0.25 FTE (preprocessing, model fitting)

#### **Equipment**
- **ECG/EDA system**: Biopac MP160 or equivalent (~$15k, one-time)
- **Desktop computers**: 2 stations with PsychoPy (~$2k each)
- **Wearables (optional)**: Polar H10 chest straps × 20 (~$2k, can be reused)
- **Smartphones (loaner devices)**: 10 Android phones (~$2k, if participants lack devices)

#### **Participant Compensation**
- **Study 1**: $30/session × 80 participants = **$2,400**
- **Study 2**: $2/day × 14 days × 60 participants = **$1,680**
- **Total**: **$4,080**

#### **Software/Services**
- **EMA app development**: Custom build (~$10k) OR use Ethica Data / Metricwire (~$3k/year)
- **Cloud storage (AWS/Google Cloud)**: ~$500/year
- **Statistical software**: R (free), MATLAB (if needed, ~$1k/year site license)

#### **Total Budget Estimate**
- **Study 1**: ~$20k (equipment) + $2.4k (participants) + $2k (misc) = **$24.4k**
- **Study 2**: ~$10k (app) + $1.7k (participants) + $1k (misc) = **$12.7k**
- **Combined**: ~**$37k** (first year; equipment reusable, marginal cost for replication ~$10k)

---

## 8. Data Sharing & Reproducibility

### 8.1 Open Science Practices

#### **Preregistration**
- Submit to OSF Registries before data collection begins
- Public link included in manuscript

#### **Data Sharing**
- **De-identified data**: Uploaded to OSF within 6 months of publication
- **Exclusions**: Clinical group identifiers (ADHD/ASD) aggregated to "clinical" for privacy
- **Format**: CSV files with data dictionary (codebook)

#### **Code Sharing**
- **Analysis scripts**: All R code for preprocessing, models, figures (GitHub repo linked in paper)
- **Model code**: RPM-EE simulation code (already in this repo: `/src/simulation.py`, `/src/presets.py`)
- **Task code**: PsychoPy scripts, mobile app source code (GitHub)

#### **Materials**
- **EMA items**: Full text in supplementary materials
- **Task stimuli**: Links to IAPS (oddball), gradCPT (open-source)

---

### 8.2 FAIR Principles Compliance

- **Findable**: DOI for dataset (OSF), indexed in Google Dataset Search
- **Accessible**: Public repository, open access manuscript (PsyArXiv preprint)
- **Interoperable**: CSV format (not proprietary), documented units/scales
- **Reusable**: CC-BY-4.0 license for data, MIT license for code

---

## 9. Ethical Considerations

### 9.1 Informed Consent
- Written consent obtained before any data collection
- Participants informed of:
  - Study purpose (validate cognitive model)
  - Procedures (tasks, EMA, physiology)
  - Risks (minimal: fatigue, eye strain, potential stress from tasks)
  - Benefits (contribution to science, monetary compensation)
  - Right to withdraw anytime without penalty

### 9.2 Data Privacy
- **Identifiers**: Stored separately from data (encrypted, access-restricted)
- **Clinical information**: ADHD/ASD diagnosis codes aggregated to "clinical" in shared datasets
- **Physiology**: ECG/EDA data scrubbed of identifying features (no voice, face, etc.)

### 9.3 Risk Mitigation
- **Stress induction**: Tasks are mild; participants can take breaks anytime
- **Clinical participants**: Screened for acute crisis; study contact info provided for concerns
- **Wearables**: Optional; no medical-grade claims made

---

## 10. Contingency Plans

### 10.1 Low Recruitment
- **Backup**: Extend timeline by 2 months OR reduce N to minimum viable (N=64 for Study 1, N=50 for Study 2)

### 10.2 Low EMA Compliance (<70%)
- **Intervention**: Mid-study check-in (email/SMS reminder), small bonus for high compliance

### 10.3 Physiological Artifact Rate High (>30%)
- **Fallback**: Drop HRV from primary analyses, relabel as exploratory

### 10.4 Model Doesn't Converge (H1-H3 all fail)
- **Plan B**: Conduct detailed exploratory analyses to diagnose mismatch (e.g., model parameters miscalibrated, measurement instruments noisy)
- Report negative result honestly (important for field)

---

## Contact Information

**Principal Investigator**: Cleveland Lewis
**Email**: [Your email]
**Institution**: [Your affiliation]
**Study Registration**: [OSF link once preregistered]

---

**End of Protocol**
