import numpy as np
import pytest
import xarray as xr
import arviz as az


def _require_sim():
    try:
        import src.simulation as sim
        return sim
    except ImportError as exc:
        pytest.skip(f"simulation import skipped: {exc}", allow_module_level=True)


def _make_ppc(samples):
    data = xr.DataArray(samples, dims=("chain", "draw", "obs"))
    return type("PPC", (), {"posterior_predictive": {"C_obs": data}})


def test_validate_fit_nc_mcm_inputs_rejects_invalid_runs():
    sim = _require_sim()
    with pytest.raises(ValueError):
        sim._validate_fit_nc_mcm_inputs(
            runs=0,
            workers=1,
            draws=10,
            tune=10,
            chains=1,
            cores=1,
            target_accept=0.9,
            max_treedepth=10,
            sim_overrides=None,
        )


def test_compute_rmse_ci_matches_expected_values():
    sim = _require_sim()
    observed = np.array([0.0, 1.0])
    samples = np.array([
        [[0.0, 1.0], [0.0, 1.0]],  # chain 0 matches observed -> rmse 0
        [[1.0, 2.0], [1.0, 2.0]],  # chain 1 offset by 1 -> rmse 1
    ])
    rmse_mean, rmse_ci = sim._compute_rmse_ci(_make_ppc(samples), observed)
    assert np.isclose(rmse_mean, 0.5)
    assert np.allclose(rmse_ci, [0.025, 0.975])  # quantiles of [0, 1]


def test_check_rhat_reports_perfect_convergence(caplog):
    sim = _require_sim()
    trace = az.from_dict(posterior={"a": np.ones((2, 5))})
    max_rhat = sim._check_rhat(trace, threshold=1.05)
    assert np.isclose(max_rhat, 1.0)


def test_extract_data_runwise_zscores_and_shapes():
    import src.nc_mcm_model as nc

    logs = [
        {"schema_stress": 1, "attunement_score": 1, "prediction_error": 0.2, "selection_confidence": 0.1, "ext_load": 1, "mem_load": 2, "affect_volatility": 0.3, "stage_2_salience": 0.5},
        {"schema_stress": 3, "attunement_score": 3, "prediction_error": 0.4, "selection_confidence": 0.3, "ext_load": 3, "mem_load": 4, "affect_volatility": 0.7, "stage_2_salience": 0.7},
        {"schema_stress": 10, "attunement_score": 5, "prediction_error": 1.0, "selection_confidence": 0.2, "ext_load": 5, "mem_load": 8, "affect_volatility": 0.9, "stage_2_salience": 0.1},
        {"schema_stress": 12, "attunement_score": 7, "prediction_error": 1.2, "selection_confidence": 0.4, "ext_load": 7, "mem_load": 10, "affect_volatility": 1.1, "stage_2_salience": 0.3},
    ]
    run_idx = np.array([0, 0, 1, 1], dtype=int)

    data = nc.extract_data(logs, run_idx)

    # Shapes and keys present
    for key in ["N_z", "N2c_z", "G_z", "L_z", "C_z", "SC_z", "SA_z", "run_idx"]:
        assert key in data
        assert data[key].shape == (4,)

    # Runwise z-scoring: first run stress values [1,3] -> z = [-1, 1]; second run [10,12] -> [-1, 1]
    assert np.allclose(data["N_z"], [-1.0, 1.0, -1.0, 1.0], atol=1e-6)
    # Runwise log-normalized mem_load: runs [2,4] and [8,10] should center to zero mean per run
    assert np.isclose(float(data["L_z"][:2].mean()), 0.0, atol=1e-6)
    assert np.isclose(float(data["L_z"][2:].mean()), 0.0, atol=1e-6)


def test_extract_data_raises_on_mismatched_run_idx_length():
    import src.nc_mcm_model as nc

    logs = [{"schema_stress": 1, "attunement_score": 1, "prediction_error": 0.2, "selection_confidence": 0.1, "ext_load": 1, "mem_load": 2, "affect_volatility": 0.3, "stage_2_salience": 0.5}]
    with pytest.raises(ValueError):
        nc.extract_data(logs, run_idx=np.array([0, 0]))
