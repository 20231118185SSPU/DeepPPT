# OfficeCLI Integration (Phase 1)

> Status: Phase 1 — Pinned Runtime and Bridge
> Authority: non-authoritative; `AGENTS.md`, `SKILL.md`, and owning workflows remain authoritative

## Purpose

OfficeCLI is DeepPPT2's fixed local Office capability layer. Phase 1 establishes the unique, verifiable, cross-platform runtime and zero-shell calling bridge.

## Components

| Component | Path | Role |
|---|---|---|
| Lock manifest | `assets/officecli-lock.json` | Pinned version, platform assets, SHA-256 |
| Installer | `install_officecli.py` | Download, verify, atomic install |
| Bridge | `officecli_bridge.py` | Typed API, JSON envelope, error codes |

## Commands

```powershell
# Runtime management
python skills/ppt-master/scripts/install_officecli.py install [--json]
python skills/ppt-master/scripts/install_officecli.py check [--json]
python skills/ppt-master/scripts/install_officecli.py path [--json]

# Bridge API (Python)
from officecli_bridge import resolve_officecli, probe_officecli, run_officecli
from officecli_bridge import run_atomic_batch, validate_office_file, inspect_office_file
```

## Version Policy

- Pinned to `v1.0.143` (2026-07-28 release, Apache-2.0).
- Installed to gitignored `.tools/officecli/v1.0.143/<platform>/`.
- PATH fallback, MCP/SDK, plugins, and auto-upgrade are prohibited.
- Upgrades must be independent changes: update lock, SHA for all platforms, and change-log.

## Stable Error Codes

`OFFICECLI_NOT_INSTALLED`, `OFFICECLI_VERSION_MISMATCH`, `OFFICECLI_CHECKSUM_MISMATCH`,
`OFFICECLI_UNSUPPORTED_PLATFORM`, `OFFICECLI_TIMEOUT`, `OFFICECLI_INVALID_JSON`,
`OFFICECLI_COMMAND_FAILED`, `OFFICECLI_PLAN_INVALID`, `OFFICECLI_PLAN_STALE`,
`OFFICECLI_TARGET_MISSING`, `OFFICECLI_BATCH_ROLLED_BACK`, `OFFICECLI_VALIDATION_FAILED`,
`OFFICECLI_PREVIEW_UNAVAILABLE`, `OFFICECLI_VISUAL_REVIEW_REQUIRED`
