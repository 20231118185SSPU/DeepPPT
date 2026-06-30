---
description: 基于内容筛选结果，为每一页 PPT 生成包含文字要点、叙事功能和配图需求的结构化大纲。替换 Strategist 的粗略大纲步骤，产出可直接驱动设计规格和图文联动的 per-page 详细计划。
---

# 详细大纲生成工作流（Detailed Outline）

> 基于内容筛选结果（`content_selection.json`），为每一页 PPT 生成包含文字要点、叙事功能和配图需求的结构化大纲。产出的 `detailed_outline.json` 直接驱动 Strategist 的内容大纲（`§IX`）和图文联动工作流（`image-text-linking.md`）。

This workflow is **conditional**: it runs as part of the Strategist phase when `content_selection.json` exists (i.e., the source was a research report and the user completed content selection). When no content selection was performed, the Strategist generates its own outline as usual.

## When to Run

| Prerequisite | Action |
|---|---|
| `content_selection.json` exists and user confirmed selection | Run this workflow as Strategist Phase A |
| No `content_selection.json` (user-provided source file) | Skip — Strategist generates outline from design_spec.md §IX directly |

**Prerequisite**: content selection (from `content-selection.md`) has been confirmed. This workflow runs **before** the Eight Confirmations (SKILL.md Step 4 defines the order: detailed-outline → Eight Confirmations). The `color_scheme` and `font_plan` fields in the output JSON are left as empty `{}` and will be populated after the Eight Confirmations settle those decisions.

---

## Step 1: Load Inputs

Read the following files:

| File | Purpose |
|---|---|
| `<project>/content_selection.json` | Selected dimensions, suggested page count, density scores |
| `<project>/sources/research_report.md` | Full research narrative — only the sections matching selected dimensions are used |
| `design_spec.md` (§I–VIII, if already written) | Template/brand constraints from Eight Confirmations (may not exist yet — this workflow runs before Confirmations) |
| `spec_lock.md` (if already written) | Locked mode, rendering style, layout constraints |

**1.1 Filter research content**

From `research_report.md`, extract only the content belonging to the dimensions listed in `content_selection.json.selected_dimensions`. Each dimension's content becomes a **content block** — the raw material for one or more PPT pages.

**1.2 Determine page count**

Use `content_selection.json.suggested_pages` as the target page count. Adjust within ±2 pages if the narrative arc (Step 2) requires it, but do not exceed the `[8, 25]` range.

---

## Step 2: Design Narrative Arc

Arrange the selected dimensions into a coherent story that guides the audience from attention to understanding to action.

**2.1 Define the arc**

Assign each dimension to a **narrative position** in the arc:

| Position | Role | Page sequence |
|---|---|---|
| `hook` | Grab attention with a surprising fact or vivid case | First content page |
| `expand` | Develop context, history, or definitions | Early-to-mid |
| `prove` | Present evidence, data, core arguments | Mid |
| `compare` | Contrast perspectives, alternatives, or trade-offs | Mid-to-late |
| `summarize` | Synthesize takeaways, call to action | Last content page |

**2.2 Arc constraints**

| Constraint | Rule |
|---|---|
| First content page | MUST be `hook` |
| Last content page | MUST be `summarize` |
| No consecutive same function | Two adjacent content pages must not share the same `narrative_function` |
| Minimum functions used | ≥3 distinct functions across all content pages |
| `prove` and `expand` | May appear multiple times; `hook` and `summarize` appear exactly once |

**2.3 Write arc summary**

Produce a one-sentence narrative arc description (≤80 chars) that captures the story flow. Example: "从市场规模的惊人数据切入，展开技术路径对比，用临床证据论证，最后展望未来趋势"

---

## Step 3: Generate Per-Page Plan

For each page in the target page count, generate a structured plan with the following fields:

**3.1 Required fields per page**

| Field | Type | Constraint |
|---|---|---|
| `page_number` | int | Sequential, starting from 1 |
| `page_type` | enum | `cover` \| `toc` \| `chapter` \| `content` \| `deep_dive` \| `comparison` \| `data` \| `timeline` \| `quote` \| `synthesis` \| `ending` |
| `layout_suggestion` | string | Which layout template variant to use (from [`templates/layouts/content_pages/`](../templates/layouts/content_pages/) library); empty string for cover/ending. Available values by scene: |

