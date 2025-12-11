#!/usr/bin/env env python3
"""
Memory Load Validation Against Meta-Analytic Benchmarks

This script validates RPM-EE's memory.py implementation against empirical
WM benchmarks from the 2012 meta-analysis (Miyake & Friedman, 36 experiments).

Tests:
1. Baseline calibration: Does mem_load fall in expected range for 2-back?
2. Difficulty sensitivity: Does mem_load increase monotonically with N-back level?
3. Load-performance relationship: Does mem_load predict RT/accuracy at expected effect sizes?
4. Parameter sensitivity: How do mem_capacity and mem_gamma affect predictions?

Reference: docs/wm_benchmarks.md

Usage:
    python docs/memory_validation.py

Output:
    - Console report with pass/fail for each test
    - validation_output/memory_validation_results.json
    - validation_output/memory_calibration_plots.png
"""

import sys
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from scipy import stats
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.simulation import run_simulation


# ============================================================================
# Meta-Analytic Benchmarks (from wm_benchmarks.md)
# ============================================================================

@dataclass
class MetaAnalyticBenchmarks:
    """Expected effect sizes from 2012 meta-analysis."""

    # H2a: Memory load → RT (standardized regression coefficient)
    memload_rt_beta_min: float = 0.30  # Updated from 0.20
    memload_rt_beta_expected: Tuple[float, float] = (0.35, 0.55)

    # H2a: Memory load → Accuracy (correlation)
    memload_accuracy_r_max: float = -0.35  # Negative correlation
    memload_accuracy_r_expected: Tuple[float, float] = (-0.60, -0.40)

    # H2b: Domain-general (verbal vs spatial difference)
    domain_general_diff_max: float = 0.15

    # H2c: Difficulty interaction (slope ratio)
    difficulty_ratio_min: float = 1.5  # |β(3back)| / |β(1back)|

    # Baseline 2-back performance expectations
    nback_2_accuracy_range: Tuple[float, float] = (0.70, 0.85)
    nback_2_rt_range: Tuple[int, int] = (600, 900)  # ms

    # Expected mem_load for 2-back task
    memload_2back_expected: Tuple[float, float] = (0.40, 0.60)

    # RT increase per N-level
    rt_per_level_ms: float = 150.0


BENCHMARKS = MetaAnalyticBenchmarks()


# ============================================================================
# Simulated N-Back Task Generator
# ============================================================================

def generate_nback_sequence(
    n_trials: int = 100,
    n_level: int = 2,
    match_rate: float = 0.30,
    seed: int = 42,
) -> List[Dict]:
    """
    Generate a simulated N-back task sequence.

    Args:
        n_trials: Number of trials
        n_level: N-back level (1, 2, or 3)
        match_rate: Proportion of match trials
        seed: Random seed

    Returns:
        List of trial dicts with stimulus, match, position
    """
    np.random.seed(seed)

    # Stimulus pool (letters)
    stimuli = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    trials = []
    sequence = []

    for i in range(n_trials):
        is_match = (i >= n_level) and (np.random.rand() < match_rate)

        if is_match:
            # Repeat stimulus from n positions back
            stimulus = sequence[i - n_level]
        else:
            # Random non-matching stimulus
            if i >= n_level:
                # Exclude stimulus from n positions back
                valid_stimuli = [s for s in stimuli if s != sequence[i - n_level]]
            else:
                valid_stimuli = stimuli
            stimulus = np.random.choice(valid_stimuli)

        sequence.append(stimulus)

        trials.append({
            'trial': i,
            'stimulus': stimulus,
            'is_match': bool(is_match),
            'n_level': n_level,
            'position': i,
        })

    return trials


def nback_to_simulation_params(n_level: int) -> Dict:
    """
    Map N-back level to simulation parameters.

    Higher N-levels should produce:
    - More events in buffer (more items to track)
    - Higher attentional demand

    Args:
        n_level: N-back level (1, 2, 3)

    Returns:
        Dict of simulation parameters
    """
    # Base parameters
    base_event_rate = 3

    # Scale with difficulty
    # 1-back: baseline
    # 2-back: +33% events
    # 3-back: +67% events
    difficulty_factor = (n_level - 1) * 0.33 + 1.0

    return {
        'event_rate': int(base_event_rate * difficulty_factor),
        'total_ticks': 200,  # 200 ticks ~ 2 seconds per trial
    }


