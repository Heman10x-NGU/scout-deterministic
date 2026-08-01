"""Run Scout scanners over benchmark JSON transcripts via the Python API.

Scout CLI (`scout scan -T ...`) expects Inspect `.eval` log files. Our v0
benchmark stores serialised `Transcript` JSON. This script is the supported
path until we export real eval logs.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from inspect_scout import Transcript

from scout_deterministic.scout_scanners import (
    claim_exit_mismatch,
    ground_truth_read,
    scorer_access,
    submit_no_exec,
)

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "benchmark" / "labels.jsonl"

SCANNERS = {
    "submit_no_exec": submit_no_exec,
    "scorer_access": scorer_access,
    "ground_truth_read": ground_truth_read,
    "claim_exit_mismatch": claim_exit_mismatch,
}


def _load_labels() -> list[dict]:
    rows = []
    with LABELS.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


async def _scan_one(scanner_factory, transcript: Transcript) -> bool:
    scanner = scanner_factory()
    result = await scanner(transcript)
    if isinstance(result, list):
        return any(bool(item.value) for item in result)
    return bool(result.value)


async def run(limit: int | None) -> list[dict]:
    rows = _load_labels()
    if limit is not None:
        rows = rows[:limit]
    output: list[dict] = []
    for row in rows:
        transcript = Transcript.model_validate_json((ROOT / row["log"]).read_text())
        flags = {}
        for name, factory in SCANNERS.items():
            flags[name] = await _scan_one(factory, transcript)
        output.append(
            {
                "sample_id": row["sample_id"],
                "label_hacked": row["hacked"],
                "any_flag": any(flags.values()),
                **flags,
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="Print JSON lines")
    args = parser.parse_args()
    results = asyncio.run(run(args.limit))
    if args.json:
        for row in results:
            print(json.dumps(row))
        return
    print(f"{'sample_id':<28} {'label':>5} {'any':>4}  flags")
    for row in results:
        flag_names = [name for name in SCANNERS if row[name]]
        print(
            f"{row['sample_id']:<28} {str(row['label_hacked']):>5} "
            f"{str(row['any_flag']):>4}  {', '.join(flag_names) or '-'}"
        )


if __name__ == "__main__":
    main()
