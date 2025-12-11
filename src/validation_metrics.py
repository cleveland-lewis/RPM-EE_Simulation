# =============================================================================
# validation_metrics.py - Endpoint Calculator for Preregistered Hypotheses
# =============================================================================
"""
This module provides utilities to compute preregistered validation metrics
for RPM-EE model outputs against empirical data.

Implements metrics from validation_protocol.md:
    - H1: Convergent validity (correlation, mixed-effects)
    - H2: Memory load prediction (GLMM, DDM alignment)
    - H3: Attunement → action execution (AUC, ROC)
    - H4: Discriminant validity (partial correlation, ICC)
    - H5: Predictive validity (cross-validated regression, lagged prediction)

Key Functions:
    - compute_convergent_validity(): Correlations between model and empirical
    - compute_action_execution_auc(): ROC analysis for attunement → action
    - compute_discriminant_validity(): Trait independence tests
    - compute_predictive_validity(): Out-of-sample prediction metrics
    - compute_all_endpoints(): Complete battery of preregistered tests

References:
    - validation_protocol.md: Sections 1.1-1.3 (Hypotheses H1-H5)
    - empirical_mapping.md: Variable definitions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import warnings
import logging

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

try:
    from sklearn.metrics import roc_auc_score, roc_curve
    from sklearn.model_selection import cross_val_score, KFold
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.exceptions import ConvergenceWarning
    _SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover - environment without sklearn
    _SKLEARN_AVAILABLE = False
except Exception as e: # Catch any other unexpected errors during sklearn import
    logger.warning(f"An unexpected error occurred during scikit-learn import: {e}")
    _SKLEARN_AVAILABLE = False


def _require_sklearn(feature: str) -> None:
    """Raise a clear error when optional sklearn dependency is missing."""
    if not _SKLEARN_AVAILABLE:
        raise ImportError(f"scikit-learn is required for {feature}; please install scikit-learn to use this metric.")


def _roc_curve_fallback(y_true: np.ndarray, y_score: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute ROC curve without sklearn (binary labels only)."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    if y_true.shape != y_score.shape:
        raise ValueError("y_true and y_score must have the same shape.")
    unique_labels = set(np.unique(y_true))
    if unique_labels - {0, 1}:
        raise ValueError("ROC computation requires binary labels in {0, 1}.")

    n_pos = np.sum(y_true == 1)
    n_neg = np.sum(y_true == 0)
    if n_pos == 0 or n_neg == 0:
        raise ValueError("Both positive and negative examples are required for ROC/AUC.")

    # Sort by descending score
    order = np.argsort(-y_score, kind='mergesort')
    y_true_sorted = y_true[order]
    y_score_sorted = y_score[order]

    # Identify unique thresholds
    distinct_idx = np.where(np.diff(y_score_sorted))[0]
    threshold_idxs = np.r_[distinct_idx, y_true_sorted.size - 1]

    tps = np.cumsum(y_true_sorted)[threshold_idxs]
    fps = (threshold_idxs + 1) - tps

    tpr = tps / n_pos
    fpr = fps / n_neg
    thresholds = y_score_sorted[threshold_idxs]

    # Prepend origin for plotting consistency
    fpr = np.r_[0.0, fpr]
    tpr = np.r_[0.0, tpr]
    thresholds = np.r_[thresholds[0] + np.finfo(float).eps, thresholds]

    return fpr, tpr, thresholds


def _roc_auc_score_fallback(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Area under the ROC curve using rank-based U statistic."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    if y_true.shape != y_score.shape:
        raise ValueError("y_true and y_score must have the same shape.")
    unique_labels = set(np.unique(y_true))
    if unique_labels - {0, 1}:
        raise ValueError("AUC computation requires binary labels in {0, 1}.")

    pos_mask = y_true == 1
    n_pos = np.sum(pos_mask)
    n_neg = y_true.size - n_pos
    if n_pos == 0 or n_neg == 0:
        raise ValueError("Both positive and negative examples are required for ROC/AUC.")

    ranks = stats.rankdata(y_score)
    sum_ranks_pos = ranks[pos_mask].sum()
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(np.clip(auc, 0.0, 1.0))


if not _SKLEARN_AVAILABLE:
    roc_auc_score = _roc_auc_score_fallback
    roc_curve = _roc_curve_fallback

# Canonical validation schema (with aliases for common empirical column names)
VALIDATION_COLUMN_ALIASES = {
    'mem_load': ['memory_load', 'mem_load_z'],
    'rt': ['response_time', 'rt_ms'],
    'accuracy': ['acc', 'correct'],
    'participant': ['subject', 'participant_id'],
}

class ValidationSchemaError(ValueError):
    """Raised when validation inputs do not match the expected schema."""


def validate_and_normalize_columns(
    df: pd.DataFrame,
    required_aliases: Dict[str, List[str]] = VALIDATION_COLUMN_ALIASES,
    *,
    allow_extra: bool = True,
) -> pd.DataFrame:
    """Ensure required columns exist (using aliases) and are finite; returns a copy with canonical names.

    Args:
        df: Input dataframe with validation inputs.
        required_aliases: Mapping from canonical column name to list of accepted aliases.
        allow_extra: If False, error on unexpected columns (default allows extras).
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValidationSchemaError("Validation inputs must be provided as a pandas DataFrame.")

    df_norm = df.copy()
    present = set(df_norm.columns)
    renamed = {}

    for canonical, aliases in required_aliases.items():
        if canonical in present:
            continue
        # Find the first alias present
        found = next((a for a in aliases if a in present), None)
        if found is None:
            raise ValidationSchemaError(f"Missing required column '{canonical}' (aliases: {aliases})")
        renamed[found] = canonical

    if renamed:
        df_norm = df_norm.rename(columns=renamed)

    # Ensure required columns exist and contain finite values
    for canonical in required_aliases:
        if canonical not in df_norm.columns:
            raise ValidationSchemaError(f"Missing required column '{canonical}' after normalization.")
        series = df_norm[canonical]
        if not np.isfinite(series).all():
            raise ValidationSchemaError(f"Non-finite values detected in '{canonical}'.")

    if not allow_extra:
        unexpected = set(df_norm.columns) - set(required_aliases.keys())
        if unexpected:
            raise ValidationSchemaError(f"Unexpected columns present: {sorted(unexpected)}")

    return df_norm

