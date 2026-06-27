# DeepPPT — AI 深度调研驱动的 PPT 生成系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 基于 [ppt-master](https://github.com/hugohe3/ppt-master) 扩展开发，增加深度调研、叙事驱动模板、双轨图片生成等能力。

English | [中文](#简介)

---

## 简介

DeepPPT 是一个端到端的 AI PPT 生成系统。给定一个主题，它会自动完成深度调研、结构化分析、叙事构建、视觉身份提取、AI 图片生成，最终产出一份**原生可编辑的 PPTX**。

**支持 12 个主流 AI Agent 平台**，克隆即用：Claude Code / Cursor / Windsurf / GitHub Copilot / OpenAI Codex / Pi / Cline / Roo Code / Aider / Amazon Q / Kiro / Junie / Hermes Agent。

**核心差异化**（相比上游 ppt-master）：

| 能力 | ppt-master (上游) | DeepPPT (本项目) |
|------|-------------------|------------------|
| 输入 | 源文件 (PDF/DOCX/URL) | 仅需一个主题 |
| 调研 | 无 / 快速搜索 | 7 步独立调研（大纲→搜索拆分→多AI逐页搜索→汇总→分析→叙事→视觉策略） |
| 搜索 | 内置 WebSearch | 多 AI 浏览器自动化（ChatGPT/Grok/Perplexity 按内容类型分工） |
| 叙事 | 模板化大纲 | 故事弧线 + 转折点 + 过渡标记 |
| 视觉 | 通用设计规范 | 从调研内容中提取视觉身份 |
| 排版 | 无自动检测 | 3 项布局检查（溢出/间距/垂直分布）+ 自动修正 |
| 动画 | 通用动画 | 按页面类型强制节奏（§18 规则） |
| 场景 | 通用模板 | 发布会品牌预设（Apple keynote 风格） |
| 页面类型 | 6 种基础类型 | 11 种（含讲解页、对比页、数据页、时间线页等） |
| 图片策略 | 单轨（AI 或网络） | 双轨——视觉页 AI 生图 + 信息页网络素材 |
| 内容深度 | 单页展示 | 内容页 + 讲解页配对，每页都可讲 |

## 与 ppt-master 的关系

本项目是 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 的**扩展分支**。

- **上游 ppt-master** 提供了完整的 PPT 生成管线：源文件转换 → 项目管理 → 八项确认 → SVG 逐页生成 → 后处理 → PPTX 导出
- **DeepPPT** 在此基础上新增了：
  - [`deep-research`](skills/ppt-master/workflows/deep-research.md) 编排器——7 步独立调研工作流，协调多 AI 浏览器自动化搜索
  - [`browse_ai.py`](skills/ppt-master/scripts/research/browse_ai.py)——Playwright CDP 浏览器自动化，ChatGPT/Grok/Perplexity 按内容类型分工搜索
  - [`event_presentation`](skills/ppt-master/templates/brands/event_presentation/) 品牌预设——发布会/产品发布场景（暗色调 keynote 风格）
  - [`story_driven`](skills/ppt-master/templates/layouts/story_driven/) 布局模板——封面/目录/过渡/内容/讲解/金句/对比/数据/时间线/全图/封底
  - [`img2img-support`](skills/ppt-master/workflows/img2img-support.md) 文档——图生图策略说明
  - 排版稳定性检测（布局溢出/元素间距/垂直分布）+ 自动修正
  - 动画节奏强制规则（§18）+ 视觉优先页规则（§19）
  - 多后端 AI 图片生成（OpenAI / Gemini / Replicate / Stability / 通义千问 / 智谱 / SiliconFlow 等 15+ 后端）

所有上游管线脚本（`project_manager.py`、`svg_editor/`、`confirm_ui/`、`svg_to_pptx.py` 等）保持不变。DeepPPT 的扩展通过新增工作流、模板和质量检查规则实现，对现有脚本的修改仅限于增加新检查项和自动修正步骤，不改变原有逻辑。

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

支持的图片后端：`openai` / `gemini` / `qwen` / `zhipu` / `volcengine` / `minimax` 等 15+ 后端。

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
│   │   ├── svg_editor/       # 实时预览编辑器
│   │   ├── image_backends/   # 15+ AI 图片后端
│   │   ├── source_to_md/     # 源文件转换器
│   │   └── research/         # 浏览器自动化搜索 (browse_ai.py)
│   ├── templates/            # 布局模板、图表模板、图标库
│   │   └── layouts/story_driven/  # 叙事驱动模板 (DeepPPT 新增)
│   └── workflows/            # 独立工作流
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
│       └── ...
├── docs/                     # 文档
├── scripts/setup/            # 依赖检查与自动安装脚本
├── examples/                 # 示例项目
└── projects/                 # 用户项目工作区
```

## 工作原理

```
主题/源文件
  │
  ▼
┌─────────────────────────────────────────┐
│  Phase A: 深度调研（7步独立工作流）       │
│  ├─ Step 1: 大纲生成（用户确认）          │
│  ├─ Step 2: 搜索需求拆分（AI分配）        │
│  ├─ Step 3: 逐页搜索（ChatGPT/Grok/     │
│  │          Perplexity 浏览器自动化）      │
│  ├─ Step 4: 汇总                         │
│  ├─ Step 5: 结构化分析 + 交叉验证         │
│  ├─ Step 6: 叙事构建（故事弧线）          │
│  └─ Step 7: 视觉策略                     │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  Phase B: 设计 + 生成                    │
│  ├─ 内容筛选 + 详细大纲                  │
│  ├─ 八项确认（交互式网页界面）            │
│  ├─ 双轨图片生成（AI 生图 + 网络素材）    │
│  ├─ SVG 逐页生成（实时预览）             │
│  ├─ 质量检查（排版/布局/动画验证）        │
│  ├─ 后处理 + PPTX 导出                   │
│  └─ 动画配置（按页面类型节奏）            │
└─────────────────────────────────────────┘
  │
  ▼
原生可编辑 PPTX
```

## 文档

| 文档 | 说明 |
|------|------|
| [SETUP.md](SETUP.md) | 首次使用指南（安装 + 配置 + 12 平台使用） |
| [SKILL.md](skills/ppt-master/SKILL.md) | 核心工作流（必须阅读） |
| [deep-research.md](skills/ppt-master/workflows/deep-research.md) | 深度调研编排器 |
| [research/](skills/ppt-master/workflows/research/) | 7 步独立调研工作流 |
| [ai-browser-setup.md](docs/ai-browser-setup.md) | 浏览器自动化配置（CDP Chrome） |
| [Canvas Formats](skills/ppt-master/references/canvas-formats.md) | 画布格式列表 |
| [Scripts & Tools](skills/ppt-master/scripts/README.md) | 工具脚本文档 |

## 更新日志

### 2026-06-28 — 深度调研重构 + 视频建议实施

**架构变更：**
- 🔄 **深度调研拆为 7 步独立工作流**（大纲→搜索拆分→多AI逐页搜索→汇总→分析→叙事→视觉策略），每步输出到独立文件夹
- 🗑️ **移除 topic-research 快速模式**，所有输入统一走深度调研
- 🤖 **新增多 AI 浏览器自动化**（`browse_ai.py`），通过 Playwright CDP 连接 Chrome，按内容类型分工：技术→ChatGPT，趋势→Grok，学术→Perplexity

**质量提升：**
- 📐 **排版稳定性检测**：svg_quality_checker.py 新增 3 项检查（布局溢出、元素间距、垂直分布）
- 🔧 **自动修正**：finalize_svg.py 新增 fix-layout 步骤（文字溢出自动缩减字号）
- 🎬 **动画节奏强制**：executor-base.md §18，按页面类型选择动画，禁止花哨效果
- 🖼️ **视觉优先页规则**：executor-base.md §19，封面等关键页用全屏 AI 背景
- 🎤 **发布会品牌预设**：`event_presentation`（暗色调、Apple keynote 风格）

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
