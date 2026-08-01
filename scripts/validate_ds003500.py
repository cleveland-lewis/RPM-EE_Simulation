#!/usr/bin/env python3
"""
Empirical Validation Against ds003500 (OpenNeuro, CC0)

Runs each clinical preset's DDM against real ds003500 blocks and compares
simulated RT/accuracy to what real participants actually did. This is
GitHub issue #5 -- see also #6 (RT direction discrepancy already found
during scoping) and #7 (statistical rigor upgrade, not attempted here).

METHODOLOGY:
1. Load real blocks via src/adapters/ds003500.py (BIDS events.tsv, one
   record per 18-trial block -- see that module's docstring for why this
   is block-level, not trial-level).
2. Split strictly by task family: Inh (go/no-go, response inhibition) vs
   Sel (single/array, visual-search load). NEVER pooled -- they are
   different cognitive manipulations funneled through the same two DDM
   inputs (evidence, load); see src/adapters/ds003500.py's module
   docstring.
3. For each task family, feed every real block's (evidence, load) through
   the matched clinical preset's DDM (adhd_typical for ADHD-group blocks,
   neurotypical for control-group blocks) and collect the simulated
   RT/accuracy distribution alongside the real one.
4. Report mean/std for both, plus relative deviation. This is a
   first-pass comparison (mean-deviation, not distributional) --
   deliberately not the KS-test upgrade scoped in issue #7.

Only ADHD-relevant presets are exercised here: ds003500 has no ASD or
MDD diagnostic labels, so asd_typical/mdd_typical have nothing to compare
against in this dataset (see issues #9, #10).
"""

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adapters.ds003500 import DS003500Adapter  # noqa: E402
from presets import get_preset  # noqa: E402
from rpm import RecursivePredictiveModeler  # noqa: E402

# Real diagnostic group -> matched clinical preset. ds003500 only labels
# ADHD/control, so that's the only pairing this script can validate.
_GROUP_TO_PRESET = {
    "adhd": "adhd_typical",
    "control": "neurotypical",
}

_TASK_FAMILIES = ("Inh", "Sel")


@dataclass
class ComparisonResult:
    task_family: str
    group: str
    preset: str
    n_blocks: int
    real_rt_mean: float
    real_rt_std: float
    sim_rt_mean: float
    sim_rt_std: float
    rt_relative_deviation: float  # (sim - real) / real
    real_accuracy_mean: float
    sim_accuracy_mean: float
    accuracy_relative_deviation: float


def _task_family(task_label: str) -> str:
    # Trial.task is "TaskName:block_type", e.g. "Conj1Inh:go"
    task_name = task_label.split(":", 1)[0]
    if "Inh" in task_name:
        return "Inh"
    if "Sel" in task_name:
        return "Sel"
    return "unknown"


def _configured_ddm(preset_name: str) -> RecursivePredictiveModeler:
    params = get_preset(preset_name)
    rpm = RecursivePredictiveModeler()
    rpm.configure_ddm(
        {
            "base_rt": params["base_rt"],
            "rt_variability": params["rt_variability"],
            "rt_slowing": params["rt_slowing"],
            "base_accuracy": params["base_accuracy"],
            "accuracy_decline": params["accuracy_decline"],
        }
    )
    return rpm


def run_comparison(bids_root: str) -> list:
    adapter = DS003500Adapter(bids_root)
    all_trials = list(adapter.iter_trials())
    print(f"Loaded {len(all_trials)} real blocks from {bids_root}")

    results = []
    for group, preset_name in _GROUP_TO_PRESET.items():
        rpm = _configured_ddm(preset_name)

        for family in _TASK_FAMILIES:
            blocks = [t for t in all_trials if t.group == group and _task_family(t.task) == family]
            if not blocks:
                print(f"  (no {group}/{family} blocks found -- skipping)")
                continue

            real_rts = [b.observed_rt_ms for b in blocks if b.observed_rt_ms is not None]
            real_accs = [b.observed_correct for b in blocks if b.observed_correct is not None]

            sim_rts = []
            sim_accs = []
            for b in blocks:
                prediction = rpm.ddm.predict_action(b.evidence, b.load, b.difficulty)
                sim_rts.append(prediction["rt"])
                if prediction["accurate"] is not None:
                    sim_accs.append(1.0 if prediction["accurate"] else 0.0)

            real_rt_mean = float(np.mean(real_rts)) if real_rts else float("nan")
            real_rt_std = float(np.std(real_rts)) if real_rts else float("nan")
            sim_rt_mean = float(np.mean(sim_rts)) if sim_rts else float("nan")
            sim_rt_std = float(np.std(sim_rts)) if sim_rts else float("nan")
            rt_dev = (sim_rt_mean - real_rt_mean) / real_rt_mean if real_rt_mean else float("nan")

            real_acc_mean = float(np.mean(real_accs)) if real_accs else float("nan")
            sim_acc_mean = float(np.mean(sim_accs)) if sim_accs else float("nan")
            acc_dev = (
                (sim_acc_mean - real_acc_mean) / real_acc_mean if real_acc_mean else float("nan")
            )

            results.append(
                ComparisonResult(
                    task_family=family,
                    group=group,
                    preset=preset_name,
                    n_blocks=len(blocks),
                    real_rt_mean=round(real_rt_mean, 1),
                    real_rt_std=round(real_rt_std, 1),
                    sim_rt_mean=round(sim_rt_mean, 1),
                    sim_rt_std=round(sim_rt_std, 1),
                    rt_relative_deviation=round(rt_dev, 3),
                    real_accuracy_mean=round(real_acc_mean, 3),
                    sim_accuracy_mean=round(sim_acc_mean, 3),
                    accuracy_relative_deviation=round(acc_dev, 3),
                )
            )
    return results


