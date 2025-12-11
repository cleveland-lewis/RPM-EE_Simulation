#!/usr/bin/env python3
# =============================================================================
# validation_example.py - Complete Validation Pipeline Integration Example
# =============================================================================
"""
Demonstrates the complete RPM-EE validation workflow:
    1. Load empirical data (lab session or EMA)
    2. Run simulation with data adapter (observation-conditioned mode)
    3. Align model outputs with empirical measurements
    4. Compute all preregistered validation metrics (H1-H5)
    5. Generate diagnostic plots and reports

This example uses SYNTHETIC data to illustrate the workflow. For real validation,
replace with actual participant data from Study 1 (Lab) or Study 2 (Ambulatory).

Usage:
    python docs/validation_example.py

Output:
    - validation_results.json: Complete metrics report
    - validation_plots/: ROC curves, calibration plots, correlation matrices
    - validation_summary.txt: Human-readable summary

References:
    - validation_protocol.md: Study designs and hypotheses
    - empirical_mapping.md: Variable measurement definitions
"""

import sys
import os
from pathlib import Path
from typing import Dict
import numpy as np
import pandas as pd
import json
import matplotlib
matplotlib.use('Agg')  # Headless backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from hashlib import sha256
from src.path_utils import hash_file
try:
    from src import __version__ as RPMEE_VERSION
except Exception:
    RPMEE_VERSION = "unknown"

# Add parent directory to path for imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.adapters import EmpiricalDataAdapter, align_model_to_empirical, EMAObserver
from src.validation_metrics import (
    compute_all_endpoints,
    compute_convergent_validity,
    compute_action_execution_auc,
    compute_icc,
    generate_calibration_plot,
)
from src.path_utils import hash_file
try:
    from src import __version__ as RPMEE_VERSION
except Exception:
    RPMEE_VERSION = "unknown"
# Note: observation-conditioned mode not yet implemented in simulation.py
# For now, we'll simulate it by running standard simulation and post-hoc alignment


# =============================================================================
# Step 1: Generate Synthetic Empirical Data (Lab Session)
# =============================================================================

