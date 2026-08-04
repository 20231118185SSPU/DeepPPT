# Native PPTX Revision (OfficeCLI-backed)

> Shared child workflow. Called by Generate PPTX, Fill Native PPTX, and Enhance Native PPTX
> routes when the user explicitly requests last-mile native edits on an exported PPTX.
> Never invoked automatically; always opt-in.

## Purpose

Allow AI to inspect, preview-select, plan, and atomically apply text/shape-level
mutations to an existing PPTX without entering the SVG pipeline. All mutations
execute on a temporary copy; the source PPTX is never modified in place.

## When to Use

- User says "改这个PPT里的文字/颜色/位置" on an already-exported deck
- User wants to relocate or restyle specific shapes without structural redesign
- Post-export micro-corrections that don't warrant full SVG regeneration

## When NOT to Use

- "重新设计/拆页/合页/换结构" → enter Generate PPTX route (SVG pipeline)
- "把新内容填回模板" → enter Fill Native PPTX route
- "只加备注/配音/时序/转场" → enter Enhance Native PPTX core (notes/audio/timings)

## Prerequisites

- OfficeCLI v1.0.143 installed and verified (`install_officecli.py check --json` returns ready).
- A confirmed `native_revision_plan.json` with valid operations.

## Workflow

### 1. Init Project

```bash
python skills/ppt-master/scripts/native_revision_pptx.py init <pptx-or-project> [--name <slug>]
```

For standalone PPTX: creates a `projects/_revision_<name>/` project and copies source.
For existing PPT Master project: links to the export.

### 2. Inspect Source

```bash
python skills/ppt-master/scripts/native_revision_pptx.py inspect <project>
```

Produces `analysis/native_revision_inventory.json` with stats, outline, issues,
and per-element depth-limited inspection. Source SHA-256 is asserted unchanged.

### 3. (Optional) Live Preview & Selection

```bash
python skills/ppt-master/scripts/native_revision_pptx.py watch <project> [--port 26315]
python skills/ppt-master/scripts/native_revision_pptx.py selected <project> --json
python skills/ppt-master/scripts/native_revision_pptx.py unwatch <project>
```

Browser-based preview for visual element selection. Selection returns stable
`@id=` paths but does not represent user confirmation.

### 4. Draft Plan

Create `analysis/native_revision_plan.json` (schema `ppt_master.native_revision_plan.v1`).
Each operation must have `id`, `command`, `path`/`parent`, `props`, `reason`, and `expect`.
Status must be `draft` until confirmed by the user.

V1 mutation allowlist: `set`, `add`, `remove`, `move`, `swap`.
Forbidden: `raw-set`, `add-part`, `import`, `merge`, `--best-effort`.

### 5. Check Plan

```bash
python skills/ppt-master/scripts/native_revision_pptx.py check-plan <project>
```

Validates schema, status, source hash freshness, allowlist, target existence,
and invariants. Non-zero on any failure.

### 6. Confirm & Apply

User must explicitly confirm. After confirmation, set `status: "confirmed"`
and `confirmation.confirmed_at`.

```bash
python skills/ppt-master/scripts/native_revision_pptx.py apply <project>
```

Apply steps (all gates must pass):
1. Probe OfficeCLI runtime
2. Re-run check-plan
3. Copy source to `.tmp/officecli-<run-id>/`
4. Execute OfficeCLI atomic batch on temp copy (no `--best-effort`)
5. On any item failure: verify `atomicRolledBack` or candidate hash unchanged, discard, non-zero exit
6. On success: OfficeCLI validate (baseline delta — only block on new issues)
7. Slide roster comparison
8. Source immutability check
9. PowerPoint COM render (Windows; marks `visual_review_required` if unavailable)
10. Atomically publish timestamped PPTX to `exports/`

### 7. SVG Divergence

When `source.origin == "generated_export"`:
- `native_revision_result.json` records `svg_divergence: true`
- Dashboard displays "原生派生版已偏离 SVG canonical source"
- Future content/layout rework defaults to SVG regeneration
- Only explicit last-mile requests continue on the latest verified derivative

## Project Artifacts

```
analysis/native_revision_inventory.json   — schema ppt_master.native_revision_inventory.v1
analysis/native_revision_plan.json        — schema ppt_master.native_revision_plan.v1
analysis/native_revision_result.json      — schema ppt_master.native_revision_result.v1
quality/officecli_validation.json         — schema ppt_master.officecli_validation.v1
validation/native_revision_report.json    — schema ppt_master.native_revision_report.v1
native_preview/officecli-watch.json       — watch state
exports/<stem>_native_revision_<ts>.pptx  — published export
```

## Error Recovery

| Failure | Recovery |
|---|---|
| Runtime/version/checksum | Install OfficeCLI; no mutation occurs |
| Plan stale | Re-inspect, re-draft plan |
| Batch item failure | Verify rollback, discard candidate |
| Postflight failure | Candidate not published; report specific gate |
| COM unavailable | Structural gates still run; mark `visual_review_required` |