def print_report(results: list) -> None:
    print()
    print("=" * 80)
    print("ds003500 EMPIRICAL VALIDATION -- real vs. simulated")
    print("=" * 80)
    for r in results:
        print(f"\n[{r.task_family}] group={r.group} preset={r.preset} (n={r.n_blocks} blocks)")
        print(
            f"  RT (ms):       real={r.real_rt_mean:.1f}±{r.real_rt_std:.1f}   "
            f"sim={r.sim_rt_mean:.1f}±{r.sim_rt_std:.1f}   "
            f"deviation={r.rt_relative_deviation:+.1%}"
        )
        print(
            f"  Accuracy:      real={r.real_accuracy_mean:.3f}   "
            f"sim={r.sim_accuracy_mean:.3f}   "
            f"deviation={r.accuracy_relative_deviation:+.1%}"
        )

    print()
    print("-" * 80)
    print("Cross-group check (real data only): does ADHD show the expected")
    print("slower/more-variable RT than control, independent of any preset?")
    for family in _TASK_FAMILIES:
        adhd = next((r for r in results if r.group == "adhd" and r.task_family == family), None)
        ctrl = next((r for r in results if r.group == "control" and r.task_family == family), None)
        if adhd and ctrl:
            direction = (
                "as expected (ADHD slower)"
                if adhd.real_rt_mean > ctrl.real_rt_mean
                else "OPPOSITE of expected (ADHD faster) -- check task/subgroup"
            )
            print(
                f"  [{family}] real ADHD RT={adhd.real_rt_mean:.1f}ms vs "
                f"real control RT={ctrl.real_rt_mean:.1f}ms -- {direction}"
            )


def save_outputs(results: list, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "ds003500_validation_results.json"
    with json_path.open("w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    print(f"\nSaved: {json_path}")

    md_path = output_dir / "ds003500_validation_report.md"
    with md_path.open("w") as f:
        f.write("# ds003500 Empirical Validation Report\n\n")
        f.write(
            "Real trial-level (block-level) behavioral data from OpenNeuro ds003500 "
            "compared against clinical preset DDM predictions. See "
            "`src/adapters/ds003500.py` for dataset/adapter caveats "
            "(block-level granularity, Inh/Sel non-pooling, evidence/load mapping "
            "as a modeling choice).\n\n"
        )
        f.write(
            "| Task family | Group | Preset | n | Real RT (ms) | Sim RT (ms) | "
            "RT dev | Real Acc | Sim Acc | Acc dev |\n"
        )
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for r in results:
            f.write(
                f"| {r.task_family} | {r.group} | {r.preset} | {r.n_blocks} | "
                f"{r.real_rt_mean:.1f}±{r.real_rt_std:.1f} | "
                f"{r.sim_rt_mean:.1f}±{r.sim_rt_std:.1f} | "
                f"{r.rt_relative_deviation:+.1%} | "
                f"{r.real_accuracy_mean:.3f} | {r.sim_accuracy_mean:.3f} | "
                f"{r.accuracy_relative_deviation:+.1%} |\n"
            )
    print(f"Saved: {md_path}")


def main():
    project_root = Path(__file__).parent.parent
    bids_root = project_root / "data" / "ds003500"
    if not bids_root.exists():
        print(
            f"ds003500 not found at {bids_root} -- download it first "
            "(see src/adapters/ds003500.py's FileNotFoundError message)."
        )
        return 1

    results = run_comparison(str(bids_root))
    print_report(results)
    save_outputs(results, project_root / "results" / "validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
