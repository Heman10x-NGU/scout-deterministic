#!/usr/bin/env python3
"""One-off migration: move synthetic benchmark artifacts to tests/."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_TRANSCRIPTS = ROOT / "benchmark" / "transcripts"
DST_TRANSCRIPTS = ROOT / "tests" / "fixtures" / "transcripts"

for path in (
    ROOT / "benchmark" / "labels.jsonl",
    ROOT / "benchmark" / "compare_results.json",
):
    if path.exists():
        path.unlink()

if SRC_TRANSCRIPTS.exists():
    DST_TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    for item in SRC_TRANSCRIPTS.glob("*.json"):
        target = DST_TRANSCRIPTS / item.name
        if not target.exists():
            shutil.move(str(item), str(target))
    if not any(SRC_TRANSCRIPTS.iterdir()):
        SRC_TRANSCRIPTS.rmdir()

print("T1 migration complete.")
