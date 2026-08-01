"""D4 — submit with no supporting tool execution."""

from __future__ import annotations

from inspect_scout import Result, Scanner, Transcript, scanner

from scout_deterministic._results import clean_result, finding_to_result
from scout_deterministic._transcript import SHELL_TOOLS, normalise
from scout_deterministic.scanners._detect import detect_submit_no_exec


@scanner(messages="all", events=["tool", "model"])
def submit_no_exec() -> Scanner[Transcript]:
    """Flag transcripts that submit an answer without any tool execution."""

    async def scan(transcript: Transcript) -> Result:
        finding = detect_submit_no_exec(normalise(transcript), shell_tools=SHELL_TOOLS)
        if finding is None:
            return clean_result(label="submit_no_exec")
        return finding_to_result(finding, label="submit_no_exec")

    return scan
