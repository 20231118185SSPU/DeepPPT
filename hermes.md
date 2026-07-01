# DeepPPT — Hermes Agent Project Instructions
# Hermes Agent reads this file when operating in the DeepPPT repository.
# <!-- Format: Hermes Agent does not have a documented project-level config convention.
#      This file serves as a readable instruction set. Verify at https://hermes-agent.nousresearch.com/ -->

## Project

DeepPPT is an AI-driven presentation generation system. It converts source documents
(PDF/DOCX/URL/Markdown) into natively editable PPTX through SVG intermediate pages,
using multi-role collaboration (Strategist → Image_Generator → Executor).

## Workflow Authority

**Read `skills/ppt-master/SKILL.md` before any PPT generation task.** This is the
authoritative workflow. Steps are strictly serial — each step's output feeds the next.
Shared rules live in `docs/ai-rules-shared.md`; routing details live in `docs/routing.md`.

## Key Rules

1. ⛔ BLOCKING steps require explicit user confirmation. Never proceed on behalf of the user.
2. SVG pages are hand-written by the agent, one at a time. Script-generated batch SVGs are forbidden.
3. Before each SVG page, re-read `spec_lock.md` for colors/fonts/icons/images.
4. Never directly read/open image files (.jpg, .png). Use `analyze_images.py` output.
5. Topic-only request (no source file)? → Read `skills/ppt-master/workflows/deep-research.md` first. Do not replace it with ordinary WebSearch.
6. After Step 2, start or reuse the read-only Dashboard with `python3 skills/ppt-master/scripts/dashboard/server.py <project_path> --daemon --no-browser`; default port `8765`, log `<project_path>/dashboard/dashboard.log`, failure non-fatal.

## Routing Guardrails

- Existing PPTX: preserve page count/order/wording and beautify only → `beautify-pptx`; reuse original deck design with new content → `template-fill-pptx`; restructure story or change page count/order → main pipeline + `ppt_to_md`; harvest reusable template → `create-template`.
- Dashboard is observability only; it does not replace Confirm UI, Live Preview, quality gates, post-processing, or export.
- Animation: page transitions are default; per-element animations are off unless requested. Object-level animation tuning → `customize-animations`.
- Live preview starts automatically in Step 6; apply submitted annotations only after Step 7 through `live-preview`.
- Visual review: follow current `SKILL.md`; currently `visual-review` is recommended by default after quality gates and skipped only by explicit opt-out.

## Key Commands

```bash
# Create project
python3 skills/ppt-master/scripts/project_manager.py init <name> --format ppt169

# Dashboard observability after Step 2
python3 skills/ppt-master/scripts/dashboard/server.py <path> --daemon --no-browser

# Eight Confirmations (interactive UI)
python3 skills/ppt-master/scripts/confirm_ui/server.py <path> --daemon --wait

# AI image generation
python3 skills/ppt-master/scripts/image_gen.py --manifest <path>/images/image_prompts.json

# Web image search
python3 skills/ppt-master/scripts/image_search.py --batch <path>/images/image_queries.json

# SVG quality check
python3 skills/ppt-master/scripts/svg_quality_checker.py <path>

# Export to PPTX
python3 skills/ppt-master/scripts/svg_to_pptx.py <path>
```

## Configuration

1. Copy `.env.example` to `.env`
2. Set `IMAGE_BACKEND` (openai/gemini/qwen/zhipu/volcengine) and the corresponding API key
3. Optional image search keys: PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_ACCESS_KEY, FLICKR_API_KEY
