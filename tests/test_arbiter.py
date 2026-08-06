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
import warnings
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


class TestFatigueDistortionSuppressThreshold:
    """fatigue_distortion_suppress_threshold is configurable (issue #48)."""

    def test_default_threshold_is_one_half(self):
        arbiter = SimulationClusterArbiter()

        assert arbiter.fatigue_distortion_suppress_threshold == 0.5

    def test_custom_threshold_suppresses_just_above_it(self):
        arbiter = SimulationClusterArbiter(fatigue_distortion_suppress_threshold=0.3)
        sims = [
            {
                "plausibility": 0.0,
                "emotional_prediction": 0.0,
                "reward_distortion": 0.31,
                "fatigue_flag": True,
            }
        ]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(0.0)

    def test_custom_threshold_does_not_suppress_just_below_it(self):
        arbiter = SimulationClusterArbiter(fatigue_distortion_suppress_threshold=0.3)
        sims = [
            {
                "plausibility": 0.0,
                "emotional_prediction": 0.0,
                "reward_distortion": 0.29,
                "fatigue_flag": True,
            }
        ]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(round(0.2 * 0.29, 3))

    def test_custom_threshold_does_not_suppress_exactly_at_it(self):
        arbiter = SimulationClusterArbiter(fatigue_distortion_suppress_threshold=0.3)
        sims = [
            {
                "plausibility": 0.0,
                "emotional_prediction": 0.0,
                "reward_distortion": 0.3,
                "fatigue_flag": True,
            }
        ]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(round(0.2 * 0.3, 3))

    def test_lower_threshold_suppresses_a_value_the_default_would_not(self):
        # reward_distortion=0.4 is below the default 0.5 threshold (not suppressed)
        # but above a custom 0.3 threshold (suppressed) -- demonstrates the
        # threshold actually changes final_score, not just internal state.
        default_arbiter = SimulationClusterArbiter()
        custom_arbiter = SimulationClusterArbiter(fatigue_distortion_suppress_threshold=0.3)
        sim = {
            "plausibility": 0.0,
            "emotional_prediction": 0.0,
            "reward_distortion": 0.4,
            "fatigue_flag": True,
        }

        default_result = default_arbiter.score_simulations([dict(sim)])
        custom_result = custom_arbiter.score_simulations([dict(sim)])

        assert default_result[0]["final_score"] == pytest.approx(round(0.2 * 0.4, 3))
        assert custom_result[0]["final_score"] == pytest.approx(0.0)


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

    def test_equal_final_score_broken_by_higher_plausibility(self):
        arbiter = SimulationClusterArbiter()
        sims = [
            {"id": "low_plausibility", "final_score": 0.5, "plausibility": 0.2},
            {"id": "high_plausibility", "final_score": 0.5, "plausibility": 0.8},
        ]

        result = arbiter.sort_simulations(sims)

        assert [s["id"] for s in result] == ["high_plausibility", "low_plausibility"]

    def test_equal_final_score_and_plausibility_broken_by_emotional_prediction(self):
        arbiter = SimulationClusterArbiter()
        sims = [
            {
                "id": "low_emotion",
                "final_score": 0.5,
                "plausibility": 0.5,
                "emotional_prediction": 0.1,
            },
            {
                "id": "high_emotion",
                "final_score": 0.5,
                "plausibility": 0.5,
                "emotional_prediction": 0.9,
            },
        ]

        result = arbiter.sort_simulations(sims)

        assert [s["id"] for s in result] == ["high_emotion", "low_emotion"]

    def test_tie_break_order_is_independent_of_input_order(self):
        # Same simulations, reversed input order -- output must match, proving
        # the ordering doesn't depend on upstream/input ordering.
        arbiter = SimulationClusterArbiter()
        low = {"id": "low_plausibility", "final_score": 0.5, "plausibility": 0.2}
        high = {"id": "high_plausibility", "final_score": 0.5, "plausibility": 0.8}

        result_forward = arbiter.sort_simulations([dict(low), dict(high)])
        result_reversed = arbiter.sort_simulations([dict(high), dict(low)])

        assert [s["id"] for s in result_forward] == ["high_plausibility", "low_plausibility"]
        assert [s["id"] for s in result_reversed] == ["high_plausibility", "low_plausibility"]

    def test_fully_tied_simulations_still_preserve_input_order(self):
        arbiter = SimulationClusterArbiter()
        sims = [
            {"id": "a", "final_score": 0.5, "plausibility": 0.3, "emotional_prediction": 0.1},
            {"id": "b", "final_score": 0.5, "plausibility": 0.3, "emotional_prediction": 0.1},
        ]

        result = arbiter.sort_simulations(sims)

        assert [s["id"] for s in result] == ["a", "b"]

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


