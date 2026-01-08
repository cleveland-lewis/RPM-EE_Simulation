# Environment Interface (Minimal)

RPM-EE can run against a task/environment stream instead of synthetic inputs.
An environment exposes two methods:

```python
class Environment:
    def reset(self, seed: int | None = None) -> dict:
        ...

    def step(self, env_state: dict, agent_state: dict, action: bool | None, t: int):
        # returns (env_state, observation, reward, done, info)
        ...
```

## Observation schema (minimum)

```python
observation = {
    "modality_loads": {"vision": 0.2, "hearing": 0.1, "touch": 0.0},
    "avg_affect_feedback": 0.0,
    "short_term_size": 120,
    # Optional:
    "memory_load": 0.4,
    "stress_rating": 0.3,
    "action_executed": True,
}
```

## Example environment

```python
class SimpleOddballEnv:
    def __init__(self, p_oddball: float = 0.2):
        self.p_oddball = p_oddball

    def reset(self, seed=None):
        self.rng = np.random.default_rng(seed)
        return {"t": 0}

    def step(self, env_state, agent_state, action, t):
        _ = agent_state, action
        oddball = float(self.rng.random() < self.p_oddball)
        observation = {
            "modality_loads": {"vision": 0.0, "hearing": oddball, "touch": 0.0},
            "avg_affect_feedback": 0.0,
            "short_term_size": 100,
        }
        return env_state, observation, 0.0, False, {"oddball": oddball}
```