**可用 `layout_suggestion` 值**（按场景分类）：

| 场景 | 可用版式 |
|------|---------|
| `academic` | `03_content_data_cards`, `03_content_table_compare`, `03_content_timeline`, `03_content_process_steps`, `03_content_bullet_cards`, `03_content_image_text`, `03_content_chart_bar`, `03_content_chart_line`, `03_content_chart_pie`, `03_content_chart_radar` |
| `business` | `03_content_kpi_grid`, `03_content_stat_highlight`, `03_content_image_hero`, `03_content_process_cards`, `03_content_comparison`, `03_content_three_columns` |
| `data_analysis` | `03_content_chart_bar`, `03_content_chart_line`, `03_content_chart_pie`, `03_content_chart_radar`, `03_content_data_dashboard` |
| `report` | `03_content_milestone_timeline`, `03_content_data_dashboard`, `03_content_text_with_sidebar`, `03_content_progress_cards`, `03_content_icon_grid`, `03_content_quote_stats` |
| `tech_sharing` | `03_content_code`, `03_content_diff`, `03_content_terminal`, `03_content_flow_diagram`, `03_content_arch_diagram`, `03_content_mindmap` |
| `project_management` | `03_content_roadmap`, `03_content_gantt`, `03_content_todo_checklist`, `03_content_timeline` |
| `creative` | `03_content_image_hero`, `03_content_big_quote`, `03_content_icon_grid`, `03_content_three_columns` |
| `_shared` | `03_content_big_quote`, `03_content_cta`, `03_content_thanks` |

> 一个版式可属于多个场景（如 `03_content_timeline` 同时出现在 academic 和 project_management）。Strategist 根据页面内容选择最匹配的版式，不限于单一场景。

| `core_argument` | string | ≤50 chars. The ONE thing this page must communicate |
| `content_bullets` | string[] | 3–5 items, each ≤60 chars. Key points on this page |
| `narrative_function` | enum | `hook` \| `expand` \| `prove` \| `compare` \| `summarize`; empty string for cover/ending |
| `visual_need` | object | See §3.2 below |
| `source_dimension` | string | Which selected dimension this page draws from (must match a `title` in `content_selection.json`) |
| `layout_plan` | object | **Pre-design layout before image generation.** See §3.3 below |
| `content_mode` | enum | `text-primary` \| `image-primary` \| `image_with_text`. Determines image generation strategy. See §3.4 below |
| `paired_with` | string | For deep-dive pages, the preceding content page id; for content pages, the follow-up deep-dive page id or empty with reason |
| `evidence_refs` | string[] | Source IDs / URLs / fact IDs supporting this page |
| `page_description` | string | ≤100 chars. One-sentence description of what the complete page looks like when finished — layout, visual elements, content placement |
| `text_hierarchy` | object | Explicit text breakdown: `{"title": "...", "subtitle": "...", "body": ["..."], "annotation": "..."}`. Draft content for each text level on this page |
| `element_list` | string[] | Enumerate ALL visual elements on this page: title, subtitle, body_bullets, chart_bar, icon_decoration, hero_image, source_annotation, etc. |
| `layout_ascii` | string | Optional. ASCII representation of the page layout, e.g. `[Title]\n[Image | Text]\n[Footer]` |
| `persuasion_action` | enum | Optional. `define` \| `prove` \| `compare` \| `sequence` \| `structure` \| `summarize` \| `emotionalize` — 本页的说服动作 |
| `content_relation` | enum | Optional. `single_claim` \| `parallel_set` \| `weighted_set` \| `compare` \| `sequence` \| `hierarchy` \| `evidence_chain` \| `matrix` \| `summary` — 内容元素间的关系 |
| `information_anchor` | string | Optional. ≤30 chars. 本页信息主角（一个数字？一张图？一个对比关系？） |
| `reading_path` | string | Optional. ≤80 chars. 读者阅读路径描述：第一眼→证据→记住什么 |
| `why_not_alternatives` | string | Optional. ≤100 chars. 为什么没有选择 2 个最诱惑的替代版式 |
| `anti_laziness_check` | string | Optional. ≤80 chars. 证明本页不是偷懒选了万能三卡或对称分栏 |

