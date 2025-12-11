"""
Example usage of TrialSimulator for common experimental paradigms.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless backend
import matplotlib.pyplot as plt
from src.trial_wrapper import TrialSimulator, DualTaskSimulator


def example_1_single_trial():
    """Example 1: Run a single trial."""
    print("=" * 60)
    print("Example 1: Single Trial")
    print("=" * 60)

    sim = TrialSimulator(preset='default', seed=42)

    result = sim.run_trial(
        stimulus={'difficulty': 0.5},
        duration=200
    )

    print(f"RT: {result['RT']:.1f} ms")
    print(f"Accuracy: {result['accuracy']:.2f}")
    print(f"Mean Attunement: {result['attunement_mean']:.3f}")
    print(f"Mean Stress: {result['stress_mean']:.3f}")
    print(f"Dominant Mode: {result['dominant_mode']}")
    print()


def example_2_multiple_difficulties():
    """Example 2: Test across difficulty levels."""
    print("=" * 60)
    print("Example 2: Difficulty Manipulation")
    print("=" * 60)

    sim = TrialSimulator(preset='default', seed=42)
    difficulties = [0.2, 0.4, 0.6, 0.8]
    n_trials_per_level = 20

    results = []
    for diff in difficulties:
        for _ in range(n_trials_per_level):
            result = sim.run_trial(
                stimulus={'difficulty': diff},
                duration=200
            )
            results.append(result)

    # Analyze by difficulty
    for diff in difficulties:
        subset = [r for r in results if r['stimulus'].get('difficulty') == diff]
        mean_RT = np.mean([r['RT'] for r in subset])
        mean_acc = np.mean([r['accuracy'] for r in subset])

        print(f"Difficulty {diff:.1f}: RT={mean_RT:.1f}ms, Acc={mean_acc:.2f}")
    print()


def example_3_dual_task():
    """Example 3: Dual-task interference."""
    print("=" * 60)
    print("Example 3: Dual-Task Paradigm")
    print("=" * 60)

    sim = DualTaskSimulator(preset='default', seed=42)

    # Create 3x3 design
    trials = sim.create_trial_design(
        ext_load_levels=[0.3, 0.6, 0.9],
        mem_load_levels=[0.3, 0.6, 0.9],
        n_reps=5
    )

    print(f"Running {len(trials)} trials...")
    results = sim.run_experiment(trials, progress=False)

    # Analyze
    for ext in [0.3, 0.6, 0.9]:
        for mem in [0.3, 0.6, 0.9]:
            condition = f'ext{ext:.1f}_mem{mem:.1f}'
            subset = [r for r in results
                     if r['stimulus']['condition'] == condition]

            mean_RT = np.mean([r['RT'] for r in subset])
            mean_acc = np.mean([r['accuracy'] for r in subset])

            print(f"Ext={ext:.1f}, Mem={mem:.1f}: RT={mean_RT:.0f}ms, Acc={mean_acc:.2f}")
    print()


def example_4_clinical_comparison():
    """Example 4: Compare NT vs ASD vs ADHD."""
    print("=" * 60)
    print("Example 4: Clinical Group Comparison")
    print("=" * 60)

    presets = ['default', 'asd_typical', 'adhd_typical']
    n_trials = 30
    difficulty = 0.7  # Challenging condition

    for preset in presets:
        sim = TrialSimulator(preset=preset, seed=42)
        results = []

        for _ in range(n_trials):
            result = sim.run_trial(
                stimulus={'difficulty': difficulty},
                duration=200
            )
            results.append(result)

        mean_RT = np.mean([r['RT'] for r in results])
        std_RT = np.std([r['RT'] for r in results])
        mean_acc = np.mean([r['accuracy'] for r in results])

        print(f"{preset:15s}: RT={mean_RT:.0f}±{std_RT:.0f}ms, Acc={mean_acc:.2f}")
    print()


def example_5_visualization():
    """Example 5: Visualize RT distributions."""
    print("=" * 60)
    print("Example 5: RT Distribution Visualization")
    print("=" * 60)

    sim = TrialSimulator(preset='default', seed=42)

    # Run 100 trials at two difficulty levels
    easy_RTs = []
    hard_RTs = []

    for _ in range(100):
        easy = sim.run_trial(stimulus={'difficulty': 0.3}, duration=200)
        hard = sim.run_trial(stimulus={'difficulty': 0.8}, duration=200)
        easy_RTs.append(easy['RT'])
        hard_RTs.append(hard['RT'])

    # Plot
    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.hist(easy_RTs, bins=20, alpha=0.7, label='Easy (0.3)', color='blue')
    plt.hist(hard_RTs, bins=20, alpha=0.7, label='Hard (0.8)', color='red')
    plt.xlabel('Response Time (ms)')
    plt.ylabel('Frequency')
    plt.title('RT Distributions by Difficulty')
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.scatter(easy_RTs, [0.3]*len(easy_RTs), alpha=0.3, label='Easy')
    plt.scatter(hard_RTs, [0.8]*len(hard_RTs), alpha=0.3, label='Hard')
    plt.xlabel('Response Time (ms)')
    plt.ylabel('Difficulty')
    plt.title('RT vs Difficulty')
    plt.legend()

    plt.tight_layout()
    plt.savefig('trial_wrapper_example.png')
    print("Saved plot to 'trial_wrapper_example.png'")
    plt.close()
    print()


if __name__ == '__main__':
    example_1_single_trial()
    example_2_multiple_difficulties()
    example_3_dual_task()
    example_4_clinical_comparison()
    example_5_visualization()

    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
