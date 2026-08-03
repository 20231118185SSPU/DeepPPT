# PPT Master Toolset

This directory contains user-facing scripts for conversion, project setup, direct PPTX template filling, SVG processing, export, recorded narration, and image generation.

## Directory Layout

- Top-level `scripts/`: runnable entry scripts
- `scripts/source_to_md/`: source-document → Markdown converters (`pdf_to_md.py`, `doc_to_md.py`, `excel_to_md.py`, `ppt_to_md.py`, `web_to_md.py`)
- `scripts/research/`: deep-research browser search, research depth gate, asset gate, and output sync tools
- `scripts/image_backends/`: internal provider implementations used by `image_gen.py`
- `scripts/tts_backends/`: internal TTS provider implementations used by `notes_to_audio.py`
- `scripts/template_import/`: internal PPTX reference-preparation helpers used by `pptx_template_import.py`
- `scripts/svg_finalize/`: internal post-processing helpers used by `finalize_svg.py`
- `scripts/docs/`: topic-focused script documentation
- `scripts/assets/`: static assets consumed by scripts

## Quick Start

Typical end-to-end workflow:

```bash
python3 scripts/source_to_md/pdf_to_md.py <file.pdf>
# or
python3 scripts/source_to_md/ppt_to_md.py <deck.pptx>
python3 scripts/source_to_md/excel_to_md.py <workbook.xlsx>
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> <source_files...>
python3 scripts/project_manager.py validate <project_path> --start-dashboard
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/animation_config.py scaffold <project_path>  # optional object-level animation overrides
python3 scripts/svg_to_pptx.py <project_path>
```

Repository update:

```bash
python3 scripts/update_repo.py
```

## Script Index

Layer definitions:

- `runtime pipeline`: called by the main SKILL.md generation, gate, post-processing, export, or validation path.
- `workflow satellite`: owned by a standalone or optional workflow, or by a one-off asset/revision workflow.
- `maintenance`: repository, example, template-index, regression, or spec upkeep tools.
- `internal helper`: importable support modules or thin service helpers whose behavior is owned by another entry point.

