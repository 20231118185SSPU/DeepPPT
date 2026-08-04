# Route Fixtures (合成路线回归依据)

> Synthetic, non-sensitive, deterministic fixtures for the formally supported routes.
> All content is fabricated (no user brands, personal data, keys, or restricted material).
> Created under `plans/deepppt2-practical-delivery-optimization-agent-brief.md` Phase 2-3;
> binaries are original (license N/A), regenerable via the `rebuild_*.py` scripts in each set.

## Matrix (route × fixture × gate)

| Set | Route / contract | Inputs | Gate commands | Expected |
|---|---|---|---|---|
| `template_fill/` | Fill Native PPTX | `sources/acme_template.pptx` (4 slides, python-pptx) | `pptx_intake` → `template_fill_pptx.py scaffold --slides 1,2,3,4` → `check-plan` → `apply` → `pptx_delivery_check` + python-pptx open + `ppt_to_md` | all rc=0; check-plan ok=8 warn=0 err=0; delivery passed; 4/4 slides keep text |
| `enhance/` | Enhance Native PPTX | `sources/enhance_source.pptx` (3 slides) + `notes/00{1..3}.md` | `native_enhance_pptx.py init --project-dir <tmp> --transition fade` → `plan` → set plan `status: confirmed`, disable `audio`/`timings` (simulated user gate) → `validate` → `apply` → delivery + readback | init/plan rc=0; validate passed; apply rc=0 (Notes 3, Transition-only 3); notes readback 3/3; `p:transition` present |
| `structured/` | Generate structured | `spec_lock.md` (mode: structured + rosters) + `svg_output/` (3 pages, root master/layout markers + title slot) + `templates/` workspace + `notes/total.md` | `spec_lock_validate` → `svg_quality_checker` → `total_md_split` → `finalize_svg` → `svg_to_pptx` → `e2e_validate` → `pptx_delivery_check` | all rc=0; export declares `PPTX structure: structured`; package has real `slideMaster1.xml` + `slideLayout12.xml` + title placeholder; e2e 7/7 |
| `partial/` | Interruption recovery / Phase B resume | 15 synthetic project states | `project_manager.py diagnose <state>` (owner: `project_utils.diagnose_project`) | 15/15 scenarios: stable step + blockers + unique next action; determinism (minus `checked_at`); read-only; bad path rc=2 |
| `beautify_1to1/` | Beautify 1:1 page-preservation | `beautify_source.pptx` (3 slides) | `ppt_to_md` on a copy | `Total slides: 3` + 3 page headings + titles verbatim (AI re-layout step excluded — non-deterministic) |
| `space_report/` | Read-only space report | 2 synthetic projects with exact-size files | `space_report.py <copy>` / `--archive-plan` | summary 880 B / renewable 350 B; archive plan paths+sizes exact; read-only; bad root rc=2 |
| `trace_calibration/` | Local run metrics | synthetic `trace.jsonl` (10 events) + harness/pptx_quality sidecars | `run_summary.py <copy> -o <tmp>` | schema `ppt-master.run-summary.v1`; null/0 semantics; retry/image counts; determinism; sensitive key fail-closed rc=1 |
| `docx_complex/` | Source fidelity (DOCX) | `complex_v2.docx` (vMerge restart/continue, gridSpan, Wingdings 2 F06A-F06C + Wingdings F081 circled digits, multi-paragraph cell, inline image) | `doc_to_md` → assert `## 原生表格` recovery | rc=0; vMerge ownership + continuation repetition; gridSpan repetition; ① ② ① mapping; paragraphs joined; image extracted; no silent loss. Corrupted inputs (`broken_*`) rc≠0 |
| `pptx_complex/` | Source fidelity (PPTX) | `complex_source.pptx` (3 slides: merged table, image + notes, symbol run) | `ppt_to_md` → assert content | rc=0; merged table visible; key numbers 1,234/1,386/12.4%/18,500/19,912 preserved; notes captured; symbols ①②③→✓±℃¥ preserved. Corrupted input rc≠0 |

## Smoke integration

The fast contract checks run in `smoke_check.py --integration` Tests 10-12 (CI smoke job):
Test 10 route contracts (partial diagnostics, converter fidelity, structured lock),
Test 11 run_summary aggregation, Test 12 interruption diagnosis, Test 13 space report.
Full renders (PowerPoint COM) stay manual/advisory — see `scripts/docs/geometry-audit.md` review order.

## Regeneration

Each set carries a `rebuild_*.py` that regenerates its binary (content-equivalent;
python-pptx timestamps vary). Partial states are plain text files documented in
`partial/README.md`.

## Cleanup

Fixtures are inputs only — they never write into their own directory when run
(mandatory). Converter/test outputs must go to a temp dir; never modify these files.