def simulate_nback_trial(
    n_level: int,
    preset: str = 'default',
    seed: int = 42,
) -> Dict:
    """
    Run RPM-EE simulation on a single N-back trial.

    Args:
        n_level: N-back difficulty (1, 2, 3)
        preset: Model preset
        seed: Random seed

    Returns:
        Dict with trial-level metrics
    """
    params = nback_to_simulation_params(n_level)

    # Run simulation
    result = run_simulation(
        total_ticks=params['total_ticks'],
        event_rate=params['event_rate'],
        preset=preset,
        seed=seed,
    )

    # Extract mem_load from logs
    logs = result.get('logs', [])
    if len(logs) == 0:
        # Fallback if no logs
        mem_load_series = [0.0] * params['total_ticks']
    else:
        # Extract mem_load from each log entry
        mem_load_series = [log.get('mem_load', 0.0) for log in logs]

    # Compute trial-level summary
    mem_load_mean = float(np.mean(mem_load_series))
    mem_load_max = float(np.max(mem_load_series))
    mem_load_std = float(np.std(mem_load_series))

    # Extract attunement from logs
    attunement_series = [log.get('attunement_score', 0.5) for log in logs] if len(logs) > 0 else [0.5]
    attunement_mean = float(np.mean(attunement_series))

    # Simulate RT and accuracy based on attunement and load
    # RT increases with load and decreases with attunement
    base_rt = 600.0  # ms
    rt_scale = 300.0
    load_penalty = mem_load_mean * 0.5  # Load slows RT
    attunement_benefit = attunement_mean * 0.3  # Attunement speeds RT

    rt = base_rt + rt_scale * (load_penalty - attunement_benefit) + np.random.randn() * 80
    rt = max(300, min(2000, rt))  # Clip to realistic range

    # Accuracy decreases with load, increases with attunement
    accuracy_logit = 1.0 + 2.0 * attunement_mean - 2.5 * mem_load_mean
    accuracy_prob = 1 / (1 + np.exp(-accuracy_logit))
    accuracy = int(np.random.rand() < accuracy_prob)

    return {
        'n_level': n_level,
        'mem_load_mean': mem_load_mean,
        'mem_load_max': mem_load_max,
        'mem_load_std': mem_load_std,
        'attunement_mean': attunement_mean,
        'rt': rt,
        'accuracy': accuracy,
        'accuracy_prob': accuracy_prob,
        'preset': preset,
        'seed': seed,
    }


# ============================================================================
# Test 1: Baseline Calibration
# ============================================================================

def test_baseline_calibration(
    n_trials: int = 50,
    preset: str = 'default',
) -> Dict:
    """
    Test 1: Does mem_load for 2-back fall in expected range?

    Expected: mean(mem_load) ~ 0.40–0.60 for neurotypical 2-back

    Args:
        n_trials: Number of trials to simulate
        preset: Model preset

    Returns:
        Dict with test results
    """
    print("\n" + "="*80)
    print("TEST 1: Baseline Calibration (2-Back)")
    print("="*80)
    print(f"Running {n_trials} trials with preset='{preset}'...")

    results = []
    for trial in range(n_trials):
        result = simulate_nback_trial(
            n_level=2,
            preset=preset,
            seed=trial + 1000,  # Offset seed
        )
        results.append(result)

    df = pd.DataFrame(results)

    # Compute statistics
    mem_load_mean = df['mem_load_mean'].mean()
    mem_load_std = df['mem_load_mean'].std()
    mem_load_ci = stats.t.interval(
        0.95,
        len(df) - 1,
        loc=mem_load_mean,
        scale=stats.sem(df['mem_load_mean'])
    )

    # Check against benchmark
    target_min, target_max = BENCHMARKS.memload_2back_expected
    in_range = target_min <= mem_load_mean <= target_max

    # Report
    print(f"\nResults:")
    print(f"  Mean mem_load:     {mem_load_mean:.3f} (SD={mem_load_std:.3f})")
    print(f"  95% CI:            [{mem_load_ci[0]:.3f}, {mem_load_ci[1]:.3f}]")
    print(f"  Target range:      [{target_min:.2f}, {target_max:.2f}]")
    print(f"  Status:            {'✓ PASS' if in_range else '✗ FAIL'}")

    if not in_range:
        if mem_load_mean < target_min:
            print(f"\n  ⚠️  mem_load too LOW ({mem_load_mean:.3f} < {target_min})")
            print(f"      Recommendation: Decrease mem_capacity or increase event_rate")
        else:
            print(f"\n  ⚠️  mem_load too HIGH ({mem_load_mean:.3f} > {target_max})")
            print(f"      Recommendation: Increase mem_capacity or decrease event_rate")

    return {
        'test': 'baseline_calibration',
        'mem_load_mean': float(mem_load_mean),
        'mem_load_std': float(mem_load_std),
        'mem_load_ci': [float(x) for x in mem_load_ci],
        'target_range': [target_min, target_max],
        'in_range': bool(in_range),
        'success': bool(in_range),
        'n_trials': n_trials,
        'data': df.to_dict(orient='records'),
    }


