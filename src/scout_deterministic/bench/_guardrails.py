"""Shared timeouts and eval caps so benchmark runs cannot run away for hours."""

from __future__ import annotations

# Inspect eval() kwargs applied to every condition (merged with per-condition caps).
EVAL_BASE_KWARGS: dict[str, object] = {
    "fail_on_error": False,
    "score_on_error": True,
    "retry_on_error": 0,
    "max_subprocesses": 0,  # avoid worker processes inheriting stale API keys
    "max_samples": 1,  # one sample at a time — easier to interrupt, predictable wall time
    "display": "plain",  # no interactive "continue?" UI after Ctrl+C
    "token_limit": 60_000,  # per-sample token ceiling
}

# Per-condition: (sample_count, extra caps). working_limit is per-sample wall clock (seconds).
CONDITION_SPECS: list[tuple[str, int, dict[str, object]]] = [
    ("clean", 8, {"message_limit": 20, "time_limit": 600, "working_limit": 600}),
    (
        "readable_answer",
        6,
        {"message_limit": 15, "time_limit": 600, "working_limit": 600},
    ),
    ("impossible", 4, {"message_limit": 15, "time_limit": 600, "working_limit": 600}),
    (
        "leading_prompt",
        4,
        {"message_limit": 15, "time_limit": 600, "working_limit": 600},
    ),
    (
        "tight_budget",
        4,
        {"message_limit": 6, "time_limit": 300, "working_limit": 300},
    ),
]

BASH_TOOL_TIMEOUT_SEC = 120
PYTEST_SCORER_TIMEOUT_SEC = 90
TRANSCRIPT_LOAD_TIMEOUT_SEC = 60
LLM_SCANNER_TIMEOUT_SEC = 120

# Worst-case wall clock per condition (for ETA prints): samples * working_limit + buffer.
CONDITION_WALL_ESTIMATE_SEC: dict[str, int] = {
    name: count * int(extra["working_limit"]) + 120
    for name, count, extra in CONDITION_SPECS
}


def condition_names() -> list[str]:
    return [name for name, _, _ in CONDITION_SPECS]


def spec_for(condition: str) -> tuple[int, dict[str, object]]:
    for name, count, extra in CONDITION_SPECS:
        if name == condition:
            return count, extra
    raise KeyError(condition)
