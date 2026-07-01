# DeepPPT — Kiro Steering Rules

> Shared rules: see [`docs/ai-rules-shared.md`](../../docs/ai-rules-shared.md) and [`docs/routing.md`](../../docs/routing.md). Always read [`skills/ppt-master/SKILL.md`](../../skills/ppt-master/SKILL.md) before any PPT generation task or repository modification.

## Quick Reference

1. Serial pipeline. ⛔ BLOCKING = hard stop for user confirmation.
2. SVG pages hand-written one at a time. No batch scripts.
3. Re-read `spec_lock.md` per page. No memory-based values.
4. Use `analyze_images.py` for image info. Never open image files directly.
5. Topic-only → run `workflows/deep-research.md` first; do not replace it with ordinary WebSearch.
6. Dashboard after Step 2 → run/reuse `python3 skills/ppt-master/scripts/dashboard/server.py <project_path> --daemon --no-browser`; default port `8765`, log `<project_path>/dashboard/dashboard.log`, failure non-fatal.

## Routing Guardrails

- Existing PPTX: preserve page count/order/wording and beautify only → `beautify-pptx`; reuse original deck design with new content → `template-fill-pptx`; restructure story or change page count/order → main pipeline + `ppt_to_md`; harvest reusable template → `create-template`.
- Dashboard is read-only observability; it does not replace Confirm UI, Live Preview, quality gates, post-processing, or export.
- Animation: page transitions are default; per-element animations are off unless requested. Object-level animation tuning → `customize-animations`.
- Live preview starts automatically in Step 6; apply submitted annotations only after Step 7 through `live-preview`.
- Visual review: follow current `SKILL.md`; currently `visual-review` is recommended by default after quality gates and skipped only by explicit opt-out.
