# tests/test_configure.py
import json

import pytest

from src.config_schema import load_simulation_config, save_simulation_config, SimulationConfig


def test_load_nonexistent_config(tmp_path):
    """load_simulation_config should return a default SimulationConfig for a missing file (no crash)."""
    fake = tmp_path / "nope.json"
    cfg = load_simulation_config(path=str(fake))
    assert isinstance(cfg, SimulationConfig)
    assert cfg.total_ticks == 2400 # Check a default value


def test_load_existing_config(tmp_path):
    sample = {"total_ticks": 500}
    cfg_file = tmp_path / "sim.json"
    cfg_file.write_text(json.dumps(sample))
    cfg = load_simulation_config(path=str(cfg_file))
    assert isinstance(cfg, SimulationConfig)
    assert cfg.total_ticks == 500


def test_save_and_reload_configuration(tmp_path):
    cfg_file = tmp_path / "simulation_config.json"
    new_cfg = SimulationConfig(total_ticks=123)
    save_simulation_config(new_cfg, path=str(cfg_file))
    reloaded = load_simulation_config(path=str(cfg_file))
    assert reloaded.total_ticks == 123


def test_save_overwrites_existing_file(tmp_path):
    cfg_file = tmp_path / "simulation_config.json"
    first = SimulationConfig(total_ticks=1)
    second = SimulationConfig(total_ticks=2)
    save_simulation_config(first, path=str(cfg_file))
    save_simulation_config(second, path=str(cfg_file))
    reloaded = load_simulation_config(path=str(cfg_file))
    assert reloaded.total_ticks == 2
