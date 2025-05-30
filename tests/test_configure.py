# tests/test_configure.py
import os, json, importlib, pytest, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MODULE_NAME = "pages.configure"

def reload_config_module():
    if MODULE_NAME in sys.modules:
        del sys.modules[MODULE_NAME]
    return importlib.import_module(MODULE_NAME)

def test_default_config_schema():
    mod = reload_config_module()
    cfg = mod.default_config()
    expected_sections = {
        "SensoryInputSystem", "SalienceTagger", "ReplayModeArbitrator",
        "ReplayFatigueSuppressor", "EmotionalEncoder", "SimulationClusterArbiter"
    }
    assert set(cfg) == expected_sections
    assert cfg["SensoryInputSystem"]["awake_duration"] == 300
    assert pytest.approx(0.01) == cfg["SalienceTagger"]["salience_decay"]

def test_load_nonexistent_config(tmp_path, monkeypatch):
    fake = tmp_path / "nope.json"
    monkeypatch.setenv("SIMULATION_CONFIG_PATH", str(fake))
    mod = reload_config_module()
    cfg = mod.load_config()
    assert isinstance(cfg, dict)
    assert set(cfg.keys()) == set(mod.default_config().keys())

def test_load_existing_config(tmp_path, monkeypatch):
    sample = {"SalienceTagger": {"salience_decay": 0.05}}
    cfg_file = tmp_path / "sim.json"
    cfg_file.write_text(json.dumps(sample))
    monkeypatch.setenv("SIMULATION_CONFIG_PATH", str(cfg_file))
    mod = reload_config_module()
    cfg = mod.load_config()
    assert isinstance(cfg, dict)
    assert cfg["SalienceTagger"]["salience_decay"] == 0.05
    assert "SensoryInputSystem" in cfg

def test_save_and_reload_configuration(tmp_path, monkeypatch):
    out = tmp_path / "cfgdir"
    out.mkdir()
    cfg_file = out / "simulation_config.json"
    monkeypatch.setenv("SIMULATION_CONFIG_PATH", str(cfg_file))
    mod = reload_config_module()
    new_cfg = mod.default_config()
    new_cfg["SalienceTagger"]["salience_decay"] = 0.123
    mod.save_config(new_cfg)
    reloaded = mod.load_config()
    assert pytest.approx(0.123) == reloaded["SalienceTagger"]["salience_decay"]