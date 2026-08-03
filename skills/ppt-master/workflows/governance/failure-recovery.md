---
description: DeepPPT2 stop/continue governance with a concrete recovery matrix for the main Generate pipeline (SKILL.md Steps 1-8).
---

# Failure Recovery Governance

Global stop/continue rules for the DeepPPT2 pipeline, plus concrete failure handling per step. Owning step and workflow documents may add narrower handling, but must not weaken the global rules or duplicate this matrix.

**Hard rule**: A failed required artifact blocks the next gate. A failed convenience surface falls back to the canonical channel and does not block the active step.

## Recovery Matrix

| Failure point | Blocking | Automatic recovery | User intervention | Resume entry |
|---|---:|---|---|---|
| Skill integrity gate (`attribution_guard.py`) | Yes | Repair the identity bundle / missing pipeline files; re-register the digest only after an intentional edit | Only when the identity manifest genuinely changed | SKILL.md mandatory load order |
| Confirm UI launch failure | No | Re-check `confirm_ui/result.json` once, then use chat fallback | No | SKILL.md Step 4 chat confirmation |
| Confirm UI wait timeout | No, if no final result yet | Re-check `result.json` once; keep server cleanup (`--shutdown`) mandatory | Only if user still wants the page | Step 4 same stage or chat fallback |
| User explicitly switches from Confirm UI to chat during any stage | Yes until the unresolved current stage is confirmed | Follow `scripts/docs/confirm_ui.md`'s in-run switch: stop the wait, `--shutdown`, re-check `result.json` once, retain persisted confirmed stages, continue current and remaining stages in chat | Confirm in chat | Step 4 current chat stage |
| Confirm UI Stage 1 confirmed then interrupted while UI remains selected | Yes until Stage 2 is written/confirmed | Read existing Stage 1 `result.json`, create `recommendations.stage2.json` without changing Stage 1, then `--wait-only --wait-stage stage2` | Usually no | Step 4 Stage 2 write/wait |
| Missing final confirmation | Yes | None | User must confirm or change the values | Step 4 final confirmation |
| `confirm_ui_gate.py` FAIL (stale result, stage skip, pending template selection) | Yes | Re-run the affected Stage 4 flow; a pending `template_selection` requires Step 3 re-application | No | Step 4 / Step 3 |
| Confirmed value missing, changed, substituted, or weakened in `design_spec.md` / `page_expression.json` | Yes | Repair from the retained final-confirmation object plus any newer explicit instruction | Only when the effective value genuinely cannot be honored | Step 4 → Step 5 |
| `spec_lock_digest.py` / `spec_lock_validate.py` FAIL | Yes | Fix the lock row from the completed Design Spec and current context; re-seal with `spec_lock_digest.py generate` | No unless the Design Spec itself is incomplete | Step 4 seal / Step 6 per-page re-read |
| `spec_compliance_check.py` FAIL | Yes | Fix the affected page SVG against `spec_lock.md`, then re-run the check | No | Step 6 current page |
| `svg_quality_checker.py` error | Yes | Review the complete issue set from one unfiltered run; fix all errors and selected warnings in one consolidated edit pass, then perform one verification rerun; never check between individual fixes | No unless a required asset is missing | Step 6 Visual Construction |
| `svg_quality_checker.py` warning | No | Continue without mandatory modification; report material fidelity/quality advice when useful | No | Step 6 advisory handling |
| `rendered_layout_check.py` FAIL | Yes | Fix the offending page layout against the confirmed page plan, re-render, re-check | Only when the confirmed plan itself is wrong | Step 6 rendered gate |
| `harness_gate.py` FAIL | Yes | Fix per the gate's report, re-run | No | Step 6 → Step 7 boundary |
| Live preview fails to start | No | Continue generation; report that preview is unavailable | Only if user requires browser preview | Step 6 or `workflows/stages/live-preview.md` Step 1 |
| Browser annotations submitted during generation | No | Defer application until after Step 7 | User asks to apply annotations | `workflows/stages/live-preview.md` Step 2 |
| Chart coordinates need calibration (charts in deck) | No (run before export) | Run `workflows/stages/verify-charts.md` between executor and post-processing | No | `verify-charts` workflow |
| AI image generation failure | No | `auto`: follow A → B → Offline Manual. Explicit `api` / `host-native`: retry only that path, then mark the row `Needs-Manual` without switching automated providers | Only when missing files are required before export | Step 5 / Step 7 image readiness gate |
| Web image search/download failure | No | Adjust query/source per `references/image-searcher.md` / `references/image-source-routing.md`, then mark `Needs-Manual` if unresolved | Only if the resource is required and no acceptable substitute exists | Step 5 |
| Residual `Pending` or `Failed` image row before Executor | Yes | Re-run path or mark `Needs-Manual` | Only if file must be supplied manually | Step 5 terminal-state check |
| `research/asset_gate.py` FAIL | Yes | Return to Image Acquisition / deep-research Step 7 as reported | No | Step 5 asset gate |
| `consulting_content_lock.py` FAIL (consulting/high-density) | Yes | Fix the lock sidecar, re-run | No | Step 5/6 |
| User replaces/adds images after analysis | No | Re-run `analyze_images.py` before reading image facts | No | Step 4/5/6 image-fact read |
| Formula rendering provider failure | No until the Step 7 readiness gate | Exhaust the provider chain; if unresolved, mark only the affected formula rows `Needs-Manual` and continue | Supply the exact target PNG or change formula policy | Step 4 / Step 7 image readiness gate |
| Missing `notes/total.md` while speaker notes are enabled | Yes | Generate speaker notes before Step 7 | No | Step 6 Logic Construction |
| `total_md_split.py` failure while speaker notes are enabled | Yes | Fix notes format/path, rerun only the split | Usually no | Step 7.1 |
| `finalize_svg.py` failure | Yes | Fix SVG/assets, rerun Step 7.2 | Only if source asset is missing | Step 7.2 |
| `svg_to_pptx.py` failure | Yes | Fix conversion issue, rerun Step 7.3 | Only if required artifact is missing | Step 7.3 |
| `e2e_validate.py` FAIL | Yes | Fix per the report, re-export, re-validate | Only when the requirement is impossible | Step 7 export validation |
| `pptx_quality_check.py` FAIL (optional strict QA) | Yes when run | Fix the DrawingML issue (text overflow etc.), re-export, re-check | No | Step 7 re-export |
| Export succeeds but user wants direct browser edits re-exported | No | Rerun Step 7.2 and Step 7.3 after applied edits | No | Post-export live-preview handling |
| `visual-review` finds issues | No (default recommended) | Apply atomic fixes per `workflows/stages/visual-review.md`, re-check | Skip only on explicit "跳过视觉自检" / `skip_visual_review: true` | `visual-review` workflow |
| Spec review (Step 8a) findings | No | Record lessons; apply to next deck | Yes when a fix is requested for this deck | Step 8a |

