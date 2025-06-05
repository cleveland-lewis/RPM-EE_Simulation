import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# from config import load_config, save_config

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
    cfg = load_config()
    return cfg

@app.post("/config")
def update_config(cfg: dict):
    """
    Accepts and saves a new simulation configuration.
    """
    if not isinstance(cfg, dict):
        raise HTTPException(status_code=400, detail="Config must be a JSON object")
    save_config(cfg)
    return {"status": "success"}

def load_config(path="config.json"):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(cfg, path="config.json"):
    try:
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")