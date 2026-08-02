#!/usr/bin/env bash
# Run the 3 corpus conditions not yet generated (clean + readable_answer already done).
# Caps: see src/scout_deterministic/bench/_guardrails.py (~90 min worst case).
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
unset OPENAI_API_KEY OPENAI_BASE_URL INSPECT_API_KEY

python benchmark/generate_real_corpus.py \
  --only impossible leading_prompt tight_budget \
  --skip-existing

python scripts/validate_corpus.py
