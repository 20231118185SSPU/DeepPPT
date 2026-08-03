# User Project Workspace

This directory is used for storing in-progress projects.

## Create a New Project

```bash
python3 skills/ppt-master/scripts/project_manager.py init my_project --format ppt169
```

## Directory Structure

A typical project usually contains the following:

```
project_name_format_YYYYMMDD/
├── README.md
├── design_spec.md
├── sources/
│   ├── Raw files / URL archives / Converted Markdown
│   └── *_files/                  # Markdown companion resource directory (e.g., images)
├── images/                       # Image assets used by the project
├── analysis/                     # Extracted source facts (PPTX intake bundle, image_analysis.csv)
├── notes/
│   ├── 01_xxx.md
│   ├── 02_xxx.md
│   └── total.md
├── svg_output/
│   ├── 01_xxx.svg
│   └── ...
├── svg_final/
│   ├── 01_xxx.svg
│   └── ...
├── templates/                    # Project-level templates (if any)
└── *.pptx
```

Projects can remain at different stages and do not necessarily have all artifacts at once. For example:

- Only `sources/` archiving and the Design Specification & Content Outline (design_spec) are complete
- `svg_output/` has been generated, but post-processing has not yet been executed
- `svg_final/`, `notes/`, and `*.pptx` are all complete

## Notes

- Contents under this directory are excluded by `.gitignore`
- Completed projects can be moved to the `examples/` directory for sharing
- Files outside the workspace are copied by default; files within the workspace are moved directly to the project's `sources/`

## Lifecycle Governance (2026-08-03)

Project folders are classified into three tiers; only active and archived projects may live here long-term.

| Tier | Criteria | Handling |
|---|---|---|
| **active** | Being generated or recently delivered (default) | Keep as-is; Dashboard 产物展台 (`dashboard/artifacts_index.json`) is the local search index |
| **archive** | Delivered and no longer being edited | Keep the folder (or move out of the repo); export a final PPTX copy before archiving |
| **disposable** | Auto-generated snapshots and caches | Safe to delete; see below |

**Disposable artifacts** (auto-generated, safe to delete):

- `backup/<timestamp>/` — `svg_output/` archive written automatically in default-flow export mode; **keep only the latest timestamp, old timestamps may be deleted** (project_manager.py documents this). A cleanup pass on 2026-08-03 removed 34 old snapshots (~0.9 GB).
- `dashboard/`, `.preview/`, `.review/`, `validation/` (regenerated reports), `__pycache__/` — runtime state, gitignored.

**Search**: each project's `dashboard/artifacts_index.json` (written whenever the Dashboard serves `/api/artifacts`) lists every artifact with type, phase (制作思路 / 设计契约 / 生成页面 / 导出成品), size and mtime — grep/jq it for local artifact search without starting the Dashboard.
