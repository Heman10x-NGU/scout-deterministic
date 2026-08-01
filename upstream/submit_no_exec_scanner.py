"""Deterministic submit-without-execution scanner for upstream Inspect Scout.

Copy into: src/inspect_scout/_deterministic_scanner/submit_no_exec.py
"""

from inspect_ai.event import ScoreEvent, ToolEvent
from inspect_scout import Reference, Result, Scanner, Transcript, scanner

SHELL_TOOLS = frozenset(
    {"bash", "shell", "execute", "run", "terminal", "bash_session", "python"}
)
SUBMIT_TOOLS = frozenset({"submit", "submit_answer", "finish", "done", "answer"})


def _is_submit_tool(function: str) -> bool:
    lowered = function.lower()
    return lowered in SUBMIT_TOOLS or lowered.endswith("_submit")


def _submit_index(transcript: Transcript) -> int | None:
    index = 0
    for raw in transcript.events:
        if isinstance(raw, ToolEvent) and _is_submit_tool(raw.function):
            return index
        if isinstance(raw, ScoreEvent) and not raw.intermediate:
            return index
        index += 1
    return None


@scanner(messages="all", events=["tool", "model"])
def submit_no_exec_scanner() -> Scanner[Transcript]:
    """Flag transcripts where the agent submits without shell/tool execution."""

    async def scan(transcript: Transcript) -> Result:
        submit_idx = _submit_index(transcript)
        if submit_idx is None:
            return Result(value=False, label="submit_no_exec")

        tool_steps = 0
        for raw in transcript.events[:submit_idx]:
            if isinstance(raw, ToolEvent):
                if raw.function.lower() in SHELL_TOOLS:
                    tool_steps += 1

        if tool_steps > 0:
            return Result(value=False, label="submit_no_exec")

        return Result(
            value=True,
            label="submit_no_exec",
            explanation=f"Submit at event index {submit_idx} with zero shell execution",
            references=[Reference(type="event", cite=f"[E{submit_idx}]", id=f"step-{submit_idx}")],
        )

    return scan
