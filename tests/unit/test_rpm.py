import pytest
from src.rpm import RecursivePredictiveModeler

@pytest.fixture
def model():
    return RecursivePredictiveModeler()

def test_generate_simulations_returns_correct_number_of_simulations(model):
    events = [
        {"id": "1", "emotion": {"valence": 0.5}, "modality": "vision", "intensity": 0.7},
        {"id": "2", "emotion": {"valence": -0.5}, "modality": "touch", "intensity": 0.3},
    ]
    simulations = model.generate_simulations(events)
    assert len(simulations) == 2

def test_generate_simulations_with_empty_events_list_returns_empty_list(model):
    simulations = model.generate_simulations([])
    assert len(simulations) == 0

def test_simulation_dictionary_contains_all_keys(model):
    event = {"id": "1", "emotion": {"valence": 0.5}, "modality": "vision", "intensity": 0.7}
    simulation = model.generate_simulations([event])[0]
    expected_keys = [
        "id",
        "source_event_id",
        "agent",
        "emotion",
        "action",
        "result",
        "plausibility",
        "emotional_prediction",
        "reward_distortion",
        "replay_weight",
    ]
    for key in expected_keys:
        assert key in simulation

def test_predict_action_with_missing_modality_returns_default_action(model):
    event = {"id": "1", "emotion": {"valence": 0.5}, "intensity": 0.7}
    action = model._predict_action(event)
    assert action == "observe"

def test_predict_result_with_missing_valence_returns_default_result(model):
    event = {"id": "1", "emotion": {}, "modality": "vision", "intensity": 0.7}
    result = model._predict_result(event)
    assert result == "neutral outcome"

def test_compute_physical_plausibility_with_missing_intensity_returns_default_plausibility(model):
    event = {"id": "1", "emotion": {"valence": 0.5}, "modality": "vision"}
    plausibility = model._compute_physical_plausibility(event)
    assert plausibility == 1.0

def test_estimate_emotional_outcome_with_missing_valence_returns_default_outcome(model):
    event = {"id": "1", "emotion": {}, "modality": "vision", "intensity": 0.7}
    outcome = model._estimate_emotional_outcome(event)
    assert outcome == 0.0

def test_distortion_bias_with_missing_keys_returns_default_bias(model):
    event = {"id": "1", "emotion": {}}
    bias = model._distortion_bias(event)
    assert bias == 0.0
