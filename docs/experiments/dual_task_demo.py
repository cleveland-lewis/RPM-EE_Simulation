

"""
Dual-task demo script

Generates a factorial dual-task design (ext_load × mem_load), runs trials,
exports results, and (optionally) produces simple summary plots.

Usage (from repo root):
    python dual_task_demo.py --preset default --ext-levels 0.3,0.6,0.9 \
        --mem-levels 0.3,0.6,0.9 --reps 5 --duration 200 --seed 42 \
        --csv results/dual_task_demo.csv --jsonl results/dual_task_demo.jsonl \
        --plot

Notes:
- CSV export requires pandas; JSONL has no extra dependency.
- Plots require matplotlib; saved to PNG files if available.
"""
from __future__ import annotations

import argparse
import os
from typing import List

import numpy as np

try:
    # Local import path
    from src.trial_wrapper import (
        DualTaskSimulator,
        results_to_dataframe,
        save_results,
    )
except ImportError:  # fallback when run from src/
    from trial_wrapper import (
        DualTaskSimulator,
        results_to_dataframe,
        save_results,
    )


def _parse_levels(arg: str) -> List[float]:
    try:
        vals = [float(x.strip()) for x in arg.split(",") if x.strip()]
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Invalid levels list: {arg}") from e
    for v in vals:
        if not (0.0 <= v <= 1.0):
            raise argparse.ArgumentTypeError(
                f"Levels must be in [0,1]. Got {v} in {arg}"
            )
    return vals


def main() -> int:
    p = argparse.ArgumentParser(description="Dual-task RPM-EE demo")
    p.add_argument("--preset", default="default", help="Engine preset name")
    p.add_argument(
        "--ext-levels",
        type=_parse_levels,
        default=[0.3, 0.6, 0.9],
        help="Comma-separated external load levels in [0,1]",
    )
    p.add_argument(
        "--mem-levels",
        type=_parse_levels,
        default=[0.3, 0.6, 0.9],
        help="Comma-separated memory load levels in [0,1]",
    )
    p.add_argument("--reps", type=int, default=5, help="Reps per cell")
    p.add_argument("--duration", type=int, default=200, help="Ticks per trial")
    p.add_argument("--seed", type=int, default=42, help="Base RNG seed")
    p.add_argument(
        "--no-shuffle",
        action="store_true",
        help="Disable deterministic shuffling of trial order",
    )
    p.add_argument("--csv", default="results/dual_task_demo.csv", help="CSV output path")
    p.add_argument(
        "--jsonl", default="results/dual_task_demo.jsonl", help="JSONL output path"
    )
    p.add_argument("--plot", action="store_true", help="Create simple summary plots")

    args = p.parse_args()

    # Ensure output directory exists
    for out_path in (args.csv, args.jsonl):
        out_dir = os.path.dirname(out_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

    # Build design and run
    sim = DualTaskSimulator(preset=args.preset, seed=args.seed)
    trials = sim.create_trial_design(
        ext_load_levels=args.ext_levels,
        mem_load_levels=args.mem_levels,
        n_reps=args.reps,
        shuffle=not args.no_shuffle,
    )

    print(
        f"[DUAL-TASK] preset={args.preset} cells={len(args.ext_levels)}x{len(args.mem_levels)}\n"
        f"            n_trials={len(trials)} duration={args.duration} seed={args.seed}"
    )

    results = sim.run_experiment(trials, progress=True)

    # Save outputs
    try:
        save_results(results, args.csv, fmt="csv")
        print(f"Saved CSV: {args.csv}")
    except Exception as e:
        print(f"[WARN] CSV export skipped ({e})")

    try:
        save_results(results, args.jsonl, fmt="jsonl")
        print(f"Saved JSONL: {args.jsonl}")
    except Exception as e:
        print(f"[WARN] JSONL export failed ({e})")

    # Print quick summary (Option A: print three accuracy metrics)
    mean_rt = float(np.mean([r["RT"] for r in results]))
    mean_acc_realized = float(np.mean([r["accuracy"] for r in results]))
    mean_p_correct = float(np.mean([r.get("p_correct", 0.0) for r in results]))
    emp_acc_rate = float(np.mean([1.0 if r.get("correct", False) else 0.0 for r in results]))

    print(f"Mean RT: {mean_rt:.1f} ms")
    print(f"Accuracy (model p_correct): {mean_p_correct:.3f}")
    print(f"Accuracy (empirical rate):  {emp_acc_rate:.3f}")
    print(f"Accuracy (realized value):  {mean_acc_realized:.3f}")

    # Optional plotting
    if args.plot:
        try:
            import matplotlib
            matplotlib.use("Agg")  # headless
            import matplotlib.pyplot as plt
            import pandas as pd

            df = results_to_dataframe(results)
            # Expect stimulus.condition present from create_trial_design
            if "stimulus.condition" not in df.columns:
                # Fallback: synthesize condition from ext/mem means
                if {"ext_load_mean", "mem_load_mean"}.issubset(df.columns):
                    df["stimulus.condition"] = (
                        "ext" + df["ext_load_mean"].round(1).astype(str)
                        + "_mem" + df["mem_load_mean"].round(1).astype(str)
                    )
                else:
                    df["stimulus.condition"] = "unknown"

            agg = (
                df.groupby("stimulus.condition")
                .agg(mean_RT=("RT", "mean"), mean_acc=("accuracy", "mean"))
                .reset_index()
            )

            # RT plot
            plt.figure()
            plt.bar(agg["stimulus.condition"], agg["mean_RT"])  # default colors
            plt.xticks(rotation=45, ha="right")
            plt.ylabel("Mean RT (ms)")
            plt.title("RT by Condition")
            plt.tight_layout()
            rt_path = os.path.join(os.path.dirname(args.csv) or ".", "dual_task_RT.png")
            plt.savefig(rt_path, dpi=150)
            print(f"Saved plot: {rt_path}")

            # Accuracy plot
            plt.figure()
            plt.bar(agg["stimulus.condition"], agg["mean_acc"])  # default colors
            plt.xticks(rotation=45, ha="right")
            plt.ylabel("Mean Accuracy")
            plt.ylim(0, 1)
            plt.title("Accuracy by Condition")
            plt.tight_layout()
            acc_path = os.path.join(os.path.dirname(args.csv) or ".", "dual_task_ACC.png")
            plt.savefig(acc_path, dpi=150)
            print(f"Saved plot: {acc_path}")
        except Exception as e:
            print(f"[WARN] Plotting skipped ({e})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())