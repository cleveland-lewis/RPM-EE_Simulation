#!/usr/bin/env bash
#
# run_test.sh
#
# Self-contained script to run random simulations via embedded Python.
#
# Usage: ./run_test.sh [num_tests]
# Default num_tests=5

NUM_TESTS=${1:-5}

python3 - << 'PYCODE'
import random
import numpy as np
from src.simulation import run_simulation
import sys

def random_test():
    params = {
        'total_ticks': random.choice([2000, 5000, 10000]),
        'salience_decay': random.uniform(0.0, 0.1),
        'highly_variable_rate': random.uniform(0.0, 0.2),
        'event_rate': random.randint(1, 5),
        'memory_buffer_size': random.randint(100, 1000),
        'memory_decay': random.uniform(0.0, 0.1),
        'memory_prune_threshold': random.uniform(0.0, 1.0),
        'low_salience_var_rate': random.uniform(0.0, 0.2),
    }
    logs = run_simulation(
        total_ticks=params['total_ticks'],
        salience_decay=params['salience_decay'],
        highly_variable_rate=params['highly_variable_rate'],
        event_rate=params['event_rate'],
        memory_buffer_size=params['memory_buffer_size'],
        memory_decay=params['memory_decay'],
        memory_prune_threshold=params['memory_prune_threshold'],
        low_salience_var_rate=params['low_salience_var_rate']
    )
    att = [entry.get('attunement_score', 0.0) for entry in logs]
    stress = [entry.get('schema_stress', 0.0) for entry in logs]
    return params, float(np.mean(att)), float(np.mean(stress))

def main(num_tests=5):
    print(f"Running {num_tests} random simulation tests...\n")
    all_atts, all_stresses, results = [], [], []
    for i in range(1, num_tests + 1):
        try:
            params, avg_att, avg_str = random_test()
            all_atts.append(avg_att)
            all_stresses.append(avg_str)
            results.append({'params': params, 'avg_att': avg_att, 'avg_str': avg_str, 'success': True})
            print(f"Test {i}:")
            for k, v in params.items():
                print(f"  {k}: {v}")
            print(f"  => Average attunement: {avg_att:.4f}")
            print(f"  => Average stress   : {avg_str:.4f}\n")
        except Exception as e:
            results.append({'success': False, 'error': str(e)})
            print(f"Test {i} ERROR: {e}\n")

    total = len(results)
    successes = sum(1 for r in results if r.get('success'))
    failures = total - successes
    print("Summary:")
    print(f"  Total tests run       : {total}")
    print(f"  Successful tests      : {successes}")
    print(f"  Failed tests          : {failures}")
    if successes:
        overall_att = float(np.mean(all_atts))
        overall_str = float(np.mean(all_stresses))
        att_std = float(np.std(all_atts))
        str_std = float(np.std(all_stresses))
        att_min, att_max = float(np.min(all_atts)), float(np.max(all_atts))
        str_min, str_max = float(np.min(all_stresses)), float(np.max(all_stresses))
        att_p5, att_p95 = float(np.percentile(all_atts, 5)), float(np.percentile(all_atts, 95))
        str_p5, str_p95 = float(np.percentile(all_stresses, 5)), float(np.percentile(all_stresses, 95))
        print(f"  Overall avg attunement: {overall_att:.4f} (std: {att_std:.4f}, min: {att_min:.4f}, max: {att_max:.4f}, 5th: {att_p5:.4f}, 95th: {att_p95:.4f})")
        print(f"  Overall avg stress    : {overall_str:.4f} (std: {str_std:.4f}, min: {str_min:.4f}, max: {str_max:.4f}, 5th: {str_p5:.4f}, 95th: {str_p95:.4f})")
        print("  Parameters of successful tests:")
        for idx, r in enumerate(results, start=1):
            if r.get('success'):
                print(f"    Test {idx}: {r['params']}")

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    main(n)
PYCODE