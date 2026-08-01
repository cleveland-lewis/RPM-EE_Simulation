#!/usr/bin/env python3
"""
Empirical Validation Against ds003500 (OpenNeuro, CC0)

Runs each clinical preset's DDM against real ds003500 blocks and compares
simulated RT/accuracy to what real participants actually did. This is
GitHub issue #5 -- see also #6 (RT direction discrepancy already found
during scoping) and #7 (statistical rigor upgrade: distributional
comparison via KS-test, implemented here).

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
   neurotypical for control-group blocks). The DDM is stochastic
   (Euler-Maruyama accumulation, see src/ddm.py), so each block is
   simulated `TRIALS_PER_BLOCK` times and averaged, mirroring how the
   real block-level RT/accuracy is itself an average over 18 real trials
   -- this keeps the two sides comparable in what they represent (a
   per-block mean), not real single trials vs. one noisy simulated draw.
4. Compare the resulting real vs. simulated per-block distributions with
   a two-sample Kolmogorov-Smirnov test (scipy.stats.ks_2samp), for RT
   and accuracy separately. KS tests whether the two samples could
   plausibly be drawn from the same distribution, not just whether their
   means match -- it's sensitive to differences in spread and shape that
   a mean-deviation comparison would miss entirely. Mean/std/relative
   deviation are still reported alongside, for continuity with the
   original report.

Only ADHD-relevant presets are exercised here: ds003500 has no ASD or
MDD diagnostic labels, so asd_typical/mdd_typical have nothing to compare
against in this dataset (see issues #9, #10).
"""

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.stats import ks_2samp

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

# Real block-level RT/accuracy are each an average over 18 real trials
# (see src/adapters/ds003500.py). Average the same number of stochastic
# simulated trials per block so both sides represent the same kind of
# quantity, rather than comparing an 18-trial real average to a single
# noisy simulated draw.
TRIALS_PER_BLOCK = 18

# Two-sided KS test significance threshold. p > ALPHA means the null
# hypothesis (same distribution) is not rejected at this sample size.
ALPHA = 0.05

# Fixed seed for the DDM's stochastic accumulation, so re-running this
# script reproduces the same KS statistics rather than drifting run to run.
_SIM_SEED = 20260801


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
    rt_ks_statistic: float
    rt_ks_pvalue: float
    rt_distributions_differ: bool  # True if rt_ks_pvalue < ALPHA
    real_accuracy_mean: float
    sim_accuracy_mean: float
    accuracy_relative_deviation: float
    accuracy_ks_statistic: float
    accuracy_ks_pvalue: float
    accuracy_distributions_differ: bool  # True if accuracy_ks_pvalue < ALPHA


def _task_family(task_label: str) -> str:
    # Trial.task is "TaskName:block_type", e.g. "Conj1Inh:go"
    task_name = task_label.split(":", 1)[0]
    if "Inh" in task_name:
        return "Inh"
    if "Sel" in task_name:
        return "Sel"
    return "unknown"


def _configured_ddm(preset_name: str, seed: int) -> RecursivePredictiveModeler:
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
    rpm.ddm.rng = np.random.default_rng(seed)  # reproducible KS statistics
    return rpm


