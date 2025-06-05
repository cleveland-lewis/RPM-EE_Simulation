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
    logs = []
    tick_time_sum = 0.0
    tick_time_count = 0
    for tick in range(total_ticks):
        t0 = time.perf_counter()
        # Advance simulation clock and decay memory buffer
        sim.update_clock()
        sim.memory_buffer.tick_decay()
        # Generate a new sensory input event packet for this tick
        packet = sim.generate_input()

        # Add simulated "attunement", "schema stress", and affect feedback values
        packet['attunement_score'] = float(attunement_scores[tick])
        packet['schema_stress'] = float(schema_stress[tick])
        packet['avg_affect_feedback'] = float(avg_affect_feedback[tick])

        # For each sensory modality, count events and calculate mean intensity
        for mod in ['vision', 'hearing', 'touch', 'smell', 'taste']:
            events = packet.get(mod, [])
            packet[f'{mod}_count'] = len(events)
            if events:
                intensities = [e.get('intensity', 0) for e in events if isinstance(e, dict)]
                packet[f'{mod}_mean_intensity'] = sum(intensities) / len(intensities) if intensities else None
            else:
                packet[f'{mod}_mean_intensity'] = None

        # Collect memory buffer stats for short-term and long-term storage
        mem_buf = sim.memory_buffer
        packet['short_term_count'] = len(getattr(mem_buf, "short_term", []))
        packet['long_term_count'] = len(getattr(getattr(sim, "long_term_storage", type('', (), {})()), "long_term", []))

        # Store the memory configuration used for this run
        memory_config = {
            'low_salience_threshold': getattr(sim, 'low_salience_threshold', None),
            'high_salience_threshold': getattr(sim, 'high_salience_threshold', None),
            'salience_decay': getattr(sim, 'salience_decay', None),
            'highly_variable_rate': getattr(sim, 'highly_variable_rate', None),
        }
        packet['memory_config'] = memory_config

        # Store memory statistics for this tick
        memory_stats = {
            'short_term_size': len(getattr(mem_buf, 'short_term', [])),
            'long_term_size': len(getattr(getattr(sim, 'long_term_storage', type('', (), {})()), 'long_term', [])),
            'tick': tick,
        }
        packet['memory_stats'] = memory_stats

        # Store current tick in the packet
        packet['tick'] = tick

        # Fill in missing or None values for core scores
        for key in ['attunement_score', 'schema_stress', 'avg_affect_feedback']:
            if key not in packet or packet[key] is None:
                packet[key] = -999

        # Select which fields to log for each tick
        log_fields = [
            'tick', 'attunement_score', 'schema_stress', 'avg_affect_feedback',
            'vision_count', 'vision_mean_intensity',
            'hearing_count', 'hearing_mean_intensity',
            'touch_count', 'touch_mean_intensity',
            'smell_count', 'smell_mean_intensity',
            'taste_count', 'taste_mean_intensity',
            'short_term_count', 'long_term_count',
            'memory_config', 'memory_stats'
        ]
        # Prepare log entry for this tick
        log_entry = {k: packet.get(k, None) for k in log_fields}
        log_entry['clock'] = log_entry.pop('tick', None)
        t1 = time.perf_counter()
        tick_time_sum += (t1 - t0)
        tick_time_count += 1
        if tick % 10000 == 0 and tick > 0:
            avg_tick = tick_time_sum / tick_time_count
            print(f"[PROFILE] Tick {tick}: {avg_tick:.6f} seconds per tick (avg over last {tick_time_count} ticks)")
            tick_time_sum = 0.0
            tick_time_count = 0
        logs.append(log_entry)

    if tick_time_count > 0:
        avg_tick = tick_time_sum / tick_time_count
        print(f"[PROFILE] FINAL: Avg tick duration for last {tick_time_count} ticks: {avg_tick:.6f} seconds")
    end = time.perf_counter()
    print(f"[PROFILE] Total simulation run time: {end - start:.3f} seconds for {total_ticks} episodes")
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
async def serve_trials():
    html_path = os.path.join(os.path.dirname(__file__), "trials.html")
    try:
        with open(html_path, "r") as f:
            html = f.read()
    except FileNotFoundError:
        return HTMLResponse(status_code=404, content="trials.html not found")
    # Inject loading spinner/message for config modal if not present
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