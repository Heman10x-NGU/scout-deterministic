#!/usr/bin/env python3
"""Pre-flight check before labelling — catches empty logs, dupes, and missing conditions."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scout_deterministic.bench._eval_logs import best_eval_path_async, consolidate_best_eval_async
from scout_deterministic.bench._guardrails import CONDITION_SPECS, condition_names
from scout_deterministic.bench._transcript_load import (
    list_eval_sample_ids_async,
    load_transcript,
)

MANIFEST = ROOT / "benchmark" / "corpus_manifest.jsonl"
RAW = ROOT / "benchmark" / "raw_logs"


def _load_manifest_rows() -> list[dict[str, object]]:
    if not MANIFEST.exists():
        return []
    rows: list[dict[str, object]] = []
    with MANIFEST.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


async def _check_sample(log: Path, sample_id: str) -> str | None:
    try:
        transcript = await asyncio.wait_for(
            load_transcript(log, sample_id=sample_id),
            timeout=60,
        )
    except TimeoutError:
        return "transcript load timed out (>60s)"
    except Exception as exc:  # noqa: BLE001
        return f"transcript load failed: {exc}"

    if not transcript.events and not transcript.messages:
        return "empty transcript (no events/messages)"
    return None


async def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    expected_total = sum(count for _, count, _ in CONDITION_SPECS)
    print(f"Expected samples: {expected_total} across {len(CONDITION_SPECS)} conditions\n")

    manifest = _load_manifest_rows()
    by_key: dict[tuple[str, str], dict[str, object]] = {}
    for row in manifest:
        key = (str(row["log"]), str(row["sample_id"]))
        if key in by_key:
            warnings.append(f"duplicate manifest row: {key}")
        by_key[key] = row

    for condition, want, _ in CONDITION_SPECS:
        log_dir = RAW / condition
        best = await consolidate_best_eval_async(ROOT, log_dir, condition)
        if best is None:
            errors.append(f"{condition}: no .eval log in {log_dir} or logs/")
            continue

        ids = await list_eval_sample_ids_async(best)
        if len(ids) < want:
            errors.append(
                f"{condition}: best eval has {len(ids)}/{want} samples ({best.name})"
            )
        elif len(ids) > want:
            warnings.append(
                f"{condition}: best eval has {len(ids)} samples (expected {want})"
            )

        manifest_ids = {
            str(r["sample_id"])
            for r in manifest
            if str(r.get("condition")) == condition
        }
        missing_manifest = set(ids) - manifest_ids
        if missing_manifest:
            warnings.append(
                f"{condition}: {len(missing_manifest)} sample(s) not in manifest "
                f"(re-run generate with --refresh-manifest or full regen)"
            )

        for sample_id in ids[:2]:
            rel = best.relative_to(ROOT).as_posix()
            issue = await _check_sample(best, sample_id)
            if issue:
                errors.append(f"{condition}/{sample_id} ({rel}): {issue}")

    unknown = {str(r.get("condition")) for r in manifest} - set(condition_names())
    for name in sorted(unknown - {""}):
        warnings.append(f"manifest references unknown condition: {name}")

    print("--- errors ---")
    if errors:
        for item in errors:
            print(f"  ERROR: {item}")
    else:
        print("  (none)")

    print("\n--- warnings ---")
    if warnings:
        for item in warnings:
            print(f"  WARN: {item}")
    else:
        print("  (none)")

    print(f"\nManifest rows: {len(manifest)} (unique log+sample keys: {len(by_key)})")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
