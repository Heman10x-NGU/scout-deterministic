"""D1 — scorer file access."""

from __future__ import annotations

from inspect_scout import Result, Scanner, Transcript, scanner

from scout_deterministic._results import clean_result, finding_to_result
from scout_deterministic._transcript import DEFAULT_SCORER_PATTERNS, normalise
from scout_deterministic.scanners._detect import detect_scorer_access


@scanner(messages="all", events=["tool"])
def scorer_access(
    patterns: list[str] | None = None,
) -> Scanner[Transcript]:
    """Flag reads or writes to scorer-dependent paths."""

    resolved = tuple(patterns) if patterns else DEFAULT_SCORER_PATTERNS

    async def scan(transcript: Transcript) -> Result:
        finding = detect_scorer_access(normalise(transcript), patterns=resolved)
        if finding is None:
            return clean_result(label="scorer_access")
        return finding_to_result(finding, label="scorer_access")

    return scan
