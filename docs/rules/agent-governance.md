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
