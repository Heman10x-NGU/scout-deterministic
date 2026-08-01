"""Simple CLI helper for hand-labelling (prints unlabelled samples)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABELS_PATH = ROOT / "benchmark" / "labels.jsonl"


def main() -> None:
    if not LABELS_PATH.exists():
        print("No labels yet. Run: python benchmark/generate_corpus.py")
        return
    with LABELS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            print(
                f"{row['sample_id']}: hacked={row['hacked']} "
                f"type={row.get('hack_type')} — {row.get('rationale')}"
            )


if __name__ == "__main__":
    main()
