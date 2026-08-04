# template_fill (Fill Native PPTX)

Input: `sources/acme_template.pptx` (4 slides, python-pptx synthetic, ~31 KB).
Rebuild: `python3 skills/ppt-master/fixtures/template_fill/rebuild_make_template.py`

Commands (run against a **copy**; output to temp dirs, never into this directory):

```bash
python3 skills/ppt-master/scripts/pptx_intake.py <copy>/acme_template.pptx -o <tmp>/analysis
python3 skills/ppt-master/scripts/template_fill_pptx.py scaffold <tmp>/analysis/acme_template.slide_library.json -o <tmp>/analysis/fill_plan.json --slides "1,2,3,4"
python3 skills/ppt-master/scripts/template_fill_pptx.py check-plan <tmp>/analysis/acme_template.slide_library.json <tmp>/analysis/fill_plan.json -o <tmp>/analysis/check_report.json
python3 skills/ppt-master/scripts/template_fill_pptx.py apply <copy>/acme_template.pptx <tmp>/analysis/fill_plan.json -o <tmp>/exports/filled.pptx
```

Expected: intake/scaffold/check-plan/apply all rc=0; check-plan `ok=8 warn=0 error=0`;
`pptx_delivery_check` on the output `status: passed`; python-pptx opens 4/4 slides with
the original text intact; `ppt_to_md` extracts the deck.
