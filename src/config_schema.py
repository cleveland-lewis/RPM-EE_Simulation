"""
Shared configuration schema for RPM-EE simulation entry points.

This model centralizes parameter names, defaults, and light validation so the
CLI, FastAPI endpoint, and presets all rely on the same contract.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import json
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class SimulationConfig(BaseModel):
    # Core simulation controls
    total_ticks: int = Field(2400, gt=0)
    salience_decay: float = Field(0.01, ge=0.0)
    highly_variable_rate: float = Field(0.1, ge=0.0)
    event_rate: int = Field(3, ge=0)
    memory_buffer_size: int = Field(1000, gt=0)
    memory_decay: float = Field(0.01, ge=0.0)
    memory_prune_threshold: float = Field(0.2, ge=0.0)
    low_salience_var_rate: float = Field(0.1, ge=0.0)
    bin_size: int = Field(1, gt=0)
    preset: Optional[str] = None
    seed: Optional[int] = None

    # Optional behavior knobs
    theta0: float = 0.07
    theta_s_mult: float = 0.65
    gate_by_attunement: int = 0
    gate_temperature: float = 1.0
    replay_softmax: int = 0
    explore_error_gain: float = 2.0
    softmax_temp: float = 1.0
    explore_floor: float = 0.0

    # Multipliers and normalization toggles
    theta_e_mult: float = 0.85
    theta_m_mult: float = 0.90
    theta_v_mult: float = 0.90
    norm_stress: int = 0
    norm_ext_load: int = 0
    norm_mem_load: int = 0
    norm_aff_vol: int = 0

    # Population mixture controls
    use_population_mixture: int = 0
    mixture_weights: Optional[Dict[str, float]] = None
    stratify_index: Optional[int] = None
    stratify_total: Optional[int] = None
    within_stratum_theta0_jitter: Optional[float] = None

    # Stress and link function knobs
    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 0.0
    kappa: float = 0.3
    tau: float = 5.0
    stress_decay: float = 0.0
    att_gain: float = 2.0
    att_offset: float = 1.0
    att_scale: float = 1.0
    stress_gain: float = 2.0
    stress_offset: float = 0.0
    att_gate_latent: float = 1.0
    stress_inner_sigmoid: int = 0

    class Config:
        extra = "ignore"

    @validator("mixture_weights")
    def _validate_mixture_weights(cls, value: Optional[Dict[str, float]]):
        if value is None:
            return value
        if not isinstance(value, dict):
            raise ValueError("mixture_weights must be a mapping of subgroup -> weight")
        if not value:
            raise ValueError("mixture_weights cannot be empty")
        total = float(sum(float(v) for v in value.values()))
        if total <= 0.0:
            raise ValueError("mixture_weights must sum to a positive value")
        return {str(k): float(v) for k, v in value.items()}

    @classmethod
    def allowed_keys(cls) -> set[str]:
        """Names accepted by the canonical schema (compatible with Pydantic v1/v2)."""
        if hasattr(cls, "model_fields"):
            return set(cls.model_fields.keys())  # type_ignore[attr-defined]
        return set(cls.__fields__.keys())  # type_ignore[attr-defined]

    @classmethod
    def filtered(cls, data: Optional[dict], preset: Optional[str] = None) -> "SimulationConfig":
        """Create a config from partial user data while discarding unknown keys."""
        payload = {**(data or {})}
        if preset is not None:
            payload.setdefault("preset", preset)
        clean = {k: v for k, v in payload.items() if k in cls.allowed_keys()}
        return cls(**clean)

    def to_kwargs(self) -> dict:
        """Export run_simulation kwargs with defaults applied and nulls removed."""
        try:
            return self.dict(exclude_none=True)  # Pydantic v1
        except AttributeError:
            return self.model_dump(exclude_none=True)  # Pydantic v2


def resolve_simulation_config(data: Optional[dict] = None, preset: Optional[str] = None) -> SimulationConfig:
    """
    Normalize any entry-point config (CLI flags, presets, API payloads) into the
    canonical SimulationConfig with defaults applied and unknown keys dropped.
    """
    payload = {**(data or {})}
    return SimulationConfig.filtered(payload, preset=preset or payload.get("preset"))


def resolve_simulation_kwargs(data: Optional[dict] = None, preset: Optional[str] = None) -> dict:
    """Return sanitized kwargs for run_simulation using the shared schema."""
    return resolve_simulation_config(data, preset=preset).to_kwargs()


def load_simulation_config(path: str | Path = "config.json") -> SimulationConfig:
    try:
        with open(path, "r") as f:
            payload = json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {path}. Returning default SimulationConfig.")
        return SimulationConfig()
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse config from {path} as JSON: {e}")
    except IOError as e:
        raise RuntimeError(f"Failed to read config file {path}: {e}")
    return resolve_simulation_config(payload)


def save_simulation_config(cfg: SimulationConfig, path: str | Path = "config.json") -> None:
    with open(path, "w") as f:
        json.dump(cfg.to_kwargs(), f, indent=2)
