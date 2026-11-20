#!/usr/bin/env bash

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

VENV_PY="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
    echo "Virtual environment not found."
    echo "Please run ./setup_mac.sh first."
    read -r -p "Press Enter to close..."
    exit 1
fi

echo "Starting IoT Protocol Testbed..."
echo "Project: $ROOT_DIR"
echo "Python: $VENV_PY"
echo ""

exec "$VENV_PY" -m streamlit run "$ROOT_DIR/dashboard/app.py"
