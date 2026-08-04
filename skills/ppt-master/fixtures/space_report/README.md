# space_report (read-only project space report)

Two synthetic projects with exact-size files exercising the renewability
classification (Brief Phase 6.2):

- `proj_a/` (720 B total): non-renewable `images/img.bin` (100) + `exports/deck.pptx` (300)
  + `spec_lock.md` (30); renewable `backup/old.bin` (200) + `quality/harness.json` (50)
  + `trace.jsonl` (40) → renewable 290.
- `proj_b/` (160 B total): non-renewable `sources/s.md` (80) + `notes/total.md` (20);
  renewable `validation/report.json` (60) → renewable 60.

Command: `python3 skills/ppt-master/scripts/space_report.py <copy>` (and
`--archive-plan <out.json>` for the dry-run plan).

Expected: summary `{projects: 2, bytes: 880, renewable_bytes: 350}`; top order
`proj_a` > `proj_b`; archive plan lists exactly `trace.jsonl`, `backup/old.bin`,
`quality/harness.json` (proj_a) and `validation/report.json` (proj_b), each with
recovery note. Read-only: running the report never modifies the tree
(regenable via `python3 .../space_report.py --help` / copy; exact sizes above).
