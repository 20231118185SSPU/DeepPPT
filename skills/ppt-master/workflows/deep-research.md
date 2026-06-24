---
description: Deep research workflow — multi-source discovery, structured analysis, narrative construction, and visual strategy. Produces enriched Markdown + analysis artifacts that feed SKILL.md Step 2's import-sources. Run when the user requests deep research or high content quality.
---

# Deep Research Workflow

> Standalone pre-processing step. Run before SKILL.md Step 1 when the user supplies only a topic but demands thorough, well-sourced, narrative-driven content. Output is a story-arc research document + structured analysis + visual strategy + image folder, all shaped to feed `project_manager.py import-sources` directly.

This workflow is **independent**: it owns the source-acquisition step when no file exists; subsequent SKILL.md steps proceed normally with the produced materials as input. For quick, general-knowledge research, use [`topic-research.md`](./topic-research.md) instead.

## When to Run

| User-supplied input | Action |
|---|---|
| Topic + "深度调研" / "deep research" / "内容质量优先" | Run this workflow |
| Topic + complex, multi-perspective subject matter | Run this workflow |
| Topic only, general knowledge sufficient | Use [`topic-research.md`](./topic-research.md) |
| ≥1 page of substantive content already in chat | Skip — feed chat content into SKILL.md Step 1 directly |
| Source file attached (PDF / DOCX / URL / Markdown) | Skip — go to SKILL.md Step 1 source converter |

### Project folder structure

All output artifacts must reside inside the single project folder created by `project_manager.py init`. No scatter across `projects/`.

```
projects/<project_slug>/          ← single source of truth
├── sources/                      ← original source files (import-sources moves these in)
├── analysis/                     ← structured analysis outputs
│   ├── research_analysis.json    ← cross-verified facts, data points, source registry
│   └── visual_strategy.json      ← color palette, page types, image strategy
├── research_report.md            ← full narrative Markdown (output of Step 4)
├── design_spec.md                ← design specification (Strategist output)
├── spec_lock.md                  ← machine-readable execution contract
├── images/
│   ├── *.png                     ← AI-generated visual page images
│   ├── web_assets/               ← web-sourced images + AI fallback images
│   └── ref/                      ← reference images (optional)
├── svg_output/                   ← SVG files
├── notes/                        ← speaker notes
├── templates/                    ← layout templates (if any)
└── exports/                      ← final PPTX
```

**Hard rules**:
- Do NOT create multiple folders for the same task under `projects/` (e.g., `xxx_analysis/` and `xxx_ppt169_/` must not coexist)
- Research reports (`research_report.md`) and narrative copy must be saved INSIDE the project folder, not in `projects/` root
- The folder name from `project_manager.py init` is the project's single canonical identifier
- **All artifacts write directly into the project directory from Step 1 onward** — no staging directories, no sibling folders, no copy-in-later

> **Single-phase artifact flow**: `project_manager.py init` runs at Step 1 (scope confirmed), producing the canonical `<project>` path. Steps 2–5 write analysis, images, and narrative directly into `<project>/analysis/`, `<project>/images/`, and `<project>/sources/`. No staging, no cleanup step.

---

## Step 1: Confirm scope

⛔ **BLOCKING**: confirm scope as a single bundled clarifier. Skip when the user's initial message already covers it.

| Item | Default if user did not specify |
|---|---|
| Topic | (from user input) |
| Scope / focus | Broad overview |
| Depth | Expert-level, multi-perspective |
| Output language | Match user input |
| Slug for files (`<topic_slug>`) | snake_case English identifier derived from topic |
| Target audience | General audience (adjust search depth) |
| PPT page count hint | 15-25 pages (affects search breadth) |

**Forbidden — itemized confirmation**: do NOT ask each row separately. One bundled clarifier or none.

### 1.1 Initialize project directory

