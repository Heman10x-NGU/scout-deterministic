"""Load Scout transcripts from eval logs or serialised JSON."""

from __future__ import annotations

import asyncio
from pathlib import Path

from inspect_scout import Transcript, transcripts_from
from inspect_scout._transcript.types import TranscriptContent

from scout_deterministic.bench._guardrails import TRANSCRIPT_LOAD_TIMEOUT_SEC

_FULL_CONTENT = TranscriptContent(messages="all", events="all")


async def list_eval_sample_ids_async(path: Path) -> list[str]:
    """Return sample/task ids inside one Inspect `.eval` log."""
    ids: list[str] = []
    collection = transcripts_from(str(path))
    async with collection.reader() as reader:
        async for info in reader.index():
            sid = info.task_id or getattr(info, "sample_id", None)
            if sid:
                ids.append(str(sid))
    return ids


def list_eval_sample_ids(path: Path) -> list[str]:
    """Sync helper — do not call from inside an async function (use list_eval_sample_ids_async)."""
    return asyncio.run(list_eval_sample_ids_async(path))


async def load_transcript(path: Path, *, sample_id: str | None = None) -> Transcript:
    """Load one transcript from an Inspect `.eval` log or JSON fixture file."""
    if path.suffix == ".eval":
        return await asyncio.wait_for(
            _load_eval_transcript(path, sample_id=sample_id),
            timeout=TRANSCRIPT_LOAD_TIMEOUT_SEC,
        )

    return Transcript.model_validate_json(path.read_text(encoding="utf-8"))


async def _load_eval_transcript(path: Path, *, sample_id: str | None) -> Transcript:
    collection = transcripts_from(str(path))
    async with collection.reader() as reader:
        async for info in reader.index():
            sid = info.task_id or getattr(info, "sample_id", None)
            if sample_id is not None and str(sid) != sample_id:
                continue
            return await reader.read(info, _FULL_CONTENT)
    raise FileNotFoundError(
        f"No transcript found in eval log: {path}"
        + (f" sample_id={sample_id}" if sample_id else "")
    )
