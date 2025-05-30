import os
import json
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from . import sensory

# --------------------
# UTILITY: Flatten nested dicts for CSV
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

# --------------------
# SIMULATION CORE
# --------------------
def run_simulation(total_ticks: int = 2400) -> list:
    """
    Run the sensory-memory simulation for `total_ticks` iterations.
    Returns a list of per-tick packets (partially flattened for CSV/export),
    preserving 'memory_config' and 'memory_stats' as nested dictionaries.
    """
    sim = sensory.SensoryInputSystem()
    logs = []
    for _ in range(total_ticks):
        sim.update_clock()
        sim.memory_buffer.tick_decay()
        packet = sim.generate_input()

        # --- Graph fields ---
        packet['attunement_score'] = random.uniform(0, 1)
        packet['schema_stress'] = random.uniform(0, 1)
        packet['avg_affect_feedback'] = random.uniform(-1, 1)

        # --- Example nested fields ---
        packet['memory_config'] = {
            'low_salience_threshold': getattr(sim.memory_buffer, "low_salience_threshold", None),
            'half_life_ranges': {'low': (1200, 2400), 'high': (2400, 4800)},
            'prune_min_salience': 0.1
        }
        packet['memory_stats'] = {
            'short_term_count': len(getattr(sim.memory_buffer, "short_term", [])),
            'long_term_count': len(getattr(getattr(sim, "long_term_storage", type('', (), {})()), "long_term", []))
        }

        # Flatten everything except 'memory_config' and 'memory_stats'
        keys_to_exclude = ['memory_config', 'memory_stats']
        partial_flat = {}
        for k, v in packet.items():
            if k in keys_to_exclude:
                partial_flat[k] = v
            else:
                if isinstance(v, dict):
                    partial_flat.update(flatten_dict({k: v}))
                else:
                    partial_flat[k] = v

        logs.append(partial_flat)
    return logs

# --------------------
# FASTAPI SETUP
# --------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# --------------------
# Saving as .JSON file
# --------------------
class LogSaveRequest(BaseModel):
    logs: list
# Overwrites each time; for append, open with 'a' and write jsonlines
@app.post("/save-logs")
async def save_logs(payload: LogSaveRequest):
    with open("saved_logs.json", "w") as f:
        json.dump(payload.logs, f, indent=2)
    return {"status": "success"}
# Serve main HTML (e.g., /src/trials.html)
@app.get("/", include_in_schema=False)
async def serve_trials():
    html_path = os.path.join(os.path.dirname(__file__), "trials.html")
    try:
        with open(html_path, "r") as f:
            html = f.read()
    except FileNotFoundError:
        return HTMLResponse(status_code=404, content="trials.html not found")
    return HTMLResponse(content=html, media_type="text/html")

# Model for /run params
class RunParams(BaseModel):
    episodes: int
    repetitions: int

# API endpoint for running simulations (returns list of lists)
@app.post("/run")
async def run_endpoint(params: RunParams):
    """
    Launch a simulation run.
    Expects JSON {episodes, repetitions}.
    Returns: {status: 'complete', data: [[packet,...], ...]}
    """
    all_logs = []
    for _ in range(params.repetitions):
        logs = run_simulation(total_ticks=params.episodes)
        all_logs.append(logs)
    return {"status": "complete", "data": all_logs}

# --- For local testing as a script ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.simulation:app", host="0.0.0.0", port=8000, reload=True)