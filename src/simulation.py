
# -----------------------------------------------------------------------------
# Standard library imports:
#   - os, sys, time, uuid, random: file operations, system functions, timing, and unique IDs
#   - threading, multiprocessing: concurrency support for parallel simulations
#   - json, glob, datetime, typing: data serialization, file pattern matching, date/time handling, and type annotations
# -----------------------------------------------------------------------------
import os
#
import time
import uuid
import random
#
import multiprocessing
import json
import glob
from datetime import datetime
from typing import Any

# -----------------------------------------------------------------------------
# Third-party library imports:
#   - numpy: core array operations and numerical computing
#   - jax / jax.numpy: accelerated computations on CPU/GPU/TPU with JIT support
#   - numba: optional JIT compilation for CPU performance
#   - fastapi, pydantic: building and validating web API endpoints
#   - filelock, datashader, pandas, colorcet: file locking, data visualization, data handling, and color palettes
# -----------------------------------------------------------------------------
import numpy as np
try:
    import jax
    import jax.numpy as jnp
    from jax import random as jax_random
    USE_JAX = True
except ImportError:
    USE_JAX = False
try:
    import numba as nb
    HAVE_NUMBA = True
except ModuleNotFoundError:
    HAVE_NUMBA = False

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from filelock import FileLock
#

# -----------------------------------------------------------------------------
# Project-specific imports:
#   - SensoryInputSystem: core simulation engine for generating sensory and memory events
#   - config: load/save configuration utilities for simulation parameters
# -----------------------------------------------------------------------------
from src.sensory import SensoryInputSystem
#

JOBS_DIR = "jobs"  # --- Directory for persistent job files ---
os.makedirs(JOBS_DIR, exist_ok=True)  # Ensure jobs dir exists
# Directory for current jobs (active/running/paused jobs)
CURRENT_JOBS_DIR = "current_jobs"
os.makedirs(CURRENT_JOBS_DIR, exist_ok=True)

def downsample_logs(logs, bin_size):
    """Downsample logs by averaging over bins of bin_size for selected keys."""
    if bin_size <= 1 or len(logs) <= 1:
        return logs
    keys_to_avg = ['attunement_score', 'schema_stress', 'avg_affect_feedback']
    # All keys to keep (fill with last value in bin)
    keep_keys = set(logs[0].keys())
    result = []
    n = len(logs)
    for i in range(0, n, bin_size):
        bin_logs = logs[i : i + bin_size]
        avg_entry = {}
        for k in keep_keys:
            if k in keys_to_avg:
                # Compute mean, ignoring None and -999
                vals = [entry.get(k) for entry in bin_logs if entry.get(k) not in (None, -999)]
                avg_entry[k] = float(np.mean(vals)) if vals else -999
            else:
                # Use last value in bin for other keys
                avg_entry[k] = bin_logs[-1].get(k)
        result.append(avg_entry)
    return result

 # -----------------------------------------------------------------------------
# MAX_PLOT_POINTS:
#   Limit the number of data points sent to the front end to avoid browser performance issues
# -----------------------------------------------------------------------------
MAX_PLOT_POINTS = 1500

# -----------------------------------------------------------------------------
# Math module import:
#   Provides functions like ceil() used in log thinning calculations
# -----------------------------------------------------------------------------
import math  # needed for ceil

 # -----------------------------------------------------------------------------
# JAX backend self-test:
#   Verify that JAX can allocate arrays and perform a simple reduction on the selected device
# -----------------------------------------------------------------------------
if USE_JAX:
    try:
        # Quick test: sum of arange(100)
        arr = jnp.arange(100)
        s = int(jnp.sum(arr).item())  # expected 4950
        dev = jax.devices()[0]
        print(f"[JAX TEST] JAX on device {dev} OK (sum={s})")
    except Exception as e:
        print(f"[JAX TEST] ERROR initializing JAX backend: {e}. Disabling JAX path.")
        USE_JAX = False
# ───────────────────────────────────────────────────

