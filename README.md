# DeepPPT - Research-Driven, Native-Editable AI Presentations

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An extension of [ppt-master](https://github.com/hugohe3/ppt-master) with briefing-led deep research, evidence-backed planning, deterministic chart recall, intent-first page composition, contract-aware observability, and production quality gates.

[English](#overview) | [中文](#简介)

## Overview

DeepPPT turns a topic or source document into a natively editable PPTX. It coordinates research, narrative and visual planning, asset acquisition, SVG authoring, validation, and export while preserving explicit machine contracts across resumable workflows.

Latest production hardening includes:

- **Deterministic chart recall** - `chart_recall.py` ranks up to the requested number of candidates from the live visualization catalog using 3-8 content-shape tags, gates semantic fallback on low lexical confidence, and validates exact selected keys.
- **Complete page-expression lifecycle** - the Strategist-owned `page_expression.json` remains authoritative across continuous, split, resume, and refine-spec paths; compliance checks enforce page coverage and visible assertions, and the contract is sealed together with `spec_lock.md`.
- **Evidence-backed consulting narratives** - when consulting evidence is enabled, research preserves traceable evidence rows and resolves exactly 2-3 SCR alternatives into one recommendation with evidence IDs, caveats, and explicit rejection reasons.
- **Digest-aware observability** - the read-only Dashboard exposes page-expression and digest state, while Harness verifies the seal for sidecar projects and fails closed on contract drift.
- **Intent-first composition QA** - the Executor composes from `content_relation`, `information_anchor`, and `visual_act` before choosing layout patterns. Sparse composition, one-sided whitespace, and large image-text gaps remain review signals rather than prompts to add filler; fixes are batched before one re-check.

---

## 简介

DeepPPT 是一个端到端的 AI PPT 生成系统。给定一个主题或源文件，它会自动完成深度调研、结构化分析、叙事构建、视觉身份提取、资源获取、SVG 页面生成、质量门禁和 PPTX 导出，最终产出一份**原生可编辑的 PPTX**。

当输入只有一个主题时，DeepPPT 会先生成可确认的 `ppt_brief.md` / `ppt_brief.json`，明确目标、受众、叙事、素材策略和验收标准；用户确认后才进入深度调研，避免在方向未锁定时直接搜索和生成。

当前版本进一步将页面表达、图表选型和执行可观测性收敛为机器合同：`page_expression.json` 贯穿连续生成、分段交接、恢复执行和规格精修路径，并与 `spec_lock.md` 一同封存；图表候选从实时目录中确定性召回并校验精确键；Dashboard 和 Harness 会显示并验证合同摘要状态，防止恢复或修改过程中的静默漂移。

**支持 13 个主流 AI Agent 平台**，克隆即用：Claude Code / Cursor / Windsurf / GitHub Copilot / OpenAI Codex / Pi / Cline / Roo Code / Aider / Amazon Q / Kiro / Junie / Hermes Agent。

**核心差异化**（相比上游 ppt-master）：

| 能力 | ppt-master (上游) | DeepPPT (本项目) |
|------|-------------------|------------------|
| 输入 | 源文件 (PDF/DOCX/URL) | 仅需一个主题 |
| 调研 | 无 / 快速搜索 | 7 步独立调研（大纲→搜索拆分→多AI逐页搜索→汇总→分析→叙事→视觉策略） |
| 主题入口 | 直接进入生成前准备 | PPT Briefing 先确认目标、受众、叙事、素材策略和风险 |
| 搜索 | 内置 WebSearch | deep-research 计划搜索路径（Agent-Reach / 平台 / 浏览器自动化），内置 WebSearch 仅作记录式 fallback |
| 叙事 | 模板化大纲 | 故事弧线 + 转折点 + 过渡标记 |
| 视觉 | 通用设计规范 | 从调研内容中提取视觉身份 |
| 工作台 | 分散脚本输出 | 统一 Dashboard 追踪项目状态、产物、质量报告、执行轨迹和预览入口 |
| 门禁 | 基础脚本校验 | confirm / research / asset / rendered visual / harness / e2e 多阶段质量门禁 |
| 页面表达合同 | 无独立逐页机器合同 | `page_expression.json` 锁定 assertion / evidence / visual act / takeaway / next beat，并覆盖 continuous / split / resume / refine 生命周期 |
| 图表选型 | 手动浏览图表索引 | 基于 3-8 个内容形态标签确定性召回候选，低置信度时才开放语义 fallback，入锁前校验精确键 |
| 协同性治理 | 依赖人工维护 | 链接扫描、workflow Exit Evidence、脚本分层、语言规则现实化和审计修复记录 |
| 排版 | 无自动检测 | 静态合同检查 + 本地渲染截图门禁 + 意图优先的留白审查；宽松构图只提示复核，不用填充物“修正” |
| 视觉审查 | 无独立视觉回看 | 视觉检查工作流 + OpenAI/Anthropic/Ollama 兼容后端 |
| 动画 | 通用动画 | 默认页间转场；页内元素动画显式 opt-in，可用 `customize-animations` 调整对象级顺序/效果/时序；完整动画链（seq_targets → timing XML → trace 富化）支持导出期校验 |
| 视频导出 | 无原生视频链路 | 本机 PowerPoint COM 编码 MP4（h264 1080p）+ 动效规划 + 字幕对齐 + 旁白指纹同步 |
| 原生增强 | 重建幻灯片 | 追加式补丁已完成的 PPTX（备注/音频/时序/转场，不重建幻灯片） |
| 快速通道 | 无 | `quick-generate` 直通 profile：显式快速意图 → 手写 SVG → lockless 检查 → 导出，不建 spec/lock |
| 原生形状 | 基础图元 | 187 个锁定 Office 预设 + 反向转换（beautify 复用同事实源）；structured 模板导出为文档化 opt-in |
| 模板治理 | 基础模板库 | 模板发现、质量审查、低分模板下线和显式路径应用 |
| 页面类型 | 6 种基础类型 | 11 种（含讲解页、对比页、数据页、时间线页等） |
| 图片策略 | 单轨（AI 或网络） | 来源路由 + 双轨——视觉页 AI 生图 + 信息页网络素材 |
| 咨询报告 | 通用大纲 | 可选证据表、SCR 备选、每页 SO WHAT / caveat / evidence IDs |
| 可编辑性 | SVG 导出为 PPTX | 可编辑信息层规则 + post-export PPTX 结构检查 |
| 内容深度 | 单页展示 | 证据和可读性驱动的页面拆分；主张与主要证据优先同页，不设置讲解页数量配额 |

## 与 ppt-master 的关系

本项目是 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 的**扩展分支**。

- **上游 ppt-master** 提供了完整的 PPT 生成管线：源文件转换 → 项目管理 → 八项确认 → SVG 逐页生成 → 后处理 → PPTX 导出
- **DeepPPT** 在此基础上新增了：
  - [`ppt-briefing`](skills/ppt-master/workflows/ppt-briefing.md) 前置构思工作流——主题输入先确认目标、受众、叙事、素材策略和风险，再进入深度调研
  - [`deep-research`](skills/ppt-master/workflows/deep-research.md) 编排器——7 步独立调研工作流，协调计划搜索路径；普通 WebSearch 只作为 deep-research Step 3 内部记录式 fallback
  - [`browse_ai.py`](skills/ppt-master/scripts/research/browse_ai.py)——Playwright CDP 浏览器自动化，支持 Grok / Kimi / DeepSeek / 通义千问 / ChatGLM / Perplexity
  - [`dashboard`](skills/ppt-master/scripts/dashboard/)——统一只读 Dashboard，集中展示项目状态、产物、质量报告、执行轨迹、模板预览和 Confirm / Live Preview 入口
  - [`chart_recall.py`](skills/ppt-master/scripts/chart_recall.py)——从实时图表目录确定性召回候选，在低词法置信度时约束语义 fallback，并校验进入 `page_charts` 的精确键
  - `page_expression.json` 全生命周期合同——逐页锁定主张、证据、视觉动作、结论和叙事衔接，与 `spec_lock.md` 一同封存并由 compliance / Harness / Dashboard 验证
  - [`confirm_ui_gate.py`](skills/ppt-master/scripts/confirm_ui_gate.py)、[`research_gate.py`](skills/ppt-master/scripts/research/research_gate.py)、[`asset_gate.py`](skills/ppt-master/scripts/research/asset_gate.py)——确认、研究深度和素材完整性门禁
  - [`image_source_router.py`](skills/ppt-master/scripts/image_source_router.py) + [`image-source-routing.md`](skills/ppt-master/references/image-source-routing.md)——按主题域选择官方、学术、开放版权、通用氛围图等来源包，降低错图和版权风险
  - [`rendered_layout_check.py`](skills/ppt-master/scripts/rendered_layout_check.py)——基于本地渲染截图的布局门禁，补足静态 SVG 检查无法发现的重叠、踩线和异常留白
  - 咨询类可选规则层——`deep-research` / `detailed-outline` / Strategist 支持 `evidence_table`、2-3 条 SCR 候选故事线、每页 `evidence_ids` / `caveats` / `so_what` / `content_density`
  - [`consulting_content_lock.py`](skills/ppt-master/scripts/consulting_content_lock.py)——从 detailed outline / spec lock 生成 `analysis/slide_content_lock.json`，锁定咨询页标题、KPI、图表、表格、注释和证据 ID
  - [`pptx_quality_check.py`](skills/ppt-master/scripts/pptx_quality_check.py)——导出后直接读取 PPTX ZIP/XML，检查画布比例、越界形状、占位符、整页图片风险、native text 数量和最小字号
  - [`icon_sync.py search`](skills/ppt-master/scripts/icon_sync.py)——按图标文件名和 SVG 头部标签搜索候选 `lib/name`，再沿用现有 icon sync 复制流程
  - [`vision_check.py`](skills/ppt-master/scripts/vision_check.py) + [`vision_backends`](skills/ppt-master/scripts/vision_backends/)——可插拔视觉检查后端
  - [`docs/reviews/`](docs/reviews/) + [`docs/rules/`](docs/rules/)——管线协同性审计、修复状态记录和仓库级语言 / 文档治理规则
  - [`batch-review`](skills/ppt-master/workflows/batch-review.md)——按批生成与审阅的可选工作流
  - 模板库质量治理——Dashboard / Confirm UI 统一展示候选预览，低分模板经审查和用户确认后从索引下线
  - [`story_driven`](skills/ppt-master/templates/layouts/story_driven/) 布局模板——封面/目录/过渡/内容/讲解/金句/对比/数据/时间线/全图/封底
  - [`img2img-support`](docs/design/img2img-support.md)——图生图支持的非运行时设计说明，不是可直接调用的 standalone workflow
  - 排版稳定性检测（布局溢出/元素间距/垂直分布）+ 自动修正
  - 默认页间转场 + 显式 opt-in 的对象级动画配置
  - 多后端 AI 图片生成（OpenAI / Gemini / Replicate / Stability / 通义千问 / 智谱 / SiliconFlow 等 15+ 后端）

DeepPPT 沿用上游管线脚本（`project_manager.py`、`svg_editor/`、`confirm_ui/`、`svg_to_pptx.py` 等），并在交互确认、实时预览、质量检查、研究门禁、视觉审查和导出校验上做了面向生产工作流的增强。

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
│   ├── SKILL.md              # 主管线工作流
│   ├── references/           # 角色定义和技术规范
│   ├── scripts/              # 运行工具脚本
│   │   ├── confirm_ui/       # 八项确认交互界面
│   │   ├── dashboard/        # 统一 Dashboard
│   │   ├── svg_editor/       # 实时预览编辑器
│   │   ├── image_backends/   # 15+ AI 图片后端
│   │   ├── image_source_router.py  # 图片来源路由
│   │   ├── chart_recall.py         # 确定性图表候选召回与键校验
│   │   ├── rendered_layout_check.py # 渲染级布局检查
│   │   ├── pptx_quality_check.py    # 导出后 PPTX 结构 QA
│   │   ├── consulting_content_lock.py # 咨询内容锁 sidecar
│   │   ├── vision_backends/  # 视觉检查后端
│   │   ├── source_to_md/     # 源文件转换器
│   │   └── research/         # 浏览器自动化搜索和研究/素材门禁
│   ├── templates/            # 布局模板、图表模板、图标库
│   │   └── layouts/story_driven/  # 叙事驱动模板 (DeepPPT 新增)
│   └── workflows/            # 独立工作流
│       ├── ppt-briefing.md   # 主题输入前置构思与确认
│       ├── deep-research.md  # 深度调研编排器 (7步协调)
│       ├── research/         # 7步独立工作流
│       │   ├── step1_outline.md       # 大纲生成
│       │   ├── step2_search_plan.md   # 搜索需求拆分
│       │   ├── step3_search.md        # 逐页多AI搜索
│       │   ├── step4_consolidate.md   # 汇总
│       │   ├── step5_analysis.md      # 结构化分析
│       │   ├── step6_narrative.md     # 叙事构建
│       │   └── step7_visual.md        # 视觉策略
│       ├── live-preview.md   # 实时预览
│       ├── visual-review.md  # 视觉审查
│       ├── batch-review.md   # 分批生成审阅
│       └── ...
├── docs/                     # 文档
├── scripts/setup/            # 依赖检查与自动安装脚本
├── examples/                 # 示例项目
└── projects/                 # 用户项目工作区
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
| [image-source-routing.md](skills/ppt-master/references/image-source-routing.md) | 图片来源路由和版权风险策略 |
| [ai-browser-setup.md](docs/ai-browser-setup.md) | 浏览器自动化配置（CDP Chrome） |
| [dashboard-unified-design.md](docs/design/dashboard-unified-design.md) | 统一 Dashboard 设计说明 |
| [pipeline-coherence-audit-2026-07.md](docs/reviews/pipeline-coherence-audit-2026-07.md) | 管线成熟度与协同性审计及修复状态 |
| [Canvas Formats](skills/ppt-master/references/canvas-formats.md) | 画布格式列表 |
| [Scripts & Tools](skills/ppt-master/scripts/README.md) | 工具脚本文档 |

## 更新日志

### 2026-08-03 — 五阶段迁移完成（对齐 ppt v4.3.0 并消化为自身架构）

**阶段 1（Confirm UI）：** 三阶段确认向导迁移 + 完整性/审计工具（stage 基准验证、confirmation 门禁）。

**阶段 2（四路由重构）：** `SKILL.md` 收敛为薄入口，`workflows/routing.md` 承载 Generate / Create Template / Fill / Enhance Native PPTX 路由矩阵；主流程提取到 `workflows/generate-pptx.md`，全仓链接重写。

**阶段 3（原生增强）：** `native_enhance_pptx` 追加式补丁套件（备注、音频、时序、转场），不重建幻灯片；notesMaster 支持与 OPC 校验。

**阶段 4（视频导出）：** 本机 PowerPoint 编码 MP4 + 动画链完整移植（seq_targets、trace 富化）+ 动效规划 + 字幕 + 旁白同步。

**阶段 5（原生形状/模板）：** `pptx_shapes`（187 预设）+ `preset_shape_svg` / `prstgeom_to_svg`（beautify 反向闭环）+ 6 份规范文档接口映射 + `spec_lock` 的 `pptx_structure.mode` 声明（structured 导出为文档化 opt-in）；`quick-generate` 直通 profile 落地。

### 2026-07-25 — 页面表达、图表召回与证据合同强化

**规划与研究：**
- `page_expression.json` 贯穿连续、分段、恢复和规格精修路径，并与 `spec_lock.md` 一同进行摘要封存和漂移检查。
- 新增确定性图表候选召回；咨询研究在启用证据模式时保留可追溯证据，并从 2-3 条 SCR 备选中形成单一建议。

**执行与质量：**
- Dashboard / Harness 展示并验证页面表达及摘要状态；合同缺失、不可见 assertion 或摘要漂移会失败关闭。
- Executor 先依据内容关系、信息锚点和视觉动作构图；宽松留白、单侧构图和较大图文间距只进入复核，不再诱导填充装饰。
- 质量修复先集中收集、一次修正，再统一复检，减少逐项反复调用检查器。

### 2026-07-04 — Dashboard / Confirm UI 预览与模板治理

**交互与可视化：**
- Dashboard 确认中心集中展示模板库候选，模板缩略图完整缩放，放大弹窗支持多页预览切换。
- Confirm UI 升级为三阶段视觉确认，加入风格 SVG 预览、图标预览、AI 图像对比和多语言界面。
- Dashboard 产物与日志页面优化产物类型布局，长文件名、大小和展开动作不再挤压重叠。

**模板与质量：**
- 完成模板质量审查并按用户确认下线低分模板，索引和模板指南同步更新。
- Dashboard 增加逐页 layout 预览入口；公式渲染默认提高清晰度并改进 manifest 字段兼容。
- 质量门禁默认采用非破坏性 layout suggest 模式，渲染截图统一写入 `quality/screenshots/` 便于复核。

### 2026-07-03 — 管线协同性审计修复

**协同一致性：**
- 修复 `SKILL.md` 与 `strategist.md` 中的相对链接断链，补齐全仓链接扫描闭环。
- 收敛 `batch-review`、`deep-research`、`image-text-linking` 的契约漂移，避免 UI 死触发、参考图门槛弱化和 prompt 模板段数不一致。
- 将非运行时 `img2img-support` 设计说明迁入 `docs/design/`，保持 `workflows/` 只承载运行工作流。

**治理与证据：**
- `scripts/README.md` 按 runtime pipeline / workflow satellite / maintenance / internal helper 分层，顶层脚本全覆盖。
- 轻量 workflow 补齐 Exit Evidence / completion block，便于恢复、复核和审计。
- 语言规则现实化为目录主模式：workflows 可采用英文结构骨架 + 中文说明正文，references 主英文，docs 按子目录声明。
- 修复状态已记录到 [docs/change-log.md](docs/change-log.md) 和 [pipeline-coherence-audit-2026-07.md](docs/reviews/pipeline-coherence-audit-2026-07.md)。

### 2026-07-03 — 仓库介绍与治理工具对齐

**文档对齐：**
- README、SETUP、FAQ、getting-started、AI browser setup、Agent 入口摘要和脚本 README 对齐当前真实工作流。
- 仅给主题时统一为 `ppt-briefing → 用户确认 → deep-research → 主流程`，不再描述为直接进入 deep-research。
- Dashboard 默认行为统一为 `--daemon`，本地运行会自动打开浏览器；`--no-browser` 仅用于 headless / remote / 用户明确要求。
- 模板和品牌应用明确要求显式目录路径；裸名称只用于发现，不会自动套用。

**治理与发现：**
- 新增 `governance_drift_check.py`，用于检查 topic-only 路由、Dashboard 默认命令、docs/rules 状态和路径漂移。
- 模板索引和模板 `design_spec.md` 补齐 `summary_zh`，支持 Dashboard / Confirm UI 双语摘要和预览发现。
- 更新日志已同步到 [docs/change-log.md](docs/change-log.md)。

### 2026-07-02 — 咨询证据链 + PPTX 结构 QA + 图标搜索

**工作流增强：**
- deep-research / detailed-outline / Strategist 新增咨询类可选证据链：`evidence_table`、2-3 条 SCR 候选、每页 `evidence_ids`、`caveats`、`so_what` 和 `content_density`。
- Executor 与 shared standards 明确“可编辑信息层 vs 复杂视觉资产层”，禁止整页截图伪装，补入 `pictures=0` 非目标和高密度页面 QA 术语。
- 新增 `consulting_content_lock.py`，为高密度咨询页生成 `analysis/slide_content_lock.json` sidecar。
- 新增 `pptx_quality_check.py`，在 `svg_to_pptx.py` 导出后做可选 PPTX ZIP/XML 结构检查。
- `icon_sync.py` 新增 `search` 子命令，支持先搜索候选图标再同步复制。

**边界：**
- 不引入 PptxGenJS / COM 合并路线，不新增 `test_*.py`、`unittest` 或 `pytest`。
- 所有新增能力服务现有 SVG → DrawingML 主线，均为可选增强或 post-export QA。

### 2026-07-02 — PPT Briefing + 图片来源路由 + 渲染级视觉门禁

**工作流增强：**
- 新增 `ppt-briefing`：仅给主题时先生成并确认 PPT 创作蓝图，再进入 deep-research。
- 新增图片来源路由规则：按人物、产品、IP、学术、历史、近期事件、通用氛围等场景选择 source pack，避免把通用图库误用于事实敏感素材。
- 新增 `image_source_router.py`，把 `ppt_brief`、`detailed_outline`、`design_spec` 中的素材意图转成可执行的图片检索/生成路由。
- 新增 `rendered_layout_check.py`，通过本地渲染截图检查重叠、踩线、异常留白和改后视觉退化风险。

**文档同步：**
- `AGENTS.md`、`SKILL.md`、脚本文档、模板说明和本 README 已同步新的入口、图片策略和质量门禁。

### 2026-06-30 — 统一 Dashboard + 多阶段质量门禁

**工作流增强：**
- 新增统一 Dashboard，集中展示项目状态、产物、质量报告、执行轨迹，并桥接八项确认和实时预览。
- 新增确认门禁、研究深度门禁、素材完整性门禁和聚合质量门禁，减少跨阶段遗漏。
- 新增视觉检查入口与多后端适配，支持 OpenAI / Anthropic 格式和 Ollama。
- 新增分批生成审阅工作流，适合长篇 deck 的阶段性视觉反馈。

**工作区整理：**
- 本地 Codex、Dashboard、Live Preview、浏览器缓存、服务日志和项目产物已通过 `.gitignore` 分离。
- 新增共享 AI 规则文档，统一多 Agent 平台的项目入口说明。

### 2026-06-28 — 深度调研重构 + 视频建议实施

**架构变更：**
- 🔄 **深度调研拆为 7 步独立工作流**（大纲→搜索拆分→多AI逐页搜索→汇总→分析→叙事→视觉策略），每步输出到独立文件夹
- 🗑️ **移除 topic-research 快速模式**，所有输入统一走深度调研
- 🤖 **新增多 AI 浏览器自动化**（`browse_ai.py`），通过 Playwright CDP 连接 Chrome；当前支持 Grok / Kimi / DeepSeek / 通义千问 / ChatGLM / Perplexity

**质量提升：**
- 📐 **排版稳定性检测**：svg_quality_checker.py 新增 3 项检查（布局溢出、元素间距、垂直分布）
- 🔧 **自动修正**：finalize_svg.py 新增 fix-layout 步骤（文字溢出自动缩减字号）
- 🎬 **动画策略收敛**：默认保留页间转场，页内元素动画改为显式 opt-in，避免不必要的自动级联
- 🖼️ **视觉优先页规则**：executor-base.md §19，封面等关键页用全屏 AI 背景
- 🧭 **模板治理**：模板库支持审查、下线和发现索引同步，低分候选不再作为默认可选项暴露

**文档更新：**
- 📖 SETUP.md 新增浏览器自动化设置章节
- 📖 ai-browser-setup.md 新增 browse_ai.py 集成文档
- 📖 所有文档移除 topic-research 引用

> 完整变更记录见 [docs/change-log.md](docs/change-log.md)

## 致谢

- **上游项目**：[ppt-master](https://github.com/hugohe3/ppt-master) by [Hugo He](https://www.hehugo.com/) — 提供了完整的 PPT 生成管线架构
- **图标库**：[Tabler Icons](https://github.com/tabler/tabler-icons) · [Simple Icons](https://github.com/simple-icons/simple-icons) · [Phosphor Icons](https://github.com/phosphor-icons/core)
- **图片资源**：[SVG Repo](https://www.svgrepo.com/) · [Pexels](https://www.pexels.com/) · [Pixabay](https://pixabay.com/)

## 许可证

[MIT](LICENSE) — 与上游 ppt-master 保持一致。使用本项目时请注明基于 [ppt-master](https://github.com/hugohe3/ppt-master) 开发。