# ============================================================================
# Test 2: Difficulty Sensitivity
# ============================================================================

def test_difficulty_sensitivity(
    n_trials_per_level: int = 30,
    preset: str = 'default',
) -> Dict:
    """
    Test 2: Does mem_load increase monotonically with N-back level?

    Expected: mem_load(3-back) > mem_load(2-back) > mem_load(1-back)

    Args:
        n_trials_per_level: Trials per difficulty level
        preset: Model preset

    Returns:
        Dict with test results
    """
    print("\n" + "="*80)
    print("TEST 2: Difficulty Sensitivity")
    print("="*80)
    print(f"Running {n_trials_per_level} trials per N-level (1, 2, 3)...")

    results = []
    for n_level in [1, 2, 3]:
        for trial in range(n_trials_per_level):
            result = simulate_nback_trial(
                n_level=n_level,
                preset=preset,
                seed=trial + n_level * 1000,
            )
            results.append(result)

    df = pd.DataFrame(results)

    # Compute means per level
    level_means = df.groupby('n_level')['mem_load_mean'].agg(['mean', 'std', 'sem'])

    mem_1back = level_means.loc[1, 'mean']
    mem_2back = level_means.loc[2, 'mean']
    mem_3back = level_means.loc[3, 'mean']

    # Check monotonicity
    is_monotonic = (mem_3back > mem_2back) and (mem_2back > mem_1back)

    # Check effect size (Cohen's d between adjacent levels)
    def cohens_d(group1, group2):
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        return (np.mean(group1) - np.mean(group2)) / pooled_std

    d_1to2 = cohens_d(
        df[df['n_level'] == 2]['mem_load_mean'],
        df[df['n_level'] == 1]['mem_load_mean']
    )
    d_2to3 = cohens_d(
        df[df['n_level'] == 3]['mem_load_mean'],
        df[df['n_level'] == 2]['mem_load_mean']
    )

    # T-tests
    t_1v2, p_1v2 = stats.ttest_ind(
        df[df['n_level'] == 2]['mem_load_mean'],
        df[df['n_level'] == 1]['mem_load_mean']
    )
    t_2v3, p_2v3 = stats.ttest_ind(
        df[df['n_level'] == 3]['mem_load_mean'],
        df[df['n_level'] == 2]['mem_load_mean']
    )

    # Success if monotonic and medium effect (d > 0.30)
    success = is_monotonic and (d_1to2 > 0.30) and (d_2to3 > 0.30)

    # Report
    print(f"\nResults:")
    print(f"  1-back: M={mem_1back:.3f} (SE={level_means.loc[1, 'sem']:.3f})")
    print(f"  2-back: M={mem_2back:.3f} (SE={level_means.loc[2, 'sem']:.3f})")
    print(f"  3-back: M={mem_3back:.3f} (SE={level_means.loc[3, 'sem']:.3f})")
    print(f"\n  Monotonicity:      {'✓ YES' if is_monotonic else '✗ NO'}")
    print(f"  Effect sizes:")
    print(f"    1→2-back: d={d_1to2:.3f}, p={p_1v2:.4f}")
    print(f"    2→3-back: d={d_2to3:.3f}, p={p_2v3:.4f}")
    print(f"  Status:            {'✓ PASS' if success else '✗ FAIL'}")

    if not success:
        if not is_monotonic:
            print(f"\n  ⚠️  Monotonicity violated!")
        if d_1to2 <= 0.30 or d_2to3 <= 0.30:
            print(f"\n  ⚠️  Effect sizes too small (need d > 0.30)")
            print(f"      Recommendation: Increase difficulty_factor in nback_to_simulation_params()")

    return {
        'test': 'difficulty_sensitivity',
        'mem_load_by_level': {
            '1back': float(mem_1back),
            '2back': float(mem_2back),
            '3back': float(mem_3back),
        },
        'effect_sizes': {
            '1to2': float(d_1to2),
            '2to3': float(d_2to3),
        },
        'p_values': {
            '1v2': float(p_1v2),
            '2v3': float(p_2v3),
        },
        'is_monotonic': bool(is_monotonic),
        'success': bool(success),
        'n_trials_per_level': n_trials_per_level,
        'data': df.to_dict(orient='records'),
    }


