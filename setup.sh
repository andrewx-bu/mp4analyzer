#!/bin/bash

module load python3
module load ffmpeg

if [ ! -d ".venv" ]; then
  echo "🐍 Creating virtual environment..."
  python3 -m venv .venv
fi

echo "⚙️ Activating virtual environment..."
source .venv/bin/activate

echo "📦 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "✅ Environment setup complete."