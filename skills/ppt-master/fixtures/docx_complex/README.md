# docx_complex (DOCX source fidelity)

Input: `complex_v2.docx` (~4.7 KB, stdlib-built: vMerge restart/continue cells,
gridSpan-2 cells, Wingdings 2 F06A-F06C + legacy Wingdings F081 circled digits,
multi-paragraph cell, inline PNG image).
Rebuild: `python3 skills/ppt-master/fixtures/docx_complex/rebuild_make_docx.py`

Command: `python3 skills/ppt-master/scripts/source_to_md/doc_to_md.py <copy>/complex_v2.docx -o <tmp>/out.md`

Expected (fidelity contract):
- `## 原生表格（docx tables 恢复，含合并单元格）` present with Table 1 + Table 2.
- Table 1: vMerge restart cell owns text; continuation rows repeat restart text;
  gridSpan-2 values appear twice per row; no phantom rows.
- Table 2: `① 区域一 | ② 区域二 | ① 区域三` (F06A/F06B/F081 → U+2460/2461/2460);
  multi-paragraph cell joined with a space; `42` preserved.
- Inline image extracted next to the output (`*_files/image_001.png`).
- Corrupted inputs (bad zip / broken XML) exit non-zero — no silent "success".

Keys to assert: `2026 Q1`, `12.4%`, `持平`, `指标 A`, `指标 B`, `① 区域一`, `多段落 第二段内容`.
