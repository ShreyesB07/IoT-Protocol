#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "======================================"
echo "  IoT Protocol Testbed - Setup"
echo "======================================"

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: Python 3 is not installed."
    exit 1
fi

PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "System Python detected: $PYTHON_VERSION"

if [[ ! -d "$ROOT_DIR/.venv" ]]; then
    echo "Creating project virtual environment..."
    python3 -m venv "$ROOT_DIR/.venv"
fi

VENV_PY="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
    echo "ERROR: Virtual environment Python not found."
    exit 1
fi

echo "Using project Python:"
"$VENV_PY" --version

echo "Installing dependencies inside .venv..."
"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r "$ROOT_DIR/requirements.txt"

echo ""
echo "Checking Streamlit..."
"$VENV_PY" -m streamlit --version

if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            echo ""
            echo "Starting Docker Compose services..."
            docker compose -f "$ROOT_DIR/docker-compose.yml" up -d
        else
            echo "Docker is installed but not running."
            echo "Open Docker Desktop if you want to use Docker."
        fi
    fi
else
    echo "Docker not found. You can use your local Mosquitto installation."
fi

echo ""
echo "======================================"
echo "  Setup completed successfully!"
echo "======================================"
echo "Launch using ./Launch_Dashboard.command"
