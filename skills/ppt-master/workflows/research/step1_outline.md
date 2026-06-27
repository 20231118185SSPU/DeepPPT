---
description: 深度调研 Step 1 — 大纲生成。根据用户主题和需求生成 PPT 结构大纲，输出到 _research/step1_outline/。
---

# Step 1: 大纲生成（Outline Generation）

> 深度调研第一步。根据用户主题、背景需求和源文件（如有），生成结构化的 PPT 大纲。大纲是后续所有搜索、分析和叙事工作的基础。

**输入**: 用户主题 + 背景需求文档（如有） + 源文件（如有）
**输出**: `_research/step1_outline/outline.md` + `outline.json`

---

## 前置检查

| 用户输入 | 动作 |
|---------|------|
| 只有主题名称 | 直接进入大纲生成 |
| 主题 + 背景需求描述 | 以需求描述为大纲框架基础 |
| 主题 + 源文件（PDF/DOCX/URL/MD） | 先用 `source_to_md/` 脚本转为 Markdown，再基于内容生成大纲 |
| 主题 + 完整研究材料 | 跳过搜索步骤（Step 2-3），直接从 Step 4 开始 |

---

## 1.1 确认范围

⛔ **BLOCKING**: 一次性确认以下信息，不要逐项确认。

| 项目 | 说明 | 默认值 |
|------|------|--------|
| 主题 | PPT 的核心主题 | （来自用户输入） |
| 场景 | 工作汇报 / 发布会 / 学术报告 / 培训课件 / 其他 | 根据主题推断 |
| 目标受众 | 面向谁 | 根据场景推断 |
| 页数范围 | 建议页数 | 15-20 页 |
| 语言 | 输出语言 | 匹配用户输入语言 |
| 项目标识 | slug，用于文件夹名 | 自动从主题生成 |

确认后立即初始化项目目录：

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
mkdir -p <project>/_research/step1_outline
```

---

## 1.2 收集背景信息

如果用户提供了背景需求文档或源文件：

1. 读取所有源材料，提取核心信息
2. 识别关键数据点、论点、事实
3. 记录可用于大纲的素材清单

如果用户只有主题：

1. 使用 WebSearch 快速了解主题背景
2. 确定主题的核心维度（3-5 个）
3. 为每个维度确定叙事角度

---

## 1.3 生成大纲

生成 PPT 大纲，每页包含：

| 字段 | 说明 |
|------|------|
| `page_id` | 页码标识，如 `P01`, `P02` |
| `title` | 页面标题 |
| `content_bullets` | 核心内容要点（3-5 条） |
| `narrative_role` | 叙事功能：`cover` / `toc` / `transition` / `hook` / `evidence` / `deep_dive` / `synthesis` / `ending` |
| `needs_data` | 是否需要搜索数据支撑（true/false） |
| `needs_image` | 是否需要配图（true/false） |
| `data_hint` | 如果 needs_data=true，简述需要什么数据 |

**大纲节奏要求**（发布会/汇报场景）：

```
P01: 封面（cover）
P02: 目录/议程（toc）
P03: 开场钩子 — 引起兴趣的惊人事实或问题（hook）
P04-P08: 核心内容页（evidence）— 每页一个核心论点
P09-P12: 深度分析页（deep_dive）— 数据对比、时间线、案例分析
P13: 转折/展望（transition）
P14: 总结/行动号召（synthesis）
P15: 结尾页（ending）
```

每种场景的节奏模板不同，根据 1.1 确认的场景选择合适模板。

---

## 1.4 输出文件

### `outline.md`（人类可读）

```markdown
# PPT 大纲: <主题>

## 场景: <场景类型>
## 目标受众: <受众>
## 预计页数: <N> 页

---

### P01 — 封面
- 标题: <标题>
- 副标题: <副标题>

### P02 — 目录
- ...

### P03 — <开场标题>
- 叙事功能: hook
- 核心要点:
  - ...
- 数据需求: <需要什么数据>
- 配图需求: <需要什么类型的图>

---
（每页同上格式）
```

### `outline.json`（结构化，供下游解析）

```json
{
  "topic": "...",
  "scenario": "presentation",
  "audience": "...",
  "language": "zh",
  "total_pages": 15,
  "pages": [
    {
      "page_id": "P01",
      "title": "...",
      "content_bullets": ["...", "..."],
      "narrative_role": "cover",
      "needs_data": false,
      "needs_image": true,
      "data_hint": null
    }
  ]
}
```

---

## 1.5 用户确认

⛔ **BLOCKING**: 展示大纲给用户确认。用户可以：

1. **确认** → 进入 Step 2
2. **修改** → 调整页数、内容、顺序后重新确认
3. **补充** → 提供更多背景信息后重新生成

确认后将大纲保存到 `_research/step1_outline/`。

---

## 交接

大纲确认后，进入 Step 2（搜索需求拆分）：

```
下一步输入: _research/step1_outline/outline.json
下一步工作流: step2_search_plan.md
```
