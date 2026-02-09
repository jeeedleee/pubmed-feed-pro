#!/bin/bash
# Build script for PubMed Papers Feed - macOS App
# Usage: ./build_macos.sh

set -e

echo "=============================================="
echo "PubMed Papers Feed - macOS Builder"
echo "=============================================="
echo ""

# Get target architecture
TARGET_ARCH=${TARGET_ARCH:-$(uname -m)}
echo "Target architecture: $TARGET_ARCH"

# Clean previous builds
echo "Step 1: Cleaning previous builds..."
rm -rf build dist *.spec

# Ensure data directories exist
mkdir -p data/reports

echo ""
echo "Step 2: Building macOS app with PyInstaller..."

# PyInstaller command for macOS
python -m PyInstaller \
    --name="PubMedPapersFeed" \
    --onefile \
    --windowed \
    --add-data="web/templates:web/templates" \
    --add-data="web/static:web/static" \
    --add-data="data:data" \
    --add-data="config.yaml.example:." \
    --target-architecture "$TARGET_ARCH" \
    --osx-bundle-identifier "com.pubmedpapers.feed" \
    --icon="NONE" \
    --clean \
    --noconfirm \
    main.py

echo ""
echo "Step 3: Creating launcher script..."

cat > "dist/start.command" << 'EOF'
#!/bin/bash
# PubMed Papers Feed Launcher for macOS

echo "Starting PubMed Papers Feed..."
echo ""

# Get the directory where this script is located
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$HOME/.pubmed_papers_feed"

# Create data directory in user home
mkdir -p "$DATA_DIR/data/reports"

# Copy config if not exists
if [ ! -f "$DATA_DIR/config.yaml" ]; then
    cp "$APP_DIR/config.yaml.example" "$DATA_DIR/config.yaml"
    echo "Created default config at $DATA_DIR/config.yaml"
    echo "Please edit it with your API key before using."
    echo ""
    read -p "Press Enter to continue..."
fi

# Open browser
open "http://localhost:8000"

# Run the app
cd "$DATA_DIR"
"$APP_DIR/PubMedPapersFeed"
EOF

chmod +x dist/start.command

echo ""
echo "Step 4: Copying additional files..."
cp config.yaml.example dist/
cp README.md dist/

echo ""
echo "=============================================="
echo "Build complete!"
echo "=============================================="
echo ""
echo "Output location: dist/"
echo "- PubMedPapersFeed        (主程序)"
echo "- start.command           (启动脚本)"
echo "- config.yaml.example     (配置模板)"
echo ""
echo "Usage:"
echo "  1. 将 dist/ 文件夹压缩发送给用户"
echo "  2. Mac用户下载后解压，双击 start.command 启动"
echo "  3. 首次运行需在 系统设置 > 隐私与安全性 中允许运行"
echo "  4. 首次运行需配置 API Key"
echo ""
echo "注意事项:"
echo "  - start.command 需要右键 -> 打开，以绕过 Gatekeeper"
echo "  - 或者在终端中运行: chmod +x start.command && ./start.command"
echo ""
