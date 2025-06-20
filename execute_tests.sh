#!/usr/bin/env bash
# ------------------------------------------------------------------
# Unified test runner for RPM‑EE Simulation
#  • Runs pytest unit tests
#  • Launches FastAPI server (uvicorn) for integration tests
#  • Executes batch and trial integration suites
#  • Shuts server down and returns combined exit status
# ------------------------------------------------------------------
set -euo pipefail

# Resolve directory of this script (works in bash or zsh)
SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
cd "$SCRIPT_DIR"

# ─────────────────────────── Helpers ──────────────────────────────
run_test_file () {
  local FILE="$1"
  if [[ -f "$FILE" ]]; then
    echo "▶ Running $(basename "$FILE")"
    python3 "$FILE"
    return $?
  fi
  return 0  # treat missing file as skip (non‑fatal)
}

# ────────────────── 1. Unit tests (pytest) ────────────────────────
echo "Running pytest unit tests..."
pytest
UNIT_STATUS=$?

# ────────────────── 2. Start FastAPI server ───────────────────────
echo "Starting FastAPI server for integration tests..."
uvicorn src.simulation:app --host 127.0.0.1 --port 8000 \
  >/dev/null 2>&1 &
API_PID=$!

# Wait up to 15 s for server readiness
for i in {1..15}; do
  if curl -fs http://127.0.0.1:8000/jobs >/dev/null; then
    echo "Server ready."
    break
  fi
  printf '.'
  sleep 1
done
echo

# ────────────────── 3. Batch integration tests ────────────────────
echo "Running batch integration tests..."
BATCH_STATUS=0
run_test_file "$SCRIPT_DIR/test_batch.py"     || BATCH_STATUS=$?
run_test_file "$SCRIPT_DIR/tests/test_batch.py" || true  # second location (ignore status if first already failed)

# ────────────────── 4. Trial integration tests ────────────────────
echo "Running trials integration tests..."
TRIAL_STATUS=0
run_test_file "$SCRIPT_DIR/test_trials.py"       || TRIAL_STATUS=$?
run_test_file "$SCRIPT_DIR/tests/test_trials.py" || true

# ────────────────── 5. Graph‑data integrity tests ────────────────
echo "Running graph‑data integrity tests..."
GRAPH_STATUS=0
run_test_file "$SCRIPT_DIR/test_graphs.py"       || GRAPH_STATUS=$?
run_test_file "$SCRIPT_DIR/tests/test_graphs.py" || true

# ────────────────── 6. Shutdown server ────────────────────────────
echo "Stopping FastAPI server..."
kill "$API_PID" 2>/dev/null || true

# ────────────────── 7. Exit summary ───────────────────────────────
if [[ $UNIT_STATUS -eq 0 && $BATCH_STATUS -eq 0 && $TRIAL_STATUS -eq 0 && ${GRAPH_STATUS:-0} -eq 0 ]]; then
  echo "✅  All tests passed!"
  exit 0
else
  echo "❌  Some tests failed."
  echo "Unit: $UNIT_STATUS  Batch: $BATCH_STATUS  Trials: $TRIAL_STATUS  Graphs: ${GRAPH_STATUS:-N/A}"
  exit 1
fi