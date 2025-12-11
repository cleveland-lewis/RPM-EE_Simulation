#!/usr/bin/env python3
"""
test_batch.py

Integration tests for the Batch Simulation FastAPI endpoints.
By default these are skipped; set RPMEE_API_BASE to enable.
"""

import os
import time
import requests
import sys
from requests.exceptions import ReadTimeout

API_BASE = os.environ.get("RPMEE_API_BASE", "http://*********:8000")

# Skip in normal unit-test runs unless an explicit API base is provided
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RPMEE_API_BASE"),
    reason="External FastAPI batch server not configured (set RPMEE_API_BASE to run these tests).",
)

def start_batch(agents):
    resp = requests.post(f"{API_BASE}/batch-job", json={"agents": agents}, timeout=10)
    resp.raise_for_status()
    job_id = resp.json().get("job_id")
    print(f"Started batch job: {job_id}")
    return job_id

def poll_status(job_id, timeout=10, interval=0.5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(f"{API_BASE}/job-status/{job_id}", timeout=5)
        except ReadTimeout:
            print(f"[{job_id}] status request timed out, retrying...")
            time.sleep(interval)
            continue
        if resp.status_code != 200:
            print(f"Status fetch failed: HTTP {resp.status_code}")
            break
        data = resp.json()
        status = data.get("status")
        print(f"[{job_id}] status: {status}")
        if status in ("complete", "cancelled", "error"):
            return data
        time.sleep(interval)
    raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

def fetch_result(job_id):
    resp = requests.get(f"{API_BASE}/job-result/{job_id}", timeout=5)
    resp.raise_for_status()
    data = resp.json()
    print(f"[{job_id}] result status: {data.get('status')}")
    return data

def cancel_batch(job_id):
    resp = requests.post(f"{API_BASE}/job-action/{job_id}", json={"action": "cancel"}, timeout=5)
    resp.raise_for_status()
    print(f"Cancelled batch job: {job_id}")

def test_complete_flow():
    print("=== Testing complete batch flow ===")
    agents = [{"episodes": 10, "repetitions": 1}]
    job_id = start_batch(agents)
    status_data = poll_status(job_id, timeout=10)
    assert status_data["status"] == "complete", f"Expected complete, got {status_data['status']}"
    result = fetch_result(job_id)
    assert result["status"] == "complete", "Result status not complete"
    assert "results_trials" in result and isinstance(result["results_trials"], list), "Invalid result payload"
    print("Complete flow test passed.\n")

def test_cancel_flow():
    print("=== Testing cancel batch flow ===")
    agents = [{"episodes": 100, "repetitions": 1}]
    job_id = start_batch(agents)
    # give the job a moment to start
    time.sleep(0.5)
    cancel_batch(job_id)
    status_data = poll_status(job_id, timeout=10)
    assert status_data["status"] == "cancelled", f"Expected cancelled, got {status_data['status']}"
    # /current-jobs should not list this job
    resp = requests.get(f"{API_BASE}/current-jobs", timeout=5)
    resp.raise_for_status()
    current = [j["job_id"] for j in resp.json()]
    assert job_id not in current, "Cancelled job still in current-jobs list"
    print("Cancel flow test passed.\n")

def main():
    try:
        test_complete_flow()
        test_cancel_flow()
        print("All tests passed!")
    except Exception as e:
        print("Test failed:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()