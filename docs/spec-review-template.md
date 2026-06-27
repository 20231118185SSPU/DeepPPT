# Spec Review Template

> After each PPT generation delivery, use this template to review which decisions should be
> permanently locked into `spec_lock.md` or workflow rules. Fill in during Step 8a (SPEC REVIEW).
>
> **Guiding principle**: "Will this recur in future generations?" If yes → update spec/workflow.
> If one-off → skip. Spec thickness = your refusal to repeat decisions.

---

## 1. User Corrections Log

Record every correction the user made during this generation.

| # | What was corrected | Before (AI default) | After (user correction) | Category |
|---|-------------------|---------------------|------------------------|----------|
| 1 | | | | one-off / repeat / uncertain |
| 2 | | | | |
| 3 | | | | |

---

## 2. Decision Classification

For each correction above, classify whether it should be persisted.

### One-off (skip)
> Corrections unique to this deck that won't recur. E.g., "this page needs exactly 5 items because the client has 5 divisions."

- [ ] None this round

### Repeat (persist)
> Corrections that reflect a general principle. E.g., "always use dark backgrounds for tech decks" or "transition pages must have centered text."

| # | Decision | Persist to | Action |
|---|----------|-----------|--------|
| 1 | | spec_lock / workflow / reference / template | |
| 2 | | | |

### Uncertain (flag for next round)
> Corrections that might be general but need one more data point.

| # | Decision | Why uncertain |
|---|----------|---------------|
| 1 | | |

---

## 3. Workflow Rule Updates

List any workflow rules that need updating based on this generation.

| File | Section | Current rule | Proposed change | Reason |
|------|---------|-------------|----------------|--------|
| | | | | |

---

## 4. Spec Lock Updates

List any values that should be added to or modified in `spec_lock.md` templates.

| Field | Current default | Proposed default | Applies to (intent/style) |
|-------|----------------|-----------------|--------------------------|
| | | | |

---

## 5. Summary

- **Total corrections**: N
- **One-off (skipped)**: N
- **Persisted (spec/workflow updated)**: N
- **Flagged for next round**: N

> After completing this review, execute the persist actions immediately (update spec_lock templates, workflow files, or references). Do not defer — the next generation should benefit from this review.