def run_comparison(bids_root: str) -> list:
    adapter = DS003500Adapter(bids_root)
    all_trials = list(adapter.iter_trials())
    print(f"Loaded {len(all_trials)} real blocks from {bids_root}")

    results = []
    for group, preset_name in _GROUP_TO_PRESET.items():
        rpm = _configured_ddm(preset_name, seed=_SIM_SEED)

        for family in _TASK_FAMILIES:
            blocks = [t for t in all_trials if t.group == group and _task_family(t.task) == family]
            if not blocks:
                print(f"  (no {group}/{family} blocks found -- skipping)")
                continue

            real_rts = [b.observed_rt_ms for b in blocks if b.observed_rt_ms is not None]
            real_accs = [b.observed_correct for b in blocks if b.observed_correct is not None]

            # Per block: simulate TRIALS_PER_BLOCK stochastic trials and
            # average, matching the real side's 18-trial block average
            # (see module docstring).
            sim_rts = []
            sim_accs = []
            for b in blocks:
                block_rts = []
                block_correct = []
                for _ in range(TRIALS_PER_BLOCK):
                    prediction = rpm.ddm.predict_action(b.evidence, b.load, b.difficulty)
                    block_rts.append(prediction["rt"])
                    if prediction["accurate"] is not None:
                        block_correct.append(1.0 if prediction["accurate"] else 0.0)
                sim_rts.append(float(np.mean(block_rts)))
                if block_correct:
                    sim_accs.append(float(np.mean(block_correct)))

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

            rt_ks_stat, rt_ks_p = _ks_test(real_rts, sim_rts)
            acc_ks_stat, acc_ks_p = _ks_test(real_accs, sim_accs)

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
                    rt_ks_statistic=round(rt_ks_stat, 4),
                    rt_ks_pvalue=round(rt_ks_p, 4),
                    rt_distributions_differ=bool(rt_ks_p < ALPHA),
                    real_accuracy_mean=round(real_acc_mean, 3),
                    sim_accuracy_mean=round(sim_acc_mean, 3),
                    accuracy_relative_deviation=round(acc_dev, 3),
                    accuracy_ks_statistic=round(acc_ks_stat, 4),
                    accuracy_ks_pvalue=round(acc_ks_p, 4),
                    accuracy_distributions_differ=bool(acc_ks_p < ALPHA),
                )
            )
    return results


_MIN_KS_SAMPLE_SIZE = 2


def _ks_test(real: list, sim: list) -> tuple:
    """Two-sample KS test; returns (statistic, pvalue), both NaN if either
    sample is too small (KS is undefined/meaningless below 2 points)."""
    if len(real) < _MIN_KS_SAMPLE_SIZE or len(sim) < _MIN_KS_SAMPLE_SIZE:
        return float("nan"), float("nan")
    result = ks_2samp(real, sim)
    return float(result.statistic), float(result.pvalue)


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
        rt_verdict = "DIFFER" if r.rt_distributions_differ else "not distinguishable"
        print(
            f"                 KS D={r.rt_ks_statistic:.3f}  p={r.rt_ks_pvalue:.4f}  "
            f"({rt_verdict} at alpha={ALPHA})"
        )
        print(
            f"  Accuracy:      real={r.real_accuracy_mean:.3f}   "
            f"sim={r.sim_accuracy_mean:.3f}   "
            f"deviation={r.accuracy_relative_deviation:+.1%}"
        )
        acc_verdict = "DIFFER" if r.accuracy_distributions_differ else "not distinguishable"
        print(
            f"                 KS D={r.accuracy_ks_statistic:.3f}  "
            f"p={r.accuracy_ks_pvalue:.4f}  ({acc_verdict} at alpha={ALPHA})"
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
            "Distributions are compared with a two-sample Kolmogorov-Smirnov test "
            f"(`scipy.stats.ks_2samp`), not just mean deviation -- KS statistic D "
            "is the max gap between the two empirical CDFs; p < "
            f"{ALPHA} rejects the null hypothesis that real and simulated values "
            "come from the same distribution. Each simulated block averages "
            f"{TRIALS_PER_BLOCK} stochastic DDM trials, matching the real side's "
            "18-trial block average.\n\n"
        )
        f.write(
            "| Task family | Group | Preset | n | Real RT (ms) | Sim RT (ms) | "
            "RT dev | RT KS D | RT KS p | RT differ? | Real Acc | Sim Acc | "
            "Acc dev | Acc KS D | Acc KS p | Acc differ? |\n"
        )
        f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in results:
            f.write(
                f"| {r.task_family} | {r.group} | {r.preset} | {r.n_blocks} | "
                f"{r.real_rt_mean:.1f}±{r.real_rt_std:.1f} | "
                f"{r.sim_rt_mean:.1f}±{r.sim_rt_std:.1f} | "
                f"{r.rt_relative_deviation:+.1%} | "
                f"{r.rt_ks_statistic:.3f} | {r.rt_ks_pvalue:.4f} | "
                f"{'yes' if r.rt_distributions_differ else 'no'} | "
                f"{r.real_accuracy_mean:.3f} | {r.sim_accuracy_mean:.3f} | "
                f"{r.accuracy_relative_deviation:+.1%} | "
                f"{r.accuracy_ks_statistic:.3f} | {r.accuracy_ks_pvalue:.4f} | "
                f"{'yes' if r.accuracy_distributions_differ else 'no'} |\n"
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