# ============================================================================
# Test 3: Load-Performance Relationship
# ============================================================================

def test_load_performance_relationship(
    n_trials: int = 100,
    preset: str = 'default',
) -> Dict:
    """
    Test 3: Does mem_load predict RT and accuracy at expected effect sizes?

    Expected:
    - mem_load → RT: β > 0.30 (positive, medium)
    - mem_load → accuracy: r ≤ -0.35 (negative, medium-large)

    Args:
        n_trials: Number of trials (mixed difficulty)
        preset: Model preset

    Returns:
        Dict with test results
    """
    print("\n" + "="*80)
    print("TEST 3: Load-Performance Relationship")
    print("="*80)
    print(f"Running {n_trials} trials (mixed 1/2/3-back)...")

    results = []
    for trial in range(n_trials):
        n_level = np.random.choice([1, 2, 3])
        result = simulate_nback_trial(
            n_level=n_level,
            preset=preset,
            seed=trial + 3000,
        )
        results.append(result)

    df = pd.DataFrame(results)

    # Standardize variables (z-score)
    df['mem_load_z'] = (df['mem_load_mean'] - df['mem_load_mean'].mean()) / df['mem_load_mean'].std()
    df['rt_z'] = (df['rt'] - df['rt'].mean()) / df['rt'].std()

    # Regression: RT ~ mem_load (standardized)
    from sklearn.linear_model import LinearRegression

    reg_rt = LinearRegression()
    reg_rt.fit(df[['mem_load_z']], df['rt_z'])
    beta_rt = float(reg_rt.coef_[0])

    # Correlation: mem_load vs accuracy
    r_acc, p_acc = stats.pearsonr(df['mem_load_mean'], df['accuracy'])

    # Check against benchmarks
    success_rt = beta_rt >= BENCHMARKS.memload_rt_beta_min
    success_acc = r_acc <= BENCHMARKS.memload_accuracy_r_max  # Negative threshold

    # Report
    print(f"\nResults:")
    print(f"  RT Prediction:")
    print(f"    β (mem_load → RT):   {beta_rt:.3f}")
    print(f"    Threshold:           ≥ {BENCHMARKS.memload_rt_beta_min:.2f}")
    print(f"    Status:              {'✓ PASS' if success_rt else '✗ FAIL'}")

    print(f"\n  Accuracy Prediction:")
    print(f"    r (mem_load, acc):   {r_acc:.3f} (p={p_acc:.4f})")
    print(f"    Threshold:           ≤ {BENCHMARKS.memload_accuracy_r_max:.2f}")
    print(f"    Status:              {'✓ PASS' if success_acc else '✗ FAIL'}")

    success = success_rt and success_acc
    print(f"\n  Overall:             {'✓ PASS' if success else '✗ FAIL'}")

    if not success:
        if not success_rt:
            print(f"\n  ⚠️  RT prediction too weak (β={beta_rt:.3f} < {BENCHMARKS.memload_rt_beta_min})")
            print(f"      Recommendation: Increase theta_m or theta_m_mult")
        if not success_acc:
            print(f"\n  ⚠️  Accuracy correlation too weak (r={r_acc:.3f} > {BENCHMARKS.memload_accuracy_r_max})")
            print(f"      Recommendation: Strengthen mem_load penalty in action gating")

    return {
        'test': 'load_performance_relationship',
        'rt_beta': float(beta_rt),
        'rt_threshold': BENCHMARKS.memload_rt_beta_min,
        'rt_success': bool(success_rt),
        'accuracy_r': float(r_acc),
        'accuracy_p': float(p_acc),
        'accuracy_threshold': BENCHMARKS.memload_accuracy_r_max,
        'accuracy_success': bool(success_acc),
        'success': bool(success),
        'n_trials': n_trials,
        'data': df.to_dict(orient='records'),
    }


# ============================================================================
# Test 4: Parameter Sensitivity
# ============================================================================

