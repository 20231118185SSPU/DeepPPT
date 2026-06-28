---
description: Deep research orchestrator — coordinates 7 independent research steps (outline → search plan → per-page search → consolidation → analysis → narrative → visual strategy). Produces structured research artifacts that feed the main PPT pipeline. Run for all topic-only and content-quality-first requests.
---

# Deep Research Workflow (Orchestrator)

> Pre-pipeline orchestrator that coordinates 7 independent research steps. Each step is a standalone workflow file under `research/` with its own output directory under `_research/`. The orchestrator ensures correct sequencing and handles the hand-off to the main PPT pipeline.

This workflow is the **single entry point** for all research. The former `topic-research.md` (quick mode) has been removed — all inputs go through this unified flow.

## When to Run

| User-supplied input | Action |
|---|---|
| Topic only (no files) | Run full 7-step flow |
| Topic + "深度调研" / "deep research" / "内容质量优先" | Run full 7-step flow |
| Topic + complex, multi-perspective subject matter | Run full 7-step flow |
| Source file attached (PDF / DOCX / URL / Markdown) | Run Step 1 (convert + outline), skip Step 3 (search), run Steps 4-7 |
| ≥1 page of substantive content already in chat | Skip — feed chat content into SKILL.md Step 1 directly |

---

## Project Folder Structure

All research artifacts reside inside `_research/` within the canonical project directory:

```
projects/<project_slug>/
├── _research/                        ← All research artifacts
│   ├── step1_outline/                ← outline.md + outline.json
│   ├── step2_search_plan/            ← search_plan.json
│   ├── step3_search/                 ← p{NN}_*.md + search_manifest.json + images/
│   ├── step4_consolidated/           ← consolidated.md
│   ├── step5_analysis/               ← research_analysis.json
│   ├── step6_narrative/              ← research_report.md
│   └── step7_visual/                 ← visual_strategy.json + ref/
├── analysis/                         ← Synced from step5 + step7
├── sources/                          ← Synced from step6
├── images/
│   ├── web_assets/                   ← Synced from step3
│   └── ref/                          ← Synced from step7
└── ... (rest of project structure)
```

**Hard rules**:
- Single project directory — no sibling folders, no staging
- All `_research/` artifacts write directly from their respective steps
- No copy-in-later — every step writes to its final location

---

## Step 0: Initialize Project

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
mkdir -p <project>/_research/{step1_outline,step2_search_plan,step3_search,step4_consolidated,step5_analysis,step6_narrative,step7_visual}
mkdir -p <project>/_research/step3_search/images
mkdir -p <project>/_research/step7_visual/ref
```

---

## Step 1: Outline Generation

📄 Workflow: [`research/step1_outline.md`](./research/step1_outline.md)

| Item | Detail |
|------|--------|
| Input | User topic + background docs (if any) + source files (if any) |
| Output | `_research/step1_outline/outline.md` + `outline.json` |
| Executor | Main AI (Claude) |
| Blocking | ⛔ YES — user must confirm outline before proceeding |

If source files are provided, convert them to Markdown first:
```bash
python3 ${SKILL_DIR}/scripts/source_to_md/pdf_to_md.py <file>    # PDF
python3 ${SKILL_DIR}/scripts/source_to_md/doc_to_md.py <file>    # DOCX
python3 ${SKILL_DIR}/scripts/source_to_md/web_to_md.py <url>     # URL
```

---

## Step 2: Search Plan

📄 Workflow: [`research/step2_search_plan.md`](./research/step2_search_plan.md)

| Item | Detail |
|------|--------|
| Input | `_research/step1_outline/outline.json` |
| Output | `_research/step2_search_plan/search_plan.json` |
| Executor | Main AI (Claude) |
| Blocking | No |

AI assignment rules:
- **Tech/Data** → ChatGPT (chatgpt)
- **News/Trends** → Grok (grok)
- **Academic/Deep** → Perplexity (perplexity)

---

## Step 3: Per-Page Search

📄 Workflow: [`research/step3_search.md`](./research/step3_search.md)

| Item | Detail |
|------|--------|
| Input | `_research/step2_search_plan/search_plan.json` |
| Output | `_research/step3_search/p{NN}_*.md` + `search_manifest.json` + `images/` |
| Executor | Main AI (Claude) via Playwright browser automation |
| Blocking | No |

**Browser automation**:
```bash
# Batch search via browse_ai.py
python3 ${SKILL_DIR}/scripts/research/browse_ai.py \
  --batch <project>/_research/step2_search_plan/search_plan.json \
  --output-dir <project>/_research/step3_search/
