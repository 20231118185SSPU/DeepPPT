# DeepPPT — Amazon Q Developer Rules

> Shared rules: see [`docs/ai-rules-shared.md`](../../docs/ai-rules-shared.md) and [`docs/routing.md`](../../docs/routing.md). Always read [`skills/ppt-master/SKILL.md`](../../skills/ppt-master/SKILL.md) before any PPT generation task or repository modification.

## Quick Reference

- Read `skills/ppt-master/SKILL.md` before any PPT task
- Steps are serial; ⛔ BLOCKING steps need user confirmation
- SVG pages: hand-written by agent, one at a time — no script-generated batch
- Re-read `spec_lock.md` before each SVG page — no values from memory
- Never read/open image files — use `analyze_images.py`
- Dashboard: after Step 2, start/reuse `python3 skills/ppt-master/scripts/dashboard/server.py <project_path> --daemon --no-browser`; default port `8765`, log `<project_path>/dashboard/dashboard.log`, failure is non-fatal, read-only only and not a replacement for Confirm UI / Live Preview / quality gates / export
- Existing PPTX: preserve page count/order/wording and beautify only → `beautify-pptx`; reuse original deck design with new content → `template-fill-pptx`; restructure story or change page count/order → main pipeline + `ppt_to_md`; harvest reusable template → `create-template`
- Topic only? → `workflows/deep-research.md` first; do not replace it with ordinary WebSearch
- Animation: page transitions are default; per-element animations are off unless requested. Object-level tuning → `customize-animations`
- Live preview starts automatically in Step 6; apply submitted annotations only after Step 7 through `live-preview`
- Visual review: follow current `SKILL.md`; currently `visual-review` is recommended by default after quality gates and skipped only by explicit opt-out
- Config: `.env.example` → `.env`, set IMAGE_BACKEND + API key
