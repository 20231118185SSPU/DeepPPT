# CLAUDE.md — Full Reference

> **This file supplements `CLAUDE.md` (project root).** The root file is the lightweight charter loaded at every conversation start. This file contains the complete operational reference — read it on-demand when executing specific steps.

## Pipeline Details

**Core Pipeline**: `Source Document → Create Project → [Template] → [Content Selection] → [Detailed Outline] → Strategist Eight Confirmations → [Image_Generator + Image-Text Linking] → Executor Live Preview → Quality Check → Post-processing → Export PPTX`

Content Selection, Detailed Outline, and Image-Text Linking are conditional phases activated when `research_report.md` exists (from topic-research or deep-research). See SKILL.md Step 2 checkpoint, Step 4, and Step 5 for trigger conditions.

Topic-only requests with no source material: run one of the two research workflows before SKILL.md Step 1:
- [`topic-research`](skills/ppt-master/workflows/topic-research.md) — quick research (3-round web search → fact-list Markdown)
- [`deep-research`](skills/ppt-master/workflows/deep-research.md) — deep research (multi-source discovery → structured analysis → narrative construction → visual strategy)

Choose deep-research when the user says "深度调研" / "deep research" or when content quality is the priority.

**deep-research creates the project directory at its own Step 1** (via `project_manager.py init`). All research artifacts write directly into `<project>/` — no staging directories, no scatter across `projects/`.

## Detailed Workflow Routing

Routing rules (discriminator logic for beautify vs. main pipeline, etc.):

> Template fill: when the user provides an existing `.pptx` template plus text materials or a topic and asks to reuse the original PPT design or fill content back into it (for example, "fill this deck with the new content", "fill this back into the template", or "reuse this deck's design"), run the standalone [`template-fill-pptx`](skills/ppt-master/workflows/template-fill-pptx.md) workflow. This route edits PPTX directly and must not enter the SVG generation pipeline.
>
> Beautify / re-layout: when the user provides an existing `.pptx` and asks to beautify or re-layout it while keeping the content (for example, "把这份 PPT 美化一下", "重新排版，内容别动", or wants to paste the regenerated elements back into the original deck), run the standalone [`beautify-pptx`](skills/ppt-master/workflows/beautify-pptx.md) workflow. Mirror of template-fill: content is preserved verbatim, the source's palette/fonts are inherited as truth, only layout is redesigned. Unlike template-fill, it regenerates a native deck through the SVG pipeline (Strategist → Executor → export), one source slide to one page; it does not edit the source in place. Routing boundary — beautify is for "keep this deck, just lay it out better": page count and page order are preserved 1:1. If the original page breakdown itself should be reconsidered (merge / split / reorder pages, re-outline the structure), that is NOT beautify: convert the deck with [`ppt_to_md`](skills/ppt-master/scripts/source_to_md/ppt_to_md.py) and run the main SKILL.md pipeline, where the Strategist re-architects the outline freely from the extracted content. The discriminator is page count / order: any change to it — split, merge, drop, reorder, even just splitting a crowded page so it reads better — is the main pipeline; beautify is strictly 1:1. Decide by one question: is the source's page split information to preserve, or just the previous author's structure to improve?
>
> Phase B resumption (split-mode execution): when the user opens a fresh chat and says "继续生成 projects/<x>" or similar, run the standalone [`resume-execute`](skills/ppt-master/workflows/resume-execute.md) workflow to enter Phase B (SVG generation + export) without re-running Phase A.
>
> Spec refinement (opt-in): when the user explicitly asks to refine / review / revise the spec before generation (for example "refine the spec first", "review the spec before generating", "send me the spec to confirm first"), run the standalone [`refine-spec`](skills/ppt-master/workflows/refine-spec.md) workflow. Strategist produces the full `design_spec.md` + `spec_lock.md` first, then stops so the user can revise any part of it (outline, color, typography, layout, image strategy, …) before any image or SVG work; on approval the pipeline resumes at Step 5/6. Default is OFF — no request means the spec is written in one pass and the pipeline auto-proceeds. Surfaced as an opt-in line in the Eight Confirmations, same shape as the split-mode note; never enter it unprompted.
>
> Decks containing data charts: run the standalone [`verify-charts`](skills/ppt-master/workflows/verify-charts.md) workflow between the executor and post-processing steps to calibrate chart coordinates.
>
> Recorded narration / video export: run the standalone [`generate-audio`](skills/ppt-master/workflows/generate-audio.md) workflow after post-processing.
>
> Object-level animation tuning: when the user asks to change animation order, effect, timing, or a specific object's reveal behavior, run the standalone [`customize-animations`](skills/ppt-master/workflows/customize-animations.md) workflow. Default export applies page transitions but no per-element entrance animation (element builds are opt-in); create `animations.json` or pass `-a auto` only when the user asks for element animation or object-level customization.
>
> Live preview: any time the user mentions "live preview", "preview", "看效果", or wants to click/select a slide element, run [`live-preview`](skills/ppt-master/workflows/live-preview.md). Step 6 auto-starts it during generation; the workflow covers post-export re-entry and applying submitted annotations.
>
> Brand identity setup: when the user asks to "set up brand" / "建立品牌" / "做品牌规范", provides a brand asset (logo / brand site URL / branded PPTX / brand PDF), or wants to extract a brand from existing materials, run the standalone [`create-brand`](skills/ppt-master/workflows/create-brand.md) workflow. Output goes to `skills/ppt-master/templates/brands/<id>/`. Brands apply at SKILL.md Step 3 via the same explicit-path rule as layout templates — the user supplies the brand directory path to apply it; bare brand names never trigger.
>
> Visual self-check: only when the user explicitly requests a per-page visual review on the generated SVGs (e.g., "跑一下视觉自检 / 视觉回看 / 视觉 rubric", "visual review", "check each page visually"), run the standalone [`visual-review`](skills/ppt-master/workflows/visual-review.md) workflow between the executor and post-processing steps. The main pipeline does NOT invoke it automatically; do not infer or recommend it from deck size, model identity, or any other signal — user request is the only trigger.

