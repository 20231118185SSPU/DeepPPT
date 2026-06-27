---
description: 深度调研 Step 3 — 逐页搜索。按搜索计划通过 Playwright 浏览器自动化调用 ChatGPT/Grok/Perplexity 逐页搜集资料。
---

# Step 3: 逐页搜索（Per-Page Search）

> 按 Step 2 的搜索计划，逐页通过浏览器自动化向不同 AI 搜索资料。每页独立搜索，结果按页保存。

**输入**: `_research/step2_search_plan/search_plan.json`
**输出**: `_research/step3_search/p{NN}_{topic}.md` + `search_manifest.json` + `images/`

---

## 前置条件

| 检查项 | 动作 |
|--------|------|
| `search_plan.json` 存在且合法 | 继续 |
| Playwright 可用（`python3 -c "from playwright.sync_api import sync_playwright"`） | 继续 |
| Playwright 不可用 | 降级到内置 WebSearch + WebFetch |

创建输出目录：
```bash
mkdir -p <project>/_research/step3_search/images
```

---

## 3.1 搜索执行

### 方式 A: 浏览器自动化（首选）

使用 `browse_ai.py` 脚本逐页搜索：

```bash
# 逐页搜索
python3 ${SKILL_DIR}/scripts/research/browse_ai.py \
  --batch <project>/_research/step2_search_plan/search_plan.json \
  --output-dir <project>/_research/step3_search/ \
  --chrome-profile "${CHROME_PROFILE}"
```

或手动逐页执行（当自动脚本遇到问题时）：

```
对 search_plan.json 中每个 skip_search=false 的页面:
  1. 根据 ai_target 选择 AI 服务
  2. 通过 Playwright MCP 打开对应 AI 网页
  3. 构建搜索提示词（见 3.2）
  4. 粘贴提示词并提交
  5. 等待 AI 回复完成
  6. 复制回复文本
  7. 保存到 p{NN}_{topic}.md
  8. 如果回复质量不足（<200字或无具体数据），重试一次
```

### 方式 B: 降级搜索（当浏览器自动化不可用时）

```
对每个需要搜索的页面:
  1. 使用内置 WebSearch 工具搜索关键词
  2. 使用 WebFetch 获取排名前 3 的结果全文
  3. 使用 web_to_md.py 提取结构化内容
  4. 合并搜索结果保存到 p{NN}_{topic}.md
```

---

## 3.2 搜索提示词模板

提示词根据页面的 `narrative_role` 和 `content_type` 自动生成。browse_ai.py 使用同样的模板逻辑。

### 按页面角色生成提示词

**cover / toc / ending**（封面/目录/结尾）:
> 这些页面通常 `skip_search: true`。如需搜索（如引用名言或行业背景），使用简短的通用模板。

**hook**（开场钩子）:
```
我需要一个引人注目的开场素材来展示「{topic}」这个主题。

请帮我找到:
1. 一个令人惊讶的事实或统计数据（必须有具体数字和来源）
2. 一个相关的名人引述或行业观点（注明出处）
3. 当前最热门的讨论话题或争议点

要求: 信息新鲜（优先2024-2025年），有明确来源URL。
```

**evidence**（核心论点支撑）:
```
我正在为PPT制作一个核心论点页面，主题是「{topic}」。

论点: {data_hint}

请帮我搜集支撑这个论点的证据:
1. 至少2个具体数据点（含数字、百分比、金额、年份）
2. 至少1个真实案例或行业标杆
3. 至少1个权威来源的引述
4. 来源URL（优先: 官方报告 > 权威媒体 > 行业博客）

输出格式: 每条证据后标注 [来源: URL]
```

**deep_dive**（深度分析）:
```
我需要深度分析材料来支撑「{topic}」的详细讲解页面。

分析角度: {data_hint}

请深入研究并提供:
1. 发展历程/时间线（关键节点 + 时间 + 事件）
2. 多角度对比数据（至少2个维度的对比）
3. 专家/机构观点（直接引述 + 出处）
4. 未来趋势预测（含具体预测数字和来源）
5. 反面观点或风险因素

要求:
- 每条信息必须有来源URL
- 数据必须是可验证的（不要模糊描述如"大幅增长"）
- 优先学术论文、官方报告、权威媒体
```

**transition / synthesis**（过渡/总结）:
```
我需要总结性材料来制作PPT的{role}页面，主题是「{topic}」。

请帮我找到:
1. 对主题的精炼总结（1-2句话概括核心观点）
3. 行动建议或未来展望（具体、可执行）
4. 适合放在PPT上的金句或金句式总结

要求: 简洁有力，适合PPT展示（每条不超过30字）。
```

### 按 AI 服务微调（后缀追加）

**→ ChatGPT**（追加到提示词末尾）:
```
请以结构化表格形式呈现数据。对每个数据点标注可信度（高/中/低）。
```

**→ Grok**（追加到提示词末尾）:
```
请优先提供最近3个月内的信息。包含社交媒体上的热门讨论角度。
```

**→ Perplexity**（追加到提示词末尾）:
```
请引用具体的学术论文、官方报告或权威媒体文章。每个关键数据点标注原始来源。
```

---

## 3.3 图片素材收集

在搜索每页内容的同时，收集相关图片：

1. 记录 AI 回复中提到的图片关键词
2. 使用 `image_search.py` 搜索对应图片：

```bash
python3 ${SKILL_DIR}/scripts/image_search.py \
  "{image_keyword}" \
  --filename p{NN}_img01.jpg \
  -o <project>/_research/step3_search/images/
```

3. 对于产品/场景图，使用 `--url-capture` 截图：

```bash
python3 ${SKILL_DIR}/scripts/image_search.py \
  --url-capture "{product_url}" \
  --filename p{NN}_screenshot.jpg \
  -o <project>/_research/step3_search/images/
```

---

## 3.4 搜索结果文件格式

每个 `p{NN}_{topic}.md` 文件格式：

```markdown
# P{NN}: {title}

## 搜索来源
- AI 工具: {ai_target}
- 搜索时间: {timestamp}
- 关键词: {keywords}

## 搜索结果

{AI 回复的完整文本}

## 图片素材
- {image_keyword}: {image_path_or_url}
- ...

## 质量评估
- 信息完整度: 高/中/低
- 数据可信度: 高/中/低
- 是否需要补充搜索: 是/否
```

---

## 3.5 降级策略

当某个 AI 服务不可用时的自动降级链：

```
chatgpt 不可用 → grok → perplexity → 内置 WebSearch
grok 不可用 → chatgpt → perplexity → 内置 WebSearch
perplexity 不可用 → chatgpt → grok → 内置 WebSearch
```

**降级触发条件**:
- 页面加载超时（30s）
- 需要登录但未登录
- 回复为空或过短（<100字）
- API 限流/错误

**降级记录**: 在 `search_manifest.json` 中记录每个页面实际使用的 AI 工具。

---

## 3.6 搜索清单

搜索全部完成后，生成 `search_manifest.json`：

```json
{
  "completed_at": "2026-06-27T12:00:00",
  "total_searched": 10,
  "total_skipped": 5,
  "fallback_used": 2,
  "results": [
    {
      "page_id": "P03",
      "ai_target": "chatgpt",
      "ai_used": "chatgpt",
      "output_file": "p03_AI行业增长.md",
      "char_count": 1580,
      "quality": "high",
      "images_collected": 2,
      "fallback": false
    }
  ]
}
```

---

## 交接

```
下一步输入: _research/step3_search/ 所有 p{NN}_*.md 文件
下一步工作流: step4_consolidate.md
```
