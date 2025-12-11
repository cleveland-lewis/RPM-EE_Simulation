import json

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from src import config
from src.config_schema import SimulationConfig


@pytest.fixture
def client(monkeypatch):
    # Avoid hitting the filesystem by stubbing load/save.
    monkeypatch.setattr(config, "load_simulation_config", lambda: SimulationConfig(total_ticks=77, preset="test_preset"))
    monkeypatch.setattr(config, "save_simulation_config", lambda cfg: None)
    return TestClient(config.app)


def test_get_config_returns_current_config(client):
    resp = client.get("/config")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total_ticks"] == 77
    assert payload["preset"] == "test_preset"


def test_post_config_persists_normalized_config(monkeypatch):
    saved = {}

    def _save(cfg):
        saved["value"] = cfg

    monkeypatch.setattr(config, "save_simulation_config", _save)
    client_local = TestClient(config.app)

    resp = client_local.post("/config", json={"total_ticks": 42})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total_ticks"] == 42
    assert isinstance(saved["value"], SimulationConfig)
    # Defaults applied (spot-check a couple)
    assert "salience_decay" in payload and payload["salience_decay"] == pytest.approx(0.01)


def test_post_config_rejects_invalid_payload(client):
    resp = client.post("/config", data=json.dumps("not a dict"))
    assert resp.status_code == 422  # validation error from FastAPI/Pydantic


def test_post_config_propagates_save_errors(monkeypatch):
    def _fail_save(cfg):
        raise IOError("disk full")

    monkeypatch.setattr(config, "save_simulation_config", _fail_save)
    client_local = TestClient(config.app)

    resp = client_local.post("/config", json={"total_ticks": 10})
    assert resp.status_code == 500
    assert "disk full" in resp.text
