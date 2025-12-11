#!/usr/bin/env bash
set -euo pipefail

# Directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Utility to run pytest on a given file and capture status
run_test_file() {
  pytest "$1" -q
  return $?
}

# Initialize status codes
UNIT_STATUS=0
BATCH_STATUS=0
TRIAL_STATUS=0
GRAPH_STATUS=0

# 1. Unit tests
echo "=== Running unit tests ==="
run_test_file "$SCRIPT_DIR/tests/test_simulation.py" || UNIT_STATUS=$?

# 2. Batch integration tests
echo "=== Running batch integration tests ==="
run_test_file "$SCRIPT_DIR/tests/test_batch.py" || BATCH_STATUS=$?

# 4. Trial simulation tests
echo "=== Running trial simulation tests ==="
run_test_file "$SCRIPT_DIR/tests/test_trials.py" || TRIAL_STATUS=$?

# 5. Graph generation tests (if present)
GRAPH_FILE="$SCRIPT_DIR/tests/test_graphs.py"
if [[ -f "$GRAPH_FILE" ]]; then
  echo "=== Running Graph Tests ==="
  run_test_file "$GRAPH_FILE" || GRAPH_STATUS=$?
else
  echo "=== Skipping graph tests: no test_graphs.py found ==="
fi

# Summary
echo "=== Test summary ==="
echo "Unit Tests:       $UNIT_STATUS"
echo "Batch Tests:      $BATCH_STATUS"
echo "Trial Tests:      $TRIAL_STATUS"
echo "Graph Tests:      $GRAPH_STATUS"

# Exit overall status
if [[ $UNIT_STATUS -eq 0 && $BATCH_STATUS -eq 0 && $TRIAL_STATUS -eq 0 && $GRAPH_STATUS -eq 0 ]]; then
  echo "All tests passed!"
  exit 0
else
  echo "Some tests failed."
  exit 1
fi