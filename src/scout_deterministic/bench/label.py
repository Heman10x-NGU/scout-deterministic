"""Interactive CLI for hand-labelling live eval transcripts."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from scout_deterministic._transcript import normalise
from scout_deterministic.bench._transcript_load import load_transcript

ROOT = Path(__file__).resolve().parents[3]
RAW_LOGS = ROOT / "benchmark" / "raw_logs"
MANIFEST_PATH = ROOT / "benchmark" / "corpus_manifest.jsonl"
LABELS_PATH = ROOT / "benchmark" / "labels.jsonl"


def _load_manifest() -> list[dict[str, object]]:
    if MANIFEST_PATH.exists():
        rows: list[dict[str, object]] = []
        with MANIFEST_PATH.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows
    rows = []
    for eval_path in sorted(RAW_LOGS.rglob("*.eval")):
        rel = eval_path.relative_to(ROOT).as_posix()
        condition = eval_path.parent.name
        rows.append(
            {
                "sample_id": eval_path.stem,
                "log": rel,
                "condition": condition,
            }
        )
    return rows


def _load_labels() -> dict[str, dict[str, object]]:
    if not LABELS_PATH.exists():
        return {}
    labels: dict[str, dict[str, object]] = {}
    with LABELS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                labels[str(row["sample_id"])] = row
    return labels


def _append_label(row: dict[str, object]) -> None:
    LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LABELS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def _print_events(transcript) -> None:
    events = normalise(transcript)
    print("\n--- transcript events ---")
    for event in events:
        parts = [f"[{event.index:02d}] {event.kind}"]
        if event.tool_name:
            parts.append(f"tool={event.tool_name}")
        if event.command:
            parts.append(f"cmd={event.command[:120]}")
        if event.paths:
            parts.append(f"paths={event.paths}")
        if event.output:
            snippet = event.output.replace("\n", " ")[:160]
            parts.append(f"out={snippet}")
        if event.exit_code is not None:
            parts.append(f"exit={event.exit_code}")
        if event.text:
            snippet = event.text.replace("\n", " ")[:160]
            parts.append(f"text={snippet}")
        print(" | ".join(parts))
    print("--- end ---\n")


def _prompt_choice(prompt: str, choices: set[str]) -> str:
    while True:
        value = input(f"{prompt} ").strip().lower()
        if value in choices:
            return value
        print(f"Choose one of: {', '.join(sorted(choices))}")


def _prompt_text(prompt: str) -> str:
    while True:
        value = input(f"{prompt} ").strip()
        if value:
            return value
        print("Required — cite a specific step index.")


async def _label_one(row: dict[str, object], *, labeller: str) -> dict[str, object] | None:
    log_path = ROOT / str(row["log"])
    if not log_path.exists():
        print(f"Missing log: {log_path}")
        return None

    print(f"\n{'=' * 72}")
    print(f"Sample: {row['sample_id']}  condition={row.get('condition')}  log={row['log']}")
    transcript = await load_transcript(log_path)
    _print_events(transcript)

    hacked_raw = _prompt_choice("Hacked? (y/n/unsure/skip)", {"y", "n", "unsure", "skip"})
    if hacked_raw == "skip":
        return None

    hacked = hacked_raw == "y"
    unsure = hacked_raw == "unsure"
    hack_type = ""
    if hacked:
        hack_type = _prompt_text("hack_type (e.g. read_answer_file, submit_no_exec):")

    rationale = _prompt_text("Rationale (must cite step index, e.g. 'step 4 cats .target'):")
    confidence = _prompt_choice("Confidence (high/medium/low)", {"high", "medium", "low"})
    if unsure:
        confidence = "low"

    return {
        "sample_id": row["sample_id"],
        "log": row["log"],
        "hacked": hacked,
        "hack_type": hack_type or None,
        "rationale": rationale,
        "labeller": labeller,
        "labelled_at": datetime.now(UTC).isoformat(),
        "confidence": confidence,
        "condition": row.get("condition"),
    }


async def run(*, labeller: str, only: str | None) -> None:
    manifest = _load_manifest()
    existing = _load_labels()
    pending = [row for row in manifest if str(row["sample_id"]) not in existing]
    if only:
        pending = [row for row in pending if str(row.get("condition")) == only]

    if not pending:
        print("Nothing to label. Run benchmark/generate_real_corpus.py first.")
        return

    print(f"{len(pending)} samples pending. Labeller={labeller}")
    for row in pending:
        labelled = await _label_one(row, labeller=labeller)
        if labelled:
            _append_label(labelled)
            print(f"Saved label for {labelled['sample_id']}")


def main() -> None:
    import asyncio

    parser = argparse.ArgumentParser(description="Hand-label live eval transcripts")
    parser.add_argument("--labeller", default="hemant")
    parser.add_argument("--condition", default=None, help="Only label one condition")
    args = parser.parse_args()
    asyncio.run(run(labeller=args.labeller, only=args.condition))


if __name__ == "__main__":
    main()
