#!/usr/bin/env bash
# Recreate a broken venv and install the package. Run from repo root.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3.11}"
echo "Using $PYTHON"
rm -rf .venv
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/pytest -q
echo "OK — activate with: source .venv/bin/activate"