## Environment & Setup

| Dependency | Required | Notes |
|------------|:--------:|-------|
| Python ≥3.10 | ✅ | Only runtime needed |
| Git | ✅ | For cloning |
| Playwright + Chromium | ❌ | Only for browser screenshots in web image capture |

```bash
# One-click install (recommended)
bash scripts/setup/install_deps.sh                    # Linux / Mac
powershell -ExecutionPolicy Bypass -File scripts/setup/install_deps.ps1  # Windows

# Check dependency status
python3 scripts/setup/check_deps.py
python3 scripts/setup/check_deps.py --install          # auto-install missing

# Manual install (core only)
pip install python-pptx Pillow requests beautifulsoup4 lxml
```

API configuration: copy `.env.example` → `.env`, set `IMAGE_BACKEND` and the corresponding API key. Zero-config image search sources (Openverse, Wikimedia, NASA, Smithsonian) need no API key.

## Multi-Role Architecture

The pipeline operates through three serial roles. Each role is a distinct prompt/persona loaded from `skills/ppt-master/references/`, not a separate process:

| Role | Responsibility | Key Output |
|------|---------------|------------|
| **Strategist** | Outline, Eight Confirmations, `design_spec.md`, `spec_lock.md`, image strategy | `design_spec.md`, `spec_lock.md`, `notes/*.md`, `image_prompts.json` / `image_queries.json` |
| **Image_Generator** | Acquire images (AI generation or web search) per Strategist's manifest | `images/*.png` + `image_sources.json` |
| **Executor** | Render one SVG per page following `spec_lock.md` constraints, run quality checks | `pages/*.svg` |

Steps are strictly serial. Steps marked ⛔ BLOCKING require explicit user confirmation. SVG pages are hand-written by the agent (never script-generated). Before generating each SVG page, re-read `spec_lock.md` for colors/fonts/icons/images.

## Project Artifact Structure

Each generated project lives under `projects/<name>/` with this layout:

```
projects/<name>/
├── design_spec.md          # Strategist's full design specification
├── spec_lock.md            # Locked palette/typography/icons/images for Executor
├── notes/                  # Per-page content notes (01_cover.md, 02_..., total.md)
├── images/                 # Acquired images + manifest files
│   ├── image_prompts.json  # AI generation manifest (Strategist writes)
│   ├── image_queries.json  # Web search manifest (Strategist writes)
│   └── image_sources.json  # Provenance metadata (Image_Generator writes)
├── icons/                  # Selected icons copied from template library
├── pages/                  # SVG files, one per slide (Executor writes)
├── source/                 # Imported source documents
└── <name>.pptx             # Final exported presentation
```

Format is set at init time (`--format ppt169` for 16:9, `--format ppt43` for 4:3). The `research_report.md` file (produced by topic-research or deep-research) activates conditional pipeline phases (Content Selection, Detailed Outline, Image-Text Linking).

## Execution Requirements

- For standalone template creation (no source deck), read [`skills/ppt-master/workflows/create-template.md`](skills/ppt-master/workflows/create-template.md).
- Technical SVG/PPT constraints live in [`skills/ppt-master/references/shared-standards.md`](skills/ppt-master/references/shared-standards.md).
- Canvas choices live in [`skills/ppt-master/references/canvas-formats.md`](skills/ppt-master/references/canvas-formats.md).
- Icon library details live in [`skills/ppt-master/templates/icons/README.md`](skills/ppt-master/templates/icons/README.md).

## Required Conventions

- **Repo-wide style rules** — when editing prompt files under [`skills/ppt-master/references/`](skills/ppt-master/references/), Python under [`skills/ppt-master/scripts/`](skills/ppt-master/scripts/), or any other code/prose in the repo, follow the matching style rule in [`docs/rules/`](docs/rules/).
- **Markdown language consistency** — Markdown files under `skills/ppt-master/workflows/`, `skills/ppt-master/references/`, and `docs/` are currently single-language per directory. New files mirror the language of their siblings; do not mix English scaffolding with Chinese paragraphs (or vice versa) inside one file. Chat replies are unaffected.

