# tests/test_salience.py
import os
import sys
import math
import uuid
import pytest
from datetime import datetime, timezone

# Add src directory to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from src.salience import SalienceTagger
class MockMemoryStore:
    @staticmethod
    def max_similarity(self, event):
        # Return a fixed similarity for testing purposes, e.g. 0.2
        return 0.2
class FixedUUID:
    @staticmethod
    def uuid4():
        return uuid.UUID(int=0)

class FixedDateTime:
    @staticmethod
    def utcnow():
        # Return fixed time
        return datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

@pytest.fixture(autouse=True)
def patch_uuid_datetime(monkeypatch):
    # Patch uuid.uuid4 and datetime.utcnow
    import uuid as uuid_module
    import src.salience as sal_mod
    monkeypatch.setattr(uuid_module, 'uuid4', FixedUUID.uuid4)
    monkeypatch.setattr(sal_mod, 'datetime', FixedDateTime)
    yield

@pytest.fixture
def tagger():
    return SalienceTagger(memory_store=MockMemoryStore(), w_i=0.6, w_n=0.4, salience_decay=0.01)

@pytest.fixture
def input_packet():
    # Single event per modality
    state = {'foo': 'bar'}
    clock = 300
    packet = {'clock': clock, 'state': state}
    for modality in SalienceTagger.MODALITIES:
        packet[modality] = [{'type': 'test', 'duration': 2.0, 'intensity': 0.5}]
    return packet


def test_tag_input_length_and_keys(tagger, input_packet):
    events = tagger.tag_input(input_packet)
    assert len(events) == len(SalienceTagger.MODALITIES)
    required_keys = {'id','timestamp','modality','state','novelty','emotion',
                     'recurrence','timing','duration','intensity','prioritization_score'}
    for e in events:
        assert set(e.keys()) == required_keys


def test_novelty_and_types(tagger, input_packet):
    events = tagger.tag_input(input_packet)
    for e in events:
        assert isinstance(e['novelty'], float)
        assert 0.2 <= e['novelty'] <= 1.0
        assert e['duration'] == 2.0
        assert e['intensity'] == 0.5
        assert e['state'] == input_packet['state']


def test_recurrence_initial_and_timing(tagger, input_packet):
    # first call recurrence should be 1.0
    events = tagger.tag_input(input_packet)
    for e in events:
        assert e['recurrence'] == pytest.approx(1.0)
        # timing = raw * (1 - salience_decay)
        raw = 1.0 / (1.0 + math.exp(-tagger.timing_steepness * (input_packet['clock'] - tagger.timing_center)))
        expected_timing = round(raw * (1.0 - tagger.salience_decay), 4)
        assert e['timing'] == pytest.approx(expected_timing)


def test_emotion_valence_and_category(tagger, input_packet):
    # Given intensity=0.5, valence = bias
    biases = {'vision':0.4, 'hearing':0.2, 'touch':-0.3, 'smell':-0.5, 'taste':0.6}
    events = tagger.tag_input(input_packet)
    for e in events:
        mod = e['modality']
        emotion = e['emotion']
        expected_val = round(biases[mod], 3)
        assert emotion['valence'] == expected_val
        # category
        if expected_val > 0.6:
            expected_cat = 'high_positive'
        elif expected_val > 0.2:
            expected_cat = 'positive'
        elif expected_val < -0.6:
            expected_cat = 'high_negative'
        elif expected_val < -0.2:
            expected_cat = 'negative'
        else:
            expected_cat = 'neutral'
        assert emotion['category'] == expected_cat


def test_id_and_timestamp_format(tagger, input_packet):
    events = tagger.tag_input(input_packet)
    for e in events:
        assert e['id'] == str(uuid.UUID(int=0))
        # timestamp from FixedDateTime.utcnow().isoformat()
        assert e['timestamp'] == FixedDateTime.utcnow().isoformat()