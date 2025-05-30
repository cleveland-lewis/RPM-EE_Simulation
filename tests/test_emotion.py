# tests/test_emotion.py
import os
import sys
import pytest

# Add src directory to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from src.emotion import EmotionalEncoder

@pytest.fixture
def encoder():
    return EmotionalEncoder()

@pytest.fixture
def base_simulation():
    # Provide base simulation dict with required keys
    return {
        "id": "sim1",
        "emotional_prediction": 0.8,
        "reward_distortion": 0.5,
        "replay_weight": 1.0
    }

@pytest.mark.parametrize("prediction, distortion, expected_feedback", [
    (0.7, 0.5, 0.6),  # high distortion & high intensity
    (0.6, 0.2, 0.3),  # intensity > 0.5
    (0.3, 0.1, 0.1),  # intensity > 0.2
    (0.1, 0.0, -0.1)  # intensity <= 0.2
])
def test_calculate_affect_feedback(prediction, distortion, expected_feedback, encoder, base_simulation):
    sim = base_simulation.copy()
    sim['emotional_prediction'] = prediction
    sim['reward_distortion'] = distortion
    # Must set emotion_intensity before calling private method
    sim['emotion_intensity'] = abs(prediction)
    feedback = encoder._calculate_affect_feedback(sim)
    assert feedback == pytest.approx(expected_feedback)


def test_encode_simulations_weight_and_flag(encoder, base_simulation):
    sim = base_simulation.copy()
    # First run: count=1 <= threshold, no fatigue
    seq = encoder.encode_simulations([sim])[0]
    # emotion_intensity is set by encode_simulations
    assert seq['emotion_intensity'] == pytest.approx(abs(base_simulation['emotional_prediction']))
    # affect_feedback for 0.8 prediction and distortion=0.5 => 0.6
    assert seq['affect_feedback'] == pytest.approx(0.6)
    # initial weight 1.0 + 0.6
    assert seq['replay_weight'] == pytest.approx(1.6)
    assert seq['fatigue_flag'] is False


def test_encode_simulations_fatigue_suppression(encoder, base_simulation):
    # Simulate runs beyond threshold to trigger suppression
    sims = [base_simulation.copy()]
    threshold = encoder.replay_fatigue_threshold
    # Perform threshold+1 runs
    for _ in range(threshold + 1):
        sims = encoder.encode_simulations(sims)
    seq = sims[0]
    assert seq['fatigue_flag'] is True
    # Manual weight calculation
    manual_weight = base_simulation['replay_weight']
    for run in range(threshold + 1):
        # compute feedback each run
        emotion_intensity = abs(base_simulation['emotional_prediction'])
        sim_dict = {
            'emotional_prediction': base_simulation['emotional_prediction'],
            'reward_distortion': base_simulation['reward_distortion'],
            'emotion_intensity': emotion_intensity
        }
        feedback = encoder._calculate_affect_feedback(sim_dict)
        manual_weight += feedback
    # suppression applies after adding feedback on last run
    manual_weight = manual_weight * 0.5
    assert seq['replay_weight'] == pytest.approx(manual_weight)