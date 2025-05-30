import os
import json

def get_config_path():
    """
    Dynamically determines the path to the configuration file.
    Respects the SIMULATION_CONFIG_PATH environment variable if set.
    """
    return os.getenv(
        'SIMULATION_CONFIG_PATH',
        os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'config', 'simulation_config.json'))
    )

def default_config():
    """
    Returns the default simulation configuration schema.
    """
    return {
        "SensoryInputSystem": {
            "awake_duration": 300,
            "fatigued_duration": 100,
            "asleep_duration": 100
        },
        "SalienceTagger": {
            "salience_decay": 0.01,
            "weight_error_corr": 1.0,
            "weight_soothing": 1.0,
            "timing_center": 300,
            "timing_steepness": 0.1
        },
        "ReplayModeArbitrator": {
            "damping_cycles": 5
        },
        "ReplayFatigueSuppressor": {
            "fatigue_threshold": 5,
            "suppression_factor": 0.5
        },
        "EmotionalEncoder": {
            "replay_fatigue_threshold": 3
        },
        "SimulationClusterArbiter": {
            "alpha": 0.5,
            "beta": 0.3,
            "gamma": 0.2
        }
    }

def merge_with_defaults(loaded):
    """
    Merges a loaded config dict with the default config to ensure all expected keys exist.
    """
    defaults = default_config()
    for section, values in defaults.items():
        if section not in loaded:
            loaded[section] = values
        elif isinstance(values, dict):
            for k, v in values.items():
                loaded[section].setdefault(k, v)
    return loaded

def load_config():
    """
    Loads the simulation configuration from JSON. If missing or malformed,
    returns a merged default config.
    """
    path = get_config_path()
    if not os.path.exists(path):
        return default_config()
    try:
        with open(path, 'r') as f:
            return merge_with_defaults(json.load(f))
    except Exception:
        return default_config()

def save_config(cfg: dict):
    """
    Saves the given configuration dict to the JSON file at get_config_path().
    """
    path = get_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(cfg, f, indent=2)