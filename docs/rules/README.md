# Project Rules

Conventions and style guides for contributors and AI agents working in this repository. These rules are derived from the de facto patterns in existing code and reference documents.

| Rule | Scope |
|---|---|
| [`prompt-style.md`](./prompt-style.md) | Style guide for files under `skills/ppt-master/references/` — voice, sectioning, table-first, forbidden patterns |
| [`code-style.md`](./code-style.md) | Style guide for Python under `skills/ppt-master/scripts/` — file headers, imports, CLI entry points, error handling, no-tests rule |
| [`agent-governance.md`](./agent-governance.md) | Draft governance rule for AI entry files, routing summaries, authority layers, and non-authoritative design drafts |
| [`documentation-style.md`](./documentation-style.md) | Draft style and status rule for `docs/`, `docs/zh/`, `docs/design/`, audits, and user-facing documents |
| [`workflow-style.md`](./workflow-style.md) | Draft structure and trigger-language rule for `skills/ppt-master/workflows/` runbooks |
| [`change-management.md`](./change-management.md) | Draft risk classification, user-confirmation, and reporting rule for documentation and workflow changes |

## Rule Selection

| Change target | Read |
|---|---|
| Python under `skills/ppt-master/scripts/` | [`code-style.md`](./code-style.md) |
| Prompt/reference files under `skills/ppt-master/references/` | [`prompt-style.md`](./prompt-style.md) |
| Standalone workflow files under `skills/ppt-master/workflows/` | [`workflow-style.md`](./workflow-style.md) |
| User docs, design docs, audits, or architecture docs under `docs/` | [`documentation-style.md`](./documentation-style.md) |
| `AGENTS.md`, `docs/routing.md`, `docs/ai-rules-shared.md`, or AI entry summaries | [`agent-governance.md`](./agent-governance.md) |
| Changes that affect routing, gates, authority, or cross-layer behavior | [`change-management.md`](./change-management.md) |

When adding a new rule file:

- One topic per file
- File name `<topic>.md` (lowercase, hyphenated)
- Add a row to the table above
- The body should be **prescriptive, not descriptive** — tell readers what to do, not what the project happens to look like
