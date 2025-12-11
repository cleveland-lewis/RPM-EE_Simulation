import numpy as np
import pandas as pd
import pytest

from src.validation_metrics import compute_action_execution_auc, compute_icc


def _make_action_df():
    rows = []
    for subj_id, offset in [("s1", 0.0), ("s2", 0.05)]:
        attunement = np.linspace(0.05, 0.95, 20)
        executed = (attunement + offset >= 0.50).astype(int)
        for score, action in zip(attunement, executed):
            rows.append(
                {
                    "participant": subj_id,
                    "attunement_score": float(score),
                    "action_executed": int(action),
                }
            )
    return pd.DataFrame(rows)


def test_compute_action_execution_auc_produces_expected_curve_and_success():
    df = _make_action_df()

    result = compute_action_execution_auc(df, attunement_col="attunement_score", action_col="action_executed")

    assert result["success"] is True
    assert result["n_participants"] == 2
    assert pytest.approx(result["auc_mean"], rel=1e-6) == 1.0
    assert pytest.approx(result["auc_std"], abs=1e-6) == 0.0
    assert pytest.approx(result["auc_global"], rel=1e-4) == 0.9987468671
    assert result["p"] < 1e-6
    assert result["fpr"] is not None and result["tpr"] is not None
    assert min(result["fpr"]) == 0.0
    assert max(result["tpr"]) == 1.0


def test_compute_icc_returns_zero_for_state_like_measurements():
    values = np.tile(np.linspace(0.1, 0.6, 6), 3)
    df = pd.DataFrame(
        {
            "participant": np.repeat(["p1", "p2", "p3"], 6),
            "attunement_score": values,
        }
    )

    icc = compute_icc(df, value_col="attunement_score", subject_col="participant")

    assert 0.0 <= icc <= 0.05


def test_compute_icc_returns_one_for_trait_like_measurements():
    df = pd.DataFrame(
        {
            "participant": np.repeat(["p1", "p2", "p3"], 5),
            "attunement_score": np.concatenate(
                [np.full(5, 0.1), np.full(5, 0.5), np.full(5, 0.9)]
            ),
        }
    )

    icc = compute_icc(df, value_col="attunement_score", subject_col="participant")

    assert pytest.approx(icc, rel=1e-6) == 1.0
