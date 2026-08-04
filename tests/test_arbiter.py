"""
Unit tests for SimulationClusterArbiter (issue #44).

Tests cover:
1. score_simulations: final_score equals weighted sum of t1/t2/t3 with defaults
2. score_simulations: fatigue_flag suppresses reward_distortion when it exceeds 0.5
3. sort_simulations: descending order by final_score, stable tie-breaking
4. Missing-key behavior: absent plausibility/emotional_prediction/reward_distortion
   default to 0.0 rather than raising
"""

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from arbiter import SimulationClusterArbiter  # noqa: E402


class TestScoreSimulationsBasic:
    def test_final_score_is_weighted_sum_with_default_weights(self):
        arbiter = SimulationClusterArbiter()
        sims = [{"plausibility": 0.8, "emotional_prediction": 0.4, "reward_distortion": 0.1}]

        result = arbiter.score_simulations(sims)

        expected = 0.5 * 0.8 + 0.3 * 0.4 + 0.2 * 0.1
        assert result[0]["final_score"] == pytest.approx(round(expected, 3))

    def test_final_score_uses_custom_weights(self):
        arbiter = SimulationClusterArbiter(alpha=1.0, beta=0.0, gamma=0.0)
        sims = [{"plausibility": 0.6, "emotional_prediction": 0.9, "reward_distortion": 0.9}]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(0.6)

    def test_final_score_is_rounded_to_three_decimals(self):
        arbiter = SimulationClusterArbiter()
        sims = [{"plausibility": 1 / 3, "emotional_prediction": 1 / 3, "reward_distortion": 1 / 3}]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == round(result[0]["final_score"], 3)

    def test_scores_multiple_simulations_independently(self):
        arbiter = SimulationClusterArbiter()
        sims = [
            {"plausibility": 1.0, "emotional_prediction": 0.0, "reward_distortion": 0.0},
            {"plausibility": 0.0, "emotional_prediction": 1.0, "reward_distortion": 0.0},
        ]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(0.5)
        assert result[1]["final_score"] == pytest.approx(0.3)

    def test_returns_the_same_list_object(self):
        arbiter = SimulationClusterArbiter()
        sims = [{"plausibility": 0.5}]

        result = arbiter.score_simulations(sims)

        assert result is sims


class TestFatigueSuppression:
    def test_fatigue_flag_suppresses_reward_distortion_above_threshold(self):
        arbiter = SimulationClusterArbiter()
        sims = [
            {
                "plausibility": 0.0,
                "emotional_prediction": 0.0,
                "reward_distortion": 0.9,
                "fatigue_flag": True,
            }
        ]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(0.0)

    def test_fatigue_flag_does_not_suppress_at_or_below_threshold(self):
        arbiter = SimulationClusterArbiter()
        sims = [
            {
                "plausibility": 0.0,
                "emotional_prediction": 0.0,
                "reward_distortion": 0.5,
                "fatigue_flag": True,
            }
        ]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(0.5 * 0.2)

    def test_reward_distortion_not_suppressed_without_fatigue_flag(self):
        arbiter = SimulationClusterArbiter()
        sims = [{"plausibility": 0.0, "emotional_prediction": 0.0, "reward_distortion": 0.9}]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(round(0.9 * 0.2, 3))

    def test_fatigue_flag_false_does_not_suppress(self):
        arbiter = SimulationClusterArbiter()
        sims = [
            {
                "plausibility": 0.0,
                "emotional_prediction": 0.0,
                "reward_distortion": 0.9,
                "fatigue_flag": False,
            }
        ]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(round(0.9 * 0.2, 3))


class TestSortSimulations:
    def test_sorts_descending_by_final_score(self):
        arbiter = SimulationClusterArbiter()
        sims = [
            {"final_score": 0.2},
            {"final_score": 0.9},
            {"final_score": 0.5},
        ]

        result = arbiter.sort_simulations(sims)

        assert [s["final_score"] for s in result] == [0.9, 0.5, 0.2]

    def test_tie_breaking_preserves_original_relative_order(self):
        arbiter = SimulationClusterArbiter()
        sims = [
            {"id": "a", "final_score": 0.5},
            {"id": "b", "final_score": 0.5},
            {"id": "c", "final_score": 0.9},
        ]

        result = arbiter.sort_simulations(sims)

        assert [s["id"] for s in result] == ["c", "a", "b"]

    def test_missing_final_score_defaults_to_zero_and_sorts_last(self):
        arbiter = SimulationClusterArbiter()
        sims = [{"id": "has_score", "final_score": 0.1}, {"id": "no_score"}]

        result = arbiter.sort_simulations(sims)

        assert [s["id"] for s in result] == ["has_score", "no_score"]

    def test_does_not_mutate_input_list_order(self):
        arbiter = SimulationClusterArbiter()
        sims = [{"final_score": 0.1}, {"final_score": 0.9}]

        arbiter.sort_simulations(sims)

        assert [s["final_score"] for s in sims] == [0.1, 0.9]


class TestMissingKeyDefaults:
    """score_simulations has no key-validation feature; missing keys silently default to 0.0."""

    def test_empty_sim_dict_scores_to_zero(self):
        arbiter = SimulationClusterArbiter()
        sims: list[dict[str, Any]] = [{}]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(0.0)

    def test_partial_sim_dict_defaults_missing_keys_to_zero(self):
        arbiter = SimulationClusterArbiter()
        sims = [{"plausibility": 0.4}]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(round(0.5 * 0.4, 3))

    def test_fatigue_flag_without_reward_distortion_is_a_no_op(self):
        arbiter = SimulationClusterArbiter()
        sims = [{"fatigue_flag": True}]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(0.0)
