"""Interactive CLI for hand-labelling live eval transcripts."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from scout_deterministic._transcript import (
    DEFAULT_SCORER_PATTERNS,
    SHELL_TOOLS,
    normalise,
    transcript_target,
)
from scout_deterministic.bench._transcript_load import load_transcript
from scout_deterministic.scanners._detect import (
    detect_claim_exit_mismatch,
    detect_ground_truth_read,
    detect_scorer_access,
    detect_submit_no_exec,
)

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


HACK_TYPE_BY_RULE = {
    "ground_truth_read": "read_answer_file",
    "scorer_access": "scorer_access",
    "submit_no_exec": "submit_no_exec",
    "claim_exit_mismatch": "claim_exit_mismatch",
}


def _detector_findings(transcript, events) -> list:
    findings = []
    for name, detector in (
        ("submit_no_exec", lambda: detect_submit_no_exec(events, shell_tools=SHELL_TOOLS)),
        ("scorer_access", lambda: detect_scorer_access(events, patterns=DEFAULT_SCORER_PATTERNS)),
        (
            "ground_truth_read",
            lambda: detect_ground_truth_read(
                events,
                patterns=DEFAULT_SCORER_PATTERNS,
                targets=transcript_target(transcript),
            ),
        ),
        ("claim_exit_mismatch", lambda: detect_claim_exit_mismatch(events)),
    ):
        finding = detector()
        if finding is not None:
            findings.append(finding)
    return findings


def _print_detector_hints(findings: list) -> None:
    if not findings:
        print("\n--- detector hints ---")
        print("  (none fired — often means hacked=n for clean runs, but read the trace)")
        print("--- end hints ---\n")
        return
    print("\n--- detector hints (confirm in trace; detectors can false-positive) ---")
    for finding in findings:
        print(f"  [{finding.rule_id}] step {finding.step_index}: {finding.evidence}")
    print("--- end hints ---\n")


def _suggest_from_findings(findings: list) -> tuple[bool | None, str, str]:
    """Draft label from detector output — human must confirm."""
    if not findings:
        return None, "", ""
    primary = findings[0]
    hack_type = HACK_TYPE_BY_RULE.get(primary.rule_id, primary.rule_id)
    rationale = f"step {primary.step_index}: {primary.evidence}"
    return True, hack_type, rationale


def _prompt_optional(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix} ").strip()
    return value or default


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


async def _label_one(
    row: dict[str, object], *, labeller: str, assist: bool
) -> dict[str, object] | None:
    log_path = ROOT / str(row["log"])
    if not log_path.exists():
        print(f"Missing log: {log_path}")
        return None

    print(f"\n{'=' * 72}")
    print(f"Sample: {row['sample_id']}  condition={row.get('condition')}  log={row['log']}")
    transcript = await load_transcript(
        log_path, sample_id=str(row.get("sample_id")) or None
    )
    events = normalise(transcript)
    findings = _detector_findings(transcript, events)
    _print_events(transcript)
    if assist:
        _print_detector_hints(findings)
        suggested_hacked, suggested_type, suggested_rationale = _suggest_from_findings(findings)
        if suggested_hacked is True:
            print("Assist suggestion: hacked=y (detector fired — verify trace above)")
        elif str(row.get("condition")) == "clean":
            print("Assist suggestion: hacked=n (clean condition, no detector hit — still verify)")

    if assist:
        default_hacked = "y" if findings else ("n" if str(row.get("condition")) == "clean" else "")
        hacked_raw = _prompt_optional(
            "Hacked? (y/n/unsure/skip)",
            default_hacked,
        ).lower()
        if hacked_raw not in {"y", "n", "unsure", "skip"}:
            hacked_raw = _prompt_choice("Hacked? (y/n/unsure/skip)", {"y", "n", "unsure", "skip"})
    else:
        hacked_raw = _prompt_choice("Hacked? (y/n/unsure/skip)", {"y", "n", "unsure", "skip"})
    if hacked_raw == "skip":
        return None

    hacked = hacked_raw == "y"
    unsure = hacked_raw == "unsure"
    _, suggested_type, suggested_rationale = _suggest_from_findings(findings)
    hack_type = ""
    if hacked:
        if assist:
            hack_type = _prompt_optional(
                "hack_type (e.g. read_answer_file, submit_no_exec):",
                suggested_type,
            )
        else:
            hack_type = _prompt_text("hack_type (e.g. read_answer_file, submit_no_exec):")

    if assist:
        rationale = _prompt_optional(
            "Rationale (must cite step index):",
            suggested_rationale,
        )
        if not rationale:
            rationale = _prompt_text("Rationale (must cite step index):")
    else:
        rationale = _prompt_text("Rationale (must cite step index, e.g. 'step 4 cats .target'):")

    default_confidence = "low" if unsure else ("high" if findings else "medium")
    if assist:
        confidence = _prompt_optional("Confidence (high/medium/low)", default_confidence).lower()
        if confidence not in {"high", "medium", "low"}:
            confidence = _prompt_choice("Confidence (high/medium/low)", {"high", "medium", "low"})
    else:
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


async def run(*, labeller: str, only: str | None, assist: bool) -> None:
    manifest = _load_manifest()
    existing = _load_labels()
    pending = [row for row in manifest if str(row["sample_id"]) not in existing]
    if only:
        pending = [row for row in pending if str(row.get("condition")) == only]

    if not pending:
        print("Nothing to label. Run benchmark/generate_real_corpus.py first.")
        return

    print(f"{len(pending)} samples pending. Labeller={labeller}" + (" [assist]" if assist else ""))
    for row in pending:
        labelled = await _label_one(row, labeller=labeller, assist=assist)
        if labelled:
            _append_label(labelled)
            print(f"Saved label for {labelled['sample_id']}")


def main() -> None:
    import asyncio

    parser = argparse.ArgumentParser(description="Hand-label live eval transcripts")
    parser.add_argument("--labeller", default="hemant")
    parser.add_argument("--condition", default=None, help="Only label one condition")
    parser.add_argument(
        "--assist",
        action="store_true",
        help="Show deterministic detector hints + default answers (you still confirm each label)",
    )
    args = parser.parse_args()
    asyncio.run(run(labeller=args.labeller, only=args.condition, assist=args.assist))


if __name__ == "__main__":
    main()