⛔ **BLOCKING**: immediately after scope confirmation, create the canonical project directory. All subsequent steps write directly into it — no staging directories.

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
```

Save the returned path as `<project>`. Create subdirectories for research artifacts:

```bash
mkdir -p <project>/analysis
mkdir -p <project>/images/ref
mkdir -p <project>/images/web_assets
```

All Steps 2–5 use `<project>` as the base path. No `projects/<topic_slug>/` or `projects/<topic_slug>_analysis/` directories are created.

---

## Step 2: Multi-dimensional search

⛔ **BLOCKING**: present the search plan to the user before executing. Proceed on approval.

### 2.0 Depth contract（调研深度合约）

**Hard rule**: deep-research 的核心价值是"深度"。以下是最低标准，不可协商：

| 指标 | 最低要求 | 说明 |
|------|---------|------|
| 搜索维度 | 4-6 个 | 每个维度代表一个独立视角 |
| 每维度搜索轮次 | ≥3 轮 | 广搜→深挖→交叉验证 |
| 每维度 Tier 1-2 来源 | ≥2 个 | 官方/权威来源不可缺 |
| 总来源数 | ≥15 个 | 含所有层级 |
| 交叉验证事实 | ≥8 个 | 同一事实被 ≥2 个独立来源确认 |
| 结构化数据点 | ≥10 个 | 统计数字、时间线事件、对比项、引言 |
| 调研报告正文 | ≥3000 字 | 不含来源列表和标记注释 |
| 每个叙事章节 | ≥400 字 | §1-§6 每章必须有足够的展开深度 |

**低于以上任何一项 = 调研不达标，必须补充搜索后再进入 Step 3。**

### 2.1 Generate search plan

Break the topic into 3-6 **search dimensions** — each represents an independent angle on the subject. Present as a table:

| Dimension | Rationale | Target source tiers |
|---|---|---|
| e.g. Background & history | Context for the audience | Tier 1-2 (encyclopedias, official) |
| e.g. Core mechanism / key players | The subject's essential structure | Tier 1-2 (academic, institutional) |
| e.g. Real-world cases / applications | Concrete evidence | Tier 2-3 (news, reports) |
| e.g. Controversy / competing views | Multi-perspective depth | Tier 3 (opinion, analysis) |
| e.g. Data & statistics | Quantitative backbone | Tier 2 (institutional data) |
| e.g. Future trends / expert outlook | Forward-looking narrative | Tier 2-3 (expert commentary) |

### 2.2 Execute search

**Tools** — use the web search and web fetch tools the current IDE provides:

| IDE | Web search | Web fetch |
|---|---|---|
| Claude Code | `WebSearch` | `WebFetch` |
| Cursor / Codebuddy / VS Code + Copilot | provider-equivalent built-in | provider-equivalent built-in |
| None available | — | fallback below |

**Fallback when no IDE web tools** — pause, ask the user for 4-8 authoritative URLs per dimension, then fetch each:

```bash
python3 ${SKILL_DIR}/scripts/source_to_md/web_to_md.py <URL>
```

**Search rounds** (minimum 2 rounds per dimension):

| Round | Action | Target |
|---|---|---|
| Broad discovery | One search per dimension; collect candidate URLs | 3-5 URLs per dimension |
| Deep fetch | Pull the highest-signal 2-3 pages per dimension in full | Full-page Markdown |
| Cross-fill | Search for claims, data points, or entities surfaced in deep fetch that lack corroboration | Targeted pages |
| Gap review | Identify under-sourced dimensions; run additional targeted searches | 1-2 extra pages per gap |

### 2.2a Multi-platform content gathering（Agent-Reach 增强）

当系统安装了 `agent-reach` 时，可在搜索阶段额外调用以下平台获取中文场景素材：

**零配置平台（直接调用）：**

| 平台 | 命令 | 适用场景 |
|------|------|---------|
| 网页阅读 | `curl -s "https://r.jina.ai/<URL>"` | 将任意 URL 转为干净 Markdown |
| B站搜索 | `curl -s "https://api.bilibili.com/x/web-interface/search/all/v2?keyword=<关键词>"` | 技术教程、科普视频、中文场景 |
| V2EX | `curl -s "https://www.v2ex.com/api/v2/nodes/<node>/topics"` 或 `https://www.v2ex.com/api/topics/hot.json` | 技术讨论、开发者观点 |
| RSS 订阅 | `python3 -c "import feedparser; d=feedparser.parse('<RSS_URL>'); [print(e.title, e.link) for e in d.entries[:10]]"` | 行业博客、新闻源 |
| YouTube 字幕 | `yt-dlp --write-auto-sub --sub-lang zh,en --skip-download -o "<project>/sources/%(title)s" "<URL>"` | 技术演讲、英文教程 |

**使用规则：**
- 这些平台作为 IDE WebSearch 的补充，不替代主要搜索流程
- B站/V2EX 内容属于 Tier 3-4 来源（用户观点、社区讨论），不能作为 Tier 1-2 事实来源
- YouTube 字幕可作为 Tier 3 来源（演讲/教程内容）
- 网页阅读（Jina Reader）可替代 `web_to_md.py`，输出质量更稳定
- 每个维度最多从这些平台获取 2-3 条补充素材，避免喧宾夺主

**Source priority**:

| Tier | Source | Credibility |
|---|---|---|
| 1 | Wikipedia / Wikidata / official documentation / peer-reviewed papers | High — use as factual backbone |
| 2 | Institutional reports / government data / reputable news (Reuters, AP, Xinhua) | High — use for data and quotes |
| 3 | Expert blogs / industry analysis / long-form journalism / conference talks | Medium — use for perspectives and cases |
| 4 | Social media / forums / opinion pieces | Low — use only for "what people think" framing; never as factual source |
| **Avoid** | Content farms / SEO-spam / unsourced aggregators / stock watermarks | — |

**Stop condition**: stop when every dimension has ≥2 Tier 1-2 sources and ≥1 concrete data point or case study. Endless searching produces noise.

### 2.3 Systematic image collection

Collect images during every search round — do not defer to the end.

> **Layout-driven dimensions**: before collecting images, determine each image's target SVG layout slot from the planned page structure (§4.3 PAGE_PLAN). Standard slot sizes for PPT 16:9: cover background 1280×720, content center 1160×425, deep-dive side 370×500, gallery thumbnail 370×170. When collecting or generating images, target these dimensions to avoid awkward cropping in the final SVG.

| Decision | Rule |
|---|---|
| Quantity | ≥1 per search dimension + cover-likely scenes + key entities |
| Resolution | Prefer originals. Wikimedia: strip `/thumb/` and the `Npx-` prefix |
| Target dimensions | Match the image's SVG layout slot (see above). For AI generation, write `target_width`/`target_height` in `image_prompts.json` |
| License | Wikimedia / public-domain / CC-licensed; avoid stock-aggregator watermarks |
| Filename | descriptive English snake_case (`coal_mine_shaft_gantry.jpg`, not `image1.jpg`) |
| Relevance tag | Note which dimension each image belongs to (used in Phase 4 visual strategy) |

```bash
curl -L -o "<project>/images/web_assets/<descriptive_name>.<ext>" "<image_url>"
```

> Images are saved directly to `<project>/images/web_assets/`. Reference images go to `<project>/images/ref/`.

### 2.4 Web asset collection with fallback strategy (three-track)

Deep-dive pages require real images (charts, diagrams, photos, infographics). Use this priority order:

| Priority | Method | When to use | How |
|---|---|---|---|
| ① | Local browser capture | Target webpage is accessible, image is interactive/dynamic | Use Playwright MCP to open page → locate image element → screenshot or right-click save to `<project>/images/web_assets/` |
| ② | Direct URL download | Image URL is publicly accessible and static | `curl -L -o <project>/images/web_assets/<filename>.png "<url>"` — verify file is readable after download |
| ③ | AI generation fallback | ①② both fail (anti-scraping, broken links, copyright restrictions) | Use `image_gen.py` to generate an image matching the deep-dive page's content needs |

**AI fallback rules** (priority ③):
- The prompt must describe the TARGET CONTENT (e.g., "infographic-style brain MRI comparison chart"), NOT repeat the deck's watercolor visual style
- Save to `<project>/images/web_assets/` (same directory as web-sourced images)
- Mark `Acquire Via: ai_fallback` in `design_spec.md §VIII`
- Image dimensions must match the deep-dive page layout (typically 1280×720 for full-width, or proportional for in-layout images)

**Hard rule**: the image collection step must NEVER be skipped. Even if all images fall back to AI generation, every deep-dive page MUST have ≥1 image.

**素材来源适配规则（2026-06-24 新增 — 防止讲解页素材不匹配）**：

通用素材库（Pexels / Pixabay / Openverse）对特定领域的覆盖率差异巨大。必须按主题类型选择素材来源：

| 主题类型 | 推荐来源 | 原因 |
|---------|---------|------|
| 风光/自然/建筑 | 通用素材库 ✅ | 关键词匹配率高，结果可用 |
| 办公/科技/商务 | 通用素材库 ✅ | 大量相关图片 |
| 历史人物/事件 | Playwright 或 AI 降级 | 通用库几乎不可能有匹配的特定历史内容 |
| 古籍/书法/文物 | Playwright 或 AI 降级 | 必须从专业文物网站采集 |
| 地域文化/民俗 | Playwright 优先 | 通用库标签粗糙，匹配度低 |

**svg-native 信息卡方案**（第④降级）：当 ①②③ 全部失败或图片内容明显不匹配时，不使用强制配图，改用纯 SVG 构建的信息卡片：
- 白底（`#FFFFFF`）+ 项目主色装饰条（3px，`primary`色）+ 结构化文本
- 内容为页面主题相关的文献出处、数据摘要、后世评价
- 100% 由项目色板和字体控制，保证内容准确
- 标记 `Acquire Via: svg-native` 于 `design_spec.md §VIII`

