---
description: 确保 AI 生图和网络素材搜索指令包含对应页面的文字内容上下文，保证图文语义一致。读取详细大纲为每张图片注入 core_argument 和 content_bullets，替换通用关键词。
---

# 图文联动工作流（Image-Text Linking）

> 确保 AI 生图（`image_gen.py --manifest`）和网络素材搜索（`image_search.py --batch`）指令包含对应页面的文字内容上下文，保证图文语义一致。读取 `detailed_outline.json` 为每张图片注入 `core_argument`、`content_bullets` 和 source routing 字段，替换通用关键词。

This workflow is **transversal**: it does not run as a standalone step but modifies the image acquisition preparation inside the Strategist and Image_Generator phases. It reads `detailed_outline.json` (from `detailed-outline.md`) and enforces content-aware prompt assembly for all image acquisition methods.

## When to Run

| Condition | Action |
|---|---|
| `detailed_outline.json` exists AND `design_spec.md §VIII` has ≥1 row with `Acquire Via: ai` or `Acquire Via: web` | Apply this workflow during image prompt/query generation |
| No `detailed_outline.json` (user-provided source, no content selection) | Skip — fall back to default prompt assembly in `image-generator.md` / `image-searcher.md` |
| All images are `Acquire Via: icon` or `Acquire Via: executor` | Skip — no external image acquisition needed |

---

## Step 1: Build Context Map

Read `<project>/detailed_outline.json` and build a lookup table mapping each page to its content context.

**1.1 Filter relevant pages**

For each page in `detailed_outline.json.pages`, include it in the context map if:

- `visual_need.image_type` is NOT `"icon"` (icons are selected from the library, no prompt needed)
- `visual_need.image_type` is NOT `"chart"` (charts are rendered natively by the Executor in SVG)

**1.2 Build context entry**

For each included page, create a context entry with:

| Field | Source |
|---|---|
| `page_number` | `pages[i].page_number` |
| `core_argument` | `pages[i].core_argument` — the one thing the page must communicate |
| `content_bullets` | `pages[i].content_bullets` — all 3–5 items |
| `image_type` | `pages[i].visual_need.image_type` |
| `image_description` | `pages[i].visual_need.image_description` |
| `text_image_link` | `pages[i].visual_need.text_image_link` — how image supports the argument |
| `image_slot_size` | `pages[i].visual_need.image_slot_size` — target dimensions from layout |
| `reference_image_required` | `pages[i].visual_need.reference_image_required` |
| `asset_file` | `pages[i].visual_need.asset_file` |
| `source_pack` | `pages[i].visual_need.source_pack` |
| `preferred_sources` | `pages[i].visual_need.preferred_sources` |
| `disabled_providers` | `pages[i].visual_need.disabled_providers` |
| `allow_generic_stock` | `pages[i].visual_need.allow_generic_stock` |
| `discovery_only` | `pages[i].visual_need.discovery_only` |
| `needs_manual_review` | `pages[i].visual_need.needs_manual_review` |
| `copyright_risk` | `pages[i].visual_need.copyright_risk` |
| `selection_reason` | `pages[i].visual_need.selection_reason` |

**1.3 Output format**

The context map is an in-memory structure (not written to disk). It is consumed directly by the prompt assembly logic in Steps 2 and 3.

---

## Step 2: Enhance AI Image Prompts

When generating `image_prompts.json` for `image_gen.py --manifest`, every prompt MUST incorporate the page's content context.

**2.1 Prompt template (6-part mandatory structure)**

Each AI image prompt MUST follow this template:

```
{image_description}。视觉目标：{image_intent}。风格：{deck_rendering}。版式尺寸：{image_slot_size.width}×{image_slot_size.height}。页面依据：{core_argument 具体化 + content_bullets 摘要 + content_density}。文字/图像关系：{text_image_link + SVG/图片文字分工}。失败兜底：{fallback_plan}
```

| Part | Source | Purpose |
|---|---|---|
| `{image_description}` | `visual_need.image_description` | What the image shows |
| `{image_intent}` | page strategy | Why the page needs this image |
| `{deck_rendering}` | `spec_lock.md` rendering lock | Visual style consistency (e.g., "扁平矢量、蓝绿渐变配色") |
| `{image_slot_size}` | `detailed_outline.json` | Prevents generating images that are later cropped |
| `{core_argument + content_bullets + content_density}` | page content context | Grounds the image in the page's information structure |
| `{text_image_link + SVG/图片文字分工}` | `visual_need.text_image_link` + layout plan | Explains whether image text is embedded, overlaid, or kept beside the image |
| `{fallback_plan}` | page strategy | Records the non-reference or non-AI path if generation fails |

**2.2 Minimum length**

Every assembled prompt MUST be ≥80 characters after template assembly. Shorter prompts lack sufficient context for meaningful image generation.

