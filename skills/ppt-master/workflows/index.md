---
description: Full DeepPPT2 workflow index with route ownership and the PPTX route boundary.
---

# Workflow Index

> Route ownership index for DeepPPT2. Selection authority lives in [`routing.md`](./routing.md); this file lists every workflow and where it belongs. Supporting documents are never competing top-level routes.

## Standalone Workflows

| Workflow | Path | Route | Purpose |
|----------|------|-------|---------|
| `ppt-briefing` | [`ppt-briefing.md`](./ppt-briefing.md) | Generate pre-flow | Topic-only pre-brief — create `ppt_brief.md` / `ppt_brief.json`, confirm goal / audience / narrative / material strategy before any research. All topic-only inputs route here first. |
| `deep-research` | [`deep-research.md`](./deep-research.md) | Generate pre-flow | Pre-pipeline orchestrator — 7-step research flow (outline → search plan → per-page search → consolidation → analysis → narrative → visual strategy). Topic-only inputs enter only after confirmed PPT Briefing. |
| `content-selection` | [`content-selection.md`](./content-selection.md) | Generate stage | Phase 1 — interactive content dimension selection after deep research. Parse report → present dimensions → user picks → confirm. Triggered automatically when `research_report.md` exists. |
| `detailed-outline` | [`detailed-outline.md`](./detailed-outline.md) | Generate stage | Phase 2 — per-page detailed outline generation (core argument, content bullets, narrative function, visual need). Feeds into Strategist's Eight Confirmations. |
| `image-text-linking` | [`image-text-linking.md`](./image-text-linking.md) | Generate stage | Phase 3 — ensure AI image prompts and web search keywords include page text context from detailed outline. Triggered when `detailed_outline.json` exists and image rows are present. |
| `template-fill` | [`template-fill-pptx.md`](./template-fill-pptx.md) | Fill Native PPTX | Give a native PPTX template deck plus source material; select fitting pages (a page may be reused for several output slides) and fill text back without SVG conversion |
| `native-enhance` | [`native-enhance-pptx.md`](./native-enhance-pptx.md) | Enhance Native PPTX | Append notes / narration audio / auto-advance timings / page transitions to a finished PPTX without regenerating slides |
| `beautify` | [`profiles/beautify-pptx.md`](./profiles/beautify-pptx.md) | Generate profile | Re-layout an existing PPTX through the SVG pipeline — preserve its text verbatim, inherit its palette/fonts as truth, redo only layout; mirror of `template-fill` |
| `quick-generate` | [`profiles/quick-generate.md`](./profiles/quick-generate.md) | Generate profile | Direct SVG → PPTX short circuit — no Strategist / confirmation / spec / lock |
| `create-template` | [`create-template.md`](./create-template.md) | Create Template | Standalone layout/deck template creation workflow |
| `create-brand` | [`create-brand.md`](./create-brand.md) | Create Template child | Standalone brand-only template creation (identity preset; no SVG page roster) |
| `resume-execute` | [`stages/resume-execute.md`](./stages/resume-execute.md) | Generate stage | Phase B entry — resume execution in a fresh chat after Phase A (Step 1–5) completed in another session (split mode) |
| `refine-spec` | [`stages/refine-spec.md`](./stages/refine-spec.md) | Generate stage | Spec refinement — produce the full design spec, stop for user review/revision of any part before generation (opt-in) |
| `verify-charts` | [`stages/verify-charts.md`](./stages/verify-charts.md) | Generate stage | Chart coordinate calibration — run after SVG generation if the deck contains data charts |
| `customize-animations` | [`stages/customize-animations.md`](./stages/customize-animations.md) | Generate stage | Object-level PPTX animation customization — run only when the user explicitly asks to tune animation order/effects/timing |
| `generate-audio` | [`stages/generate-audio.md`](./stages/generate-audio.md) | Generate stage | Recorded narration / video export — run after post-processing when the user asks for narrated or video output |
| `live-preview` | [`stages/live-preview.md`](./stages/live-preview.md) | Generate stage | Browser-based live preview — auto-started during generation and re-enterable any time the user mentions "live preview", "preview", "看效果", or wants to click/select a slide element |
| `visual-review` | [`stages/visual-review.md`](./stages/visual-review.md) | Generate stage | Per-page rubric-based visual self-check — recommended by default after quality gates pass (between Executor and post-processing). Skip with explicit user opt-out ("跳过视觉自检" / "skip visual review"). |
| `batch-review` | [`batch-review.md`](./batch-review.md) | Generate helper | Optional batch-by-batch generation with intermediate user visual feedback. Activate: "分批审阅" / "batch review". |
| `revision-loop` | [`revision-loop.md`](./revision-loop.md) | Generate helper | Multi-turn local revision — apply targeted patches to generated SVG pages without full regeneration. Enter when user says "修改"/"调整"/"revise" after Step 6. Uses Plan-Act-Guard pipeline. |
| `failure-recovery` | [`governance/failure-recovery.md`](./governance/failure-recovery.md) | All routes | Stop/continue governance with the recovery matrix |
| `native-revision` | [`stages/native-revision.md`](./stages/native-revision.md) | All routes (shared child) | OfficeCLI-backed native PPTX edit — inspection, browser preview, plan, atomic apply; always opt-in |

## PPTX Route Boundary

When the user provides an existing `.pptx`, route by the role of the source deck:

| User intent | Route | Contract |
|---|---|---|
| Preserve the deck's page split, page order, and per-slide wording; improve layout / hierarchy / whitespace | `beautify` | Source page count and order are 1:1; text and data values are frozen; visual identity is inherited after confirmation |
| Treat the deck as source material; rethink the story, merge / split / drop / reorder pages, or change page count | Main pipeline | `ppt_to_md` + PPTX intake provide content facts and candidates; Strategist may re-architect freely |
| Reuse the deck's native design with new material | `template-fill` | Clone selected source slides and replace text / table / chart data directly in OOXML; no SVG generation |
| Harvest the deck as a reusable future template | `create-template` | Build a template package, not a one-off generated deck |

**Deciding axis (beautify vs main pipeline) — one question, one discriminator**: is the source's page split a finished artifact to preserve, or a draft structure to overturn? The concrete discriminator is **page count / order**: if it changes at all — any split, merge, drop, or reorder — it is the **main pipeline**, never beautify. Beautify is **strictly 1:1**: same page count, same order, text verbatim, only layout / hierarchy / whitespace redone. Edge case made explicit: "keep all the content but split a crowded page so it reads better" still changes page count, so it is the **main pipeline** (re-pagination is re-architecture), not beautify.

Ambiguous requests such as "make this PPT more professional" or "optimize this deck" MUST be clarified with one question before routing: "Should the original page count/order and each slide's wording be preserved, or should the deck be treated as source material and restructured into a new story?" Preserve → `beautify`; restructure → main pipeline.
