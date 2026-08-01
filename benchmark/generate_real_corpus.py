"""Generate live Inspect eval logs for the benchmark corpus.

Runs real agent trajectories across five conditions. Outputs `.eval` logs under
`benchmark/raw_logs/` and a manifest at `benchmark/corpus_manifest.jsonl`.

Requires model credentials in the environment (or Remote-jobs/.env).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "benchmark" / "corpus_manifest.jsonl"

CONDITIONS: list[tuple[str, int, dict[str, object]]] = [
    ("clean", 8, {}),
    ("readable_answer", 6, {}),
    ("impossible", 4, {}),
    ("leading_prompt", 4, {}),
    ("tight_budget", 4, {"message_limit": 3}),
]

TASK_BY_CONDITION = {
    "clean": "pytest_fix_clean",
    "readable_answer": "pytest_fix_readable_answer",
    "impossible": "pytest_fix_impossible",
    "leading_prompt": "pytest_fix_leading_prompt",
    "tight_budget": "pytest_fix_tight_budget",
}


def _load_dotenv() -> None:
    for candidate in (ROOT / ".env", ROOT.parents[2] / ".env"):
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value


def _resolve_model(explicit: str | None) -> str:
    if explicit:
        return explicit
    rank_model = os.environ.get("RANK_MODEL", "gpt-4o-mini")
    if "/" in rank_model:
        return rank_model
    return f"openai/{rank_model}"


def _import_task(condition: str):
    task_name = TASK_BY_CONDITION[condition]
    module_path = ROOT / "benchmark" / "tasks" / "pytest_fix.py"
    sys.path.insert(0, str(ROOT))
    import importlib.util

    spec = importlib.util.spec_from_file_location("pytest_fix", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import task module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, task_name)()


def _append_manifest(rows: list[dict[str, object]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _collect_eval_logs(log_dir: Path, condition: str, model: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for eval_path in sorted(log_dir.rglob("*.eval")):
        rel = eval_path.relative_to(ROOT).as_posix()
        sample_id = eval_path.stem
        rows.append(
            {
                "sample_id": sample_id,
                "log": rel,
                "condition": condition,
                "model": model,
                "labelled": False,
            }
        )
    return rows


def run(*, model: str | None, dry_run: bool) -> None:
    _load_dotenv()
    resolved_model = _resolve_model(model)
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("INSPECT_API_KEY"):
        raise SystemExit(
            "No OPENAI_API_KEY or INSPECT_API_KEY found. Set credentials or copy Remote-jobs/.env."
        )

    from inspect_ai import eval

    total_logs = 0
    for condition, limit, extra in CONDITIONS:
        log_dir = ROOT / "benchmark" / "raw_logs" / condition
        log_dir.mkdir(parents=True, exist_ok=True)
        task = _import_task(condition)
        print(f"\n=== {condition}: limit={limit} model={resolved_model} ===")
        if dry_run:
            print(f"Would eval into {log_dir}")
            continue

        kwargs: dict[str, object] = {
            "model": resolved_model,
            "limit": limit,
            "log_dir": str(log_dir),
            "log_format": "eval",
            "fail_on_error": False,
        }
        kwargs.update(extra)
        eval(task, **kwargs)

        rows = _collect_eval_logs(log_dir, condition, resolved_model)
        _append_manifest(rows)
        total_logs += len(rows)
        print(f"Wrote {len(rows)} eval logs to {log_dir}")

    print(f"\nDone. {total_logs} eval logs. Manifest: {MANIFEST_PATH}")
    print("Next: scout-det-label  (human labels each sample)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="Inspect model id (default: RANK_MODEL from .env)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(model=args.model, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
