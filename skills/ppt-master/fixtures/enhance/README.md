# enhance (Enhance Native PPTX)

Inputs: `sources/enhance_source.pptx` (3 slides, ~30 KB) + `notes/001.md`..`003.md`.
Rebuild: `python3 skills/ppt-master/fixtures/enhance/rebuild_make_source.py`

Commands (project dir must NOT be `projects/`; use `--project-dir <tmp>`):

```bash
python3 skills/ppt-master/scripts/native_enhance_pptx.py init <copy>/enhance_source.pptx --name enhance_fix --project-dir <tmp>/proj --transition fade --transition-duration 800
python3 skills/ppt-master/scripts/native_enhance_pptx.py plan <tmp>/proj
# 模拟用户确认门（真实运行中为 BLOCKING 人工确认）：
#   plan JSON: modules.audio.enabled=false, modules.timings.enabled=false, status="confirmed"
#   并把 notes/00{1..3}.md 复制到 <tmp>/proj/notes/
python3 skills/ppt-master/scripts/native_enhance_pptx.py validate <tmp>/proj --materials notes
python3 skills/ppt-master/scripts/native_enhance_pptx.py apply <tmp>/proj
```

Expected: init/plan rc=0; validate `status: passed`; apply rc=0 with
`Notes applied: 3, Transition-only slides: 3`; output delivery check passed;
notes readback 3/3 matches `notes/00*.md`; slide XML contains `p:transition`.