## Global Stop/Continue Rules

| Condition | Action |
|---|---|
| Required gate artifact missing | Stop at that gate and name the missing artifact. |
| Optional stage not explicitly requested | Do not run it as recovery. |
| Convenience UI/server failure | Fall back to chat or continue without the surface. |
| Derived artifact stale | Regenerate it from its owning source. |
| Required manual artifact missing | Pause and name the exact required artifacts; resume only after they exist. |
| Validation or export failure | Fix the owning source artifact, then rerun the failed operation and affected downstream operations only. |
| Confirmed execution choice cannot be honored | Keep the confirmed requirement visible. Retry the confirmed provider, mode, voice, effect, or path only as its owning workflow allows; if it remains unavailable, stop, request a new decision, or hand off through the owning workflow's declared manual fallback (e.g. `Needs-Manual` with a user summary). Never omit it or switch to another automated value or path silently. |
| Split-mode / resume handoff | `resume-execute.md` re-enters Phase B from `projects/<name>` without re-running Phase A; do not re-run briefing/deep-research/confirm. |
| Refine-spec stop | With `refine_spec: true`, stop after Gate 1 for unrestricted chat review; revisions supersede only affected decisions; touch no lock until approval. |

**Missing values**: For a field in an existing artifact, follow only the exact requiredness, inference procedure, or fixed default declared by its owning schema or workflow; an active omission with no such rule stops at the owning boundary. Empty values, inactive conditional fields, whole artifacts, derived artifacts, and file-format attributes keep their own declared semantics—do not extend a fallback by analogy.
