---
description: PPT Briefing workflow — topic-only 项目的前置构思流程。先确认创作蓝图，再进入 deep-research。
---

# PPT Briefing Workflow

> Topic-only PPT 的前置构思流程。把用户的一句话主题转成可确认的 PPT 创作蓝图，并输出 `ppt_brief.md` 与 `ppt_brief.json` 供 deep-research、Strategist 和后续素材路由使用。

**Hard rule**: Topic-only 请求必须先运行本 workflow。用户未确认 `ppt_brief.md` / `ppt_brief.json` 前，不得进入 [`deep-research`](./deep-research.md)。

**Trigger**: 用户只给主题、方向、关键词或一句话需求，没有文件、URL、长文本材料或足以直接生成的实质内容。

---

## 1. 入口判定

| 用户输入 | 动作 |
|---|---|
| 只有主题 / 一句话方向 | 运行 PPT Briefing，生成并确认 brief |
| 主题 + 零散要求（页数、风格、受众等） | 运行 PPT Briefing，把要求写入 brief |
| 主题 + 完整长文本材料 | 可跳过 Brief，进入 SKILL.md Step 1 |
| PDF / DOCX / URL / Markdown / PPTX 等源文件 | 按 SKILL.md Step 1 处理源材料；需要深度调研时 deep-research 可读取源材料，不强制 Brief |
| 用户明确要求“先构思 / 先做 brief / 先确认方向” | 运行 PPT Briefing |

**Hard rule**: 不要用 deep-research Step 1 的大纲确认替代 Brief 确认。Brief 确认的是“这份 PPT 要做成什么”，大纲确认的是“按已确认方向如何展开研究”。

---

## 2. 项目初始化

🚧 **GATE**: 已判定为 topic-only，且用户尚未提供可直接作为源材料的文件或长文本。

