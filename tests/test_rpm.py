# tests/test_rpm.py
import os
import sys
import uuid
import pytest

# Add src directory to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from rpm import RecursivePredictiveModeler

@pytest.fixture(autouse=True)
def patch_uuid(monkeypatch):
    # Make UUIDs deterministic for testing
    monkeypatch.setattr(uuid, 'uuid4', lambda: uuid.UUID(int=0))
    yield

@ pytest.fixture
def example_event():
    return {
        'id': 'evt1',
        'modality': 'vision',
        'emotion': {'valence': 0.8},
        'intensity': 0.6
    }


def test_generate_simulations_and_simulation_history(example_event):
    rpm = RecursivePredictiveModeler()
    sims = rpm.generate_simulations([example_event])
    assert isinstance(sims, list) and len(sims) == 1
    sim = sims[0]
    # ID should match patched UUID
    assert sim['id'] == str(uuid.UUID(int=0))
    # Source event ID
    assert sim['source_event_id'] == example_event['id']
    # simulation stored in both simulations and history
    assert rpm.get_simulations() == sims
    assert rpm.simulation_history == sims


def test_create_simulation_fields_and_defaults(example_event):
    rpm = RecursivePredictiveModeler()
    sim = rpm._create_simulation(example_event)
    # Agent default
    assert sim['agent'] == 'self'
    # Emotion carried over
    assert sim['emotion'] == example_event['emotion']
    # Plausibility: 1 - abs(intensity-0.5) = 0.9
    assert sim['plausibility'] == pytest.approx(0.9)
    # Emotional prediction equals valence
    assert sim['emotional_prediction'] == pytest.approx(0.8)
    # Reward distortion: max(0, valence - plausibility) = max(0,0.8-0.9)=0
    assert sim['reward_distortion'] == pytest.approx(0.0)
    # Default replay weight
    assert sim['replay_weight'] == pytest.approx(1.0)


def test_predict_action_variants(example_event):
    rpm = RecursivePredictiveModeler()
    # positive vision => approach
    ev = example_event.copy()
    ev['modality'] = 'vision'; ev['emotion']['valence'] = 0.1
    sim = rpm._create_simulation(ev)
    assert sim['action'] == 'approach'
    # negative vision => withdraw
    ev['emotion']['valence'] = -0.1
    sim = rpm._create_simulation(ev)
    assert sim['action'] == 'withdraw'
    # positive touch => explore
    ev['modality'] = 'touch'; ev['emotion']['valence'] = 0.1
    sim = rpm._create_simulation(ev)
    assert sim['action'] == 'explore'
    # negative touch => recoil
    ev['emotion']['valence'] = -0.1
    sim = rpm._create_simulation(ev)
    assert sim['action'] == 'recoil'
    # other => observe
    ev['modality'] = 'hearing'; ev['emotion']['valence'] = 0
    sim = rpm._create_simulation(ev)
    assert sim['action'] == 'observe'


def test_predict_result_boundaries(example_event):
    rpm = RecursivePredictiveModeler()
    ev = example_event.copy()
    # valence > 0.5 -> positive outcome
    ev['emotion']['valence'] = 0.6
    sim = rpm._create_simulation(ev)
    assert sim['result'] == 'positive outcome'
    # valence < -0.5 -> negative outcome
    ev['emotion']['valence'] = -0.6
    sim = rpm._create_simulation(ev)
    assert sim['result'] == 'negative outcome'
    # else neutral
    ev['emotion']['valence'] = 0.0
    sim = rpm._create_simulation(ev)
    assert sim['result'] == 'neutral outcome'
