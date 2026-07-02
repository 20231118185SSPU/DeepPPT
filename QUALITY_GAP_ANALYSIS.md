# Quality Gap Analysis: Rendered Visual Reliability

## Scope

Regression sample:

`projects/ppt_master_e2e_validation_mini_deck_ppt169_20260701`

Problem: `svg_quality_checker.py` and `harness_gate.py --quick` passed while rendered PPT visuals had obvious failures. The defect class is not a single SVG syntax bug; it is a quality-system boundary issue.

## Findings

| Page | Observed issue | Old gate result | Classification | New gate handling |
|---|---|---|---|---|
| P01 | Bottom path labels were too close to / overlapping the long horizontal rule in the first exported backup | Static pass | False negative | `text_line_collision` must-fix on the bad backup |
| P02 | Bottom wide strip had text concentrated on the left and excessive right-side whitespace; long strip text could sit too close to borders | Static pass | False negative / human-review case | `wide_container_sparse_right` and close-fit items become `needs_human_review` |
| P03 | `svg_quality_checker.py` reports element overlap, but rendered table is visually acceptable because many overlaps are grid backgrounds/lines vs table text | Warning despite acceptable visual | False positive / accepted risk | Keep in static checker as warning; do not auto-fix solely to clear it |
| P04 | Early backup had large left title crossing the vertical timeline divider into the right column | Static pass | False negative | `cross_column_text_intrusion` must-fix on the bad backup |
| P04 | Later warning-fix changes modified SVGs after a revision snapshot; visual state required re-check to prevent regression | Static pass | Harmful remediation risk | `rendered_regression_review_required` requires explicit human confirmation for changed rendered screenshots |
| P04 | Left lower area can become empty in split layouts | Static pass or weak warning | Layout quality / human-review case | `large_blank_region` / screenshot occupancy signals are review blockers, not hard style rules |

## Root Cause

The old quality system mixed three different meanings of "pass":

1. `svg_quality_checker.py` checks XML and static SVG contracts: viewBox, banned features, spec-lock drift, font/color bounds, basic geometry estimates.
2. `harness_gate.py --quick` aggregates static checks only and explicitly skips e2e.
3. `e2e_validate.py` verifies PPTX package integrity, slide count, notes, and image presence. It does not inspect visual layout.

None of those gates is a rendered visual acceptance check. They do not reliably see browser-rendered text extents, z-order, line collisions, visual whitespace, or whether a warning fix made the slide worse.

## Gate Layering

| Layer | Tool | Blocks on | Does not decide |
|---|---|---|---|
| Deterministic SVG structure | `svg_quality_checker.py` | XML validity, banned SVG/PPT features, spec-lock drift, severe static violations | Final visual quality |
| Spec semantic compliance | `spec_compliance_check.py` | missing templates/icons/images, unused declared assets, inverse spec drift | Rendered layout |
| Aggregated static shortcut | `harness_gate.py --quick` | static gate failures | e2e or visual pass |
| Rendered visual gate | `rendered_layout_check.py` | cross-column intrusion, text-line contact, missing/stale PNG, abnormal whitespace review blockers, revision-regression review | Subjective redesign choices |
| Rubric/human review | `visual-review.md` and user inspection | hierarchy/rhythm/collision judgments that heuristics cannot prove | XML/PPTX integrity |
| PPTX integrity | `e2e_validate.py` | slide count, speaker notes, image completeness, package openability | Visual acceptance |

## Implemented Change

Added `skills/ppt-master/scripts/rendered_layout_check.py`.

Key behavior:

- Reads `svg_output/*.svg` and `.preview/*.png`.
- Optionally refreshes screenshots through `visual_review.py --render`.
- Emits `quality/rendered_visual_gate.json`.
- Returns non-zero for `must_fix` or `needs_human_review`.
- Writes `quality/rendered_visual_acceptance.json` only when `--accept-current-render` is explicitly run after human visual confirmation.

Detected issue types:

- `cross_column_text_intrusion`: hard block for text crossing a vertical divider.
- `text_line_collision`: hard block for text touching or overlapping a long rule.
- `text_container_edge_contact`: hard block only for severe container overflow.
- `text_container_close_fit`: human-review block for borderline fit.
- `wide_container_sparse_right`: human-review block for suspicious one-sided wide strips.
- `large_blank_region`: human-review block for abnormal dead zones.
- `rendered_regression_review_required`: human-review block when SVG hashes changed after a revision snapshot.

## Workflow Updates

Updated `SKILL.md`, `workflows/visual-review.md`, and script docs to state:

- Static script pass is not visual pass.
- Export requires rendered screenshot visual gate or explicit human visual confirmation.
- `harness_gate.py --quick`, `svg_quality_checker.py`, `rendered_layout_check.py`, `visual-review.md`, and `e2e_validate.py` have distinct responsibilities.

## Regression Verification

Baseline:

```bash
python skills/ppt-master/scripts/harness_gate.py projects/ppt_master_e2e_validation_mini_deck_ppt169_20260701 --quick --read-only
```

Result: PASS. Confirms old quick gate did not block the known visual-failure class.

```bash
python skills/ppt-master/scripts/svg_quality_checker.py projects/ppt_master_e2e_validation_mini_deck_ppt169_20260701/svg_output --integrated-review --ir-output projects/ppt_master_e2e_validation_mini_deck_ppt169_20260701/quality/svg_ir_current_probe.json
```

Result: exit 0, `PASS_WITH_WARNINGS`; only P03 overlap warning remained.

```bash
python skills/ppt-master/scripts/e2e_validate.py projects/ppt_master_e2e_validation_mini_deck_ppt169_20260701 --pptx projects/ppt_master_e2e_validation_mini_deck_ppt169_20260701/exports/ppt_master_e2e_validation_mini_deck_20260701_203630.pptx
```

Result: PASS, 7 passed / 0 warnings / 0 errors. Confirms PPTX integrity is not visual acceptance.

New gate:

```bash
python skills/ppt-master/scripts/rendered_layout_check.py projects/ppt_master_e2e_validation_mini_deck_ppt169_20260701 --read-only
```

Result: BLOCKED with `needs_human_review` items, including `rendered_regression_review_required`. Current screenshots require explicit human confirmation because SVGs changed after `.revision/snapshots.json`.

Bad historical backup:

```bash
python skills/ppt-master/scripts/rendered_layout_check.py projects/ppt_master_e2e_validation_mini_deck_ppt169_20260701 --svg-dir projects/ppt_master_e2e_validation_mini_deck_ppt169_20260701/backup/20260701_200045/svg_output --preview-dir projects/ppt_master_e2e_validation_mini_deck_ppt169_20260701/.preview --read-only
```

Result: BLOCKED. Must-fix findings include P01 `text_line_collision` and P04 `cross_column_text_intrusion`; P02 wide-strip whitespace is surfaced as human review.

## Accepted Warnings

P03 `Element overlap` from `svg_quality_checker.py` is accepted as a static false positive for this sample: the visible table uses overlapping grid backgrounds, header fills, and separators that render correctly. Clearing that warning by moving table geometry is more dangerous than leaving an accepted risk.

## Remaining Risk

Rendered heuristics are conservative and intentionally do not replace visual judgment. They catch known failure classes and force review for ambiguous whitespace/fit issues, but they cannot score taste, narrative hierarchy, or every possible z-order/text-shaping edge case. The final release decision still needs screenshot review when the gate emits `needs_human_review`.
