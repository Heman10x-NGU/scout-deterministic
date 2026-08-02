#!/usr/bin/env bash
# Resume partial conditions; consolidate Inspect ./logs into raw_logs first.
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
unset OPENAI_API_KEY OPENAI_BASE_URL INSPECT_API_KEY

python scripts/consolidate_logs.py
python scripts/rebuild_manifest.py
python scripts/validate_corpus.py || true

python benchmark/generate_real_corpus.py \
  --only impossible leading_prompt tight_budget \
  --skip-existing

python scripts/consolidate_logs.py
python scripts/rebuild_manifest.py
python scripts/validate_corpus.py