__all__ = [
    'compute_convergent_validity',
    'compute_hrv_stress_convergence',
    'compute_memory_load_prediction',
    'compute_action_execution_auc',
    'compute_confidence_correlation',
    'compute_discriminant_validity',
    'compute_icc',
    'compute_lapse_prediction',
    'compute_lagged_omission_prediction',
    'compute_all_endpoints',
    'generate_calibration_plot',
    'validate_and_normalize_columns',
]


# =============================================================================
# Constants
# =============================================================================

METRICS_SCHEMA_VERSION = "1.0.0"

# Preregistered effect size thresholds (from validation_protocol.md Section 1)
THRESHOLDS = {
    'H1a_stress_corr': 0.30,        # r ≥ 0.30 for stress convergence
    'H1b_hrv_corr': -0.25,          # r ≤ -0.25 for HRV inverse correlation
    'H2a_memload_beta': 0.20,       # β > 0.20 for memory load → RT
    'H3a_action_auc': 0.70,         # AUC ≥ 0.70 for attunement → action
    'H3b_confidence_corr': 0.30,    # r ≥ 0.30 for attunement ~ confidence
    'H4a_trait_delta_r2': 0.02,     # ΔR² < 0.02 for trait independence
    'H4b_icc_threshold': 0.40,      # ICC < 0.40 for state variability
    'H5a_lapse_rmse': 0.15,         # RMSE < 0.15 for lapse prediction
    'H5b_lag_or': 1.40,             # OR > 1.40 for lagged omission prediction
}

# Canonical validation schema (with aliases for common empirical column names)
VALIDATION_COLUMN_ALIASES = {
    'mem_load': ['memory_load', 'mem_load_z'],
    'rt': ['response_time', 'rt_ms'],
    'accuracy': ['acc', 'correct'],
    'participant': ['subject', 'participant_id'],
}


# =============================================================================
# H1: Convergent Validity (Stress, Memory Load, Attunement)
# =============================================================================

