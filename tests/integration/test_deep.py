import numpy as np

from src.randomness import seed_everything
from src.simulation import run_simulation
from src.trial_wrapper import TrialSimulator
from src import nc_mcm_model


def test_simulation_signal_ranges_deep():
    out = run_simulation(total_ticks=60, seed=111, bin_size=1)
    logs = out["logs"]

    att = [log["attunement_score"] for log in logs]
    stress = [log["schema_stress"] for log in logs]
    ext = [log["ext_load"] for log in logs]
    mem = [log["mem_load"] for log in logs]

    assert all(0.0 <= a <= 1.0 for a in att), "Attunement outside [0,1]"
    assert all(s >= 0.0 for s in stress), "Stress negative"
    assert all(0.0 <= e <= 1.0 for e in ext), "External load outside [0,1]"
    assert all(0.0 <= m <= 1.0 for m in mem), "Memory load outside [0,1]"
    assert len(logs) == 60, "Log length mismatch"
    # Diagnostics should carry replay rates and seed
    diag = out["diagnostics"]
    assert "replay_mode_rates" in diag and "seed" in diag


def test_trial_wrapper_learning_deep():
    sim = TrialSimulator(preset="default", seed=42, enable_learning=True, learning_rate=0.2)
    trial1 = sim.run_trial({"ext_load_target": 0.3, "mem_load_target": 0.2}, duration=30)
    trial2 = sim.run_trial({"ext_load_target": 0.6, "mem_load_target": 0.5}, duration=30)

    history = sim.get_history()
    assert len(history) == 2, "Trial history length mismatch"
    assert trial1["seed"] != trial2["seed"], "Seeds should increment per trial"
    for t in history:
        assert 0.0 <= t["accuracy"] <= 1.0, "Accuracy outside [0,1]"
        assert 0.0 <= t["p_correct"] <= 1.0, "p_correct outside [0,1]"
        assert isinstance(t["RT"], float), "RT not recorded"


def test_nc_mcm_extract_data_full_shapes():
    base = seed_everything(333).master_seed
    logs, run_idx = nc_mcm_model.run_multiple_simulations(n_runs=2, workers=1, base_seed=base)
    data = nc_mcm_model.extract_data(logs, run_idx)

    n = data["C_z"].shape[0]
    assert n > 0, "No data extracted"
    for key in ("C_z", "G_z", "L_z", "N_z", "run_idx"):
        assert data[key].shape[0] == n, f"{key} length mismatch"
    # Z-scored arrays should have finite values
    for key in ("C_z", "G_z", "L_z", "N_z"):
        arr = data[key]
        assert np.isfinite(arr).all(), f"{key} contains non-finite values"


def test_run_multiple_simulations_isolates_runs():
    base = seed_everything(444).master_seed
    logs, run_idx = nc_mcm_model.run_multiple_simulations(n_runs=3, workers=1, base_seed=base)
    unique_runs = set(run_idx.tolist())
    assert unique_runs == {0, 1, 2}, "Run indices not isolated per run"
    counts = {r: run_idx.tolist().count(r) for r in unique_runs}
    assert all(c > 0 for c in counts.values()), "Missing logs for a run"


def test_seed_everything_distribution():
    streams = seed_everything(777)
    children = streams.spawn(5)
    assert len(set(children)) == 5, "Spawned child seeds are not unique"
    # Master seed should remain stable
    assert streams.master_seed == 777
