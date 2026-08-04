# trace_calibration (run_summary metrics)

Synthetic trace + sidecar reports exercising every `run_summary.py` metric
semantic. All content fabricated; the single `bridge_status` event is the
intentional legacy event (no `schema_version`).

Inputs: `trace.jsonl` (11 events, incl. one `pptx_export`) + `annotations.jsonl` (3 records) +
`quality/harness.json` + `quality/pptx_quality.json`.

Command: `python3 skills/ppt-master/scripts/run_summary.py <copy> -o <tmp>/run_summary.json`

Expected summary (contract):
- `route: "generate"`, `slide_count: 3` (from pptx_quality.json), `events_total: 11`.
- `stages.strategist.duration_ms: 2000` (measured); `stages.images.duration_ms: null`
  (start only — not measured); `stages.noop.duration_ms: 0` (writer-measured zero,
  must NOT become null).
- `gates: {svg_quality: PASS, image_gen_attempt: PASS}` (latest per gate).
- `errors: {count: 1, by_code: {IMG_E001: 1}}`.
- `retry_count: 1` (svg_quality FAIL→PASS; a step_start+step_complete pair is one
  run, not a retry).
- `image_attempts: 2` (image_gen_attempt + image_search; the `images` stage name
  must not count).
- `annotations.live_preview_count: 3` (from `annotations.jsonl` — svg_editor server product);
  `annotations.pptx_reexport_count: 1` (from the `pptx_export` event);
  `svg_regeneration_count: null` + not-wired (agent-driven, no script hook).
- `final_results: {delivery: "passed", e2e: "PASS", visual: null}`.
- Deterministic: repeated aggregation on the same input yields byte-identical JSON.
- Sensitive fail-closed: any event with a forbidden key (`prompt`, `api_key`,
  `token`, `secret`, …) aborts with exit 1 and writes no summary.
