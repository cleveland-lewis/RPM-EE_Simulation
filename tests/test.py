#!/usr/bin/env python3
"""
test.py

Runner script to execute test_batch.py integration tests.
"""

import os
import sys
import subprocess

def main():
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    batch_test_path = os.path.join(script_dir, "test_batch.py")

    if not os.path.exists(batch_test_path):
        print(f"Error: test_batch.py not found at {batch_test_path}")
        sys.exit(1)

    # Run test_batch.py using the same Python interpreter
    result = subprocess.run([sys.executable, batch_test_path], check=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()