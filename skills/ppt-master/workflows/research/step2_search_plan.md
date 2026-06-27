---
description: 深度调研 Step 2 — 搜索需求拆分。解析大纲每一页，生成逐页搜索计划并分配 AI 工具。
---

# Step 2: 搜索需求拆分（Search Plan）

> 解析 Step 1 输出的大纲，为每一页分析需要搜索的内容，生成结构化的搜索计划。按内容类型分配不同的 AI 搜索工具。

**输入**: `_research/step1_outline/outline.json`
**输出**: `_research/step2_search_plan/search_plan.json`

---

## 2.1 加载大纲

读取 `_research/step1_outline/outline.json`，获取所有页面信息。

过滤出 `needs_data: true` 的页面作为搜索目标。`needs_data: false` 的页面（如封面、目录、结尾）标记 `skip_search: true`。

---

## 2.2 分析每页搜索需求

对每个需要搜索的页面：

1. **解读 data_hint** — 该页需要什么类型的数据
2. **生成搜索关键词** — 3-5 个精准关键词
3. **确定内容类型** — 用于分配 AI 工具
4. **评估优先级** — 核心论点页 > 数据支撑页 > 背景页

---

## 2.3 AI 工具分配规则

按内容类型选择最适合的 AI 搜索工具：

| 内容类型 | AI 工具 | 理由 |
|---------|---------|------|
| **技术/数据** — 统计数据、技术参数、产品规格、对比数据 | ChatGPT (`chatgpt`) | 擅长结构化信息整理、数据分析 |
| **新闻/趋势** — 最新动态、市场趋势、行业热点、社交媒体 | Grok (`grok`) | 实时信息获取能力强，接入 X/Twitter |
| **学术/深度** — 历史背景、学术观点、理论分析、深度报道 | Perplexity (`perplexity`) | 擅长引用来源、深度研究、学术搜索 |
| **中文/本土** — 中国行业数据、政策、中文媒体 | Grok (`grok`) 或 ChatGPT (`chatgpt`) | 中文内容覆盖面广 |

**判断逻辑**:
```
if data_hint 包含 "最新/趋势/热点/动态/市场":
    ai_target = "grok"
elif data_hint 包含 "学术/研究/理论/历史/分析":
    ai_target = "perplexity"
else:
    ai_target = "chatgpt"  # 默认：技术/数据类
```

---

## 2.4 搜索计划 JSON 格式

保存到 `_research/step2_search_plan/search_plan.json`：

```json
{
  "generated_at": "2026-06-27",
  "outline_source": "_research/step1_outline/outline.json",
  "total_pages": 15,
  "search_targets": 10,
  "skipped_pages": 5,
  "pages": [
    {
      "page_id": "P01",
      "title": "封面",
      "skip_search": true,
      "reason": "封面页无需搜索"
    },
    {
      "page_id": "P03",
      "title": "开场: AI 行业的惊人增长",
      "skip_search": false,
      "topic": "2024-2025 AI 行业增长数据与里程碑事件",
      "keywords": ["AI market size 2025", "AI industry growth rate", "AI funding rounds 2025", "AI breakthroughs"],
      "content_type": "data",
      "ai_target": "chatgpt",
      "source_tier": "tier1",
      "priority": 1,
      "data_hint": "需要具体数字: 市场规模、增长率、融资额"
    },
    {
      "page_id": "P04",
      "title": "核心论点: 大模型竞争格局",
      "skip_search": false,
      "topic": "大语言模型竞争格局与最新动态",
      "keywords": ["LLM competition 2025", "GPT vs Claude vs Gemini", "model benchmarks"],
      "content_type": "trend",
      "ai_target": "grok",
      "source_tier": "tier1",
      "priority": 1,
      "data_hint": "最新模型发布、性能对比、市场份额"
    }
  ]
}
```

---

## 2.5 同步信息

当用户提供了源文件时，对于源文件中已有充足素材的页面，标记 `skip_search: true` 并注明 `reason: "source material sufficient"`。

---

## 2.6 输出验证

检查清单：
- [ ] 每个 `needs_data: true` 的页面都有对应的搜索计划
- [ ] 每个搜索计划都有明确的 `ai_target`
- [ ] 关键词具体、可搜索（非抽象概念）
- [ ] 高优先级页面排在前面
- [ ] `search_plan.json` 是合法 JSON

---

## 交接

```
下一步输入: _research/step2_search_plan/search_plan.json
下一步工作流: step3_search.md
```
