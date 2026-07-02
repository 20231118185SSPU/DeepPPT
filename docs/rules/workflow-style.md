# Workflow Style Rules

> Scope: standalone workflow runbooks under `skills/ppt-master/workflows/` and research substeps under `skills/ppt-master/workflows/research/`.
> Status: draft governance rule. It guides workflow documentation edits but does not override `SKILL.md` or any owning workflow file.

Workflow files are runtime instructions for a specific route. They should be clear enough to execute without duplicating the entire main pipeline.

---

## 1. Header Shape

New or substantially revised standalone workflows should use this shape:

```markdown
# <Workflow Name>

> Authority: standalone workflow for <scope>. It does not override `skills/ppt-master/SKILL.md` outside this scope.

## When to Run
## When NOT to Run
## Inputs
## Gates
## Steps
## Exit Evidence
## Fallback / Recovery
## Integration With SKILL.md
```

Existing workflows do not need mechanical rewrites. Apply this structure when a file is already being edited for behavior or clarity.

---

## 2. Trigger Language

| Label | Meaning |
|---|---|
| `When to Run` | Actual entry condition based on user intent or artifact evidence |
| `When NOT to Run` | Boundary that routes elsewhere |
| `Default` | Behavior used without extra user choice |
| `Recommended` | Surface to the user or run only when the owning authority says it is default |
| `Hard rule` | Non-negotiable behavior inside this workflow |
| `BLOCKING` | Stop and wait for explicit user confirmation |

**Hard rule**: "applies to", "useful for", or "high quality" wording is not an automatic trigger. If a condition is only a recommendation signal, label it as such.

---

## 3. Gates And Evidence

Every gate should name concrete evidence:

| Gate type | Evidence examples |
|---|---|
| User confirmation | exact confirmation, `confirm_ui/result.json`, or workflow-specific result |
| Artifact existence | file path and freshness expectation |
| Script pass | command and expected pass/fail semantics |
| Handoff | next workflow, required inputs, and stop condition |

Do not state a gate as a preference. If the workflow may proceed after a warning, say who accepts the warning and where it is recorded.

---

## 4. Scope Boundaries

| File class | Rule |
|---|---|
| Standalone workflows | Own only their route's entry, steps, gates, fallback, and exit evidence |
| `research/*.md` | Own deep-research substeps only; do not become independent entry routes |
| Implementation plans | Put in `docs/design/` or mark clearly as non-runtime drafts |

If a workflow requires a main-pipeline behavior change, mark it as "requires user confirmation to promote into `SKILL.md`" instead of silently enforcing it.

---

## 5. Integration With SKILL.md

When a workflow wraps or branches from the main pipeline, state:

1. Where it starts relative to `SKILL.md`.
2. Which `SKILL.md` gates still apply unchanged.
3. Which workflow-specific gates add hard stops.
4. Where control returns to `SKILL.md`.

Do not copy long `SKILL.md` command blocks unless the command is different in this workflow.
