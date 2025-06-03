from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import load_config, save_config

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
    save_config(cfg)
    return {"status": "success"}