**3.1b Layout Thinking（推荐）**

> 借鉴 PPT Hell 的版式思考框架。对于内容页（`content` / `deep_dive` / `comparison` / `data`），推荐填写以上 6 个字段，帮助 Strategist 避免版式偷懒。这些字段为可选——当来源是简单用户文件（非研究报告）时可省略。
>
> 核心问题：这一页要完成什么说服任务？内容之间是什么关系？谁是信息主角？读者的阅读路径如何？为什么这个版式比另外两个选项更对？
>
> **`persuasion_action` 枚举**:
> - `define` — 定义问题、对象、边界或概念
> - `prove` — 用证据证明一个判断
> - `compare` — 解释对象/状态/方案之间的差异
> - `sequence` — 表达时间、步骤、流程或阶段
> - `structure` — 建立模型、层级或系统
> - `summarize` — 压缩为决策、建议或结论
> - `emotionalize` — 制造停顿、情绪、转折或记忆点
>
> **`content_relation` 枚举**:
> - `single_claim` — 一个强判断需要空间
> - `parallel_set` — 多项地位相等
> - `weighted_set` — 多项相关但不等权
> - `compare` — 有可比维度
> - `sequence` — 时间/流程很重要
> - `hierarchy` — 层级/嵌套逻辑很重要
> - `evidence_chain` — 判断需要数据/案例证明
> - `matrix` — 两条轴线解释内容
> - `summary` — 复杂材料收束为行动

> **命名约定说明**: `layout_suggestion` 使用 `03_content_*` 格式（匹配 SVG 文件名），而 content_pages JSON 中的 `layout_type` 字段使用描述性名称（如 `data_cards_left_text_right`）。两者是同一版式的不同标识符：Strategist 输出 `layout_suggestion`，Executor 通过 `layout_type` 读取 JSON 配置。

**3.2 `visual_need` sub-object**

Every content and chapter page must include a `visual_need` object:

| Field | Type | Constraint |
|---|---|---|
| `image_type` | enum | `ai_generated` \| `stock_search` \| `chart` \| `icon` |
| `image_description` | string | ≤50 chars. Describes the image for AI generation or web search |
| `text_image_link` | string | ≤30 chars. How the image supports the `core_argument` |
| `image_slot_size` | object | `{"width": N, "height": N}` — target pixel dimensions for AI image generation. Must match the template's `image_slots` entry |
| `reference_image_required` | bool | `true` when the image depicts people / products / objects / places / IP-specific subjects |
| `reference_image_query` | string | Concrete query for collecting the reference image |
| `asset_file` | string | Existing web asset filename for information pages, or empty before acquisition |

For cover and ending pages, `visual_need` may use `ai_generated` with a thematic description.

**3.3 `layout_plan` sub-object**

Every content page MUST have a `layout_plan` determined BEFORE image generation:

| Field | Type | Constraint |
|---|---|---|
| `template` | string | Which template variant to use (same as `layout_suggestion`) |
| `text_area` | object | `{"position": "left"/"right"/"top"/"bottom"/"center", "width": N, "alignment": "start"/"middle"}` |
| `image_area` | object | `{"position": "left"/"right"/"top"/"bottom"/"full", "width": N, "height": N}` |
| `visual_weight` | enum | `text-dominant` (≤20% image) \| `balanced` (40-60% image) \| `image-dominant` (≥80% image) |
| `rationale` | string | ≤50 chars. Why this layout fits the content |

**3.4 `content_mode` enum**

| Mode | Definition | When to use | Image generation behavior |
|---|---|---|---|
| `text-primary` | Text/data is the main content | KPI, tables, bullet lists, code, charts | Images are decorative or chart-based; `text_policy: none` |
| `image-primary` | Image is the main voice | Hero moments, visual impact pages | Full-canvas image; `text_policy: none` for non-content pages |
| `image_with_text` | Image WITH embedded explanation text | Flow explanations, architecture, case studies, process demos | Prompt describes the explanation content; `text_policy: embedded`; image carries the information |

**3.3 Page type distribution**

