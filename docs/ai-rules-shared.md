# DeepPPT — Shared AI Agent Rules

> **Single source of truth** for rules common to all AI coding assistants (Cursor, Copilot, Amazon Q, Kiro, etc.). Tool-specific configs reference this file and add only their own extras.

## Project

DeepPPT is an AI-driven presentation generation system. Multi-role collaboration (Strategist → Image_Generator → Executor) converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX through SVG intermediate pages.

## Core Pipeline

Source Document → Create Project + Dashboard → [Template] → Strategist Eight Confirmations → [Image_Generator + Image-Text Linking] → Executor SVG → Quality Check → Post-processing → Export PPTX

## Workflow Authority

Read `skills/ppt-master/SKILL.md` before any PPT generation task or repository modification. It is the authoritative workflow. On conflict with generic coding rules, entry files, or summaries here, follow SKILL.md.

## Key Rules

1. **Serial execution** — Steps must be executed in order. Each step's output feeds the next.
2. **⛔ BLOCKING = hard stop** — Steps marked ⛔ BLOCKING require explicit user confirmation before proceeding.
3. **Hand-written SVG** — Every SVG page is written by the agent directly, one page at a time. Script-generated batch SVGs are forbidden.
4. **Re-read spec_lock.md** — Before generating each SVG page, re-read `spec_lock.md` for colors, fonts, icons, and images. No values from memory.
5. **No direct image reading** — Never read/open image files (.jpg, .png). Use `analyze_images.py` output.
6. **No generic scaffolding** — Do not create `.worktrees/`, `tests/`, or generic engineering structure by default.

## Deep Research

When the user asks to make a PPT with only a topic (no source files), first run `skills/ppt-master/workflows/deep-research.md`, then proceed with the main pipeline. Do not replace `deep-research` with ordinary built-in WebSearch; WebSearch is only a fallback inside the `deep-research` workflow.

## Dashboard Observability

After Step 2 creates the project directory and imports sources, start or reuse the unified read-only Dashboard:

```bash
python3 skills/ppt-master/scripts/dashboard/server.py <project_path> --daemon --no-browser
```

- Default port: `8765`; if occupied, the launcher advances to the next safe port.
- Log path: `<project_path>/dashboard/dashboard.log`.
- Report the actual Dashboard URL and log path to the user/developer.
- Launch failure is non-fatal. Print the warning and continue the PPT workflow.
- Dashboard is an observability surface for status, artifacts, quality reports, trace, and bridge states. It does not replace Confirm UI, Live Preview, quality gates, post-processing, or export.

## High-Risk Routing Summary

This is a memory aid for lightweight agent entry points. It does not replace `skills/ppt-master/SKILL.md` or `docs/routing.md`.

### Existing PPTX

Route by the role of the existing deck:

| User intent | Route |
|-------------|-------|
| Preserve page count, page order, and per-slide wording; only improve layout / hierarchy / whitespace | `skills/ppt-master/workflows/beautify-pptx.md` |
| Reuse the original deck's design and fill it with new content | `skills/ppt-master/workflows/template-fill-pptx.md` |
| Treat the PPTX as source material and freely restructure story, merge / split / drop / reorder pages, or change page count | Main pipeline with `skills/ppt-master/scripts/source_to_md/ppt_to_md.py` |
| Turn the PPTX into a reusable template package | `skills/ppt-master/workflows/create-template.md` |

If the request is ambiguous, ask whether page count/order and wording must be preserved. Preserve = `beautify-pptx`; restructure = main pipeline.

### Other Common Boundaries

- Topic-only with no source material: run `skills/ppt-master/workflows/deep-research.md` first; do not substitute ordinary WebSearch.
- Animation: page transitions are on by default; per-element entrance animations are off by default. Use `skills/ppt-master/workflows/customize-animations.md` only for object-level order / effect / timing requests.
- Live preview: Step 6 starts live preview automatically. Do not apply submitted annotations during generation; the annotation-application window opens after Step 7 via `skills/ppt-master/workflows/live-preview.md`.
- Visual review: follow the current `skills/ppt-master/SKILL.md` rule. As of this file, `visual-review` is recommended by default after quality gates and is skipped only by explicit opt-out.

## Configuration

1. Copy `.env.example` to `.env`
2. Set `IMAGE_BACKEND` (openai/gemini/qwen/zhipu/volcengine) and the corresponding API key
3. Optional: `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `UNSPLASH_ACCESS_KEY`, `FLICKR_API_KEY`