| Layer | Area | Top-level scripts / packages | Documentation |
|------|------|-------------------------------|---------------|
| `runtime pipeline` | Conversion and intake | `source_to_md/`, `pptx_intake.py` | [docs/conversion.md](./docs/conversion.md) |
| `runtime pipeline` | Project setup and local UI services | `project_manager.py`, `dashboard/`, `confirm_ui/`, `svg_editor/` | [docs/project.md](./docs/project.md), Step 4 / Live Preview docs in `../workflows/` |
| `runtime pipeline` | Confirmation, research, and image gates | `research/`, `confirm_ui_gate.py`, `image_source_router.py` | Deep-research and Step 4/5 gate docs in `../workflows/` |
| `runtime pipeline` | Image and asset acquisition | `analyze_images.py`, `icon_sync.py`, `image_gen.py`, `image_search.py`, `latex_render.py` | [docs/image.md](./docs/image.md) |
| `runtime pipeline` | Pre-executor and quality gates | `consulting_content_lock.py`, `harness_gate.py`, `layout_capacity_check.py`, `rendered_layout_check.py`, `spec_compliance_check.py`, `spec_lock_digest.py`, `svg_quality_checker.py`（薄入口 → `svg_quality/` 包） | [docs/svg-pipeline.md](./docs/svg-pipeline.md) |
| `runtime pipeline` | Post-processing and export | `e2e_validate.py`, `finalize_svg.py`, `memory_manager.py`, `pptx_quality_check.py`, `svg_to_pptx.py`, `total_md_split.py` | [docs/svg-pipeline.md](./docs/svg-pipeline.md) |
| `workflow satellite` | Direct PPTX and template workflows | `beautify_identity.py`, `beautify_inventory.py`, `extract_svg_assets.py`, `pptx_template_import.py`, `pptx_to_svg.py`, `register_template.py`, `template_fill_pptx.py` | [docs/project.md](./docs/project.md), create-template / beautify / template-fill docs in `../workflows/` |
| `workflow satellite` | Native PPTX enhancement (Enhance route) | `native_enhance_pptx.py`, `native_enhance_pptx_core.py`, `native_narration_pptx.py`, `native_payloads.py`, `native_pptx_animations.py`, `pptx_delivery_check.py`, `pptx_effects.py`, `pptx_opc_validation.py`, `pptx_transitions.py` | [docs/pptx-transitions.md](./docs/pptx-transitions.md), `../workflows/native-enhance-pptx.md` |
| `workflow satellite` | Video export and narration sync | `narration_sync.py`, `powerpoint_video.py`, `video_motion_plan.py`, `video_subtitles.py` | `docs/audio-narration.md`, `../workflows/stages/generate-audio.md` |
| `workflow satellite` | Review, revision, charts, audio, and animation | `animation_config.py`, `chart_recall.py`, `check_annotations.py`, `notes_to_audio.py`, `svg_patch.py`, `svg_position_calculator.py`, `svg_snapshot.py`, `vision_check.py`, `visual_review.py` | [docs/chart-recall.md](./docs/chart-recall.md), [docs/svg-pipeline.md](./docs/svg-pipeline.md), visual-review / live-preview / verify-charts docs in `../workflows/` |
| `workflow satellite` | Template authoring and native shapes | `compact_svg_coordinates.py`, `extract_svg_pictures.py`, `preset_shape_svg.py`, `slice_images.py`, `svg_authoring_view.py`, `template_preview_pptx.py`, `template_text_slots.py` | `../workflows/profiles/quick-generate.md`, `../workflows/create-template.md` |
| `workflow satellite` | Shape boolean (deferred core) | `shape_boolean_svg.py` — CLI degrades with a clear message until the deferred DrawingML refactor wires `svg_to_pptx.shape_boolean` (roadmap item) | `../workflows/profiles/quick-generate.md` |
| `workflow satellite` | Image fixups | `gemini_watermark_remover.py`, `rotate_images.py` | [docs/image.md](./docs/image.md), [docs/conversion.md](./docs/conversion.md) |
| `maintenance` | Project, repo, and spec upkeep | `batch_validate.py`, `generate_examples_index.py`, `governance_drift_check.py`, `smoke_check.py`, `update_repo.py`, `update_spec.py` | [docs/project.md](./docs/project.md), [docs/update_spec.md](./docs/update_spec.md), README install/update section |
| `internal helper` | Shared configuration, validation, and service support | `config.py`, `dashboard_launcher.py`, `error_helper.py`, `json_utils.py`, `project_utils.py`, `server_common.py` | [docs/project.md](./docs/project.md), [docs/troubleshooting.md](./docs/troubleshooting.md) |
| `internal helper` | Shared encoding and PPTX animation XML | `console_encoding.py` (UTF-8 stdout/stderr setup for CLI scripts, including Windows non-UTF-8 locales), `pptx_animations.py` (pure XML generation for slide transitions and per-element entrance animations) | Imported by CLI/export wrappers |
| `internal helper` | Refactored SVG→DrawingML exporter internals | `svg_to_pptx/drawingml/`（context/converter/elements/paths/styles/text_properties/theme_colors/theme_fonts/utils）、`svg_to_pptx/pptx_package/`（builder/cli/template_structure/template_validation/notes/narration/media/…）、`svg_to_pptx/native_objects/`、`svg_quality/`（checker/svg_contracts/cli + `deepppt_extensions.py` 迁移的 DeepPPT2 特有审查检查） | Consumed by `svg_to_pptx.py` / `svg_quality_checker.py` wrappers and the enhance route |

## High-Frequency Commands

Conversion:

```bash
python3 scripts/source_to_md/pdf_to_md.py <file.pdf>
python3 scripts/source_to_md/ppt_to_md.py <deck.pptx>
python3 scripts/source_to_md/doc_to_md.py <file.docx>
python3 scripts/source_to_md/excel_to_md.py <workbook.xlsx>
python3 scripts/source_to_md/web_to_md.py <url>
```