**清理规则**：步骤 8 导出前，删除 `web_assets/` 中未被任何 SVG 引用的僵尸文件（参考 `spec_lock.md` images 节）。

---

## Step 3: Structured analysis

Organize all gathered material into a structured analysis. This phase produces facts that are cross-verified, not just collected.

### 3.1 Source register

Build a source register — every URL used, with metadata:

| Field | Description |
|---|---|
| `url` | Source URL |
| `title` | Page title |
| `tier` | 1 / 2 / 3 / 4 |
| `published_date` | Publication date (if found) |
| `author` | Author or organization |
| `dimensions` | Which search dimensions this source covers |
| `key_facts` | List of concrete facts extracted (dates, numbers, names) |

### 3.2 Cross-verification

For every key claim in the research:

| Verification status | Meaning |
|---|---|
| `multi_verified` | Confirmed by ≥2 independent Tier 1-2 sources |
| `single_verified` | Confirmed by 1 Tier 1-2 source |
| `corroborated` | Confirmed by ≥2 Tier 3 sources (not independently authoritative) |
| `unverified` | Single Tier 3-4 source only — flag explicitly |

**Hard rule**: claims with status `unverified` must be labeled as such in the final narrative. Do not present them as established fact.

### 3.3 Extract structured data

From the gathered material, extract and structure:

| Data type | Format | Example |
|---|---|---|
| Key statistics | `{metric, value, unit, source_url, year}` | `{metric: "患病率", value: 49.14, unit: "%", source: "...", year: 2024}` |
| Timeline events | `{date, event, significance, source_url}` | `{date: "1998", event: "首次大规模调查", significance: "...", source: "..."}` |
| Comparisons | `{dimension, item_a, item_b, source_url}` | `{dimension: "有效率", item_a: "手术 95%", item_b: "保守 70%", source: "..."}` |
| Key entities | `{name, role, relevance, source_url}` | `{name: "WHO", role: "发布机构", relevance: "...", source: "..."}` |
| Expert quotes | `{quote, speaker, context, source_url}` | Direct quotes with attribution |

### 3.4 Research richness assessment

Before moving to narrative construction (Step 4), evaluate each chapter's content density to determine deep-dive page allocation:

**Per-dimension minimum output（不可协商）**:

| Requirement | Threshold | Why |
|---|---|---|
| Cross-verified facts from Tier 1-2 sources | ≥3 per dimension | 确保每个维度有可靠的事实骨架 |
| Quantifiable data points (effect sizes, percentages, sample counts) | ≥2 per dimension | 数字让叙事有说服力 |
| Directly usable case study or quote for deep-dive pages | ≥1 per dimension | 给讲解页提供具体素材 |
| Detailed narrative paragraphs (≥100 字/段) | ≥2 per dimension | 调研不是关键词罗列，必须有展开的叙述 |
| Counter-arguments or alternative perspectives | ≥1 per dimension | 避免单面叙事，增加深度感 |

If a dimension falls below these thresholds, run additional targeted searches before proceeding.

**Content density → deep-dive page allocation**:

| Content type | Criteria | Deep-dive pages |
|---|---|---|
| Data-heavy | ≥5 quantifiable data points | 2-3 pages |
| Concept/history-heavy | ≥3 core concepts + timeline | 2 pages |
| Practice guide | ≥5 steps or methods | 1-2 pages |

If a chapter's research content cannot support the planned number of deep-dive pages, either merge adjacent pages or run supplementary searches for that chapter.

**GATE**: before proceeding to Step 4, confirm:
- Total planned deep-dive pages ≥ 30% of (content pages + deep-dive pages)
- Every dimension meets the minimum output requirements above
- If either check fails, run additional targeted searches before continuing

### 3.5 Build narrative nodes

Identify 3-6 **narrative nodes** — the key turning points or insights that will form the backbone of the story arc:

| Node | Role in narrative |
|---|---|
| Opening hook | A surprising fact, counterintuitive claim, or vivid case that grabs attention |
| Problem definition | What the audience needs to understand — the core tension |
| Evidence blocks | 2-4 data-backed arguments, each with a claim + evidence chain |
| Turning point | A shift in perspective, a surprising finding, or a "but then..." moment |
| Synthesis | How all the evidence connects — the "so what" |
| Forward look | Implications, open questions, what comes next |

### 3.6 Plan speaking depth

🚧 **GATE**: every core claim must have a speaking-depth plan before proceeding.

For each core claim identified in 3.4, plan how deep the presenter needs to go:

| Claim | Speaking depth | Deep-dive content type | Supporting material |
|---|---|---|---|
| e.g. "Character origin" | Needs expansion | timeline | Key events + dates |
| e.g. "Core contradiction" | Needs expansion | compare | Two sides + evidence |
| e.g. "Turning moment" | Needs expansion | story | Specific scene + quote |
| e.g. "Impact" | Optional expansion | data | Statistics + sources |

**Deep-dive content types**:
- `timeline` — chronological events the presenter walks through
- `compare` — two-sided analysis the presenter contrasts
- `data` — specific numbers/statistics the presenter explains
- `quote` — key quotes the presenter reads and interprets
- `story` — narrative scene the presenter tells in detail

### 3.7 Write analysis artifact

🚧 **GATE**: analysis artifact must be written before proceeding to narrative construction.

Save `<project>/analysis/research_analysis.json`:

```json
{
  "topic": "<topic>",
  "slug": "<topic_slug>",
  "search_dimensions": [
    {"id": "dim_1", "name": "Background & History", "sources_count": 5}
  ],
  "sources": [
    {
      "url": "...",
      "title": "...",
      "tier": 1,
      "published_date": "2024-01-15",
      "author": "...",
      "dimensions": ["dim_1", "dim_2"],
      "key_facts": ["fact 1", "fact 2"]
    }
  ],
  "cross_references": [
    {
      "claim": "...",
      "verification_status": "multi_verified",
      "sources": ["url_1", "url_2"]
    }
  ],
  "structured_data": {
    "statistics": [],
    "timeline": [],
    "comparisons": [],
    "entities": [],
    "quotes": []
  },
  "narrative_nodes": [
    {
      "id": "hook",
      "role": "opening_hook",
      "content": "...",
      "evidence": ["source_url"]
    }
  ],
  "speaking_depth": [
    {
      "claim": "...",
      "depth": "needs_expansion",
      "type": "timeline|compare|data|quote|story",
      "detail": "What the deep-dive page should cover"
    }
  ]
}
```

---

## Step 4: Narrative construction

Transform the structured analysis into a story-arc Markdown document. This is the core differentiator from quick research — the output reads as a coherent narrative, not a fact list.

### 4.0 Narrative depth contract（叙事深度合约）

**Hard rule**: 调研报告是给演讲者（Presenter）用的"讲稿素材库"，不是给机器读的摘要。每个章节必须有**足够的展开深度**，让演讲者翻到任何一页都有东西可讲。

| 质量指标 | 最低标准 | 判定方法 |
|---------|---------|---------|
| 报告总字数 | ≥3000 字（中文） | 不含来源列表、HTML 标记、JSON |
| 每个 §1-§6 章节 | ≥400 字 | 逐章检查 |
| §3 核心论证 | 2-4 个 evidence block，每个 ≥200 字 | 每个 block 必须有：主张→数据/案例→来源→分析 |
| §4 转折 | ≥300 字 | 必须有具体的反面证据或意外发现，不能只是一句概括 |
| 引用/数据嵌入 | 每章 ≥2 个具体数据或直接引言 | 不能全是概括性描述 |
| 来源标注 | 每个事实性陈述后跟 `[来源: URL]` | 方便演讲者验证和展开 |
| DEEP_DIVE 标记 | ≥5 个 | 每个标记包含 ≥50 字的展开方向描述 |

**不达标处理**：任何章节低于字数要求 → 回到 Step 2 补充搜索对应维度，然后重写该章节。不允许通过"注水"（重复、废话、空洞概括）来凑字数。

### 4.1 Story arc structure

**Hard rule**: the document must follow this narrative skeleton — section names adapt to the topic, but the arc is fixed:

| Section | Narrative role | Content | **最低深度要求** |
|---|---|---|---|
| §1 Opening | Hook the audience | Surprising fact / counterintuitive claim / vivid case | ≥200 字，必须有一个具体的生动案例或数据 |
| §2 Background | Set the stage | History, definitions, context | ≥400 字，必须有时间线/发展脉络，不能只是定义 |
| §3 Core argument | The main thesis | 2-4 evidence blocks, each: claim → data/case → source | 每个 block ≥200 字，含具体数据+来源+分析 |
| §4 Turning point | Shift perspective | Counter-evidence, surprising finding | ≥300 字，必须有具体的反面案例或意外发现 |
| §5 Implications | The "so what" | Why this matters to the audience | ≥300 字，必须有对受众的具体影响分析 |
| §6 Conclusion | Forward look | Open questions, future trends | ≥200 字，必须有可操作的建议或展望 |
| §7 Sources | Provenance | All URLs used, grouped by tier | 不限，按可信度分组 |

