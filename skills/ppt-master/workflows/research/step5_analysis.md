---
description: 深度调研 Step 5 — 结构化分析。对汇总文档进行交叉验证、数据提取和叙事节点构建。
---

# Step 5: 结构化分析（Structured Analysis）

> 对 Step 4 的汇总文档进行深度分析：交叉验证事实、提取结构化数据、构建叙事节点、规划演讲深度。

**输入**: `_research/step4_consolidated/consolidated.md` + `ppt_brief.json`（若存在）+ 已确认的用户上下文
**输出**: `_research/step5_analysis/research_analysis.json`

**Hard rule**: 本步骤只输出结构化分析。不得在这里写完整叙事报告、视觉策略、图片提示词或 SVG 设计方案。

---

## 5.1 来源注册

提取所有来源 URL，构建来源注册表：

```json
{
  "source_id": "S01",
  "url": "https://...",
  "tier": 1,
  "published_date": "2025-03",
  "author": "...",
  "source_type": "industry_report",
  "key_facts": ["..."]
}
```

来源分级：
- **Tier 1**: 官方报告、学术论文、权威媒体
- **Tier 2**: 行业博客、专业分析、知名媒体
- **Tier 3**: 社交媒体、论坛讨论、AI 生成内容
- **Tier 4**: 来源不明、无法验证

---

## 5.2 交叉验证

对汇总文档中的每条事实性声明进行验证：

| 验证状态 | 标准 | 标记 |
|---------|------|------|
| `multi_verified` | ≥2 个独立 Tier 1-2 来源确认 | ✅ |
| `single_verified` | 1 个 Tier 1 来源确认 | ⚠️ |
| `corroborated` | ≥2 个 Tier 2-3 来源一致 | ⚠️ |
| `unverified` | 仅 1 个来源或来源质量低 | ❌ |

**规则**: `unverified` 的事实在后续叙事中必须标注为"据报道"或"有待验证"。

---

## 5.3 提取结构化数据

从汇总文档中提取：

1. **统计数据**: 数字、百分比、金额、排名
2. **时间线事件**: 按时间排序的关键事件
3. **对比数据**: 产品对比、方案对比、前后对比
4. **关键实体**: 人物、公司、产品、技术
5. **专家引述**: 有出处的直接引述

每条数据必须关联来源 ID。

---

## 5.4 咨询证据层（条件启用）

仅在咨询、管理层简报、金字塔汇报、董事会、投资者、战略分析或其他高密度决策型演示中启用。根据 `ppt_brief.json` 的目标、受众和使用场景，以及用户已确认的上下文判断；通识教育、作品展示、叙事分享和轻量营销自动关闭，不为此单独询问用户。不得仅因材料中出现数据就自动启用。

无论是否启用，都在顶层记录判定及理由：

```json
{
  "consulting_evidence": {
    "enabled": true,
    "reason": "董事会需要基于证据作出市场进入决策",
    "source": "ppt_brief"
  }
}
```

`source` 只能是 `user_request`、`ppt_brief` 或 `orchestrator_classification`，用于记录本次路由依据；它不改变用户已确认的目标。

启用时，额外输出顶层 `evidence_table`。每个影响结论或决策的事实、数字、比较、建议、冲突和限制条件各占一行：

```json
{
  "evidence_id": "E001",
  "claim_or_data": "目标市场连续三年增长",
  "value": "18.4",
  "unit": "% CAGR",
  "period": "2023-2026E",
  "normalized_value": null,
  "normalized_unit": null,
  "source_ids": ["S01", "S03"],
  "source_location": "S01 p.27 table 4; S03 section 2.1",
  "confidence": "high",
  "conflict_or_caveat": "S03 使用自然年，S01 使用财年",
  "implication": "增长成立，但进入节奏需按财年口径复核",
  "recommended_visual": "带口径注释的趋势图"
}
```

**Hard rules**:

