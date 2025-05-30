# tests/test_sensory.py
import os
import sys
import pytest
import random

# Add src directory to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from sensory import SensoryInputSystem

@pytest.fixture
def system():
    return SensoryInputSystem()


def test_initial_state_and_timer(system):
    assert system.clock == 0
    assert system.state == "awake"
    assert system.state_timer == system.state_durations["awake"]


def test_transition_state_cycles(system):
    system.transition_state()
    assert system.state == "fatigued"
    assert system.state_timer == system.state_durations["fatigued"]
    system.transition_state()
    assert system.state == "asleep"
    assert system.state_timer == system.state_durations["asleep"]
    system.transition_state()
    assert system.state == "awake"
    assert system.state_timer == system.state_durations["awake"]


def test_update_clock_and_auto_transition(system):
    system.state = "awake"
    system.state_timer = 1
    system.update_clock()
    assert system.clock == 1
    assert system.state == "fatigued"
    assert system.state_timer == system.state_durations["fatigued"]


def test_generate_input_awake(monkeypatch, system):
    monkeypatch.setattr(random, 'uniform', lambda a, b: 0.5)
    monkeypatch.setattr(random, 'randint', lambda a, b: 1)
    monkeypatch.setattr(random, 'random', lambda: 0.0)

    system.state = "awake"
    system.clock = 10
    packet = system.generate_input()

    assert packet["clock"] == 10
    assert packet["state"] == "awake"

    # Vision events
    assert len(packet["vision"]) == 1
    ev = packet["vision"][0]
    assert ev["modality"] == "vision"
    assert ev["intensity"] == pytest.approx(0.5)
    assert ev["duration"] == 1

    # Hearing events
    assert len(packet["hearing"]) == 1
    ev = packet["hearing"][0]
    assert ev["modality"] == "hearing"
    assert ev["intensity"] == pytest.approx(0.5)
    assert ev["duration"] == 1

    # Touch events
    assert len(packet["touch"]) == 1
    ev = packet["touch"][0]
    assert ev["modality"] == "touch"
    assert ev["intensity"] == pytest.approx(0.5)
    assert ev["duration"] == 1

    # Smell events
    assert len(packet["smell"]) == 1
    ev = packet["smell"][0]
    assert ev["modality"] == "smell"
    assert ev["intensity"] == pytest.approx(0.5)
    assert ev["duration"] == 3

    # Taste events
    assert len(packet["taste"]) == 1
    ev = packet["taste"][0]
    assert ev["modality"] == "taste"
    assert ev["intensity"] == pytest.approx(0.5)
    assert ev["duration"] == 2


def test_generate_input_asleep(monkeypatch, system):
    monkeypatch.setattr(random, 'uniform', lambda a, b: 0.2)
    monkeypatch.setattr(random, 'randint', lambda a, b: 2)
    rand_vals = iter([0.5, 0.5])
    monkeypatch.setattr(random, 'random', lambda: next(rand_vals))

    system.state = "asleep"
    system.clock = 5
    packet = system.generate_input()

    assert packet["clock"] == 5
    assert packet["state"] == "asleep"

    # Vision asleep => no events
    assert packet["vision"] == []

    # Hearing asleep => 1 event
    assert len(packet["hearing"]) == 1
    ev = packet["hearing"][0]
    assert ev["modality"] == "hearing"

    # Touch asleep => 1 event
    assert len(packet["touch"]) == 1
    ev = packet["touch"][0]
    assert ev["modality"] == "touch"

    # Smell asleep => random()>0.3 => no events
    assert packet["smell"] == []

    # Taste asleep => random()>0.1 => no events
    assert packet["taste"] == []