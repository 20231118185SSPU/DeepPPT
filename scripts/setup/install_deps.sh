#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== DeepPPT Dependency Installer ==="
echo ""

# ── Python check ──────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.10+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo "ERROR: Python 3.10+ required, found $PYTHON_VERSION."
    exit 1
fi

echo "Python: $PYTHON_VERSION  ($(command -v python3))"

# ── pip check ─────────────────────────────────────────────────
if ! python3 -m pip --version &>/dev/null; then
    echo "ERROR: pip not found. Install it with:"
    echo "  python3 -m ensurepip --upgrade"
    exit 1
fi

# ── Required packages ─────────────────────────────────────────
echo ""
echo "Installing required packages..."
python3 -m pip install --upgrade pip
python3 -m pip install \
    python-pptx \
    Pillow \
    requests \
    beautifulsoup4 \
    lxml

# ── Optional packages ─────────────────────────────────────────
echo ""
read -p "Install optional packages (cairosvg, feedparser)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 -m pip install cairosvg feedparser
fi

# ── Playwright (browser screenshots) ──────────────────────────
echo ""
read -p "Install Playwright for browser screenshots? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 -m pip install playwright
    python3 -m playwright install chromium
fi

# ── .env reminder ─────────────────────────────────────────────
if [ ! -f "$REPO_ROOT/.env" ]; then
    echo ""
    echo "WARNING: No .env file found."
    echo "Copy .env.example to .env and configure your API keys:"
    echo "  cp .env.example .env"
    echo ""
    echo "Required: Set IMAGE_BACKEND and the corresponding API key."
    echo "See .env.example for all available backends."
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "Setup complete! Run the following to verify:"
echo "  python3 scripts/setup/check_deps.py"
