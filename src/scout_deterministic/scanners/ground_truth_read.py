"""D2 — ground-truth read before submit."""

from __future__ import annotations

from inspect_scout import Result, Scanner, Transcript, scanner

from scout_deterministic._results import clean_result, finding_to_result
from scout_deterministic._transcript import (
    DEFAULT_SCORER_PATTERNS,
    normalise,
    transcript_target,
)
from scout_deterministic.scanners._detect import detect_ground_truth_read


@scanner(messages="all", events=["tool", "model"])
def ground_truth_read(
    patterns: list[str] | None = None,
) -> Scanner[Transcript]:
    """Flag ground-truth access before the submit event."""

    resolved = tuple(patterns) if patterns else DEFAULT_SCORER_PATTERNS

    async def scan(transcript: Transcript) -> Result:
        finding = detect_ground_truth_read(
            normalise(transcript),
            patterns=resolved,
            targets=transcript_target(transcript),
        )
        if finding is None:
            return clean_result(label="ground_truth_read")
        return finding_to_result(finding, label="ground_truth_read")

    return scan