def compute_convergent_validity(
    merged_df: pd.DataFrame,
    model_col: str,
    empirical_col: str,
    method: str = 'pearson',
    within_subject: bool = True,
    subject_col: str = 'participant',
) -> Dict:
    """
    Compute convergent validity correlation between model and empirical measure.

    Supports within-subject correlation (averaged across participants) or
    across-subject correlation (single global value).

    Parameters:
        merged_df: DataFrame with aligned model and empirical data
        model_col: Column name for model-derived variable
        empirical_col: Column name for empirical measurement
        method: 'pearson' or 'spearman'
        within_subject: If True, compute per-participant then average
        subject_col: Column name for subject/participant ID

    Returns:
        dict with keys:
            - r: correlation coefficient (mean if within_subject)
            - p: p-value
            - n: sample size (participants if within_subject, else observations)
            - r_std: standard deviation of within-subject r's (if applicable)
            - success: bool, whether threshold met (H1a: r ≥ 0.30)
    """
    # Remove missing values
    df = merged_df[[model_col, empirical_col, subject_col]].dropna()

    if len(df) < 10:
        warnings.warn(f"Insufficient data: only {len(df)} valid observations")
        return {'r': np.nan, 'p': np.nan, 'n': 0, 'success': False}

    corr_func = pearsonr if method == 'pearson' else spearmanr

    if within_subject and subject_col in df.columns:
        # Compute per-participant correlations, then average
        subject_corrs = []
        for subj_id, subj_df in df.groupby(subject_col):
            if len(subj_df) >= 5:  # Minimum 5 obs per participant
                try:
                    r_subj, _ = corr_func(subj_df[model_col], subj_df[empirical_col])
                    if not np.isnan(r_subj):
                        subject_corrs.append(r_subj)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Could not compute correlation for subject {subj_id}: {e}")
                    continue

        if len(subject_corrs) == 0:
            return {'r': np.nan, 'p': np.nan, 'n': 0, 'success': False}

        # Fisher z-transform, average, inverse transform
        z_scores = np.arctanh(subject_corrs)
        mean_z = np.mean(z_scores)
        r_mean = np.tanh(mean_z)
        r_std = np.std(subject_corrs)

        # One-sample t-test: is mean r significantly > 0?
        t_stat, p_value = stats.ttest_1samp(subject_corrs, 0.0, alternative='greater')

        success = r_mean >= THRESHOLDS['H1a_stress_corr'] and p_value < 0.05

        return {
            'r': float(r_mean),
            'r_std': float(r_std),
            'p': float(p_value),
            'n': len(subject_corrs),
            'method': f'{method}_within_subject',
            'success': bool(success),
            'threshold': THRESHOLDS['H1a_stress_corr'],
        }

    else:
        # Global correlation (all observations pooled)
        r, p_value = corr_func(df[model_col], df[empirical_col])
        success = r >= THRESHOLDS['H1a_stress_corr'] and p_value < 0.05

        return {
            'r': float(r),
            'p': float(p_value),
            'n': len(df),
            'method': f'{method}_pooled',
            'success': bool(success),
            'threshold': THRESHOLDS['H1a_stress_corr'],
        }


def compute_hrv_stress_convergence(
    merged_df: pd.DataFrame,
    model_stress_col: str = 'schema_stress',
    hrv_col: str = 'hrv_rmssd',
    subject_col: str = 'participant',
) -> Dict:
    """
    Compute H1b: Model stress inversely correlates with HRV (r ≤ -0.25).

    Higher stress → lower HRV (parasympathetic withdrawal).

    Parameters:
        merged_df: DataFrame with model stress and HRV
        model_stress_col: Column for model-derived stress
        hrv_col: Column for HRV (RMSSD in ms)
        subject_col: Participant ID column

    Returns:
        dict with r, p, n, success (r ≤ -0.25 and p < 0.05)
    """
    result = compute_convergent_validity(
        merged_df,
        model_col=model_stress_col,
        empirical_col=hrv_col,
        method='spearman',  # Use Spearman (HRV often skewed)
        within_subject=True,
        subject_col=subject_col,
    )

    # Adjust success criterion for inverse correlation
    result['success'] = result['r'] <= THRESHOLDS['H1b_hrv_corr'] and result['p'] < 0.05
    result['threshold'] = THRESHOLDS['H1b_hrv_corr']
    result['hypothesis'] = 'H1b'

    return result


# =============================================================================
# H2: Memory Load Prediction
# =============================================================================