Project setup:

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> <source_files...>
python3 scripts/project_manager.py validate <project_path>
```

Leave `import-sources` unflagged by default. Add `--move` only when intentionally relocating originals; add `--copy` when an in-repo source must remain in place.

After Step 2 project setup/import, start or reuse the read-only Dashboard:

```bash
python3 scripts/dashboard/server.py <project_path> --daemon
```

Or ask `project_manager.py` to do the same best-effort startup after a successful
project command:

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169 --start-dashboard
python3 scripts/project_manager.py import-sources <project_path> <source_files...> --start-dashboard
python3 scripts/project_manager.py validate <project_path> --start-dashboard
```

Without `--start-dashboard`, project commands only print the Dashboard hint.

Default port: `8765`; log: `<project_path>/dashboard/dashboard.log`. The default local launch may open a browser; add `--no-browser` only for headless/remote sessions or when the user explicitly asks for no window. Launch failure is non-fatal. Dashboard shows status, artifacts, quality, trace, and bridge state only; it does not replace Confirm UI, Live Preview, quality gates, post-processing, or export.

Template source import:

```bash
python3 scripts/pptx_template_import.py <template.pptx>
python3 scripts/pptx_template_import.py <template.pptx> --manifest-only
python3 scripts/pptx_template_import.py <template.pptx> --inheritance-mode both
```

Template fill (direct PPTX, no SVG conversion):

```bash
mkdir -p <project_path>/sources <project_path>/analysis <project_path>/exports <project_path>/validation
python3 scripts/template_fill_pptx.py analyze <project_path>/sources/<source.pptx> -o <project_path>/analysis/<stem>.slide_library.json
python3 scripts/template_fill_pptx.py scaffold <project_path>/analysis/<stem>.slide_library.json -o <project_path>/analysis/fill_plan.json --slides "1,3,4"
python3 scripts/template_fill_pptx.py check-plan <project_path>/analysis/<stem>.slide_library.json <project_path>/analysis/fill_plan.json -o <project_path>/analysis/check_report.json
python3 scripts/template_fill_pptx.py apply <project_path>/sources/<source.pptx> <project_path>/analysis/fill_plan.json -o <project_path>/exports/filled.pptx
```

`apply` automatically writes `filled_YYYYMMDD_HHMMSS.pptx` unless the output stem already ends with a timestamp. It applies a `fade` page transition by default; `--transition <effect>` (fade/push/wipe/split/strips/cover/random, `--transition-duration` in seconds) changes it, `--transition none` removes it, `--transition keep` preserves the source transitions, and a per-slide `transition` field in the plan overrides whatever the CLI selects.

Research / confirmation gates:

```bash
python3 scripts/research/browse_ai.py --batch <project>/_research/step2_search_plan/search_plan.json --output-dir <project>/_research/step3_search
python3 scripts/research/research_gate.py <project>          # after deep-research Step 7, before sync
python3 scripts/research/sync_research_outputs.py <project>
python3 scripts/confirm_ui_gate.py <project>                 # after Eight Confirmations, before spec writing
python3 scripts/research/asset_gate.py <project>             # after image acquisition, before Executor
```

Gate failures are blocking. Return to the step printed by the gate and rerun it before continuing.

Aggregated quality gate:

```bash
python3 scripts/harness_gate.py <project_path> --quick
python3 scripts/harness_gate.py <project_path> --quick --read-only
```

By default, `harness_gate.py` writes `<project_path>/quality/harness.json` and appends
`<project_path>/trace.jsonl` so the Dashboard can show the latest aggregate gate
result. Add `--read-only` (alias: `--no-write`) for regression checks that must not
modify project files.

Pre-merge / post-fix regression checklist (run from repository root):

```powershell
# Smoke import/help check: verifies script imports without running the full help suite.
python skills/ppt-master/scripts/smoke_check.py --skip-help

# Full E2E gate: runs spec compliance, SVG quality, and e2e validation for the exported test deck.
python skills/ppt-master/scripts/harness_gate.py projects/e2e_smoke_test_ppt169_20260701

# Full E2E validation: verifies page count, notes, image completeness, and PPTX integrity.
python skills/ppt-master/scripts/e2e_validate.py projects/e2e_smoke_test_ppt169_20260701 --pptx projects/e2e_smoke_test_ppt169_20260701/exports/e2e_smoke_test_20260701_151710.pptx

# Post-export PPTX structure QA: checks slide size, bounds, placeholders,
# native text count, font floor, and large/full-slide image risks.
python skills/ppt-master/scripts/pptx_quality_check.py projects/e2e_smoke_test_ppt169_20260701/exports/e2e_smoke_test_20260701_151710.pptx --json-out projects/e2e_smoke_test_ppt169_20260701/quality/pptx_quality.json

# Quick static gate: runs static project gates only; it skips e2e validation.
python skills/ppt-master/scripts/harness_gate.py examples/ppt169_kubernetes_blueprint_2026 --quick
```

