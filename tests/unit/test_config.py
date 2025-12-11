import pytest
from fastapi.testclient import TestClient
from src.config import app, SimulationConfig

@pytest.fixture
def client():
    return TestClient(app)

def test_get_config_returns_current_config(client, monkeypatch):
    monkeypatch.setattr("src.config.load_simulation_config", lambda: SimulationConfig(total_ticks=123))
    response = client.get("/config")
    assert response.status_code == 200
    assert response.json()["total_ticks"] == 123

def test_update_config_with_valid_config_returns_updated_config(client, monkeypatch):
    monkeypatch.setattr("src.config.save_simulation_config", lambda cfg: None)
    response = client.post("/config", json={"total_ticks": 456})
    assert response.status_code == 200
    assert response.json()["total_ticks"] == 456

def test_update_config_with_invalid_config_raises_http_exception(client):
    response = client.post("/config", json={"total_ticks": "invalid"})
    assert response.status_code == 422  # Unprocessable Entity
