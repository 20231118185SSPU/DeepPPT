# DeepPPT — GitHub Copilot Instructions
# https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot

## Project Overview

DeepPPT is an AI-driven presentation generation system. Multi-role collaboration (Strategist → Image_Generator → Executor) converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML) through SVG intermediate pages.

## Core Pipeline

Source Document → Create Project → [Template] → Strategist Eight Confirmations → [Image_Generator + Image-Text Linking] → Executor Live Preview → Quality Check → Post-processing → Export PPTX

## Key Workflow Rules

1. **Read SKILL.md first**: `skills/ppt-master/SKILL.md` is the authoritative workflow for any PPT generation task.
2. **Serial execution**: Steps must be executed in order. Steps marked ⛔ BLOCKING require explicit user confirmation.
3. **Hand-written SVG**: Every SVG page is written by the agent directly, one page at a time. Script-generated batch SVGs are forbidden.
4. **Re-read spec_lock.md**: Before generating each SVG page, re-read `spec_lock.md` for colors, fonts, icons, and images.
5. **No direct image reading**: Never read/open image files (.jpg, .png). Use `analyze_images.py` output.

## Key Scripts

- `python3 skills/ppt-master/scripts/project_manager.py init <name> --format ppt169` — Create project
- `python3 skills/ppt-master/scripts/confirm_ui/server.py <path> --daemon --wait` — Eight Confirmations
- `python3 skills/ppt-master/scripts/image_gen.py --manifest <path>/images/image_prompts.json` — AI images
- `python3 skills/ppt-master/scripts/svg_quality_checker.py <path>` — Quality check
- `python3 skills/ppt-master/scripts/svg_to_pptx.py <path>` — Export

## Deep Research

When user asks to "做PPT" with only a topic (no source files), first run `skills/ppt-master/workflows/deep-research.md`, then proceed with the main pipeline.

## Configuration

1. Copy `.env.example` to `.env`
2. Set `IMAGE_BACKEND` and the corresponding API key
3. Optional: `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `UNSPLASH_ACCESS_KEY`, `FLICKR_API_KEY`
