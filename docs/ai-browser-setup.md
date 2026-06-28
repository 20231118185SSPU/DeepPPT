# AI Browser Setup — Let Your AI Agent Control a Real Browser

Connect any AI coding agent (Claude Code, Cursor, Windsurf, Cline, etc.) to a real Chrome instance via the Chrome DevTools Protocol (CDP). The browser keeps your login sessions across restarts.

## Why

Most AI agents can generate code, but they can't *see* a website, click buttons, or test UI. By pointing them at a CDP-enabled Chrome, you give them eyes and hands:

- **Claude Code** — Playwright MCP plugin connects automatically
- **Cursor / Windsurf** — use Puppeteer or Playwright MCP
- **Any CDP client** — Selenium, `chrome-remote-interface`, direct WebSocket

## Quick Start (3 steps)

### 1. Copy the config template

```bash
cp scripts/.hermes-chrome.env.example scripts/.hermes-chrome.env
```

Edit `scripts/.hermes-chrome.env` and fill in your paths:

```ini
# Windows
CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe
HERMES_CHROME_PROFILE=C:\Users\YourName\chrome-hermes-profile

# macOS
CHROME_EXE=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
HERMES_CHROME_PROFILE=/Users/YourName/chrome-hermes-profile

# Linux
CHROME_EXE=/usr/bin/google-chrome
HERMES_CHROME_PROFILE=/home/yourname/chrome-hermes-profile

HERMES_CHROME_PORT=9222
```

> **`HERMES_CHROME_PROFILE` must NOT be your default Chrome profile directory.**
> Chrome's security policy blocks CDP on the default profile. Any other path works.

### 2. Start the browser

```bash
# Windows — double-click or run:
scripts\start-hermes-chrome.bat

# macOS / Linux:
bash scripts/start-hermes-chrome.sh
```

The script checks if CDP is already running (port 9222 by default) and skips if so.

### 3. Connect your AI agent

| Agent / Tool | How to connect |
|---|---|
| **Claude Code + Playwright MCP** | Automatic — just open a new tab in the CDP Chrome and the plugin finds it |
| **Puppeteer** | `puppeteer.connect({ browserURL: 'http://localhost:9222' })` |
| **Selenium** | `options.debugger_address = "127.0.0.1:9222"` |
| **CDP direct** | `CDP({ port: 9222 })` (Node.js `chrome-remote-interface`) |

## How It Works

```
┌─────────────┐     CDP (port 9222)     ┌──────────────────┐
│  AI Agent   │ ◄──────────────────────► │  Chrome Browser  │
│  (Playwright│     WebSocket / HTTP      │  (hermes profile)│
│   Puppeteer │                           │  persistent login│
│   Selenium) │                           │  sessions        │
└─────────────┘                           └──────────────────┘
```

- Chrome runs with `--remote-debugging-port=9222` and a **dedicated profile directory**
- The profile directory is persistent — your cookies, bookmarks, and logins survive restarts
- Any CDP-compatible tool can connect to `http://localhost:9222`
- Only accessible from `localhost` (no remote exposure)

## Troubleshooting

### "DevTools remote debugging requires a non-default data directory"

Chrome rejects `--remote-debugging-port` on the default profile. Set `HERMES_CHROME_PROFILE` to any path that is **not** your usual Chrome data directory (e.g., not `~/.config/google-chrome` or `AppData/Local/Google/Chrome/User Data`).

### Port already in use

Another process is using port 9222. Either stop it or change `HERMES_CHROME_PORT` in the config.

### Chrome won't start / crashes immediately

- Make sure no other Chrome instance is running (the script kills existing Chrome to avoid the single-instance problem)
- Check that `CHROME_EXE` points to a valid Chrome binary
- On Windows, try running the script as administrator if path issues persist

### AI agent can't connect

1. Verify Chrome is listening: `curl http://localhost:9222/json/version`
2. If that returns JSON, the CDP endpoint is healthy — check your agent's connection config
3. If it fails, Chrome may not have started with the flag — restart with the script

## Files

| File | Tracked in Git | Purpose |
|---|---|---|
| `scripts/.hermes-chrome.env.example` | Yes | Config template — copy to `.hermes-chrome.env` |
| `scripts/.hermes-chrome.env` | **No** (gitignored) | Your local config with personal paths |
| `scripts/start-hermes-chrome.bat` | Yes | Windows startup script |
| `scripts/start-hermes-chrome.sh` | Yes | macOS/Linux startup script |

## Integration with Deep Research (browse_ai.py)

The deep-research workflow uses `browse_ai.py` to automate searches on ChatGPT, Grok, and Perplexity. It connects to your CDP Chrome automatically.

### Setup

1. Start Chrome with CDP (steps 1-2 above)
2. Log into ChatGPT / Grok / Perplexity in the CDP Chrome (sessions persist across restarts)
3. That's it — `browse_ai.py` auto-reads `scripts/.hermes-chrome.env` for the CDP port

### Usage

```bash
# Single search via ChatGPT (connects to CDP Chrome at port 9222)
python skills/ppt-master/scripts/research/browse_ai.py \
  --ai chatgpt --prompt "What is the AI market size in 2025?" --output result.md

# Batch search (reads search_plan.json, routes by content type)
python skills/ppt-master/scripts/research/browse_ai.py \
  --batch projects/my_project/_research/step2_search_plan/search_plan.json \
  --output-dir projects/my_project/_research/step3_search/

# Override CDP port (if not using default 9222)
python skills/ppt-master/scripts/research/browse_ai.py \
  --ai grok --prompt "..." --cdp-port 9223
```

### How browse_ai.py connects

```
Priority 1: CDP (localhost:9222)  ← recommended, uses running Chrome with your logins
Priority 2: --chrome-profile     ← launches Chrome with a profile dir
Priority 3: Fresh Chromium       ← no persistence, fallback only
```

When `--cdp-port` is set (or read from `.hermes-chrome.env`), the script connects to the already-running Chrome. This is the fastest and most reliable mode — no browser launch delay, all login sessions available.
