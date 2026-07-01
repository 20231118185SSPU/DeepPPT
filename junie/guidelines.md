# DeepPPT — JetBrains Junie Guidelines

## Project

DeepPPT is an AI-driven presentation generation system that converts source documents into
natively editable PPTX through SVG intermediate pages, using multi-role collaboration
(Strategist → Image_Generator → Executor).

## Workflow Authority

Read `skills/ppt-master/SKILL.md` before any PPT generation task or repository modification.
It is the authoritative workflow document.
Shared rules live in `docs/ai-rules-shared.md`; routing details live in `docs/routing.md`.

## Core Rules

1. **Serial execution**: Steps must be executed in order. Steps marked ⛔ BLOCKING require
   explicit user confirmation before proceeding.
2. **Hand-written SVG**: Every SVG page is written by the agent directly, one page at a time.
   Script-generated batch SVGs are forbidden.
3. **Spec re-read**: Before generating each SVG page, re-read `spec_lock.md` for colors, fonts,
   icons, and images. Never use values from memory.
4. **Image handling**: Never read/open image files (.jpg, .png). Use `analyze_images.py` output.
5. **Language**: Match the user's input language. Design spec follows English template structure.
6. **Dashboard**: After Step 2, start or reuse `python3 skills/ppt-master/scripts/dashboard/server.py <project_path> --daemon --no-browser`. Default port is `8765`; logs are at `<project_path>/dashboard/dashboard.log`; failure is non-fatal.

## Key Scripts

- `python3 skills/ppt-master/scripts/project_manager.py init <name> --format ppt169`
- `python3 skills/ppt-master/scripts/dashboard/server.py <path> --daemon --no-browser`
- `python3 skills/ppt-master/scripts/confirm_ui/server.py <path> --daemon --wait`
- `python3 skills/ppt-master/scripts/image_gen.py --manifest <path>/images/image_prompts.json`
- `python3 skills/ppt-master/scripts/svg_quality_checker.py <path>`
- `python3 skills/ppt-master/scripts/svg_to_pptx.py <path>`

## Deep Research

When the user asks to "做PPT" with only a topic (no source files), first run
`skills/ppt-master/workflows/deep-research.md`, then proceed with the main pipeline. Do not
replace it with ordinary WebSearch.

## Routing Guardrails

- Existing PPTX: preserve page count/order/wording and beautify only → `beautify-pptx`; reuse
  original deck design with new content → `template-fill-pptx`; restructure story or change
  page count/order → main pipeline + `ppt_to_md`; harvest reusable template → `create-template`.
- Dashboard is read-only observability; it does not replace Confirm UI, Live Preview, quality
  gates, post-processing, or export.
- Animation: page transitions are default; per-element animations are off unless requested.
  Object-level animation tuning → `customize-animations`.
- Live preview starts automatically in Step 6; apply submitted annotations only after Step 7
  through `live-preview`.
- Visual review: follow current `SKILL.md`; currently `visual-review` is recommended by default
  after quality gates and skipped only by explicit opt-out.

## Configuration

1. Copy `.env.example` to `.env`
2. Set `IMAGE_BACKEND` (openai/gemini/qwen/zhipu/volcengine) and corresponding API key
3. Optional: PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_ACCESS_KEY, FLICKR_API_KEY
