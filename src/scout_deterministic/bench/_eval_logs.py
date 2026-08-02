"""Helpers for picking and inspecting on-disk Inspect `.eval` logs."""

from __future__ import annotations

import shutil
from pathlib import Path

from scout_deterministic.bench._transcript_load import (
    list_eval_sample_ids,
    list_eval_sample_ids_async,
)

# Substring in Inspect log filenames for each benchmark condition.
CONDITION_LOG_SLUG: dict[str, str] = {
    "clean": "pytest-fix-clean",
    "readable_answer": "pytest-fix-readable-answer",
    "impossible": "pytest-fix-impossible",
    "leading_prompt": "pytest-fix-leading-prompt",
    "tight_budget": "pytest-fix-tight-budget",
}


def eval_search_dirs(repo_root: Path, log_dir: Path) -> list[Path]:
    """Directories that may hold eval logs (raw_logs + Inspect default ./logs)."""
    dirs = [log_dir]
    inspect_logs = repo_root / "logs"
    if inspect_logs.exists():
        dirs.append(inspect_logs)
    return dirs


def candidate_eval_paths(
    repo_root: Path, log_dir: Path, condition: str
) -> list[Path]:
    slug = CONDITION_LOG_SLUG[condition]
    found: list[Path] = []
    seen: set[Path] = set()
    for base in eval_search_dirs(repo_root, log_dir):
        for path in base.glob("*.eval"):
            if slug not in path.name:
                continue
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                found.append(path)
    return found


def best_eval_path(
    log_dir: Path,
    *,
    repo_root: Path | None = None,
    condition: str | None = None,
) -> Path | None:
    """Return the `.eval` with the most samples (tie: newest mtime)."""
    if repo_root is not None and condition is not None:
        candidates = candidate_eval_paths(repo_root, log_dir, condition)
    else:
        candidates = list(log_dir.glob("*.eval"))
    if not candidates:
        return None

    def sort_key(path: Path) -> tuple[int, float]:
        return (len(list_eval_sample_ids(path)), path.stat().st_mtime)

    return max(candidates, key=sort_key)


async def best_eval_path_async(
    log_dir: Path,
    *,
    repo_root: Path,
    condition: str,
) -> Path | None:
    candidates = candidate_eval_paths(repo_root, log_dir, condition)
    if not candidates:
        return None

    async def sort_key(path: Path) -> tuple[int, float]:
        ids = await list_eval_sample_ids_async(path)
        return (len(ids), path.stat().st_mtime)

    best = candidates[0]
    best_key = await sort_key(best)
    for path in candidates[1:]:
        key = await sort_key(path)
        if key > best_key:
            best, best_key = path, key
    return best


def sample_count(eval_path: Path) -> int:
    return len(list_eval_sample_ids(eval_path))


def consolidate_best_eval(
    repo_root: Path, log_dir: Path, condition: str
) -> Path | None:
    """Copy the best matching eval into log_dir if Inspect wrote it under ./logs."""
    log_dir.mkdir(parents=True, exist_ok=True)
    best = best_eval_path(log_dir, repo_root=repo_root, condition=condition)
    if best is None:
        return None
    if best.parent.resolve() == log_dir.resolve():
        return best
    dest = log_dir / best.name
    if not dest.exists() or sample_count(best) >= sample_count(dest):
        shutil.copy2(best, dest)
        print(f"    consolidated {best.relative_to(repo_root)} -> {dest.relative_to(repo_root)}")
    return dest if dest.exists() else best


async def consolidate_best_eval_async(
    repo_root: Path, log_dir: Path, condition: str
) -> Path | None:
    """Async variant for validate_corpus (never call sync asyncio.run from async code)."""
    log_dir.mkdir(parents=True, exist_ok=True)
    best = await best_eval_path_async(log_dir, repo_root=repo_root, condition=condition)
    if best is None:
        return None
    if best.parent.resolve() == log_dir.resolve():
        return best
    dest = log_dir / best.name
    best_n = len(await list_eval_sample_ids_async(best))
    dest_n = len(await list_eval_sample_ids_async(dest)) if dest.exists() else 0
    if not dest.exists() or best_n >= dest_n:
        shutil.copy2(best, dest)
        print(f"    consolidated {best.relative_to(repo_root)} -> {dest.relative_to(repo_root)}")
    return dest if dest.exists() else best
