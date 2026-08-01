"""
Adapter for OpenNeuro ds003500 -- "Response inhibition and selective attention
in adults and children with and without ADHD" (Lytle, Burman & Booth, 2021).
https://openneuro.org/datasets/ds003500 (CC0, no DUA)

SCHEMA CONFIRMED 2026-08-01 against the actual downloaded behavioral files
(data/ds003500/, via `scripts/inspect_ds003500_schema.py`). Replaces an
earlier guessed-schema version of this module -- see git history if you need
the prior placeholder mapping.

BIDS layout (confirmed):
    participants.tsv               -- participant_id, birthdate_shifted, sex,
                                       adhd (0/1), handedness, a_date, b_date
    sub-<id>/func/
        sub-<id>_task-<TASK>_acq-{a,b}_events.tsv

Group label: the `adhd` column in participants.tsv is 0/1, not a text label.
    0 -> "control", 1 -> "adhd". 38 subjects total: 26 control, 12 ADHD.

GRANULARITY -- IMPORTANT DEVIATION FROM THE ORIGINAL DESIGN:
    events.tsv rows are NOT individual trials. Each row is one 18-trial
    BLOCK, with block-level aggregates:
        block_type_intended / block_type_performed  -- condition label
        response_time_avg   -- mean RT for the block, in SECONDS
        correct_total, errors_total                 -- out of 18 trials
        false-no_go / false-go (Inh tasks) or false-neg / false-pos (Sel
            tasks) -- column names differ by task family; not used here
    There is no way to recover single-trial RT/accuracy from this dataset's
    events.tsv -- the DDM's per-trial predict_action() will be compared
    against block-level real averages, not individual real trials. That's a
    coarser comparison than originally scoped and should be reported as such
    (n=12 blocks per subject per task, not n=18*12 trials).

TRIAL-LEVEL SEMANTICS CONFIRMED 2026-08-01 against the actual PsyScope
stimulus scripts (data/ds003500/code/<TaskName>, plain-text .psc-style
source with CR line endings -- not the events.json sidecars, which were
the only source used for the previous confirmation pass). This closes
GitHub issue #8. All twelve task scripts (six main + six Practice_*)
were checked; Inh and Sel each show one shared instruction wording per
family (bar the feature/conjunction target -- "red triangle" for Conj*,
a colored-shape target for Feat*), consistent with the block_type
labels below:
    Inh  (e.g. Conj1Inh code, Direct1/Direct2 events):
        "Go: Press index finger for all shapes."
        "Stop: If a red triangle is present, do not press anything.
         If no red triangle is present, press index finger."
    Sel  (e.g. Conj19Sel code, Direct event; One/Many block names in the
    script correspond to BIDS "single"/"array"):
        "Press index finger if there is a red triangle.
         Press middle finger if there is no red triangle."
        (Single vs. array only changes the stimulus display -- One-Stim
        is one picture, Many-Stim/Many-Mask is a 3x3-array display with
        the target at one cell -- not the response rule.)
No discrepancy from the events.json-derived mapping below was found;
this is confirmation, not a revision.

Six task files, two families with distinct manipulations (confirmed from
task-<TASK>_bold.json TaskDescription/Instructions, and now from the
PsyScope source directly per above):
    Conj1Inh, Conj9Inh, Feat1Inh, Feat9Inh
        Response inhibition. block_type is "go" or "no-go".
        Go blocks: press for every shape (no inhibition demand).
        No-go blocks: withhold response if a red triangle is present
        (inhibition demand). This is a go/no-go manipulation, not a
        set-size manipulation -- despite the "1"/"9" in the task name.
    Conj19Sel, Feat19Sel
        Feature/conjunction selection. block_type is "single" or "array".
        Single: one shape shown. Array: 3x3 grid (8 distractors + 1
        target/distractor). This IS a set-size / visual-search-load
        manipulation.

EVIDENCE/DIFFICULTY MAPPING (still a modeling choice, now grounded in the
confirmed manipulation rather than a guessed numeric set size):
    Inh blocks:  go     -> high evidence, low difficulty  (respond to everything)
                 no-go  -> low evidence,  high difficulty (must suppress response)
    Sel blocks:  single -> high evidence, low difficulty  (no distractors)
                 array  -> low evidence,  high difficulty (8 distractors present)

    IMPORTANT (see GitHub issue #6): the harder-condition signal (no-go,
    array) is mapped to `difficulty`, NOT `load`. `load` in ddm.py shrinks
    the decision boundary, which produces FASTER-but-less-accurate
    responses -- the opposite of what real participants do on harder
    conditions (they get slower). `difficulty` attenuates drift instead,
    which correctly produces slower-and-less-accurate responses. `load` is
    left at 0.0 throughout this adapter since ds003500 has no independent
    working-memory-load manipulation to map it to. See README.md, section
    "DDM load vs. difficulty", and src/ddm.py's predict_action docstring.

    This still conflates two different cognitive demands (inhibitory
    control vs. visual search) into the DDM's single difficulty input --
    that conflation is a real limitation of comparing to a DDM with only
    one difficulty axis, not an oversight to silently fix. Report Inh and
    Sel task results separately, never pooled, given they're not the same
    manipulation.
"""