### 4.2 Deep-dive markers

**MANDATORY**: for claims that need expansion, embed deep-dive markers:

```markdown
<!-- DEEP_DIVE: type="timeline" detail="Walk through the 5 key events from 2019 to 2024" -->
```

Types: `timeline` / `compare` / `data` / `quote` / `story`

These markers tell the PPT generator to create a "deep-dive page" (讲解页) after the content page, giving the presenter rich material to elaborate on.

### 4.2a Deep-dive page allocation rules

**Core principle**: the number of deep-dive pages per chapter must be proportional to the research content's richness for that chapter. One deep-dive page is rarely enough to explain anything thoroughly.

| Research content density | Deep-dive pages per chapter | Example |
|---|---|---|
| Data-heavy (statistics, meta-analyses, multiple studies) | 2-3 | Brain imaging data + clinical trial results + effect size breakdown |
| Rich history / multi-layered concepts | 2 | Timeline + philosophical foundations |
| Comparison + practical mechanics | 2 | Side-by-side comparison + detailed technique guide |
| Synthesis / practical guide | 1-2 | Practice plan + integration framework |

**Hard rules**:

1. **Every content page that makes a substantive claim MUST be followed by ≥1 deep-dive page** that expands on that claim with evidence, data, or detailed explanation.
2. **Total deep-dive pages ≥ 30% of content+deep-dive pages combined.** If you have 5 content pages, you need at least 3-4 deep-dive pages.
3. **Each chapter gets deep-dive pages proportional to its research richness** — do not distribute them evenly if the research is uneven.

### 4.2a-dedup Deep-dive content deduplication

**Hard rule**: within a single deck, no two deep-dive pages may share the same data point, quote, or evidence block.

| Check | Threshold | Action |
|---|---|---|
| Text overlap between any two deep-dive pages | ≥50% shared content | Merge into one page or diversify the second page with new dimensions |
| Same statistic cited on two pages | Same number + same source | Keep on the earlier page; replace on the later page with a different data point |
| Same quote on two pages | Verbatim match | Keep on the more impactful page; replace the other |

**Executor instruction**: when generating deep-dive SVGs, cross-check each page's content against all other deep-dive pages. If overlap is found, supplement with content from the research analysis that has not yet been used.

### 4.2b Deep-dive page layout rules

**Core principle**: deep-dive pages are the presenter's "talking pages" — they must be immediately readable from a distance and visually structured, not text walls.

| Rule | Specification |
|---|---|
| Text alignment | All text content center-aligned unless the layout specifically requires otherwise (e.g., timeline) |
| Title size | 36-44px, Bold, must echo/reference the preceding content page's core claim |
| Body text size | 22-26px minimum; for pages with fewer items (≤3), enlarge to 28-36px |
| Line height | 1.6-1.8 |
| Element spacing | ≥32px between text blocks and surrounding elements |
| Layout variety | Use cards, columns, timelines, data callouts — never plain text paragraphs |
| Web assets | Every deep-dive page MUST include ≥1 web-sourced image (chart, diagram, photo, infographic) |
| Image integration | Image area ≥25% of page total (≥216,000px²); image and text must form a cohesive layout, NOT a small thumbnail in a corner |
| Image-text layouts | Choose one per page: left-image/right-text, right-image/left-text, top-image/bottom-text, or image-interspersed; alternate across pages for rhythm |
| Image rendering | Use `preserveAspectRatio="xMidYMid slice"` (crop-to-fill for visual impact). When image and container aspect ratios differ, the image fills the container completely with center-cropped edges — this is preferred over `meet` which leaves empty bands. |

