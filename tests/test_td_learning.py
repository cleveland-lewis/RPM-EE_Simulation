"""
Unit tests for Temporal Difference Learning implementation.

Tests verify that:
1. TD learner initializes correctly and learns values
2. Clinical presets show expected learning patterns
3. MDD shows persistent negative bias
4. ADHD shows high learning rate and delay aversion
5. Integration with EmotionalEncoder works correctly
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from emotion import EmotionalEncoder
from presets import CLINICAL_PRESETS
from td_learning import TemporalDifferenceLearner


class TestTDLearningBasics:
    """Test basic TD learning operations."""

    def test_initialization(self):
        """Verify TD learner initializes correctly."""
        td = TemporalDifferenceLearner(
            alpha=0.1, gamma=0.9, reward_sensitivity=1.0, initial_value=0.0
        )

        assert td.alpha == 0.1
        assert td.gamma == 0.9
        assert td.reward_sensitivity == 1.0
        assert td.initial_value == 0.0
        assert len(td.td_errors) == 0

    def test_value_computation(self):
        """Verify value computation for simulations."""
        td = TemporalDifferenceLearner()

        sim = {"emotion_intensity": 0.8, "plausibility": 0.6, "reward_distortion": 0.2}

        # Initial value should be initial_value (0.0)
        value = td.compute_value(sim)
        assert value == 0.0

    def test_value_update_returns_dict(self):
        """Verify update_value returns expected keys."""
        td = TemporalDifferenceLearner()

        sim = {"emotion_intensity": 0.7, "plausibility": 0.5, "reward_distortion": 0.1}

        result = td.update_value(sim, terminal=True)

        required_keys = ["value", "td_error", "reward", "alpha", "gamma"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_value_learning_convergence(self):
        """Verify values converge with repeated positive experiences."""
        td = TemporalDifferenceLearner(alpha=0.2, gamma=0.9)

        # Repeated high-reward simulation
        sim = {
            "emotion_intensity": 0.9,  # High emotion = high reward
            "plausibility": 0.8,
            "reward_distortion": 0.1,
        }

        # Update 50 times
        for _ in range(50):
            td.update_value(sim, terminal=True)

        # Value should increase substantially
        final_value = td.compute_value(sim)
        assert final_value > 0.5, f"Value {final_value} should increase with positive rewards"

    def test_td_error_tracking(self):
        """Verify TD errors are tracked correctly."""
        td = TemporalDifferenceLearner()

        sim = {"emotion_intensity": 0.6, "plausibility": 0.5, "reward_distortion": 0.0}

        # First update
        td.update_value(sim, terminal=True)
        assert len(td.td_errors) == 1

        # Second update
        td.update_value(sim, terminal=True)
        assert len(td.td_errors) == 2

        # TD errors should decrease as learning progresses
        assert abs(td.td_errors[-1]) < abs(td.td_errors[0])


class TestClinicalDifferentiation:
    """Test that clinical presets show expected learning patterns."""

    def test_mdd_negative_bias(self):
        """MDD should start with negative bias and show blunted learning."""
        mdd_params = CLINICAL_PRESETS["mdd_typical"]
        td_mdd = TemporalDifferenceLearner(
            alpha=mdd_params["td_alpha"],
            gamma=mdd_params["td_gamma"],
            initial_value=mdd_params["td_initial_value"],
        )

        # Positive simulation
        sim = {"emotion_intensity": 0.8, "plausibility": 0.7, "reward_distortion": 0.0}

        # Initial value should be negative (pessimistic bias)
        initial_value = td_mdd.compute_value(sim)
        assert initial_value < 0, f"MDD initial value {initial_value} should be negative"

        # After 20 updates, value should increase but remain low (blunted learning)
        for _ in range(20):
            td_mdd.update_value(sim, terminal=True)

        mdd_value = td_mdd.compute_value(sim)

        # Compare with NT
        nt_params = CLINICAL_PRESETS["neurotypical"]
        td_nt = TemporalDifferenceLearner(
            alpha=nt_params["td_alpha"],
            gamma=nt_params["td_gamma"],
            initial_value=nt_params["td_initial_value"],
        )
        for _ in range(20):
            td_nt.update_value(sim, terminal=True)
        nt_value = td_nt.compute_value(sim)

        # MDD should have lower learned value (pessimistic + slow learning)
        assert (
            mdd_value < nt_value
        ), f"MDD value {mdd_value:.2f} should be lower than NT {nt_value:.2f}"

    def test_adhd_high_learning_rate(self):
        """ADHD should show fast learning (high alpha)."""
        adhd_params = CLINICAL_PRESETS["adhd_typical"]
        nt_params = CLINICAL_PRESETS["neurotypical"]

        td_adhd = TemporalDifferenceLearner(
            alpha=adhd_params["td_alpha"],
            gamma=adhd_params["td_gamma"],
            initial_value=adhd_params["td_initial_value"],
        )
        td_nt = TemporalDifferenceLearner(
            alpha=nt_params["td_alpha"],
            gamma=nt_params["td_gamma"],
            initial_value=nt_params["td_initial_value"],
        )

        # Single high-reward experience
        sim = {"emotion_intensity": 0.9, "plausibility": 0.6, "reward_distortion": 0.1}

        td_adhd.update_value(sim, terminal=True)
        td_nt.update_value(sim, terminal=True)

        adhd_value = td_adhd.compute_value(sim)
        nt_value = td_nt.compute_value(sim)

        # ADHD should learn faster (higher value after 1 update)
        assert (
            adhd_value > nt_value
        ), f"ADHD value {adhd_value:.2f} should be higher than NT {nt_value:.2f} after 1 update"

    def test_adhd_delay_aversion(self):
        """ADHD should show delay aversion (low gamma = devalue future)."""
        adhd_params = CLINICAL_PRESETS["adhd_typical"]
        nt_params = CLINICAL_PRESETS["neurotypical"]

        # ADHD gamma should be significantly lower
        assert (
            adhd_params["td_gamma"] < nt_params["td_gamma"]
        ), f"ADHD gamma {adhd_params['td_gamma']} should be < NT {nt_params['td_gamma']}"

        # Verify gamma is <0.7 (strong discounting)
        assert (
            adhd_params["td_gamma"] < 0.7
        ), f"ADHD gamma {adhd_params['td_gamma']} should be <0.7 for delay aversion"

    def test_adhd_optimistic_bias(self):
        """ADHD should start with optimistic bias (positive initial value)."""
        adhd_params = CLINICAL_PRESETS["adhd_typical"]
        td_adhd = TemporalDifferenceLearner(
            alpha=adhd_params["td_alpha"],
            gamma=adhd_params["td_gamma"],
            initial_value=adhd_params["td_initial_value"],
        )

        sim = {"emotion_intensity": 0.5, "plausibility": 0.5, "reward_distortion": 0.0}
        initial_value = td_adhd.compute_value(sim)

        # Should have positive initial bias
        assert initial_value > 0, f"ADHD initial value {initial_value} should be positive"


class TestAffectFeedback:
    """Test affect feedback calculation."""

    def test_affect_feedback_range(self):
        """Affect feedback should be in range [-0.5, 1.0]."""
        td = TemporalDifferenceLearner()

        # Test various simulations
        test_sims = [
            {"emotion_intensity": 0.9, "plausibility": 0.8, "reward_distortion": 0.1},
            {"emotion_intensity": 0.1, "plausibility": 0.9, "reward_distortion": 0.0},
            {"emotion_intensity": 0.5, "plausibility": 0.5, "reward_distortion": 0.5},
        ]

        for sim in test_sims:
            # Update several times to build value
            for _ in range(10):
                td.update_value(sim, terminal=True)

            feedback = td.get_affect_feedback(sim)
            assert -0.5 <= feedback <= 1.0, f"Feedback {feedback} outside range [-0.5, 1.0]"

    def test_affect_feedback_continuous(self):
        """Affect feedback should be continuous (not hardcoded thresholds)."""
        td = TemporalDifferenceLearner(alpha=0.2)

        # Train on gradually increasing reward
        feedbacks = []
        for intensity in np.linspace(0.1, 0.9, 9):
            sim = {"emotion_intensity": intensity, "plausibility": 0.5, "reward_distortion": 0.0}

            # Train
            for _ in range(20):
                td.update_value(sim, terminal=True)

            feedbacks.append(td.get_affect_feedback(sim))

        # Feedbacks should generally increase (not jump at thresholds)
        # Check that at least 6 out of 8 transitions are increasing
        increasing = sum(1 for i in range(len(feedbacks) - 1) if feedbacks[i + 1] > feedbacks[i])
        assert (
            increasing >= 6
        ), f"Feedbacks should increase continuously, got {increasing}/8 increases: {feedbacks}"


class TestEmotionalEncoderIntegration:
    """Test TD learning integration with EmotionalEncoder."""

    def test_encoder_td_configuration(self):
        """Verify EmotionalEncoder can be configured with TD learner."""
        encoder = EmotionalEncoder()
        nt_params = CLINICAL_PRESETS["neurotypical"]

        encoder.configure_td_learning(
            {
                "td_alpha": nt_params["td_alpha"],
                "td_gamma": nt_params["td_gamma"],
                "td_initial_value": nt_params["td_initial_value"],
                "reward_sensitivity": nt_params["reward_sensitivity"],
            }
        )

        assert encoder.td_learner is not None
        assert encoder.td_learner.alpha == nt_params["td_alpha"]
        assert encoder.td_learner.gamma == nt_params["td_gamma"]

    def test_encoder_uses_td_learning(self):
        """Verify encoder uses TD learning when configured."""
        encoder = EmotionalEncoder()
        nt_params = CLINICAL_PRESETS["neurotypical"]

        encoder.configure_td_learning(
            {
                "td_alpha": nt_params["td_alpha"],
                "td_gamma": nt_params["td_gamma"],
                "td_initial_value": nt_params["td_initial_value"],
                "reward_sensitivity": nt_params["reward_sensitivity"],
            }
        )

        # Create test simulation
        sim = {
            "id": "test_1",
            "emotional_prediction": 0.7,
            "emotion_intensity": 0.7,
            "plausibility": 0.6,
            "reward_distortion": 0.2,
            "replay_weight": 0.5,
        }

        # Encode
        encoded = encoder.encode_simulations([sim])

        # Should have affect_feedback
        assert "affect_feedback" in encoded[0]

        # Feedback should be in valid range
        feedback = encoded[0]["affect_feedback"]
        assert -0.5 <= feedback <= 1.0

    def test_encoder_fallback_without_td(self):
        """Verify encoder falls back to hardcoded thresholds without TD."""
        encoder = EmotionalEncoder()  # No TD configuration

        # High emotion, high distortion simulation
        sim = {
            "id": "test_1",
            "emotional_prediction": 0.8,
            "emotion_intensity": 0.8,
            "plausibility": 0.3,
            "reward_distortion": 0.5,
            "replay_weight": 0.5,
        }

        encoded = encoder.encode_simulations([sim])

        # Should use hardcoded value (0.6 for high emotion + high distortion)
        feedback = encoded[0]["affect_feedback"]
        assert feedback == 0.6, f"Expected hardcoded 0.6, got {feedback}"


class TestTDStatistics:
    """Test TD learning statistics."""

    def test_statistics_empty(self):
        """Statistics should work with no updates."""
        td = TemporalDifferenceLearner()
        stats = td.get_statistics()

        assert stats["mean_td_error"] == 0.0
        assert stats["n_updates"] == 0

    def test_statistics_after_learning(self):
        """Statistics should reflect learning progress."""
        td = TemporalDifferenceLearner(alpha=0.2)

        sim = {"emotion_intensity": 0.8, "plausibility": 0.6, "reward_distortion": 0.1}

        # 30 updates
        for _ in range(30):
            td.update_value(sim, terminal=True)

        stats = td.get_statistics()

        assert stats["n_updates"] == 30
        assert stats["n_unique_states"] > 0
        assert "mean_td_error" in stats
        assert "mean_abs_td_error" in stats
        assert "std_td_error" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
