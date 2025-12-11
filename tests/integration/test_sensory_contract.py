import random

import numpy as np
import pytest

from src.sensory import SensoryInputSystem, validate_tick_payload


def _base_payload():
    return {
        "attunement_score": 0.6,
        "schema_stress": 0.2,
        "avg_affect_feedback": 0.1,
        "short_term_size": 3,
        "long_term_size": 1,
    }


def test_validate_tick_payload_accepts_complete_numeric_payload():
    payload = _base_payload()
    validated = validate_tick_payload(payload)

    assert set(validated.keys()) == set(payload.keys())
    assert isinstance(validated["short_term_size"], int)
    assert isinstance(validated["attunement_score"], float)


def test_validate_tick_payload_rejects_missing_and_invalid_values():
    with pytest.raises(ValueError):
        validate_tick_payload({"attunement_score": 0.1})  # missing required keys

    with pytest.raises(ValueError):
        bad = _base_payload()
        bad["avg_affect_feedback"] = float("nan")
        validate_tick_payload(bad)

    with pytest.raises(ValueError):
        bad = _base_payload()
        bad["short_term_size"] = -2
        validate_tick_payload(bad)


def test_tick_output_matches_contract():
    sis = SensoryInputSystem(
        event_rate=1,
        senses_count_range=(1, 1),
        py_random=random.Random(0),
        np_random=np.random.default_rng(0),
    )
    validated = validate_tick_payload(sis.tick())

    assert validated["short_term_size"] >= 0
    assert -1.0 <= validated["avg_affect_feedback"] <= 1.0
