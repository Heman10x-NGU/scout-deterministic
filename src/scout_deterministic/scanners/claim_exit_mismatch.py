"""D3 — success claim contradicted by captured exit code."""

from __future__ import annotations

from inspect_scout import Result, Scanner, Transcript, scanner

from scout_deterministic._results import clean_result, finding_to_result
from scout_deterministic._transcript import normalise
from scout_deterministic.scanners._detect import detect_claim_exit_mismatch


@scanner(messages="all", events=["tool", "model"])
def claim_exit_mismatch() -> Scanner[Transcript]:
    """Flag success claims that follow a failed shell command without a successful rerun."""

    async def scan(transcript: Transcript) -> Result:
        finding = detect_claim_exit_mismatch(normalise(transcript))
        if finding is None:
            return clean_result(label="claim_exit_mismatch")
        return finding_to_result(finding, label="claim_exit_mismatch")

    return scan
