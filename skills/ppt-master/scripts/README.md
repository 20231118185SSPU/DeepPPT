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
python3 scripts/project_manager.py validate <project_path> --start-dashboard --no-browser
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

| Area | Primary scripts | Documentation |
|------|-----------------|---------------|
| Conversion | `source_to_md/pdf_to_md.py`, `source_to_md/doc_to_md.py`, `source_to_md/excel_to_md.py`, `source_to_md/ppt_to_md.py`, `source_to_md/web_to_md.py`, `pptx_intake.py` | [docs/conversion.md](./docs/conversion.md) |
| Project management | `project_manager.py`, `batch_validate.py`, `generate_examples_index.py`, `error_helper.py`, `pptx_template_import.py`, `template_fill_pptx.py` | [docs/project.md](./docs/project.md) |
| SVG pipeline | `finalize_svg.py`, `svg_to_pptx.py`, `total_md_split.py`, `svg_quality_checker.py`, `extract_svg_assets.py`, `animation_config.py`, `notes_to_audio.py` | [docs/svg-pipeline.md](./docs/svg-pipeline.md) |
| Spec maintenance | `update_spec.py` | [docs/update_spec.md](./docs/update_spec.md) |
| Image tools | `image_gen.py`, `latex_render.py`, `analyze_images.py`, `gemini_watermark_remover.py` | [docs/image.md](./docs/image.md) |
| Research gates | `research/browse_ai.py`, `research/research_gate.py`, `research/asset_gate.py`, `research/sync_research_outputs.py`, `confirm_ui_gate.py` | Deep-research and Step 4/5 gate docs in `../workflows/` |
| Repo maintenance | `update_repo.py` | README install/update section |
| Troubleshooting | validation, preview, export, dependency issues | [docs/troubleshooting.md](./docs/troubleshooting.md) |

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
python3 scripts/dashboard/server.py <project_path> --daemon --no-browser
```

Or ask `project_manager.py` to do the same best-effort startup after a successful
project command:

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169 --start-dashboard --no-browser
python3 scripts/project_manager.py import-sources <project_path> <source_files...> --start-dashboard --no-browser
python3 scripts/project_manager.py validate <project_path> --start-dashboard --no-browser
```

Without `--start-dashboard`, project commands only print the Dashboard hint.

Default port: `8765`; log: `<project_path>/dashboard/dashboard.log`. Launch failure is non-fatal. Dashboard shows status, artifacts, quality, trace, and bridge state only; it does not replace Confirm UI, Live Preview, quality gates, post-processing, or export.

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

Post-processing and export:

```bash
python3 scripts/extract_svg_assets.py <svg_dir> --icons-dir <icons_dir> --inplace --id-prefix <prefix>  # optional: shrink imported/reference SVGs before AI review
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

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

_Last updated: 2026-04-09_
