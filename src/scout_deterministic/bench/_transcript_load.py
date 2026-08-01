"""Load Scout transcripts from eval logs or serialised JSON."""

from __future__ import annotations

from pathlib import Path

from inspect_scout import Transcript, transcripts_from
from inspect_scout._transcript.types import TranscriptContent

_FULL_CONTENT = TranscriptContent(messages="all", events="all")


async def load_transcript(path: Path, *, sample_id: str | None = None) -> Transcript:
    """Load one transcript from an Inspect `.eval` log or JSON fixture file."""
    if path.suffix == ".eval":
        collection = transcripts_from(str(path))
        async with collection.reader() as reader:
            async for info in reader.index():
                if sample_id is not None and info.task_id != sample_id:
                    continue
                return await reader.read(info, _FULL_CONTENT)
        raise FileNotFoundError(
            f"No transcript found in eval log: {path}" + (f" sample_id={sample_id}" if sample_id else "")
        )

    return Transcript.model_validate_json(path.read_text(encoding="utf-8"))
