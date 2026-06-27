# CLAUDE.md

**You MUST read [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) before any PPT generation task or repo modification.** SKILL.md is the authoritative workflow. This file is the project charter — it defines identity, routing, and constraints. For operational details (commands, setup, artifact structure, architecture), read [`docs/claude-reference.md`](docs/claude-reference.md).

## Project Identity

PPT Master is an AI-driven presentation generation system. Multi-role collaboration (Strategist → Image_Generator → Executor) converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML).

**Core Pipeline**: `Source → Project → [Template] → [Content Selection] → [Outline] → Eight Confirmations → [Images] → SVG Render → Quality Check → Post-process → Export`

**Detailed routing table**: [`docs/routing.md`](docs/routing.md) — loaded on demand.

## Constraints

- This repository is a workflow/skill package, not an app scaffold.
- Do NOT assume generic-project conventions (`.worktrees/`, `tests/`, mandatory branches) unless explicitly requested.
- On conflict with a generic coding skill, prioritize SKILL.md inside this repository.
- Markdown language consistency: files under `skills/ppt-master/workflows/`, `skills/ppt-master/references/`, and `docs/` are single-language per directory.
- Repo-wide style rules: follow matching rule in [`docs/rules/`](docs/rules/) when editing any code or prose in this repo.
- Code safety: Before modifying any file under `skills/ppt-master/scripts/` or `skills/ppt-master/workflows/`, run `python scripts/smoke_check.py` to establish baseline. After modification, run `python scripts/e2e_validate.py --quick` to confirm no regression. Log all changes in [`docs/change-log.md`](docs/change-log.md). Modifications to SKILL.md itself require `[NEEDS_HUMAN_REVIEW]` annotation.

## Quick Links

| Resource | Purpose |
|----------|---------|
| [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) | Main workflow authority |
| [`docs/claude-reference.md`](docs/claude-reference.md) | Full operational reference (commands, setup, architecture) |
| [`skills/ppt-master/references/`](skills/ppt-master/references/) | Role definitions and technical specifications |
| [`skills/ppt-master/scripts/`](skills/ppt-master/scripts/) | Runnable tool scripts |
| [`skills/ppt-master/templates/`](skills/ppt-master/templates/) | Layout templates, charts, icons, brands |
| [`skills/ppt-master/workflows/`](skills/ppt-master/workflows/) | Standalone workflow files |
| [`docs/`](docs/) | User-facing documentation |
| [`projects/`](projects/) | User project workspace |
| [`docs/routing.md`](docs/routing.md) | Complete workflow routing table |
| [`docs/change-log.md`](docs/change-log.md) | Script/workflow modification audit trail |
