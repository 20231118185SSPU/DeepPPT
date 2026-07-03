# AI Agent Governance Rules

> Scope: AI entry files, routing summaries, and design-draft boundaries. Applies to `AGENTS.md`, `docs/routing.md`, `docs/ai-rules-shared.md`, `docs/ai-router-design.md`, and `docs/design/*`.
> Status: draft governance rule. It guides low-risk documentation work but does not override `AGENTS.md`, `SKILL.md`, or owning workflow files.

These rules govern where agent-facing behavior may be stated. They do not replace `AGENTS.md`, `skills/ppt-master/SKILL.md`, or the owning workflow files.

---

## 1. Authority Order

| Layer | Files | Rule |
|---|---|---|
| Repository entry | `AGENTS.md` | Owns required reading, compatibility boundaries, safety constraints, and short high-risk routing pointers |
| Main workflow | `skills/ppt-master/SKILL.md` | Owns the PPT generation pipeline, gates, role switching, quality checks, post-processing, and export |
| Standalone workflow | `skills/ppt-master/workflows/*.md` | Owns the entry, gates, steps, fallback, and exit evidence for that workflow only |
| Technical reference | `skills/ppt-master/references/*.md` | Owns role behavior and SVG/PPT technical constraints when loaded by SKILL or a workflow |
| Rules | `docs/rules/*.md` | Owns editing style, governance, and change-management rules |
| Summaries | `docs/routing.md`, `docs/ai-rules-shared.md` | Summarize active rules; they do not outrank the owning workflow |
| Drafts and audits | `docs/ai-router-design.md`, `docs/design/*`, audit reports | Provide proposals or findings; they are not runtime authority |

**Conflict rule**: follow the highest applicable layer. If a summary disagrees with `SKILL.md` or an owning workflow, update the summary rather than changing runtime behavior.

---

## 2. Entry File Boundaries

| File type | Allowed | Forbidden |
|---|---|---|
| `AGENTS.md` | Required reading, compatibility boundaries, safety constraints, short routing pointers | Full workflow steps, long command copies, implementation drafts |
| `docs/routing.md` | Compact dispatch table and high-risk boundary reminders | Full workflow internals, research substep details, new authority rules |
| `docs/ai-rules-shared.md` | Lightweight cross-tool baseline and links to authority | Claims to be the single source of truth, copied workflow runbooks |
| `docs/ai-router-design.md` | Supervisor/router proposals and future automation ideas | Statements that imply unimplemented router behavior is active |

**Hard rule**: design proposals become active only after the specific rule is promoted into `AGENTS.md`, `SKILL.md`, or the owning workflow.

---

## 3. Summary Maintenance

When editing a summary document:

1. Read the owning authority first.
2. Preserve the summary's lower authority wording.
3. Link the owning file instead of copying long internal sections.
4. State the before/after behavior in the handoff or final response.
5. If the summary cannot be made accurate without changing `AGENTS.md`, `SKILL.md`, or a workflow gate, stop and mark the authority change as requiring user confirmation.

**Default**: keep `docs/routing.md` compact. Use one-line triggers and boundaries; put detailed gates in the workflow file.

---

## 4. Draft Boundaries

| Draft source | Runtime treatment |
|---|---|
| `docs/ai-router-design.md` | Read only for router governance or future implementation planning |
| `docs/design/*` | Read only for the named design area or implementation task |
| Audit reports | Read for findings and migration plans; do not treat recommendations as already approved |

**Required status**: new design drafts should declare `Status`, `Authority`, and `Implemented in` in the first screen.

---

## 5. Temporary Development Artifacts

`projects/` is a user workspace first. Agents must not use it as a general scratch directory for code experiments, Dashboard / Confirm UI smoke runs, validation logs, or one-off reproduction folders.

**Default location**: use a gitignored repository-local temporary directory such as `.tmp/` or `.codex-tmp/` for development artifacts that do not require the PPT project layout. Do not write temporary files outside the repository unless the user explicitly approves it.

**Allowed `projects/` exception**: use `projects/_smoke_*`, `projects/_tmp_*`, or `projects/_agent_*` only when the code under test requires a valid PPT project structure or project-relative behavior. The prefix marks the folder as disposable; it does not make cleanup optional.

**Hard rules**:

1. Never create an agent-only temporary project with an unprefixed user-looking name.
2. Every temporary directory created by an agent must use one of these disposable basenames: `_smoke_*`, `_tmp_*`, or `_agent_*`.
3. Before finishing, stop any Dashboard, Confirm UI, live preview, local HTTP server, or other service started for validation.
4. Before finishing, remove the temporary directories and logs the agent created.
5. If a temporary directory must be retained to reproduce a bug, the final response must list its absolute path, why it is retained, and the exact cleanup command.
6. Never delete a project directory unless its resolved absolute path is inside this repository and its basename starts with `_smoke_`, `_tmp_`, or `_agent_`.
7. Never bulk-clean `projects/`; report suspicious temporary directories and ask for user confirmation before deleting historical folders.

**Safe deletion check**: before deleting any temporary project, resolve the absolute path and verify both conditions are true: it is under `<repo>/projects/`, and the basename starts with an approved disposable prefix. If either check fails, stop.