**2.2a Manifest audit fields**

For every `items[]` entry in `image_prompts.json`, write these fields outside the prompt as well:

| Field | Required value |
|---|---|
| `image_intent` | The page-level communication job |
| `page_evidence` | `core_argument`, relevant `content_bullets`, density, and layout reason |
| `text_image_relationship` | Editable SVG text vs in-image text ownership |
| `fallback_plan` | Text-to-image, native SVG, web, placeholder, or manual fallback |
| `reference_image_policy` | Required only when `reference_image` is present |
| `source_routing` | Required when prompt depends on concrete reference images or fallback web sourcing |

**Source routing for references**: when an AI prompt needs a concrete reference image for a person, IP, product, place, event, historical artifact, or academic figure, carry the same source-pack fields used by web rows. Browser / Google results are discovery-only and cannot become `reference_image` without manual review and source-page provenance.

**2.3 Forbidden patterns**

| Pattern | Example | Why forbidden |
|---|---|---|
| Generic topic words only | "科技感背景图" | No page context — generates generic stock imagery |
| Style-only prompts | "水彩风格插画" | Describes rendering, not content |
| Page number without argument | "第三页配图" | No semantic link to the page's message |
| Duplicate prompts across pages | Same prompt for pages 5 and 8 | Violates one-image-per-claim principle |
| Unreviewed reference image | Person/place/event image with `reference_image` but no source, semantic match, confidence, or fallback | Risks same-name misidentification and img2img drift |

**2.4 Good vs bad examples**

```
❌ "科技感背景图"
✅ "柱状图展示2020-2025年新能源汽车市场规模增长趋势，从120万辆到680万辆。
    风格：扁平矢量、蓝绿渐变配色。场景：宏观市场鸟瞰视角。
    文字呼应：支撑'市场规模翻5倍'的核心论点"
```

```
❌ "医疗健康插画"
✅ "MRI脑部扫描对比图，左侧为训练前灰质密度，右侧为8周正念训练后灰质密度增加区域（高亮标注海马体）。
    风格：医学信息图、冷色调。场景：临床研究证据展示。
    文字呼应：支撑'8周改变大脑结构'的实验结论"
```

### 2.5 Cross-Page Style Consistency

All AI image prompts within one deck MUST reference a common set of style anchors to ensure visual coherence across pages.

**Style anchors** (derived from `spec_lock.md` during Strategist phase):

| Anchor | Source | How to enforce |
|---|---|---|
| `color_temperature` | `spec_lock.md` colors → background + primary | Every prompt includes "warm/cool/neutral color temperature" matching the palette |
| `lighting_direction` | `spec_lock.md` visual_style behavior | Every prompt uses consistent lighting (e.g., "soft top-left diffused lighting") |
| `art_style` | `spec_lock.md` rendering lock | Every prompt includes the locked rendering style verbatim (e.g., "flat vector, blue-green gradient") |
| `background_treatment` | `spec_lock.md` colors.background | Every prompt references the background color family for consistency |

**Cross-page coherence validation** — before finalizing `image_prompts.json`, verify:

| Check | Threshold | Action on failure |
|---|---|---|
| Every prompt contains `{deck_rendering}` segment | 100% | Append rendering style to prompt |
| No two prompts use conflicting lighting directions | 0 conflicts | Unify to the deck's chosen direction |
| No prompt contradicts the deck's color temperature | 0 conflicts | Rewrite temperature-specific language |
| Same subject across pages uses consistent reference images | 100% | Link all depictions to the same `reference_image` |
| Reference image policy exists for every `reference_image` | 100% | Add source, semantic match, confidence, approval, and fallback |

**Forbidden**:
- Prompts that omit the deck's locked rendering style
- Contradictory visual language across pages (one page "watercolor pastel" while another "sharp vector illustration")
- Different reference images for the same character/product across pages
- Using high-ambiguity person/place/event references from weak web search results; omit `reference_image` and use a symbolic or text-to-image fallback instead

---

## Step 3: Enhance Web Search Keywords

When generating `image_queries.json` for `image_search.py --batch`, every query MUST extract keywords from the page's content context, not from generic topic words.

**3.1 Keyword extraction rules**

| Rule | Description |
|---|---|
| Source from `content_bullets` | Keywords MUST be derived from the page's `content_bullets`, not from the topic name alone |
| Include `core_argument` | The page's `core_argument` should appear as part of the search context |
| 3–5 keyword combinations | Each query should have multiple keyword variants to improve hit rate |
| Include specificity markers | Add years, numbers, proper nouns from `content_bullets` to narrow results |

**3.2 Good vs bad examples**

```
❌ keywords: ["新能源汽车", "市场"]
✅ keywords: ["新能源汽车销量增长", "2020-2025市场规模", "柱状图数据可视化"]
```