def generate_synthetic_lab_data(
    n_participants: int = 20,
    n_trials_per_participant: int = 150,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic empirical data mimicking Study 1 (Lab).

    Simulates:
        - Oddball task (prediction error)
        - N-back task (memory load, RT, accuracy)
        - EMA prompts (stress, affect)
        - Action execution (response vs. omission)
        - Confidence ratings

    Returns:
        DataFrame with trial-level data for all participants
    """
    np.random.seed(seed)

    data = []

    for subj_id in range(n_participants):
        # Participant-level traits (for discriminant validity testing)
        trait_openness = np.random.randn() * 1.0 + 3.0  # Mean=3, SD=1
        trait_conscientiousness = np.random.randn() * 1.0 + 3.5

        # Participant-level baseline stress/attunement (between-subject variance)
        baseline_stress = np.clip(np.random.randn() * 0.15 + 0.45, 0.2, 0.8)
        baseline_attunement = np.clip(np.random.randn() * 0.15 + 0.60, 0.3, 0.9)

        for trial_idx in range(n_trials_per_participant):
            # Time (ms from session start)
            timestamp = trial_idx * 2500  # ~2.5 sec per trial

            # Block assignment (2 blocks of 75 trials each)
            block = 0 if trial_idx < 75 else 1

            # State affect (oscillates + noise)
            affect_valence = 0.5 * np.sin(trial_idx / 20) + np.random.randn() * 0.3
            affect_valence = np.clip(affect_valence, -1, 1)

            # State stress (correlated with trial difficulty, with drift)
            trial_difficulty = 0.3 + 0.4 * (trial_idx / n_trials_per_participant)  # Increases over time
            stress_rating = baseline_stress + 0.3 * trial_difficulty + np.random.randn() * 0.15
            stress_rating = np.clip(stress_rating, 0, 1)

            # Memory load (from N-back performance)
            nback_accuracy = np.clip(0.85 - 0.4 * trial_difficulty + np.random.randn() * 0.1, 0, 1)
            nback_rt = 700 + 300 * trial_difficulty + np.random.randn() * 100  # ms
            mem_load = (1 - nback_accuracy) * 0.7 + (nback_rt - 600) / 800 * 0.3
            mem_load = np.clip(mem_load, 0, 1)

            # External load (oddball stimulus intensity)
            is_oddball = (trial_idx % 5 == 0)  # 20% oddball rate
            vision_load = 0.7 if is_oddball else 0.3 + np.random.rand() * 0.2

            # Model-derived attunement (ground truth for this synthetic example)
            # Will be "predicted" by RPM-EE and compared to this ground truth
            attunement_true = baseline_attunement - 0.4 * stress_rating - 0.3 * mem_load + 0.2 * affect_valence
            attunement_true = np.clip(attunement_true, 0, 1)

            # Action executed (influenced by attunement)
            action_prob = attunement_true * (1 - 0.3 * stress_rating)
            action_executed = int(np.random.rand() < action_prob)
            omission = 1 - action_executed

            # Confidence rating (correlated with attunement)
            confidence_rating = attunement_true + np.random.randn() * 0.15
            confidence_rating = np.clip(confidence_rating, 0, 1)

            # HRV (inverse correlated with stress)
            hrv_rmssd = np.exp(4.0 - 2.0 * stress_rating + np.random.randn() * 0.2)  # ms

            data.append({
                'participant': f'P{subj_id:03d}',
                'trial_number': trial_idx,
                'block': block,
                'timestamp': timestamp,
                'affect_valence': affect_valence,
                'stress_rating': stress_rating,
                'vision_load': vision_load,
                'auditory_load': 0.2 + np.random.rand() * 0.1,
                'touch_load': 0.1,
                'nback_accuracy': nback_accuracy,
                'nback_rt': nback_rt,
                'mem_load_empirical': mem_load,
                'action_executed': action_executed,
                'omission': omission,
                'confidence_rating': confidence_rating,
                'hrv_rmssd': hrv_rmssd,
                'attunement_ground_truth': attunement_true,  # For validation
                'trait_openness': trait_openness,
                'trait_conscientiousness': trait_conscientiousness,
            })

    df = pd.DataFrame(data)

    print(f"Generated synthetic data: {len(df)} trials, {n_participants} participants")
    print(f"  Mean stress: {df['stress_rating'].mean():.3f}")
    print(f"  Mean attunement (ground truth): {df['attunement_ground_truth'].mean():.3f}")
    print(f"  Action execution rate: {df['action_executed'].mean():.1%}")

    return df


# =============================================================================
# Step 2: Run RPM-EE Simulation (Currently: Post-Hoc Alignment)
# =============================================================================

def run_rpm_simulation_on_empirical_data(
    empirical_df: pd.DataFrame,
    preset: str = 'default',
    seed: int = 42,
) -> pd.DataFrame:
    """
    Run RPM-EE simulation aligned with empirical data.

    NOTE: This is a PLACEHOLDER. Once observation-conditioned mode is implemented
    in simulation.py, this function will use data_adapter instead of post-hoc alignment.

    For now, we'll create synthetic model outputs that mimic what the real simulation
    would produce, with realistic correlations to empirical measures.

    Parameters:
        empirical_df: Trial-level empirical data
        preset: RPM-EE preset to use
        seed: Random seed

    Returns:
        DataFrame with model outputs aligned to empirical trials
    """
    np.random.seed(seed)

    print(f"\nRunning RPM-EE simulation (preset={preset})...")

    # TODO: Replace with actual observation-conditioned simulation:
    # adapter = EmpiricalDataAdapter.from_dataframe(empirical_df, tick_rate='trial')
    # result = run_simulation(data_adapter=adapter, observed_mode=1, preset=preset)
    # model_df = pd.DataFrame(result['logs'])

    # For now: Generate realistic model outputs
    model_outputs = []

    for idx, row in empirical_df.iterrows():
        # Model stress (correlated r~0.50 with empirical stress)
        schema_stress = 0.50 * row['stress_rating'] + 0.50 * np.random.rand()
        schema_stress = np.clip(schema_stress, 0, 1)

        # Model attunement (correlated r~0.60 with ground truth)
        # Realistic formula: influenced by affect, stress, mem_load
        att_model = (
            0.60 +  # baseline (theta0)
            0.20 * row['affect_valence'] -
            0.35 * schema_stress -
            0.25 * row['mem_load_empirical'] +
            np.random.randn() * 0.10  # noise
        )
        att_model = np.clip(att_model, 0, 1)

        # Memory load (from model's internal calculation, correlated with empirical)
        mem_load_model = 0.70 * row['mem_load_empirical'] + 0.30 * np.random.rand()
        mem_load_model = np.clip(mem_load_model, 0, 1)

        # External load (precision-weighted combination)
        ext_load_model = 0.6 * row['vision_load'] + 0.3 * row['auditory_load'] + 0.1 * row['touch_load']

        # Prediction error (computed from external load vs. expectation)
        # Use simple EMA observer
        if idx == 0 or row['trial_number'] == 0:
            pe_model = 0.3  # Initial
        else:
            prev_ext = model_outputs[-1]['ext_load'] if model_outputs else 0.3
            pe_model = abs(ext_load_model - prev_ext)

        # Selection confidence (from model, correlated with empirical confidence)
        selection_confidence = 1.0 - 0.5 * schema_stress - 0.3 * pe_model
        selection_confidence = np.clip(selection_confidence, 0, 1)

        # Action executed (model prediction, for validation vs. empirical)
        action_prob_model = att_model * (1 - 0.2 * schema_stress)
        action_executed_model = int(np.random.rand() < action_prob_model)

        model_outputs.append({
            'participant': row['participant'],
            'trial_number': row['trial_number'],
            'timestamp': row['timestamp'],
            'schema_stress': schema_stress,
            'attunement_score': att_model,
            'mem_load': mem_load_model,
            'ext_load': ext_load_model,
            'prediction_error': pe_model,
            'selection_confidence': selection_confidence,
            'action_executed_model': action_executed_model,
            'affect_volatility': 0.2,  # Placeholder
        })

    model_df = pd.DataFrame(model_outputs)

    print(f"  Model mean attunement: {model_df['attunement_score'].mean():.3f}")
    print(f"  Model mean stress: {model_df['schema_stress'].mean():.3f}")

    return model_df


# =============================================================================
# Step 3: Align and Merge Data
# =============================================================================

def merge_empirical_and_model(
    empirical_df: pd.DataFrame,
    model_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge empirical and model DataFrames for validation analyses.

    Parameters:
        empirical_df: Empirical measurements
        model_df: Model outputs

    Returns:
        Merged DataFrame with both empirical and model columns
    """
    merged = pd.merge(
        empirical_df,
        model_df,
        on=['participant', 'trial_number', 'timestamp'],
        how='inner',
        suffixes=('_empirical', '_model')
    )

    print(f"\nMerged data: {len(merged)} trials")
    return merged


# =============================================================================
# Step 4: Compute Validation Metrics
# =============================================================================

def run_validation_analyses(merged_df: pd.DataFrame) -> Dict:
    """
    Compute all preregistered validation metrics (H1-H5).

    Parameters:
        merged_df: Merged empirical + model data

    Returns:
        dict with all validation results
    """
    print("\n" + "="*70)
    print("COMPUTING VALIDATION METRICS (H1-H5)")
    print("="*70)

    # Prepare aggregated DataFrames
    # Block-level aggregates
    block_df = merged_df.groupby(['participant', 'block']).agg({
        'attunement_score': 'mean',
        'schema_stress': 'mean',
        'stress_rating': 'mean',
        'affect_valence': 'mean',
        'confidence_rating': 'mean',
        'trait_openness': 'first',
        'trait_conscientiousness': 'first',
    }).reset_index()

    # Participant-level aggregates (for H5a)
    participant_df = merged_df.groupby('participant').apply(
        lambda g: pd.Series({
            'mean_stress_block1': g[g['block'] == 0]['schema_stress'].mean(),
            'mean_attunement_block1': g[g['block'] == 0]['attunement_score'].mean(),
            'lapse_rate_block2': (g[g['block'] == 1]['omission']).mean(),
        })
    ).reset_index()

    # Compute all endpoints
    results = compute_all_endpoints(
        merged_df=merged_df,
        trial_df=merged_df,  # Trial-level is same as merged
        block_df=block_df,
        participant_df=participant_df,
    )

    # Print summary
    print("\n" + "-"*70)
    print("VALIDATION RESULTS SUMMARY")
    print("-"*70)

    for hyp_name, hyp_result in results['hypotheses'].items():
        success = hyp_result.get('success', False)
        status = "✓ PASS" if success else "✗ FAIL"

        if 'r' in hyp_result:
            print(f"{hyp_name}: r={hyp_result['r']:.3f}, p={hyp_result.get('p', np.nan):.3f} {status}")
        elif 'auc_mean' in hyp_result:
            print(f"{hyp_name}: AUC={hyp_result['auc_mean']:.3f} {status}")
        elif 'delta_r2' in hyp_result:
            print(f"{hyp_name}: ΔR²={hyp_result['delta_r2']:.4f} {status}")
        elif 'icc' in hyp_result:
            print(f"{hyp_name}: ICC={hyp_result['icc']:.3f} {status}")
        elif 'rmse_mean' in hyp_result:
            print(f"{hyp_name}: RMSE={hyp_result['rmse_mean']:.3f} {status}")
        else:
            print(f"{hyp_name}: {status}")

    print("-"*70)
    print(f"Overall Success Rate: {results['summary']['success_rate']:.1%} "
          f"({results['summary']['n_successes']}/{results['summary']['n_hypotheses_tested']})")
    print("-"*70)

    return results


# =============================================================================
# Step 5: Generate Diagnostic Plots
# =============================================================================

def generate_validation_plots(
    merged_df: pd.DataFrame,
    results: Dict,
    output_dir: Path,
):
    """
    Generate diagnostic plots for validation report.

    Plots:
        1. Correlation matrix (model vs. empirical)
        2. ROC curve (attunement → action execution)
        3. Calibration plot (attunement → action probability)
        4. Scatter plots (stress, attunement, memory load)
        5. ICC visualization (within vs. between subject variance)

    Parameters:
        merged_df: Merged data
        results: Validation results dict
        output_dir: Directory to save plots
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating diagnostic plots in {output_dir}...")

    # Set style
    sns.set_style('whitegrid')
    sns.set_palette('colorblind')

    # 1. Correlation matrix
    fig, ax = plt.subplots(figsize=(10, 8))
    corr_cols = [
        'schema_stress', 'stress_rating',
        'attunement_score', 'attunement_ground_truth',
        'mem_load', 'mem_load_empirical',
        'confidence_rating', 'selection_confidence',
    ]
    corr_df = merged_df[corr_cols].corr()

    sns.heatmap(corr_df, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                vmin=-1, vmax=1, square=True, ax=ax)
    ax.set_title('Correlation Matrix: Model vs. Empirical', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'correlation_matrix.png', dpi=150)
    plt.close()

    # 2. ROC curve (H3a)
    if 'H3a_action_auc' in results['hypotheses']:
        h3a = results['hypotheses']['H3a_action_auc']
        if h3a['fpr'] is not None and h3a['tpr'] is not None:
            fig, ax = plt.subplots(figsize=(7, 7))
            ax.plot(h3a['fpr'], h3a['tpr'], linewidth=2, label=f"AUC={h3a['auc_global']:.3f}")
            ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Chance (AUC=0.50)')
            ax.axhline(y=0.70, color='red', linestyle=':', linewidth=1, alpha=0.5, label='Threshold (0.70)')
            ax.set_xlabel('False Positive Rate', fontsize=12)
            ax.set_ylabel('True Positive Rate', fontsize=12)
            ax.set_title('ROC Curve: Attunement → Action Execution (H3a)', fontsize=14, fontweight='bold')
            ax.legend(loc='lower right')
            ax.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig(output_dir / 'roc_curve_h3a.png', dpi=150)
            plt.close()

    # 3. Calibration plot
    fig, ax = plt.subplots(figsize=(7, 7))
    calib = generate_calibration_plot(
        merged_df['action_executed'].values,
        merged_df['attunement_score'].values,
        n_bins=10
    )
    ax.plot(calib['predicted_freq'], calib['observed_freq'], 'o-', linewidth=2, markersize=8, label='Calibration')
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Perfect Calibration')
    ax.set_xlabel('Predicted Action Probability (Attunement)', fontsize=12)
    ax.set_ylabel('Observed Action Frequency', fontsize=12)
    ax.set_title(f'Calibration Plot (ECE={calib["calibration_error"]:.3f})', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'calibration_plot.png', dpi=150)
    plt.close()

    # 4. Scatter plots (model vs. empirical)
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))

    # Stress
    ax = axes[0, 0]
    for subj in merged_df['participant'].unique()[:5]:  # Show first 5 participants
        subj_df = merged_df[merged_df['participant'] == subj]
        ax.scatter(subj_df['stress_rating'], subj_df['schema_stress'], alpha=0.6, s=20)
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Empirical Stress (EMA)', fontsize=11)
    ax.set_ylabel('Model Stress (schema_stress)', fontsize=11)
    ax.set_title('H1a: Stress Convergence', fontsize=12, fontweight='bold')
    ax.grid(alpha=0.3)

    # Attunement
    ax = axes[0, 1]
    for subj in merged_df['participant'].unique()[:5]:
        subj_df = merged_df[merged_df['participant'] == subj]
        ax.scatter(subj_df['attunement_ground_truth'], subj_df['attunement_score'], alpha=0.6, s=20)
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Ground Truth Attunement', fontsize=11)
    ax.set_ylabel('Model Attunement', fontsize=11)
    ax.set_title('Attunement Alignment', fontsize=12, fontweight='bold')
    ax.grid(alpha=0.3)

    # Memory load
    ax = axes[1, 0]
    ax.scatter(merged_df['mem_load_empirical'], merged_df['mem_load'], alpha=0.5, s=15)
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Empirical Memory Load', fontsize=11)
    ax.set_ylabel('Model Memory Load', fontsize=11)
    ax.set_title('H2: Memory Load Convergence', fontsize=12, fontweight='bold')
    ax.grid(alpha=0.3)

    # Confidence
    ax = axes[1, 1]
    ax.scatter(merged_df['confidence_rating'], merged_df['selection_confidence'], alpha=0.5, s=15)
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Empirical Confidence', fontsize=11)
    ax.set_ylabel('Model Selection Confidence', fontsize=11)
    ax.set_title('H3b: Confidence Correlation', fontsize=12, fontweight='bold')
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / 'scatter_plots.png', dpi=150)
    plt.close()

    # 5. ICC visualization (within vs. between variance)
    fig, ax = plt.subplots(figsize=(10, 6))

    participant_means = merged_df.groupby('participant')['attunement_score'].mean()
    participant_stds = merged_df.groupby('participant')['attunement_score'].std()

    x = np.arange(len(participant_means))
    ax.errorbar(x, participant_means, yerr=participant_stds, fmt='o', capsize=5, alpha=0.7)
    ax.axhline(y=merged_df['attunement_score'].mean(), color='red', linestyle='--', linewidth=2, label='Grand Mean')
    ax.set_xlabel('Participant', fontsize=12)
    ax.set_ylabel('Attunement Score', fontsize=12)
    ax.set_title(f'H4b: Within-Subject Variability (ICC={compute_icc(merged_df, "attunement_score"):.3f})',
                 fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'icc_visualization.png', dpi=150)
    plt.close()

    print(f"  Saved 5 diagnostic plots to {output_dir}")


# =============================================================================
# Step 6: Generate Reports
# =============================================================================

def save_validation_report(
    results: Dict,
    output_path: Path,
    *,
    metadata: Dict | None = None,
):
    """
    Save validation results to JSON file.

    Parameters:
        results: Validation results dict
        output_path: Path to save JSON report
    """
    payload = dict(results)
    if metadata:
        payload.setdefault("metadata", {}).update(metadata)
    with open(output_path, 'w') as f:
        json.dump(payload, f, indent=2)

    print(f"\nSaved validation results to {output_path}")


def generate_human_readable_summary(
    results: Dict,
    merged_df: pd.DataFrame,
    output_path: Path,
):
    """
    Generate human-readable validation summary (text report).

    Parameters:
        results: Validation results dict
        merged_df: Merged data
        output_path: Path to save text report
    """
    with open(output_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("RPM-EE VALIDATION REPORT\n")
        f.write("="*80 + "\n\n")

        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Schema Version: {results['schema_version']}\n\n")

        f.write("-"*80 + "\n")
        f.write("SAMPLE CHARACTERISTICS\n")
        f.write("-"*80 + "\n")
        f.write(f"Total observations: {len(merged_df)}\n")
        f.write(f"Participants: {merged_df['participant'].nunique()}\n")
        f.write(f"Trials per participant (mean): {len(merged_df) / merged_df['participant'].nunique():.1f}\n\n")

        f.write("-"*80 + "\n")
        f.write("HYPOTHESIS TESTING RESULTS\n")
        f.write("-"*80 + "\n\n")

        for hyp_name, hyp_result in results['hypotheses'].items():
            success = hyp_result.get('success', False)
            status_icon = "✓" if success else "✗"

            f.write(f"{status_icon} {hyp_name}\n")

            if 'r' in hyp_result:
                f.write(f"    Correlation: r = {hyp_result['r']:.3f}, p = {hyp_result.get('p', np.nan):.4f}\n")
                f.write(f"    Threshold: r ≥ {hyp_result.get('threshold', 'N/A')}\n")
                if 'r_std' in hyp_result:
                    f.write(f"    Within-subject SD: {hyp_result['r_std']:.3f}\n")

            elif 'auc_mean' in hyp_result:
                f.write(f"    AUC (mean): {hyp_result['auc_mean']:.3f} ± {hyp_result.get('auc_std', 0):.3f}\n")
                f.write(f"    Threshold: AUC ≥ {hyp_result.get('threshold', 'N/A')}\n")
                f.write(f"    Participants: {hyp_result.get('n_participants', 'N/A')}\n")

            elif 'delta_r2' in hyp_result:
                f.write(f"    ΔR² (traits): {hyp_result['delta_r2']:.4f}\n")
                f.write(f"    Threshold: ΔR² < {hyp_result.get('threshold', 'N/A')}\n")
                f.write(f"    F-test p-value: {hyp_result.get('p', np.nan):.4f}\n")

            elif 'icc' in hyp_result:
                f.write(f"    ICC: {hyp_result['icc']:.3f}\n")
                f.write(f"    Threshold: ICC < {hyp_result.get('threshold', 'N/A')}\n")

            elif 'rmse_mean' in hyp_result:
                f.write(f"    RMSE (CV): {hyp_result['rmse_mean']:.3f}\n")
                f.write(f"    Threshold: RMSE < {hyp_result.get('threshold', 'N/A')}\n")

            f.write("\n")

        f.write("-"*80 + "\n")
        f.write("OVERALL SUMMARY\n")
        f.write("-"*80 + "\n")
        f.write(f"Hypotheses tested: {results['summary']['n_hypotheses_tested']}\n")
        f.write(f"Hypotheses passed: {results['summary']['n_successes']}\n")
        f.write(f"Success rate: {results['summary']['success_rate']:.1%}\n\n")

        f.write("="*80 + "\n")

    print(f"Saved human-readable summary to {output_path}")


# =============================================================================
# Main Pipeline
# =============================================================================

def main():
    """
    Main validation pipeline.

    Steps:
        1. Generate synthetic empirical data (or load real data)
        2. Run RPM-EE simulation with data adapter
        3. Merge and align outputs
        4. Compute validation metrics
        5. Generate plots and reports
    """
    print("="*80)
    print("RPM-EE VALIDATION PIPELINE")
    print("="*80)

    # Output directories (timestamped run label for traceability)
    run_label = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    output_dir = REPO_ROOT / 'validation_output' / run_label
    plots_dir = output_dir / 'plots'
    output_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate synthetic data
    print("\n[STEP 1] Generating synthetic empirical data...")
    empirical_df = generate_synthetic_lab_data(n_participants=20, n_trials_per_participant=150, seed=42)

    # Save empirical data
    empirical_path = output_dir / 'empirical_data.csv'
    empirical_df.to_csv(empirical_path, index=False)
    print(f"  Saved to {empirical_path}")

    # Step 2: Run simulation
    print("\n[STEP 2] Running RPM-EE simulation...")
    model_df = run_rpm_simulation_on_empirical_data(empirical_df, preset='default', seed=42)

    # Save model outputs
    model_path = output_dir / 'model_outputs.csv'
    model_df.to_csv(model_path, index=False)
    print(f"  Saved to {model_path}")

    # Step 3: Merge
    print("\n[STEP 3] Merging empirical and model data...")
    merged_df = merge_empirical_and_model(empirical_df, model_df)

    # Step 4: Compute validation metrics
    print("\n[STEP 4] Computing validation metrics...")
    results = run_validation_analyses(merged_df)

    # Step 5: Generate plots
    print("\n[STEP 5] Generating diagnostic plots...")
    generate_validation_plots(merged_df, results, plots_dir)

    # Step 6: Save reports + traceability metadata
    print("\n[STEP 6] Saving reports...")
    validation_meta = {
        "preset": "default",
        "seed": 42,
        "run_label": run_label,
        "version": RPMEE_VERSION,
        "model_outputs_hash": hash_file(model_path),
        "empirical_data_hash": hash_file(empirical_path),
    }

    save_validation_report(results, output_dir / 'validation_results.json', metadata=validation_meta)
    with open(output_dir / "validation_meta.json", "w") as fmeta:
        json.dump(validation_meta, fmeta, indent=2)
    generate_human_readable_summary(results, merged_df, output_dir / 'validation_summary.txt')

    print("\n" + "="*80)
    print("VALIDATION PIPELINE COMPLETE")
    print("="*80)
    print(f"\nOutputs saved to: {output_dir}")
    print(f"  - empirical_data.csv: Synthetic empirical measurements")
    print(f"  - model_outputs.csv: RPM-EE simulation results")
    print(f"  - validation_results.json: Complete metrics (H1-H5)")
    print(f"  - validation_summary.txt: Human-readable report")
    print(f"  - validation_meta.json: Traceability (preset/seed/version/hashes/run_label)")
    print(f"  - plots/: Diagnostic visualizations")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
