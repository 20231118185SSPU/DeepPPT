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

## Native PPTX Revision (Phase 2)

```powershell
python skills/ppt-master/scripts/native_revision_pptx.py init <pptx-or-project> [--name <slug>]
python skills/ppt-master/scripts/native_revision_pptx.py inspect <project>
python skills/ppt-master/scripts/native_revision_pptx.py watch <project> [--port 26315]
python skills/ppt-master/scripts/native_revision_pptx.py selected <project> --json
python skills/ppt-master/scripts/native_revision_pptx.py unwatch <project>
python skills/ppt-master/scripts/native_revision_pptx.py check-plan <project>
python skills/ppt-master/scripts/native_revision_pptx.py apply <project>
python skills/ppt-master/scripts/native_revision_pptx.py validate <project> --pptx <candidate>
```

Read-only inspection → browser preview/selection → confirmed atomic plan → temp-copy
apply with postflight gates (OfficeCLI validate baseline-delta, slide roster,
unaddressed-parts preservation, PowerPoint COM render, SVG-divergence record).
Full rollback on any batch item failure; no export is published on failure.
V1 mutation allowlist: `set` / `add` / `remove` / `move` / `swap`.
Workflow: `workflows/stages/native-revision.md`.

## Office Source Inspection & Repair (Phase 3)

```powershell
# Read-only structure manifest for .docx/.xlsx/.pptx sources (auto-run on import-sources)
python skills/ppt-master/scripts/office_source_inspect.py <project> [--json]

# Opt-in copy-only DOCX/XLSX repair
python skills/ppt-master/scripts/office_source_repair.py scaffold <project> --source <relative-path>
python skills/ppt-master/scripts/office_source_repair.py check-plan <project>
python skills/ppt-master/scripts/office_source_repair.py apply <project>
```

`office_source_inspect.py` writes `analysis/office_sources.json`
(schema `ppt_master.office_sources.v1`) with format-specific counts, limited
outline, issues and converter mapping; sources are never modified. Legacy
formats (`.doc` / `.xls` / …) are listed under `unsupported_enrichment` without
inspection. Repair executes on a temp copy, publishes a timestamped copy to
`sources/repaired/`, re-runs the original converter to a new Markdown, and
records original/repaired/Markdown hashes, operation digest and issues delta;
the user's original file is never opened for mutation.
