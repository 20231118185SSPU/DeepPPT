---
name: ppt-master
description: >
  AI-driven multi-format SVG content generation system. Converts source documents
  (PDF/DOCX/URL/Markdown) into high-quality SVG pages and exports to PPTX through
  multi-role collaboration. Use when user asks to "create PPT", "make presentation",
  "生成PPT", "做PPT", "制作演示文稿", or mentions "ppt-master".
---

# PPT Master Skill

> AI-driven multi-format SVG content generation system. Converts source documents into high-quality SVG pages through multi-role collaboration and exports to PPTX.

**Core Pipeline**: `Source Document → Create Project + Dashboard → [Template] → Strategist → [Image_Generator] → Executor Live Preview → Quality Check → Post-processing → Export`

> ⚠️ **Mandatory load order — run the integrity gate first** [NEEDS_HUMAN_REVIEW]: before any PPT generation task or repo modification, run the fail-closed skill integrity gate and fix anything it reports:
> ```bash
> python3 ${SKILL_DIR}/scripts/attribution_guard.py
> ```
> It verifies the DeepPPT2 identity bundle (`attribution/identity.json` + repo `LICENSE`) and the presence of the critical pipeline entry scripts. After intentionally editing `attribution/identity.json`, refresh the embedded digest with `python3 ${SKILL_DIR}/scripts/attribution_guard.py --register`.

> [!CAUTION]
> ## 🚨 Global Execution Discipline (MANDATORY)
>
> **This workflow is a strict serial pipeline. The following rules have the highest priority — violating any one of them constitutes execution failure:**
>
> 1. **SERIAL EXECUTION** — Steps MUST be executed in order; the output of each step is the input for the next. Non-BLOCKING adjacent steps may proceed continuously once prerequisites are met, without waiting for the user to say "continue"
> 2. **BLOCKING = HARD STOP** — Steps marked ⛔ BLOCKING require a full stop; the AI MUST wait for an explicit user response before proceeding and MUST NOT make any decisions on behalf of the user
> 3. **NO CROSS-PHASE BUNDLING** — Cross-phase bundling is FORBIDDEN. (Note: the Eight Confirmations in Step 4 are ⛔ BLOCKING — the AI MUST present recommendations and wait for explicit user confirmation before proceeding. Once the user confirms, all subsequent non-BLOCKING steps — design spec output, SVG generation, speaker notes, and post-processing — may proceed automatically without further user confirmation)
> 4. **GATE BEFORE ENTRY** — Each Step has prerequisites (🚧 GATE) listed at the top; these MUST be verified before starting that Step
> 5. **NO SPECULATIVE EXECUTION** — "Pre-preparing" content for subsequent Steps is FORBIDDEN (e.g., writing SVG code during the Strategist phase)
> 6. **NO SUB-AGENT SVG GENERATION** — Executor Step 6 initial per-page SVG authoring is context-dependent and MUST be completed by the current main agent end-to-end. Delegating page SVG generation to sub-agents is FORBIDDEN. The later `visual-review` workflow may still perform its own constrained review / atomic-fix protocol when that workflow explicitly calls for it
> 7. **SEQUENTIAL PAGE GENERATION ONLY** — In Executor Step 6, after the global design context is confirmed, SVG pages MUST be generated sequentially page by page in one continuous pass. Grouped page batches (for example, 5 pages at a time) are FORBIDDEN
> 8. **SPEC_LOCK RE-READ PER PAGE** — Before generating each SVG page, Executor MUST `read_file <project_path>/spec_lock.md`. All colors / fonts / icons / images MUST come from this file — no values from memory or invented on the fly. Executor MUST also look up the current page's `page_rhythm` (`anchor` / `dense` / `breathing`), `page_layouts` (which template SVG to inherit, if any), and `page_charts` (which chart template to adapt, if any). Empty / absent entries are intentional Strategist signals — see executor-base.md §2.1. Also see executor-base.md §2.1a for narrative restatement. This rule exists to resist context-compression drift on long decks and to break the uniform "every page is a card grid" default
> 9. **SVG MUST BE HAND-WRITTEN, NOT SCRIPT-GENERATED** — Every SVG page is written by the main agent directly, one page at a time (see rules 6 and 7). Writing or running a Python / Node / shell script that produces the SVG files in batch — looping over pages, templating from data, or emitting them via a generator — is FORBIDDEN, including under "save tokens", "quick draft", or "user is in a hurry" pretexts. The script-generation path was tried on a feature branch and abandoned: cross-page visual consistency depends on per-page authoring with full upstream context, which a generator script cannot reproduce