# -----------------------------------------------------------------------------
# Numba JIT warm-up:
#   Compile the Numba-accelerated array generator once on import to eliminate first-run latency
# -----------------------------------------------------------------------------
if HAVE_NUMBA:
    @nb.njit
    def _generate_base_arrays_numba(total_ticks: int):
        """
        Numba‐accelerated generator for per‑tick arrays.
        Returns the same tuple as _generate_base_arrays.
        """
        att    = np.random.rand(total_ticks).astype(np.float32)
        stress = np.random.rand(total_ticks).astype(np.float32)
        affect = (np.random.rand(total_ticks) * 2 - 1).astype(np.float32)

        vis = np.random.randint(0, 4, total_ticks).astype(np.int16)
        hear = np.random.randint(0, 3, total_ticks).astype(np.int16)
        touch = np.random.randint(0, 2, total_ticks).astype(np.int16)
        smell = np.zeros(total_ticks, dtype=np.int16)
        taste = np.zeros(total_ticks, dtype=np.int16)

        ticks = np.arange(total_ticks, dtype=np.int32)
        st_sz = np.maximum(0, 500 - (ticks % 500)).astype(np.int32)
        lt_sz = (ticks // 1000).astype(np.int32)

        return (att, stress, affect,
                vis, hear, touch, smell, taste,
                st_sz, lt_sz)
    _ = _generate_base_arrays_numba(1)

# -----------------------------------------------------------------------------
# JAX_TICK_THRESHOLD:
#   Minimum number of ticks before switching to JAX acceleration to offset JIT overhead
# -----------------------------------------------------------------------------
JAX_TICK_THRESHOLD = 1_000_000

# -----------------------------------------------------------------------------
# JAX-accelerated base array generator:
#   Uses jax.random to create parallel arrays of sensory and size data on the accelerator
# -----------------------------------------------------------------------------
def _generate_base_arrays_jax(total_ticks: int):
    """
    JAX-accelerated generator for per-tick arrays.
    Returns same tuple as _generate_base_arrays.
    """
    key = jax_random.PRNGKey(0)
    k1, k2, k3, k4, k5, k6, k7 = jax_random.split(key, 7)
    att = jax_random.uniform(k1, (total_ticks,), dtype=jnp.float32)
    stress = jax_random.uniform(k2, (total_ticks,), dtype=jnp.float32)
    affect = (jax_random.uniform(k3, (total_ticks,), dtype=jnp.float32) * 2 - 1).astype(jnp.float32)
    vis = jax_random.randint(k4, (total_ticks,), 0, 4, dtype=jnp.int16)
    hear = jax_random.randint(k5, (total_ticks,), 0, 3, dtype=jnp.int16)
    touch = jax_random.randint(k6, (total_ticks,), 0, 2, dtype=jnp.int16)
    smell = jnp.zeros((total_ticks,), dtype=jnp.int16)
    taste = jnp.zeros((total_ticks,), dtype=jnp.int16)
    ticks = jnp.arange(total_ticks, dtype=jnp.int32)
    st_sz = jnp.maximum(0, 500 - (ticks % 500)).astype(jnp.int32)
    lt_sz = (ticks // 1000).astype(jnp.int32)
    # Convert back to NumPy
    return (np.array(att), np.array(stress), np.array(affect),
            np.array(vis), np.array(hear), np.array(touch),
            np.array(smell), np.array(taste),
            np.array(st_sz), np.array(lt_sz))

# -----------------------------------------------------------------------------
# Apply JAX JIT compilation:
#   Transform the JAX generator into an optimized, fused function for repeated calls
# -----------------------------------------------------------------------------
if 'USE_JAX' in globals() and USE_JAX:
    _generate_base_arrays_jax = jax.jit(_generate_base_arrays_jax)

 # -----------------------------------------------------------------------------
# VECTORISED FAST-PATH (_generate_base_arrays):
#   Single-shot NumPy implementation for generating random inputs when JAX/Numba
#   are not used or for smaller simulations, enabling efficient CPU execution.
# -----------------------------------------------------------------------------
def _generate_base_arrays(total_ticks: int):
    """
    Return tuple of NumPy arrays:
      att, stress, affect,
      vis, hear, touch, smell, taste,
      st_sz, lt_sz
    Arrays dtypes are chosen for compactness (float32 / int16 / int32).
    NOTE: In this first step we only create the function; run_simulation
    continues to use the existing logic until step 3.
    """

    # Use JAX path for large tick counts when acceleration is enabled
    if 'USE_JAX' in globals() and USE_JAX and total_ticks >= JAX_TICK_THRESHOLD:
        return _generate_base_arrays_jax(total_ticks)

    global HAVE_NUMBA
    # Numba path disabled due to unreliable random output; using NumPy fallback directly
    if False and HAVE_NUMBA:
        try:
            return _generate_base_arrays_numba(total_ticks)
        except Exception:
            # Disable Numba for future calls if compilation/runtime fails
            HAVE_NUMBA = False
            # Fall through to NumPy fallback
    att    = np.random.rand(total_ticks).astype(np.float32)
    stress = np.random.rand(total_ticks).astype(np.float32)
    affect = (np.random.rand(total_ticks) * 2 - 1).astype(np.float32)

    vis   = np.random.randint(0, 4, total_ticks, dtype=np.int16)
    hear  = np.random.randint(0, 3, total_ticks, dtype=np.int16)
    touch = np.random.randint(0, 2, total_ticks, dtype=np.int16)
    smell = np.zeros(total_ticks, dtype=np.int16)
    taste = np.zeros(total_ticks, dtype=np.int16)

    ticks = np.arange(total_ticks)
    st_sz = np.maximum(0, 500 - (ticks % 500)).astype(np.int32)
    lt_sz = (ticks // 1000).astype(np.int32)

    return (att, stress, affect,
            vis, hear, touch, smell, taste,
            st_sz, lt_sz)

# -----------------------------------------------------------------------------
# Log thinning helper (_thin_logs):
#   Uniformly sample log entries to limit output size for front-end visualization
# -----------------------------------------------------------------------------
def _thin_logs(logs, max_points: int = MAX_PLOT_POINTS):
    """
    Down‑sample a list of per‑tick dicts so the client never receives more
    than `max_points` entries. Keeps every ⌈len(logs)/max_points⌉‑th sample
    and always includes the final entry.
    """
    n = len(logs)
    if n <= max_points or max_points <= 0:
        return logs
    step = math.ceil(n / max_points)
    thinned = logs[::step]
    if thinned[-1] is not logs[-1]:
        thinned.append(logs[-1])  # ensure last point present
    return thinned
# -----------------------------------------------------------------------------
# flatten_dict utility:
#   Recursively flatten nested dictionaries into flat key-value pairs
#   for CSV or tabular export formats
# -----------------------------------------------------------------------------
def flatten_dict(d, parent_key='', sep='.'):
    """Recursively flatten a nested dictionary (for CSV)."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# -----------------------------------------------------------------------------
# SIMULATION CORE (run_simulation):
#   Orchestrates a full simulation run including:
#     - Initialization of memory thresholds and sensory system
#     - Generation of random inputs via JAX/NumPy/Numba
#     - Per-tick processing for attunement, stress, and affect feedback
#     - Batching and aggregation of results for front-end consumption
#   Accepts parameters for decay rates, event frequencies, and memory settings.
# -----------------------------------------------------------------------------
def run_simulation(
    total_ticks: int = 2400,
    salience_decay: float = 0.01,
    highly_variable_rate: float = 0.1,
    event_rate: int = 3,  # wired from popup
    memory_buffer_size: int = 1000,
    memory_decay: float = 0.01,
    memory_prune_threshold: float = 0.2,
    low_salience_var_rate: float = 0.1,
    bin_size: int = 1,
) -> list:
    """
    The main simulation function.
    Simulates a sequence of sensory events and memory state over time.
    Parameters:
      total_ticks: Number of simulation time steps (episodes)
      salience_decay: Rate at which salience decays in memory
      highly_variable_rate: Controls frequency of highly variable sensory events
      event_rate: Controls frequency of events per tick
    Returns a list of dicts, each representing the state/log at a time tick.
        The returned log list is automatically thinned to ≤ MAX_PLOT_POINTS (1500)
        to keep browser rendering fast.
    """
    start = time.perf_counter()
    # Randomize initial thresholds for this simulation run
    base_low = random.uniform(0.3, 0.7)
    base_high = random.uniform(0.7, 0.95)
    # The following parameters should be integrated into your simulation logic as needed:
    # memory_buffer_size, memory_decay, memory_prune_threshold, low_salience_var_rate
    # For now, these are received and can be logged or passed to SensoryInputSystem
    # Create the sensory input system with randomized thresholds and config
    # event_rate is not a parameter of run_simulation, but if you want to integrate from config/UI, you may need to pass it in.
    # For now, try to get event_rate from the caller's context or set a default.
    event_rate = locals().get('event_rate', 3)  # fallback to 3 if not present
    sim = SensoryInputSystem(
        low_salience_threshold=base_low,
        high_salience_threshold=base_high,
        salience_decay=salience_decay,
        highly_variable_rate=highly_variable_rate,
        low_salience_var_rate=low_salience_var_rate,
        event_rate=event_rate,
        memory_buffer_size=memory_buffer_size,
        memory_decay=memory_decay,
        memory_prune_threshold=memory_prune_threshold
    )
    # Use memory state to compute attunement, stress, affect feedback
    attunement_scores = np.zeros(total_ticks, dtype=np.float32)
    schema_stress = np.zeros(total_ticks, dtype=np.float32)
    avg_affect_feedback = np.zeros(total_ticks, dtype=np.float32)
    # logs = []  # Removed: replaced by structured array buffer
    tick_time_sum = 0.0
    tick_time_count = 0

    # --- Structured array buffer for results (object dtype for dict fields) ---
    n_bins = (total_ticks + bin_size - 1) // bin_size
    # Structured buffer for results (object dtype for dict fields)
    dtype = [
        ('clock', 'i4'),
        ('attunement_score', 'f4'),
        ('schema_stress', 'f4'),
        ('avg_affect_feedback', 'f4'),
        ('vision_count', 'i4'),
        ('hearing_count', 'i4'),
        ('touch_count', 'i4'),
        ('smell_count', 'i4'),
        ('taste_count', 'i4'),
        ('short_term_count', 'i4'),
        ('long_term_count', 'i4'),
        ('memory_config', 'O'),
        ('memory_stats', 'O'),
    ]
    out = np.zeros(n_bins, dtype=dtype)

    # ---------- Step 3: Full vectorised generation & aggregation ----------
    # Generate base arrays in one shot
    att_arr, stress_arr, affect_arr, vis, hear, touch, smell, taste, st_sz, lt_sz = _generate_base_arrays(total_ticks)
    # DEBUG: print range of generated stress array to verify non-zero values
    print(f"[DEBUG] stress_arr range: min={stress_arr.min():.4f}, max={stress_arr.max():.4f}")

    # --- Compute attunement_scores, schema_stress, avg_affect_feedback using SensoryInputSystem ---
    for i in range(total_ticks):
        tick_result = sim.tick()
        if not isinstance(tick_result, dict):
            raise ValueError(f"Expected dict from sim.tick(), got {type(tick_result)}")
        try:
            attunement_scores[i] = float(tick_result["attunement_score"])
            # Option A: inflate short‑term stress by current random stress input
            kappa = 1.0  # weight of external stress on perceived short‑term load....higher equals stronger coupling of random stress to short-term load
            raw_st_sz = int(tick_result["short_term_size"])
            effective_st_sz = raw_st_sz + kappa * stress_arr[i] * memory_buffer_size
            schema_stress[i] = float(np.clip(effective_st_sz / memory_buffer_size, 0.0, 1.0))
            avg_affect_feedback[i] = float(tick_result["avg_affect_feedback"])
        except KeyError as e:
            raise KeyError(f"Missing key in tick_result: {e}")

    # Pad arrays so total_ticks is divisible by bin_size
    pad = (-total_ticks) % bin_size
    if pad:
        pad_kwargs = {'constant_values': 0}
        att_arr     = np.pad(att_arr,     (0, pad), **pad_kwargs)
        stress_arr  = np.pad(stress_arr,  (0, pad), **pad_kwargs)
        affect_arr  = np.pad(affect_arr,  (0, pad), **pad_kwargs)
        vis         = np.pad(vis,         (0, pad), **pad_kwargs)
        hear        = np.pad(hear,        (0, pad), **pad_kwargs)
        touch       = np.pad(touch,       (0, pad), **pad_kwargs)
        smell       = np.pad(smell,       (0, pad), **pad_kwargs)
        taste       = np.pad(taste,       (0, pad), **pad_kwargs)
        st_sz       = np.pad(st_sz,       (0, pad), **pad_kwargs)
        lt_sz       = np.pad(lt_sz,       (0, pad), **pad_kwargs)

    # Compute number of bins after padding
    n_effective = total_ticks + pad
    n_bins = n_effective // bin_size

    # Helper to reshape and mean
    def bin_mean(arr):
        return arr.reshape(n_bins, bin_size).mean(axis=1)

    # Aggregate numeric metrics
    att_b    = bin_mean(attunement_scores)
    stress_b = bin_mean(schema_stress)
    affect_b = bin_mean(avg_affect_feedback)
    vc_b     = bin_mean(vis).astype(int)
    hc_b     = bin_mean(hear).astype(int)
    tc_b     = bin_mean(touch).astype(int)
    sc_b     = bin_mean(smell).astype(int)
    tc2_b    = bin_mean(taste).astype(int)
    st_b     = st_sz.reshape(n_bins, bin_size)[:, -1].astype(int)
    lt_b     = lt_sz.reshape(n_bins, bin_size)[:, -1].astype(int)
    clock_b  = (np.arange(n_bins) + 1) * bin_size - 1

    # Prepare memory_config once
    mem_cfg = {
        'low_salience_threshold': base_low,
        'high_salience_threshold': base_high,
        'salience_decay': salience_decay,
        'highly_variable_rate': highly_variable_rate,
        'event_rate': event_rate,
    }

    # Build memory_stats array
    mem_stats = [
        {'short_term_size': int(st_b[i]),
         'long_term_size': int(lt_b[i]),
         'tick': int(clock_b[i])}
        for i in range(n_bins)
    ]

    # Fill structured buffer
    out['clock']               = clock_b
    out['attunement_score']    = att_b.astype(np.float32)
    out['schema_stress']       = stress_b.astype(np.float32)
    out['avg_affect_feedback'] = affect_b.astype(np.float32)
    out['vision_count']        = vc_b
    out['hearing_count']       = hc_b
    out['touch_count']         = tc_b
    out['smell_count']         = sc_b
    out['taste_count']         = tc2_b
    out['short_term_count']    = st_b
    out['long_term_count']     = lt_b
    out['memory_config']       = np.empty(n_bins, dtype=object)
    out['memory_config'][:]    = mem_cfg
    out['memory_stats']        = np.array(mem_stats, dtype=object)

    if tick_time_count > 0:
        avg_tick = tick_time_sum / tick_time_count
        print(f"[PROFILE] FINAL: Avg tick duration for last {tick_time_count} ticks: {avg_tick:.6f} seconds")
    end = time.perf_counter()
    print(f"[PROFILE] Total simulation run time: {end - start:.3f} seconds for {total_ticks} episodes")

    # Convert structured array to list of dicts with native Python types
    logs = []
    for i in range(len(out)):
        entry = {}
        for name in out.dtype.names:
            val = out[i][name]
            # Cast NumPy scalar to Python native
            if isinstance(val, np.generic):
                val = val.item()
            entry[name] = val
        logs.append(entry)
    # Down‑sample for the frontend if needed
    logs = _thin_logs(logs, MAX_PLOT_POINTS)
    return logs
# -------------------------------------------------
# --------------------
# FASTAPI SETUP
# --------------------
# Set up FastAPI app to provide simulation API endpoints.

# Ensure saved_logs folder exists for raw JSON dumps
SAVED_LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'saved_logs')
os.makedirs(SAVED_LOGS_DIR, exist_ok=True)

app = FastAPI()

# Serve local Chart.js and other static assets
app.mount("/js", StaticFiles(directory="js"), name="js")

# Allow cross-origin requests for all domains and methods (dev use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# --------------------
# Saving as .JSON file
# Endpoint to save simulation logs as a JSON file on the server.
# --------------------
class LogSaveRequest(BaseModel):
    logs: list

@app.post("/save-logs")
async def save_logs(payload: LogSaveRequest):
    # Save full payload JSON to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_ts = timestamp  # already safe format
    filename = f"log_{safe_ts}.json"
    filepath = os.path.join(SAVED_LOGS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(payload.dict(), f, indent=2)
    return {"status": "success", "filename": filepath}


# --------------------
# List all saved logs endpoint
# --------------------
@app.get("/save-logs")
async def list_saved_logs():
    """
    Return a JSON array of all saved log payloads.
    """
    logs = []
    for fname in sorted(os.listdir(SAVED_LOGS_DIR)):
        if fname.endswith(".json"):
            path = os.path.join(SAVED_LOGS_DIR, fname)
            try:
                with open(path, "r") as f:
                    logs.append(json.load(f))
            except Exception:
                continue
    return logs


# --------------------
# List all jobs endpoint
# --------------------
@app.get("/jobs")
async def list_jobs():
    """
    Return a list of current batch jobs stored in JOBS_DIR.
    Each job is a JSON file containing job_id, status, progress, and summary.
    """
    jobs = []
    for filename in os.listdir(JOBS_DIR):
        filepath = os.path.join(JOBS_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                job_data = json.load(f)
            jobs.append(job_data)
        except Exception as e:
            # Skip invalid files
            continue
    return jobs

# Serve main HTML page (e.g., /src/trials.html) for browser access
@app.get("/", include_in_schema=False)
@app.get("/batch.html", include_in_schema=False)
async def serve_batch():
    html_path = os.path.join(os.path.dirname(__file__), "batch.html")
    try:
        with open(html_path, "r") as f:
            html = f.read()
    except FileNotFoundError:
        return HTMLResponse(status_code=404, content="batch.html not found")
    # ensure the debug-panel div is present
    if '<div id="debug-panel"></div>' not in html and "</body>" in html:
        html = html.replace("</body>", "\n<div id=\"debug-panel\"></div>\n</body>")
    return HTMLResponse(content=html, media_type="text/html")    # Inject loading spinner/message for config modal if not present
    # This is a simple string replace for demonstration; in production, use a template engine.
    if "</body>" in html:
        loading_span = '<span id="configLoading" style="color:#555; margin-bottom:8px; display:none;">Loading config...</span>\n'
        # Try to inject just before modal close, if present
        if 'id="configModal"' in html and 'id="saveBtn"' in html:
            # Insert after configModal open div or before saveBtn
            import re
            # Try to insert after the first <div ... id="configModal"...>
            html = re.sub(r'(<div[^>]*id="configModal"[^>]*>)', r'\1\n' + loading_span, html, count=1)
        else:
            html = html.replace("</body>", loading_span + "</body>")
    # Inject debug panel div near the end of the body if not present
    if '<div id="debug-panel"></div>' not in html:
        if "</body>" in html:
            debug_panel_div = '\n<div id="debug-panel"></div>\n'
            html = html.replace("</body>", debug_panel_div + "</body>")
    # Inject CSS for debug panel and dev-mode if not present
    if "<style>" not in html or "#debug-panel" not in html:
        style_block = """
<style>
body.dev-mode #debug-panel {
  display: block !important;
  background-color: #111;
  color: #0f0;
  font-weight: bold;
  padding: 1rem;
  max-height: 200px;
  overflow-y: auto;
  border: 2px solid #0f0;
}
#debug-panel {
  display: none;
}
</style>
"""
        if "</head>" in html:
            html = html.replace("</head>", style_block + "</head>")
        else:
            # If no head tag, prepend style at start
            html = style_block + html
    # Inject JavaScript functions debugLog and toggleDevMode if not present
    if "function debugLog" not in html or "function toggleDevMode" not in html:
        js_block = """
<script>
function debugLog(msg) {
  const debugPanel = document.getElementById("debug-panel");
  if (debugPanel) {
    debugPanel.textContent += msg + "\\n";
  }
}
function toggleDevMode() {
  document.body.classList.toggle('dev-mode');
  const debugPanel = document.getElementById('debug-panel');
  if (debugPanel) {
    debugPanel.style.display = document.body.classList.contains('dev-mode') ? 'block' : 'none';
  }
}
</script>
"""
        if "</body>" in html:
            html = html.replace("</body>", js_block + "</body>")
        else:
            html += js_block
    return HTMLResponse(content=html, media_type="text/html")

# --------------------
# Input validation model for simulation runs
# Used for validating and parsing input to the /run API endpoint.
# --------------------
class RunParams(BaseModel):
    episodes: int
    repetitions: int
    salience_decay: float = 0.01
    event_rate: int = 3
    memory_buffer_size: int = 1000
    memory_decay: float = 0.01
    memory_prune_threshold: float = 0.2
    high_salience_var_rate: float = 0.1
    low_salience_var_rate: float = 0.1

    class Config:
        extra = "allow"

import traceback

# --------------------
# Persistent File-based Job System for Batch Agent Simulations
# --------------------

# --- Helper functions for job state persistence ---
def save_job_state(job_id: str, state: dict):
    """Save the job state to disk (jobs/{job_id}.json),
    and also mirror to current_batches if running/paused, using atomic writes."""
    path = os.path.join(JOBS_DIR, f"{job_id}.json")
    lock = FileLock(path + ".lock")

    with lock:
        temp_path = path + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(state, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)

        # Mirror to CURRENT_JOBS_DIR atomically
        current_path = os.path.join(CURRENT_JOBS_DIR, f"{job_id}.json")
        temp_current = current_path + ".tmp"
        with open(temp_current, "w") as cf:
            json.dump(state, cf, indent=2)
            cf.flush()
            os.fsync(cf.fileno())
        os.replace(temp_current, current_path)

def load_job_state(job_id: str) -> dict:
    """Load the job state from disk with a shared lock."""
    path = os.path.join(JOBS_DIR, f"{job_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Job {job_id} not found")

    lock = FileLock(path + ".lock")
    with lock:
        with open(path, "r") as f:
            return json.load(f)

def list_jobs() -> list:
    """Return a list of all job IDs and their states."""
    job_files = glob.glob(os.path.join(JOBS_DIR, "*.json"))
    jobs = []
    for jf in job_files:
        try:
            with open(jf, "r") as f:
                state = json.load(f)
                jobs.append({"job_id": state.get("job_id"), "status": state.get("status"), "created_at": state.get("created_at"), "agents": state.get("agents", [])})
        except Exception:
            continue
    return jobs

# --- Expose jobs list as API route ---
@app.get("/jobs")
async def get_jobs():
    """
    Return a list of all batch job states.
    """
    return list_jobs()

def update_job_progress(job_id: str, agent_idx: int, progress: int, total: int):
    """Update progress for a given agent in the job."""
    state = load_job_state(job_id)
    if "agents" in state and 0 <= agent_idx < len(state["agents"]):
        state["agents"][agent_idx]["progress"] = progress
        state["agents"][agent_idx]["total"] = total
        save_job_state(job_id, state)

def mark_job_complete(job_id: str, agent_idx: int, result: Any):
    """Mark agent as complete and store result."""
    state = load_job_state(job_id)
    if "agents" in state and 0 <= agent_idx < len(state["agents"]):
        state["agents"][agent_idx]["progress"] = state["agents"][agent_idx].get("total", 0)
        state["agents"][agent_idx]["status"] = "complete"
        state["agents"][agent_idx]["result"] = result
        # Check if all agents complete
        all_done = all(a.get("status") == "complete" for a in state["agents"])
        if all_done:
            state["status"] = "complete"
        save_job_state(job_id, state)
        # Remove from current jobs when job fully complete
        try:
            os.remove(os.path.join(CURRENT_JOBS_DIR, f"{job_id}.json"))
        except FileNotFoundError:
            pass

def set_job_status(job_id: str, status: str):
    """Set job overall status."""
    state = load_job_state(job_id)
    state["status"] = status
    save_job_state(job_id, state)

# --------------------
# /batch-job endpoint for persistent background jobs
# --------------------
class JobActionRequest(BaseModel):
    action: str

class BatchJobRequest(BaseModel):
    agents: list

def _run_agent_simulation(job_id: str, agent_idx: int, agent_params: dict):
    """Background thread: run simulation for one agent, update job state."""
    try:
        episodes = agent_params.get("episodes", 1000)
        repetitions = agent_params.get("repetitions", 1)
        salience_decay = agent_params.get("salience_decay", 0.01)
        high_salience_var_rate = agent_params.get("high_salience_var_rate", 0.1)
        memory_buffer_size = agent_params.get("memory_buffer_size", 1000)
        memory_decay = agent_params.get("memory_decay", 0.01)
        memory_prune_threshold = agent_params.get("memory_prune_threshold", 0.2)
        low_salience_var_rate = agent_params.get("low_salience_var_rate", 0.1)
        event_rate = agent_params.get("event_rate", 3)
        # For progress reporting
        total = episodes * repetitions
        progress = 0
        all_logs = []
        for rep in range(repetitions):
            # Check for cancellation
            state = load_job_state(job_id)
            if state.get("status") == "cancelled":
                # Mark this agent as cancelled and exit
                state["agents"][agent_idx]["status"] = "cancelled"
                save_job_state(job_id, state)
                return
            logs = run_simulation(
                total_ticks=episodes,
                salience_decay=salience_decay,
                highly_variable_rate=high_salience_var_rate,
                event_rate=event_rate,
                memory_buffer_size=memory_buffer_size,
                memory_decay=memory_decay,
                memory_prune_threshold=memory_prune_threshold,
                low_salience_var_rate=low_salience_var_rate,
            )
            all_logs.append(logs)
            progress += episodes
            # Save progress every repetition
            update_job_progress(job_id, agent_idx, progress, total)
        # Save result and mark complete
        mark_job_complete(job_id, agent_idx, all_logs)
    except Exception as e:
        # On error, mark agent as failed
        state = load_job_state(job_id)
        if "agents" in state and 0 <= agent_idx < len(state["agents"]):
            state["agents"][agent_idx]["status"] = "error"
            state["agents"][agent_idx]["error"] = str(e)
            save_job_state(job_id, state)

@app.post("/batch-job")
async def batch_job_endpoint(payload: BatchJobRequest):
    """
    Launch a persistent file-based batch job for background agent simulations.
    Returns immediately with job_id.
    """
    agents = payload.agents
    if not isinstance(agents, list) or len(agents) == 0:
        raise HTTPException(status_code=400, detail="agents must be a non-empty list")
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    # Prepare job state
    job_state = {
        "job_id": job_id,
        "status": "running",
        "created_at": now,
        "agents": [
            {
                "index": i,
                "params": agent,
                "progress": 0,
                "total": agent.get("episodes", 1000) * agent.get("repetitions", 1),
                "status": "running",
                "result": None,
                "error": None,
            }
            for i, agent in enumerate(agents)
        ],
    }
    save_job_state(job_id, job_state)
    # Launch processes for each agent
    for i, agent in enumerate(agents):
        p = multiprocessing.Process(target=_run_agent_simulation, args=(job_id, i, agent), daemon=True)
        p.start()
    return {"job_id": job_id}

# --------------------
# /job-status/{job_id} endpoint
# --------------------
@app.get("/job-status/{job_id}")
async def job_status_endpoint(job_id: str):
    """Return the state: overall job status, per-agent progress, whether complete."""
    try:
        state = load_job_state(job_id)
        # Filter result data for status only (do not include full logs)
        agents_status = [
            {
                "index": a.get("index"),
                "progress": a.get("progress"),
                "total": a.get("total"),
                "status": a.get("status"),
                "error": a.get("error"),
            }
            for a in state.get("agents", [])
        ]
        return {
            "job_id": job_id,
            "status": state.get("status"),
            "created_at": state.get("created_at"),
            "agents": agents_status,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")


# --------------------
# /job-action/{job_id} endpoint
# --------------------
@app.post("/job-action/{job_id}")
async def job_action_endpoint(job_id: str, req: JobActionRequest):
    """
    Handle job control actions: pause, resume, or cancel.
    """
    try:
        action = req.action.lower()
        if action == "pause":
            set_job_status(job_id, "paused")
        elif action == "resume":
            set_job_status(job_id, "running")
        elif action == "cancel":
            set_job_status(job_id, "cancelled")
            # Remove from current jobs when cancelled
            try:
                os.remove(os.path.join(CURRENT_JOBS_DIR, f"{job_id}.json"))
            except FileNotFoundError:
                pass
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")
        return {"status": "success", "job_id": job_id, "action": action}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")

# --------------------
# /run endpoint for trial simulation
# --------------------
@app.post("/run", response_model=dict)
async def run_trial_endpoint(params: RunParams):
    """
    Synchronous trial simulation endpoint.
    """
    # Run a single trial with the given parameters
    logs = run_simulation(
        total_ticks=params.episodes,
        salience_decay=params.salience_decay,
        highly_variable_rate=params.high_salience_var_rate,
        event_rate=params.event_rate,
        memory_buffer_size=params.memory_buffer_size,
        memory_decay=params.memory_decay,
        memory_prune_threshold=params.memory_prune_threshold,
        low_salience_var_rate=params.low_salience_var_rate,
    )
    # Return status and nested data (one repetition)
    return {"status": "complete", "data": [logs]}

# --------------------
# /job-result/{job_id} endpoint
# --------------------
@app.get("/job-result/{job_id}")
async def job_result_endpoint(job_id: str):
    """Return job result if done."""
    try:
        state = load_job_state(job_id)
        if state.get("status") != "complete":
            return {"status": state.get("status"), "message": "Job not complete yet"}
        # Only return results (logs) for each agent
        agents_results = [
            {
                "index": a.get("index"),
                "result": a.get("result"),
                "params": a.get("params"),
                "error": a.get("error"),
            }
            for a in state.get("agents", [])
        ]
        return {
            "job_id": job_id,
            "status": "complete",
            "results": agents_results,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")

# --------------------
# Fast endpoint for current jobs lookup
# --------------------

# Place this endpoint just below the jobs list routes:
@app.get("/current-jobs")
async def list_current_jobs():
    """
    Return only running or paused batch job states for quick UI lookup.
    """
    jobs = []
    for fname in os.listdir(CURRENT_JOBS_DIR):
        path = os.path.join(CURRENT_JOBS_DIR, fname)
        try:
            with open(path, 'r') as f:
                state = json.load(f)
            if state.get("status") in ("running", "paused"):
                jobs.append(state)
        except Exception:
            continue
    return jobs

if __name__ == "__main__":
    # Quick sanity check for run_simulation
    try:
        print("Running self-test: 5 ticks simulation")
        test_logs = run_simulation(
            total_ticks=5,
            salience_decay=0.01,
            highly_variable_rate=0.1,
            event_rate=2,
            memory_buffer_size=50,
            memory_decay=0.01,
            memory_prune_threshold=0.2,
            low_salience_var_rate=0.1
        )
        print("Self-test passed. Sample output:", test_logs[:2])
    except Exception as e:
        print("Self-test FAILED:", e)