# DeepPPT — JetBrains Junie Guidelines

## Project

DeepPPT is an AI-driven presentation generation system that converts source documents into
natively editable PPTX through SVG intermediate pages, using multi-role collaboration
(Strategist → Image_Generator → Executor).

## Workflow Authority

Read `skills/ppt-master/SKILL.md` before any PPT generation task or repository modification.
It is the authoritative workflow document.

## Core Rules

1. **Serial execution**: Steps must be executed in order. Steps marked ⛔ BLOCKING require
   explicit user confirmation before proceeding.
2. **Hand-written SVG**: Every SVG page is written by the agent directly, one page at a time.
   Script-generated batch SVGs are forbidden.
3. **Spec re-read**: Before generating each SVG page, re-read `spec_lock.md` for colors, fonts,
   icons, and images. Never use values from memory.
4. **Image handling**: Never read/open image files (.jpg, .png). Use `analyze_images.py` output.
5. **Language**: Match the user's input language. Design spec follows English template structure.

## Key Scripts

- `python3 skills/ppt-master/scripts/project_manager.py init <name> --format ppt169`
- `python3 skills/ppt-master/scripts/confirm_ui/server.py <path> --daemon --wait`
- `python3 skills/ppt-master/scripts/image_gen.py --manifest <path>/images/image_prompts.json`
- `python3 skills/ppt-master/scripts/svg_quality_checker.py <path>`
- `python3 skills/ppt-master/scripts/svg_to_pptx.py <path>`

## Deep Research

When the user asks to "做PPT" with only a topic (no source files), first run
`skills/ppt-master/workflows/deep-research.md`, then proceed with the main pipeline.

## Configuration

1. Copy `.env.example` to `.env`
2. Set `IMAGE_BACKEND` (openai/gemini/qwen/zhipu/volcengine) and corresponding API key
3. Optional: PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_ACCESS_KEY, FLICKR_API_KEY
