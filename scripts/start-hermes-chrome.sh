#!/usr/bin/env bash
# ============================================================
#  Hermes Chrome - AI Agent Browser (CDP)
#  Reads config from scripts/.hermes-chrome.env
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.hermes-chrome.env"

# Load .env config
if [[ ! -f "$ENV_FILE" ]]; then
    echo "[Hermes] ERROR: Config file not found: $ENV_FILE"
    echo "[Hermes] Copy .hermes-chrome.env.example to .hermes-chrome.env and fill in your paths."
    exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

# Validate required config
: "${CHROME_EXE:?CHROME_EXE not set in .hermes-chrome.env}"
: "${HERMES_CHROME_PROFILE:?HERMES_CHROME_PROFILE not set in .hermes-chrome.env}"
HERMES_CHROME_PORT="${HERMES_CHROME_PORT:-9222}"

# Check if already running
if curl -sf "http://localhost:${HERMES_CHROME_PORT}/json/version" >/dev/null 2>&1; then
    echo "[Hermes] Chrome CDP already running on port ${HERMES_CHROME_PORT}"
    exit 0
fi

# Kill existing Chrome
if command -v taskkill &>/dev/null; then
    taskkill //F //IM chrome.exe >/dev/null 2>&1 || true
else
    pkill -f chrome || true
fi
sleep 2

# Create profile dir if needed
mkdir -p "$HERMES_CHROME_PROFILE"

# Start Chrome
"$CHROME_EXE" \
    --remote-debugging-port="${HERMES_CHROME_PORT}" \
    --user-data-dir="${HERMES_CHROME_PROFILE}" \
    --no-first-run \
    --disable-default-apps &
CHROME_PID=$!

sleep 4

# Verify
if curl -sf "http://localhost:${HERMES_CHROME_PORT}/json/version" >/dev/null 2>&1; then
    echo "[Hermes] Chrome CDP started on port ${HERMES_CHROME_PORT}"
    echo "[Hermes] Endpoint: http://localhost:${HERMES_CHROME_PORT}"
else
    echo "[Hermes] ERROR: Failed to start Chrome CDP on port ${HERMES_CHROME_PORT}"
    kill $CHROME_PID 2>/dev/null || true
    exit 1
fi
