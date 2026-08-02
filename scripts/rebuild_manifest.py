#!/usr/bin/env python3
"""Rebuild benchmark/corpus_manifest.jsonl from on-disk .eval logs (fixes bad sample_ids)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scout_deterministic.bench._eval_logs import consolidate_best_eval
from scout_deterministic.bench._guardrails import CONDITION_SPECS
from scout_deterministic.bench._transcript_load import list_eval_sample_ids

MANIFEST = ROOT / "benchmark" / "corpus_manifest.jsonl"
RAW = ROOT / "benchmark" / "raw_logs"


def main() -> None:
    rows: list[dict[str, object]] = []
    for condition, _, _ in CONDITION_SPECS:
        log_dir = RAW / condition
        if not log_dir.exists():
            continue
        best = consolidate_best_eval(ROOT, log_dir, condition)
        if best is None:
            continue
        rel = best.relative_to(ROOT).as_posix()
        for sample_id in list_eval_sample_ids(best):
            rows.append(
                {
                    "sample_id": sample_id,
                    "log": rel,
                    "condition": condition,
                    "model": "openai/deepseek-v4-flash",
                    "labelled": False,
                }
            )

    MANIFEST.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {MANIFEST}")


if __name__ == "__main__":
    main()