def compute_memory_load_prediction(
    trial_df: pd.DataFrame,
    mem_load_col: str = 'mem_load',
    rt_col: str = 'rt',
    accuracy_col: str = 'accuracy',
    subject_col: str = 'participant',
) -> Dict:
    """
    Compute H2a: Model memory load predicts N-back RT and accuracy.

    Uses mixed-effects framework (conceptually; here we use sklearn for simplicity).

    Parameters:
        trial_df: Trial-level DataFrame
        mem_load_col: Column for model-derived memory load
        rt_col: Reaction time (ms)
        accuracy_col: Accuracy (0 or 1)
        subject_col: Participant ID

    Returns:
        dict with beta coefficients, p-values, success flags
    """
    _require_sklearn("compute_memory_load_prediction")
    df = validate_and_normalize_columns(
        trial_df,
        {
            'mem_load': VALIDATION_COLUMN_ALIASES['mem_load'],
            'rt': VALIDATION_COLUMN_ALIASES['rt'],
            'accuracy': VALIDATION_COLUMN_ALIASES['accuracy'],
            'participant': VALIDATION_COLUMN_ALIASES['participant'],
        },
    )[[mem_load_col, rt_col, accuracy_col, subject_col]].dropna()

    if len(df) < 20:
        return {'rt_beta': np.nan, 'acc_beta': np.nan, 'success': False}

    # Within-subject standardization (z-score within each participant)
    def z_score_within(group):
        return (group - group.mean()) / (group.std() + 1e-6)

    df['mem_load_z'] = df.groupby(subject_col)[mem_load_col].transform(z_score_within)
    df['rt_z'] = df.groupby(subject_col)[rt_col].transform(z_score_within)

    # Linear regression: RT ~ mem_load (within-subject standardized)
    X_rt = df[['mem_load_z']].values
    y_rt = df['rt_z'].values
    reg_rt = LinearRegression().fit(X_rt, y_rt)
    beta_rt = reg_rt.coef_[0]

    # Logistic regression: accuracy ~ mem_load
    X_acc = df[[mem_load_col]].values
    y_acc = df[accuracy_col].values
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            reg_acc = LogisticRegression(max_iter=200, solver='lbfgs').fit(X_acc, y_acc)
            beta_acc = reg_acc.coef_[0][0]
    except (ValueError, ConvergenceWarning) as e:
        logger.debug(f"Logistic regression for accuracy failed: {e}")
        beta_acc = np.nan
    except Exception as e:
        logger.warning(f"An unexpected error occurred during logistic regression for accuracy: {e}")
        beta_acc = np.nan

    # Success: beta_rt > 0.20 (higher load → slower RT)
    success_rt = beta_rt >= THRESHOLDS['H2a_memload_beta']

    # For accuracy: expect negative beta (higher load → lower accuracy)
    success_acc = beta_acc < 0.0  # Qualitative check

    return {
        'rt_beta': float(beta_rt),
        'rt_success': bool(success_rt),
        'accuracy_beta': float(beta_acc) if not np.isnan(beta_acc) else None,
        'accuracy_success': bool(success_acc) if not np.isnan(beta_acc) else None,
        'n_trials': len(df),
        'hypothesis': 'H2a',
        'threshold': THRESHOLDS['H2a_memload_beta'],
        'success': bool(success_rt),  # Primary criterion
    }


# =============================================================================
# H3: Attunement → Action Execution (ROC/AUC)
# =============================================================================

def compute_action_execution_auc(
    trial_df: pd.DataFrame,
    attunement_col: str = 'attunement_score',
    action_col: str = 'action_executed',
    subject_col: str = 'participant',
) -> Dict:
    """
    Compute H3a: Attunement predicts action execution with AUC ≥ 0.70.

    Returns ROC curve data and per-participant AUC statistics.

    Parameters:
        trial_df: Trial-level DataFrame
        attunement_col: Model-derived attunement
        action_col: Binary action executed (1) vs omission (0)
        subject_col: Participant ID

    Returns:
        dict with auc_mean, auc_std, success (auc ≥ 0.70), fpr/tpr for curve
    """
    df = trial_df[[attunement_col, action_col, subject_col]].dropna()

    if len(df) < 20:
        return {'auc': np.nan, 'success': False}

    # Compute per-participant AUC
    subject_aucs = []
    for subj_id, subj_df in df.groupby(subject_col):
        if len(subj_df) >= 10 and subj_df[action_col].nunique() == 2:  # Need both classes
            try:
                auc = roc_auc_score(subj_df[action_col], subj_df[attunement_col])
                subject_aucs.append(auc)
            except (ValueError, ZeroDivisionError) as e:
                logger.debug(f"Could not compute AUC for subject {subj_id}: {e}")
                continue
            except Exception as e:
                logger.warning(f"An unexpected error occurred during AUC calculation for subject {subj_id}: {e}")
                continue

    if len(subject_aucs) == 0:
        return {'auc': np.nan, 'success': False}

    auc_mean = np.mean(subject_aucs)
    auc_std = np.std(subject_aucs)

    # One-sample t-test: is mean AUC > 0.50 (chance)?
    t_stat, p_value = stats.ttest_1samp(subject_aucs, 0.50, alternative='greater')

    # Global ROC curve (pooled data)
    try:
        fpr, tpr, thresholds = roc_curve(df[action_col], df[attunement_col])
        global_auc = roc_auc_score(df[action_col], df[attunement_col])
    except (ValueError, ZeroDivisionError) as e:
        logger.debug(f"Could not compute global ROC/AUC: {e}")
        fpr, tpr, thresholds, global_auc = None, None, None, np.nan
    except Exception as e:
        logger.warning(f"An unexpected error occurred during global ROC/AUC calculation: {e}")
        fpr, tpr, thresholds, global_auc = None, None, None, np.nan

    success = auc_mean >= THRESHOLDS['H3a_action_auc'] and p_value < 0.05

    return {
        'auc_mean': float(auc_mean),
        'auc_std': float(auc_std),
        'auc_global': float(global_auc) if not np.isnan(global_auc) else None,
        'p': float(p_value),
        'n_participants': len(subject_aucs),
        'fpr': fpr.tolist() if fpr is not None else None,
        'tpr': tpr.tolist() if tpr is not None else None,
        'hypothesis': 'H3a',
        'threshold': THRESHOLDS['H3a_action_auc'],
        'success': bool(success),
    }


