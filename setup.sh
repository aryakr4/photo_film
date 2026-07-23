#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

uv venv --python 3.13 .venv
uv pip install --python .venv -e ".[dev]"

echo ""
echo "Setup complete."
echo "Drop RAW/JPEG/TIFF files into raw_inbox/, then run:"
echo "  .venv/bin/python process.py"