| Page type | Typical count | Notes |
|---|---|---|
| `cover` | 1 | Always page 1 |
| `chapter` | 1–3 | Section transitions; depends on dimension count |
| `content` | 5–18 | Bulk of the deck; one or more per dimension |
| `ending` | 1 | Always the last page |

**3.4 Content allocation rules**

| Rule | Description |
|---|---|
| Density-proportional allocation | Dimensions with higher `density` score get more pages |
| Minimum pages per dimension | ≥1 page per selected dimension |
| Maximum pages per dimension | ≤5 pages (avoid overweighting) |
| Deep-dive pages | For dimensions with `density ≥ 7`, consider adding an `expand` or `prove` page after the initial content page |

**Hard rule — content/deep-dive pairing**: every substantive content page must be followed by a `deep_dive`, `comparison`, `data`, `timeline`, or `quote` page unless the page is explicitly a transition / synthesis page. This is what keeps the presenter from running out of material after user content selection.

**Hard rule — evidence per page**: every content and deep-dive page must cite at least 2 evidence refs. Pages that cannot cite evidence must be rewritten, merged, or sent back to research.

**Hard rule — layout before image**: `layout_plan.image_area` and `visual_need.image_slot_size` must be filled before any image prompt or web query is written.

---

## Step 4: Output

Write `<project>/detailed_outline.json`:

```json
{
  "pages": [
    {
      "page_number": 1,
      "page_type": "cover",
      "layout_suggestion": "",
      "core_argument": "",
      "content_bullets": [],
      "narrative_function": "",
      "visual_need": {
        "image_type": "ai_generated",
        "image_description": "",
        "text_image_link": ""
      },
      "source_dimension": ""
    },
    {
      "page_number": 2,
      "page_type": "content",
      "layout_suggestion": "03_content_chart_bar",
      "core_argument": "新能源汽车市场规模翻5倍",
      "content_bullets": [
        "2020年全球销量120万辆",
        "2025年预计突破680万辆",
        "中国市场份额超60%"
      ],
      "narrative_function": "hook",
      "visual_need": {
        "image_type": "chart",
        "image_description": "柱状图展示2020-2025年全球新能源汽车销量增长趋势",
        "text_image_link": "数据可视化支撑市场翻倍论点",
        "image_slot_size": {"width": 1160, "height": 425},
        "reference_image_required": false,
        "reference_image_query": "",
        "asset_file": ""
      },
      "layout_plan": {
        "template": "03_content_chart_bar",
        "text_area": {"position": "top", "width": 1160, "alignment": "start"},
        "image_area": {"position": "center", "width": 1160, "height": 425},
        "visual_weight": "balanced",
        "rationale": "柱状图为主，标题和要点在顶部"
      },
      "content_mode": "text-primary",
      "source_dimension": "市场规模与增长",
      "paired_with": "P03",
      "evidence_refs": ["S01", "S03"],
      "page_description": "柱状图占据页面中央，上方标题和三条要点总结市场翻倍论点，底部注明数据来源",
      "text_hierarchy": {
        "title": "新能源汽车市场规模翻5倍",
        "subtitle": "2020-2025年全球销量增长趋势",
        "body": ["2020年全球销量120万辆", "2025年预计突破680万辆", "中国市场份额超60%"],
        "annotation": "数据来源：IEA Global EV Data Explorer 2025"
      },
      "element_list": ["title", "subtitle", "chart_bar", "body_bullets_x3", "source_annotation"],
      "layout_ascii": "[Title + Subtitle]\n[   Bar Chart   ]\n[Source annotation]"
    }
  ],
  "narrative_arc": "从市场规模的惊人数据切入，展开技术路径对比，用临床证据论证，最后展望未来趋势",
  "total_pages": 12,
  "color_scheme": {},
  "font_plan": {}
}
```

**Field notes**:

| Field | Description |
|---|---|
| `color_scheme` | Populated after Eight Confirmations; left as empty `{}` if Confirmations have not run yet |
| `font_plan` | Populated after Eight Confirmations; left as empty `{}` if Confirmations have not run yet |
| `narrative_arc` | One-sentence summary from Step 2.3 |
| `total_pages` | Actual page count (may differ from `suggested_pages` by ±2) |

---

## Step 5: Feed into Strategist

