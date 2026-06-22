# DeepPPT — AI 深度调研驱动的 PPT 生成系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 基于 [ppt-master](https://github.com/hugohe3/ppt-master) 扩展开发，增加深度调研、叙事驱动模板、双轨图片生成等能力。

English | [中文](#简介)

---

## 简介

DeepPPT 是一个端到端的 AI PPT 生成系统。给定一个主题，它会自动完成深度调研、结构化分析、叙事构建、视觉身份提取、AI 图片生成，最终产出一份**原生可编辑的 PPTX**。

**核心差异化**（相比上游 ppt-master）：

| 能力 | ppt-master (上游) | DeepPPT (本项目) |
|------|-------------------|------------------|
| 输入 | 源文件 (PDF/DOCX/URL) | 仅需一个主题 |
| 调研 | 无 / 快速搜索 | 多维深度调研 + 交叉验证 |
| 叙事 | 模板化大纲 | 故事弧线 + 转折点 + 过渡标记 |
| 视觉 | 通用设计规范 | 从调研内容中提取视觉身份 |
| 页面类型 | 6 种基础类型 | 11 种（含讲解页、对比页、数据页、时间线页等） |
| 图片策略 | 单轨（AI 或网络） | 双轨——视觉页 AI 生图 + 信息页网络素材 |
| 内容深度 | 单页展示 | 内容页 + 讲解页配对，每页都可讲 |

## 与 ppt-master 的关系

本项目是 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 的**扩展分支**。

- **上游 ppt-master** 提供了完整的 PPT 生成管线：源文件转换 → 项目管理 → 八项确认 → SVG 逐页生成 → 后处理 → PPTX 导出
- **DeepPPT** 在此基础上新增了：
  - [`deep-research`](skills/ppt-master/workflows/deep-research.md) 工作流——多维搜索、结构化分析、叙事构建、视觉策略
  - [`ppt-deep-research`](skills/ppt-master/workflows/deep-research.md) Skill——端到端一键流程，从主题到 PPTX
  - [`story_driven`](skills/ppt-master/templates/layouts/story_driven/) 布局模板——封面/目录/过渡/内容/讲解/金句/对比/数据/时间线/全图/封底
  - [`img2img-support`](skills/ppt-master/workflows/img2img-support.md) 文档——图生图策略说明
  - 多后端 AI 图片生成（OpenAI / Gemini / Replicate / Stability / 通义千问 / 智谱 / SiliconFlow 等 15+ 后端）

所有上游管线脚本（`project_manager.py`、`svg_editor/`、`confirm_ui/`、`finalize_svg.py`、`svg_to_pptx.py` 等）保持不变，DeepPPT 的扩展通过新增工作流和模板实现，不修改任何现有脚本。

**感谢上游作者 [Hugo He](https://www.hehugo.com/) 的开创性工作。** 如果本项目对你有帮助，也请给上游 [ppt-master](https://github.com/hugohe3/ppt-master) 一个 ⭐。

## 快速开始

### 1. 环境准备

| 依赖 | 必需 | 说明 |
|------|:----:|------|
| [Python](https://www.python.org/downloads/) 3.10+ | ✅ | 唯一需要安装的运行时 |
| [Git](https://git-scm.com/downloads) | ✅ | 克隆仓库 |

### 2. 安装

```bash
git clone https://github.com/<your-username>/DeepPPT.git
cd DeepPPT
pip install -r requirements.txt
```

### 3. 配置 AI 图片生成（可选）

复制环境变量模板并填入 API Key：

```bash
cp .env.example .env
# 编辑 .env，设置 IMAGE_BACKEND 和对应的 API_KEY
```

支持的图片后端：`openai` / `gemini` / `replicate` / `stability` / `qwen` / `zhipu` / `siliconflow` / `volcengine` / `minimax` / `modelscope` / `fal` / `bfl` / `openrouter` / `ideogram` 等。

### 4. 使用

**方式一：深度调研模式**（推荐——只需一个主题）

在任何支持 Agent 的 AI IDE（Claude Code / Cursor / VS Code Copilot）中打开项目目录，然后说：

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
│   │   └── source_to_md/     # 源文件转换器
│   ├── templates/            # 布局模板、图表模板、图标库
│   │   └── layouts/story_driven/  # 叙事驱动模板 (DeepPPT 新增)
│   └── workflows/            # 独立工作流
│       ├── deep-research.md  # 深度调研工作流 (DeepPPT 新增)
│       ├── live-preview.md   # 实时预览
│       └── ...
├── docs/                     # 文档
├── examples/                 # 示例项目
└── projects/                 # 用户项目工作区
```

## 工作原理

```
主题/源文件
  │
  ▼
┌─────────────────────────────────────────┐
│  Phase A: 调研 + 设计                    │
│  ├─ 深度调研（多维搜索 + 交叉验证）       │
│  ├─ 叙事构建（故事弧线 + 页面节奏）       │
│  ├─ 视觉身份提取（从内容推导配色）         │
│  ├─ 八项确认（交互式网页界面）             │
│  └─ 设计规范 + 执行锁                     │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  Phase B: 生成 + 导出                    │
│  ├─ 双轨图片生成（AI 生图 + 网络素材）     │
│  ├─ SVG 逐页生成（实时预览）              │
│  ├─ 质量检查                              │
│  ├─ 后处理 + PPTX 导出                    │
│  └─ 动画配置（可选）                      │
└─────────────────────────────────────────┘
  │
  ▼
原生可编辑 PPTX
```

## 文档

| 文档 | 说明 |
|------|------|
| [SKILL.md](skills/ppt-master/SKILL.md) | 核心工作流（必须阅读） |
| [deep-research.md](skills/ppt-master/workflows/deep-research.md) | 深度调研工作流 |
| [Canvas Formats](skills/ppt-master/references/canvas-formats.md) | 画布格式列表 |
| [Scripts & Tools](skills/ppt-master/scripts/README.md) | 工具脚本文档 |

## 致谢

- **上游项目**：[ppt-master](https://github.com/hugohe3/ppt-master) by [Hugo He](https://www.hehugo.com/) — 提供了完整的 PPT 生成管线架构
- **图标库**：[Tabler Icons](https://github.com/tabler/tabler-icons) · [Simple Icons](https://github.com/simple-icons/simple-icons) · [Phosphor Icons](https://github.com/phosphor-icons/core)
- **图片资源**：[SVG Repo](https://www.svgrepo.com/) · [Pexels](https://www.pexels.com/) · [Pixabay](https://pixabay.com/)

## 许可证

[MIT](LICENSE) — 与上游 ppt-master 保持一致。使用本项目时请注明基于 [ppt-master](https://github.com/hugohe3/ppt-master) 开发。
