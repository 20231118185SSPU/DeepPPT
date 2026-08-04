# structured (Generate structured)

Inputs: `spec_lock.md` (mode: structured + template_reuse_scope: layout + full
`pptx_masters` / `pptx_layouts` / `page_pptx_layouts` rosters) + `svg_output/`
(3 pages with root master/layout markers and a title slot) + `templates/`
(workspace `design_spec.md` with `replication_mode: standard` + prototype
`t03_content.svg`) + `notes/total.md` + `images/sample_badge.png`.

Commands (against a copy; outputs to temp dirs):

```bash
python3 skills/ppt-master/scripts/spec_lock_validate.py <copy>
python3 skills/ppt-master/scripts/svg_quality_checker.py <copy>
python3 skills/ppt-master/scripts/total_md_split.py <copy>
python3 skills/ppt-master/scripts/finalize_svg.py <copy>
python3 skills/ppt-master/scripts/svg_to_pptx.py <copy>
python3 skills/ppt-master/scripts/e2e_validate.py <copy> --pptx <copy>/exports/<newest>.pptx
python3 skills/ppt-master/scripts/pptx_delivery_check.py <copy>/exports/<newest>.pptx
```

Expected: all rc=0; `spec_lock_validate` PASS (12 sections); export log declares
`PPTX structure: structured` and `1 master(s), 1 layout(s), 1 placeholder definition(s)`;
package contains real `ppt/slideMasters/slideMaster1.xml` + `ppt/slideLayouts/slideLayout12.xml`
with a title placeholder; e2e 7/7; delivery passed.
