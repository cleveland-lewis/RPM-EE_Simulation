# tests/test_attunement.py

import os
import sys
import pytest

# Ensure src/ is on the import path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from src.attunement import SocialAttunementSystem

def test_infer_from_simulations_empty():
    system = SocialAttunementSystem()
    predicted = system._infer_from_simulations([])
    assert isinstance(predicted, float), "Predicted value should be float"
    assert predicted == 0.5, f"Expected neutral guess 0.5, got {predicted}"

def test_infer_from_simulations_extremes():
    system = SocialAttunementSystem()
    sims_high = [{"emotional_prediction": 1.0}, {"emotional_prediction": 1.0}]
    assert system._infer_from_simulations(sims_high) == 1.0
    sims_low = [{"emotional_prediction": -1.0}, {"emotional_prediction": -1.0}]
    assert system._infer_from_simulations(sims_low) == 0.0

@pytest.mark.parametrize("predicted, truth, expected", [
    (0.0, 0.04, 5),
    (0.0, 0.05, 4),
    (0.0, 0.1, 3),
    (0.0, 0.2, 2),
    (0.0, 0.3, 1),
    (0.0, 0.4, 0),
])
def test_score_prediction_boundaries(predicted, truth, expected):
    system = SocialAttunementSystem()
    assert system._score_prediction(predicted, truth) == expected

def test_evaluate_predictions_logs_history_and_updates_truth():
    system = SocialAttunementSystem()
    # fix initial truth
    system.current_truth = 0.5
    score = system.evaluate_predictions([])
    assert score == 5, f"Expected score 5, got {score}"
    # history updated
    assert len(system.history) == 1, "History should contain one entry"
    entry = system.history[0]
    assert set(entry.keys()) == {"truth", "predicted", "score"}
    assert entry["score"] == score
    # truth should change
    assert system.current_truth != 0.5, "current_truth should update after evaluation"