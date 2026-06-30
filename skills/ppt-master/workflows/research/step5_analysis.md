---
description: 深度调研 Step 5 — 结构化分析。对汇总文档进行交叉验证、数据提取和叙事节点构建。
---

# Step 5: 结构化分析（Structured Analysis）

> 对 Step 4 的汇总文档进行深度分析：交叉验证事实、提取结构化数据、构建叙事节点、规划演讲深度。

**输入**: `_research/step4_consolidated/consolidated.md`
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

## 5.4 研究丰富度评估

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

## 5.5 构建叙事节点

确定 3-6 个叙事节点，构建故事弧：

1. **开场钩子** (Opening Hook) — 引起注意力的事实或问题
2. **问题定义** (Problem Definition) — 为什么这个问题重要
3. **证据块** (Evidence Blocks) — 支撑核心论点的数据和案例
4. **转折点** (Turning Point) — 出人意料的发现或视角转换
5. **综合** (Synthesis) — 将所有证据串联为完整论述
6. **前瞻** (Forward Look) — 展望未来、行动建议

---

## 5.6 规划演讲深度

对每个核心论点确定深度展开类型：

| 类型 | 适用场景 | 产出页类型 |
|------|---------|-----------|
| `timeline` | 发展历程、事件序列 | 时间轴布局 |
| `compare` | 方案对比、产品对比 | 对比表格布局 |
| `data` | 数据密集型论证 | 数据仪表板布局 |
| `quote` | 权威观点支撑 | 大字引述布局 |
| `story` | 案例故事、用户故事 | 叙事图文布局 |

---

## 5.7 输出 JSON

增量写入 `_research/step5_analysis/research_analysis.json`（3 轮防超时）：

**Round 5.7a**: 来源和维度
**Round 5.7b**: 交叉验证和结构化数据（read → merge → save）
**Round 5.7c**: 叙事节点和演讲深度（read → merge → save）

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
  "richness_assessment": {...},
  "content_options": [...],
  "narrative_nodes": [...],
  "speaking_depth": {
    "P04": {"type": "data", "allocated_pages": ["P09", "P10"]},
    "P05": {"type": "compare", "allocated_pages": ["P11"]}
  }
}
```

---

## 交接

```
下一步输入: _research/step5_analysis/research_analysis.json + consolidated.md
下一步工作流: step6_narrative.md
```
