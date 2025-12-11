import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from src.salience import SalienceTagger


class DummyStore:
    """Minimal memory_store with max_similarity for SalienceTagger tests."""

    def __init__(self):
        self.queries = []

    def max_similarity(self, event):
        self.queries.append(event)
        return 0.0


def test_tag_events_basic_fields():
    store = DummyStore()
    tagger = SalienceTagger(memory_store=store, w_i=0.6, w_n=0.4, salience_decay=0.01)
    events = [{"intensity": 0.5}, {"intensity": 1.2}]
    tagged = tagger.tag_events(events)
    assert len(tagged) == len(events)
    for e in tagged:
        assert "id" in e and "timestamp" in e
        assert 0.0 <= e["salience"] <= 1.0
        assert 0.0 <= e["initial_salience"] <= 1.0
        assert "decay_rate" in e


def test_tag_input_uses_modalities_and_state():
    store = DummyStore()
    tagger = SalienceTagger(store, salience_decay=0.01)
    packet = {
        "clock": 10,
        "state": {"mode": "test"},
        "vision": [{"intensity": 0.3}],
        "hearing": [],
    }
    tagged = tagger.tag_input(packet)
    assert len(tagged) == 1
    e = tagged[0]
    assert e["modality"] == "vision"
    assert e["state"] == {"mode": "test"}
    assert "emotion" in e and "novelty" in e and "prioritization_score" in e
