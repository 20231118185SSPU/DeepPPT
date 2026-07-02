# AGENTS.md

This file is the project entry point for general AI agents.

**You MUST read [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) before any PPT generation task or repo modification.** This repository exists to generate presentations; SKILL.md is the authoritative workflow that owns project creation, role switching, serial execution, quality gates, post-processing, export, and every per-step command. The rest of this file only points to where related material lives — it never substitutes for SKILL.md.

## Project Overview

PPT Master is an AI-driven presentation generation system. Multi-role collaboration (Strategist → Image_Generator → Executor) converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML).

**Core Pipeline**: `Source Document → Create Project + Dashboard → [Template] → Strategist Eight Confirmations → [Image_Generator] → Executor Live Preview → Quality Check → Post-processing → Export PPTX`

> Topic-only requests with no source material: first run the [`ppt-briefing`](skills/ppt-master/workflows/ppt-briefing.md) workflow to create `ppt_brief.md` and `ppt_brief.json`, then stop for explicit user confirmation. Only after the user confirms the Brief may the agent run the [`deep-research`](skills/ppt-master/workflows/deep-research.md) orchestrator before SKILL.md Step 1. This route is: `Topic → PPT Briefing → user confirmation → deep-research`.
>
> Dashboard observability: after Step 2 creates the project directory and imports sources, start or reuse the unified read-only Dashboard with `python3 skills/ppt-master/scripts/dashboard/server.py <project_path> --daemon` (default port `8765`; occupied ports auto-advance). This auto-opens the browser in normal local runs; add `--no-browser` only for headless/remote sessions or when the user explicitly does not want a window. Report the actual URL and `<project_path>/dashboard/dashboard.log`; if launch fails, report the warning and continue the PPT workflow. Dashboard is for status/artifacts/quality/log/bridge visibility only — it does not replace Confirm UI, Live Preview, quality gates, post-processing, or export commands.
>
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
> Visual self-check: after Executor quality gates pass and before Step 7 post-processing, run the standalone [`visual-review`](skills/ppt-master/workflows/visual-review.md) workflow as the default recommended quality step. Skip it only when the user explicitly says "跳过视觉自检" / "skip visual review", or when `confirm_ui/result.json` contains `skip_visual_review: true`. For decks containing data charts, run [`verify-charts`](skills/ppt-master/workflows/verify-charts.md) first, then run `visual-review`.

## Execution Requirements

- For standalone template creation (no source deck), read [`skills/ppt-master/workflows/create-template.md`](skills/ppt-master/workflows/create-template.md).
- Technical SVG/PPT constraints live in [`skills/ppt-master/references/shared-standards.md`](skills/ppt-master/references/shared-standards.md).
- Canvas choices live in [`skills/ppt-master/references/canvas-formats.md`](skills/ppt-master/references/canvas-formats.md).
- Icon library details live in [`skills/ppt-master/templates/icons/README.md`](skills/ppt-master/templates/icons/README.md).

## Required Conventions

- **Repo-wide style rules** — when editing prompt files under [`skills/ppt-master/references/`](skills/ppt-master/references/), Python under [`skills/ppt-master/scripts/`](skills/ppt-master/scripts/), or any other code/prose in the repo, follow the matching style rule in [`docs/rules/`](docs/rules/).
- **Markdown language consistency** — Markdown files under `skills/ppt-master/workflows/`, `skills/ppt-master/references/`, and `docs/` are currently single-language per directory. New files mirror the language of their siblings; do not mix English scaffolding with Chinese paragraphs (or vice versa) inside one file. Chat replies are unaffected.

## Compatibility Boundary

- This repository is a workflow/skill package, not an app or service scaffold.
- Do NOT assume generic-project conventions like `.worktrees/`, `tests/`, or mandatory branch setup unless the user explicitly requests them.
- On conflict with a generic coding skill, prioritize [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) inside this repository.
- For local Codex work, keep the project boundary at `C:/Users/FUTIAN/Desktop/DeepPPT`; do not write outside this repository unless the user explicitly approves it.
- Treat `.env`, local browser/session files, credentials, and production deployment settings as sensitive; never print, modify, or move them unless the user explicitly asks.
- Do not run publish, deploy, destructive cleanup, commit, or push commands without explicit user approval.

## Command Quick Reference

Convenience summary only — full workflow in [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md).

```bash
# Source content conversion
python3 skills/ppt-master/scripts/source_to_md/pdf_to_md.py <PDF_file>
python3 skills/ppt-master/scripts/source_to_md/doc_to_md.py <DOCX_or_other_file>
python3 skills/ppt-master/scripts/source_to_md/excel_to_md.py <XLSX_or_XLSM_file>
python3 skills/ppt-master/scripts/source_to_md/ppt_to_md.py <PPTX_file>
python3 skills/ppt-master/scripts/source_to_md/web_to_md.py <URL>

# Project management
python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files_or_URLs...>
# Add --move only when intentionally relocating originals; add --copy to keep in-repo sources in place.
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>

# Unified read-only workflow dashboard — start/reuse after Step 2 project setup
python3 skills/ppt-master/scripts/dashboard/server.py <project_path> --daemon
# Add --no-browser only for headless/remote sessions or explicit no-window runs.

# Icon selection — copy chosen library icons into <project>/icons/ (missing names reported + non-zero = re-pick)
python3 skills/ppt-master/scripts/icon_sync.py search <query> [--library lib] [--limit N]
python3 skills/ppt-master/scripts/icon_sync.py <project_path> <lib/name> [<lib/name>...]

# Step 4 Eight Confirmations — interactive visual page (default auto-launch; chat fallback)
python3 skills/ppt-master/scripts/confirm_ui/server.py <project_path> --daemon --wait

# Image tools and SVG quality check
python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images
# In-pipeline AI image generation — manifest mode (required, even for 1 image):
python3 skills/ppt-master/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json
python3 skills/ppt-master/scripts/image_gen.py --render-md <project_path>/images/image_prompts.json
# Out-of-pipeline one-off / debug / single-image fixup only (no manifest, no sidecar):
python3 skills/ppt-master/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
python3 skills/ppt-master/scripts/svg_editor/server.py <project_path> --live
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
python3 skills/ppt-master/scripts/consulting_content_lock.py <project_path>  # optional, consulting/high-density sidecar
python3 skills/ppt-master/scripts/animation_config.py scaffold <project_path>  # optional, only for custom object-level animation
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>  # optional, before re-export

# Post-processing pipeline: run sequentially, one command at a time
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
python3 skills/ppt-master/scripts/e2e_validate.py <project_path> --pptx exports/<exported_file>.pptx
python3 skills/ppt-master/scripts/pptx_quality_check.py <project_path>/exports/<exported_file>.pptx --json-out <project_path>/quality/pptx_quality.json  # optional strict post-export structure QA
# Mergeable dy-stacked paragraph blocks collapse into one editable text frame by default; add --no-merge to keep every line as its own frame (strict line fidelity). See SKILL.md Step 7.3.
```

## Core Directories

- `skills/ppt-master/SKILL.md` — main workflow authority.
- `skills/ppt-master/references/` — role definitions and technical specifications.
- `skills/ppt-master/scripts/` — runnable tool scripts.
- `skills/ppt-master/scripts/docs/` — topic-focused script docs.
- `skills/ppt-master/templates/` — layout templates, chart templates, icon library, brand presets.
- `skills/ppt-master/workflows/` — standalone workflow files.
- `docs/` — user-facing documentation (FAQ, installation, technical design, templates guide, audio narration).
- `docs/rules/` — repo-wide style rules.
- `examples/` — example projects.
- `projects/` — user project workspace.
