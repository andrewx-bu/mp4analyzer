#!/usr/bin/env bash
set -e

echo "🐍 Ensuring virtual environment..."
uv venv

echo "📦 Installing dependencies from pyproject.toml..."
uv sync --extra dev

echo "⚙️ Activating virtual environment..."
if [ -f ".venv/bin/activate" ]; then . .venv/bin/activate; else . .venv/Scripts/activate; fi

echo "✅ Environment setup complete."
