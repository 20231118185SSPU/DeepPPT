# DeepPPT — Kiro Steering Rules

> Shared rules: see [`docs/ai-rules-shared.md`](../../docs/ai-rules-shared.md) for project overview, core pipeline, key rules, deep research, and configuration.

## Quick Reference

1. Serial pipeline. ⛔ BLOCKING = hard stop for user confirmation.
2. SVG pages hand-written one at a time. No batch scripts.
3. Re-read `spec_lock.md` per page. No memory-based values.
4. Use `analyze_images.py` for image info. Never open image files directly.
5. Topic-only → run `workflows/deep-research.md` first.