```

**Fallback** when Playwright is unavailable or all browser AIs fail: `browse_ai.py` writes `needs_manual_websearch` and a copyable prompt into `search_manifest.json`; the Agent then manually uses built-in WebSearch + WebFetch + `web_to_md.py`. Local Python cannot call the Agent's built-in WebSearch by itself.

**Skip condition**: When user provided source files and all pages have sufficient material, mark all pages as `skip_search: true` in search_plan and skip this step.

---

## Step 4: Consolidation

📄 Workflow: [`research/step4_consolidate.md`](./research/step4_consolidate.md)

| Item | Detail |
|------|--------|
| Input | `_research/step3_search/` all results + `step1_outline/outline.json` |
| Output | `_research/step4_consolidated/consolidated.md` |
| Executor | Main AI (Claude) |
| Blocking | No |

---

## Step 5: Structured Analysis

📄 Workflow: [`research/step5_analysis.md`](./research/step5_analysis.md)

| Item | Detail |
|------|--------|
| Input | `_research/step4_consolidated/consolidated.md` |
| Output | `_research/step5_analysis/research_analysis.json` |
| Executor | Main AI (Claude) |
| Blocking | No |

Incremental write (3 rounds) to prevent timeout.

---

## Step 6: Narrative Construction

📄 Workflow: [`research/step6_narrative.md`](./research/step6_narrative.md)

| Item | Detail |
|------|--------|
| Input | `_research/step5_analysis/research_analysis.json` + `consolidated.md` |
| Output | `_research/step6_narrative/research_report.md` |
| Executor | Main AI (Claude) |
| Blocking | No |

Incremental write (3 rounds). Quality gate enforces narrative depth contract.

---

## Step 7: Visual Strategy

📄 Workflow: [`research/step7_visual.md`](./research/step7_visual.md)

| Item | Detail |
|------|--------|
| Input | `_research/step6_narrative/research_report.md` + `research_analysis.json` |
| Output | `_research/step7_visual/visual_strategy.json` + `ref/` |
| Executor | Main AI (Claude) |
| Blocking | No |

⛔ **MANDATORY CHECKPOINT**: At least 1 reference image in `ref/`.

---

## Hand-off to Main Pipeline

After all 7 steps complete, sync artifacts to the main pipeline directories:

```bash
python3 ${SKILL_DIR}/scripts/research/sync_research_outputs.py <project>
```

**Checkpoint output**:

```markdown
<!-- RESEARCH_COMPLETE
project: <project_slug>
steps_completed: 7/7
artifacts:
  - _research/step1_outline/outline.json
  - _research/step2_search_plan/search_plan.json
  - _research/step3_search/search_manifest.json
  - _research/step4_consolidated/consolidated.md
  - _research/step5_analysis/research_analysis.json
  - _research/step6_narrative/research_report.md
  - _research/step7_visual/visual_strategy.json
next_step: content-selection (if research_report.md exists)
-->
```

**Next step**: Content Selection → Detailed Outline → SKILL.md Step 4 (Eight Confirmations).

---

## Error Recovery

| Scenario | Action |
|----------|--------|
| Step 3 search fails for all browser AIs | `browse_ai.py` marks `needs_manual_websearch`; Agent manually runs built-in WebSearch/WebFetch or asks user for URLs |
| Step 6 quality gate fails | Auto-return to Step 3 for gap pages, then re-run Steps 4-6 |
| Context window exhaustion | Use split mode: Steps 1-3 in one session, Steps 4-7 in another |
| Playwright unavailable | `browse_ai.py` cannot browse locally; use the emitted manual WebSearch prompt |
