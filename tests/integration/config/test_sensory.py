import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from src.sensory import SensoryInputSystem


def test_state_cycle_awake_fatigued_asleep():
    sis = SensoryInputSystem(awake_ticks=1, fatigue_ticks=1, asleep_ticks=1)
    assert sis.state == "awake"
    sis.update_clock()
    assert sis.state == "fatigued"
    sis.update_clock()
    assert sis.state == "asleep"
    sis.update_clock()
    assert sis.state == "awake"


def test_generate_input_packet_structure():
    sis = SensoryInputSystem()
    packet = sis.generate_input()
    assert "clock" in packet and "state" in packet
    for mod in sis.MODALITIES:
        assert mod in packet
        assert isinstance(packet[mod], list)


def test_tick_returns_metrics_and_advances_clock():
    sis = SensoryInputSystem()
    before_clock = sis.clock
    out = sis.tick()
    required = {"attunement_score", "schema_stress", "avg_affect_feedback", "short_term_size", "long_term_size"}
    assert required.issubset(out.keys())
    assert sis.clock == before_clock + 1
