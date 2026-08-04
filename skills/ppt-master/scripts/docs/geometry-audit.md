# SVG Geometry Audit (`svg_geometry_audit.py`)

> Deterministic glyph-box layout audit. **Advisory only** — it never blocks export or
> delivery gates. The final layout authority is the PowerPoint real render; see
> [Review order](#review-order) below.
> Layout budget rules this tool enforces are owned by
> [executor-base.md](../../references/executor-base.md#147-vertical--horizontal-budget-rules-垂直横向预算规则).

## Checks

| Check | Severity | Rule |
|---|---|---|
| `text-overlap` | error / warning | Cross-element glyph-box overlap: y-overlap > 6px → error, > 2px → warning. Glyph box = baseline − 0.78·fs .. baseline + 0.22·fs. |
| `line-spacing` | warning | Adjacent lines inside one `<text>` with baseline gap < 1.0·fs. Rows at the same baseline (`<tspan>` without `dy`) are inline continuations and are skipped. |
| `footer-gap` | error / warning | Footer row (baseline ≥ 680) vs text above: glyph gap < 2px → error, < 6px → warning. |
| `rect-over-text` | warning | A filled `<rect>` drawn **after** a text (document order = z-order) whose box covers the text's glyph box. |
| `text-beyond-rect` | warning | Text glyph bottom exceeds its containing rect bottom by > 1px. |
| `rect-overlap` | info | Partial intersection of two later/earlier filled rects (full containment is not flagged). |
| `image-size` | info | Content-type `<image>` with a short side < 150px. |

Width estimation reuses `svg_to_pptx.drawingml.utils.estimate_text_width` (the exporter's
authoritative metric) so audit and export never disagree on text extents.

## Usage

```bash
python3 skills/ppt-master/scripts/svg_geometry_audit.py <project_path>
python3 skills/ppt-master/scripts/svg_geometry_audit.py <project_path> --strict   # exit 1 on errors
python3 skills/ppt-master/scripts/svg_geometry_audit.py <project_path> --json-out <file>
```

- Requires `<project_path>/svg_output/`; exit 2 when absent.
- Default exit code is always 0 (advisory). `--strict` returns 1 when any error-level issue exists.
- Report: `<project>/quality/geometry_audit.json` (schema `ppt_master.svg_geometry_audit.v1`,
  per-page issues with `severity` / `check` / `message`, plus a summary).

## Limitations

- Only `translate()` transforms are expanded (nested groups accumulate). `rotate` /
  `scale` / `matrix` are not; schema mockups under such transforms need manual review.
- One level of `<tspan>` nesting is parsed.
- Font metrics are estimates. The 0.22 descent ratio overestimates some Latin faces
  (e.g. Arial Black "Aa" renders no descender into the caption row); treat borderline
  findings as suspicious and adjudicate on the PowerPoint render.

## Review order

The final visual review sequence (also documented in
[visual-review.md Step 4b](../../workflows/stages/visual-review.md)):

1. `svg_geometry_audit.py <project_path>` — deterministic first pass (advisory).
2. `svg_to_pptx.py <project_path>` — export.
3. `pptx_delivery_check.py <exported.pptx>` — package/delivery risks (zip integrity, fonts, media, dangling relationships).
4. `pptx_render_export.py --pptx <exported.pptx> -o <project>/quality/pptx_render` — PowerPoint real render (Windows + Office; exit 2 without Office).
5. `e2e_validate.py <project_path> --pptx <exported.pptx>` — structural E2E gate.
6. Visual/human adjudication on the PowerPoint PNGs — final truth; Chromium previews and this audit are first-pass only.

PowerPoint render differs from Chromium on font metrics (YaHei line height, width
headroom); text that clears by 2px in the browser can visibly collide in PowerPoint.
Adjudicate disputed findings on the PowerPoint PNGs, never on the browser preview.

## Calibration record (Phase 1, 2026-08-04)

Golden Set: `examples/ppt169_kubernetes_blueprint_2026` (10p),
`examples/ppt169_swiss_grid_systems` (14p), `examples/ppt169_global_ai_capital_2026` (20p),
PowerPoint-PNG adjudicated:

- `line-spacing`: 58 findings, all inline-`<tspan>` false positives (same baseline) → fixed (skip `gap <= 0`).
- `rect-over-text` / `rect-overlap`: 16 + 30 findings on transformed schema groups (translate not expanded) → fixed (translate accumulation).
- `text-overlap`: 3 findings on `swiss_grid 07_typefaces` — 2 true positives (Arial 700/400 descender collides with the caption row, pixel-verified), 1 false positive (Arial Black descent overestimated by the 0.22 ratio model).
- Known-defect recall: 5/5 synthetic injections (footer-gap −2.4px, text-overlap 9.2px, rect-over-text, text-beyond-rect 5.3px, x-overlap 34.5px) reproduced.

Measured precision after fixes: text-overlap 67% (2 TP / 1 FP) — below the 95% upgrade bar,
so all checks stay advisory. `--strict` and gate promotion require the Gate G2 process.
