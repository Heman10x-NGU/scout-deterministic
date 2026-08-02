#!/usr/bin/env python3
"""Run compare (deterministic + optional LLM) and write RESULTS.md."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scout_deterministic.bench.compare import compare
from scout_deterministic.bench.report import render


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()
    run_llm = args.llm and not args.no_llm
    results = await compare(run_llm=run_llm)
    out = ROOT / "benchmark" / "compare_results.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    md = ROOT / "benchmark" / "RESULTS.md"
    md.write_text(render(results), encoding="utf-8")
    print(f"Wrote {out} and {md}")
    print(f"corpus={results['corpus_size']} positives={results['positives']} recall={results['deterministic']['aggregate']['recall']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
