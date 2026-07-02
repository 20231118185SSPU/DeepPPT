# Change Management Rules

> Scope: documentation, workflow, reference, script, routing, and AI-entry changes that can affect agent behavior.
> Status: draft governance rule. It guides change planning and reporting but does not override explicit user instructions or higher-authority workflow files.

Use this file to decide when a documentation change is safe to make directly, when it needs explicit user confirmation, and what must be reported afterward.

---

## 1. Risk Levels

| Risk | Examples | Requirement |
|---|---|---|
| High | `AGENTS.md`, `SKILL.md`, workflow gates, BLOCKING behavior, export/quality rules, destructive commands | Get explicit user confirmation before changing unless the user already specifically requested that change |
| Medium | `docs/routing.md`, `docs/ai-rules-shared.md`, workflow trigger wording, docs/rules, design status labels | Read authority upstream, make scoped edits, report before/after semantics |
| Low | Typos, broken links, formatting that does not change behavior | Make scoped edits and report files touched |

**Hard rule**: do not move, delete, merge, or archive existing docs unless the user explicitly approves that structural change.

---

## 2. Authority Changes

Before changing a rule that affects agent behavior:

1. Identify the owning authority file.
2. Check whether the current task authorizes editing that file.
3. If not authorized, update only lower-level summaries or mark the authority change as requiring confirmation.
4. Do not enforce design-draft recommendations as active rules.

Examples that usually need explicit confirmation:

| Change | Owner |
|---|---|
| Main pipeline step, gate, or export behavior | `skills/ppt-master/SKILL.md` |
| Repository-level reading or safety rule | `AGENTS.md` |
| Standalone workflow entry or hard stop | owning `skills/ppt-master/workflows/*.md` |
| Role behavior or SVG/PPT technical rule | owning `skills/ppt-master/references/*.md` |

---

## 3. Summary Synchronization

When editing routing or AI-entry summaries:

| Summary | Upstream to check |
|---|---|
| `docs/routing.md` | `SKILL.md` and the referenced workflow |
| `docs/ai-rules-shared.md` | `AGENTS.md`, `SKILL.md`, `docs/routing.md` |
| User docs that mention workflows | `SKILL.md` or the owning workflow |
| Design docs claiming implementation | actual implemented files |

If the upstream is unclear, do not invent a rule. Record the ambiguity and ask for confirmation.

---

## 4. Reporting Requirements

For medium or high risk changes, final handoff should include:

1. Files changed.
2. Why each file changed.
3. Before/after behavior for agent-facing rules.
4. Files intentionally not changed.
5. Follow-up items needing user confirmation.
6. Verification performed.

For low-risk copyedits, a concise file list and verification note is enough.

---

## 5. Change Log

Use `docs/change-log.md` when the change affects shipped workflow behavior, scripts, references, or user-facing operating instructions. For governance-only edits, either update the change log when requested or include the change summary in the final response.
