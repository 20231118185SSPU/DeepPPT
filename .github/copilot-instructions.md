# DeepPPT — GitHub Copilot Instructions
# https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot

> Shared rules: see [`docs/ai-rules-shared.md`](docs/ai-rules-shared.md) for project overview, core pipeline, key rules, deep research, and configuration.

## Key Scripts

- `python3 skills/ppt-master/scripts/project_manager.py init <name> --format ppt169` — Create project
- `python3 skills/ppt-master/scripts/confirm_ui/server.py <path> --daemon --wait` — Eight Confirmations
- `python3 skills/ppt-master/scripts/image_gen.py --manifest <path>/images/image_prompts.json` — AI images
- `python3 skills/ppt-master/scripts/svg_quality_checker.py <path>` — Quality check
- `python3 skills/ppt-master/scripts/svg_to_pptx.py <path>` — Export