def compute_confidence_correlation(
    block_df: pd.DataFrame,
    attunement_col: str = 'attunement_score',
    confidence_col: str = 'confidence_rating',
    subject_col: str = 'participant',
) -> Dict:
    """
    Compute H3b: Attunement correlates with confidence (r ≥ 0.30).

    Block-level aggregation (mean attunement per block ~ mean confidence).

    Parameters:
        block_df: Block-level DataFrame
        attunement_col: Model attunement
        confidence_col: Self-reported confidence [0, 1]
        subject_col: Participant ID

    Returns:
        dict with r, p, n, success
    """
    return compute_convergent_validity(
        block_df,
        model_col=attunement_col,
        empirical_col=confidence_col,
        method='pearson',
        within_subject=True,
        subject_col=subject_col,
    )


# =============================================================================
# H4: Discriminant Validity (Trait Independence)
# =============================================================================

def compute_discriminant_validity(
    block_df: pd.DataFrame,
    attunement_col: str = 'attunement_score',
    affect_col: str = 'affect_valence',
    stress_col: str = 'stress_rating',
    trait_cols: List[str] = ['trait_openness', 'trait_conscientiousness'],
) -> Dict:
    """
    Compute H4a: Attunement independent of traits after controlling for state.

    Hierarchical regression:
        Model 1: attunement ~ affect + stress
        Model 2: attunement ~ affect + stress + trait_openness + trait_conscientiousness

    Test: ΔR² < 0.02 (traits add minimal variance).

    Parameters:
        block_df: Block-level DataFrame
        attunement_col: Model attunement
        affect_col: State affect
        stress_col: State stress
        trait_cols: List of trait variable columns

    Returns:
        dict with r2_model1, r2_model2, delta_r2, success (ΔR² < 0.02)
    """
    df = block_df[[attunement_col, affect_col, stress_col] + trait_cols].dropna()

    if len(df) < 30:
        return {'delta_r2': np.nan, 'success': False}

    # Model 1: State predictors only
    X1 = df[[affect_col, stress_col]].values
    y = df[attunement_col].values
    reg1 = LinearRegression().fit(X1, y)
    r2_model1 = reg1.score(X1, y)

    # Model 2: State + trait predictors
    X2 = df[[affect_col, stress_col] + trait_cols].values
    reg2 = LinearRegression().fit(X2, y)
    r2_model2 = reg2.score(X2, y)

    delta_r2 = r2_model2 - r2_model1

    # F-test for significance of ΔR²
    n = len(df)
    k1 = X1.shape[1]
    k2 = X2.shape[1]
    f_stat = ((r2_model2 - r2_model1) / (k2 - k1)) / ((1 - r2_model2) / (n - k2 - 1))
    p_value = 1 - stats.f.cdf(f_stat, k2 - k1, n - k2 - 1)

    # Success: ΔR² < 0.02 AND p > 0.05 (traits not significant)
    success = delta_r2 < THRESHOLDS['H4a_trait_delta_r2'] and p_value > 0.05

    return {
        'r2_model1': float(r2_model1),
        'r2_model2': float(r2_model2),
        'delta_r2': float(delta_r2),
        'f_stat': float(f_stat),
        'p': float(p_value),
        'hypothesis': 'H4a',
        'threshold': THRESHOLDS['H4a_trait_delta_r2'],
        'success': bool(success),
    }


