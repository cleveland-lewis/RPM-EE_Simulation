# tests/test_replay.py
import os
import sys
import pytest

# Ensure src directory is on path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from replay import ReplayModeArbitrator

@pytest.fixture
def arbitrator():
    return ReplayModeArbitrator(damping_cycles=5)

@pytest.fixture
def base_state():
    return {"clock": 10, "stress": 0.0, "prediction_error": 0.0, "emotion_volatility": 0.0}


def test_no_switch_within_damping(arbitrator, base_state):
    # Within damping_cycles, mode should not switch regardless of state
    initial_mode = arbitrator.current_mode
    arbitrator.last_switch_clock = 10
    state = base_state.copy()
    state.update({
        "clock": arbitrator.last_switch_clock + arbitrator.damping_cycles - 1,
        "stress": 0.9,
        "prediction_error": 0.9,
        "emotion_volatility": 0.9
    })
    mode = arbitrator.select_mode(state)
    assert mode == initial_mode, f"Mode should remain '{initial_mode}' within damping cycles"


def test_switch_to_soothing_after_damping(arbitrator, base_state):
    # After damping_cycles elapsed, stress > 0.7 triggers soothing
    arbitrator.current_mode = "problem_solving"
    arbitrator.last_switch_clock = 0
    state = base_state.copy()
    state.update({"clock": arbitrator.damping_cycles + 1, "stress": 0.8})
    mode = arbitrator.select_mode(state)
    assert mode == "soothing", f"Expected soothing, got {mode}"
    assert arbitrator.current_mode == "soothing"
    assert arbitrator.last_switch_clock == state["clock"]


def test_switch_to_problem_solving_based_on_error(arbitrator, base_state):
    # prediction_error > 0.6 triggers problem_solving
    arbitrator.current_mode = "soothing"
    arbitrator.last_switch_clock = 0
    state = base_state.copy()
    state.update({"clock": arbitrator.damping_cycles + 1, "stress": 0.0, "prediction_error": 0.7})
    mode = arbitrator.select_mode(state)
    assert mode == "problem_solving"


def test_switch_to_pattern_search_based_on_volatility(arbitrator, base_state):
    # emotion_volatility > 0.5 triggers pattern_search
    arbitrator.current_mode = "rest"
    arbitrator.last_switch_clock = 0
    state = base_state.copy()
    state.update({"clock": arbitrator.damping_cycles + 2, "emotion_volatility": 0.6})
    mode = arbitrator.select_mode(state)
    assert mode == "pattern_search"


def test_switch_to_rest_when_no_conditions_met(arbitrator, base_state):
    # all metrics below thresholds triggers rest
    arbitrator.current_mode = "pattern_search"
    arbitrator.last_switch_clock = 0
    state = base_state.copy()
    state.update({"clock": arbitrator.damping_cycles + 3})
    mode = arbitrator.select_mode(state)
    assert mode == "rest", f"Expected rest, got {mode}"

@pytest.mark.parametrize("initial, new", [
    ("problem_solving", "soothing"),
    ("soothing", "problem_solving"),
])
def test_switch_mode_updates_correctly(arbitrator, base_state, initial, new):
    # Test that switching to a different mode updates both current_mode and last_switch_clock
    arbitrator.current_mode = initial
    arbitrator.last_switch_clock = 0
    state = base_state.copy()
    state.update({"clock": arbitrator.damping_cycles + 1})
    if new == "soothing":
        state["stress"] = 0.8
    else:
        state["prediction_error"] = 0.7
    mode = arbitrator.select_mode(state)
    assert mode == new
    assert arbitrator.current_mode == new
    assert arbitrator.last_switch_clock == state["clock"]