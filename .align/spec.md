# .align/spec.md — 项目开发规范

> 由 `align-init` skill 扫描生成。每条标注置信度：`[原文]` / `[推断]` / `[假设]`。
> 修订记录：2026-08-03 人工按 `docs/reviews/deep-ppt-repository-inventory-2026-08.md` §5 刷新过期事实（CI 存在性、测试语义、Python 版本、smoke 基线）；下次 align-init 重新扫描时可覆盖。

---

## 技术栈与版本

- 语言：Python 3.x `[原文]`（本机实测 3.12.13，uv 托管 cpython-3.12-windows-x86_64）`[原文]`（2026-08-03 实测）
- 运行时：Python 3（python.org 发行版；Windows 上 `python3` 可能不可用，需用 `python` 替代）`[原文]`
- 包管理：pip（`requirements.txt`）`[原文]`
- 核心依赖：python-pptx ≥0.6.21、Pillow ≥9.0.0、PyMuPDF ≥1.23.0、flask ≥3.0.0、google-genai ≥1.0.0、edge-tts ≥7.2.8 `[原文]`
- SVG 处理：CairoSVG（推荐）或 svglib + reportlab `[原文]`

---

## 目录约定

- `skills/ppt-master/scripts/`：可运行的工具脚本（CLI 入口），非 Python 包 `[原文]`
- `skills/ppt-master/references/`：角色定义和技术规范（英文为主）`[原文]`
- `skills/ppt-master/templates/`：布局模板、图表模板、图标库、品牌预设 `[原文]`
- `skills/ppt-master/workflows/`：独立工作流文件（英文骨架 + 中文解释）`[原文]`
- `docs/`：用户文档（根目录英文为主）`[原文]`
- `docs/rules/`：仓库级风格规则 `[原文]`
- `projects/`：用户 PPT 项目工作区，非通用临时目录 `[原文]`
- 临时文件使用 `.tmp/` 或 `.codex-tmp/`，或 `projects/_smoke_*` / `_tmp_*` / `_agent_*` 前缀 `[原文]`

---

## 分支与提交规范

- 提交风格：混合（部分 conventional commits `feat:/fix:/docs:/chore:`，部分纯描述性）`[推断]`
- 推荐：采用 Conventional Commits 格式 `type(scope): description` `[假设]`
- 有 CI 流水线：`.github/workflows/ci.yml`（smoke + svg-quality + e2e 三 job，main 推送/PR 触发）+ `deploy-pages.yml`（GitHub Pages）`[原文]`（2026-08-03 修订，原「无 CI 流水线」过期）

---

## 测试与验证命令

- 无 `tests/` 目录、无 `test_*.py`；自动化验证 = `smoke_check.py`（81 个入口脚本 import + `--help` + 集成测试），由 CI 自动运行 `[原文]`（2026-08-03 修订，原「无自动化测试」语义过窄）
- 脚本冒烟检查：`python skills/ppt-master/scripts/smoke_check.py --skip-help` `[原文]`；当前基线 78 passed / 0 failed / 3 skipped / 81 checks（完整模式 158/0/4 / 162 checks）`[原文]`（2026-08-03 实测）
- 聚合质量门：`python skills/ppt-master/scripts/harness_gate.py <project_path> --quick` `[原文]`
- 端到端验证：`python skills/ppt-master/scripts/e2e_validate.py <project_path> --pptx <pptx_path>` `[原文]`
- 代码修改前必须先跑 smoke_check 建立基线，修改后再次验证 `[原文]`

---

## 代码风格

- 缩进：4 空格，无 tab `[原文]`
- 行宽：软限 100，硬限 120 `[原文]`
- 编码：UTF-8，LF 换行，无 BOM `[原文]`
- 命名：模块 `snake_case.py`，函数 `snake_case`，常量 `UPPER_SNAKE_CASE`，类 `PascalCase` `[原文]`
- CLI 入口：`main(argv=None) -> int`，`raise SystemExit(main())` `[原文]`
- sys.path 注入：仅在入口脚本中，使用 `Path(__file__).resolve().parent` `[原文]`
- 类型提示：所有新公共函数必须有类型提示 `[原文]`
- 禁止 bare `except:`，必须命名异常类 `[原文]`
- 依赖分层：标准库 > requests/Pillow/lxml > Provider SDK（懒导入+软失败）`[原文]`

---

## 评审与合并规则

- 无 PR 流程（个人项目）`[推断]`
- 变更记录：所有脚本/工作流修改记录到 `docs/change-log.md` `[原文]`
- SKILL.md 修改需要 `[NEEDS_HUMAN_REVIEW]` 标注 `[原文]`

---

## 高风险操作清单

- PPTX 导出：不可逆输出，导出前必须通过质量门 `[原文]`
- AI 图片生成：消耗 API 额度，生成前确认 manifest 正确 `[推断]`
- 项目目录删除：仅允许删除 `_smoke_*` / `_tmp_*` / `_agent_*` 前缀目录 `[原文]`
- Dashboard / Confirm UI 服务管理：启动前确认端口，结束前必须关闭 `[原文]`
- spec_lock.md 修改：必须重新生成 digest `[原文]`
- 修改 `skills/ppt-master/SKILL.md`：需要 `[NEEDS_HUMAN_REVIEW]` 标注 `[原文]`
- 修改 `skills/ppt-master/scripts/` 或 `workflows/`：修改前后必须跑 smoke_check `[原文]`