def compute_icc(
    df: pd.DataFrame,
    value_col: str,
    subject_col: str = 'participant',
) -> float:
    """
    Compute Intraclass Correlation Coefficient (ICC) for state variable.

    ICC = between-subject variance / total variance.

    Higher ICC → more trait-like (stable across time).
    Lower ICC → more state-like (varies within-subject).

    For H4b: ICC < 0.40 indicates predominantly state variable.

    Parameters:
        df: DataFrame with repeated measures
        value_col: Column to compute ICC for (e.g., attunement_score)
        subject_col: Participant ID column

    Returns:
        ICC value [0, 1]
    """
    # One-way random effects ANOVA
    grouped = df.groupby(subject_col)[value_col]
    n_subjects = grouped.ngroups
    n_obs = len(df)

    # Between-subject variance
    subject_means = grouped.mean()
    grand_mean = df[value_col].mean()
    ss_between = sum(grouped.size() * (subject_means - grand_mean) ** 2)
    ms_between = ss_between / (n_subjects - 1)

    # Within-subject variance
    ss_within = sum((df[value_col] - df[subject_col].map(subject_means)) ** 2)
    ms_within = ss_within / (n_obs - n_subjects)

    # ICC(1,1) - one-way random effects, single measurement
    icc = (ms_between - ms_within) / (ms_between + (grouped.size().mean() - 1) * ms_within)

    return float(np.clip(icc, 0.0, 1.0))


# =============================================================================
# H5: Predictive Validity
# =============================================================================

def compute_lapse_prediction(
    participant_df: pd.DataFrame,
    block1_predictors: List[str] = ['mean_stress_block1', 'mean_attunement_block1'],
    block2_outcome: str = 'lapse_rate_block2',
    cv_folds: int = 10,
) -> Dict:
    """
    Compute H5a: Early-block predictors forecast late-block lapse rate.

    Uses cross-validated linear regression (10-fold CV).

    Parameters:
        participant_df: One row per participant with block-level aggregates
        block1_predictors: List of predictor columns (Block 1 means)
        block2_outcome: Outcome column (Block 2 lapse rate)
        cv_folds: Number of CV folds

    Returns:
        dict with rmse, r2, success (rmse < 0.15)
    """
    _require_sklearn("compute_lapse_prediction")
    df = participant_df[block1_predictors + [block2_outcome]].dropna()

    if len(df) < cv_folds:
        return {'rmse': np.nan, 'success': False}

    X = df[block1_predictors].values
    y = df[block2_outcome].values

    # Cross-validated prediction
    kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    reg = LinearRegression()

    # Get negative MSE (sklearn convention), convert to RMSE
    mse_scores = -cross_val_score(reg, X, y, cv=kfold, scoring='neg_mean_squared_error')
    rmse_mean = np.sqrt(mse_scores.mean())
    rmse_std = np.sqrt(mse_scores.std())

    # R² on full data (for reference)
    reg.fit(X, y)
    r2 = reg.score(X, y)

    success = rmse_mean < THRESHOLDS['H5a_lapse_rmse']

    return {
        'rmse_mean': float(rmse_mean),
        'rmse_std': float(rmse_std),
        'r2_full': float(r2),
        'n_participants': len(df),
        'cv_folds': cv_folds,
        'hypothesis': 'H5a',
        'threshold': THRESHOLDS['H5a_lapse_rmse'],
        'success': bool(success),
    }


def compute_lagged_omission_prediction(
    trial_df: pd.DataFrame,
    attunement_col: str = 'attunement_score',
    omission_col: str = 'omission',
    subject_col: str = 'participant',
) -> Dict:
    """
    Compute H5b: Attunement_t predicts omission_{t+1}.

    Lagged logistic regression within-subject.

    Parameters:
        trial_df: Trial-level DataFrame
        attunement_col: Model attunement at trial t
        omission_col: Binary omission at trial t (1=omission, 0=response)
        subject_col: Participant ID

    Returns:
        dict with odds_ratio, p, success (OR > 1.40 for 0.1-unit decrease)
    """
    _require_sklearn("compute_lagged_omission_prediction")
    df = trial_df[[attunement_col, omission_col, subject_col]].dropna()

    # Create lagged attunement (within-subject)
    df = df.sort_values([subject_col, 'trial_number'] if 'trial_number' in df else [subject_col])
    df['attunement_lag1'] = df.groupby(subject_col)[attunement_col].shift(1)
    df = df.dropna(subset=['attunement_lag1'])

    if len(df) < 50:
        return {'odds_ratio': np.nan, 'success': False}

    # Logistic regression: omission ~ attunement_lag1
    X = df[['attunement_lag1']].values
    y = df[omission_col].values

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            reg = LogisticRegression(max_iter=200, solver='lbfgs').fit(X, y)
            beta = reg.coef_[0][0]
            odds_ratio = np.exp(beta)

            # For 0.1-unit DECREASE in attunement → expect OR > 1.40 for omission
            # beta < 0 (lower attunement → higher omission)
            # OR for 0.1-unit increase = exp(0.1 * beta)
            # OR for 0.1-unit decrease = 1 / exp(0.1 * beta)
            or_per_decrease = 1.0 / np.exp(0.1 * beta)

            success = or_per_decrease >= THRESHOLDS['H5b_lag_or']

    except (ValueError, ConvergenceWarning) as e:
        logger.debug(f"Logistic regression for lagged omission failed: {e}")
        return {'odds_ratio': np.nan, 'success': False}
    except Exception as e:
        logger.warning(f"An unexpected error occurred during logistic regression for lagged omission: {e}")
        return {'odds_ratio': np.nan, 'success': False}

    return {
        'beta': float(beta),
        'odds_ratio': float(odds_ratio),
        'or_per_01_decrease': float(or_per_decrease),
        'n_trials': len(df),
        'hypothesis': 'H5b',
        'threshold': THRESHOLDS['H5b_lag_or'],
        'success': bool(success),
    }