```
❌ keywords: ["脑科学", "健康"]
✅ keywords: ["正念冥想MRI脑部变化", "灰质密度对比图", "海马体体积增长数据"]
```

**3.3 Query structure**

Each entry in the **advisory** `image_queries.json` (produced by this workflow as guidance for the Strategist) should follow:

```json
{
  "page_number": 5,
  "keywords": ["关键词组合1", "关键词组合2", "关键词组合3"],
  "context": "core_argument 原文",
  "source_pack": "academic_science",
  "preferred_sources": ["wikimedia", "institutional_report"],
  "disabled_providers": ["pexels", "pixabay", "unsplash"],
  "allow_generic_stock": false,
  "discovery_only": false,
  "needs_manual_review": false,
  "copyright_risk": "medium",
  "selection_reason": "Scientific/academic visual should use authoritative or open-license sources."
}
```

> **Schema note**: This advisory format uses `keywords` (array) and `page_number` for Strategist context. The **authoritative** `image_queries.json` consumed by `image_search.py --batch` uses a different schema defined in [`image-searcher.md`](../references/image-searcher.md): `{items: [{filename, query, slide, purpose, orientation, status}]}`. The Strategist is responsible for transforming this advisory format into the authoritative schema (merging `keywords` into a single `query` string, adding `filename`/`status`, wrapping in `items` array) before writing the final `image_queries.json`.

For web rows, include target dimensions and the planned page context in the authoritative batch query:

```json
{
  "filename": "p05_growth_chart.jpg",
  "query": "新能源汽车 2020 2025 销量 柱状图",
  "slide": "P05",
  "purpose": "deep_dive:data supporting 市场规模翻5倍",
  "orientation": "landscape",
  "min_width": 928,
  "min_height": 340,
  "source_pack": "data_report_capture",
  "preferred_sources": ["official_report", "data_portal"],
  "disabled_providers": ["pexels", "pixabay", "unsplash"],
  "allow_generic_stock": false,
  "discovery_only": true,
  "needs_manual_review": true,
  "copyright_risk": "medium",
  "selection_reason": "Data chart should come from source report or be redrawn as SVG.",
  "status": "Pending"
}
```

The `context` field carries the `core_argument` verbatim — search providers may use it for relevance ranking.

**Hard rule**: For web rows, preserve source routing fields from `detailed_outline.json.visual_need`. Do not replace them with provider guesses. `generic_atmosphere` is the only default route that may enable generic stock providers.

---

## Constraints

| Constraint | Threshold | Enforcement |
|---|---|---|
| No image prompt without page text context | 100% | Every AI prompt must contain `core_argument` or `content_bullets` content |
| No stock search keywords from generic topic words alone | 100% | Keywords must trace to `content_bullets` |
| Minimum AI prompt length | ≥80 characters | After template assembly; reject shorter prompts |
| `text_image_link` present in every AI prompt | 100% | The 4-part template includes it as the final segment |
| No duplicate prompts across pages | 0 duplicates | Each page gets a unique prompt reflecting its specific `core_argument` |
| Required reference images present | 100% | Any `reference_image_required=true` AI row must include a real local path or URL |
| Target dimensions carried into image manifests/queries | 100% | Every AI/web row includes slot width/height or min dimensions |
| Source routing carried into web queries | 100% | Every web row includes `source_pack`, risk, review, and provider policy when available |
| Discovery-only not treated as cleared final asset | 100% | Browser / Google rows carry `discovery_only: true` and `needs_manual_review` when high-risk |

---

## Integration Points

| Direction | Target | Data |
|---|---|---|
| **Reads from** | `<project>/detailed_outline.json` | Per-page `core_argument`, `content_bullets`, `visual_need` |
| **Reads from** | `<project>/spec_lock.md` | Deck-wide rendering style for `{deck_rendering}` segment |
| **Feeds into** | `references/image-generator.md` §4 (Prompt Assembly) | Enhanced prompt template and constraints |
| **Feeds into** | `references/image-searcher.md` §5 (Batch Queries) | Content-aware keyword extraction rules |
| **Feeds into** | `references/image-source-routing.md` | Source pack, provider policy, discovery-only, risk, and review fields |
| **Consumed by** | `image_gen.py --manifest` | Reads `<project>/images/image_prompts.json` with enhanced prompts |
| **Consumed by** | `image_search.py --batch` | Reads `<project>/images/image_queries.json` with enhanced keywords |

---

## Output

This workflow does not produce a standalone artifact. It modifies the **content** of two files that the Image_Generator phase produces:

| File | Enhancement |
|---|---|
| `<project>/images/image_prompts.json` | Every `prompt` field follows the 4-part template with page context |
| `<project>/images/image_queries.json` | Every `keywords` / `query` value is derived from `content_bullets`, not generic terms; web rows preserve source routing fields |

These files are written by the Image_Generator role as usual — this workflow only constrains *how* their content is assembled.