**⛔ BLOCKING — Web asset gate (HARD rule)**: before generating any deep-dive SVG, the Executor MUST verify that `<project>/images/web_assets/` contains ≥1 image file for EACH deep-dive page listed in spec_lock.md's page_rhythm table. If files are missing:
1. Attempt Playwright MCP browser capture from target URLs
2. If Playwright fails, attempt direct curl/wget下载
3. If both fail, generate AI fallback images via image_gen.py (prompt describes the target content, NOT the deck's visual style)
4. If AI also fails or topic is niche historical/cultural (通用素材库不可能匹配), build **svg-native info card** — a white card with project accent bar + structured text from research_analysis.json. Mark `Acquire Via: svg-native` in design_spec.md §VIII.
5. Only after all deep-dive pages have ≥1 visual element (image or svg-native card) may SVG generation proceed

**Do NOT generate deep-dive SVGs without visual elements.** A deep-dive page needs visual content — either a matching web image, AI-generated infographic, or svg-native info card. Pure text walls are a quality failure.

**Post-generation cleanup**: after export, delete any `web_assets/*.png` not referenced by SVGs (verify against `spec_lock.md` images section). Unused files waste ~135MB per project on average.
| Narrative continuity | Title must explicitly reference the preceding content page's core message |

**Narrative continuity rule (MANDATORY)**: every deep-dive page title must echo or continue the preceding content page's core claim. This creates a reading chain: content page makes a claim → deep-dive page proves it.

Examples:
- Content: "8周改变大脑" → Deep-dive: "8周改变大脑：关键研究数据"
- Content: "站桩为拳学之母" → Deep-dive: "母功的传承谱系"
- Content: "水与山的对话" → Deep-dive: "自上而下 vs 自下而上：详细对比"

### 4.2c Content page layout rules

**Core principle**: content pages are the visual hooks — they use a large central AI image with minimal text (title + caption + takeaway). The layout structure follows the story_driven template's `03_content.svg` / `03a_content.svg` as a reference: full-width central image area, title at top, takeaway at bottom.

**Color adaptation (MANDATORY)**: the content page background and text colors MUST match the project's `spec_lock.md` color scheme. Do NOT blindly copy the template's dark background (#1A1A2E) — if the project uses a light theme (e.g., warm white #F5F0E6 or ice white #F8F4F0), the content page must use that light background with appropriate text colors. The template provides the STRUCTURE (image placement, text hierarchy); the project's spec provides the COLORS.

**Light-theme adaptation checklist (2026-06-24 新增)** — when converting dark templates to light theme, verify:
1. All tertiary text (#8C8C8C level) is upgraded to secondary (#5C5C5C) or darker — light gray text on light background is invisible
2. Background overlay opacities on AI images are ≥0.50 for readable text contrast
3. Card borders and divider lines use #D5CFC5 minimum (not blending into #F5F0E8 background)
4. Deep-dive body text is ≥16px and uses `text-anchor="middle"` for centered card content
5. All font sizes are ≥13px (absolute minimum; annotation floor) — run `svg_quality_checker.py` to verify
6. Check WCAG contrast: all body text fills must have ≥4.5:1 contrast against page background

**Layout variety**: alternate between variant A (clean line decoration) and variant B (dot decoration + bordered image) for visual rhythm. The Executor may also create project-specific variations that maintain the "large central image + sparse text" principle while adapting to the theme. Both template-based and self-created layouts are acceptable, as long as they:
- Feature a large central AI image (≥60% of content area)
- Use the project's color scheme (not the template's hardcoded colors)
- Keep text sparse (title + caption + takeaway only)
- Maintain visual consistency with the rest of the deck

### 4.3 Page rhythm plan

**MANDATORY**: append a page sequence plan at the end of the document:

```markdown
<!-- PAGE_PLAN
P01: cover
P02: toc
P03: transition → section 1
P04: content — section 1 core claim (visual hook)
P05: deep_dive — expand: timeline of key events
P06: transition → section 2
P07: content — section 2 core claim
P08: deep_dive — expand: comparison of two approaches
P09: quote — iconic statement from section 2
P10: transition → section 3
...
P18: ending
-->
```

This plan drives SVG generation — each line becomes one SVG page.

### 4.4 Content density rules

| Rule | Description |
|---|---|
| **Every claim needs a source** | Inline source reference: (来源: URL_short_name, 2024) |
| **Key data in tables** | Statistics, comparisons, timelines go in Markdown tables — not buried in prose |
| **Core propositions stated explicitly** | Each section's main argument in **bold** as its opening sentence |
| **Narrative nodes as section anchors** | Each §3 evidence block maps to a `narrative_node` from Step 3 |
| **Transition hooks between sections** | Each section ends with a sentence that bridges to the next — these become PPT transition page content |
| **No filler prose** | Every sentence carries information or advances the argument |
| **Unverified claims labeled** | Use `⚠️ 未经多源验证` or equivalent marker |

### 4.5 Transition node markers

**Mandatory**: embed transition markers between major sections. These feed the Strategist's `{{PREV_SECTION_SUMMARY}}` and `{{NEXT_HOOK}}` placeholders for the `story_driven` template's chapter pages:

```markdown
<!-- TRANSITION: prev_summary="上一节核心结论" next_hook="引导下一节的问题" -->
```

Place one marker between §1→§2, §2→§3, §3→§4, §4→§5, §5→§6. The Strategist reads these to populate transition page text.

### 4.6 Write the narrative document

Save to `<project>/sources/research_report.md`. The document MUST end with a `## Sources` section listing all URLs grouped by tier.

**Content density**: concrete facts (dates, names, numbers, quotes) with inline sources. The Strategist composes final slide copy from this material.

### 4.7 Quality gate — research depth verification

⛔ **BLOCKING**: before proceeding to Step 5, verify the research report meets the depth contract:

```markdown
## 调研深度自检报告
- [ ] 总字数 ≥3000：实际 ___ 字
- [ ] 每章 ≥400 字：§1 ___ / §2 ___ / §3 ___ / §4 ___ / §5 ___ / §6 ___
- [ ] §3 evidence blocks 每个 ≥200 字：共 ___ 个，最短 ___ 字
- [ ] §4 转折 ≥300 字：实际 ___ 字
- [ ] 每章 ≥2 个具体数据/引言：§1___ / §2___ / §3___ / §4___ / §5___ / §6___
- [ ] 来源标注覆盖：___ 个事实性陈述带 [来源: URL]
- [ ] DEEP_DIVE 标记 ≥5 个：实际 ___ 个
- [ ] 交叉验证事实 ≥8 个：实际 ___ 个
```

**任何一项不达标 → 回到 Step 2 补充搜索，然后重写不达标的章节。不允许跳过。**

---

## Step 5: Visual strategy

Research visual conventions and prepare image strategy for the PPT.

### 5.1 Visual reference research

During search rounds, collect visual references:

| What to look for | Where |
|---|---|
| Color palettes used in the domain | Existing presentations, infographics, institutional reports on the topic |
| Visual metaphors common to the field | Editorial illustrations, news graphics, academic figures |
| Image style conventions | What style does the audience expect (photorealistic? illustrative? data-driven?) |
| Competitor/reference decks | Similar-topic presentations for benchmarking |

### 5.2 Draft AI image prompts

For each planned PPT page that needs an AI image, draft a prompt reference:

| PPT page type | Prompt direction | Composition hint |
|---|---|---|
| Cover | The topic's visual essence in one frame | Full-bleed, hero composition |
| TOC | Thematic overview | Atmospheric, sets tone |
| Transition (per section) | Section-specific visual metaphor | Bridges prev and next content |
| Content (per page) | Page's core visual story | Supports the page's one claim |
| Ending | Closing emotional frame | Bookend with cover |

**Hard rule**: prompt references are subject + intent + composition only. Do NOT include style words or HEX — the image-generator.md prompt assembler injects those from the deck-wide rendering + palette lock.

### 5.3 Write visual strategy artifact

Save `<project>/analysis/visual_strategy.json`:

```json
{
  "topic": "<topic>",
  "domain_visual_conventions": {
    "typical_palette": "描述该领域常见配色倾向",
    "common_metaphors": ["metaphor 1", "metaphor 2"],
    "style_preference": "描述该领域常见视觉风格倾向"
  },
  "color_recommendation": {
    "rationale": "基于调研内容和领域惯例的配色理由",
    "primary_direction": "dark/light + 色调倾向",
    "candidates": ["#hex1", "#hex2", "#hex3"]
  },
  "image_prompts": [
    {
      "ppt_role": "cover",
      "subject": "主题的核心视觉隐喻",
      "intent": "唤起的情绪或认知效果",
      "composition": "构图方向"
    },
    {
      "ppt_role": "transition",
      "section_id": 1,
      "subject": "该板块的视觉隐喻",
      "intent": "承上启下的视觉语言",
      "composition": "构图方向"
    }
  ]
}
```

> Note: the color candidates here are advisory — the Strategist's Eight Confirmations makes the final call. The visual strategy provides domain-informed input so the Confirm UI's color candidates are topic-relevant rather than generic.

---

## Hand-off

Output a checkpoint, then continue with the main pipeline. All artifacts are already inside `<project>`:

```markdown
## ✅ Deep Research Complete
- [x] Document: `<project>/sources/research_report.md` (N sections, narrative arc)
- [x] Analysis: `<project>/analysis/research_analysis.json` (N sources, M verified claims)
- [x] Visual strategy: `<project>/analysis/visual_strategy.json`
- [x] Images: `<project>/images/` (N files)
- [ ] **Next**: Content Selection phase — interactive dimension picking (SKILL.md Step 2 checkpoint triggers this automatically when `research_report.md` exists)
```

The Strategist reads `<project>/analysis/research_analysis.json` for cross-verified claims, structured data, and narrative nodes. It reads `<project>/analysis/visual_strategy.json` for domain-informed color and image prompt direction. Both files are optional supplements — the pipeline works without them.
