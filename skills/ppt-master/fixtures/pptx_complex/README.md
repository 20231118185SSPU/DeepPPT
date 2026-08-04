# pptx_complex (PPTX source fidelity)

Input: `complex_source.pptx` (3 slides, python-pptx: merged table cell, inline
image + speaker notes, symbol run).
Rebuild: `python3 skills/ppt-master/fixtures/pptx_complex/rebuild_make_source.py`

Command: `python3 skills/ppt-master/scripts/source_to_md/ppt_to_md.py <copy>/complex_source.pptx -o <tmp>/out.md`

Expected:
- Slide 1 table: merged cell content `核心指标` present, all key numbers preserved
  (`1,234`, `1,386`, `12.4%`, `12.3%`, `18,500`, `19,912`).
- Slide 2: image extracted (`<out>_files/image1.png`), `### Speaker Notes` with
  `本页备注：图片为合成占位图，无敏感内容。`.
- Slide 3: symbol run intact (`圈号 ①②③ · 箭头 → · 检查 ✓ · 温度 ±2℃ · 汇率 ¥7.12`).
- Corrupted input (truncated pptx) exits non-zero.
