#!/usr/bin/env python3
"""
Test Clinical Presets for RPM-EE v1.1

This script demonstrates the clinical presets by running simulations
with different clinical profiles and comparing behavioral outputs.
"""

import sys
import os

# Add src to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import with absolute imports (modules will use relative imports internally)
import simulation
import presets
import numpy as np


def run_preset_test(preset_name, episodes=100):
    """Run simulation with specified preset and return metrics."""
    print(f"\n{'='*70}")
    print(f"Testing preset: {preset_name}")
    print(f"{'='*70}")
    print(presets.get_preset_description(preset_name))
    print()
    
    sim = simulation.RPMEESimulation(preset=preset_name)
    sim.run(episodes=episodes)
    
    # Extract metrics from logs
    logs = sim.logs
    
    metrics = {
        'preset': preset_name,
        'stress_mean': np.mean([log['schema_stress'] for log in logs]),
        'stress_std': np.std([log['schema_stress'] for log in logs]),
        'stress_final': logs[-1]['schema_stress'],
        'attunement_mean': np.mean([log['attunement_score'] for log in logs]),
        'attunement_std': np.std([log['attunement_score'] for log in logs]),
        'vigilance_mean': np.mean([log.get('vigilance', 0.85) for log in logs]),
        'vigilance_final': logs[-1].get('vigilance', 0.85),
        'num_simulations_mean': np.mean([log['num_simulations'] for log in logs]),
    }
    
    # Display metrics
    print(f"\nMetrics Summary:")
    print(f"  Stress (mean):      {metrics['stress_mean']:.3f} ± {metrics['stress_std']:.3f}")
    print(f"  Stress (final):     {metrics['stress_final']:.3f}")
    print(f"  Attunement (mean):  {metrics['attunement_mean']:.2f} ± {metrics['attunement_std']:.2f}")
    print(f"  Vigilance (mean):   {metrics['vigilance_mean']:.3f}")
    print(f"  Vigilance (final):  {metrics['vigilance_final']:.3f}")
    print(f"  Simulations/tick:   {metrics['num_simulations_mean']:.1f}")
    
    # Display preset parameters
    params = sim.params
    print(f"\nKey Clinical Parameters:")
    print(f"  WM Capacity:        {params['wm_capacity']:.1f} items")
    print(f"  Stress Baseline:    {params['stress_baseline']:.2f}")
    print(f"  Stress Reactivity:  {params['stress_reactivity']:.2f}")
    print(f"  Stress Recovery:    {params['stress_recovery']:.2f}")
    print(f"  Attention Stability:{params['attention_stability']:.2f}")
    print(f"  Exploration Rate:   {params['exploration_rate']:.2f}")
    
    return metrics


def compare_presets():
    """Compare all clinical presets."""
    print("\n" + "="*70)
    print("CLINICAL PRESETS COMPARISON TEST")
    print("="*70)
    
    presets_list = presets.list_presets()
    print(f"\nAvailable presets: {', '.join(presets_list)}")
    
    all_metrics = []
    for preset_name in presets_list:
        metrics = run_preset_test(preset_name, episodes=100)
        all_metrics.append(metrics)
    
    # Comparative summary
    print("\n" + "="*70)
    print("COMPARATIVE SUMMARY")
    print("="*70)
    print("\nStress Levels:")
    print(f"{'Preset':<20} {'Mean':<10} {'Final':<10} {'Recovery':<10}")
    print("-" * 50)
    for m in all_metrics:
        recovery = "Good" if m['stress_final'] < m['stress_mean'] else "Poor"
        print(f"{m['preset']:<20} {m['stress_mean']:<10.3f} {m['stress_final']:<10.3f} {recovery:<10}")
    
    print("\nVigilance/Attention:")
    print(f"{'Preset':<20} {'Mean':<10} {'Final':<10} {'Decrement':<10}")
    print("-" * 50)
    for m in all_metrics:
        decrement = m['vigilance_mean'] - m['vigilance_final']
        print(f"{m['preset']:<20} {m['vigilance_mean']:<10.3f} {m['vigilance_final']:<10.3f} {decrement:<10.3f}")
    
    print("\nAttunement (Social Prediction):")
    print(f"{'Preset':<20} {'Mean':<10} {'Std':<10}")
    print("-" * 50)
    for m in all_metrics:
        print(f"{m['preset']:<20} {m['attunement_mean']:<10.2f} {m['attunement_std']:<10.2f}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nExpected Differences:")
    print("  • ASD: Higher stress, slower stress recovery")
    print("  • ADHD: Lower vigilance final (steep decrement)")
    print("  • MDD: Highest stress, poorest recovery, lowest attunement")
    print("  • Neurotypical: Balanced metrics, good recovery")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test RPM-EE clinical presets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare all presets:
  python test_clinical_presets.py

  # Test specific preset:
  python test_clinical_presets.py --preset adhd_typical

  # Run longer simulation:
  python test_clinical_presets.py --preset mdd_typical --episodes 500
        """
    )
    parser.add_argument(
        '--preset',
        type=str,
        choices=presets.list_presets() + ['all'],
        default='all',
        help='Preset to test (default: all)'
    )
    parser.add_argument(
        '--episodes',
        type=int,
        default=100,
        help='Number of episodes to run (default: 100)'
    )
    
    args = parser.parse_args()
    
    if args.preset == 'all':
        compare_presets()
    else:
        run_preset_test(args.preset, episodes=args.episodes)
