# Chart Candidate Recall

`chart_recall.py` gives the Strategist a bounded, deterministic shortlist from
the live visualization catalog. It reads
`templates/charts/charts_index.json` on every invocation, so the catalog stays
the single source of truth.

## Recall Candidates

Describe one page's information shape with 3-8 concise English semantic tags.
Translate source-language or industry terms into structural meaning first.

```bash
python3 skills/ppt-master/scripts/chart_recall.py recall \
  --page P03 \
  --tag "time series" \
  --tag "three metrics" \
  --tag "direction over time" \
  --limit 6
```

Read the returned JSON without filtering. Review each candidate's `summary`,
including its `Skip` clause, before selecting it.

`--limit` accepts 3-8 and defaults to 6. It is an upper bound: when fewer
positive matches exist, `candidates` may contain fewer items or be empty.

| Field | Contract |
|---|---|
| `page` | Input `P<NN>` page key |
| `semantic_tags` | Deduplicated structural tags |
| `confidence` | Lexical recall strength; never a selection decision |
| `candidates` | Ranked catalog keys, paths, summaries, scores, and matched tags |
| `semantic_fallback` | Full live catalog, with each item carrying `key`, `path`, and `summary`; present only when low/none confidence is rerun with `--semantic-fallback` |
| `no_template_match` | Explicit fallback with an `allowed` gate |

At `high` or `medium` confidence, select the best semantic fit or retain
`no-template-match` after reviewing the bounded candidates. At `low` or `none`,
select a fitting bounded candidate directly; otherwise rerun the same command
once with `--semantic-fallback` before retaining no match.

```bash
python3 skills/ppt-master/scripts/chart_recall.py recall \
  --page P03 \
  --tag "time series" \
  --tag "three metrics" \
  --tag "direction over time" \
  --semantic-fallback
```

The scorer treats the key and the summary's `Pick` clause as positive evidence.
Terms found only in the `Skip` clause cannot make a candidate eligible and
reduce its score. This keeps the shortlist bounded without replacing semantic
judgment.

## Validate Selected Keys

Validate every selected catalog key before writing `design_spec.md` section VII
or `spec_lock.md page_charts`:

```bash
python3 skills/ppt-master/scripts/chart_recall.py validate \
  line_chart quadrant_text_bullets
```

The command exits `0` only when every argument is a non-empty, unique, exact
catalog key. It exits `1` for empty arguments, normalized duplicates, malformed
or absent keys, and reports those cases separately in JSON. `no-template-match`
is not a catalog key: record its fallback and reason in the Design Spec, and
omit the page from `page_charts`.

## Design Spec Mapping

Keep DeepPPT's existing section VII audit format:

- Copy the selected candidate's key, path, and summary verbatim from the JSON.
- Write one page-specific usage statement.
- Draw runners-up from real returned candidates and state why they lose for the
  current page.
- Do not serialize scores or lexical confidence into the Design Spec.

Only open the selected SVG as an Executor reference for its mapped page. Do not
load unrelated catalog SVGs.