`harness_gate.py --quick` is a static gate shortcut: it runs spec compliance and
SVG quality checks, marks e2e as skipped, and does not prove the deck passed the
complete end-to-end export validation. Use the full E2E gate plus
`e2e_validate.py --pptx ...` before treating a fix as end-to-end validated.

Main-pipeline spec compliance also validates the Strategist-owned
`page_expression.json`: schema/owner, page coverage, content fields, structural
page exceptions, allowed `content_relation` values, and the verbatim assertion
in a top-level editable `lead` or `subtitle` group at or above `typography.body`.
`template-fill` and `beautify` preservation projects are detected from their
existing `analysis/` artifacts and retain an explicit compatibility warning.
`spec_lock_digest.py generate` seals both `spec_lock.md` and
`page_expression.json` when the sidecar exists; `harness_gate.py` requires and
verifies that seal for sidecar projects, while older projects without the
sidecar retain the legacy digest-optional path.

Optional consulting content lock:

```bash
python3 scripts/consulting_content_lock.py <project_path>
```

This writes `<project_path>/analysis/slide_content_lock.json` from
`analysis/detailed_outline.json`, root `detailed_outline.json`, or `spec_lock.md`.

Rendered visual gate:

```bash
python3 scripts/rendered_layout_check.py <project_path> --render
python3 scripts/rendered_layout_check.py <project_path> --accept-current-render
```

`rendered_layout_check.py` uses local PNG screenshots plus SVG layout heuristics
to flag collision, text-line contact, abnormal whitespace, stale renders, and
revision-regression review needs. It complements `svg_quality_checker.py`; it
does not replace human visual judgment. A static script pass is not a visual
pass until this gate passes or a human accepts the current rendered screenshots.

Post-processing and export:

```bash
python3 scripts/extract_svg_assets.py <svg_dir> --icons-dir <icons_dir> --inplace --id-prefix <prefix>  # optional: shrink imported/reference SVGs before AI review
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

SVG page filenames may use either the recommended `P<NN>_<slug>.svg` form or
legacy numeric prefixes such as `01_cover.svg`; pipeline tools normalize both to
the same spec page IDs (`P01`, `P02`, ...). See [SVG Pipeline Tools](./docs/svg-pipeline.md).

Image generation:

```bash
python3 scripts/latex_render.py <project_path>
python3 scripts/latex_render.py <project_path> --providers codecogs,quicklatex,mathpad,wikimedia
python3 scripts/image_gen.py "A modern futuristic workspace"
python3 scripts/image_gen.py --list-backends
python3 scripts/analyze_images.py <project_path>/images
```

Repository update:

```bash
python3 scripts/update_repo.py
python3 scripts/update_repo.py --skip-pip
```

## Recommendations

- Keep one user-facing entry point per workflow at the top level of `scripts/`
- Move provider-specific or helper internals into subdirectories
- Prefer the unified entry points `project_manager.py`, `finalize_svg.py`, and `image_gen.py`
- Use the default export source split: native PPTX reads `svg_output/`; SVG snapshot / legacy preview reads `svg_final/`.
- Pass `-s output` or `-s final` only when a workflow explicitly needs both export products to read from one source.

## Related Docs

- [Conversion Tools](./docs/conversion.md)
- [Project Tools](./docs/project.md)
- [SVG Pipeline Tools](./docs/svg-pipeline.md)
- [Image Tools](./docs/image.md)
- [Troubleshooting](./docs/troubleshooting.md)
- [Skill Entry](../SKILL.md)

_Last updated: 2026-07-19_
