# tests/test_memory.py
import os
import sys
import pytest
from src.memory import MemoryBuffer


# Add src directory to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

@pytest.fixture
def store():
    return MemoryBuffer(max_short_term=3)

@pytest.fixture
def example_event():
    # Minimal tagged_event structure
    return {
        "modality": "vision",
        "duration": 2.0,
        "intensity": 0.5,
        "emotion": {"valence": 0.1},
        "timing": 0.5,
        "prioritization_score": 0.8
    }

def test_init_store_empty(store):
    assert store.short_term.maxlen == 3
    assert len(store.short_term) == 0
    assert store.long_term == {}

def test_store_events_appends_and_respects_maxlen(store, example_event):
    # Add four events, maxlen=3 so oldest dropped
    for _ in range(4):
        store.store_events([example_event.copy()])
    assert len(store.short_term) == 3

def test_event_similarity_identical(store, example_event):
    # identical events should have similarity 1.0
    sim = store._event_similarity(example_event, example_event)
    assert sim == pytest.approx(1.0)

def test_event_similarity_different_modality(store, example_event):
    other = example_event.copy()
    other["modality"] = "hearing"
    sim = store._event_similarity(example_event, other)
    # modality mismatch penalizes 0.1*0 => drop that component
    assert sim < 1.0
    assert sim >= 0.0

def test_match_patterns_no_memory(store, example_event):
    # short_term empty -> similarity 0, so all unmatched
    matched, unmatched = store.match_patterns([example_event.copy()])
    assert matched == []
    assert len(unmatched) == 1
    assert "recurrence" not in unmatched[0]

def test_match_patterns_with_memory(store, example_event):
    # store a similar event
    store.store_events([example_event.copy()])
    # new event identical -> similarity 1.0 -> matched
    new = example_event.copy()
    matched, unmatched = store.match_patterns([new])
    assert len(matched) == 1
    assert matched[0].get("recurrence") == 1
    assert unmatched == []

def test_prune_old_memory(store, example_event):
    # store events with varying prioritization_score
    e1 = example_event.copy()
    e1["prioritization_score"] = 0.2
    e2 = example_event.copy()
    e2["prioritization_score"] = 0.4
    store.store_events([e1, e2])
    # prune should remove e1 only
    store.prune_old_memory()
    remaining = list(store.short_term)
    assert len(remaining) == 1
    assert remaining[0]["prioritization_score"] == pytest.approx(0.4)
