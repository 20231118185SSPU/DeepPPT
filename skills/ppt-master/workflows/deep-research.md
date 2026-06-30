---
description: Deep research orchestrator — coordinates 7 independent research steps (outline → search plan → per-page search → consolidation → analysis → narrative → visual strategy). Produces structured research artifacts that feed the main PPT pipeline. Run for all topic-only and content-quality-first requests.
---

# Deep Research Workflow (Orchestrator)

> Pre-pipeline orchestrator that coordinates 7 independent research steps. Each step is a standalone workflow file under `research/` with its own output directory under `_research/`. The orchestrator ensures correct sequencing and handles the hand-off to the main PPT pipeline.

This workflow is the **single entry point** for all research. The former `topic-research.md` (quick mode) has been removed — all inputs go through this unified flow.

**Hard rule**: Topic-only PPT requests MUST enter this workflow before SKILL.md Step 1. Do not satisfy the research phase with the agent's built-in WebSearch alone. Built-in WebSearch is only a recorded fallback after the browser-AI / Agent-Reach / platform-specific routes fail or return low-quality output.

**Hard rule**: The seven steps are separate deliverables. Do not merge consolidation, analysis, narrative construction, and visual strategy into one writing pass. Each step writes its own artifact and passes a quality gate before the next step starts.

## Research Depth Contract

| Metric | Minimum |
|---|---|
| Search dimensions | 4-6 dimensions |
| Search rounds per dimension | >=3 query rounds |
| Tier 1-2 sources per dimension | >=2 |
| Total cited sources | >=15 |
| Cross-verified facts | >=8 facts confirmed by >=2 independent sources |
| Structured data points | >=10 statistics / timeline events / comparisons / quotes |
| Research report body | >=3000 Chinese characters or equivalent depth in the deck language |
| DEEP_DIVE markers | >=5 |
| AI-page reference images | 1-3 vetted references per AI-generated page that depicts people, products, objects, places, or IP-specific subjects |
| Information pages | >=1 downloaded web asset or svg-native information card per deep-dive / comparison / data / timeline page |

If any metric fails, return to Step 2 or Step 3 and fill the gap before entering the main PPT pipeline. Do not pad prose to pass a word-count gate.

## When to Run

| User-supplied input | Action |
|---|---|
| Topic only (no files) | Run full 7-step flow |
| Topic + "深度调研" / "deep research" / "内容质量优先" | Run full 7-step flow |
| Topic + complex, multi-perspective subject matter | Run full 7-step flow |
| Source file attached (PDF / DOCX / URL / Markdown) | Run Step 1 (convert + outline), skip Step 3 only when the source already satisfies the depth contract; otherwise run targeted search for gaps, then run Steps 4-7 |
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
| Blocking | ⛔ YES — show the search plan and source strategy before executing |

AI assignment rules:
- **Tech/Data** → Kimi (`kimi`) 或 DeepSeek (`deepseek`)
- **News/Trends** → Grok (grok)
- **Academic/Deep** → Perplexity (perplexity)

---

## Step 3: Per-Page Search

📄 Workflow: [`research/step3_search.md`](./research/step3_search.md)

| Item | Detail |
|------|--------|
| Input | `_research/step2_search_plan/search_plan.json` |
| Output | `_research/step3_search/p{NN}_*.md` + `search_manifest.json` + `images/` |
| Executor | Main AI (Claude) via browser automation / Agent-Reach / platform CLIs; built-in WebSearch only as fallback |
| Blocking | No |

**Browser automation**:
```bash
# Batch search via browse_ai.py
python3 ${SKILL_DIR}/scripts/research/browse_ai.py \
  --batch <project>/_research/step2_search_plan/search_plan.json \
  --output-dir <project>/_research/step3_search/
```

**Fallback** when Playwright is unavailable or all browser AIs fail: `browse_ai.py` writes `needs_manual_websearch` and a copyable prompt into `search_manifest.json`; the Agent then manually uses built-in WebSearch + WebFetch + `web_to_md.py`. Local Python cannot call the Agent's built-in WebSearch by itself. Each fallback must record `fallback_reason` and `quality_gap` in `search_manifest.json`; fallback output is not accepted unless it still meets the per-page evidence thresholds in `research/step3_search.md`.

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

After all 7 steps complete, run the machine gate before syncing artifacts to the main pipeline directories:

```bash
python3 ${SKILL_DIR}/scripts/research/research_gate.py <project>
python3 ${SKILL_DIR}/scripts/research/sync_research_outputs.py <project>
```

**Hard rule**: `research_gate.py` runs after Step 7 and before `sync_research_outputs.py`. Any FAIL blocks sync and must return to the step reported by the gate (usually Step 2, Step 3, Step 5, Step 6, or Step 7). Do not continue into Content Selection or the main PPT pipeline with a failed research gate.

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
| Step 2 plan is too broad or source list is weak | Rewrite Step 2 before any search; do not compensate later with generic WebSearch |
| Step 3 page result does not map to the search plan | Re-search that page using its planned dimensions / queries / source targets |
| Step 6 quality gate fails | Auto-return to Step 3 for gap pages, then re-run Steps 4-6 |
| `research_gate.py` fails after Step 7 | Return to the exact step printed by the gate; re-run downstream steps, then run the gate again before sync |
| Context window exhaustion | Use split mode: Steps 1-3 in one session, Steps 4-7 in another |
| Playwright unavailable | `browse_ai.py` cannot browse locally; use the emitted manual WebSearch prompt |
