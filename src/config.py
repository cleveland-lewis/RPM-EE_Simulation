from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from .config_schema import SimulationConfig, load_simulation_config, resolve_simulation_config, save_simulation_config
except ImportError:  # pragma: no cover - fallback for running as a script
    from config_schema import SimulationConfig, load_simulation_config, resolve_simulation_config, save_simulation_config

app = FastAPI()

# Enable CORS so frontend can access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to your frontend origin for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/config")
def get_config():
    """
    Returns the current simulation configuration as JSON.
    """
    return load_simulation_config()

@app.post("/config", response_model=SimulationConfig)
def update_config(cfg: SimulationConfig):
    """
    Accepts and saves a new simulation configuration.
    """
    if not isinstance(cfg, SimulationConfig):
        raise HTTPException(status_code=400, detail="Config must be a JSON object")
    normalized = resolve_simulation_config(cfg.to_kwargs(), preset=cfg.preset)
    save_simulation_config(normalized)
    return normalized