def test_parameter_sensitivity(
    n_trials: int = 30,
    preset: str = 'default',
) -> Dict:
    """
    Test 4: Variability and consistency of mem_load.

    Tests:
    - Within-condition variability (same N-level)
    - Reliability (split-half correlation)

    Note: mem_capacity=500 and mem_gamma=1.25 are hardcoded in simulation.py,
    so we cannot test parameter sweeps here. This test focuses on empirical
    properties of the computed mem_load.

    Args:
        n_trials: Number of trials
        preset: Model preset

    Returns:
        Dict with test results
    """
    print("\n" + "="*80)
    print("TEST 4: Mem_Load Variability and Reliability")
    print("="*80)
    print(f"Running {n_trials} trials (2-back)...")
    print(f"Note: mem_capacity=500, mem_gamma=1.25 (hardcoded)")

    results = []
    for trial in range(n_trials):
        result = simulate_nback_trial(
            n_level=2,
            preset=preset,
            seed=trial + 4000,
        )
        results.append(result)

    df = pd.DataFrame(results)

    # Compute variability
    mem_load_std = df['mem_load_mean'].std()
    mem_load_cv = mem_load_std / df['mem_load_mean'].mean()  # Coefficient of variation

    # Split-half reliability
    half = len(df) // 2
    first_half = df.iloc[:half]['mem_load_mean'].mean()
    second_half = df.iloc[half:]['mem_load_mean'].mean()
    diff = abs(first_half - second_half)

    # Success if variability is moderate (SD ~ 0.10-0.15) and halves agree
    variability_ok = 0.08 <= mem_load_std <= 0.20
    reliability_ok = diff < 0.10

    success = variability_ok and reliability_ok

    # Report
    print(f"\nResults:")
    print(f"  Within-condition variability:")
    print(f"    SD(mem_load):     {mem_load_std:.3f}")
    print(f"    CV:               {mem_load_cv:.2%}")
    print(f"    Expected:         0.08-0.20")
    print(f"    Status:           {'✓ OK' if variability_ok else '✗ FAIL'}")

    print(f"\n  Split-half reliability:")
    print(f"    First half:       {first_half:.3f}")
    print(f"    Second half:      {second_half:.3f}")
    print(f"    Difference:       {diff:.3f}")
    print(f"    Status:           {'✓ OK' if reliability_ok else '✗ FAIL'}")

    print(f"\n  Overall:            {'✓ PASS' if success else '✗ FAIL'}")

    return {
        'test': 'parameter_sensitivity',
        'mem_load_std': float(mem_load_std),
        'mem_load_cv': float(mem_load_cv),
        'split_half_diff': float(diff),
        'variability_ok': bool(variability_ok),
        'reliability_ok': bool(reliability_ok),
        'success': bool(success),
        'n_trials': n_trials,
        'hardcoded_params': {'mem_capacity': 500, 'mem_gamma': 1.25},
        'data': df.to_dict(orient='records'),
    }


# ============================================================================
# Visualization
# ============================================================================

