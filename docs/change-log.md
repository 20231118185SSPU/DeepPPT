# Change Log

> Record of modifications to workflow files, references, and scripts under `skills/ppt-master/`.
> Purpose: audit trail for AI-driven changes, regression tracking, and human review.
>
> **Mandatory**: every modification to `skills/ppt-master/scripts/`, `skills/ppt-master/workflows/`, or `skills/ppt-master/references/` MUST be logged here.

---

## Format

```
### YYYY-MM-DD — <short description>
- **Files**: <list of modified files>
- **Reason**: <why the change was made>
- **Before**: <key behavior before the change>
- **After**: <key behavior after the change>
- **Risk**: low / medium / high
- **Human reviewed**: yes / pending / N/A
```

---

## Log

### 2026-06-27 — Initial change log created
- **Files**: `docs/change-log.md`
- **Reason**: P1-3 from development manual — establish AI modification audit trail
- **Before**: No change tracking for workflow/script modifications
- **After**: All modifications logged with before/after behavior

### 2026-06-27 — PvZ 7 轮迭代问题固化：executor-base.md + deep-research.md 规则增强

- **Files**: `references/executor-base.md`, `workflows/deep-research.md`
- **Reason**: plants_vs_zombies 项目经 7 轮迭代发现的 8 个系统性问题（P1-P8），属于 deep-research 工作流和 Executor SVG 生成流程的结构性缺陷，需固化到工作流文件使未来所有 PPT 项目自动遵守
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks（修改前后一致，无回归）

**P1 — SVG 文字居中规则增强** (`executor-base.md` §10)
- **Before**: 仅规定 `text-anchor="middle"` + canvas center，无分栏布局特殊处理
- **After**: 新增"Split-layout centering"子节，含 5 种分栏比例的 center x 坐标表（3:7, 4:6, 7:3, 6:4, custom），公式 `text_x = (panel_left + panel_right) / 2`；禁止在分栏布局中使用 `x=640`

**P2 — 视觉装饰要求** (`executor-base.md` §17.1-17.2)
- **Before**: 无数据页/讲解页视觉增强强制规则，页面像 Word 文档
- **After**: 新增 §17.1"Visual Enrichment Rule"——数据页/讲解页/时间轴页必须有 ≥2/3 层增强（渐变背景、卡片阴影、装饰元素）；§17.2 卡片深度规则含 shadow filter 参数

**P3 — 遮罩/蒙版不透明度规则** (`executor-base.md` §17.3)
- **Before**: 无量化遮罩标准，opacity=0.88 不够
- **After**: 新增 §17.3"Overlay/Mask Opacity Rule"——深色底 ≥0.92，混合 ≥0.85，浅色底 ≥0.55；分栏过渡区遮罩延伸 ≥60px

**P4 — 字体最小值规则增强** (`executor-base.md` §14.2)
- **Before**: 仅 deep-dive body ≥22px、content body ≥20px、line height
- **After**: 新增全局绝对最小值 14px、脚注/页码 ≥12px（唯一例外）、数据页 body ≥16px、讲解页 body ≥18px、数据页卡片标签 ≥14px

**P5 — 网络素材搜集策略扩展** (`deep-research.md` §2.4)
- **Before**: 素材来源适配表含 5 种主题类型（风光/办公/历史/古籍/民俗）
- **After**: 新增 3 种类型——"游戏/IP/角色"（Playwright 优先→wiki→AI 降级）、"科幻/奇幻/动漫"、"小众亚文化/特定社群"

**P6 — ref/ 目录强制检查点** (`deep-research.md` §2.3a)
- **Before**: §2.3 仅提及 ref/ 目录，无强制执行机制
- **After**: 新增 §2.3a"Reference image collection — MANDATORY checkpoint"——Step 2 结束前 images/ref/ 必须 ≥1 张参考图，按主题类型给出来源优先级和最低数量，禁止空目录进入 Step 3

**P7 — 讲解页布局目录扩展** (`deep-research.md` §4.2b)
- **Before**: 4 种基础布局（left/right image-text, top-bottom, image-interspersed）
- **After**: 新增"Deep-dive layout catalog"含 7 种布局——新增"期刊风格时间轴""分支路径图""数据仪表盘""引言全页""对比分栏"；强制规则"连续 3 页不得使用相同布局"

**P8 — 垂直分布规则** (`executor-base.md` §14.5)
- **Before**: 无垂直空间利用规则，内容集中在上半部分
- **After**: 新增 §14.5"Vertical Distribution Rule"——safe area 分为 3 区（top/middle/bottom），每区 ≥20% 内容权重；底部 40% 全空 = 违规

- **Risk**: low（规则增强，不修改脚本逻辑）
- **Human reviewed**: pending
- **Risk**: low
- **Human reviewed**: N/A (new file)

### 2026-06-27 — 深度调研重构：7 步独立工作流 + 多 AI 浏览器自动化

