#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# venv bootstrap (first run only)
if [ ! -d .venv ]; then
  python3.12 -m venv .venv
fi
source .venv/bin/activate
# deps (idempotent)
python -m pip install --upgrade pip >/dev/null
pip install -q fastapi uvicorn requests python-dotenv openai chromadb pydantic
# run
uvicorn agents.main:app --reload --port 8001