import csv
from collections.abc import Iterator
from pathlib import Path
from typing import ClassVar

from .base import Trial

_GROUP_COLUMN = "adhd"
_GROUP_LABELS = {"0": "control", "1": "adhd"}


class DS003500Adapter:
    """Reads ds003500's behavioral BIDS tree and yields one Trial per block.

    Despite the field name `Trial`, each record here represents one
    18-trial block's aggregate behavior -- see module docstring.
    """

    def __init__(self, bids_root: str):
        self.root = Path(bids_root)
        if not self.root.exists():
            msg = (
                f"BIDS root not found: {self.root}. Download behavioral files "
                f"only via openneuro-py, e.g.:\n"
                f"  openneuro.download(dataset='ds003500', target_dir=..., "
                f"include=['participants.tsv', 'task-*.json', "
                f"'**/*_events.tsv'])"
            )
            raise FileNotFoundError(msg)
        self._participant_groups = self._load_participant_groups()

    def _load_participant_groups(self) -> dict[str, str]:
        path = self.root / "participants.tsv"
        groups: dict[str, str] = {}
        if not path.exists():
            return groups
        with path.open(newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                subject_id = row.get("participant_id", "").strip()
                raw = row.get(_GROUP_COLUMN, "").strip()
                groups[subject_id] = _GROUP_LABELS.get(raw, "unknown")
        return groups

    def groups(self) -> list[str]:
        return sorted(set(self._participant_groups.values()))

    def _subject_dirs(self) -> list[Path]:
        return sorted(p for p in self.root.glob("sub-*") if p.is_dir())

    def _events_files(self, subject_dir: Path) -> list[Path]:
        func_dir = subject_dir / "func"
        if not func_dir.exists():
            return []
        return sorted(func_dir.glob("*_events.tsv"))

    def iter_trials(self, group: str | None = None) -> Iterator[Trial]:
        for subject_dir in self._subject_dirs():
            subject_id = subject_dir.name
            subj_group = self._participant_groups.get(subject_id, "unknown")
            if group is not None and subj_group != group.lower():
                continue

            for events_path in self._events_files(subject_dir):
                task = self._task_name_from_filename(events_path.name)
                with events_path.open(newline="") as f:
                    reader = csv.DictReader(f, delimiter="\t")
                    for row in reader:
                        trial = self._row_to_trial(subject_id, subj_group, task, row)
                        if trial is not None:
                            yield trial

    @staticmethod
    def _task_name_from_filename(filename: str) -> str:
        # sub-213_task-Conj1Inh_acq-a_events.tsv -> Conj1Inh
        marker = "_task-"
        rest = filename.split(marker, 1)[1]
        return rest.split("_", 1)[0]

    def _row_to_trial(
        self, subject_id: str, group: str, task: str, row: dict[str, str]
    ) -> Trial | None:
        block_type = (
            row.get("block_type_performed") or row.get("block_type_intended") or ""
        ).strip()

        rt_raw = row.get("response_time_avg", "").strip()
        observed_rt_ms = None
        if rt_raw and rt_raw not in ("n/a", "N/A"):
            try:
                observed_rt_ms = float(rt_raw) * 1000.0  # confirmed: seconds in source
            except ValueError:
                observed_rt_ms = None

        correct_raw = row.get("correct_total", "").strip()
        errors_raw = row.get("errors_total", "").strip()
        observed_correct = None  # here: block accuracy in [0, 1], not a bool -- see note below
        try:
            correct = float(correct_raw)
            errors = float(errors_raw)
            total = correct + errors
            if total > 0:
                observed_correct = correct / total
        except (ValueError, TypeError):
            pass

        evidence, difficulty = self._evidence_from_block_type(task, block_type)
        if evidence is None:
            return None  # unrecognized block_type -- skip rather than guess

        return Trial(
            subject_id=subject_id,
            group=group,
            task=f"{task}:{block_type}",
            evidence=evidence,
            load=0.0,  # no WM-load manipulation in this dataset -- see module docstring
            difficulty=difficulty,
            observed_rt_ms=observed_rt_ms,
            observed_correct=observed_correct,
            raw=row,
        )

    # (evidence, difficulty) per (task family, block_type) -- see module
    # docstring EVIDENCE/DIFFICULTY MAPPING for rationale and its stated
    # limitation (Inh and Sel are different demands funneled through the
    # same one difficulty input -- do not pool across task family).
    _EVIDENCE_DIFFICULTY_TABLE: ClassVar[dict] = {
        ("Inh", "go"): (0.9, 0.1),
        ("Inh", "no-go"): (0.3, 0.7),
        ("Sel", "single"): (0.9, 0.1),
        ("Sel", "array"): (0.3, 0.7),
    }

    @classmethod
    def _evidence_from_block_type(cls, task: str, block_type: str):
        """Map the confirmed block manipulation to (evidence, difficulty)."""
        family = "Inh" if "Inh" in task else "Sel" if "Sel" in task else None
        return cls._EVIDENCE_DIFFICULTY_TABLE.get((family, block_type), (None, None))
