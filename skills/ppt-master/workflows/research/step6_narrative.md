---
description: 深度调研 Step 6 — 叙事构建。基于结构化分析结果，构建完整的故事弧叙事文档。
---

# Step 6: 叙事构建（Narrative Construction）

> 基于 Step 5 的分析结果，构建完整的叙事文档。采用 7 段式故事弧，含深度分析标记和页面节奏计划。

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
| DEEP_DIVE 标记 | ≥5 个 |
| PAGE_PLAN | 完整覆盖所有页面 |

不满足任何一项 → 返回 Step 3 补充搜索。

---

## 6.1 故事弧结构

固定 7 段式结构：

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
<!-- DEEP_DIVE type="data" -->

### 证据块 B: {论点标题}
> 字数: ≥200字
<!-- DEEP_DIVE type="compare" -->

<!-- TRANSITION -->
prev_summary: 核心论点概述
next_hook: 引出转折

## 4. 转折 (Turning Point)
> 字数: ≥300字
<!-- DEEP_DIVE type="story" -->

提供出人意料的视角或发现。

<!-- TRANSITION -->
prev_summary: 转折要点
next_hook: 引出影响分析

## 5. 影响与启示 (Implications)
> 字数: ≥400字
<!-- DEEP_DIVE type="timeline" -->

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

## 6.2 深度分析页规则

每个 DEEP_DIVE 标记对应 PPT 中的一个深度分析页面：

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

## 6.3 PAGE_PLAN 块

报告末尾必须包含 `<!-- PAGE_PLAN -->` 块：

```markdown
<!-- PAGE_PLAN
P01: cover
P02: toc
P03: content — 开场钩子
P04: content — 核心论点A
P05: deep_dive:data — 论点A数据支撑
P06: content — 核心论点B
P07: deep_dive:compare — 论点B对比分析
P08: content — 核心论点C
P09: deep_dive:timeline — 发展历程
P10: transition — 转折
P11: deep_dive:story — 案例故事
P12: content — 影响与启示
P13: synthesis — 总结
P14: ending
-->
```

每页必须标注图片来源和讲解关系：

```markdown
P04: content — 核心论点A [AI图, follows layout slot 1160x425]
P05: deep_dive:data — 论点A数据支撑 [网络素材: p05_case_chart.jpg]
```

**内容页+讲解页规则**：每个可展开核心论点必须形成 `content → deep_dive` 单元。若某个内容页没有讲解页，必须在 PAGE_PLAN 中写明原因（例如“概念承接页，无独立证据展开”）。

---

## 6.4 增量写入（防超时）

分 3 轮写入 `_research/step6_narrative/research_report.md`：

| 轮次 | 内容 | 方式 |
|------|------|------|
| Round 6.4a | 第 1-2 章 + 过渡 | 新建文件写入 |
| Round 6.4b | 第 3-4 章 + 过渡 | 追加写入 |
| Round 6.4c | 第 5-7 章 + 来源 + PAGE_PLAN | 追加写入 |

---

## 6.5 质量检查

⛔ **BLOCKING**: 完成后检查深度合同：

- [ ] 总字数 ≥ 3000
- [ ] 每章 ≥ 400 字
- [ ] 第 3 章有 2-4 个证据块，每个 ≥ 200 字
- [ ] 第 4 章 ≥ 300 字
- [ ] DEEP_DIVE 标记 ≥ 5 个
- [ ] PAGE_PLAN 覆盖所有页面
- [ ] 所有 TRANSITION 标记完整（prev_summary + next_hook）
- [ ] 未验证事实已标注

不满足 → 自动返回 Step 3 补充搜索，然后重新执行 Step 4-6。

---

## 交接

```
下一步输入: _research/step6_narrative/research_report.md + step5 analysis
下一步工作流: step7_visual.md
```
