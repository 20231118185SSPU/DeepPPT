# DeepPPT — 首次使用指南 / Getting Started

## 环境要求

| 项目 | 最低版本 | 必需/可选 |
|------|---------|----------|
| Python | ≥3.10 | 必需 |
| pip | 最新版 | 必需 |
| Git | 任意 | 必需 |
| Playwright + Chromium | 最新版 | 可选（浏览器截图） |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/20231118185SSPU/DeepPPT.git
cd DeepPPT
```

### 2. 安装依赖

**一键安装（推荐）**：

```bash
# Linux / Mac
bash scripts/setup/install_deps.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts/setup/install_deps.ps1
```

**手动安装**：

```bash
# 必需
pip install python-pptx Pillow requests beautifulsoup4 lxml

# 可选：SVG 预览 + RSS 采集
pip install cairosvg feedparser

# 可选：浏览器截图（网络图片采集）
pip install playwright
python -m playwright install chromium
```

**检查依赖**：

```bash
python3 scripts/setup/check_deps.py          # 表格模式
python3 scripts/setup/check_deps.py --quiet   # 只显示缺失项
python3 scripts/setup/check_deps.py --json    # JSON 输出
python3 scripts/setup/check_deps.py --install # 自动安装缺失依赖
```

### 3. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env`，至少设置一组 AI 图片后端：

```env
IMAGE_BACKEND=openai
OPENAI_API_KEY=sk-xxx
```

支持的后端：`openai` / `gemini` / `qwen` / `zhipu` / `volcengine` / `minimax`

可选图片搜索 API Key（零配置源 Openverse/Wikimedia/NASA/Smithsonian 无需 Key）：
- `PEXELS_API_KEY` — https://www.pexels.com/api/
- `PIXABAY_API_KEY` — https://pixabay.com/api/docs/
- `UNSPLASH_ACCESS_KEY` — https://unsplash.com/developers
- `FLICKR_API_KEY` — https://www.flickr.com/services/apps/create/

## AI Agent 平台使用说明

DeepPPT 为以下 12 个主流 AI Agent 平台提供了项目级配置：

### P0 — 核心平台

| 平台 | 使用方式 |
|------|---------|
| **Claude Code** | 直接打开项目目录，自动读取 `CLAUDE.md`。输入 `/ppt-deep-research` 触发完整流程 |
| **Cursor** | 打开项目，`.cursor/rules/deep-ppt.md` 自动生效。在 Chat 或 Composer 中描述 PPT 需求 |
| **Windsurf** | 打开项目，`.windsurfrules` 自动生效。在 Cascade 中描述 PPT 需求 |
| **GitHub Copilot** | 在 VS Code 中打开项目，`.github/copilot-instructions.md` 自动加载到 Copilot Chat |
| **OpenAI Codex CLI** | 在项目目录运行 `codex`，自动读取 `AGENTS.md` |
| **Pi** | 在项目目录运行 `pi`，自动读取 `AGENTS.md` |

### P1 — 扩展平台

| 平台 | 使用方式 |
|------|---------|
| **Cline** | VS Code 扩展，`.clinerules` 自动生效 |
| **Roo Code** | VS Code 扩展，`.roo/rules` 自动生效 |
| **Aider** | 项目目录运行 `aider`，`.aider.conf.yml` 自动读取 SKILL.md 和 CLAUDE.md |

### P2 — 补充平台

| 平台 | 使用方式 |
|------|---------|
| **Amazon Q Developer** | VS Code 扩展，`.amazonq/rules/deep-ppt.md` 自动生效 |
| **Amazon Kiro** | Kiro IDE，`.kiro/steering/deep-ppt.md` 自动生效 |
| **JetBrains Junie** | JetBrains IDE，`junie/guidelines.md` 自动加载 |
| **Hermes Agent** | 在项目目录运行 Hermes CLI，读取 `hermes.md` |

## 使用流程

### 有源文件（PDF/DOCX/URL）

1. 用任意 Agent 打开项目
2. 发送：`帮我把这个 PDF 做成 PPT`（附文件）
3. Agent 会自动走 SKILL.md 主管线

### 只有主题（无源文件）

1. 用任意 Agent 打开项目
2. 发送：`做一个关于XX的PPT` / `/ppt-deep-research`
3. Agent 先执行深度调研，再走主管线

### 继续之前的项目（Split Mode）

1. 发送：`继续生成 projects/<project_name>`
2. Agent 进入 Phase B（SVG 生成 + 导出）

## 常见问题

**Q: `python3` 命令找不到怎么办？**
A: Windows 上用 `python` 替代 `python3`。详见 SKILL.md 中的 Windows note。

**Q: Playwright 安装失败？**
A: Playwright 是可选依赖。如果安装失败，网络图片采集会降级为 curl 直接下载或 AI 生成。不影响核心流程。

**Q: 没有配置图片 API Key 能用吗？**
A: 可以。零配置图片源（Openverse、Wikimedia、NASA、Smithsonian）无需 Key。AI 生图需要至少一组后端 Key。

**Q: 导出的 PPTX 在哪里？**
A: `projects/<project_name>/exports/` 目录下。

**Q: 如何自定义 PPT 的配色和字体？**
A: 在八项确认（Step 4）中修改。支持交互式网页确认或聊天确认两种方式。

**Q: 支持哪些输入格式？**
A: PDF、DOCX、XLSX、PPTX、EPUB、HTML、LaTeX、Markdown、网页 URL、纯文本描述。
