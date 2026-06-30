---
name: revision-loop
description: >
  Multi-turn local revision workflow for PPT-master2. Applies targeted patches
  to generated SVG pages without full regeneration. Inspired by MemSlides'
  Plan-Act-Guard pipeline.
---

# Revision Loop Workflow

> Apply localized, minimal-effective edits to generated SVG pages through a
> structured Plan-Act-Guard pipeline. Each revision round targets only the
> affected elements, preserving all non-targeted content.

## When to Enter

After Step 6 (Executor) completes and all SVGs pass quality check, if the user:
- Says "修改" / "调整" / "修订" / "改一下" / "revise" / "tweak" / "fix"
- Submits annotations in live-preview browser
- Says "不满意" / "not happy with" + specifies a page or element
- Asks to change colors, fonts, text, layout of specific elements

## Prerequisites

- All SVGs generated in `svg_output/`
- Quality check passed
- Snapshot saved (auto-created on entry)

## Step 1: Initialize Revision Session

1. Role switch to Reviser:
   ```
   ## [Role Switch: Reviser]
   Read references/reviser.md
   ```

2. Create revision workspace:
   ```bash
   mkdir -p <project_path>/.revision
   ```

3. Save baseline snapshots:
   ```bash
   python3 ${SKILL_DIR}/scripts/svg_snapshot.py save <project_path>/svg_output
   ```
   This writes `<project_path>/.revision/snapshots.json` with hashes of all SVGs.

4. Acknowledge to user: "已进入修订模式。请告诉我要修改什么。"

## Step 2: Receive Revision Feedback

Collect user feedback. Possible sources:
- **Chat**: user types what they want changed
- **Live-preview**: annotations submitted in browser (read from `<project>/.review/annotations.json` if present)

## Step 3: Plan — Build Execution Contract

For each revision request:

1. **Classify scope**: local / page / global / hybrid
2. **Identify targets**: which pages, which element ids
3. **Determine operations**: what patch ops are needed
4. **Build contract**:
   ```python
   contract = {
       "scope": "global",
       "target_pages": "all",
       "target_elements": ["title"],
       "operations": [{"op": "update_fill", "target": "title", "params": {"fill": "#005587"}}]
   }
   ```

Present the contract to user for confirmation (optional — skip if the request is unambiguous):
"将修改以下元素：[summary]。确认开始？"

## Step 4: Act — Apply Patches

For each target page:

```bash
# 1. List editable elements to map user request to element ids
python3 ${SKILL_DIR}/scripts/svg_snapshot.py list <svg_path>

# 2. Apply patches
python3 ${SKILL_DIR}/scripts/svg_patch.py apply <svg_path> \
  --ops '[{"op":"update_fill","target":"title","params":{"fill":"#005587"}}]' \
  --hash <expected_hash>
```

For batch operations across pages, run sequentially per page (same as Executor's serial rule).

## Step 5: Guard — Verify

1. **Coverage check**: all target pages patched?
2. **Quality check**:
   ```bash
   python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path>
   ```
   Fix any errors.

3. **Diff summary**: report what changed
   ```bash
   python3 ${SKILL_DIR}/scripts/svg_snapshot.py diff <baseline> <current>
   ```

4. Report to user:
   "修订完成。修改了 N 个元素，涉及 M 个页面。质量检查通过。"

## Step 6: Loop or Exit

- If user has more feedback → return to Step 2
- If user says "完成" / "done" / "导出" / "export" → exit

### On Exit

1. Update snapshots:
   ```bash
   python3 ${SKILL_DIR}/scripts/svg_snapshot.py save <project_path>/svg_output
   ```

2. Role switch back:
   ```
   ## [Role Switch: Post-processing]
   ```

3. Proceed to Step 7 (re-run post-processing if SVGs were modified):
   ```bash
   python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
   python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>
   ```

## Loop Safety

- Maximum 20 revision rounds per session
- Hash mismatch on any page → pause and report (manual SVG edit detected)
- Quality check failure → must fix before next round

## Escalation Rules

> Adapted from PPT Hell: "同一页同类 issue 连续两轮仍未解决时，必须升级处理"。

### Issue Tracking

Each round, track unresolved issues in `<project>/.revision/issue_tracker.json`:

```json
{
  "slide_05": {
    "text_overflow": {"rounds_unresolved": 2, "first_seen_round": 3},
    "color_mismatch": {"rounds_unresolved": 0, "first_seen_round": 5}
  }
}
```

After each Guard step (Step 5), update the tracker:
- Issue resolved → reset `rounds_unresolved` to 0
- Issue persists → increment `rounds_unresolved`

### 2-Round Escalation Rule

When the same issue category on the same page persists for **2 consecutive rounds** without resolution:

1. **STOP** attempting the same fix approach
2. **Present to user** with explicit options:
   - "回到设计规格调整版式/内容分配" (return to Strategist/spec change)
   - "接受当前状态并标注已知限制" (accept with noted limitation)
   - "人工介入修改 SVG" (manual intervention)
3. Record escalation to `<project>/.revision/escalations.json`
4. Mark the issue as `escalated` — excluded from automatic retry

### Issue Categories

| Category | Typical Trigger |
|----------|----------------|
| `text_overflow` | Text exceeds container bounds after patch |
| `alignment` | Elements drift from grid/baseline after adjustment |
| `color_mismatch` | Color cannot match spec_lock despite attempts |
| `spacing` | Element spacing repeatedly fails minimum gaps |
| `content_missing` | Required content cannot be restored in layout |
| `layout_structure` | Major layout rework needed beyond patch scope |
| `image_fit` | Image cannot fit slot without unacceptable crop |
| `font_size` | Text requires size below readability minimum |

## Integration with Live-Preview

If live-preview is running, the user can also submit revisions through the browser:
1. Select element → write annotation → click "Submit"
2. Annotation is saved to `<project>/.review/annotations.json`
3. Reviser reads annotations and converts them to patch operations

This is the preferred workflow for visual edits (positioning, sizing, colors).
