# beautify_1to1 (Beautify 1:1 page-preservation contract)

Synthetic 3-slide source deck for the beautify route's **deterministic half**:
`ppt_to_md` must preserve the page split 1:1 (beautify never merges/splits pages —
the discriminator in AGENTS.md). The AI re-layout step (Strategist) is
non-deterministic and stays excluded; export of the re-authored pages is covered
by the Golden Set / structured fixtures.

Input: `sources/beautify_source.pptx` (3 slides, python-pptx).
Rebuild: `python3 skills/ppt-master/fixtures/beautify_1to1/rebuild_make_source.py`

Command: `python3 skills/ppt-master/scripts/source_to_md/ppt_to_md.py <copy>/sources/beautify_source.pptx -o <tmp>/out.md`

Expected (1:1 contract):
- `- Total slides: 3`
- `## Slide 1` + `第一章 背景与动机`, `## Slide 2` + `第二章 方案设计`,
  `## Slide 3` + `第三章 验证与结论` — page count and titles preserved verbatim;
  no page merged, split, or reordered.
- Body bullets of each slide present under its own page heading.
