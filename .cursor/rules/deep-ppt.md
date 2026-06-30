# DeepPPT — Cursor Rules
# https://docs.cursor.com/context/rules-for-ai

> Shared rules: see [`docs/ai-rules-shared.md`](../../docs/ai-rules-shared.md) for project overview, core pipeline, key rules, deep research, and configuration.

## Key Scripts

| Script | Purpose |
|--------|---------|
| `skills/ppt-master/scripts/project_manager.py init <name> --format ppt169` | Create project |
| `skills/ppt-master/scripts/confirm_ui/server.py <path> --daemon --wait` | Eight Confirmations UI |
| `skills/ppt-master/scripts/image_gen.py --manifest <path>/images/image_prompts.json` | AI image generation |
| `skills/ppt-master/scripts/image_search.py --batch <path>/images/image_queries.json` | Web image search |
| `skills/ppt-master/scripts/svg_quality_checker.py <path>` | Quality check |
| `skills/ppt-master/scripts/svg_to_pptx.py <path>` | Export PPTX |

## Do NOT

- Skip ⛔ BLOCKING steps
- Generate SVG via scripts — pages must be hand-written one at a time
- Bundle cross-phase steps together
- Create `.worktrees/`, `tests/`, or generic engineering scaffolding
