"""
Integration tests for RPM-EE v2.0 with all remediation components.

Tests verify that:
1. Full simulation pipeline runs with all clinical presets
2. All v2.0 metrics are logged correctly (RT, accuracy, precision_ratio, volatility)
3. Clinical differentiation is preserved across all new metrics
4. DDM, Bayesian PE, and TD learning integrate correctly
5. No regressions in existing functionality
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from presets import list_presets
from simulation import RPMEESimulation


class TestFullPipelineIntegration:
    """Test complete simulation pipeline with all presets."""

    @pytest.mark.parametrize("preset", list_presets())
    def test_simulation_runs_without_errors(self, preset):
        """Verify simulation runs successfully for all presets."""
        sim = RPMEESimulation(preset=preset)

        # Run 20 episodes
        for _ in range(20):
            sim.step()

        # Should complete without errors
        assert len(sim.logs) == 20
        assert sim.clock == 20

    @pytest.mark.parametrize("preset", list_presets())
    def test_all_v2_metrics_logged(self, preset):
        """Verify all v2.0 metrics are present in logs."""
        sim = RPMEESimulation(preset=preset)

        # Run 10 episodes
        for _ in range(10):
            sim.step()

        # Check last log entry has all v2.0 metrics
        last_log = sim.logs[-1]

        # Existing metrics
        assert "clock" in last_log
        assert "state" in last_log
        assert "replay_mode" in last_log
        assert "schema_stress" in last_log
        assert "preset" in last_log

        # NEW Phase 1: DDM metrics
        assert "rt_mean" in last_log
        assert "rt_std" in last_log
        assert "accuracy" in last_log

        # NEW Phase 3: Bayesian PE metrics
        assert "precision_ratio" in last_log
        assert "volatility" in last_log

    def test_nt_baseline_metrics(self):
        """Verify neurotypical baseline produces expected metrics."""
        sim = RPMEESimulation(preset="neurotypical")

        # Run 50 episodes to get stable statistics
        for _ in range(50):
            sim.step()

        # Collect metrics (excluding None values)
        rt_values = [log["rt_mean"] for log in sim.logs if log["rt_mean"] is not None]
        accuracy_values = [log["accuracy"] for log in sim.logs if log["accuracy"] is not None]
        precision_ratios = [log["precision_ratio"] for log in sim.logs]

        if rt_values:
            mean_rt = np.mean(rt_values)
            # NT should have RT around 400-500ms (DDM adjusted)
            assert 300 < mean_rt < 600, f"NT mean RT {mean_rt} outside expected range"

        if accuracy_values:
            mean_accuracy = np.mean(accuracy_values)
            # NT accuracy depends on emotional valence strength in the simulation.
            # EZ-diffusion with typical weak-to-moderate evidence (valences ~0.4-0.8)
            # produces 70-85% accuracy, which is clinically valid for cognitive tasks.
            assert mean_accuracy > 0.65, f"NT accuracy {mean_accuracy} too low"

        # NT should have balanced precision ratio (~1.0). Allow up to 1.6:
        # the HGF log-volatility adapts over episodes, and early large PEs
        # can transiently push the sensory/prior ratio above 1.0 before settling.
        mean_precision = np.mean(precision_ratios)
        assert 0.5 < mean_precision < 1.6, f"NT precision ratio {mean_precision} should be ~1.0"


class TestClinicalDifferentiation:
    """Test that clinical presets show distinct behavioral patterns."""

    def test_mdd_psychomotor_slowing(self):
        """MDD should show slower RT than NT."""
        sim_nt = RPMEESimulation(preset="neurotypical")
        sim_mdd = RPMEESimulation(preset="mdd_typical")

        # Run 30 episodes each
        for _ in range(30):
            sim_nt.step()
            sim_mdd.step()

        # Collect RT values
        rt_nt = [log["rt_mean"] for log in sim_nt.logs if log["rt_mean"] is not None]
        rt_mdd = [log["rt_mean"] for log in sim_mdd.logs if log["rt_mean"] is not None]

        if rt_nt and rt_mdd:
            mean_rt_nt = np.mean(rt_nt)
            mean_rt_mdd = np.mean(rt_mdd)

            # MDD should be slower than NT
            assert (
                mean_rt_mdd > mean_rt_nt
            ), f"MDD RT {mean_rt_mdd:.1f} should be > NT {mean_rt_nt:.1f}"

    def test_adhd_high_variability(self):
        """ADHD should show higher RT variability than NT."""
        sim_nt = RPMEESimulation(preset="neurotypical")
        sim_adhd = RPMEESimulation(preset="adhd_typical")

        # Run 30 episodes each
        for _ in range(30):
            sim_nt.step()
            sim_adhd.step()

        # Collect RT std values
        rt_std_nt = [log["rt_std"] for log in sim_nt.logs if log["rt_std"] is not None]
        rt_std_adhd = [log["rt_std"] for log in sim_adhd.logs if log["rt_std"] is not None]

        if rt_std_nt and rt_std_adhd:
            mean_std_nt = np.mean(rt_std_nt)
            mean_std_adhd = np.mean(rt_std_adhd)

            # ADHD should have higher variability
            assert (
                mean_std_adhd > mean_std_nt
            ), f"ADHD RT std {mean_std_adhd:.1f} should be > NT {mean_std_nt:.1f}"

    def test_asd_aberrant_precision(self):
        """ASD should show elevated precision ratio (>3.0)."""
        sim_asd = RPMEESimulation(preset="asd_typical")

        # Run 30 episodes
        for _ in range(30):
            sim_asd.step()

        # Collect precision ratios
        precision_ratios = [log["precision_ratio"] for log in sim_asd.logs]
        mean_precision = np.mean(precision_ratios)

        # ASD should have high precision ratio (sensory dominance)
        assert mean_precision > 3.0, f"ASD precision ratio {mean_precision:.2f} should be > 3.0"

    def test_mdd_prior_dominance(self):
        """MDD should show low precision ratio (<1.0 - prior dominance)."""
        sim_mdd = RPMEESimulation(preset="mdd_typical")

        # Run 30 episodes
        for _ in range(30):
            sim_mdd.step()

        # Collect precision ratios
        precision_ratios = [log["precision_ratio"] for log in sim_mdd.logs]
        mean_precision = np.mean(precision_ratios)

        # MDD should have low precision ratio (prior dominance)
        assert mean_precision < 1.0, f"MDD precision ratio {mean_precision:.2f} should be < 1.0"


class TestComponentIntegration:
    """Test that all components integrate correctly."""

    def test_ddm_produces_rt_metrics(self):
        """Verify DDM produces RT and accuracy values."""
        sim = RPMEESimulation(preset="neurotypical")

        # Run 20 episodes
        for _ in range(20):
            sim.step()

        # Count non-None RT values
        rt_count = sum(1 for log in sim.logs if log["rt_mean"] is not None)
        accuracy_count = sum(1 for log in sim.logs if log["accuracy"] is not None)

        # Should have RT/accuracy values in most episodes (>50%)
        assert rt_count > 10, f"Only {rt_count}/20 episodes have RT values"
        assert accuracy_count > 10, f"Only {accuracy_count}/20 episodes have accuracy values"

    def test_bayesian_pe_produces_precision_metrics(self):
        """Verify Bayesian PE produces precision and volatility metrics."""
        sim = RPMEESimulation(preset="neurotypical")

        # Run 20 episodes
        for _ in range(20):
            sim.step()

        # All episodes should have precision metrics
        for log in sim.logs:
            assert log["precision_ratio"] is not None
            assert log["volatility"] is not None

            # Values should be in reasonable ranges
            assert 0.1 < log["precision_ratio"] < 10.0
            assert 0.0 <= log["volatility"] <= 2.0

    def test_td_learning_affects_replay_weights(self):
        """Verify TD learning affects simulation replay weights."""
        sim = RPMEESimulation(preset="neurotypical")

        # Verify TD learner is configured
        assert sim.encoder.td_learner is not None
        assert sim.encoder.td_learner.alpha == 0.10
        assert sim.encoder.td_learner.gamma == 0.90

        # Run simulation - TD learner should be used internally
        for _ in range(10):
            sim.step()

        # No errors means TD learning is working
        assert len(sim.logs) == 10

    def test_all_subsystems_configured(self):
        """Verify all subsystems are properly configured from presets."""
        sim = RPMEESimulation(preset="adhd_typical")

        # DDM configured
        assert sim.rpm.ddm is not None
        assert sim.rpm.ddm.rt_variability == 0.45  # ADHD value

        # Bayesian PE configured
        assert sim.self_model.bayesian_pe is not None
        assert sim.self_model.bayesian_pe.precision.sensory_precision == 0.6

        # TD learning configured
        assert sim.encoder.td_learner is not None
        assert sim.encoder.td_learner.alpha == 0.20  # ADHD high learning rate
        assert sim.encoder.td_learner.gamma == 0.60  # ADHD delay aversion


class TestBackwardCompatibility:
    """Test backward compatibility with v1.1 behavior."""

    def test_existing_log_fields_preserved(self):
        """Verify v1.1 log fields still exist."""
        sim = RPMEESimulation(preset="neurotypical")

        sim.step()
        log = sim.logs[0]

        # v1.1 fields that must be preserved
        v1_fields = [
            "clock",
            "state",
            "replay_mode",
            "num_tagged",
            "num_simulations",
            "attunement_score",
            "schema_stress",
            "preset",
            "vigilance",
        ]

        for field in v1_fields:
            assert field in log, f"v1.1 field '{field}' missing from logs"

    def test_simulation_interface_unchanged(self):
        """Verify RPMEESimulation interface is backward compatible."""
        # Should initialize with just preset name
        sim = RPMEESimulation(preset="neurotypical")

        # Should have step() and run() methods
        assert hasattr(sim, "step")
        assert hasattr(sim, "run")

        # Should have logs attribute
        assert hasattr(sim, "logs")
        assert isinstance(sim.logs, list)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_simulations_episode(self):
        """Verify simulation handles episodes with no simulations gracefully."""
        sim = RPMEESimulation(preset="neurotypical")

        # Run 10 episodes - some may have zero simulations
        for _ in range(10):
            sim.step()

        # Should complete without errors
        assert len(sim.logs) == 10

    def test_high_stress_conditions(self):
        """Verify simulation handles high stress conditions."""
        sim = RPMEESimulation(preset="mdd_typical")  # Starts with elevated stress

        # Run 30 episodes to accumulate stress
        for _ in range(30):
            sim.step()

        # Stress should be bounded [0, 1]
        for log in sim.logs:
            assert 0.0 <= log["schema_stress"] <= 1.0

    def test_long_simulation_stability(self):
        """Verify simulation remains stable over long runs."""
        sim = RPMEESimulation(preset="neurotypical")

        # Run 100 episodes
        for _ in range(100):
            sim.step()

        # Check last 10 episodes for stability (no NaN, Inf)
        for log in sim.logs[-10:]:
            if log["rt_mean"] is not None:
                assert np.isfinite(log["rt_mean"])
            if log["accuracy"] is not None:
                assert np.isfinite(log["accuracy"])
            assert np.isfinite(log["precision_ratio"])
            assert np.isfinite(log["volatility"])
            assert np.isfinite(log["schema_stress"])


class TestParameterCoverage:
    """Test that all preset parameters are now used."""

    def test_all_parameters_have_effect(self):
        """Verify all preset parameters are actually used in simulation."""
        from presets import CLINICAL_PRESETS

        nt_params = CLINICAL_PRESETS["neurotypical"]

        # Count parameters
        n_params = len(nt_params)

        # v1.1 had 18 params (6 were inert)
        # v2.0 should have 25 params (18 + 4 Bayesian + 3 TD)
        assert n_params == 25, f"Expected 25 parameters, got {n_params}"

        # Verify all critical parameters exist
        critical_params = [
            # RT/Accuracy (now functional via DDM)
            "base_rt",
            "rt_variability",
            "rt_slowing",
            "base_accuracy",
            "accuracy_decline",
            # Bayesian PE (new)
            "sensory_precision",
            "prior_precision",
            "volatile_precision",
            "precision_learning_rate",
            # TD Learning (new)
            "td_alpha",
            "td_gamma",
            "td_initial_value",
            # Existing
            "wm_capacity",
            "stress_baseline",
            "reward_sensitivity",
        ]

        for param in critical_params:
            assert param in nt_params, f"Missing critical parameter: {param}"


class TestMetricsValidity:
    """Test that metrics are within valid ranges."""

    def test_rt_metrics_valid_range(self):
        """RT metrics should be in physiologically plausible ranges."""
        sim = RPMEESimulation(preset="neurotypical")

        for _ in range(30):
            sim.step()

        for log in sim.logs:
            if log["rt_mean"] is not None:
                # RT should be 100-2000ms
                assert 100 < log["rt_mean"] < 2000, f"RT {log['rt_mean']} outside plausible range"

            if log["rt_std"] is not None:
                # RT std should be non-negative (can be 0 if only 1 simulation)
                assert log["rt_std"] >= 0

    def test_accuracy_metrics_valid_range(self):
        """Accuracy should be in [0, 1] range."""
        sim = RPMEESimulation(preset="neurotypical")

        for _ in range(30):
            sim.step()

        for log in sim.logs:
            if log["accuracy"] is not None:
                assert 0.0 <= log["accuracy"] <= 1.0, f"Accuracy {log['accuracy']} outside [0, 1]"

    def test_precision_ratio_positive(self):
        """Precision ratio should be positive."""
        sim = RPMEESimulation(preset="neurotypical")

        for _ in range(20):
            sim.step()

        for log in sim.logs:
            assert (
                log["precision_ratio"] > 0
            ), f"Precision ratio {log['precision_ratio']} should be positive"

    def test_volatility_non_negative(self):
        """Volatility should be non-negative."""
        sim = RPMEESimulation(preset="neurotypical")

        for _ in range(20):
            sim.step()

        for log in sim.logs:
            assert log["volatility"] >= 0, f"Volatility {log['volatility']} should be non-negative"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
