#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "== 1) Lark preflight =="
python3 scripts/lark_preflight.py

echo
echo "== 2) Chroma preflight =="
python3 scripts/chroma_preflight.py

echo
echo "All preflight checks passed."
