#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "== 1/4 generate live corpus =="
python benchmark/generate_real_corpus.py

echo ""
echo "== 2/4 hand-label (interactive) =="
scout-det-label

echo ""
echo "== 3/4 compare deterministic vs LLM =="
scout-det-compare --llm

echo ""
echo "== 4/4 write RESULTS.md =="
scout-det-report

echo "Done. Review benchmark/RESULTS.md before publishing numbers."