> [!IMPORTANT]
> ## 🌐 Language & Communication Rule
>
> - **Response language**: match the user's input and source materials. Explicit user override (e.g., "请用英文回答") takes precedence.
> - **Template format**: `design_spec.md` MUST follow its original English template structure (section headings, field names) regardless of conversation language. Content values may be in the user's language.

> [!IMPORTANT]
> ## 🔌 Compatibility With Generic Coding Skills
>
> - `ppt-master` is a repository-specific workflow, not a general application scaffold
> - Do NOT create `.worktrees/`, `tests/`, branch workflows, or generic engineering structure by default
> - On conflict with a generic coding skill, follow this skill unless the user explicitly says otherwise
---

## Route Selection

Load [`workflows/routing.md`](workflows/routing.md) to select exactly one top-level route, then follow only that route's authority. The four routes:

| Route | Authority | Trigger |
|---|---|---|
| **Generate PPTX** | [`workflows/generate-pptx.md`](workflows/generate-pptx.md) | New presentation; regenerate an existing deck visually; source material or topic; optional explicit template workspace |
| **Create Template** | [`workflows/create-template.md`](workflows/create-template.md) | Reusable brand / layout / deck template request (child: [`workflows/create-brand.md`](workflows/create-brand.md)) |
| **Fill Native PPTX** | [`workflows/template-fill-pptx.md`](workflows/template-fill-pptx.md) | Raw PPTX native slide shells + new content |
| **Enhance Native PPTX** | [`workflows/native-enhance-pptx.md`](workflows/native-enhance-pptx.md) | Finished PPTX + notes / audio / timings / transitions |

- Pre-pipeline flows for topic-only inputs: [`ppt-briefing`](workflows/ppt-briefing.md) → [`deep-research`](workflows/deep-research.md).
- Generate-route stages and profiles: [`workflows/index.md`](workflows/index.md).
- Failure recovery: [`workflows/governance/failure-recovery.md`](workflows/governance/failure-recovery.md).
- Shared native PPTX revision (OfficeCLI): [`workflows/stages/native-revision.md`](workflows/stages/native-revision.md).

## Context Loading Strategy

- **ALWAYS LOAD**: Global Execution Discipline (this section), Language & Communication Rule, Compatibility section
- **LOAD ON DEMAND**: [`workflows/generate-pptx.md`](workflows/generate-pptx.md) (route authority — tooling table, template index, Steps 1-8), [`workflows/routing.md`](workflows/routing.md) + [`workflows/index.md`](workflows/index.md) (when routing)
- **DO NOT PRE-LOAD**: Individual workflow files, reference files, script READMEs

---

## Role Switching Protocol

Before switching roles, **MUST first read** the corresponding reference file. Output marker:

```markdown
## [Role Switch: <Role Name>]
📖 Reading role definition: references/<filename>.md
📋 Current task: <brief description>
```

---

## Project Folder Integrity

All artifacts for a single PPT project must reside inside one project folder. Do NOT scatter outputs across `projects/`.

**Hard rules**:
- Research reports (`research_report.md`) live inside the project folder, not in `projects/` root
- Analysis files (`research_analysis.json`, `visual_strategy.json`) live in `<project>/analysis/`
- Do NOT create parallel folders for the same task (e.g., `projects/my_topic_analysis/` alongside `projects/my_topic_ppt169_/`)
- The folder created by `project_manager.py init` is the single canonical location for all project outputs

> For the complete project folder structure diagram, see [`workflows/deep-research.md`](workflows/deep-research.md) §Project folder structure.

---

## Reference Resources

| Resource | Path |
|----------|------|
| Shared technical constraints | `references/shared-standards.md` |
| Canvas format specification | `references/canvas-formats.md` |
| Image-text layout patterns (Primary structures + Modifier layers — combine freely) | `references/image-layout-patterns.md` |
| Image layout sizing (math for side-by-side container dimensions) | `references/image-layout-spec.md` |
| SVG image embedding | `references/svg-image-embedding.md` |
| Icon library | `templates/icons/README.md` |

---

## Notes

- Local preview: `python3 -m http.server -d <project_path>/svg_final 8000`
- **Troubleshooting**: on generation issues (layout overflow, export errors, blank images, etc.), check `docs/faq.md` for known solutions
