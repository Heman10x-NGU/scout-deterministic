"""Generate live Inspect eval logs for the benchmark corpus.

Runs real agent trajectories across five conditions. Outputs `.eval` logs under
`benchmark/raw_logs/` and a manifest at `benchmark/corpus_manifest.jsonl`.

Guardrails (see bench/_guardrails.py):
- Per-sample message_limit, time_limit, working_limit, token_limit
- max_samples=1 (sequential), retry_on_error=0, score_on_error=True
- --skip-existing skips conditions whose latest eval already has enough samples
- API smoke test before any eval run

Requires model credentials in the environment (see `.env.example`).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from scout_deterministic.bench._eval_logs import (
    best_eval_path,
    consolidate_best_eval,
    sample_count,
)
from scout_deterministic.bench._guardrails import (
    CONDITION_SPECS,
    CONDITION_WALL_ESTIMATE_SEC,
    EVAL_BASE_KWARGS,
    condition_names,
)
from scout_deterministic.bench._model_env import configure_benchmark_model, verify_model_api
from scout_deterministic.bench._transcript_load import list_eval_sample_ids

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "benchmark" / "corpus_manifest.jsonl"

TASK_BY_CONDITION = {
    "clean": "pytest_fix_clean",
    "readable_answer": "pytest_fix_readable_answer",
    "impossible": "pytest_fix_impossible",
    "leading_prompt": "pytest_fix_leading_prompt",
    "tight_budget": "pytest_fix_tight_budget",
}


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


def _load_manifest_keys() -> set[tuple[str, str]]:
    if not MANIFEST_PATH.exists():
        return set()
    keys: set[tuple[str, str]] = set()
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            keys.add((str(row["log"]), str(row["sample_id"])))
    return keys


def _append_manifest(rows: list[dict[str, object]], *, existing: set[tuple[str, str]]) -> int:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    added = 0
    with MANIFEST_PATH.open("a", encoding="utf-8") as handle:
        for row in rows:
            key = (str(row["log"]), str(row["sample_id"]))
            if key in existing:
                continue
            handle.write(json.dumps(row) + "\n")
            existing.add(key)
            added += 1
    return added


def _condition_complete(log_dir: Path, condition: str, expected_samples: int) -> bool:
    best = best_eval_path(log_dir, repo_root=ROOT, condition=condition)
    if best is None:
        return False
    return sample_count(best) >= expected_samples


def _retry_kwargs(caps: dict[str, object], log_dir: Path) -> dict[str, object]:
    out: dict[str, object] = {
        "log_dir": str(log_dir),
        "log_format": "eval",
    }
    for key in (
        "max_subprocesses",
        "display",
        "fail_on_error",
        "score_on_error",
        "retry_on_error",
    ):
        if key in caps:
            out[key] = caps[key]
    return out


def _collect_eval_rows(
    log_dir: Path, condition: str, model: str, *, eval_path: Path | None = None
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    targets = [eval_path] if eval_path else sorted(log_dir.glob("*.eval"))
    for path in targets:
        rel = path.relative_to(ROOT).as_posix()
        for sample_id in list_eval_sample_ids(path):
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


def _print_eta(conditions: list[tuple[str, int, dict[str, object]]]) -> None:
    total_sec = sum(CONDITION_WALL_ESTIMATE_SEC.get(name, 0) for name, _, _ in conditions)
    print(
        f"Wall-clock budget (worst case, all caps hit): ~{total_sec // 60} min "
        f"for {len(conditions)} condition(s). Interrupt with Ctrl+C — score_on_error saves partial logs."
    )


def run(
    *,
    model: str | None,
    dry_run: bool,
    only: list[str] | None = None,
    from_condition: str | None = None,
    skip_existing: bool = False,
    refresh_manifest: bool = False,
    force: bool = False,
) -> None:
    conditions = CONDITION_SPECS
    if only:
        wanted = set(only)
        conditions = [c for c in CONDITION_SPECS if c[0] in wanted]
        missing = wanted - {c[0] for c in conditions}
        if missing:
            raise SystemExit(f"Unknown condition(s): {', '.join(sorted(missing))}")
    elif from_condition:
        names = condition_names()
        if from_condition not in names:
            raise SystemExit(f"Unknown --from-condition {from_condition!r}")
        conditions = CONDITION_SPECS[names.index(from_condition) :]

    resolved_model = configure_benchmark_model(model)
    if not dry_run:
        print(f"API smoke test for {resolved_model} ...")
        verify_model_api(resolved_model)
        print("API OK")

    from inspect_ai.model import get_model

    _print_eta(conditions)
    manifest_keys = _load_manifest_keys()
    total_new = 0

    for condition, limit, extra in conditions:
        configure_benchmark_model(model)
        log_dir = ROOT / "benchmark" / "raw_logs" / condition
        log_dir.mkdir(parents=True, exist_ok=True)

        if skip_existing and not force and _condition_complete(log_dir, condition, limit):
            best = consolidate_best_eval(ROOT, log_dir, condition)
            if best is None:
                print(f"\n=== {condition}: SKIP flag set but no eval found ===")
                continue
            print(f"\n=== {condition}: SKIP (best eval has >={limit} samples: {best.name}) ===")
            if refresh_manifest and best:
                rows = _collect_eval_rows(log_dir, condition, resolved_model, eval_path=best)
                added = _append_manifest(rows, existing=manifest_keys)
                print(f"Refreshed manifest: +{added} row(s)")
                total_new += added
            continue

        task = _import_task(condition)
        caps = {**EVAL_BASE_KWARGS, **extra}
        best = best_eval_path(log_dir, repo_root=ROOT, condition=condition)
        have = sample_count(best) if best else 0
        print(f"\n=== {condition}: want={limit} have={have} model={resolved_model} ===")
        print(f"    caps: {caps}")
        if dry_run:
            action = "eval_retry" if best and have < limit else "eval"
            print(f"Would {action} into {log_dir}")
            continue

        from inspect_ai import eval, eval_retry

        if best and have < limit and not force:
            print(f"    resume: eval_retry on {best.name}")
            eval_retry(str(best), **_retry_kwargs(caps, log_dir))
        else:
            base_url = os.environ.get("OPENAI_BASE_URL")
            inspect_model = get_model(resolved_model, base_url=base_url)
            kwargs: dict[str, object] = {
                "model": inspect_model,
                "limit": limit,
                "log_dir": str(log_dir),
                "log_format": "eval",
            }
            kwargs.update(caps)
            eval(task, **kwargs)

        target_eval = consolidate_best_eval(ROOT, log_dir, condition)

        if target_eval is None:
            print(f"WARNING: no .eval written under {log_dir}")
            continue

        rows = _collect_eval_rows(log_dir, condition, resolved_model, eval_path=target_eval)
        added = _append_manifest(rows, existing=manifest_keys)
        total_new += added
        print(f"Eval {target_eval.name}: {len(rows)} sample(s); manifest +{added}")

    print(f"\nDone. Manifest +{total_new} new row(s): {MANIFEST_PATH}")
    print("Validate: python scripts/validate_corpus.py")
    print("Next: scout-det-label  (human labels each sample)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default=None,
        help="Inspect model id (default: deepseek-v4-flash if DEEPSEEK_API_KEY set, else RANK_MODEL)",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--only",
        nargs="+",
        choices=condition_names(),
        metavar="CONDITION",
        help="Run only these conditions",
    )
    parser.add_argument(
        "--from-condition",
        choices=condition_names(),
        help="Skip conditions before this one",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip a condition if its latest .eval already contains all samples",
    )
    parser.add_argument(
        "--refresh-manifest",
        action="store_true",
        help="With --skip-existing, still append missing manifest rows from on-disk evals",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run even if --skip-existing would skip",
    )
    args = parser.parse_args()
    if args.only and args.from_condition:
        raise SystemExit("Use --only or --from-condition, not both.")
    run(
        model=args.model,
        dry_run=args.dry_run,
        only=args.only,
        from_condition=args.from_condition,
        skip_existing=args.skip_existing,
        refresh_manifest=args.refresh_manifest,
        force=args.force,
    )


if __name__ == "__main__":
    main()
