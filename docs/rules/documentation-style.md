# Documentation Style Rules

> Scope: user documentation, architecture explanations, design drafts, audits, and maintenance documents under `docs/`, `docs/zh/`, and `docs/design/`.
> Status: draft governance rule. It guides low-risk documentation work but does not override `AGENTS.md`, `SKILL.md`, or owning workflow files.

These rules keep documentation useful without turning explanations or drafts into hidden runtime authority.

---

## 1. Document Type

| Type | Location | Required stance |
|---|---|---|
| User guide / FAQ | `docs/*.md`, `docs/zh/*.md` | Explain usage and link authority; do not define workflow behavior |
| Architecture explanation | `docs/technical-design.md`, `docs/templates-architecture.md` | Explain design and data models; link implemented files |
| Routing aid | `docs/routing.md` | Summarize dispatch only; defer to `SKILL.md` and workflows |
| Design draft | `docs/design/*.md`, `docs/*-design.md` | Mark status and authority; never imply proposal is active |
| Audit report | `docs/*audit*.md` | State scope, findings, and confirmation requirements |
| Template / checklist | `docs/*template*.md` | Provide structure; do not bypass governance or user confirmation |

**Hard rule**: user docs, architecture docs, drafts, and audits must not claim to override `AGENTS.md`, `SKILL.md`, or workflow files.

---

## 2. Status Headers

Design drafts and audits should declare their status in the first screen:

```markdown
> Status: draft / implementation guide / implemented / archived.
> Authority: non-authoritative; `SKILL.md` and owning workflow files remain authoritative.
> Implemented in: `path/to/file` / Not implemented.
```

Use `Implemented in` only for files that actually contain the live rule or implementation. If a design is partially implemented, list the implemented pieces and mark the remaining parts as proposed.

---

## 3. Language Placement

| Location | Rule |
|---|---|
| `docs/` user docs | English is the default root version |
| `docs/zh/` | Chinese mirrors for user-facing docs |
| `docs/design/` | Internal design language may follow the task, but each file should stay internally consistent |
| Audit/governance drafts | May use the review language; must clearly mark status and authority |

Do not mix English scaffolding with long Chinese explanatory prose inside a new user-facing document unless matching an existing local pattern.

---

## 4. Cross-References

| Summary topic | Link authority |
|---|---|
| Main PPT pipeline | `skills/ppt-master/SKILL.md` |
| Standalone workflow behavior | `skills/ppt-master/workflows/<name>.md` |
| SVG/PPT technical constraints | `skills/ppt-master/references/shared-standards.md` or the relevant reference |
| Templates / brands | the relevant template workflow or architecture document |
| AI entry/routing governance | `docs/rules/agent-governance.md` |

**Default**: summarize once, then link. Do not paste full workflow steps into user docs.

---

## 5. Runtime Read Boundaries

Runtime agents should not read user guides, roadmaps, audits, or design drafts as execution rules unless the current task explicitly asks for that document. If a document is useful background, describe it as background in the response.