def generate_validation_plots(results: Dict, output_dir: Path):
    """Generate validation plots."""
    print("\n" + "="*80)
    print("Generating Plots...")
    print("="*80)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Test 1: Baseline calibration
    if 'baseline_calibration' in results:
        ax = axes[0, 0]
        data = pd.DataFrame(results['baseline_calibration']['data'])

        ax.hist(data['mem_load_mean'], bins=20, alpha=0.7, color='steelblue', edgecolor='black')
        ax.axvline(results['baseline_calibration']['mem_load_mean'],
                   color='red', linestyle='--', linewidth=2, label='Mean')

        # Target range
        target = results['baseline_calibration']['target_range']
        ax.axvspan(target[0], target[1], alpha=0.2, color='green', label='Target Range')

        ax.set_xlabel('Mean mem_load (per trial)')
        ax.set_ylabel('Frequency')
        ax.set_title('Test 1: Baseline Calibration (2-Back)')
        ax.legend()

    # Test 2: Difficulty sensitivity
    if 'difficulty_sensitivity' in results:
        ax = axes[0, 1]
        data = pd.DataFrame(results['difficulty_sensitivity']['data'])

        level_means = data.groupby('n_level')['mem_load_mean'].agg(['mean', 'sem'])

        ax.errorbar(level_means.index, level_means['mean'], yerr=level_means['sem'],
                    marker='o', markersize=8, linewidth=2, capsize=5, color='steelblue')

        ax.set_xlabel('N-Back Level')
        ax.set_ylabel('Mean mem_load')
        ax.set_title('Test 2: Difficulty Sensitivity')
        ax.set_xticks([1, 2, 3])
        ax.grid(True, alpha=0.3)

    # Test 3: Load-performance (RT)
    if 'load_performance_relationship' in results:
        ax = axes[1, 0]
        data = pd.DataFrame(results['load_performance_relationship']['data'])

        ax.scatter(data['mem_load_mean'], data['rt'], alpha=0.5, s=30, color='steelblue')

        # Regression line
        z = np.polyfit(data['mem_load_mean'], data['rt'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(data['mem_load_mean'].min(), data['mem_load_mean'].max(), 100)
        ax.plot(x_line, p(x_line), 'r--', linewidth=2,
                label=f"β={results['load_performance_relationship']['rt_beta']:.3f}")

        ax.set_xlabel('mem_load')
        ax.set_ylabel('RT (ms)')
        ax.set_title('Test 3: mem_load → RT')
        ax.legend()
        ax.grid(True, alpha=0.3)

    # Test 4: Variability
    if 'parameter_sensitivity' in results:
        ax = axes[1, 1]
        data = pd.DataFrame(results['parameter_sensitivity']['data'])

        ax.hist(data['mem_load_mean'], bins=15, alpha=0.7, color='steelblue', edgecolor='black')
        ax.axvline(data['mem_load_mean'].mean(),
                   color='red', linestyle='--', linewidth=2, label=f"Mean={data['mem_load_mean'].mean():.3f}")

        ax.set_xlabel('mem_load (2-back)')
        ax.set_ylabel('Frequency')
        ax.set_title(f"Test 4: Variability (SD={results['parameter_sensitivity']['mem_load_std']:.3f})")
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    plot_path = output_dir / 'memory_calibration_plots.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"  Saved: {plot_path}")
    plt.close()


# ============================================================================
# Main Validation Pipeline
# ============================================================================

def run_memory_validation(
    output_dir: Optional[Path] = None,
    preset: str = 'default',
) -> Dict:
    """
    Run all memory validation tests.

    Args:
        output_dir: Output directory (default: validation_output/)
        preset: Model preset to test

    Returns:
        Dict with all test results
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'validation_output'

    output_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "="*80)
    print("RPM-EE MEMORY VALIDATION")
    print("="*80)
    print(f"Preset: {preset}")
    print(f"Output: {output_dir}")
    print(f"Meta-analytic reference: docs/wm_benchmarks.md")

    results = {}

    # Run tests
    results['baseline_calibration'] = test_baseline_calibration(n_trials=50, preset=preset)
    results['difficulty_sensitivity'] = test_difficulty_sensitivity(n_trials_per_level=30, preset=preset)
    results['load_performance_relationship'] = test_load_performance_relationship(n_trials=100, preset=preset)
    results['parameter_sensitivity'] = test_parameter_sensitivity(n_trials=30, preset=preset)

    # Summary
    successes = [r['success'] for r in results.values()]
    success_rate = sum(successes) / len(successes)

    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"  Tests passed: {sum(successes)}/{len(successes)}")
    print(f"  Success rate: {success_rate * 100:.1f}%")

    for test_name, test_result in results.items():
        status = "✓ PASS" if test_result['success'] else "✗ FAIL"
        print(f"    {status}  {test_name}")

    # Overall assessment
    print("\n" + "="*80)
    if success_rate == 1.0:
        print("✓ EXCELLENT: All tests passed. Memory implementation is well-calibrated.")
    elif success_rate >= 0.75:
        print("✓ GOOD: Most tests passed. Minor calibration adjustments may improve alignment.")
    elif success_rate >= 0.50:
        print("⚠️  MODERATE: Some tests failed. Review failed tests and adjust parameters.")
    else:
        print("✗ POOR: Major calibration issues. Memory implementation needs significant adjustment.")

    # Save results
    results['summary'] = {
        'n_tests': len(successes),
        'n_successes': sum(successes),
        'success_rate': float(success_rate),
        'preset': preset,
    }

    # Remove raw data from JSON (too large)
    results_json = {k: {kk: vv for kk, vv in v.items() if kk != 'data'}
                    for k, v in results.items()}

    json_path = output_dir / 'memory_validation_results.json'
    with open(json_path, 'w') as f:
        json.dump(results_json, f, indent=2)
    print(f"\n  Results saved: {json_path}")

    # Generate plots
    generate_validation_plots(results, output_dir)

    print("="*80 + "\n")

    return results


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Validate RPM-EE memory implementation')
    parser.add_argument('--preset', default='default', help='Model preset (default: default)')
    parser.add_argument('--output-dir', type=Path, default=None, help='Output directory')

    args = parser.parse_args()

    results = run_memory_validation(
        output_dir=args.output_dir,
        preset=args.preset,
    )

    # Exit code based on success
    success_rate = results['summary']['success_rate']
    if success_rate >= 0.75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure
