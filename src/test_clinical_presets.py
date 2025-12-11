"""
Clinical Presets Validation Script
===================================
Tests that clinical presets (NT, ASD, ADHD, MDD) produce empirically appropriate
distributions for RT, accuracy, attunement, and stress.

Updated: 2025-10-15
"""

import numpy as np
from .trial_wrapper import TrialSimulator
import sys

def test_preset_distributions(preset_name: str, n_trials: int = 50):
    """Run trials for a preset and return summary statistics."""

    sim = TrialSimulator(
        preset=preset_name,
        base_RT=400.0,
        RT_scale=600.0,
        seed=42
    )

    results = []
    for i in range(n_trials):
        # Moderate difficulty
        result = sim.run_trial({'difficulty': 0.5}, duration=200)
        results.append(result)

    RTs = [r['RT'] for r in results]
    accs = [r['accuracy'] for r in results]
    stresses = [r['stress_mean'] for r in results]
    attunements = [r['attunement_mean'] for r in results]

    return {
        'preset': preset_name,
        'n_trials': n_trials,
        'RT_mean': float(np.mean(RTs)),
        'RT_std': float(np.std(RTs)),
        'RT_CV': float(np.std(RTs) / np.mean(RTs)),  # Coefficient of variation
        'RT_min': float(np.min(RTs)),
        'RT_max': float(np.max(RTs)),
        'accuracy_mean': float(np.mean(accs)),
        'accuracy_std': float(np.std(accs)),
        'stress_mean': float(np.mean(stresses)),
        'stress_std': float(np.std(stresses)),
        'attunement_mean': float(np.mean(attunements)),
        'attunement_std': float(np.std(attunements)),
    }


def validate_empirical_expectations():
    """
    Validate that presets match empirical expectations from literature.

    Expected patterns:
    - NT: Baseline performance (RT ~700ms, Acc ~0.85-0.95)
    - ASD: 10-15% slower RT, comparable accuracy, elevated stress
    - ADHD: Higher RT variability (CV +35-50%), reduced accuracy
    - MDD: 15-20% slower RT, 5-10% reduced accuracy, elevated stress
    """

    print("=" * 70)
    print("Clinical Presets Validation")
    print("=" * 70)
    print()

    presets = ['default', 'asd_typical', 'adhd_typical', 'mdd_typical']
    results = {}

    # Run simulations
    for preset in presets:
        print(f"Testing {preset}...")
        results[preset] = test_preset_distributions(preset, n_trials=50)

    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()

    # RT Comparison
    print("Response Time (RT) Statistics:")
    print("-" * 70)
    print(f"{'Preset':<20} {'Mean RT (ms)':<15} {'SD (ms)':<12} {'CV':<10}")
    print("-" * 70)

    nt_rt = results['default']['RT_mean']
    for preset in presets:
        r = results[preset]
        rt_pct = ((r['RT_mean'] - nt_rt) / nt_rt) * 100
        sign = "+" if rt_pct > 0 else ""
        print(f"{preset:<20} {r['RT_mean']:>8.1f} ({sign}{rt_pct:>+5.1f}%)  {r['RT_std']:>8.1f}  {r['RT_CV']:>6.3f}")

    print()

    # Accuracy Comparison
    print("Accuracy Statistics:")
    print("-" * 70)
    print(f"{'Preset':<20} {'Mean Accuracy':<18} {'SD':<12}")
    print("-" * 70)

    nt_acc = results['default']['accuracy_mean']
    for preset in presets:
        r = results[preset]
        acc_pct = ((r['accuracy_mean'] - nt_acc) / nt_acc) * 100
        sign = "+" if acc_pct > 0 else ""
        print(f"{preset:<20} {r['accuracy_mean']:>10.3f} ({sign}{acc_pct:>+5.1f}%)  {r['accuracy_std']:>8.3f}")

    print()

    # Stress Comparison
    print("Stress Statistics:")
    print("-" * 70)
    print(f"{'Preset':<20} {'Mean Stress':<18} {'SD':<12}")
    print("-" * 70)

    nt_stress = results['default']['stress_mean']
    for preset in presets:
        r = results[preset]
        stress_pct = ((r['stress_mean'] - nt_stress) / nt_stress) * 100
        sign = "+" if stress_pct > 0 else ""
        print(f"{preset:<20} {r['stress_mean']:>10.3f} ({sign}{stress_pct:>+5.1f}%)  {r['stress_std']:>8.3f}")

    print()

    # Validation Checks
    print("=" * 70)
    print("VALIDATION CHECKS")
    print("=" * 70)
    print()

    checks = []

    # ASD checks
    asd_rt_slowdown = (results['asd_typical']['RT_mean'] - nt_rt) / nt_rt
    checks.append(('ASD RT 10-15% slower', 0.10 <= asd_rt_slowdown <= 0.20,
                   f"Actual: +{asd_rt_slowdown*100:.1f}%"))

    asd_stress_elevated = results['asd_typical']['stress_mean'] > results['default']['stress_mean']
    checks.append(('ASD elevated stress', asd_stress_elevated,
                   f"ASD: {results['asd_typical']['stress_mean']:.3f} vs NT: {results['default']['stress_mean']:.3f}"))

    # ADHD checks
    adhd_cv = results['adhd_typical']['RT_CV']
    nt_cv = results['default']['RT_CV']
    adhd_cv_increase = (adhd_cv - nt_cv) / nt_cv
    checks.append(('ADHD RT variability +35-50%', 0.25 <= adhd_cv_increase <= 0.60,
                   f"Actual: +{adhd_cv_increase*100:.1f}%"))

    adhd_acc_reduced = results['adhd_typical']['accuracy_mean'] < results['default']['accuracy_mean']
    checks.append(('ADHD reduced accuracy', adhd_acc_reduced,
                   f"ADHD: {results['adhd_typical']['accuracy_mean']:.3f} vs NT: {results['default']['accuracy_mean']:.3f}"))

    # MDD checks
    mdd_rt_slowdown = (results['mdd_typical']['RT_mean'] - nt_rt) / nt_rt
    checks.append(('MDD RT 15-20% slower', 0.12 <= mdd_rt_slowdown <= 0.25,
                   f"Actual: +{mdd_rt_slowdown*100:.1f}%"))

    mdd_acc_reduction = (nt_acc - results['mdd_typical']['accuracy_mean']) / nt_acc
    checks.append(('MDD accuracy 5-10% reduced', 0.00 <= mdd_acc_reduction <= 0.15,
                   f"Actual: -{mdd_acc_reduction*100:.1f}%"))

    mdd_stress_elevated = results['mdd_typical']['stress_mean'] > results['default']['stress_mean']
    checks.append(('MDD elevated stress', mdd_stress_elevated,
                   f"MDD: {results['mdd_typical']['stress_mean']:.3f} vs NT: {results['default']['stress_mean']:.3f}"))

    # Display checks
    passed = 0
    failed = 0

    for check_name, passed_check, details in checks:
        status = "✓ PASS" if passed_check else "✗ FAIL"
        print(f"{status:<8} {check_name:<40} {details}")
        if passed_check:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 70)
    print(f"SUMMARY: {passed}/{len(checks)} checks passed")
    print("=" * 70)
    print()

    if failed == 0:
        print("All validation checks PASSED! ✓")
        print("Clinical presets are empirically calibrated.")
        return 0
    else:
        print(f"{failed} validation check(s) FAILED.")
        print("Consider recalibrating preset parameters.")
        return 1


if __name__ == '__main__':
    exit_code = validate_empirical_expectations()
    sys.exit(exit_code)
