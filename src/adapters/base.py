"""
Base interfaces for trial-level dataset adapters.

RPM-EE's normal run loop (RPMEESimulation.step()) free-runs on synthetic
sensory input with no ground truth per tick. Empirical validation instead
needs a trial-locked mode: one real trial in, one (rt, accurate) prediction
out, compared against what the real participant actually did.

A dataset adapter's job is narrow: read a dataset's native trial records
and produce a stream of `Trial` objects with fields the DDM already
understands (evidence, load) plus enough metadata to group results by
diagnosis and condition afterward. It does NOT run the simulation --
that stays in simulation.py so the DDM/Bayesian-PE/TD-learning core is
untouched by dataset-specific code.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Trial:
    """One real trial, normalized to what RecursivePredictiveModeler/DDM expect.

    evidence: signed float in [-1, 1]. Sign/magnitude convention is
        adapter-specific (see each adapter's docstring for how it derives
        this from the source task) -- the DDM only cares that it's evidence
        strength/direction, not what it means semantically.
    load: cognitive/WM load in [0, 1], passed straight to
        DriftDiffusionModel.predict_action -- shrinks the boundary (faster,
        less accurate). Default 0.0. Do NOT use this for "harder task
        condition" -- that inverts the RT ordering (see issue #6). Use
        `difficulty` for that instead.
    difficulty: task/stimulus difficulty in [0, 1], passed straight to
        DriftDiffusionModel.predict_action -- attenuates drift (slower,
        less accurate). Default 0.0. This is the right field for "more
        distractors", "harder discrimination", "requires inhibition", etc.
    observed_rt_ms: the real participant's reaction time in milliseconds, if present.
    observed_correct: accuracy for this record, if scorable. Type depends on
        the adapter's granularity: a per-trial adapter should use bool; a
        per-block/aggregate adapter (e.g. ds003500, which has no true
        single-trial rows) should use a float proportion in [0, 1]. Check
        the specific adapter's docstring before assuming which.
    """

    subject_id: str
    group: str  # e.g. "adhd", "control" -- from participants.tsv, not inferred
    task: str  # source task/condition name, kept verbatim for traceability
    evidence: float
    load: float = 0.0
    difficulty: float = 0.0
    observed_rt_ms: float | None = None
    observed_correct: float | None = None  # bool or [0,1] proportion -- see above
    raw: dict = field(default_factory=dict)  # original row, for debugging/re-derivation


class TaskAdapter(Protocol):
    """Contract every dataset adapter must satisfy."""

    def iter_trials(self, group: str | None = None) -> Iterator[Trial]:
        """Yield Trial records, optionally filtered to one diagnostic group."""
        ...

    def groups(self) -> list[str]:
        """Return the distinct diagnostic/group labels present in the dataset."""
        ...
