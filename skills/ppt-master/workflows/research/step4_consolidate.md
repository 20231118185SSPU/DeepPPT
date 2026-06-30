---
description: 深度调研 Step 4 — 汇总。将所有逐页搜索结果按大纲顺序合并为一份结构化文档。
---

# Step 4: 汇总（Consolidation）

> 将 Step 3 的逐页搜索结果按大纲顺序合并为一份完整的结构化调研文档。去重、标注质量、标记信息缺口。

**输入**: `_research/step3_search/` 所有 `p{NN}_*.md` + `_research/step1_outline/outline.json`
**输出**: `_research/step4_consolidated/consolidated.md`

**Hard rule**: 本步骤只做汇总、去重、溯源和缺口标注。不得在这里写叙事报告、视觉策略、页面设计或 AI 生图提示词。

---

## 4.1 加载所有搜索结果

1. 读取 `_research/step1_outline/outline.json` 获取页面顺序
2. 读取 `_research/step3_search/search_manifest.json` 获取搜索元数据
3. 按 page_id 顺序读取所有 `p{NN}_*.md` 文件

---

## 4.2 合并与去重

按大纲页面顺序合并所有搜索结果：

1. **顺序排列**: 严格按 page_id 顺序（P01, P02, ...）
2. **去重**: 跨页面重复的信息只保留一次，后续页面引用"（详见 P{NN}）"
3. **来源保留**: 每条信息保留其原始来源 URL 和 AI 工具标识
4. **时间标注**: 标注信息的时效性（最新/历史/不确定）

---

## 4.3 标注信息质量

对每条信息进行质量评估：

| 标签 | 含义 |
|------|------|
| `[HIGH]` | 有明确来源、具体数字、可验证 |
| `[MEDIUM]` | 有来源但数据模糊，或来源权威性一般 |
| `[LOW]` | 无来源、AI 生成的概括性描述、无法验证 |
| `[GAP: ...]` | 信息缺失，标注需要补充什么 |

---

## 4.4 整合用户源文件

如果用户提供了原始文件（PDF/DOCX/URL）：

1. 将源文件内容按主题匹配到对应页面
2. 源文件信息标记为 `[SOURCE]`，优先级高于 AI 搜索结果
3. 源文件中的数据与 AI 搜索数据冲突时，标记 `[CONFLICT: ...]`

---

## 4.5 输出格式

`_research/step4_consolidated/consolidated.md`:

```markdown
# 调研汇总: {topic}

> 生成时间: {timestamp}
> 来源数: {total_sources}
> AI 搜索页面: {searched_count} / {total_pages}

---

## P01 — {标题}
（封面页，无搜索内容）

## P02 — {标题}
（目录页，无搜索内容）

## P03 — {标题}
### 来源
- ChatGPT 搜索 / {timestamp}
- WebSearch / {timestamp}

### 内容
[HIGH] 根据 Gartner 报告，2025年全球 AI 市场规模达到 5500 亿美元...
来源: https://gartner.com/...

[MEDIUM] 行业分析师预计增长率将保持在 30% 以上...

[GAP: 需要补充中国 AI 市场的单独数据]

### 图片素材
- AI 市场增长趋势图: images/p03_growth_chart.jpg
- 来源: Pexels (CC0)

---

## P04 — {标题}
### 来源
- Grok 搜索 / {timestamp}

### 内容
[HIGH] OpenAI 于2025年3月发布 GPT-5...
来源: https://openai.com/blog/...

[SOURCE] （来自用户原始文件）我们的产品定位是...

---
（每页同上格式）

## 信息缺口汇总

| 页面 | 缺口描述 | 建议补充方式 |
|------|---------|-------------|
| P03 | 中国 AI 市场数据 | 补充搜索: "中国AI市场规模 2025" |
| P07 | 竞品定价数据 | 用户提供或补充搜索 |

## 来源索引

| # | URL | 引用页面 | 可信度 |
|---|-----|---------|--------|
| 1 | https://... | P03, P05 | HIGH |
| 2 | https://... | P04 | MEDIUM |
```

---

## 4.6 质量检查

完成汇总后检查：

- [ ] 所有 `needs_data: true` 的页面都有内容（非空）
- [ ] 信息缺口已标注 `[GAP]`
- [ ] 跨页重复信息已去重
- [ ] 来源 URL 已保留
- [ ] 文件长度合理（预期 5000-15000 字）
- [ ] 来源索引总数 ≥15，或明确列出不足页面并返回 Step 3
- [ ] 每个搜索维度至少有 2 个 Tier 1-2 来源
- [ ] 每个页面列出已获取素材或 svg-native 降级声明
- [ ] 未做叙事重写，未输出视觉策略

---

## 交接

```
下一步输入: _research/step4_consolidated/consolidated.md
下一步工作流: step5_analysis.md
```
