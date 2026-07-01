# DeepPPT — GitHub Copilot Instructions
# https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot

> Shared rules: see [`docs/ai-rules-shared.md`](docs/ai-rules-shared.md) and [`docs/routing.md`](docs/routing.md). Always read [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) before any PPT generation task or repository modification.

## Routing Guardrails

- Existing PPTX: preserve page count/order/wording and beautify only → `beautify-pptx`; reuse original deck design with new content → `template-fill-pptx`; restructure story or change page count/order → main pipeline + `ppt_to_md`; harvest reusable template → `create-template`.
- Dashboard: after Step 2, start/reuse `python3 skills/ppt-master/scripts/dashboard/server.py <project_path> --daemon --no-browser`; default port `8765`, log `<project_path>/dashboard/dashboard.log`, failure non-fatal, read-only only and not a replacement for Confirm UI / Live Preview / quality gates / export.
- Topic-only with no source → `deep-research`; do not replace it with ordinary WebSearch.
- Animation: page transitions are default; per-element animations are off unless requested. Object-level animation tuning → `customize-animations`.
- Live preview starts automatically in Step 6; apply submitted annotations only after Step 7 through `live-preview`.
- Visual review: follow current `SKILL.md`; currently `visual-review` is recommended by default after quality gates and skipped only by explicit opt-out.

## Key Scripts

- `python3 skills/ppt-master/scripts/project_manager.py init <name> --format ppt169` — Create project
- `python3 skills/ppt-master/scripts/dashboard/server.py <path> --daemon --no-browser` — Dashboard after Step 2
- `python3 skills/ppt-master/scripts/confirm_ui/server.py <path> --daemon --wait` — Eight Confirmations
- `python3 skills/ppt-master/scripts/image_gen.py --manifest <path>/images/image_prompts.json` — AI images
- `python3 skills/ppt-master/scripts/svg_quality_checker.py <path>` — Quality check
- `python3 skills/ppt-master/scripts/svg_to_pptx.py <path>` — Export
