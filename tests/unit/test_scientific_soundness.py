import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.simulation import run_simulation, _precision_from_var


class DeterministicEnv:
    def reset(self, seed=None):
        self.t = 0
        return {"t": 0}

    def step(self, env_state, agent_state, action, t):
        _ = env_state, agent_state, action
        obs = {
            "modality_loads": {"vision": (t % 10) / 10.0, "hearing": 0.2, "touch": 0.1},
            "avg_affect_feedback": 0.1,
            "short_term_size": 100,
        }
        return env_state, obs, 0.0, False, {}


class PatternEnv:
    def __init__(self, loads):
        self.loads = loads

    def reset(self, seed=None):
        _ = seed
        return {"t": 0}

    def step(self, env_state, agent_state, action, t):
        _ = env_state, agent_state, action
        load = float(self.loads[t])
        obs = {
            "modality_loads": {"vision": load, "hearing": 0.0, "touch": 0.0},
            "avg_affect_feedback": 0.0,
            "short_term_size": 50,
        }
        return env_state, obs, 0.0, False, {}


class AdapterStub:
    def __init__(self, total_ticks, obs):
        self._total_ticks = total_ticks
        self._obs = obs

    def get_total_ticks(self):
        return self._total_ticks

    def get_affect_feedback(self, tick):
        return float(self._obs[tick]["avg_affect_feedback"])

    def get_external_load(self, tick):
        return dict(self._obs[tick]["modality_loads"])

    def get_memory_load(self, tick):
        return None

    def get_action_executed(self, tick):
        return None

    def get_observation(self, tick):
        return dict(self._obs[tick])


def test_deterministic_env_same_seed():
    env = DeterministicEnv()
    out1 = run_simulation(total_ticks=20, seed=42, bin_size=1, env=env)
    env = DeterministicEnv()
    out2 = run_simulation(total_ticks=20, seed=42, bin_size=1, env=env)
    assert out1["logs"] == out2["logs"]


def test_stress_fast_slow_impulse_and_step():
    impulse = [0.0, 0.0, 1.0, 0.0, 0.0]
    out = run_simulation(
        total_ticks=len(impulse),
        seed=1,
        bin_size=1,
        env=PatternEnv(impulse),
        tau=10.0,
        tau_fast=1.5,
    )
    logs = out["logs"]
    assert logs[2]["stress_fast"] > logs[1]["stress_fast"]
    assert logs[4]["stress_fast"] < logs[2]["stress_fast"]
    assert abs(logs[2]["stress_slow"] - logs[1]["stress_slow"]) < abs(
        logs[2]["stress_fast"] - logs[1]["stress_fast"]
    )

    step = [0.0, 0.0, 1.0, 1.0, 1.0, 1.0]
    out = run_simulation(
        total_ticks=len(step),
        seed=2,
        bin_size=1,
        env=PatternEnv(step),
        tau=8.0,
        tau_fast=1.5,
    )
    logs = out["logs"]
    assert logs[4]["stress_slow"] > logs[2]["stress_slow"]
    assert logs[3]["stress_fast"] >= logs[4]["stress_fast"]


def test_precision_monotonicity_ext_load():
    low_var = _precision_from_var(0.01, 0.0, 1e6, 1e-6)
    high_var = _precision_from_var(1.0, 0.0, 1e6, 1e-6)
    assert high_var < low_var


def test_att_scale_changes_output():
    loads = [0.4] * 20
    env = PatternEnv(loads)
    out_low = run_simulation(total_ticks=20, seed=4, bin_size=1, env=env, att_scale=0.5)
    env = PatternEnv(loads)
    out_base = run_simulation(total_ticks=20, seed=4, bin_size=1, env=env, att_scale=1.0)
    mean_low = np.mean([log["attunement_score"] for log in out_low["logs"]])
    mean_base = np.mean([log["attunement_score"] for log in out_base["logs"]])
    assert mean_low < mean_base


def test_adapter_observations_used():
    obs = [
        {
            "modality_loads": {"vision": 0.5, "hearing": 0.5, "touch": 0.5},
            "avg_affect_feedback": 0.1,
            "short_term_size": 100,
        }
        for _ in range(5)
    ]
    adapter = AdapterStub(total_ticks=5, obs=obs)
    out = run_simulation(seed=5, bin_size=1, data_adapter=adapter)
    first = out["logs"][0]
    assert abs(first["obs_vision_load"] - 0.5) < 1e-6
    assert abs(first["ext_load"] - 0.5) < 1e-6


def test_precision_zero_eliminates_affect_term():
    env = DeterministicEnv()
    out = run_simulation(
        total_ticks=5,
        seed=6,
        bin_size=1,
        env=env,
        pi_min=0.0,
        pi_max=0.0,
    )
    assert out["logs"][0]["logit_aff_term"] == 0.0
