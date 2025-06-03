import os
import json
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from src.sensory import SensoryInputSystem  # Core class for simulating sensory input and memory

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
def run_simulation(total_ticks: int = 2400, salience_decay: float = 0.01, highly_variable_rate: float = 0.1) -> list:
    # Randomize initial thresholds for this simulation run
    base_low = random.uniform(0.3, 0.7)
    base_high = random.uniform(0.7, 0.95)
    # Create the sensory input system with randomized thresholds and config
    sim = SensoryInputSystem(
        low_salience_threshold=base_low,
        high_salience_threshold=base_high,
        salience_decay=salience_decay,
        highly_variable_rate=highly_variable_rate,
    )
    logs = []
    for tick in range(total_ticks):
        # Advance simulation clock and decay memory buffer
        sim.update_clock()
        sim.memory_buffer.tick_decay()
        # Generate a new sensory input event packet for this tick
        packet = sim.generate_input()

        # Add simulated "attunement", "schema stress", and affect feedback values
        packet['attunement_score'] = random.uniform(0, 1)
        packet['schema_stress'] = random.uniform(0, 1)
        packet['avg_affect_feedback'] = random.uniform(-1, 1)

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
        logs.append(log_entry)

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
class LogSaveRequest(BaseModel):
    logs: list
# Overwrites each time; for append, open with 'a' and write jsonlines
@app.post("/save-logs")
async def save_logs(payload: LogSaveRequest):
    with open("saved_logs.json", "w") as f:
        json.dump(payload.logs, f, indent=2)
    return {"status": "success"}

# Serve main HTML page (e.g., /src/trials.html) for browser access
@app.get("/", include_in_schema=False)
async def serve_trials():
    html_path = os.path.join(os.path.dirname(__file__), "trials.html")
    try:
        with open(html_path, "r") as f:
            html = f.read()
    except FileNotFoundError:
        return HTMLResponse(status_code=404, content="trials.html not found")
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
    # Add more as needed

import traceback

# --------------------
# Simulation API endpoint
# Runs the simulation with given parameters.
# Handles errors gracefully and returns logs or error details.
# --------------------
@app.post("/run")
async def run_endpoint(params: RunParams):
    print("Received simulation config:", params.dict())
    """
    Launch a simulation run.
    Expects JSON {episodes, repetitions}.
    Returns: {status: 'complete', data: [[packet,...], ...]}
    On error: {status: 'error', error: str, traceback: str, params: dict}
    """
    try:
        all_logs = []
        # Repeat the simulation for the requested number of repetitions
        for _ in range(params.repetitions):
            logs = run_simulation(
                total_ticks=params.episodes,
                salience_decay=params.salience_decay,
                highly_variable_rate=params.event_rate
            )
            all_logs.append(logs)
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
        return {
            "status": "error",
            "error": str(e),
            "traceback": tb_str,
            "params": params.dict() if hasattr(params, "dict") else dict(params)
        }

# --- For local testing as a script ---
# This block allows running the FastAPI app directly with uvicorn for local testing.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.simulation:app", host="0.0.0.0", port=8000, reload=True)