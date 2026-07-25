---
description: 深度调研 Step 6 — 叙事构建。基于结构化分析结果，构建完整的故事弧叙事文档。
---

# Step 6: 叙事构建（Narrative Construction）

> 基于 Step 5 的分析结果，构建完整的叙事文档。采用 7 段式故事弧，含可选的深度分析标记和页面节奏计划。

**输入**: `_research/step5_analysis/research_analysis.json` + `_research/step4_consolidated/consolidated.md`
**输出**: `_research/step6_narrative/research_report.md`

**Hard rule**: 本步骤只构建可讲述的研究报告、叙事弧和页面节奏计划。不得在这里生成视觉策略、配色、AI 图片提示词或 SVG 布局细节。

---

## 6.0 叙事深度合同

| 项目 | 最低要求 |
|------|---------|
| 总报告字数 | ≥3000 字（中文） |
| 每章字数 | ≥400 字 |
| 第 3 章证据块 | 2-4 个，每个 ≥200 字 |
| 第 4 章转折 | ≥300 字 |
| DEEP_DIVE 标记 | 仅在证据确需独立深挖段时使用；无全局数量配额 |
| PAGE_PLAN | 完整覆盖所有页面 |

叙事正文或机器合同不合格 → 留在 Step 6 修复；只有明确缺少来源或证据时才返回 Step 3 补搜，再重跑 Step 4-6。

---

## 6.1 SCR 备选（条件启用）

当 `research_analysis.json.consulting_evidence.enabled` 为 `true` 时，在撰写正文前基于 `evidence_table` 形成 2-3 条 SCR 备选，并把结果写入报告开头的机器可读注释块：

```markdown
<!-- STORYLINE_ALTERNATIVES
{
  "enabled": true,
  "recommended_storyline": {
    "storyline_id": "S2",
    "rationale": "证据链最完整，且直接支持董事会决策"
  },
  "storyline_alternatives": [
    {
      "storyline_id": "S1",
      "scr": {
        "situation": "...",
        "complication": "...",
        "resolution": "..."
      },
      "management_conclusion": "...",
      "key_evidence_ids": ["E001", "E004", "E007"],
      "caveats": ["..."],
      "audience_fit": "适合需要判断市场吸引力、但尚未决定时点的管理层",
      "rejected_reason": "证据能说明市场吸引力，但不足以支持进入时点",
      "page_material_pool": ["趋势图", "口径对比表", "风险侧栏"]
    },
    {
      "storyline_id": "S2",
      "scr": {
        "situation": "...",
        "complication": "...",
        "resolution": "..."
      },
      "management_conclusion": "...",
      "key_evidence_ids": ["E002", "E005", "E008"],
      "caveats": ["..."],
      "audience_fit": "适合需要本轮决定进入路径与优先级的董事会",
      "rejected_reason": null,
      "page_material_pool": ["情景矩阵", "行动路线图", "证据注释"]
    }
  ]
}
-->
```

每条备选必须满足：

| 字段 | 要求 |
|------|------|
| `storyline_id` | 稳定且唯一的 `S1` / `S2` / `S3` |
| `scr` | Situation、Complication、Resolution 各用一句可验证陈述 |
| `management_conclusion` | 明确支持的管理层判断或行动 |
| `key_evidence_ids` | 仅引用 `evidence_table` 中存在的 ID；优先 5-8 条，证据不足时按实际数量并在 `caveats` 明示 |
| `caveats` | 写出会削弱结论的冲突、条件或缺口 |
| `audience_fit` | 说明该论证适合的受众、场景和决策需求 |
| `rejected_reason` | 每个未选项必填；推荐项固定为 `null` |
| `page_material_pool` | 可直接转成页面的数字、表格、图表、矩阵、时间线、注释或侧栏 |

顶层 `recommended_storyline` 必须引用且只引用 `storyline_alternatives` 中的一条备选，其 `rationale` 说明该项与目标、受众和证据的匹配。比较备选时至少检查论证是否明确、证据是否足够、结论是否可执行、页面物料是否可视化，以及限制条件是否被诚实保留。选择证据最强且最贴合用户目标的一条驱动后续 7 段式正文；其他备选只留在注释块中，不混入 PAGE_PLAN。

**Default — no extra user stop**: 自动记录推荐项和弃选原因并继续本步骤。只有用户明确要求先审阅故事线时，才暂停等待确认。咨询证据层关闭时不生成占位 SCR 块。

---

## 6.2 故事弧结构

固定 7 段式正文骨架；深挖标记不是骨架成员。只有证据确需独立画布时，才在对应证据块前插入 `<!-- DEEP_DIVE type="<type>" -->`；整篇可以是 0 个或多个。下列模板故意不预置任何深挖标记：

