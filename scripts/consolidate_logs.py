#!/usr/bin/env python3
"""Copy best eval logs from ./logs into benchmark/raw_logs/<condition>/."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scout_deterministic.bench._eval_logs import CONDITION_LOG_SLUG, consolidate_best_eval
from scout_deterministic.bench._guardrails import condition_names


def main() -> None:
    raw = ROOT / "benchmark" / "raw_logs"
    for condition in condition_names():
        log_dir = raw / condition
        best = consolidate_best_eval(ROOT, log_dir, condition)
        if best:
            print(f"{condition}: {best.relative_to(ROOT)} ({CONDITION_LOG_SLUG[condition]})")
        else:
            print(f"{condition}: (no eval found)")


if __name__ == "__main__":
    main()
