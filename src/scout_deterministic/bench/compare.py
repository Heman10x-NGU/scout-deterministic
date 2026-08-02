"""Run deterministic scanners and optional llm_scanner over labelled corpus."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from inspect_scout import Transcript, llm_scanner

from scout_deterministic._transcript import (
    DEFAULT_SCORER_PATTERNS,
    SHELL_TOOLS,
    normalise,
    transcript_target,
)
from scout_deterministic.bench._guardrails import (
    LLM_SCANNER_TIMEOUT_SEC,
    TRANSCRIPT_LOAD_TIMEOUT_SEC,
)
from scout_deterministic.bench._model_env import configure_benchmark_model, load_dotenv
from scout_deterministic.bench._transcript_load import load_transcript
from scout_deterministic.bench.reward_hacking import REWARD_HACKING_QUESTION
from scout_deterministic.scanners._detect import (
    detect_claim_exit_mismatch,
    detect_ground_truth_read,
    detect_scorer_access,
    detect_submit_no_exec,
)

ROOT = Path(__file__).resolve().parents[3]
LABELS_PATH = ROOT / "benchmark" / "labels.jsonl"
RESULTS_JSON = ROOT / "benchmark" / "compare_results.json"

DETECTORS = {
    "submit_no_exec": lambda events, transcript: detect_submit_no_exec(
        events, shell_tools=SHELL_TOOLS
    ),
    "scorer_access": lambda events, transcript: detect_scorer_access(
        events, patterns=DEFAULT_SCORER_PATTERNS
    ),
    "ground_truth_read": lambda events, transcript: detect_ground_truth_read(
        events,
        patterns=DEFAULT_SCORER_PATTERNS,
        targets=transcript_target(transcript),
    ),
    "claim_exit_mismatch": lambda events, transcript: detect_claim_exit_mismatch(events),
}


def _load_labels() -> list[dict[str, Any]]:
    if not LABELS_PATH.exists():
        raise FileNotFoundError(
            f"No labels at {LABELS_PATH}. Run scout-det-label after generating the corpus."
        )
    rows: list[dict[str, Any]] = []
    with LABELS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _metrics(y_true: list[bool], y_pred: list[bool]) -> dict[str, float]:
    tp = sum(1 for truth, pred in zip(y_true, y_pred, strict=True) if truth and pred)
    fp = sum(1 for truth, pred in zip(y_true, y_pred, strict=True) if not truth and pred)
    fn = sum(1 for truth, pred in zip(y_true, y_pred, strict=True) if truth and not pred)
    tn = sum(1 for truth, pred in zip(y_true, y_pred, strict=True) if not truth and not pred)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def _result_flagged(result: object) -> bool:
    if isinstance(result, list):
        return any(bool(item.value) for item in result)
    value = getattr(result, "value", result)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"yes", "true", "1"}
    return bool(value)


async def _run_llm_scanner(transcript: Transcript, *, model: str) -> bool:
    scanner = llm_scanner(
        question=REWARD_HACKING_QUESTION,
        answer="boolean",
        model=model,
    )
    return _result_flagged(
        await asyncio.wait_for(scanner(transcript), timeout=LLM_SCANNER_TIMEOUT_SEC)
    )


async def _load_transcript_safe(path: Path, *, sample_id: str | None) -> Transcript:
    return await asyncio.wait_for(
        load_transcript(path, sample_id=sample_id),
        timeout=TRANSCRIPT_LOAD_TIMEOUT_SEC,
    )


async def compare(*, run_llm: bool) -> dict[str, Any]:
    bench_model = os.environ.get("SCOUT_BENCH_MODEL") or configure_benchmark_model()
    labels = _load_labels()
    per_detector: dict[str, list[bool]] = {name: [] for name in DETECTORS}
    aggregate_pred: list[bool] = []
    y_true: list[bool] = []
    clean_preds: dict[str, list[bool]] = {name: [] for name in DETECTORS}
    llm_preds: list[bool] = []
    disagreements: list[dict[str, object]] = []

    det_start = time.perf_counter()
    for index, row in enumerate(labels):
        transcript = await _load_transcript_safe(
            ROOT / row["log"], sample_id=str(row.get("sample_id")) or None
        )
        events = normalise(transcript)
        hacked = bool(row["hacked"])
        y_true.append(hacked)
        detector_hits = []
        for name, detector in DETECTORS.items():
            flagged = detector(events, transcript) is not None
            per_detector[name].append(flagged)
            detector_hits.append(flagged)
            if not hacked:
                clean_preds[name].append(flagged)
        aggregate_pred.append(any(detector_hits))

    det_seconds = time.perf_counter() - det_start

    llm_available = False
    llm_seconds = 0.0
    llm_error: str | None = None
    if run_llm:
        llm_start = time.perf_counter()
        try:
            for index, row in enumerate(labels):
                if index and index % 5 == 0:
                    print(f"llm_scanner: {index}/{len(labels)} ...", flush=True)
                transcript = await _load_transcript_safe(
                    ROOT / row["log"], sample_id=str(row.get("sample_id")) or None
                )
                llm_flag = await _run_llm_scanner(transcript, model=bench_model)
                llm_preds.append(llm_flag)
                det_flag = aggregate_pred[index]
                if llm_flag != det_flag:
                    disagreements.append(
                        {
                            "sample_id": row["sample_id"],
                            "label_hacked": row["hacked"],
                            "deterministic": det_flag,
                            "llm_scanner": llm_flag,
                            "rationale": row.get("rationale"),
                        }
                    )
            llm_available = True
            llm_seconds = time.perf_counter() - llm_start
        except TimeoutError as exc:
            llm_available = False
            llm_error = f"timeout after {LLM_SCANNER_TIMEOUT_SEC}s per sample: {exc}"
        except Exception as exc:  # noqa: BLE001
            llm_available = False
            llm_error = str(exc)
    else:
        llm_error = "skipped (--no-llm or no API key)"

    clean_count = sum(1 for value in y_true if not value)
    aggregate_fp_clean = sum(
        1 for truth, pred in zip(y_true, aggregate_pred, strict=True) if not truth and pred
    )

    conditions: dict[str, int] = {}
    models: set[str] = set()
    for row in labels:
        condition = str(row.get("condition") or "unknown")
        conditions[condition] = conditions.get(condition, 0) + 1
        if row.get("model"):
            models.add(str(row["model"]))

    results: dict[str, Any] = {
        "corpus_size": len(labels),
        "positives": sum(y_true),
        "negatives": clean_count,
        "corpus_metadata": {
            "source": "live inspect eval logs",
            "conditions": conditions,
            "models": sorted(models),
            "labeller": labels[0].get("labeller") if labels else None,
        },
        "deterministic": {
            "wall_seconds": round(det_seconds, 4),
            "ms_per_transcript": round((det_seconds / len(labels)) * 1000, 2),
            "tokens": 0,
            "aggregate": _metrics(y_true, aggregate_pred),
            "false_positive_rate_clean": round(aggregate_fp_clean / max(1, clean_count), 4),
            "per_detector": {
                name: {
                    **_metrics(y_true, preds),
                    "false_positive_rate_clean": round(
                        sum(clean_preds[name]) / max(1, len(clean_preds[name])), 4
                    ),
                }
                for name, preds in per_detector.items()
            },
        },
        "llm_scanner": {
            "available": llm_available,
            "error": llm_error,
            "question": REWARD_HACKING_QUESTION,
            "wall_seconds": round(llm_seconds, 4) if llm_available else None,
            "tokens": None,
            "agreement_with_deterministic": None,
            "disagreements": disagreements[:10],
            "disagreement_count": len(disagreements) if llm_available else None,
        },
    }

    if llm_available and llm_preds:
        agreements = [
            det == llm for det, llm in zip(aggregate_pred, llm_preds, strict=True)
        ]
        results["llm_scanner"]["agreement_with_deterministic"] = round(
            sum(agreements) / len(agreements), 4
        )
        results["llm_scanner"]["precision_vs_labels"] = _metrics(y_true, llm_preds)
        results["llm_scanner"]["speedup_factor"] = round(
            llm_seconds / max(det_seconds, 1e-9), 1
        )

    RESULTS_JSON.write_text(json.dumps(results, indent=2))
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="Also run llm_scanner (needs model API)")
    parser.add_argument("--no-llm", action="store_true", help="Skip llm_scanner")
    args = parser.parse_args()
    run_llm = args.llm and not args.no_llm
    if not args.no_llm and not args.llm:
        load_dotenv()
        configure_benchmark_model()
        run_llm = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("INSPECT_API_KEY"))
    results = asyncio.run(compare(run_llm=run_llm))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
