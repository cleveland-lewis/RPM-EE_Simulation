import threading  # --- Added for job system ---
import multiprocessing
import uuid # --- Added for job system ---
import os
from typing import Dict, Any  # --- Added for job system ---
JOBS_DIR = "jobs"  # --- Directory for persistent job files ---
os.makedirs(JOBS_DIR, exist_ok=True)  # Ensure jobs dir exists
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
import os
import json
import random
import time
import numpy as np
# --- Step 4.1: Optional Numba JIT flag ---
try:
    import numba as nb
    HAVE_NUMBA = True
except ModuleNotFoundError:
    HAVE_NUMBA = False

# --- Numba JIT-accelerated base array generator ---
if HAVE_NUMBA:
    @nb.njit
    def _generate_base_arrays_numba(total_ticks: int):
        """
        Numba‐accelerated generator for per‑tick arrays.
        Returns the same tuple as _generate_base_arrays.
        """
        import numpy as _np
        att    = _np.random.rand(total_ticks).astype(_np.float32)
        stress = _np.random.rand(total_ticks).astype(_np.float32)
        affect = (_np.random.rand(total_ticks) * 2 - 1).astype(_np.float32)

        vis   = _np.random.randint(0, 4, total_ticks, dtype=_np.int16)
        hear  = _np.random.randint(0, 3, total_ticks, dtype=_np.int16)
        touch = _np.random.randint(0, 2, total_ticks, dtype=_np.int16)
        smell = _np.zeros(total_ticks, dtype=_np.int16)
        taste = _np.zeros(total_ticks, dtype=_np.int16)

        ticks = _np.arange(total_ticks, dtype=_np.int32)
        st_sz = _np.maximum(0, 500 - (ticks % 500)).astype(_np.int32)
        lt_sz = (ticks // 1000).astype(_np.int32)

        return (att, stress, affect,
                vis, hear, touch, smell, taste,
                st_sz, lt_sz)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from src.sensory import SensoryInputSystem  # Core class for simulating sensory input and memory
from .config import load_config, save_config

import datashader as ds
import datashader.transfer_functions as tf
import pandas as pd
import colorcet

#
# --------------------
# VECTORISED FAST‑PATH (step 1/5)
# This helper generates all per‑tick arrays in one NumPy shot.
# Later steps will make run_simulation call this instead of looping.
# -------------------------------------------------------------------
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
    # Step 4.3: Dispatch to JIT version if available
    if HAVE_NUMBA:
        return _generate_base_arrays_numba(total_ticks)
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
# UTILITY: Flatten nested dicts for CSV
# Used to prepare nested simulation output for CSV export.
# --------------------
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

#
# --------------------
# SIMULATION CORE
# --------------------
# The main simulation function.
# Simulates a sequence of sensory events and memory state over time.
# Parameters:
#   total_ticks: Number of simulation time steps (episodes)
#   salience_decay: Rate at which salience decays in memory
#   highly_variable_rate: Controls frequency of highly variable sensory events
# Returns a list of dicts, each representing the state/log at a time tick.
#
def run_simulation(
    total_ticks: int = 2400,
    salience_decay: float = 0.01,
    highly_variable_rate: float = 0.1,
    memory_buffer_size: int = 1000,
    memory_decay: float = 0.01,
    memory_prune_threshold: float = 0.2,
    low_salience_var_rate: float = 0.1,
    bin_size: int = 1,
) -> list:
    start = time.perf_counter()
    # Randomize initial thresholds for this simulation run
    base_low = random.uniform(0.3, 0.7)
    base_high = random.uniform(0.7, 0.95)
    # The following parameters should be integrated into your simulation logic as needed:
    # memory_buffer_size, memory_decay, memory_prune_threshold, low_salience_var_rate
    # For now, these are received and can be logged or passed to SensoryInputSystem
    # Create the sensory input system with randomized thresholds and config
    sim = SensoryInputSystem(
        low_salience_threshold=base_low,
        high_salience_threshold=base_high,
        salience_decay=salience_decay,
        highly_variable_rate=highly_variable_rate,
    )
    attunement_scores = np.random.uniform(0, 1, total_ticks)
    schema_stress = np.random.uniform(0, 1, total_ticks)
    avg_affect_feedback = np.random.uniform(-1, 1, total_ticks)
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
    att_b    = bin_mean(att_arr)
    stress_b = bin_mean(stress_arr)
    affect_b = bin_mean(affect_arr)
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
    return logs
# -------------------------------------------------
# --------------------
# FASTAPI SETUP
# --------------------
# Set up FastAPI app to provide simulation API endpoints.
app = FastAPI()

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
from datetime import datetime

class LogSaveRequest(BaseModel):
    logs: list

@app.post("/save-logs")
async def save_logs(payload: LogSaveRequest):
    os.makedirs("saved_logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"saved_logs/log_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(payload.logs, f, indent=2)
    return {"status": "success", "filename": filename}

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
# Simulation API endpoint
# Runs the simulation with given parameters.
# Handles errors gracefully and returns logs or error details.
# --------------------
@app.post("/run")
async def run_endpoint(params: RunParams):
    print("Received simulation config:", params.dict())
    import sys
    sys.stdout.flush()
    print("Params parsed OK.")
    sys.stdout.flush()
    try:
        all_logs = []
        total_samples = params.episodes * params.repetitions
        # If total_samples > 500_000, do not return raw logs
        if total_samples > 500_000:
            # Run simulations but do not return logs
            for _ in range(params.repetitions):
                print("Starting simulation run (large, logs not returned)...")
                sys.stdout.flush()
                _ = run_simulation(
                    total_ticks=params.episodes,
                    salience_decay=params.salience_decay,
                    highly_variable_rate=params.high_salience_var_rate,
                    memory_buffer_size=params.memory_buffer_size,
                    memory_decay=params.memory_decay,
                    memory_prune_threshold=params.memory_prune_threshold,
                    low_salience_var_rate=params.low_salience_var_rate,
                )
                print("Simulation run complete.")
                sys.stdout.flush()
            print("All simulation runs complete (logs not returned).")
            sys.stdout.flush()
            return {
                "status": "complete",
                "message": "Log data is too large to return directly. Please use the Datashader cluster plots for visualization.",
                "config": {
                    "salience_decay": params.salience_decay,
                    "event_rate": params.event_rate
                }
            }
        else:
            # For <=500,000, apply adaptive downsampling
            for _ in range(params.repetitions):
                print("Starting simulation run...")
                sys.stdout.flush()
                logs = run_simulation(
                    total_ticks=params.episodes,
                    salience_decay=params.salience_decay,
                    highly_variable_rate=params.high_salience_var_rate,
                    memory_buffer_size=params.memory_buffer_size,
                    memory_decay=params.memory_decay,
                    memory_prune_threshold=params.memory_prune_threshold,
                    low_salience_var_rate=params.low_salience_var_rate,
                )
                # Calculate bin_size for downsampling
                N = len(logs)
                if N <= 1000:
                    bin_size = 1
                else:
                    bin_size = max(1, int(1.1 ** ((N - 1000)//1000)))
                logs_downsampled = downsample_logs(logs, bin_size)
                all_logs.append(logs_downsampled)
                print("Simulation run complete (downsampled).")
                sys.stdout.flush()
            print("All simulation runs complete.")
            sys.stdout.flush()
            return {
                "status": "complete",
                "data": all_logs,
                "config": {
                    "salience_decay": params.salience_decay,
                    "event_rate": params.event_rate
                }
            }
    except Exception as e:
        # On error, return error message and stack trace for debugging
        tb_str = traceback.format_exc()
        print("Error in /run:", tb_str)  # Log error to terminal
        import sys
        sys.stdout.flush()
        return {
            "status": "error",
            "error": str(e),
            "traceback": tb_str,
            "params": params.dict() if hasattr(params, "dict") else dict(params)
        }


# --- Utility functions for flattening/unflattening config dicts ---
def flatten_dict(d, parent_key='', sep='_'):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items

def unflatten_dict(d, sep='_'):
    result = {}
    for k, v in d.items():
        keys = k.split(sep)
        cur = result
        for part in keys[:-1]:
            if part not in cur:
                cur[part] = {}
            cur = cur[part]
        cur[keys[-1]] = v
    return result

# --- For local testing as a script ---
# This block allows running the FastAPI app directly with uvicorn for local testing.
@app.get("/config")
def get_config():
    """Returns the current simulation configuration as a flattened JSON dict."""
    cfg = load_config()
    flat_cfg = flatten_dict(cfg)
    return flat_cfg

@app.post("/config")
def update_config(cfg: dict):
    """Accepts and saves a new simulation configuration."""
    nested_cfg = unflatten_dict(cfg)
    save_config(nested_cfg)
    return {"status": "success"}

# New endpoint for datashader plots
@app.post("/datashader-plots")
async def datashader_plots(payload: LogSaveRequest):
    os.makedirs("saved_logs", exist_ok=True)
    df = pd.DataFrame(payload.logs)
    # Cluster: attunement (x), stress (y), color by clock
    cvs = ds.Canvas(plot_width=600, plot_height=600)
    agg1 = cvs.points(df, 'attunement_score', 'schema_stress', agg=ds.mean('clock'))
    img1 = tf.shade(agg1, cmap=colorcet.fire, how='eq_hist')
    img1.to_pil().save("saved_logs/plot_attn_stress.png")
    # Cluster: clock (x), stress (y), color by attunement
    agg2 = cvs.points(df, 'clock', 'schema_stress', agg=ds.mean('attunement_score'))
    img2 = tf.shade(agg2, cmap=colorcet.kbc, how='eq_hist')
    img2.to_pil().save("saved_logs/plot_clock_stress.png")
    # Cluster: clock (x), attunement (y), color by stress
    agg3 = cvs.points(df, 'clock', 'attunement_score', agg=ds.mean('schema_stress'))
    img3 = tf.shade(agg3, cmap=colorcet.bgy, how='eq_hist')
    img3.to_pil().save("saved_logs/plot_clock_attn.png")
    return {
        "status": "success",
        "plots": [
            "saved_logs/plot_attn_stress.png",
            "saved_logs/plot_clock_stress.png",
            "saved_logs/plot_clock_attn.png"
        ]
    }

# Optional static file serving endpoint for saved PNG files
@app.get("/static/{filename}")
async def serve_static(filename: str):
    file_path = os.path.join("saved_logs", filename)
    if os.path.isfile(file_path):
        return FileResponse(file_path, media_type="image/png")
    return HTMLResponse(status_code=404, content="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.simulation:app", host="0.0.0.0", port=8000, reload=True)
# --------------------
# Persistent File-based Job System for Batch Agent Simulations
# --------------------
import glob

# --- Helper functions for job state persistence ---
def save_job_state(job_id: str, state: dict):
    """Save the job state to disk (jobs/{job_id}.json)."""
    path = os.path.join(JOBS_DIR, f"{job_id}.json")
    with open(path, "w") as f:
        json.dump(state, f, indent=2)

def load_job_state(job_id: str) -> dict:
    """Load the job state from disk."""
    path = os.path.join(JOBS_DIR, f"{job_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Job {job_id} not found")
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

def set_job_status(job_id: str, status: str):
    """Set job overall status."""
    state = load_job_state(job_id)
    state["status"] = status
    save_job_state(job_id, state)

# --------------------
# /batch-job endpoint for persistent background jobs
# --------------------
from fastapi import BackgroundTasks, Request
from fastapi import HTTPException
class JobActionRequest(BaseModel):
    action: str
from datetime import datetime

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
        # For progress reporting
        total = episodes * repetitions
        progress = 0
        all_logs = []
        for rep in range(repetitions):
            logs = run_simulation(
                total_ticks=episodes,
                salience_decay=salience_decay,
                highly_variable_rate=high_salience_var_rate,
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
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")
        return {"status": "success", "job_id": job_id, "action": action}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")

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
