# DeepPPT — AI Agent Platform Configuration
# https://docs.cursor.com/context/rules-for-ai
# Format: Markdown rules file, ≤80 lines

## Project

DeepPPT is an AI-driven presentation generation system. Multi-role collaboration (Strategist → Image_Generator → Executor) converts source documents into natively editable PPTX through SVG intermediate pages.

## Core Pipeline

Source → Create Project → [Template] → Strategist Eight Confirmations → [Image_Generator + Image-Text Linking] → Executor SVG → Quality Check → Post-processing → Export PPTX

## Key Rules

- Steps are strictly serial. Each step's output feeds the next.
- Steps marked ⛔ BLOCKING require explicit user confirmation before proceeding.
- SVG pages are hand-written by the agent, never script-generated.
- Before generating each SVG page, re-read `spec_lock.md` for colors/fonts/icons/images.
- Never directly read/open image files (.jpg, .png). Use `analyze_images.py` output.
- Match the user's input language for responses.

## Key Scripts

| Script | Purpose |
|--------|---------|
| `skills/ppt-master/scripts/project_manager.py init <name> --format ppt169` | Create project |
| `skills/ppt-master/scripts/confirm_ui/server.py <path> --daemon --wait` | Eight Confirmations UI |
| `skills/ppt-master/scripts/image_gen.py --manifest <path>/images/image_prompts.json` | AI image generation |
| `skills/ppt-master/scripts/image_search.py --batch <path>/images/image_queries.json` | Web image search |
| `skills/ppt-master/scripts/svg_quality_checker.py <path>` | Quality check |
| `skills/ppt-master/scripts/svg_to_pptx.py <path>` | Export PPTX |

## Configuration

1. Copy `.env.example` to `.env`
2. Set `IMAGE_BACKEND` (openai/gemini/qwen/zhipu/volcengine)
3. Set the corresponding API key
4. Optional: PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_ACCESS_KEY, FLICKR_API_KEY

## For Deep Research

When the user says "做PPT" with only a topic (no source files), read `skills/ppt-master/workflows/deep-research.md` first, then proceed with the main pipeline.

## Do NOT

- Create `.worktrees/`, `tests/`, or generic engineering scaffolding
- Skip ⛔ BLOCKING steps
- Generate SVG via scripts — pages must be hand-written one at a time
- Bundle cross-phase steps together
