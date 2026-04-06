#!/bin/bash
# Build the complete SubTranslate application.
# Produces .dmg for macOS or .exe installer for Windows.
set -e

echo "🚀 Building SubTranslate Application..."
echo "========================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Step 1: Build Backend
echo ""
echo "📋 Step 1/3: Building Python Backend..."
bash "$SCRIPT_DIR/build-backend.sh"

# Step 2: Build Frontend
echo ""
echo "📋 Step 2/3: Building Vue.js Frontend..."
cd "$PROJECT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

echo "🏗️  Building frontend..."
npm run build

# Copy dist to electron folder
echo "📂 Copying frontend dist to electron..."
mkdir -p "$PROJECT_DIR/electron/dist"
cp -r "$PROJECT_DIR/frontend/dist/"* "$PROJECT_DIR/electron/dist/"

# Step 3: Build Electron App
echo ""
echo "📋 Step 3/3: Building Electron Application..."
cd "$PROJECT_DIR/electron"

if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

echo "🏗️  Packaging Electron app..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    npm run build:mac

    # Create .dmg manually (avoids dmg-builder module issues)
    echo "📦 Creating .dmg..."
    DMG_STAGING="/tmp/subtranslate-dmg-staging"
    rm -rf "$DMG_STAGING"
    mkdir -p "$DMG_STAGING"
    cp -R "$PROJECT_DIR/dist-electron/mac-arm64/SubTranslate.app" "$DMG_STAGING/"
    ln -sf /Applications "$DMG_STAGING/Applications"
    hdiutil create -volname "SubTranslate" \
      -srcfolder "$DMG_STAGING" \
      -ov -format UDZO \
      "$PROJECT_DIR/dist-electron/SubTranslate.dmg"
    rm -rf "$DMG_STAGING"

    # Remove quarantine attribute
    xattr -cr "$PROJECT_DIR/dist-electron/mac-arm64/SubTranslate.app"

    echo ""
    echo "✅ macOS build complete!"
    echo "   .app: $PROJECT_DIR/dist-electron/mac-arm64/SubTranslate.app"
    echo "   .dmg: $PROJECT_DIR/dist-electron/SubTranslate.dmg"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    npm run build:win
    echo ""
    echo "✅ Windows build complete!"
    echo "   Output: $PROJECT_DIR/dist-electron/SubTranslate Setup.exe"
else
    npm run build
    echo ""
    echo "✅ Build complete!"
    echo "   Output: $PROJECT_DIR/dist-electron/"
fi

echo ""
echo "========================================"
echo "🎉 SubTranslate build finished!"