## Command Quick Reference

Convenience summary only — full workflow in [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md).

```bash
# Source content conversion
python3 skills/ppt-master/scripts/source_to_md/pdf_to_md.py <PDF_file>
python3 skills/ppt-master/scripts/source_to_md/doc_to_md.py <DOCX_or_other_file>
python3 skills/ppt-master/scripts/source_to_md/excel_to_md.py <XLSX_or_XLSM_file>
python3 skills/ppt-master/scripts/source_to_md/ppt_to_md.py <PPTX_file>
python3 skills/ppt-master/scripts/source_to_md/web_to_md.py <URL>

# Agent-Reach 多平台内容采集（可选，需 pip install agent-reach）
agent-reach doctor --json                          # 检查平台可用状态
curl -s "https://r.jina.ai/<URL>"                  # 网页转 Markdown（零配置）
curl -s "https://api.bilibili.com/x/web-interface/search/all/v2?keyword=<关键词>"  # B站搜索
yt-dlp --write-auto-sub --sub-lang zh,en --skip-download "<YouTube_URL>"  # YouTube 字幕

# Project management
python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files_or_URLs...> --move
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>
python3 skills/ppt-master/scripts/project_manager.py checkpoint save <project_path> [--notes "..."]
python3 skills/ppt-master/scripts/project_manager.py checkpoint load <project_path>

# Icon selection — copy chosen library icons into <project>/icons/ (missing names reported + non-zero = re-pick)
python3 skills/ppt-master/scripts/icon_sync.py <project_path> <lib/name> [<lib/name>...]

# Step 4 Eight Confirmations — interactive visual page (default auto-launch; chat fallback)
python3 skills/ppt-master/scripts/confirm_ui/server.py <project_path> --daemon --wait

# Image tools and SVG quality check
python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images
# Formula rendering — manifest written by Strategist after typography confirmation:
python3 skills/ppt-master/scripts/latex_render.py <project_path>
python3 skills/ppt-master/scripts/latex_render.py <project_path> --dry-run
python3 skills/ppt-master/scripts/latex_render.py <project_path> --providers codecogs,quicklatex,mathpad,wikimedia
# In-pipeline AI image generation — manifest mode (required, even for 1 image):
python3 skills/ppt-master/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json
python3 skills/ppt-master/scripts/image_gen.py --render-md <project_path>/images/image_prompts.json
# Out-of-pipeline one-off / debug / single-image fixup only (no manifest, no sidecar):
python3 skills/ppt-master/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
# 网络图片搜索（批量模式）
python3 skills/ppt-master/scripts/image_search.py --batch <project_path>/images/image_queries.json -o <project_path>/images
# 网页截图采集（深度调研产品页面）
python3 skills/ppt-master/scripts/image_search.py --url-capture https://example.com -o <project_path>/images/web_assets/web_assets
python3 skills/ppt-master/scripts/svg_editor/server.py <project_path> --live
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
python3 skills/ppt-master/scripts/spec_compliance_check.py <project_path>    # spec_lock semantic compliance
python3 skills/ppt-master/scripts/spec_lock_digest.py generate <project_path>  # Step 4 end: seal spec_lock integrity
python3 skills/ppt-master/scripts/spec_lock_digest.py verify <project_path>    # Step 6 start: verify before Executor reads
python3 skills/ppt-master/scripts/e2e_validate.py <project_path>               # post-export: page count + notes + images + PPTX
python3 skills/ppt-master/scripts/e2e_validate.py <project_path> --pptx exports/deck.pptx  # with PPTX slide-level checks
python3 skills/ppt-master/scripts/smoke_check.py                                # import + CLI smoke check for all scripts
python3 skills/ppt-master/scripts/animation_config.py scaffold <project_path>  # optional, only for custom object-level animation
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>  # optional, before re-export

# Post-processing pipeline: run sequentially, one command at a time
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
# Mergeable dy-stacked paragraph blocks collapse into one editable text frame by default; add --no-merge to keep every line as its own frame (strict line fidelity). See SKILL.md Step 7.3.
```

## Core Directories

- `skills/ppt-master/SKILL.md` — main workflow authority.
- `skills/ppt-master/references/` — role definitions and technical specifications.
- `skills/ppt-master/scripts/` — runnable tool scripts.
- `skills/ppt-master/scripts/docs/` — topic-focused script docs.
- `skills/ppt-master/templates/` — layout templates (including `layouts/content_pages/` with 18 pre-built content page variants across academic/business/report scenarios), chart templates, icon library, brand presets.
- `skills/ppt-master/workflows/` — standalone workflow files.
- `docs/` — user-facing documentation (FAQ, installation, technical design, templates guide, audio narration).
- `docs/rules/` — repo-wide style rules.
- `examples/` — example projects.
- `projects/` — user project workspace.
