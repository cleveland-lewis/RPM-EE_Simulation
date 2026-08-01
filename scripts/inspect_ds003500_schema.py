#!/usr/bin/env python3
"""
Inspect a downloaded ds003500 BIDS tree and print its actual column names.

Run this FIRST after downloading ds003500 (openneuro.org/datasets/ds003500,
CC0, no DUA), BEFORE trusting src/adapters/ds003500.py -- that adapter's
column-name guesses (_CANDIDATE_COLUMNS, _GROUP_COLUMN_CANDIDATES) were
written from the dataset's public description, not from the real files, and
need to be corrected against this script's output.

Usage:
    python scripts/inspect_ds003500_schema.py /path/to/ds003500
"""

import csv
import sys
from pathlib import Path


def inspect(bids_root: Path):
    participants = bids_root / "participants.tsv"
    if participants.exists():
        with participants.open(newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader)
            first_rows = [next(reader, None) for _ in range(3)]
        print(f"participants.tsv columns: {header}")
        for row in first_rows:
            if row:
                print(f"  sample row: {row}")
    else:
        print("participants.tsv NOT FOUND at expected root -- check path")

    print()

    subject_dirs = sorted(p for p in bids_root.glob("sub-*") if p.is_dir())
    if not subject_dirs:
        print("No sub-* directories found -- check bids_root path")
        return

    first_subject = subject_dirs[0]
    func_dir = first_subject / "func"
    events_files = sorted(func_dir.glob("*_events.tsv")) if func_dir.exists() else []

    if not events_files:
        print(f"No events.tsv found under {func_dir}")
        return

    print(f"Found {len(events_files)} events.tsv files for {first_subject.name}:")
    for ef in events_files:
        print(f"  {ef.name}")

    print()
    first_events = events_files[0]
    with first_events.open(newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        sample = [next(reader, None) for _ in range(5)]
    print(f"{first_events.name} columns: {header}")
    for row in sample:
        if row:
            print(f"  sample row: {row}")

    print()
    print("Next step: update _CANDIDATE_COLUMNS and _GROUP_COLUMN_CANDIDATES")
    print("in src/adapters/ds003500.py to match the real column names above,")
    print("and confirm RT units (seconds vs ms) and go/no-go trial semantics")
    print("for the *Inh task conditions against dataset/code/ (PsyScope scripts)")
    print("before trusting any evidence-mapping output from that adapter.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} /path/to/ds003500")
        sys.exit(1)
    inspect(Path(sys.argv[1]))