# =============================================================================
# Master Function: Compute All Endpoints
# =============================================================================

def compute_all_endpoints(
    merged_df: pd.DataFrame,
    trial_df: Optional[pd.DataFrame] = None,
    block_df: Optional[pd.DataFrame] = None,
    participant_df: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Compute all preregistered validation endpoints (H1-H5).

    Parameters:
        merged_df: Tick/trial-level aligned model+empirical data
        trial_df: Trial-level DataFrame (for H2, H3a, H5b)
        block_df: Block-level DataFrame (for H3b, H4)
        participant_df: Participant-level DataFrame (for H5a)

    Returns:
        dict with all hypothesis results and summary success rate
    """
    results = {
        'schema_version': METRICS_SCHEMA_VERSION,
        'thresholds': THRESHOLDS,
        'hypotheses': {},
    }

    # H1a: Stress convergence
    if 'stress_rating' in merged_df.columns and 'schema_stress' in merged_df.columns:
        results['hypotheses']['H1a_stress_corr'] = compute_convergent_validity(
            merged_df,
            model_col='schema_stress',
            empirical_col='stress_rating',
            within_subject=True,
        )

    # H1b: HRV convergence
    if 'hrv_rmssd' in merged_df.columns and 'schema_stress' in merged_df.columns:
        results['hypotheses']['H1b_hrv_corr'] = compute_hrv_stress_convergence(
            merged_df,
            model_stress_col='schema_stress',
            hrv_col='hrv_rmssd',
        )

    # H2a: Memory load prediction
    if trial_df is not None and all(c in trial_df for c in ['mem_load', 'rt', 'accuracy']):
        results['hypotheses']['H2a_memload_prediction'] = compute_memory_load_prediction(
            trial_df,
            mem_load_col='mem_load',
            rt_col='rt',
            accuracy_col='accuracy',
        )

    # H3a: Action execution AUC
    if trial_df is not None and all(c in trial_df for c in ['attunement_score', 'action_executed']):
        results['hypotheses']['H3a_action_auc'] = compute_action_execution_auc(
            trial_df,
            attunement_col='attunement_score',
            action_col='action_executed',
        )

    # H3b: Confidence correlation
    if block_df is not None and all(c in block_df for c in ['attunement_score', 'confidence_rating']):
        results['hypotheses']['H3b_confidence_corr'] = compute_confidence_correlation(
            block_df,
            attunement_col='attunement_score',
            confidence_col='confidence_rating',
        )

    # H4a: Discriminant validity (trait independence)
    if block_df is not None and all(c in block_df for c in ['attunement_score', 'affect_valence', 'stress_rating', 'trait_openness']):
        results['hypotheses']['H4a_trait_independence'] = compute_discriminant_validity(
            block_df,
            attunement_col='attunement_score',
            affect_col='affect_valence',
            stress_col='stress_rating',
            trait_cols=['trait_openness', 'trait_conscientiousness'],
        )

    # H4b: ICC (state variability)
    if 'attunement_score' in merged_df.columns:
        icc = compute_icc(merged_df, value_col='attunement_score')
        results['hypotheses']['H4b_icc'] = {
            'icc': icc,
            'hypothesis': 'H4b',
            'threshold': THRESHOLDS['H4b_icc_threshold'],
            'success': icc < THRESHOLDS['H4b_icc_threshold'],
        }

    # H5a: Lapse prediction
    if participant_df is not None and all(c in participant_df for c in ['mean_stress_block1', 'mean_attunement_block1', 'lapse_rate_block2']):
        results['hypotheses']['H5a_lapse_prediction'] = compute_lapse_prediction(
            participant_df,
            block1_predictors=['mean_stress_block1', 'mean_attunement_block1'],
            block2_outcome='lapse_rate_block2',
        )

    # H5b: Lagged omission prediction
    if trial_df is not None and all(c in trial_df for c in ['attunement_score', 'omission']):
        results['hypotheses']['H5b_lagged_omission'] = compute_lagged_omission_prediction(
            trial_df,
            attunement_col='attunement_score',
            omission_col='omission',
        )

    # Summary success rate
    successes = [h.get('success', False) for h in results['hypotheses'].values()]
    results['summary'] = {
        'n_hypotheses_tested': len(successes),
        'n_successes': sum(successes),
        'success_rate': sum(successes) / len(successes) if successes else 0.0,
    }

    return results


# =============================================================================
# Calibration Plots & Diagnostics
# =============================================================================

def generate_calibration_plot(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    n_bins: int = 10,
) -> Dict:
    """
    Generate calibration plot data for probabilistic predictions.

    Useful for validating attunement → action execution probabilities.

    Parameters:
        y_true: True binary outcomes (0 or 1)
        y_pred_proba: Predicted probabilities [0, 1]
        n_bins: Number of bins for calibration curve

    Returns:
        dict with bin_edges, observed_freq, predicted_freq, calibration_error
    """
    bins = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_pred_proba, bins) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)

    observed_freq = []
    predicted_freq = []
    bin_centers = []

    for i in range(n_bins):
        mask = bin_indices == i
        if mask.sum() > 0:
            obs = y_true[mask].mean()
            pred = y_pred_proba[mask].mean()
            observed_freq.append(obs)
            predicted_freq.append(pred)
            bin_centers.append((bins[i] + bins[i + 1]) / 2)

    # Expected Calibration Error (ECE)
    if len(observed_freq) > 0:
        ece = np.mean(np.abs(np.array(observed_freq) - np.array(predicted_freq)))
    else:
        ece = np.nan

    return {
        'bin_centers': bin_centers,
        'observed_freq': observed_freq,
        'predicted_freq': predicted_freq,
        'calibration_error': float(ece),
    }


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    """
    Example: Compute validation metrics on synthetic data.
    """
    import sys

    # Create synthetic aligned data
    np.random.seed(42)
    n_obs = 200
    n_subjects = 20

    synthetic_df = pd.DataFrame({
        'participant': np.repeat(np.arange(n_subjects), n_obs // n_subjects),
        'schema_stress': np.random.rand(n_obs) * 0.5 + 0.3,  # [0.3, 0.8]
        'stress_rating': np.random.rand(n_obs) * 0.5 + 0.3,  # Correlated
        'attunement_score': np.random.rand(n_obs) * 0.6 + 0.2,  # [0.2, 0.8]
        'action_executed': (np.random.rand(n_obs) > 0.4).astype(int),  # 60% action rate
        'mem_load': np.random.rand(n_obs) * 0.7,
        'rt': np.random.rand(n_obs) * 500 + 600,  # [600, 1100]ms
        'accuracy': (np.random.rand(n_obs) > 0.3).astype(int),  # 70% accuracy
    })

    # Add correlation between model and empirical
    synthetic_df['stress_rating'] = 0.7 * synthetic_df['schema_stress'] + 0.3 * np.random.rand(n_obs)

    print("=== Testing Validation Metrics ===\n")

    # H1a: Stress convergence
    h1a = compute_convergent_validity(
        synthetic_df,
        model_col='schema_stress',
        empirical_col='stress_rating',
        within_subject=True,
    )
    print(f"H1a (Stress Convergence): r={h1a['r']:.3f}, p={h1a['p']:.3f}, success={h1a['success']}")

    # H3a: Action execution AUC
    h3a = compute_action_execution_auc(
        synthetic_df,
        attunement_col='attunement_score',
        action_col='action_executed',
    )
    print(f"H3a (Action AUC): AUC={h3a['auc_mean']:.3f}, success={h3a['success']}")

    # H4b: ICC
    icc = compute_icc(synthetic_df, value_col='attunement_score')
    print(f"H4b (ICC): {icc:.3f}, success={icc < 0.40}")

    print("\n✓ Validation metrics module working correctly")