class TestNormalizeInputs:
    """normalize_inputs min-max scales t1/t2/t3 to [0, 1] across the batch (issue #38)."""

    def test_off_by_default_uses_raw_values(self):
        arbiter = SimulationClusterArbiter()
        sims = [{"plausibility": 0.6, "emotional_prediction": -0.4, "reward_distortion": 2.0}]

        result = arbiter.score_simulations(sims)

        expected = 0.5 * 0.6 + 0.3 * -0.4 + 0.2 * 2.0
        assert result[0]["final_score"] == pytest.approx(round(expected, 3))

    def test_scales_min_to_zero_and_max_to_one_within_batch(self):
        arbiter = SimulationClusterArbiter(normalize_inputs=True, alpha=1.0, beta=0.0, gamma=0.0)
        sims = [
            {"plausibility": 0.5},
            {"plausibility": 1.0},
            {"plausibility": 0.75},
        ]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(0.0)
        assert result[1]["final_score"] == pytest.approx(1.0)
        assert result[2]["final_score"] == pytest.approx(0.5)

    def test_all_equal_values_map_to_neutral_midpoint_without_division_by_zero(self):
        arbiter = SimulationClusterArbiter(normalize_inputs=True, alpha=1.0, beta=0.0, gamma=0.0)
        sims = [{"plausibility": 0.7}, {"plausibility": 0.7}]

        result = arbiter.score_simulations(sims)

        assert result[0]["final_score"] == pytest.approx(0.5)
        assert result[1]["final_score"] == pytest.approx(0.5)

    def test_empty_simulation_list_does_not_raise(self):
        arbiter = SimulationClusterArbiter(normalize_inputs=True)

        result = arbiter.score_simulations([])

        assert result == []

    def test_different_input_scales_yield_comparable_scores_for_same_relative_pattern(self):
        # Same relative pattern (lowest/middle/highest), very different absolute
        # scales -- normalized final_scores should match despite that.
        small_scale = SimulationClusterArbiter(normalize_inputs=True, alpha=1.0, beta=0, gamma=0)
        large_scale = SimulationClusterArbiter(normalize_inputs=True, alpha=1.0, beta=0, gamma=0)
        small_sims = [
            {"plausibility": 0.1},
            {"plausibility": 0.2},
            {"plausibility": 0.3},
        ]
        large_sims = [
            {"plausibility": 100.0},
            {"plausibility": 200.0},
            {"plausibility": 300.0},
        ]

        small_result = small_scale.score_simulations(small_sims)
        large_result = large_scale.score_simulations(large_sims)

        small_scores = [s["final_score"] for s in small_result]
        large_scores = [s["final_score"] for s in large_result]
        assert small_scores == pytest.approx(large_scores)

    def test_fatigue_suppression_still_applies_after_normalization(self):
        arbiter = SimulationClusterArbiter(normalize_inputs=True, alpha=0, beta=0, gamma=1.0)
        sims = [
            {"reward_distortion": 0.0, "fatigue_flag": True},
            {"reward_distortion": 10.0, "fatigue_flag": True},
        ]

        result = arbiter.score_simulations(sims)

        # normalized: sim 0 -> t3=0.0 (below threshold, kept); sim 1 -> t3=1.0
        # (above threshold, suppressed to 0.0)
        assert result[0]["final_score"] == pytest.approx(0.0)
        assert result[1]["final_score"] == pytest.approx(0.0)


