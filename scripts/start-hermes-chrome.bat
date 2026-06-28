@echo off
setlocal
REM ============================================================
REM  Hermes Chrome - AI Agent Browser (CDP)
REM  Reads config from scripts/.hermes-chrome.env
REM ============================================================

set "SCRIPT_DIR=%~dp0"
set "ENV_FILE=%SCRIPT_DIR%.hermes-chrome.env"

REM Load .env config
if exist "%ENV_FILE%" (
    for /F "usebackq tokens=1,* delims==" %%A in ("%ENV_FILE%") do (
        REM Skip comments and empty lines
        echo %%A | findstr /R "^#" >nul 2>&1 || set "%%A=%%B"
    )
) else (
    echo [Hermes] ERROR: Config file not found: %ENV_FILE%
    echo [Hermes] Copy .hermes-chrome.env.example to .hermes-chrome.env and fill in your paths.
    exit /b 1
)

REM Validate required config
if "%CHROME_EXE%"=="" (
    echo [Hermes] ERROR: CHROME_EXE not set in .hermes-chrome.env
    exit /b 1
)
if "%HERMES_CHROME_PROFILE%"=="" (
    echo [Hermes] ERROR: HERMES_CHROME_PROFILE not set in .hermes-chrome.env
    exit /b 1
)
if "%HERMES_CHROME_PORT%"=="" set "HERMES_CHROME_PORT=9222"

REM Check if already running
netstat -ano | findstr ":%HERMES_CHROME_PORT%" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [Hermes] Chrome CDP already running on port %HERMES_CHROME_PORT%
    exit /b 0
)

REM Kill existing Chrome (single-instance conflict)
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Create profile dir if needed
if not exist "%HERMES_CHROME_PROFILE%" mkdir "%HERMES_CHROME_PROFILE%"

REM Start Chrome with CDP
start "" "%CHROME_EXE%" ^
    --remote-debugging-port=%HERMES_CHROME_PORT% ^
    --user-data-dir="%HERMES_CHROME_PROFILE%" ^
    --no-first-run ^
    --disable-default-apps

timeout /t 4 /nobreak >nul

REM Verify
netstat -ano | findstr ":%HERMES_CHROME_PORT%" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [Hermes] Chrome CDP started on port %HERMES_CHROME_PORT%
    echo [Hermes] Endpoint: http://localhost:%HERMES_CHROME_PORT%
) else (
    echo [Hermes] ERROR: Failed to start Chrome CDP on port %HERMES_CHROME_PORT%
    exit /b 1
)
