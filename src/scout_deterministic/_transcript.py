"""Normalise Inspect Scout transcripts into a flat, indexed event list."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

from inspect_ai.event import ModelEvent, ScoreEvent, ToolEvent
from inspect_ai.model import ChatMessageAssistant
from inspect_scout._transcript.types import Transcript

EventKind = Literal["model", "tool", "submit", "message"]

SHELL_TOOLS = frozenset(
    {
        "bash",
        "shell",
        "execute",
        "run",
        "terminal",
        "bash_session",
        "python",
    }
)

SUBMIT_TOOLS = frozenset({"submit", "submit_answer", "finish", "done", "answer"})

SUCCESS_CLAIM_RE = re.compile(
    r"\b(all tests pass|tests are passing|tests pass|works now|fixed|successfully fixed)\b",
    re.IGNORECASE,
)

FAILURE_OUTPUT_RE = re.compile(
    r"\b(FAILED|ERROR|Exit code: [1-9]\d*|returncode[=: ]*[1-9]\d*|[1-9]\d* failed)\b",
    re.IGNORECASE,
)

DEFAULT_SCORER_PATTERNS = (
    r"score",
    r"grade",
    r"answer",
    r"target",
    r"solution",
    r"expected",
    r"\.golden$",
    r"conftest\.py$",
)


@dataclass(frozen=True)
class NormalisedEvent:
    """Flattened transcript step for deterministic detectors."""

    index: int
    kind: EventKind
    event_id: str
    tool_name: str | None
    command: str | None
    paths: tuple[str, ...]
    output: str | None
    exit_code: int | None
    text: str | None
    failed: bool = False


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _extract_paths(arguments: dict[str, object]) -> list[str]:
    paths: list[str] = []
    for key in ("file", "path", "filename", "filepath", "target"):
        if key in arguments:
            paths.append(_as_text(arguments[key]))
    for key in ("cmd", "command", "code"):
        if key in arguments:
            cmd = _as_text(arguments[key])
            paths.extend(re.findall(r"(?:/[\w./-]+|\./[\w./-]+|\w+\.[\w]+)", cmd))
    return [p for p in paths if p]


def _extract_command(arguments: dict[str, object]) -> str | None:
    for key in ("cmd", "command", "code", "input"):
        if key in arguments:
            return _as_text(arguments[key])
    return None


def _parse_exit_code(result: str, failed: bool, error: str | None) -> int | None:
    if failed:
        return 1
    if error:
        return 1
    match = re.search(r"(?:exit code|returncode)[:= ]*(\d+)", result, re.IGNORECASE)
    if match:
        code = int(match.group(1))
        return code if code != 0 else 0
    if FAILURE_OUTPUT_RE.search(result):
        return 1
    if "exit code: 0" in result.lower() or "returncode=0" in result.lower():
        return 0
    return None


def _is_submit_tool(function: str) -> bool:
    lowered = function.lower()
    return lowered in SUBMIT_TOOLS or lowered.endswith("_submit")


def _tool_kind(function: str) -> EventKind:
    return "submit" if _is_submit_tool(function) else "tool"


def _event_from_tool(event: ToolEvent, index: int) -> NormalisedEvent:
    arguments = event.arguments or {}
    result_text = _as_text(event.result)
    error_text = _as_text(event.error.message) if event.error else None
    output = result_text
    if error_text:
        output = f"{result_text}\n{error_text}".strip()
    return NormalisedEvent(
        index=index,
        kind=_tool_kind(event.function),
        event_id=event.uuid or f"tool-{index}",
        tool_name=event.function,
        command=_extract_command(arguments),
        paths=tuple(_extract_paths(arguments)),
        output=output or None,
        exit_code=_parse_exit_code(output, bool(event.failed), error_text),
        text=None,
        failed=bool(event.failed),
    )


def _event_from_model(event: ModelEvent, index: int) -> NormalisedEvent:
    completion = event.output.completion or ""
    return NormalisedEvent(
        index=index,
        kind="model",
        event_id=event.uuid or f"model-{index}",
        tool_name=None,
        command=None,
        paths=(),
        output=None,
        exit_code=None,
        text=completion,
    )


def _event_from_score(event: ScoreEvent, index: int) -> NormalisedEvent:
    return NormalisedEvent(
        index=index,
        kind="submit",
        event_id=event.uuid or f"score-{index}",
        tool_name="score",
        command=None,
        paths=(),
        output=_as_text(event.score.value),
        exit_code=None,
        text=None,
    )


def _assistant_messages(transcript: Transcript, start_index: int) -> list[NormalisedEvent]:
    events: list[NormalisedEvent] = []
    idx = start_index
    for message in transcript.messages:
        if isinstance(message, ChatMessageAssistant):
            text = message.text or ""
            if text.strip():
                events.append(
                    NormalisedEvent(
                        index=idx,
                        kind="message",
                        event_id=getattr(message, "id", None) or f"msg-{idx}",
                        tool_name=None,
                        command=None,
                        paths=(),
                        output=None,
                        exit_code=None,
                        text=text,
                    )
                )
                idx += 1
    return events


def normalise(transcript: Transcript) -> list[NormalisedEvent]:
    """Flatten transcript events and assistant messages into indexed steps."""
    events: list[NormalisedEvent] = []
    index = 1
    for raw in transcript.events:
        if isinstance(raw, ToolEvent):
            events.append(_event_from_tool(raw, index))
            index += 1
        elif isinstance(raw, ModelEvent):
            events.append(_event_from_model(raw, index))
            index += 1
        elif isinstance(raw, ScoreEvent) and not raw.intermediate:
            events.append(_event_from_score(raw, index))
            index += 1
    events.extend(_assistant_messages(transcript, index))
    return events


def path_matches_scorer(path: str, patterns: tuple[str, ...] = DEFAULT_SCORER_PATTERNS) -> bool:
    lowered = path.lower().replace("\\", "/")
    for pattern in patterns:
        if re.search(pattern, lowered):
            return True
    return False


def transcript_target(transcript: Transcript) -> list[str]:
    target = transcript.metadata.get("target")
    if not target:
        return []
    if isinstance(target, str):
        return [part.strip() for part in target.split(",") if part.strip()]
    if isinstance(target, list):
        return [str(item) for item in target]
    return [str(target)]


def serialise_events(events: list[NormalisedEvent]) -> str:
    return json.dumps([event.__dict__ for event in events], indent=2)
