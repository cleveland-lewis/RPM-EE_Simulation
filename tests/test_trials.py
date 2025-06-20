

#!/usr/bin/env python3
"""
test_trials.py

Integration tests for the Trial Simulation FastAPI endpoint.
Requires the server running at http://127.0.0.1:8000.
"""

import time
import requests
import sys

API_BASE = "http://127.0.0.1:8000"

def run_trial(params):
    resp = requests.post(f"{API_BASE}/run", json=params)
    resp.raise_for_status()
    return resp.json()

def test_trial_complete():
    print("=== Testing Trial Simulation complete flow ===")
    # Minimal parameters: just episodes and repetitions
    params = {
        "episodes": 50,
        "repetitions": 1
    }
    result = run_trial(params)
    assert isinstance(result, dict), "Response not a JSON object"
    status = result.get("status")
    assert status == "complete", f"Expected status 'complete', got '{status}'"
    data = result.get("data")
    assert isinstance(data, list), "Expected 'data' field as list"
    # Check first replicate is a list of log entries
    assert len(data) > 0 and isinstance(data[0], list), "Expected nested list in 'data'"
    logs = data[0]
    # Each log entry should be a dict with required keys
    required_keys = {
        "clock", "attunement_score", "schema_stress",
        "avg_affect_feedback", "vision_count", "hearing_count",
        "touch_count", "smell_count", "taste_count",
        "short_term_count", "long_term_count",
        "memory_config", "memory_stats"
    }
    assert len(logs) > 0, "No log entries returned"
    first = logs[0]
    assert required_keys.issubset(first.keys()), f"Missing keys in log entry: {required_keys - set(first.keys())}"
    print("Trial complete flow test passed.\n")

def main():
    try:
        test_trial_complete()
        print("All trial tests passed!")
    except AssertionError as e:
        print("Trial test failed:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()