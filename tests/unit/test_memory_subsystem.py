from src.memory import MemorySubsystem


def test_memory_subsystem_snapshot_empty():
    subsystem = MemorySubsystem()
    snapshot = subsystem.snapshot()
    assert isinstance(snapshot, dict)
    assert "short_term" in snapshot
    assert "long_term" in snapshot
    assert snapshot["short_term"] == []
    assert snapshot["long_term"] == []


def test_memory_subsystem_step_updates_snapshot():
    subsystem = MemorySubsystem()
    subsystem.step(0)
    snapshot = subsystem.snapshot()
    assert "short_term" in snapshot
    assert "long_term" in snapshot
