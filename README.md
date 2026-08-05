# DeepPPT - Research-Driven, Native-Editable AI Presentations

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/20231118185SSPU/DeepPPT/actions/workflows/ci.yml/badge.svg)](https://github.com/20231118185SSPU/DeepPPT/actions/workflows/ci.yml)

> An extension of [ppt-master](https://github.com/hugohe3/ppt-master) with briefing-led deep research, evidence-backed planning, deterministic chart recall, intent-first page composition, contract-aware observability, and production quality gates.

[English](#overview) | [中文](#简介)

## Overview

DeepPPT turns a topic or source document into a natively editable PPTX. It coordinates research, narrative and visual planning, asset acquisition, SVG authoring, validation, and export while preserving explicit machine contracts across resumable workflows.

**Capabilities at a glance:**

- **End-to-end generation pipeline** — topic-only input goes through an explicit PPT Briefing confirmation, then a 7-step deep-research orchestrator (multi-AI browser automation), Eight Confirmations, a sealed `page_expression.json` contract, deterministic chart recall, dual-track image acquisition, hand-written SVG pages, quality gates, and export. Optional `quick-generate` fast lane and 1:1 `beautify` re-layout.
- **Native Office capability layer** — OfficeCLI v1.0.143 as a pinned, SHA-256-locked local runtime: native PPTX revision (read-only inspect → browser element selection → confirmed atomic plan → temp-copy apply with full rollback → PowerPoint COM final render → SVG-divergence recording), Office source enrichment (`office_sources.json` on import), and opt-in copy-only DOCX/XLSX repair. User originals are never modified.
- **Quality gates & observability** — staged confirm/research/asset/visual/harness/e2e gates plus the refactored `svg_quality` diagnostic pack; PowerPoint COM real render as the final layout truth with an advisory glyph-box audit; unified Dashboard artifact showcase; versioned trace envelope + `run_summary` metrics.
- **Engineering governance & cross-platform** — 13 mainstream AI agent platforms work out of the box, synthetic non-sensitive regression fixtures with smoke integration contracts (291 checks), three green CI jobs (Linux runner installs the pinned OfficeCLI binary), single-source-of-truth project accessors, read-only interruption diagnostics, and prompt-corpus governance.

## 简介

DeepPPT 是一个端到端的 AI PPT 生成系统。给定一个主题或源文件，它会自动完成深度调研、结构化分析、叙事构建、视觉身份提取、资源获取、SVG 页面生成、质量门禁和 PPTX 导出，最终产出一份**原生可编辑的 PPTX**。

当输入只有一个主题时，DeepPPT 会先生成可确认的 `ppt_brief.md` / `ppt_brief.json`，明确目标、受众、叙事、素材策略和验收标准；用户确认后才进入深度调研，避免在方向未锁定时直接搜索和生成。

> 完整变更记录见 [docs/change-log.md](docs/change-log.md)；最近成果见文末[更新日志](#更新日志)。

### 核心能力

#### 1. 端到端生成管线

- **主题直达**：仅给主题时先走 `ppt-briefing` 前置构思并等待确认，再进入 7 步独立深度调研（大纲 → 搜索拆分 → 多 AI 逐页搜索 → 汇总 → 分析 → 叙事 → 视觉策略），支持 Agent-Reach / 平台 / 浏览器自动化三条搜索路径
- **机器合同贯穿**：`page_expression.json` 逐页锁定主张、证据、视觉动作、结论与叙事衔接，与 `spec_lock.md` 一同封存，在连续生成 / 分段交接 / 恢复执行 / 规格精修全路径上防漂移
- **确定性图表选型**：基于 3-8 个内容形态标签从实时目录召回候选，低置信度才开放语义 fallback，入锁前校验精确键
- **图片来源路由 + 双轨生成**：按人物 / 产品 / 学术 / 历史 / 近期事件 / 通用氛围选择来源包，视觉页 AI 生图 + 信息页网络素材，15+ 图片后端
- **SVG 逐页手写生成**：Executor 按内容关系、信息锚点、视觉动作构图，配合实时预览；页面类型 11 种（含讲解页、对比页、数据页、时间线页）
- **快速通道**：`quick-generate` 直通 profile（显式快速意图 → 手写 SVG → lockless 检查 → 导出）；`beautify-pptx` 1:1 重排版（内容逐字保留、源版式为准）
- **咨询证据链（可选）**：证据表、2-3 条 SCR 备选、每页 evidence IDs / caveats / SO WHAT / content density

#### 2. 原生 Office 能力（OfficeCLI v1.0.143 固定运行时）

- **固定运行时与零 shell 桥接**：SHA-256 校验安装到 gitignored `.tools/officecli/`，8 平台 lock manifest，typed bridge + 14 个稳定错误码，原子 batch，无 PATH fallback / MCP / SDK / 自动升级
- **原生 PPTX 修订子工作流**：只读 inspect（对象树 / 格式 / 问题 / 稳定 `@id=` 路径）→ 浏览器 watch 选择对象 → 确认 plan（V1 allowlist：set/add/remove/move/swap）→ 临时副本原子 apply → 7 门禁 postflight（baseline-delta validate、slide roster、未寻址 parts 保护、COM render、SVG divergence 记录），任一失败整批回滚、不发布产物
- **Office 源文件结构增强**：`import-sources` 自动生成 `analysis/office_sources.json`（DOCX/PPTX/XLSX 格式感知计数、问题报告、converter 映射），检查前后源 SHA-256 不变
- **副本式 DOCX/XLSX 修复（opt-in）**：原件永不为 mutation target，修复副本发布到 `sources/repaired/` 并重跑原 converter 产出新 Markdown（不覆盖旧）
- **原生增强**：追加式补丁已完成 PPTX（备注 / 音频 / 时序 / 转场，不重建幻灯片）；PowerPoint COM 编码 MP4 视频导出
- **权威边界**：四条顶层路由（Generate / Create Template / Fill Native PPTX / Enhance Native PPTX）不变，上述能力均为共享子工作流；SVG 生成与 Markdown converters 仍是生成权威

#### 3. 质量门禁与可观测性

- **多阶段门禁**：confirm / research depth / asset completeness / rendered visual / harness / e2e，外加重构版 `svg_quality` 诊断包（真实文字度量硬错误、transform 感知溢出契约、21 类 SVG→DrawingML 语法契约）
- **PowerPoint 真实渲染终裁**：`pptx_render_export.py` 经 COM `Slide.Export` 逐页出图作为版式最终依据；`svg_geometry_audit.py` 字形盒级审计为 advisory 首道防线；浏览器预览不冒充最终视觉通过
- **Dashboard 产物展台**：按「制作思路 → 设计契约 → 生成页面 → 导出成品」四阶段浏览项目全过程产物，本地 `artifacts_index.json` 可搜找，`/api/state` 展示 OfficeCLI runtime / sources / revision 状态与 SVG divergence
- **运行指标闭环**：trace 版本化信封 + `run_summary.py` 聚合（null≠0 语义、敏感字段 fail-closed）；`pptx_quality_check.py` 导出后 PPTX 结构 QA
- **prompt 语料治理**：`prompt_audit.py` 按路由 load-set 审计 173 文档 token 预算（Generate 路由典型加载 −21.4%，coverage 闭合）

#### 4. 工程治理与跨平台协同

- **13 个主流 AI Agent 平台克隆即用**：Claude Code / Cursor / Windsurf / GitHub Copilot / OpenAI Codex / Pi / Cline / Roo Code / Aider / Amazon Q / Kiro / Junie / Hermes Agent
- **回归与 CI**：合成非敏感 fixture（template-fill / enhance / structured / partial 15 态 / DOCX+PPTX 保真 / trace 校准 / space / beautify 1:1 / officecli，附 rebuild 脚本）驱动 smoke integration Tests 10-17（291 checks）；CI 三 job 全绿，Linux runner 自动安装 pinned OfficeCLI 并校验校验和
- **单一事实源**：`project_utils` 规范 accessors + `derive_pipeline_state`；`spec_lock.md` 由唯一解析所有者承载；trace 事件版本化信封
- **中断恢复与空间治理**：`project_manager.py diagnose` 15 态只读诊断（稳定 blocker + 唯一 next action）；`space_report.py` 只读空间报告 + 归档 dry-run；`attribution_guard.py` 技能完整性 fail-closed 门禁

## 与 ppt-master 的关系

本项目是 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 的**扩展分支**。上游提供了完整 PPT 生成管线（源文件转换 → 项目管理 → 八项确认 → SVG 逐页生成 → 后处理 → PPTX 导出），DeepPPT 在此基础上做面向生产工作流的增强。

**核心差异化**：

| 能力 | ppt-master (上游) | DeepPPT (本项目) |
|------|-------------------|------------------|
| 输入 | 源文件 (PDF/DOCX/URL) | 仅需一个主题 |
| 调研 | 无 / 快速搜索 | 7 步独立调研（大纲→搜索拆分→多AI逐页搜索→汇总→分析→叙事→视觉策略） |
| 主题入口 | 直接进入生成前准备 | PPT Briefing 先确认目标、受众、叙事、素材策略和风险 |
| 搜索 | 内置 WebSearch | deep-research 计划搜索路径（Agent-Reach / 平台 / 浏览器自动化），内置 WebSearch 仅作记录式 fallback |
| 叙事 | 模板化大纲 | 故事弧线 + 转折点 + 过渡标记 |
| 视觉 | 通用设计规范 | 从调研内容中提取视觉身份 |
| 工作台 | 分散脚本输出 | 统一 Dashboard **产物展台**——按制作思路/设计契约/生成页面/导出成品四阶段浏览，本地 `artifacts_index.json` 可搜找；桥接 Confirm / Live Preview |
| 门禁 | 基础脚本校验 | confirm / research / asset / rendered visual / harness / e2e 多阶段质量门禁 + 重构版 `svg_quality` 诊断包 |
| 页面表达合同 | 无独立逐页机器合同 | `page_expression.json` 锁定 assertion / evidence / visual act / takeaway / next beat，覆盖 continuous / split / resume / refine 生命周期 |
| 图表选型 | 手动浏览图表索引 | 基于 3-8 个内容形态标签确定性召回候选，低置信度时才开放语义 fallback，入锁前校验精确键 |
| 排版 | 无自动检测 | 重构版导出器真实文字度量硬错误 + 静态合同检查 + 本地渲染截图门禁 + 意图优先的留白审查 |
| 视觉审查 | 无独立视觉回看 | 视觉检查工作流 + OpenAI/Anthropic/Ollama 兼容后端 |
| 动画 | 通用动画 | 默认页间转场；页内元素动画显式 opt-in，`customize-animations` 调整对象级顺序/效果/时序 |
| 视频导出 | 无原生视频链路 | 本机 PowerPoint COM 编码 MP4（h264 1080p）+ 动效规划 + 字幕对齐 + 旁白指纹同步 |
| 原生增强 | 重建幻灯片 | 追加式补丁（备注/音频/时序/转场，不重建幻灯片） |
| 原生修订 | 重建幻灯片 | OfficeCLI v1.0.143 固定运行时：原生 PPTX 对象树读取 + 浏览器选择 + 原子化可回滚修改（set/add/remove/move/swap）+ 副本修复 DOCX/XLSX + SVG divergence 状态 |
| 快速通道 | 无 | `quick-generate` 直通 profile |
| 原生形状 | 基础图元 | 187 个锁定 Office 预设 + 反向转换（beautify 复用同事实源）；structured 模板导出为文档化 opt-in |
| 模板治理 | 基础模板库 | 模板发现、质量审查、低分模板下线和显式路径应用 |
| 页面类型 | 6 种基础类型 | 11 种（含讲解页、对比页、数据页、时间线页等） |
| 图片策略 | 单轨（AI 或网络） | 来源路由 + 双轨——视觉页 AI 生图 + 信息页网络素材 |
| 咨询报告 | 通用大纲 | 可选证据表、SCR 备选、每页 SO WHAT / caveat / evidence IDs |
| 可编辑性 | SVG 导出为 PPTX | 可编辑信息层规则 + post-export PPTX 结构检查 |
| 内容深度 | 单页展示 | 证据和可读性驱动的页面拆分；主张与主要证据优先同页 |

DeepPPT 新增的代表性模块：`ppt-briefing`、`deep-research` 编排器、`browse_ai.py` 浏览器自动化、统一 Dashboard、`chart_recall.py`、`confirm_ui_gate.py` / `research_gate.py` / `asset_gate.py`、`image_source_router.py`、`rendered_layout_check.py`、`pptx_quality_check.py`、`icon_sync.py search`、`vision_check.py` + 多后端、OfficeCLI 集成套件（`install_officecli.py` / `officecli_bridge.py` / `native_revision_pptx.py` / `office_source_inspect.py` / `office_source_repair.py`）、`run_summary.py` / `space_report.py` / `project_manager.py diagnose` 治理工具。

**感谢上游作者 [Hugo He](https://www.hehugo.com/) 的开创性工作。** 如果本项目对你有帮助，也请给上游 [ppt-master](https://github.com/hugohe3/ppt-master) 一个 ⭐。

## 快速开始

> 📖 详细安装指南见 [SETUP.md](SETUP.md)

### 1. 环境准备

| 依赖 | 必需 | 说明 |
|------|:----:|------|
| [Python](https://www.python.org/downloads/) 3.10+ | ✅ | 唯一需要安装的运行时 |
| [Git](https://git-scm.com/downloads) | ✅ | 克隆仓库 |

### 2. 安装

```bash
git clone https://github.com/20231118185SSPU/DeepPPT.git
cd DeepPPT

# 一键安装（推荐）
bash scripts/setup/install_deps.sh          # Linux / Mac
# 或
powershell -ExecutionPolicy Bypass -File scripts/setup/install_deps.ps1  # Windows

# 检查依赖状态
python3 scripts/setup/check_deps.py
```

### 3. 配置 AI 图片生成（可选）

复制环境变量模板并填入 API Key：

```bash
cp .env.example .env
# 编辑 .env，设置 IMAGE_BACKEND 和对应的 API_KEY
```

支持的图片后端通过 `IMAGE_BACKEND` 显式选择，例如 `openai` / `gemini` / `qwen` / `zhipu` / `volcengine` / `minimax` 等。

零配置图片搜索源：Openverse / Wikimedia / NASA / Smithsonian（无需 API Key）。

### 4. 使用

**用任意 AI Agent 打开项目即可开始。** 项目为以下平台提供了配置文件：

| 平台 | 配置文件 |
|------|---------|
| Claude Code | `CLAUDE.md`（自动加载） |
| Cursor | `.cursor/rules/deep-ppt.md` |
| Windsurf | `.windsurfrules` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Codex CLI / Pi | `AGENTS.md` |
| Cline / Roo Code | `.clinerules` / `.roo/rules` |
| Aider | `.aider.conf.yml` |
| Amazon Q / Kiro | `.amazonq/rules/` / `.kiro/steering/` |
| JetBrains Junie | `junie/guidelines.md` |
| Hermes Agent | `hermes.md` |

**方式一：深度调研模式**（推荐——只需一个主题）

在任何支持 Agent 的 AI IDE 中打开项目目录，然后说：

```
做一个关于「量子计算的商业化前景」的 PPT
```

AI 会自动执行完整流程：深度调研 → 八项确认 → 图片生成 → SVG 生成 → 导出 PPTX。

主题只有一句话时，流程会先停在 PPT Briefing：系统生成 `ppt_brief.md` 和 `ppt_brief.json`，请你确认目标、受众、叙事、页数、素材来源和风险边界；确认后才进入深度调研和后续生成。

**方式二：源文件模式**（有现成材料）

```
请用 projects/my-report/report.pdf 生成 PPT
```

### 5. 输出

- `projects/<name>/exports/<name>_<timestamp>.pptx` — 原生可编辑 PPTX（Office 2016+）
- `projects/<name>/svg_output/` — SVG 源文件（可通过 live preview 实时编辑）

## 项目结构

```
DeepPPT/
├── skills/ppt-master/
│   ├── SKILL.md              # 薄入口主管线工作流（四路由分发）
│   ├── references/           # 角色定义和技术规范
│   ├── scripts/              # 运行工具脚本
│   │   ├── confirm_ui/       # 八项确认三阶段交互界面
│   │   ├── dashboard/        # 产物展台 Dashboard（四阶段浏览 + 本地索引）
│   │   ├── svg_editor/       # 实时预览编辑器
│   │   ├── svg_quality/      # 重构版质量诊断包（真实文字度量/溢出契约）
│   │   ├── svg_to_pptx/      # 重构版导出器（drawingml/pptx_package/native_objects）
│   │   ├── image_backends/   # 15+ AI 图片后端
│   │   ├── install_officecli.py / officecli_bridge.py  # OfficeCLI 固定运行时与桥接层
│   │   ├── native_revision_pptx.py     # 原生 PPTX 修订子工作流（inspect/watch/plan/apply）
│   │   ├── office_source_inspect.py / office_source_repair.py  # Office 源增强与副本修复
│   │   ├── image_source_router.py      # 图片来源路由
│   │   ├── chart_recall.py             # 确定性图表候选召回与键校验
│   │   ├── rendered_layout_check.py    # 渲染级布局检查
│   │   ├── pptx_quality_check.py       # 导出后 PPTX 结构 QA
│   │   ├── consulting_content_lock.py  # 咨询内容锁 sidecar
│   │   ├── attribution_guard.py        # 技能完整性门禁（fail-closed）
│   │   ├── prompt_audit.py             # prompt 语料审计（load_sets/token 预算/重复声明）
│   │   ├── svg_geometry_audit.py       # 字形盒级几何审计（advisory 首道防线）
│   │   ├── pptx_render_export.py       # PowerPoint COM 真实渲染导出（最终版式依据）
│   │   ├── run_summary.py              # 本地运行指标聚合（quality/run_summary.json）
│   │   ├── space_report.py             # 只读空间报告 + 归档 dry-run
│   │   ├── vision_backends/  # 视觉检查后端
│   │   ├── source_to_md/     # 源文件转换器
│   │   └── research/         # 浏览器自动化搜索和研究/素材门禁
│   ├── fixtures/             # 合成路线回归 fixture（template-fill/enhance/structured/partial 15 态/保真/trace/space/beautify 1:1/officecli，rebuild 脚本可重建）
│   ├── templates/            # 布局模板、图表模板、图标库、品牌预设
│   └── workflows/            # 路由 + 独立工作流
│       ├── routing.md        # 四路由选择权威（Generate/Template/Fill/Enhance）
│       ├── generate-pptx.md  # 主管线 Step 1-8（门禁/合同/导出）
│       ├── ppt-briefing.md   # 主题输入前置构思与确认
│       ├── deep-research.md  # 深度调研编排器 (7步协调)
│       ├── research/         # 7步独立工作流
│       ├── stages/           # 阶段工作流（resume/refine/live-preview/verify-charts/visual-review/animations/audio/native-revision）
│       ├── profiles/         # 生成 profile（quick-generate / beautify-pptx）
│       ├── create-template.md / create-brand.md / template-fill-pptx.md / native-enhance-pptx.md
│       └── governance/       # failure-recovery 恢复矩阵
├── docs/                     # 文档（含 reviews/ 审计、rules/ 治理规则、zh/ 中文镜像）
├── scripts/setup/            # 依赖检查与自动安装脚本
├── examples/                 # 29 个公开回归示例（checker + e2e 双门全绿，CI/Pages 使用）
└── projects/                 # 用户项目工作区（active/archive/disposable 生命周期治理）
```

模板和品牌预设只在用户给出明确目录路径时应用；裸模板名、品牌名或风格描述不会自动触发套用。可先询问 Dashboard / Confirm UI 中的模板列表，再把选中的 `skills/ppt-master/templates/.../<id>/` 路径交给工作流。

## 工作原理

```
主题/源文件
  │
  ▼
┌─────────────────────────────────────────┐
│  Phase 0: PPT Briefing（仅主题输入）      │
│  ├─ 明确目标、受众、场景和页数            │
│  ├─ 锁定叙事框架、内容边界和验收标准      │
│  └─ 确认素材策略、来源路由和版权风险      │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  Phase A: 深度调研（7步独立工作流）       │
│  ├─ Step 1: 大纲生成（用户确认）          │
│  ├─ Step 2: 搜索需求拆分（AI分配）        │
│  ├─ Step 3: 逐页搜索（Agent-Reach /     │
│  │          平台 / 浏览器自动化路径）       │
│  ├─ Step 4: 汇总                         │
│  ├─ Step 5: 结构化分析 + 交叉验证         │
│  ├─ Step 6: 叙事构建（故事弧线）          │
│  └─ Step 7: 视觉策略                     │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  Phase B: 设计 + 生成                    │
│  ├─ 统一 Dashboard（状态/产物/质量/轨迹） │
│  ├─ 内容筛选 + 详细大纲 + 图文语境绑定     │
│  ├─ 八项确认 + 确认门禁                  │
│  ├─ 页面表达合同 + spec lock 摘要封存      │
│  ├─ 图表候选召回 + 精确键校验             │
│  ├─ 图片来源路由 + 双轨图片生成           │
│  ├─ 研究深度 / 素材完整性门禁             │
│  ├─ SVG 逐页生成（实时预览）             │
│  ├─ 静态质量检查 + 渲染级布局检查 + 视觉审查 │
│  ├─ 后处理 + PPTX 导出                   │
│  └─ 导出校验 + 动画配置                  │
└─────────────────────────────────────────┘
  │
  ▼
原生可编辑 PPTX
```

## 文档

| 文档 | 说明 |
|------|------|
| [SETUP.md](SETUP.md) | 首次使用指南（安装 + 配置 + 13 平台使用） |
| [SKILL.md](skills/ppt-master/SKILL.md) | 核心工作流（必须阅读） |
| [ppt-briefing.md](skills/ppt-master/workflows/ppt-briefing.md) | 主题输入前置构思与确认 |
| [deep-research.md](skills/ppt-master/workflows/deep-research.md) | 深度调研编排器 |
| [research/](skills/ppt-master/workflows/research/) | 7 步独立调研工作流 |
| [native-revision.md](skills/ppt-master/workflows/stages/native-revision.md) | 原生 PPTX 修订子工作流（OfficeCLI） |
| [officecli.md](skills/ppt-master/scripts/docs/officecli.md) | OfficeCLI 集成（运行时/桥接/修订/源增强/修复） |
| [image-source-routing.md](skills/ppt-master/references/image-source-routing.md) | 图片来源路由和版权风险策略 |
| [ai-browser-setup.md](docs/ai-browser-setup.md) | 浏览器自动化配置（CDP Chrome） |
| [dashboard-unified-design.md](docs/design/dashboard-unified-design.md) | 统一 Dashboard 设计说明 |
| [Canvas Formats](skills/ppt-master/references/canvas-formats.md) | 画布格式列表 |
| [Scripts & Tools](skills/ppt-master/scripts/README.md) | 工具脚本文档 |
| [Change Log](docs/change-log.md) | 完整变更记录 |

## 更新日志

### 2026-08-05 — OfficeCLI 深度集成 Phase 1-4 契约收尾

- **固定运行时**：OfficeCLI v1.0.143 安装到 gitignored `.tools/officecli/`（SHA-256 锁、8 平台 manifest、无 PATH fallback）；`install/check/path --json` 公共命令契约修复（子命令前后 `--json` 均可），checksum/version 负例 fail-closed
- **原生 PPTX 修订**：inspect / watch / selected / check-plan / apply / validate 八子命令；check-plan 实测 target 存在性与 expect fingerprint；apply 七门禁 postflight（baseline-delta validate、slide roster、未寻址 parts 语义保护、COM render、SVG divergence）；中途失败整批回滚不发布
- **Office 源增强与副本修复**：`import-sources` 自动生成 `office_sources.json`（DOCX/PPTX/XLSX 格式感知计数 + 问题 + converter 映射，含 legacy 标记）；opt-in 副本式 DOCX/XLSX 修复（原件 SHA-256 不变、修复副本 + 新 Markdown + provenance）
- **可观测性与 CI**：8 个稳定 trace operation（含 probe/validate）零敏感内容；Dashboard `/api/state` 三键只读展示；run_summary 消费 officecli 耗时；smoke integration Tests 15-17（291 checks）；CI 自动安装 pinned 二进制
- 全部验证：guard rc=0；smoke 89/0/3/92、180/0/4/184、291/0/4/295；四顶层路由不变

### 2026-08-04 — 实际交付优化（Phase 1-6）：PowerPoint 真实渲染终裁 + 路线 fixture + 运行指标

- PowerPoint COM 真实渲染成为最终版式依据；`svg_geometry_audit.py` 字形盒审计（Golden Set 校准 74 FP → 0，保持 advisory）
- 9 套合成非敏感 fixture 入库（含 rebuild 脚本），smoke integration Tests 10-14；DOCX/PPTX 源内容保真对账、损坏输入 fail-closed
- `run_summary.py` 运行指标闭环（null≠0 语义）；`project_manager.py diagnose` 15 态只读诊断；`space_report.py` 空间治理（已批准清理 307 MiB）
- CI 三 job 全绿（smoke-check 282 项 / svg-quality 29 项目 / e2e 29 项目）

### 2026-08-04 — 系统优化收尾（Phase 1-8）：单一事实源 + 契约治理 + CLI 卫生

- `project_utils` 规范 accessors + `derive_pipeline_state` 单一事实源；`spec_lock.md` 唯一解析所有者
- `prompt_audit` 契约重建（Generate 路由典型加载 −21.4%，语料 coverage 闭合）；trace 版本化信封
- 85 个 CLI 入口统一 `raise SystemExit(main())`；smoke integration 升级至 187 项

### 2026-08-03 — v4.3.0 迁移收尾：质量门全绿 + Dashboard 产物展台 + CI/Pages 上线

- 重构版导出器（真实文字度量 / 21 类 SVG→DrawingML 语法契约）+ `svg_quality` 诊断包整体接线；`structured` 模板导出落地
- 29 个公开示例全部通过双门（29/29）；GitHub Actions CI 三 job 全绿；GitHub Pages 上线
- Dashboard 重新定位为产物在线观看平台（四阶段浏览 + 本地索引）

> 更早的完整变更记录见 [docs/change-log.md](docs/change-log.md)。

## 致谢

- **上游项目**：[ppt-master](https://github.com/hugohe3/ppt-master) by [Hugo He](https://www.hehugo.com/) — 提供了完整的 PPT 生成管线架构
- **图标库**：[Tabler Icons](https://github.com/tabler/tabler-icons) · [Simple Icons](https://github.com/simple-icons/simple-icons) · [Phosphor Icons](https://github.com/phosphor-icons/core)
- **图片资源**：[SVG Repo](https://www.svgrepo.com/) · [Pexels](https://www.pexels.com/) · [Pixabay](https://pixabay.com/)

## 许可证

[MIT](LICENSE) — 与上游 ppt-master 保持一致。使用本项目时请注明基于 [ppt-master](https://github.com/hugohe3/ppt-master) 开发。