- **Files**:
  - **新增**: `workflows/research/step1_outline.md`, `step2_search_plan.md`, `step3_search.md`, `step4_consolidate.md`, `step5_analysis.md`, `step6_narrative.md`, `step7_visual.md`
  - **新增**: `scripts/research/browse_ai.py`（Playwright 浏览器自动化搜索脚本）
  - **重写**: `workflows/deep-research.md`（从 824 行单体重写为 ~160 行编排器）
  - **删除**: `workflows/topic-research.md`（快速模式，被统一深度调研替代）
  - **修改**: `SKILL.md`, `docs/routing.md`, `docs/claude-reference.md`, `docs/faq.md`, `docs/zh/faq.md`, `docs/roadmap.md`, `docs/zh/roadmap.md`, `AGENTS.md`, `workflows/content-selection.md`, `references/strategist.md`
- **Reason**: 用户反馈深度调研流程耦合度高、各步骤不独立。参考 B 站视频"横评6大PPT开发Skill"的发布会准备流程，将研究拆为 7 个独立步骤，每步输出到独立文件夹，支持通过 Playwright 浏览器自动化调用不同 AI（ChatGPT/Grok/Perplexity）分工搜索
- **Before**: `deep-research.md` 为 824 行单体工作流（5 步耦合）；`topic-research.md` 为独立快速模式；搜索仅用内置 WebSearch
- **After**: `deep-research.md` 为编排器，协调 7 个独立步骤文件（`research/step1-7`）；每步输出到 `_research/stepN_name/`；`browse_ai.py` 支持通过 Playwright 自动化 ChatGPT/Grok/Perplexity 网页搜索；按内容类型分配 AI（技术→GPT，趋势→Grok，学术→Perplexity）；所有输入统一走深度调研
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks（修改前后一致，无回归）
- **Risk**: medium（架构重构，但仅涉及工作流 markdown 文件和新增脚本，未修改现有 Python 脚本逻辑）
- **Human reviewed**: pending

### 2026-06-28 — 视频建议实施：排版稳定性检测 + 布局自动修正 + 动画节奏规则 + 发布会品牌预设

- **Files**:
  - **修改**: `scripts/svg_quality_checker.py`（新增 3 个检查：layout_bounds, element_spacing, vertical_distribution）
  - **修改**: `scripts/finalize_svg.py`（新增 Step 5: fix-layout 自动修正文字溢出）
  - **修改**: `references/executor-base.md`（新增 §18 动画节奏强制规则, §19 视觉优先页规则）
  - **新增**: `templates/brands/event_presentation/design_spec.md`（发布会品牌预设）
  - **修改**: `templates/brands/brands_index.json`（新增 event_presentation 条目）
- **Reason**: B站视频横评中 PPT Master 排版评分 ★★☆、动画评分 ★★☆。分析发现 svg_quality_checker.py 完全没有布局边界/溢出/间距检测；executor-base.md 有生成规则但无自动化验证；动画节奏缺乏强制执行
- **Before**: 质量检查器无布局验证；finalize_svg.py 无自动修正能力；动画规则散落在 customize-animations.md 但 Executor 不强制参照；无发布会专用品牌预设
- **After**: svg_quality_checker.py 新增 check 12/13/14（文字溢出检测、元素间距检测、垂直分布检测）；finalize_svg.py 新增 fix-layout 步骤（文字溢出自动缩减字号）；executor-base.md 新增 §18（动画节奏按页面类型强制）和 §19（视觉优先页渲染策略）；event_presentation 品牌预设（暗色调、Apple keynote 风格）
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks（修改前后一致，无回归）
- **Risk**: low（新增检查和规则，不修改现有脚本核心逻辑）
- **Human reviewed**: pending

### 2026-06-28 — 深度调研执行闭环补齐：浏览器搜索降级 + 研究产物同步

- **Files**:
  - **修改**: `scripts/research/browse_ai.py`
  - **新增**: `scripts/research/sync_research_outputs.py`
  - **修改**: `workflows/deep-research.md`, `workflows/research/step3_search.md`, `workflows/research/step7_visual.md`
  - **修改**: `docs/change-log.md`
- **Reason**: 昨日 7 步深度调研重构已落地架构和文档，但浏览器搜索脚本缺少低质量重试、真实 fallback 记录、全部失败后的人工 WebSearch 交接；研究产物同步仍使用裸 `cp`，在 Windows 和目录缺失时不稳定
- **Before**: `browse_ai.py` 递归 fallback 但 manifest 只写目标 AI，低质量结果不会明确重试；三家浏览器 AI 全失败时文档暗示脚本可调用内置 WebSearch；hand-off 需要手写 `cp` / `cp -r`
- **After**: `browse_ai.py` 对空回复、少于 200 字、缺少来源 URL 的结果重试一次，manifest 记录 `ai_target` / `ai_used` / `fallback` / `fallback_chain` / `status` / `char_count` / `quality` / `output_file` / `image_suggestions` / `needs_manual_websearch`；全部失败时写出可复制人工 WebSearch prompt；新增同步脚本创建 `sources/`、`analysis/`、`images/ref/`、`images/web_assets/` 并复制研究产物；文档改为调用同步脚本并说明 WebSearch 是 Agent 手动降级能力
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks；专项 `py_compile` 覆盖 `scripts/research/browse_ai.py` 和 `scripts/research/sync_research_outputs.py`
- **Risk**: medium（修改新研究流程脚本和 manifest 结构；主 PPT 生成流程未改）
- **Human reviewed**: pending
