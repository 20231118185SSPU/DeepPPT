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

**Hard rule**: 搜索计划必须同时覆盖“内容证据”和“素材证据”。`needs_data: false` 的封面、目录、过渡、结尾页可以跳过事实搜索，但不能自动跳过视觉参考图搜索；凡是后续需要 AI 生图的页面，都必须规划 1-3 张参考图来源。

不要只按页面拆搜索。先建立 4-6 个搜索维度，再把每一页绑定到一个或多个维度，确保逐页搜索继承前面的计划。

## 2.1a 维度级搜索设计

每个维度必须包含：

| 字段 | 要求 |
|------|------|
| `dimension_id` | `D01` / `D02` ... |
| `name` | 维度名称 |
| `why_it_matters` | 该维度对 PPT 叙事的作用 |
| `source_strategy` | Tier 1-2 优先来源清单，至少 3 类 |
| `search_rounds` | 至少 3 轮，每轮有不同目的 |
| `required_evidence` | 事实 / 数据 / 案例 / 反面观点 / 引言 |
| `asset_targets` | 参考图、网络素材、截图或 svg-native 卡片需求 |

**Machine gate mapping**: `research_gate.py` reads `dimensions[]`, `dimensions[].search_rounds`, `dimensions[].source_strategy` / `source_targets`, and each searched page's `dimension_ids`, `search_rounds`, `source_targets`, and `asset_requirements`. Missing fields are not prose issues; they become gate failures after Step 7.

**来源优先级**：

| Tier | 来源类型 | 用途 |
|------|----------|------|
| Tier 1 | 官方报告、论文、监管/标准机构、公司一手资料、原始数据集 | 核心事实和数据 |
| Tier 2 | 权威媒体、专业研究机构、行业数据库、出版社/博物馆/百科类权威页 | 解释、案例、背景 |
| Tier 3 | 社交平台、论坛、视频、博客、社区讨论 | 观点、趋势、文化语境 |
| Tier 4 | AI 摘要、无来源聚合、转载页 | 只能作线索，不能作事实依据 |

---

## 2.2 分析每页搜索需求

对每个需要搜索的页面：

1. **解读 data_hint** — 该页需要什么类型的数据
2. **生成搜索关键词** — 3-5 个精准关键词
3. **确定内容类型** — 用于分配 AI 工具
4. **绑定维度** — 写入 `dimension_ids`
5. **继承搜索轮次** — 从维度计划中挑选该页必须执行的 2-4 轮搜索
6. **规划素材** — 写清参考图 / 网络素材 / 截图 / 信息图需求和目标尺寸
7. **评估优先级** — 核心论点页 > 数据支撑页 > 背景页

---

## 2.3 AI 工具分配规则

按内容类型选择最适合的 AI 搜索工具：

| 内容类型 | AI 工具 | 理由 |
|---------|---------|------|
| **新闻/趋势** — 最新动态、市场趋势、行业热点、社交媒体 | Grok (`grok`) | 实时信息获取能力强，接入 X/Twitter |
| **技术/数据** — 统计数据、技术参数、产品规格、对比数据 | Kimi (`kimi`) 或 DeepSeek (`deepseek`) | 擅长结构化信息整理、长文本分析、数据处理 |
| **学术/深度** — 历史背景、学术观点、理论分析、深度报道 | Perplexity (`perplexity`) | 擅长引用来源、深度研究、学术搜索 |
| **中文/本土** — 中国行业数据、政策、中文媒体 | DeepSeek (`deepseek`) 或通义 (`tongyi`) | 中文内容覆盖面广，本土来源可靠 |

**判断逻辑**:
```
if data_hint 包含 "最新/趋势/热点/动态/市场":
    ai_target = "grok"
elif data_hint 包含 "学术/研究/理论/历史/分析":
    ai_target = "perplexity"
elif data_hint 包含 "中文/国内/政策/法规/本土":
    ai_target = "deepseek"  # 或 tongyi
else:
    ai_target = "kimi"  # 默认：技术/数据类
```

---

## 2.4 搜索计划 JSON 格式

保存到 `_research/step2_search_plan/search_plan.json`：

```json
{
  "generated_at": "2026-06-27",
  "outline_source": "_research/step1_outline/outline.json",
  "total_pages": 15,
  "quality_contract": {
    "dimensions": 5,
    "min_rounds_per_dimension": 3,
    "min_tier12_sources_per_dimension": 2,
    "min_total_sources": 15
  },
  "dimensions": [
    {
      "dimension_id": "D01",
      "name": "市场规模与增长",
      "why_it_matters": "为开场钩子和核心论证提供可量化证据",
      "source_strategy": ["official reports", "industry databases", "analyst research"],
      "search_rounds": [
        {
          "round_id": "D01-R1",
          "purpose": "锁定最新市场规模与增长率",
          "queries": ["AI market size 2025 official report", "AI industry CAGR 2024 2025"],
          "preferred_sources": ["official report", "analyst report"],
          "ai_target": "kimi"
        }
      ],
      "required_evidence": ["statistics", "case", "counterpoint"],
      "asset_targets": ["market growth chart screenshot", "report cover/reference visual"]
    }
  ],
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
      "dimension_ids": ["D01"],
      "keywords": ["AI market size 2025", "AI industry growth rate", "AI funding rounds 2025", "AI breakthroughs"],
      "search_rounds": ["D01-R1", "D01-R2", "D01-R3"],
      "source_targets": {
        "tier12_min": 2,
        "total_min": 3,
        "preferred_domains": ["official reports", "analyst reports"]
      },
      "asset_requirements": [
        {
          "type": "web_asset",
          "purpose": "市场增长图或报告截图",
          "target_slot": {"width": 1160, "height": 425},
          "save_to": "_research/step3_search/images/p03_growth_chart.jpg"
        }
      ],
      "content_type": "data",
      "ai_target": "kimi",
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
- [ ] 有 4-6 个搜索维度
- [ ] 每个维度 ≥3 轮搜索
- [ ] 每个维度规划 ≥2 个 Tier 1-2 来源目标
- [ ] 每个 `needs_data: true` 的页面都有对应的搜索计划
- [ ] 每个 AI 生图页面都有参考图搜索计划
- [ ] 每个 deep-dive / comparison / data / timeline 页面都有素材图或 svg-native 信息卡计划
- [ ] 每个搜索计划都有明确的 `ai_target`
- [ ] 关键词具体、可搜索（非抽象概念）
- [ ] 高优先级页面排在前面
- [ ] `search_plan.json` 是合法 JSON
- [ ] `python3 ${SKILL_DIR}/scripts/research/research_gate.py <project>` will be able to read every required planning field after Step 7

⛔ **BLOCKING**: 将搜索计划摘要展示给用户确认。至少展示：搜索维度、每维度搜索轮次、优先来源类型、逐页素材计划、降级策略。用户确认后才能进入 Step 3。

---

## 交接

```
下一步输入: _research/step2_search_plan/search_plan.json
下一步工作流: step3_search.md
```