创建项目目录：

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
```

**Mandatory**: `ppt_brief.md` 和 `ppt_brief.json` 写入项目根目录：

```text
<project_path>/ppt_brief.md
<project_path>/ppt_brief.json
```

**Default — project slug (may override when user specifies)**: 用主题生成短 slug；避免另建 `_brief/`、临时目录或 sibling project。

---

## 3. Brief 字段

### 3.1 `ppt_brief.json`

输出合法 JSON，字段如下：

```json
{
  "topic": "",
  "user_goal": "",
  "target_audience": "",
  "usage_context": "",
  "decision_stage": "explore | persuade | report | teach | launch | entertain",
  "page_range": {"min": 8, "max": 15, "preferred": 12},
  "narrative_frame": {
    "recommended_mode": "pyramid | narrative | instructional | showcase | briefing | custom",
    "story_arc": "",
    "opening_hook": "",
    "closing_intent": ""
  },
  "content_boundary": {
    "must_include": [],
    "must_exclude": [],
    "depth": "overview | standard | deep | expert",
    "freshness": "evergreen | recent | latest",
    "region_or_language": ""
  },
  "visual_direction": {
    "style_intent": "",
    "layout_preference": "dense | balanced | visual-led | text-led",
    "image_density": "none | low | medium | high",
    "chart_density": "none | low | medium | high"
  },
  "material_strategy": {
    "domain": "",
    "domain_confidence": 0.0,
    "preferred_source_packs": [],
    "disabled_source_packs": [],
    "generic_stock_policy": "disabled_by_default | fallback_only | allowed_for_atmosphere",
    "requires_official_assets": false,
    "requires_manual_asset_review": false
  },
  "source_strategy": {
    "tier1_sources": [],
    "tier2_sources": [],
    "platforms": [],
    "search_languages": []
  },
  "copyright_and_risk": {
    "public_distribution": false,
    "copyright_risk_level": "low | medium | high",
    "google_images_policy": "discovery_only",
    "manual_review_required": []
  },
  "acceptance_criteria": {
    "content": [],
    "visual": [],
    "asset": [],
    "delivery": []
  },
  "confirmation_items": []
}
```

**Hard rule**: `google_images_policy` 默认为 `discovery_only`。当主题涉及人物、IP、产品、历史、学术或近期新闻时，`requires_manual_asset_review` 必须按风险设为 `true`。

### 3.2 `ppt_brief.md`

`ppt_brief.md` 必须包含以下可读摘要：

| 区块 | 内容 |
|---|---|
| 目标 | 这份 PPT 要帮助谁做什么决策、理解或行动 |
| 受众 | 身份、知识背景、阅读耐心、关注点 |
| 场景 | 汇报、培训、发布、路演、研究分享等 |
| 叙事 | 推荐故事线、开场钩子、结尾意图 |
| 页数 | 建议范围和理由 |
| 内容边界 | 必讲、不讲、资料深度、时效要求 |
| 视觉 | 风格方向、版式倾向、图片密度、图表密度 |
| 素材 | 领域 source pack 倾向、禁用来源、是否需要官方资产或人工复核 |
| 风险 | 版权、时效、主体歧义、公开发布风险 |
| 验收 | 内容、视觉、素材、交付标准 |

---

## 4. 生成方式

**Per-brief synthesis**: 基于用户主题和已有偏好生成推荐值；没有足够信息时写入明确假设，并放入 `confirmation_items`。

**Forbidden — research before confirmation**:
- 不运行 deep-research
- 不做正式 WebSearch
- 不下载图片
- 不写 research artifacts
- 不提前生成详细大纲或 design spec

**Default — conservative material policy (may override when user confirms)**: 未明确需要通用氛围图时，`generic_stock_policy` 使用 `disabled_by_default` 或 `fallback_only`；只有商业氛围、背景图、抽象场景图才写 `allowed_for_atmosphere`。

---

## 5. 用户确认

⛔ **BLOCKING**: 展示 Brief 摘要并等待用户明确确认或修改。一次性展示，不逐项追问。

确认摘要至少包含：

| 项目 | 展示内容 |
|---|---|
| 目标 | `user_goal` |
| 受众 | `target_audience` |
| 叙事 | `narrative_frame.story_arc` / `opening_hook` / `closing_intent` |
| 页数 | `page_range` |
| 内容边界 | `content_boundary.must_include` / `must_exclude` / `depth` / `freshness` |
| 视觉 | `visual_direction` |
| 素材 | `material_strategy` 与 `source_strategy` |
| 风险 | `copyright_and_risk` |
| 验收 | `acceptance_criteria` |

用户可以：

1. **确认** -> 保留 `ppt_brief.md` / `ppt_brief.json`，进入 [`deep-research`](./deep-research.md)
2. **修改** -> 更新两个 brief 文件后重新确认
3. **补充材料** -> 若补充文件或长文本，按 SKILL.md Step 1 重新判断是否仍需 Brief

**Hard rule**: 只有收到明确确认后，才允许 deep-research Step 0/1 开始。

---

## 6. 交接

确认后，deep-research 必须读取：

```text
<project_path>/ppt_brief.json
<project_path>/ppt_brief.md
```

下游使用方式：

| 下游阶段 | 使用 brief 的方式 |
|---|---|
| deep-research Step 1 | 用目标、受众、叙事框架、内容边界生成研究大纲 |
| deep-research Step 2 | 用资料深度、source_strategy、素材策略和验收标准生成搜索计划 |
| content-selection | 用目标和内容边界过滤研究报告维度 |
| detailed-outline | 用叙事框架和验收标准约束逐页计划 |
| Strategist | 用 Brief 作为 Eight Confirmations 的上游创作约束 |
| Image Source Routing | 用 `material_strategy` 和 `copyright_and_risk` 决定 source pack |

**Checkpoint output**:

```markdown
## ✅ PPT Briefing Complete
- [x] `ppt_brief.md` exists at `<project_path>/ppt_brief.md`
- [x] `ppt_brief.json` exists at `<project_path>/ppt_brief.json`
- [x] User explicitly confirmed the Brief
- [ ] **Next**: enter `deep-research` with `ppt_brief.json` as upstream constraint
```
