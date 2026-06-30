---
description: 可选分批生成模式。Executor 每生成 N 页后暂停，等待用户视觉确认，后续批次吸收反馈。适用于 20+ 页长 deck 或视觉风格要求高的项目。
---

# 批次审阅工作流（Batch Review）

> 适用于长 deck 或高质量要求项目。Executor 每生成一批后暂停，收集用户视觉反馈，后续批次吸收修正方向。默认不启用——需显式触发。
>
> Adapted from PPT Hell's batch discipline: "后续页面必须吸收当前批次视觉审阅反馈后再生成"。

## When to Activate

| Trigger | Example |
|---------|---------|
| User explicit request | "分批审阅" / "batch review" / "逐批确认" / "每 5 页确认一次" |
| confirm_ui result | `generation_mode: "batch-review"` in result.json |
| Long deck + quality emphasis | User says "认真做" / "高质量" + page count > 15 |

**Default pipeline (no batch-review)**: Executor generates all pages sequentially → quality gates → post-processing. This workflow wraps Step 6 with intermediate checkpoints.

## Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `batch_size` | 5 | Pages per batch (matches visual-review.md K=5) |
| `feedback_carry` | true | Later batches read earlier batch feedback as style context |

User can override: "每 3 页确认一次" → batch_size = 3.

---

## Flow

### Pre-flight

1. Read `spec_lock.md` page_rhythm to determine page order
2. Partition pages into batches: `ceil(total_pages / batch_size)`
3. Create workspace: `<project>/.batch_review/`
4. Announce: "已启用批次审阅模式。共 {N} 页，分为 {M} 批，每批 {batch_size} 页。"

### Per-Batch Loop

For batch `i` (1-indexed):

#### 2a. Generate

- Generate pages in this batch sequentially (same Executor rules: per-page spec_lock re-read)
- If `feedback_carry` and previous batch feedback exists:
  - Read `<project>/.batch_review/batch_{i-1:02d}.json`
  - Apply style corrections as additional context when generating this batch

#### 2b. Quality Check

```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path>/svg_output \
  --integrated-review --ir-output <project>/.batch_review/review_{i:02d}.json
```

Fix any `must_fix` issues before proceeding.

#### 2c. Visual Self-Check

Run [`visual-review.md`](visual-review.md) on current batch pages only (set K = batch_size).

#### 2d. Present to User (BLOCKING)

Show user:
- PNG previews of current batch
- Summary: "批次 {i}/{M} 完成。{batch_size} 页已生成。"
- Ask: "请确认本批次，或指出需要修改的页面。"

#### 2e. Collect Feedback

| User Response | Action |
|---------------|--------|
| "通过" / "approve" / "继续" | Record approval, proceed to next batch |
| Points out specific issues | Enter revision-loop for affected pages in this batch only |
| "全部重做" | Regenerate entire batch with new direction |

#### 2f. Record Feedback

Write `<project>/.batch_review/batch_{i:02d}.json`:

```json
{
  "batch_id": "batch_01",
  "pages": ["P01", "P02", "P03", "P04", "P05"],
  "status": "approved",
  "feedback": "slightly reduce card padding on P03; otherwise good",
  "style_corrections": ["card padding: reduce by ~10px", "keep current color scheme"],
  "approved_at": "2026-06-29T12:00:00Z"
}
```

### After All Batches

1. Announce: "全部 {M} 批次已通过审阅。"
2. Proceed to Step 7 (post-processing) as normal

---

## Feedback Carry Mechanism

When generating batch N+1, Executor reads:
1. `spec_lock.md` (as always, per-page)
2. `.batch_review/batch_{N:02d}.json` → `style_corrections` array

Style corrections are treated as supplementary design guidance (same weight as `spec_lock.md ## decisions`). They inform the Executor's visual choices but do not override locked values (colors, fonts, etc.).

---

## Integration with SKILL.md

This workflow replaces Step 6's default sequential generation when activated. The pipeline becomes:

```
Step 5 (Images) → [Batch Review wraps Step 6] → Step 7 (Post-processing)
                   ├─ Batch 1: generate → check → review → approve
                   ├─ Batch 2: generate (+ feedback) → check → review → approve
                   └─ Batch N: ...
```

---

## Constraints

- Each batch MUST be approved before the next batch starts
- Do NOT pre-generate pages from future batches
- Revision within a batch follows the same revision-loop.md rules (including 2-round escalation)
- If user abandons batch-review mid-flow ("算了直接全部生成"), switch back to default pipeline for remaining pages
