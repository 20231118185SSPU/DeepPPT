# partial (Phase B resume / partial states / interruption diagnosis)

Fifteen synthetic project states (plain text files, regenerable by copying the
listed content into a fresh dir). Each tests ONE diagnosis scenario.

Diagnosis owner: `project_utils.diagnose_project()` (single source; CLI entry
`project_manager.py diagnose <project>` — Dashboard consumes the same
`derive_pipeline_state` owner, no second inference). Read-only, deterministic
across repeats except `checked_at`.

## Scenario matrix (name → expected step / blocker codes / next-action code / status)

| State | step | blockers | next | status |
|---|---|---|---|---|
| `only_sources/` | 2-sources | NO_SOURCES | NO_SOURCES | blocked |
| `confirmation_pending/` | 4-design-spec | CONFIRMATION_PENDING | CONFIRMATION_PENDING | blocked |
| `confirmation_stale/` | 4-design-spec | CONFIRMATION_STALE | CONFIRMATION_STALE | blocked |
| `confirmation_malformed/` | 4-design-spec | CONFIRMATION_MALFORMED | CONFIRMATION_MALFORMED | blocked |
| `spec_lock_no_digest/` | 5-spec-lock | SPEC_LOCK_DIGEST_MISMATCH | SPEC_LOCK_DIGEST_MISMATCH | blocked |
| `spec_lock_mode_conflict/` | 5-spec-lock | SPEC_LOCK_MODE_CONFLICT | SPEC_LOCK_MODE_CONFLICT | blocked |
| `images_partial/` | 6-images | IMAGES_PARTIAL | IMAGES_PARTIAL | blocked |
| `image_manifest_failed/` | 6-images | IMAGE_MANIFEST_FAILED | IMAGE_MANIFEST_FAILED | blocked |
| `svg_count_mismatch/` | 7a-svg-gen | SVG_COUNT_MISMATCH | SVG_COUNT_MISMATCH | blocked |
| `svg_naming_conflict/` | 7a-svg-gen | SVG_NAMING_CONFLICT | SVG_NAMING_CONFLICT | blocked |
| `quality_failed/` | 7b-postprocess | SVG_QUALITY_GATE_FAILED | SVG_QUALITY_GATE_FAILED | blocked |
| `svg_no_export/` | 7c-export | — | EXPORT_PENDING | partial |
| `exported/` | 8-export | — | VALIDATE_EXPORT | ok |
| `exported_failed/` | 8-export | E2E_FAILED, DELIVERY_FAILED | E2E_FAILED | blocked |
| `resume_phase_b/` | 5-spec-lock | — | RESUME_PHASE_B | partial |

## Commands

```bash
python3 skills/ppt-master/scripts/project_manager.py diagnose skills/ppt-master/fixtures/partial/<state>
python3 -c "import sys; sys.path.insert(0, 'skills/ppt-master/scripts'); from project_utils import diagnose_project; print(diagnose_project('skills/ppt-master/fixtures/partial/exported_failed')['blockers'])"
```

Expected: JSON with `schema: ppt-master.project-diagnosis.v1`, stable
step/blockers/next_action, `checked_at` the only varying field; bad project
path exits 2; diagnosis never writes into the project.

Notes on fixture construction:
- Non-digest-test states carry a valid `.spec_lock.digest` (generate after
  writing `spec_lock.md`); `spec_lock_no_digest/` intentionally has none.
- `confirmation_stale/` uses an ancient `confirmed_at` (2000-01-01) plus a
  `recommendations.stage3.json` with a future mtime.
- `quality_failed/` keeps `overall: PASS` with `svg_quality: FAIL`;
  `exported_failed/` carries `overall: FAIL` (E2E) + `pptx_quality status: failed`.
