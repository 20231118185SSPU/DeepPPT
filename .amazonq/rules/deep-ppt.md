# DeepPPT — Amazon Q Developer Rules

## Project

DeepPPT: AI-driven presentation generation. Strategist → Image_Generator → Executor → PPTX.

## Workflow

Read `skills/ppt-master/SKILL.md` before any PPT task. Steps are serial, ⛔ BLOCKING steps need user confirmation.

## Key Rules

- SVG pages: hand-written by agent, one at a time. No script-generated batch.
- Re-read `spec_lock.md` before each SVG page. No values from memory.
- Never read/open image files. Use `analyze_images.py`.
- Topic only? → `workflows/deep-research.md` first.

## Config

`.env.example` → `.env`. Set IMAGE_BACKEND + API key.
