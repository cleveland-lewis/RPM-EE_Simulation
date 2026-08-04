"""
Unit tests for SelfModel.evaluate_simulations (issue #60).

Tests cover:
1. Fallback (non-Bayesian) mismatch scoring
2. Bayesian PE mismatch scoring and belief-update passthrough
3. Schema stress ramp/decay based on mismatch magnitude
4. Schema filtering penalty applied to final_score
5. Verbose arbiter_debug payload (issue #58)
"""

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from selfmodel import _STRESS_TRIGGER_MISMATCH, SelfModel  # noqa: E402


class TestFallbackMismatchScoring:
    """No Bayesian PE configured: plain |actual - expected| mismatch."""

    def test_mismatch_is_abs_difference_from_baseline(self):
        model = SelfModel()
        model.emotion_baseline = 0.2
        sims = [{"emotional_prediction": 0.5}]

        result = model.evaluate_simulations(sims)

        assert result[0]["schema_mismatch"] == pytest.approx(0.3)

    def test_missing_emotional_prediction_defaults_to_zero(self):
        model = SelfModel()
        model.emotion_baseline = 0.4
        sims: list[dict[str, Any]] = [{}]

        result = model.evaluate_simulations(sims)

        assert result[0]["schema_mismatch"] == pytest.approx(0.4)

    def test_does_not_attach_bayesian_pe_fields(self):
        model = SelfModel()
        sims = [{"emotional_prediction": 0.1}]

        result = model.evaluate_simulations(sims)

        for key in ("pe_sensory", "pe_state", "volatility", "precision_ratio"):
            assert key not in result[0]


class TestBayesianPEMismatchScoring:
    """Bayesian PE configured: mismatch derived from update_beliefs()."""

    def _configured_model(self):
        model = SelfModel()
        model.configure_bayesian_pe(
            {
                "sensory_precision": 1.0,
                "prior_precision": 1.0,
                "volatile_precision": 0.5,
                "precision_learning_rate": 0.1,
            }
        )
        return model

    def test_schema_mismatch_matches_bayesian_pe_total(self):
        precision_model = self._configured_model()
        sims = [{"emotional_prediction": 0.5, "confidence": 0.8}]

        expected_pe_total = precision_model.bayesian_pe.update_beliefs(
            observation=0.5, observation_precision=0.8
        )["pe_total"]

        model = self._configured_model()
        result = model.evaluate_simulations(sims)

        assert result[0]["schema_mismatch"] == pytest.approx(abs(expected_pe_total))

    def test_attaches_pe_component_fields(self):
        model = self._configured_model()
        sims = [{"emotional_prediction": 0.3, "confidence": 0.5}]

        result = model.evaluate_simulations(sims)

        for key in ("pe_sensory", "pe_state", "volatility", "precision_ratio"):
            assert key in result[0]

    def test_missing_confidence_defaults_observation_precision(self):
        model = self._configured_model()
        sims = [{"emotional_prediction": 0.3}]

        # Should not raise despite missing "confidence" key.
        result = model.evaluate_simulations(sims)

        assert "schema_mismatch" in result[0]


class TestSchemaStressUpdate:
    """schema_stress ramps on large mismatch, decays otherwise."""

    def test_stress_ramps_above_trigger(self):
        model = SelfModel()
        model.emotion_baseline = 0.0
        sims = [{"emotional_prediction": _STRESS_TRIGGER_MISMATCH + 0.1}]

        model.evaluate_simulations(sims)

        assert model.schema_stress == pytest.approx(0.1)

    def test_stress_decays_at_or_below_trigger(self):
        model = SelfModel()
        model.emotion_baseline = 0.0
        model.schema_stress = 0.5
        sims = [{"emotional_prediction": _STRESS_TRIGGER_MISMATCH - 0.1}]

        model.evaluate_simulations(sims)

        assert model.schema_stress == pytest.approx(0.5 * 0.95)

    def test_stress_accumulates_across_multiple_sims(self):
        model = SelfModel()
        model.emotion_baseline = 0.0
        sims = [
            {"emotional_prediction": _STRESS_TRIGGER_MISMATCH + 0.1},
            {"emotional_prediction": _STRESS_TRIGGER_MISMATCH + 0.2},
        ]

        model.evaluate_simulations(sims)

        assert model.schema_stress == pytest.approx(0.2)


class TestSchemaFiltering:
    """schema_filtered_score penalizes implausible simulations."""

    def test_perfectly_plausible_sim_has_no_penalty(self):
        model = SelfModel()
        sims = [{"emotional_prediction": 0.0, "final_score": 0.9, "plausibility": 1.0}]

        result = model.evaluate_simulations(sims)

        assert result[0]["schema_filtered_score"] == pytest.approx(0.9)

    def test_implausible_sim_is_penalized(self):
        model = SelfModel()
        realism_bias = model.traits["realism_bias"]
        sims = [{"emotional_prediction": 0.0, "final_score": 0.9, "plausibility": 0.0}]

        result = model.evaluate_simulations(sims)

        assert result[0]["schema_filtered_score"] == pytest.approx(max(0.0, 0.9 - realism_bias))

    def test_score_is_floored_at_zero(self):
        model = SelfModel()
        sims = [{"emotional_prediction": 0.0, "final_score": 0.1, "plausibility": 0.0}]

        result = model.evaluate_simulations(sims)

        assert result[0]["schema_filtered_score"] == 0.0

    def test_missing_plausibility_and_final_score_default_to_zero(self):
        model = SelfModel()
        sims = [{"emotional_prediction": 0.0}]

        result = model.evaluate_simulations(sims)

        assert result[0]["schema_filtered_score"] == 0.0