The `detailed_outline.json` becomes the primary input for the Strategist's design spec generation:

**5.1 Content outline (`§IX`)**

The Strategist reads `detailed_outline.json.pages` and writes `§IX Content Outline` of `design_spec.md` directly from it. Each page entry maps 1:1 to an outline row. The Strategist does not re-derive the outline — it translates the structured plan into the spec's prose format.

**5.2 Image strategy (`§VIII`)**

The Strategist reads `detailed_outline.json.pages[].visual_need` and writes the image acquisition table in `§VIII`. Each `visual_need.image_type` maps to an `Acquire Via` column:

| `image_type` | `Acquire Via` |
|---|---|
| `ai_generated` | `ai` |
| `stock_search` | `web` |
| `chart` | `executor` (rendered natively in SVG) |
| `icon` | `icon` (from icon library) |

**5.3 Page rhythm (`spec_lock.md`)**

The Strategist reads `narrative_function` values and assigns page rhythm labels:

| `narrative_function` | Rhythm |
|---|---|
| `hook` | `anchor` |
| `expand` | `dense` |
| `prove` | `anchor` |
| `compare` | `dense` |
| `summarize` | `anchor` |
| (cover/ending) | `breathing` |

---

## Validation

⛔ **BLOCKING**: verify the output before writing `detailed_outline.json`.

| Check | Threshold | Action on failure |
|---|---|---|
| Every page has all 5 required fields + `visual_need` sub-object | 100% | Fill missing fields; abort if `core_argument` cannot be derived |
| Every content/deep-dive page has `evidence_refs` | >=2 refs | Return to research or merge page |
| Every substantive content page has a follow-up deep-dive page | 100% | Add deep-dive page or mark reason |
| Every image page has `layout_plan.image_area` before prompt generation | 100% | Fill layout first |
| No consecutive pages share the same `narrative_function` | 0 violations | Swap adjacent pages or reassign functions |
| `visual_need.image_type = "chart"` requires `image_description` to include chart type + data source | 100% | Add chart type (e.g., "柱状图") and data source to description |
| `content_bullets` count per page | 3–5 (each ≤60 chars) | Merge thin bullets or split dense ones |
| `core_argument` length | ≤50 chars | Compress; use abbreviations if needed |
| Every content page has `page_description` | 100% | Fill from core_argument + layout_plan |
| Every content page has `text_hierarchy` with at least title and body | 100% | Draft from content_bullets |
| Every content page has `element_list` with ≥3 items | 100% | Enumerate from layout_plan + visual_need |
| `source_dimension` matches a `title` in `content_selection.json` | 100% | Correct the dimension name |
| First content page has `narrative_function = "hook"` | Required | Reassign |
| Last content page has `narrative_function = "summarize"` | Required | Reassign |

**Fallback on validation failure**: most failures are self-repairable (fill, merge, reassign). If `core_argument` cannot be derived for multiple pages despite attempts, the research content is too thin for this page structure — return to the `content-selection` workflow and either drop the underspecified dimension or re-run `deep-research` Step 5 (analysis) for that dimension. Do NOT skip the detailed outline and proceed to Eight Confirmations with an empty or partial `detailed_outline.json`; either produce a complete file or omit it entirely (the pipeline falls back to Strategist's classic outline generation when the file is absent).

---

## Output

| Artifact | Path | Purpose |
|---|---|---|
| Detailed outline | `<project>/detailed_outline.json` | Feeds Strategist §IX, §VIII, and spec_lock.md; drives `image-text-linking.md` |

---

## Integration Points

| Direction | Target | Data |
|---|---|---|
| **Reads from** | `<project>/content_selection.json` | Selected dimensions, page count, density scores |
| **Reads from** | `<project>/sources/research_report.md` | Research content for selected dimensions |
| **Feeds into** | Eight Confirmations | Content basis (page count, outline structure) for confirmation decisions |
| **Feeds into** | Strategist (design_spec.md §IX) | Per-page content outline |
| **Feeds into** | Strategist (design_spec.md §VIII) | Image acquisition table |
| **Feeds into** | Strategist (spec_lock.md) | Page rhythm labels |
| **Feeds into** | `image-text-linking.md` workflow | Page context for prompt enhancement |
