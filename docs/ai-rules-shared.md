# DeepPPT — Shared AI Agent Rules

> **Single source of truth** for rules common to all AI coding assistants (Cursor, Copilot, Amazon Q, Kiro, etc.). Tool-specific configs reference this file and add only their own extras.

## Project

DeepPPT is an AI-driven presentation generation system. Multi-role collaboration (Strategist → Image_Generator → Executor) converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX through SVG intermediate pages.

## Core Pipeline

Source Document → Create Project → [Template] → Strategist Eight Confirmations → [Image_Generator + Image-Text Linking] → Executor SVG → Quality Check → Post-processing → Export PPTX

## Workflow Authority

Read `skills/ppt-master/SKILL.md` before any PPT generation task. It is the authoritative workflow. On conflict with generic coding rules, follow SKILL.md.

## Key Rules

1. **Serial execution** — Steps must be executed in order. Each step's output feeds the next.
2. **⛔ BLOCKING = hard stop** — Steps marked ⛔ BLOCKING require explicit user confirmation before proceeding.
3. **Hand-written SVG** — Every SVG page is written by the agent directly, one page at a time. Script-generated batch SVGs are forbidden.
4. **Re-read spec_lock.md** — Before generating each SVG page, re-read `spec_lock.md` for colors, fonts, icons, and images. No values from memory.
5. **No direct image reading** — Never read/open image files (.jpg, .png). Use `analyze_images.py` output.
6. **No generic scaffolding** — Do not create `.worktrees/`, `tests/`, or generic engineering structure by default.

## Deep Research

When the user asks to make a PPT with only a topic (no source files), first run `skills/ppt-master/workflows/deep-research.md`, then proceed with the main pipeline.

## Configuration

1. Copy `.env.example` to `.env`
2. Set `IMAGE_BACKEND` (openai/gemini/qwen/zhipu/volcengine) and the corresponding API key
3. Optional: `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `UNSPLASH_ACCESS_KEY`, `FLICKR_API_KEY`
