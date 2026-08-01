"""Entry point for `scout scan` — all @scanner functions must live in this file."""

from inspect_scout import Result, Scanner, Transcript, scanner

from scout_deterministic._results import clean_result, finding_to_result
from scout_deterministic._transcript import (
    DEFAULT_SCORER_PATTERNS,
    SHELL_TOOLS,
    normalise,
    transcript_target,
)
from scout_deterministic.scanners._detect import (
    detect_claim_exit_mismatch,
    detect_ground_truth_read,
    detect_scorer_access,
    detect_submit_no_exec,
)


@scanner(messages="all", events=["tool", "model"])
def submit_no_exec() -> Scanner[Transcript]:
    async def scan(transcript: Transcript) -> Result:
        finding = detect_submit_no_exec(normalise(transcript), shell_tools=SHELL_TOOLS)
        if finding is None:
            return clean_result(label="submit_no_exec")
        return finding_to_result(finding, label="submit_no_exec")

    return scan


@scanner(messages="all", events=["tool"])
def scorer_access(patterns: list[str] | None = None) -> Scanner[Transcript]:
    resolved = tuple(patterns) if patterns else DEFAULT_SCORER_PATTERNS

    async def scan(transcript: Transcript) -> Result:
        finding = detect_scorer_access(normalise(transcript), patterns=resolved)
        if finding is None:
            return clean_result(label="scorer_access")
        return finding_to_result(finding, label="scorer_access")

    return scan


@scanner(messages="all", events=["tool", "model"])
def ground_truth_read(patterns: list[str] | None = None) -> Scanner[Transcript]:
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


@scanner(messages="all", events=["tool", "model"])
def claim_exit_mismatch() -> Scanner[Transcript]:
    async def scan(transcript: Transcript) -> Result:
        finding = detect_claim_exit_mismatch(normalise(transcript))
        if finding is None:
            return clean_result(label="claim_exit_mismatch")
        return finding_to_result(finding, label="claim_exit_mismatch")

    return scan
