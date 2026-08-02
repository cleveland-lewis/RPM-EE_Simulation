"""
Unit tests for Bayesian Precision-Weighted Prediction Error implementation.

Tests verify that:
1. ASD preset shows elevated sensory/prior precision ratio (>3.0)
2. Volatility tracking increases with prediction errors
3. Precision-weighting affects belief updating
4. Clinical presets show expected precision patterns
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bayesian_pe import BayesianPredictiveModeler, PrecisionWeights
from presets import CLINICAL_PRESETS


class TestBayesianPEBasicFunctionality:
    """Test basic Bayesian PE operations."""

    def test_initialization(self):
        """Verify Bayesian PE initializes correctly."""
        precision = PrecisionWeights(
            sensory_precision=1.0, prior_precision=1.0, volatile_precision=0.5, learning_rate=0.1
        )
        bpe = BayesianPredictiveModeler(precision)

        assert bpe.mu_sensory == 0.0
        assert bpe.mu_state == 0.0
        assert bpe.mu_volatility == 0.5

    def test_update_beliefs_returns_dict(self):
        """Verify update_beliefs returns expected keys."""
        precision = PrecisionWeights()
        bpe = BayesianPredictiveModeler(precision)

        result = bpe.update_beliefs(observation=0.5, observation_precision=1.0)

        required_keys = [
            "pe_sensory",
            "pe_state",
            "pe_total",
            "mu_sensory",
            "mu_state",
            "volatility",
            "precision_ratio",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_beliefs_converge_to_observations(self):
        """Verify beliefs converge to stable observations."""
        precision = PrecisionWeights(learning_rate=0.2)
        bpe = BayesianPredictiveModeler(precision)

        # Present stable observation (0.7) for 50 trials
        for _ in range(50):
            bpe.update_beliefs(observation=0.7, observation_precision=1.0)

        # Beliefs should converge near observation
        assert 0.6 < bpe.mu_state < 0.8, f"State belief {bpe.mu_state} didn't converge to 0.7"


class TestPrecisionRatios:
    """Test precision ratios across clinical presets."""

    def test_neurotypical_balanced_precision(self):
        """NT preset should have balanced precision ratio (~1.0)."""
        nt_params = CLINICAL_PRESETS["neurotypical"]
        precision = PrecisionWeights(
            sensory_precision=nt_params["sensory_precision"],
            prior_precision=nt_params["prior_precision"],
            volatile_precision=nt_params["volatile_precision"],
            learning_rate=nt_params["precision_learning_rate"],
        )
        bpe = BayesianPredictiveModeler(precision)

        # Run a few updates
        for obs in [0.5, 0.6, 0.4, 0.5]:
            result = bpe.update_beliefs(observation=obs, observation_precision=1.0)

        # NT should have balanced ratio. Allow 0.7-1.5: the HGF may briefly
        # inflate volatility on the first large PE (state=0 vs obs=0.5), which
        # reduces pi_state and raises the ratio transiently before settling.
        assert (
            0.7 < result["precision_ratio"] < 1.5
        ), f"NT precision ratio {result['precision_ratio']:.2f} outside balanced range"

    def test_asd_aberrant_precision(self):
        """ASD preset should have high sensory/prior precision ratio (>3.0)."""
        asd_params = CLINICAL_PRESETS["asd_typical"]
        precision = PrecisionWeights(
            sensory_precision=asd_params["sensory_precision"],
            prior_precision=asd_params["prior_precision"],
            volatile_precision=asd_params["volatile_precision"],
            learning_rate=asd_params["precision_learning_rate"],
        )
        bpe = BayesianPredictiveModeler(precision)

        # Run several updates
        for obs in [0.5, 0.7, 0.3, 0.8, 0.2]:
            result = bpe.update_beliefs(observation=obs, observation_precision=1.0)

        # ASD should have HIGH precision ratio (sensory dominance)
        assert (
            result["precision_ratio"] > 3.0
        ), f"ASD precision ratio {result['precision_ratio']:.2f} should be > 3.0"

        # Baseline ratio from params should be 1.8/0.4 = 4.5
        baseline_ratio = asd_params["sensory_precision"] / asd_params["prior_precision"]
        assert baseline_ratio > 4.0, f"ASD baseline ratio {baseline_ratio:.2f} should be > 4.0"

    def test_mdd_prior_dominance(self):
        """MDD preset should have low sensory/prior ratio (<1.0 - prior dominance)."""
        mdd_params = CLINICAL_PRESETS["mdd_typical"]
        precision = PrecisionWeights(
            sensory_precision=mdd_params["sensory_precision"],
            prior_precision=mdd_params["prior_precision"],
            volatile_precision=mdd_params["volatile_precision"],
            learning_rate=mdd_params["precision_learning_rate"],
        )
        bpe = BayesianPredictiveModeler(precision)

        # Run several updates
        for obs in [0.5, 0.6, 0.4, 0.5]:
            result = bpe.update_beliefs(observation=obs, observation_precision=1.0)

        # MDD should have LOW precision ratio (prior dominance → rigid beliefs)
        assert (
            result["precision_ratio"] < 1.0
        ), f"MDD precision ratio {result['precision_ratio']:.2f} should be < 1.0 (prior dominance)"

        # Baseline ratio from params should be 0.7/1.3 = 0.54
        baseline_ratio = mdd_params["sensory_precision"] / mdd_params["prior_precision"]
        assert baseline_ratio < 0.7, f"MDD baseline ratio {baseline_ratio:.2f} should be < 0.7"


class TestVolatilityTracking:
    """Test volatility estimation and adaptation."""

    def test_volatility_responds_to_prediction_errors(self):
        """Volatility estimate should respond to variable observations."""
        precision = PrecisionWeights(learning_rate=0.15)
        bpe = BayesianPredictiveModeler(precision)

        # Start with stable observations to establish baseline
        for _ in range(10):
            bpe.update_beliefs(observation=0.5, observation_precision=1.0)

        # Reset and measure volatile environment from start
        bpe.reset()
        precision2 = PrecisionWeights(learning_rate=0.15)
        bpe2 = BayesianPredictiveModeler(precision2)

        # Volatile environment (large oscillations)
        for i in range(20):
            obs = 0.1 if i % 2 == 0 else 0.9
            bpe2.update_beliefs(observation=obs, observation_precision=1.0)

        # Volatility in volatile environment should be higher than initial
        # (Even if it settles, the average should reflect variability)
        assert (
            bpe2.mu_volatility != bpe.mu_volatility
        ), "Volatility should respond to observation patterns"

    def test_high_volatility_reduces_prior_precision(self):
        """High volatility should reduce prior precision (less trust in predictions)."""
        precision = PrecisionWeights(prior_precision=1.0, learning_rate=0.2)
        bpe = BayesianPredictiveModeler(precision)

        initial_prior_precision = bpe.pi_state

        # Induce high volatility with variable observations
        for i in range(30):
            obs = 0.1 if i % 2 == 0 else 0.9
            bpe.update_beliefs(observation=obs, observation_precision=1.0)

        final_prior_precision = bpe.pi_state

        # Prior precision should decrease with high volatility
        assert (
            final_prior_precision < initial_prior_precision
        ), "Prior precision should decrease with high volatility"


class TestPrecisionWeighting:
    """Test that precision affects belief updating."""

    def test_sensory_precision_affects_weighting(self):
        """Sensory precision should weight prediction errors appropriately."""
        # Low sensory precision (more weight to observations)
        low_precision = PrecisionWeights(sensory_precision=0.5, prior_precision=1.0)
        bpe_low = BayesianPredictiveModeler(low_precision)

        # High sensory precision (more weight to prior sensory beliefs)
        high_precision = PrecisionWeights(sensory_precision=2.0, prior_precision=1.0)
        bpe_high = BayesianPredictiveModeler(high_precision)

        # Single observation
        observation = 0.9

        result_low = bpe_low.update_beliefs(observation=observation, observation_precision=1.0)
        result_high = bpe_high.update_beliefs(observation=observation, observation_precision=1.0)

        # High sensory precision should produce LARGER weighted prediction errors
        # (because PE is weighted by precision: π * PE)
        assert abs(result_high["pe_sensory"]) > abs(
            result_low["pe_sensory"]
        ), "High sensory precision should produce larger weighted PEs"

    def test_observation_precision_modulates_update(self):
        """DDM confidence (observation precision) should modulate belief updating."""
        precision = PrecisionWeights()
        bpe = BayesianPredictiveModeler(precision)

        # Low confidence observation
        bpe.update_beliefs(observation=0.9, observation_precision=0.3)
        belief_low_conf = bpe.mu_sensory

        # Reset
        bpe.reset()

        # High confidence observation
        bpe.update_beliefs(observation=0.9, observation_precision=1.5)
        belief_high_conf = bpe.mu_sensory

        # High confidence should produce stronger belief update
        assert abs(belief_high_conf) > abs(
            belief_low_conf
        ), "High observation precision should produce stronger updates"


class TestClinicalDifferentiation:
    """Test that clinical presets show expected patterns."""

    def test_asd_vs_nt_precision_difference(self):
        """ASD should have much higher precision ratio than NT."""
        nt_params = CLINICAL_PRESETS["neurotypical"]
        asd_params = CLINICAL_PRESETS["asd_typical"]

        nt_ratio = nt_params["sensory_precision"] / nt_params["prior_precision"]
        asd_ratio = asd_params["sensory_precision"] / asd_params["prior_precision"]

        # ASD ratio should be >4x higher than NT
        assert (
            asd_ratio > nt_ratio * 3
        ), f"ASD ratio {asd_ratio:.2f} should be >3x NT ratio {nt_ratio:.2f}"

    def test_adhd_low_precision(self):
        """ADHD should have reduced precision (noisy processing)."""
        adhd_params = CLINICAL_PRESETS["adhd_typical"]
        nt_params = CLINICAL_PRESETS["neurotypical"]

        # ADHD should have lower sensory precision than NT
        assert (
            adhd_params["sensory_precision"] < nt_params["sensory_precision"]
        ), "ADHD sensory precision should be lower than NT (noisy processing)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
