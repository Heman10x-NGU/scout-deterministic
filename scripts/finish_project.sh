#!/usr/bin/env bash
# Finalize benchmark after labels exist: compare, report, test.
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
unset OPENAI_API_KEY OPENAI_BASE_URL INSPECT_API_KEY

python scripts/run_compare_and_report.py --llm
pytest -q
echo "Done. See benchmark/RESULTS.md and PORTFOLIO.md"
