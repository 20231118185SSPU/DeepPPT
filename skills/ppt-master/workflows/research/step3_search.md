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

### 通用模板

```
请帮我搜索并整理以下主题的详细信息。

主题: {topic}
关键词: {keywords}

请提供:
1. 核心事实和数据（含具体数字和年份）
2. 来源链接（URL）
3. 关键引述（如有）
4. 相关图片搜索建议（关键词）

要求:
- 信息必须有明确来源
- 数据必须包含具体数字，不要模糊描述
- 如果有争议信息，请列出不同观点
- 请用 {language} 回答
```

### 按 AI 服务调整

**ChatGPT** (技术/数据):
```
你是数据分析专家。请搜索并整理以下技术/数据主题。
重点关注: 统计数据、技术参数、对比表格、产品规格。
请以结构化格式输出，包含表格。
```

**Grok** (新闻/趋势):
```
请搜索以下主题的最新动态和趋势。
重点关注: 最新新闻、行业动态、市场趋势、社交媒体讨论。
请包含信息的发布时间，确保是最新信息。
```

**Perplexity** (学术/深度):
```
请深入研究以下主题。
重点关注: 学术观点、历史背景、深度分析、权威来源。
请引用具体来源，优先使用学术论文、权威媒体和官方报告。
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
