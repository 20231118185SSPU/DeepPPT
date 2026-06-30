# DeepPPT — Amazon Q Developer Rules

> Shared rules: see [`docs/ai-rules-shared.md`](../../docs/ai-rules-shared.md) for project overview, core pipeline, key rules, deep research, and configuration.

## Quick Reference

- Read `skills/ppt-master/SKILL.md` before any PPT task
- Steps are serial; ⛔ BLOCKING steps need user confirmation
- SVG pages: hand-written by agent, one at a time — no script-generated batch
- Re-read `spec_lock.md` before each SVG page — no values from memory
- Never read/open image files — use `analyze_images.py`
- Topic only? → `workflows/deep-research.md` first
- Config: `.env.example` → `.env`, set IMAGE_BACKEND + API key
