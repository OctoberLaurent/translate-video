#!/bin/bash
# Build the Python backend into a standalone executable using PyInstaller.
set -e

echo "🔧 Building SubTranslate Backend..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

cd "$BACKEND_DIR"

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.12 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

# Build with PyInstaller
echo "🏗️  Running PyInstaller..."
pyinstaller backend.spec --clean --noconfirm \
    --distpath dist \
    --workpath build

echo "✅ Backend built successfully!"
echo "   Output: $BACKEND_DIR/dist/backend"
