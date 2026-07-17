# CLAUDE.md

**You MUST read [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) before any PPT generation task or repo modification.** SKILL.md is the authoritative workflow. This file is the project charter — it defines identity, routing, and constraints. For operational details (commands, setup, artifact structure, architecture), read [`docs/claude-reference.md`](docs/claude-reference.md).

## Project Identity

PPT Master is an AI-driven presentation generation system. Multi-role collaboration (Strategist → Image_Generator → Executor) converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML).

**Core Pipeline**: `Source → Project + Dashboard → [Template] → [Content Selection] → [Outline] → Eight Confirmations → [Images] → SVG Render → Quality Check → Post-process → Export`

**Detailed routing table**: [`docs/routing.md`](docs/routing.md) — loaded on demand.

**Dashboard observability**: after Step 2 creates/imports the project, start or reuse the read-only Dashboard with `python3 skills/ppt-master/scripts/dashboard/server.py <project_path> --daemon`. Default local behavior may open the browser; add `--no-browser` only for headless/remote sessions or when the user explicitly requests no browser window. Default port is `8765`; logs are at `<project_path>/dashboard/dashboard.log`. Report the actual URL/log path. Launch failure is non-fatal, and Dashboard never replaces Confirm UI, Live Preview, quality gates, post-processing, or export.

## Constraints

- This repository is a workflow/skill package, not an app scaffold.
- Do NOT assume generic-project conventions (`.worktrees/`, `tests/`, mandatory branches) unless explicitly requested.
- On conflict with a generic coding skill, prioritize SKILL.md inside this repository.
- Markdown language consistency: follow the directory primary-language modes in [`docs/rules/documentation-style.md`](docs/rules/documentation-style.md#3-language-placement). Workflows may use English structural scaffolding with Chinese explanatory body text; references are primarily English; `docs/` follows its subdirectory declarations. A single file should not switch primary language casually.
- Repo-wide style rules: follow matching rule in [`docs/rules/`](docs/rules/) when editing any code or prose in this repo.
- Code safety: Before modifying any file under `skills/ppt-master/scripts/` or `skills/ppt-master/workflows/`, run `python skills/ppt-master/scripts/smoke_check.py --skip-help` to establish baseline. After modification, run validation matched to the change type: at minimum `python skills/ppt-master/scripts/smoke_check.py --skip-help`; when a usable project artifact exists, run `python skills/ppt-master/scripts/harness_gate.py <project_path> --quick` or `python skills/ppt-master/scripts/e2e_validate.py <project_path> --pptx <pptx_path>`. Do not pass `--quick` to `e2e_validate.py`; it does not support that flag. Log all changes in [`docs/change-log.md`](docs/change-log.md). Modifications to SKILL.md itself require `[NEEDS_HUMAN_REVIEW]` annotation.

## Quick Links

| Resource | Purpose |
|----------|---------|
| [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) | Main workflow authority |
| [`docs/claude-reference.md`](docs/claude-reference.md) | Full operational reference (commands, setup, architecture) |
| [`skills/ppt-master/references/`](skills/ppt-master/references/) | Role definitions and technical specifications |
| [`skills/ppt-master/scripts/`](skills/ppt-master/scripts/) | Runnable tool scripts |
| [`skills/ppt-master/templates/`](skills/ppt-master/templates/) | Layout templates, charts, icons, brands |
| [`skills/ppt-master/workflows/`](skills/ppt-master/workflows/) | Standalone workflow files |
| [`docs/`](docs/) | User-facing documentation |
| [`projects/`](projects/) | User project workspace |
| [`docs/routing.md`](docs/routing.md) | Complete workflow routing table |
| [`docs/change-log.md`](docs/change-log.md) | Script/workflow modification audit trail |

<!-- align-protocol:begin v3.0 -->
## 对齐协议（Alignment Protocol）
每条开发指令执行前，静默完成三档路由评估：
1. 读取 .align/lessons.md → .align/spec.md → .align/context.md
2. 五维快评：简单且明确 → 直接执行（但交付前必须自验证）
3. 有缺口但项目上下文可补全 → 开头 ≤3 行披露对齐假设，然后直接执行
4. 高风险（见 .align/spec.md 高风险清单）或总分<6 或假设>2 条
   → 停下澄清，一次只问一个问题并给推荐答案
5. 任务结束：有踩坑/纠正/新约定 → 追加到 .align/lessons.md
硬性红线：高风险静默假设 = 无效输出；交付前不验证 = 无效输出。
<!-- align-protocol:end -->