class TestValidateKeys:
    """validate_keys surfaces missing required sim keys instead of silent 0.0s (issue #41)."""

    def test_off_by_default_no_warning_on_missing_keys(self):
        arbiter = SimulationClusterArbiter()
        sims: list[dict[str, Any]] = [{}]

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = arbiter.score_simulations(sims)  # must not raise

        assert result[0]["final_score"] == pytest.approx(0.0)

    def test_validate_keys_warns_on_missing_key_by_default(self):
        arbiter = SimulationClusterArbiter(validate_keys=True)
        sims = [{"plausibility": 0.5, "emotional_prediction": 0.1}]  # missing reward_distortion

        with pytest.warns(UserWarning, match="reward_distortion"):
            result = arbiter.score_simulations(sims)

        # still falls back to 0.0 and scores normally after warning
        assert result[0]["final_score"] == pytest.approx(round(0.5 * 0.5 + 0.3 * 0.1, 3))

    def test_validate_keys_warning_lists_all_missing_keys(self):
        arbiter = SimulationClusterArbiter(validate_keys=True)
        sims: list[dict[str, Any]] = [{}]

        with pytest.warns(UserWarning) as record:
            arbiter.score_simulations(sims)

        message = str(record[0].message)
        for key in ("plausibility", "emotional_prediction", "reward_distortion"):
            assert key in message

    def test_validate_keys_does_not_warn_about_missing_fatigue_flag(self):
        arbiter = SimulationClusterArbiter(validate_keys=True)
        sims = [
            {"plausibility": 0.5, "emotional_prediction": 0.1, "reward_distortion": 0.2}
        ]  # no fatigue_flag -- legitimate, not a data-quality issue

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = arbiter.score_simulations(sims)  # must not raise

        assert result[0]["final_score"] == pytest.approx(
            round(0.5 * 0.5 + 0.3 * 0.1 + 0.2 * 0.2, 3)
        )

    def test_on_missing_keys_raise_stops_scoring(self):
        arbiter = SimulationClusterArbiter(validate_keys=True, on_missing_keys="raise")
        sims: list[dict[str, Any]] = [{"plausibility": 0.5}]

        with pytest.raises(ValueError, match="emotional_prediction"):
            arbiter.score_simulations(sims)

        assert "final_score" not in sims[0]

    def test_validate_keys_checks_every_simulation_in_the_batch(self):
        arbiter = SimulationClusterArbiter(validate_keys=True)
        sims = [
            {"plausibility": 0.5, "emotional_prediction": 0.1, "reward_distortion": 0.2},
            {"plausibility": 0.5, "emotional_prediction": 0.1},  # missing reward_distortion
        ]

        with pytest.warns(UserWarning, match="index 1"):
            arbiter.score_simulations(sims)


class TestVerboseArbiterScoreDebug:
    """verbose attaches an arbiter_score_debug payload per sim (issue #42)."""

    def test_off_by_default_no_debug_payload(self):
        arbiter = SimulationClusterArbiter()
        sims = [{"plausibility": 0.5, "emotional_prediction": 0.1, "reward_distortion": 0.2}]

        result = arbiter.score_simulations(sims)

        assert "arbiter_score_debug" not in result[0]

    def test_verbose_attaches_component_values_and_final_score(self):
        arbiter = SimulationClusterArbiter(verbose=True)
        sims = [{"plausibility": 0.5, "emotional_prediction": 0.1, "reward_distortion": 0.2}]

        result = arbiter.score_simulations(sims)

        debug = result[0]["arbiter_score_debug"]
        assert debug["t1"] == pytest.approx(0.5)
        assert debug["t2"] == pytest.approx(0.1)
        assert debug["t3"] == pytest.approx(0.2)
        assert debug["fatigue_suppressed"] is False
        assert debug["final_score"] == result[0]["final_score"]

    def test_verbose_debug_reflects_fatigue_suppression(self):
        arbiter = SimulationClusterArbiter(verbose=True)
        sims = [
            {
                "plausibility": 0.0,
                "emotional_prediction": 0.0,
                "reward_distortion": 0.9,
                "fatigue_flag": True,
            }
        ]

        result = arbiter.score_simulations(sims)

        debug = result[0]["arbiter_score_debug"]
        assert debug["fatigue_suppressed"] is True
        assert debug["t3"] == pytest.approx(0.0)

    def test_verbose_debug_reflects_normalized_values(self):
        arbiter = SimulationClusterArbiter(verbose=True, normalize_inputs=True, alpha=1.0)
        sims = [{"plausibility": 0.5}, {"plausibility": 1.0}]

        result = arbiter.score_simulations(sims)

        assert result[0]["arbiter_score_debug"]["t1"] == pytest.approx(0.0)
        assert result[1]["arbiter_score_debug"]["t1"] == pytest.approx(1.0)

    def test_arbiter_score_debug_does_not_collide_with_selfmodel_arbiter_debug_key(self):
        arbiter = SimulationClusterArbiter(verbose=True)
        sims = [
            {
                "plausibility": 0.5,
                "emotional_prediction": 0.1,
                "reward_distortion": 0.2,
                "arbiter_debug": {"unrelated": "selfmodel payload"},
            }
        ]

        result = arbiter.score_simulations(sims)

        assert result[0]["arbiter_debug"] == {"unrelated": "selfmodel payload"}
        assert "arbiter_score_debug" in result[0]
