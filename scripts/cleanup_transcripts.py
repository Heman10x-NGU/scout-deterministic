#!/usr/bin/env python3
"""Delete synthetic benchmark/transcripts/*.json (T1 cleanup)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
transcripts = ROOT / "benchmark" / "transcripts"
if transcripts.exists():
    for path in transcripts.glob("*.json"):
        path.unlink()
    if not any(transcripts.iterdir()):
        transcripts.rmdir()
print("Removed benchmark/transcripts/")