```markdown
## 1. 开场 (Opening)
> 字数: ≥400字

用一个引人注目的事实、问题或故事开场。
引用 research_analysis.json 中的 narrative_nodes[0] (Opening Hook)。

<!-- TRANSITION -->
prev_summary: （无，这是开场）
next_hook: 引出背景问题

## 2. 背景 (Background)
> 字数: ≥400字

提供理解主题所需的背景信息。
解释为什么这个主题值得讨论。

<!-- TRANSITION -->
prev_summary: 简述背景
next_hook: 引出核心论点

## 3. 核心论点 (Core Argument)
> 字数: ≥1200字（含证据块）

展开核心论述，每个论点用证据支撑。
证据块类型由 speaking_depth 决定（timeline/compare/data/quote/story）。

### 证据块 A: {论点标题}
> 字数: ≥200字

### 证据块 B: {论点标题}
> 字数: ≥200字

<!-- TRANSITION -->
prev_summary: 核心论点概述
next_hook: 引出转折

## 4. 转折 (Turning Point)
> 字数: ≥300字

提供出人意料的视角或发现。

<!-- TRANSITION -->
prev_summary: 转折要点
next_hook: 引出影响分析

## 5. 影响与启示 (Implications)
> 字数: ≥400字

分析主题的影响范围和未来启示。

<!-- TRANSITION -->
prev_summary: 影响概述
next_hook: 引出结论

## 6. 结论 (Conclusion)
> 字数: ≥400字

总结核心发现，提出行动建议或思考方向。

## 7. 来源 (Sources)
列出所有引用来源。
```

---

## 6.3 深度分析页规则

每个实际写入的 DEEP_DIVE 标记对应 PPT 中的一个深度分析页面：

| 类型 | 布局 | 说明 |
|------|------|------|
| `timeline` | journal-style timeline | 发展历程、事件时间轴 |
| `compare` | split comparison | 两栏或多栏对比 |
| `data` | data dashboard | 数据仪表板、图表密集 |
| `quote` | full-page quote | 大字引述、专家观点 |
| `story` | narrative illustration | 叙事配图、案例故事 |
| `branching` | branching path | 分支决策树、流程图 |
| `infographic` | visual infographic | 信息图、统计可视化 |

**规则**:
- 每个 DEEP_DIVE 页面不与其他页面共享数据点
- 深度分析页标题必须引用前一页内容页的核心论点
- 每种类型最多使用 2 次（避免重复）

---

## 6.4 PAGE_PLAN 块

报告末尾必须包含 `<!-- PAGE_PLAN -->` 块：

```markdown
<!-- PAGE_PLAN
P01: cover
P02: toc
P03: content — 开场钩子
P04: content — 核心论点A（论点与主证据同页）
P05: content — 核心论点B（提出待解问题）
P06: deep_dive:data — 论点B数据支撑 [split: 数据需独立画布，回答 P05]
P07: transition — 转折
P08: content — 影响与启示
P09: synthesis — 总结
P10: ending
-->
```

每页必须标注图片来源和讲解关系：

```markdown
P04: content — 核心论点A [AI图, follows layout slot 1160x425]
P05: deep_dive:data — 论点A数据支撑 [网络素材: p05_case_chart.jpg]
```

**内容页+讲解页规则**：论点与主证据能在同页保持清晰、可追溯、可解释时，保留在一个 content 页。仅当证据确需独立画布时才形成 `content → deep_dive` 单元，并在 PAGE_PLAN 中写明拆页理由与前页提出、后页回答的问题；不得按配额拆页。

---

## 6.5 增量写入（防超时）

分 3 轮写入 `_research/step6_narrative/research_report.md`：

| 轮次 | 内容 | 方式 |
|------|------|------|
| Round 6.5a | 条件 SCR 备选 + 第 1-2 章 + 过渡 | 新建文件写入 |
| Round 6.5b | 第 3-4 章 + 过渡 | 追加写入 |
| Round 6.5c | 第 5-7 章 + 来源 + PAGE_PLAN | 追加写入 |

---

## 6.6 质量检查

⛔ **BLOCKING**: 完成后检查深度合同：

- [ ] 总字数 ≥ 3000
- [ ] 每章 ≥ 400 字
- [ ] 第 3 章有 2-4 个证据块，每个 ≥ 200 字
- [ ] 第 4 章 ≥ 300 字
- [ ] DEEP_DIVE 标记仅用于确需独立深挖的证据段，且每个都能映射到 PAGE_PLAN
- [ ] PAGE_PLAN 覆盖所有页面
- [ ] 所有 TRANSITION 标记完整（prev_summary + next_hook）
- [ ] 未验证事实已标注
- [ ] 若咨询证据层已启用：存在 2-3 条唯一 SCR 备选，`recommended_storyline` 恰好引用其中一条，未选项均有弃选原因
- [ ] 若咨询证据层已启用：所有 `key_evidence_ids` 均能解析到 `evidence_table`，缺口未被编造补齐

叙事正文、PAGE_PLAN 或 SCR 合同不满足 → 留在 Step 6 修复；仅当检查明确指向来源或证据缺口时，返回 Step 3 补充搜索，然后重新执行 Step 4-6。

---

## 交接

```
下一步输入: _research/step6_narrative/research_report.md + step5 analysis
下一步工作流: step7_visual.md
```