class TestVerboseDebugPayload:
    """arbiter_debug is only attached when verbose=True (issue #58)."""

    def test_no_debug_payload_by_default(self):
        model = SelfModel()
        sims = [{"emotional_prediction": 0.0, "final_score": 0.5}]

        result = model.evaluate_simulations(sims)

        assert "arbiter_debug" not in result[0]

    def test_debug_payload_present_when_verbose(self):
        model = SelfModel(verbose=True)
        sims = [{"emotional_prediction": 0.2, "final_score": 0.5, "fatigue_flag": True}]

        result = model.evaluate_simulations(sims)

        debug = result[0]["arbiter_debug"]
        assert debug["final_score"] == pytest.approx(0.5)
        assert debug["mismatch"] == pytest.approx(0.2)
        assert debug["suppressed"] is True

    def test_debug_payload_pe_fields_none_without_bayesian_pe(self):
        model = SelfModel(verbose=True)
        sims = [{"emotional_prediction": 0.1, "final_score": 0.0}]

        result = model.evaluate_simulations(sims)

        debug = result[0]["arbiter_debug"]
        assert debug["pe_sensory"] is None
        assert debug["pe_state"] is None
        assert debug["volatility"] is None


class TestEmotionBaselineUpdate:
    def test_exponential_moving_average(self):
        model = SelfModel()
        model.emotion_baseline = 1.0

        model.update_emotion_baseline(0.0)

        assert model.emotion_baseline == pytest.approx(0.8)


class TestUpdateStressFromMismatchHelper:
    """_update_stress_from_mismatch (issue #57) targeted in isolation."""

    def test_ramps_above_trigger(self):
        model = SelfModel()

        model._update_stress_from_mismatch(_STRESS_TRIGGER_MISMATCH + 0.01)

        assert model.schema_stress == pytest.approx(0.1)

    def test_decays_at_trigger_boundary(self):
        model = SelfModel()
        model.schema_stress = 1.0

        model._update_stress_from_mismatch(_STRESS_TRIGGER_MISMATCH)

        assert model.schema_stress == pytest.approx(0.95)

    def test_decays_below_trigger(self):
        model = SelfModel()
        model.schema_stress = 1.0

        model._update_stress_from_mismatch(0.0)

        assert model.schema_stress == pytest.approx(0.95)

    def test_repeated_calls_accumulate(self):
        model = SelfModel()

        for _ in range(3):
            model._update_stress_from_mismatch(_STRESS_TRIGGER_MISMATCH + 0.1)

        assert model.schema_stress == pytest.approx(0.3)


class TestMissingKeyValidation:
    """on_missing_keys controls behavior when required sim keys are absent (issue #57)."""

    def test_invalid_mode_raises_at_construction(self):
        with pytest.raises(ValueError):
            SelfModel(on_missing_keys="bogus")

    def test_default_mode_is_warn(self):
        model = SelfModel()
        assert model.on_missing_keys == "warn"

    def test_ignore_mode_is_silent(self, recwarn):
        model = SelfModel(on_missing_keys="ignore")
        sims: list[dict[str, Any]] = [{}]

        model.evaluate_simulations(sims)

        assert len(recwarn) == 0

    def test_warn_mode_emits_warning_and_still_defaults(self):
        model = SelfModel(on_missing_keys="warn")
        sims: list[dict[str, Any]] = [{}]

        with pytest.warns(UserWarning, match="missing required keys"):
            result = model.evaluate_simulations(sims)

        assert result[0]["schema_mismatch"] == pytest.approx(0.0)

    def test_error_mode_raises_on_missing_key(self):
        model = SelfModel(on_missing_keys="error")
        sims = [{"emotional_prediction": 0.5}]  # missing "plausibility"

        with pytest.raises(KeyError, match="plausibility"):
            model.evaluate_simulations(sims)

    def test_error_mode_passes_when_all_keys_present(self):
        model = SelfModel(on_missing_keys="error")
        sims = [{"emotional_prediction": 0.5, "plausibility": 1.0}]

        result = model.evaluate_simulations(sims)

        assert result[0]["schema_mismatch"] == pytest.approx(0.5)

    def test_warn_mode_lists_all_missing_keys(self):
        model = SelfModel(on_missing_keys="warn")
        sims: list[dict[str, Any]] = [{}]

        with pytest.warns(UserWarning) as record:
            model.evaluate_simulations(sims)

        message = str(record[0].message)
        assert "emotional_prediction" in message
        assert "plausibility" in message
