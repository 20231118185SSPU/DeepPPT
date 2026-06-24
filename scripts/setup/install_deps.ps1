#Requires -Version 5.1
<#
.SYNOPSIS
    DeepPPT Dependency Installer for Windows.
.DESCRIPTION
    Installs required and optional Python packages for the DeepPPT project.
    Run with:  powershell -ExecutionPolicy Bypass -File scripts/setup/install_deps.ps1
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = (Resolve-Path "$ScriptDir\..\..").Path

Write-Host "=== DeepPPT Dependency Installer ===" -ForegroundColor Cyan
Write-Host ""

# ── Python check ──────────────────────────────────────────────
$pythonCmd = $null
foreach ($candidate in @("python3", "python")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $pythonCmd = $candidate
        break
    }
}

if (-not $pythonCmd) {
    Write-Host "ERROR: Python 3 not found. Please install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

$versionRaw = & $pythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
$parts      = $versionRaw.Split(".")
$pyMajor    = [int]$parts[0]
$pyMinor    = [int]$parts[1]

if ($pyMajor -lt 3 -or ($pyMajor -eq 3 -and $pyMinor -lt 10)) {
    Write-Host "ERROR: Python 3.10+ required, found $versionRaw." -ForegroundColor Red
    exit 1
}

$pythonPath = (Get-Command $pythonCmd).Source
Write-Host "Python: $versionRaw  ($pythonPath)"

# ── pip resolution ────────────────────────────────────────────
# Try "pip" first; fall back to "python -m pip" if not on PATH.
function Invoke-Pip {
    param([string[]]$PipArgs)
    if (Get-Command pip -ErrorAction SilentlyContinue) {
        & pip @PipArgs
    } else {
        & $pythonCmd -m pip @PipArgs
    }
}

# Verify pip is usable
try {
    Invoke-Pip @("--version") | Out-Null
} catch {
    Write-Host "ERROR: pip not found. Install it with:" -ForegroundColor Red
    Write-Host "  $pythonCmd -m ensurepip --upgrade"
    exit 1
}

# ── Required packages ─────────────────────────────────────────
Write-Host ""
Write-Host "Installing required packages..."
Invoke-Pip @("install", "--upgrade", "pip")
Invoke-Pip @("install",
    "python-pptx",
    "Pillow",
    "requests",
    "beautifulsoup4",
    "lxml"
)

# ── Optional packages ─────────────────────────────────────────
Write-Host ""
$reply = Read-Host "Install optional packages (cairosvg, feedparser)? [y/N]"
if ($reply -match '^[Yy]') {
    Invoke-Pip @("install", "cairosvg", "feedparser")
}

# ── Playwright (browser screenshots) ──────────────────────────
Write-Host ""
$reply = Read-Host "Install Playwright for browser screenshots? [y/N]"
if ($reply -match '^[Yy]') {
    Invoke-Pip @("install", "playwright")
    & $pythonCmd -m playwright install chromium
}

# ── .env reminder ─────────────────────────────────────────────
$envFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host ""
    Write-Host "WARNING: No .env file found." -ForegroundColor Yellow
    Write-Host "Copy .env.example to .env and configure your API keys:"
    Write-Host "  cp .env.example .env"
    Write-Host ""
    Write-Host "Required: Set IMAGE_BACKEND and the corresponding API key."
    Write-Host "See .env.example for all available backends."
}

# ── Done ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "Setup complete! Run the following to verify:" -ForegroundColor Green
Write-Host "  python scripts/setup/check_deps.py"
