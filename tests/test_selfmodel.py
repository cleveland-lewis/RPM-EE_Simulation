# tests/test_selfmodel.py
import os
import sys
import pytest

# Add src directory to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.selfmodel import SelfModel

@pytest.fixture
def model():
    return SelfModel()

@pytest.fixture
def sample_sims():
    # Provide sims with different valences and plausibility, initial final_score
    return [
        {'emotional_prediction': 0.8, 'plausibility': 0.7, 'final_score': 0.5},  # mismatch high
        {'emotional_prediction': 0.1, 'plausibility': 0.4, 'final_score': 0.6},  # mismatch low
    ]

def test_evaluate_simulations_schema_mismatch_and_stress(model, sample_sims):
    # Initial stress
    assert model.schema_stress == 0.0
    sims = model.evaluate_simulations(list(sample_sims))
    # After first sim: mismatch > threshold (0.8>0.5), stress increases by 0.1 then decays by 0.95 -> 0.095
    assert pytest.approx(0.095, rel=1e-3) == model.schema_stress
    # After second sim: mismatch <= threshold, no change in schema_stress
# stress remains same as previous: 0.095
    assert pytest.approx(0.095, rel=1e-3) == model.schema_stress

    # Check schema_mismatch and filtered_score fields
    sim1 = sims[0]
    # Mismatch = |0.8 - previous_baseline| = 0.8
    assert 'schema_mismatch' in sim1 and pytest.approx(0.8) == sim1['schema_mismatch']
    # Penalty = (1 - plausibility)*0.7 = 0.21; filtered_score = max(0, 0.5 - 0.21) = 0.29
    assert 'schema_filtered_score' in sim1 and pytest.approx(0.29, rel=1e-3) == sim1['schema_filtered_score']

    sim2 = sims[1]
    # Mismatch = |0.1 - previous_baseline| = 0.1
    assert 'schema_mismatch' in sim2 and pytest.approx(0.1) == sim2['schema_mismatch']
    # Penalty = (1 - 0.4)*0.7 = 0.42; filtered_score = max(0, 0.6 - 0.42) = 0.18
    assert 'schema_filtered_score' in sim2 and pytest.approx(0.18, rel=1e-3) == sim2['schema_filtered_score']

def test_update_emotion_baseline(model):
    # Starting baseline 0.0
    model.update_emotion_baseline(0.5)
    # baseline = 0.8*0 + 0.2*0.5 = 0.1
    assert pytest.approx(0.1, rel=1e-3) == model.emotion_baseline

    # Update with new_valence 1.0: baseline=0.8*0.1 + 0.2*1.0 = 0.28
    model.update_emotion_baseline(1.0)
    assert pytest.approx(0.28, rel=1e-3) == model.emotion_baseline
