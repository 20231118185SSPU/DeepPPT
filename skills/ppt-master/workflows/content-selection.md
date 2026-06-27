---
description: 深度调研完成后、Strategist 大纲生成前，交互式筛选用户要放入 PPT 的核心内容维度。基于信息密度评分辅助用户取舍调研章节，输出结构化筛选结果供详细大纲工作流使用。
---

# 内容筛选工作流（Content Selection）

> 深度调研完成后、Strategist 大纲生成前，交互式筛选用户要放入 PPT 的核心内容维度。基于信息密度评分辅助用户取舍，输出结构化筛选结果供详细大纲工作流（`detailed-outline.md`）使用。

This workflow is **conditional**: it inserts between source processing and the Strategist phase only when the source material is a research report (from `deep-research` or `topic-research`). When the user provides a source file (PDF / DOCX / URL), the content is already defined — skip this workflow and proceed to SKILL.md Step 4 directly.

## When to Run

| Source material | Action |
|---|---|
| `research_report.md` exists (output of `deep-research` or `topic-research`) | Run this workflow |
| User-provided file (PDF / DOCX / URL / Markdown) | Skip — go to SKILL.md Step 4 |
| Chat content only (≥1 page of substantive text) | Skip — feed into SKILL.md Step 4 directly |

**Prerequisite**: `research_report.md` has been generated and saved to `<project>/sources/` (by `deep-research` or after `import-sources --move` from `topic-research`).

---

## Step 1: Parse Research Report

Read `<project>/sources/research_report.md`.

**1.1 Split into dimensions**

Split the document by H2 (`##`) and H3 (`###`) headings into **content dimensions**. Each dimension is an independent topical section of the research.

**1.2 Extract metadata per dimension**

For each dimension, extract:

| Field | Method |
|---|---|
| `title` | Heading text (H2/H3) |
| `summary` | First sentence of the section, or ≤30 chars summarizing the section |
| `density` | Info density score = `(dimension_word_count / total_word_count) × 10`, rounded to integer |

**1.3 Sort and filter**

- Sort dimensions by `density` descending (highest information density first)
- Discard dimensions with `density < 1` (less than 1% of total content — too thin to warrant PPT pages)
- If fewer than 3 dimensions remain after filtering, skip this workflow entirely — the content is too focused to require selection

---

## Step 2: Present to User

⛔ **BLOCKING**: present dimensions for interactive selection. Use the multi-round format below.

**2.1 Display format**

Present **2 dimensions per round**（not 4 — 因为 AskUserQuestion 工具限制最多 4 个选项，其中 2 个必须留给快捷选项），sorted by density descending. Each dimension is formatted as:

```
[维度标题] — {摘要}（信息密度：{X}/10）
```

**2.2 Quick options（MANDATORY — 每轮必须包含，不允许省略）**

Each round's AskUserQuestion call must use exactly 4 options: **2 content dimensions + 2 quick-action options**.

| Option slot | Content | Behavior |
|---|---|---|
| Option 1 | 维度 A | Select this dimension |
| Option 2 | 维度 B | Select this dimension |
| Option 3 | **"以上都选"** | Select both dimensions in this round, continue to next round |
| Option 4 | **"跳过本轮"** | Skip both dimensions in this round, continue to next round |

> **Why 2 dimensions per round, not 4**: The `AskUserQuestion` tool hard-limits to 4 options max. Reserving 2 slots for quick-action shortcuts is mandatory per this workflow. This means more rounds for 6+ dimensions, but each round is faster and the user always has a "select all" escape hatch.

The user may also select individual dimensions by name or number.

**2.3 Multi-round**

Continue rounds until all dimensions have been presented. Dimensions not selected in earlier rounds are still shown in later rounds (the user may change their mind).

---

## Step 3: Record Selection

After the user completes selection, write `<project>/content_selection.json`:

```json
{
  "selected_dimensions": [
    {
      "title": "维度标题",
      "summary": "摘要文本",
      "density": 8
    }
  ],
  "suggested_pages": 12,
  "selection_rounds": 3,
  "total_density": 24.5
}
```

**Field calculation**:

| Field | Rule |
|---|---|
| `selected_dimensions` | All dimensions the user selected, preserving density-sorted order |
| `total_density` | Sum of all selected dimensions' `density` values (float) |
| `suggested_pages` | `ceil(total_density / 1.5)`, clamped to **[8, 25]** |
| `selection_rounds` | Number of presentation rounds it took to complete selection |

---

## Step 4: Confirm Selection

⛔ **BLOCKING**: display the final selection summary and wait for user confirmation or modification.

**4.1 Summary display**

Present a compact summary:

```
已选维度（N 个）：
1. [维度A]（密度 8/10）
2. [维度B]（密度 6/10）
3. ...

建议页数：12 页（基于信息密度计算）

确认以上选择？回复"确认"继续，或告诉我想调整的部分。
```

**4.2 Modifications**

The user may:
- Remove a dimension (e.g., "去掉维度C")
- Add a dimension from the unselected pool
- Override the suggested page count (e.g., "改成 15 页")

Apply modifications, recalculate `suggested_pages`, update `content_selection.json`, and re-confirm.

**4.3 Confirmation**

On explicit confirmation (e.g., "确认" / "好" / "可以"), auto-proceed to the next phase (SKILL.md Step 3 — Template Option). The `detailed-outline` workflow will run automatically inside Step 4 if `content_selection.json` exists.

---

## Gate

Before proceeding, verify:

| Check | Threshold |
|---|---|
| `research_report.md` exists and has H2/H3 structure | Required |
| At least 3 content dimensions found | Required |
| At least 1 dimension selected | Required |

If the H2/H3 structure check fails (flat document without section headings), skip this workflow — the content is unstructured and the Strategist should handle outline generation directly.

---

## Output

| Artifact | Path | Purpose |
|---|---|---|
| Content selection record | `<project>/content_selection.json` | Feeds into `detailed-outline.md` as input; Strategist reads it during Eight Confirmations to understand content priorities |

---

## Integration Points

| Direction | Target | Data |
|---|---|---|
| **Reads from** | `<project>/sources/research_report.md` | Research content to parse and score |
| **Feeds into** | `detailed-outline.md` workflow | `content_selection.json` drives narrative arc and page allocation |
| **Feeds into** | Strategist (SKILL.md Step 4) | Selected dimensions inform content outline (`§IX`) and page count |
| **Referenced by** | `CLAUDE.md` routing table | Trigger condition: after research, before Strategist |