- `evidence_id` 使用稳定且唯一的 `E001` 格式；后续改写不得重排或复用已删除的 ID
- `value` / `unit` / `period` 保留来源原值；仅在可推导时填写 `normalized_value` / `normalized_unit`
- `source_ids` 必须存在于 `sources`，`source_location` 必须精确到文件、URL、页码、章节、表格、工作表、段落或时间戳
- `confidence` 只能是 `high` / `medium` / `low`，并与来源等级和交叉验证结果一致
- 缺失或薄弱证据使用 `not provided` / `not derivable` / `directional only` / `needs external verification` 明示；不得用常识补值或把预测写成事实
- `conflict_or_caveat`、`implication` 和 `recommended_visual` 不得省略；无已知冲突时写 `none identified`

未启用时同样写完整 `consulting_evidence` 回执，并省略 `evidence_table`；不得生成空洞占位行。

---

## 5.5 研究丰富度评估

对每个搜索维度评估丰富度：

| 维度 | 最低要求 |
|------|---------|
| 交叉验证事实 | ≥3 条 |
| 可量化数据 | ≥2 条 |
| 案例/故事 | ≥1 个 |
| 叙述段落 | ≥2 段 |
| 反面观点 | ≥1 条 |

**GATE**: 深度分析页数量必须 ≥ 内容页总数的 30%。不满足时需要返回 Step 3 补充搜索。

每个维度还必须输出 `content_options`，供后续内容筛选使用，避免用户进入选择环节时发现可选内容太少：

```json
{
  "dimension_id": "D01",
  "title": "市场规模与增长",
  "option_summary": "可讲市场规模、增长速度、区域差异、未来预测",
  "evidence_count": 8,
  "data_points": 4,
  "available_angles": ["宏观趋势", "区域对比", "投资变化", "风险反转"],
  "recommended_pages": 3
}
```

---

## 5.6 构建叙事节点

确定 3-6 个叙事节点，构建故事弧：

1. **开场钩子** (Opening Hook) — 引起注意力的事实或问题
2. **问题定义** (Problem Definition) — 为什么这个问题重要
3. **证据块** (Evidence Blocks) — 支撑核心论点的数据和案例
4. **转折点** (Turning Point) — 出人意料的发现或视角转换
5. **综合** (Synthesis) — 将所有证据串联为完整论述
6. **前瞻** (Forward Look) — 展望未来、行动建议

---

## 5.7 规划演讲深度

对每个核心论点确定深度展开类型：

| 类型 | 适用场景 | 产出页类型 |
|------|---------|-----------|
| `timeline` | 发展历程、事件序列 | 时间轴布局 |
| `compare` | 方案对比、产品对比 | 对比表格布局 |
| `data` | 数据密集型论证 | 数据仪表板布局 |
| `quote` | 权威观点支撑 | 大字引述布局 |
| `story` | 案例故事、用户故事 | 叙事图文布局 |

---

## 5.8 输出 JSON

增量写入 `_research/step5_analysis/research_analysis.json`（3 轮防超时）：

**Round 5.8a**: 来源、维度和咨询证据层判定
**Round 5.8b**: 交叉验证、结构化数据和条件 `evidence_table`（read → merge → save）
**Round 5.8c**: 叙事节点和演讲深度（read → merge → save）

```json
{
  "sources": [...],
  "dimensions": [...],
  "cross_verification": {
    "fact_id": {
      "claim": "...",
      "status": "multi_verified",
      "source_ids": ["S01", "S03"]
    }
  },
  "structured_data": {
    "statistics": [...],
    "timeline": [...],
    "comparisons": [...],
    "entities": [...],
    "quotes": [...]
  },
  "consulting_evidence": {
    "enabled": true,
    "reason": "...",
    "source": "ppt_brief"
  },
  "evidence_table": [...],
  "richness_assessment": {...},
  "content_options": [...],
  "narrative_nodes": [...],
  "speaking_depth": {
    "P04": {"type": "data", "allocated_pages": ["P09", "P10"]},
    "P05": {"type": "compare", "allocated_pages": ["P11"]}
  }
}
```

启用咨询证据层时，交付前验证 `evidence_table` 的 ID 唯一、`source_ids` 可解析，且每行均包含原值口径、精确来源位置、置信度、限制条件、含义和推荐视觉。关闭时验证顶层判定存在且没有伪造占位证据。

---

## 交接

```
下一步输入: _research/step5_analysis/research_analysis.json + consolidated.md
下一步工作流: step6_narrative.md
```
