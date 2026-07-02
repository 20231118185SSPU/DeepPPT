> See [`image-generator.md`](./image-generator.md), [`image-searcher.md`](./image-searcher.md), and [`image-source-routing.md`](./image-source-routing.md) for path-specific behavior and source-pack routing.

# Image Acquisition Common Reference

Shared baseline for both acquisition paths. Path-specific behavior lives in the path's own reference.

---

## 1. Trigger Condition

Active when at least one resource list row has `Acquire Via: ai` or `Acquire Via: web`. Rows with `user` / `formula` / `placeholder` are skipped.

| Mode | Trigger |
|---|---|
| In-pipeline | `generate-ppt` workflow, image rows present |
| Standalone | Direct request against an existing project |

---

## 2. Image Resource List Format

Defined in `design_spec.md §VIII`. Status enum: see [`svg-image-embedding.md`](svg-image-embedding.md).

| Filename | Dimensions | Purpose | Type | Acquire Via | Status | Reference | Source pack | Copyright risk | Selection reason |
|---|---|---|---|---|---|---|---|---|---|
| cover.png | 1280x720 | Cover background | Background | `ai` | Pending | Modern tech abstract, deep blue gradient #0A2540 | — | — | — |
| team.jpg | 800x600 | Team photo | Photography | `web` | Pending | Diverse engineering team in modern office | `generic_atmosphere` | low | Generic workplace mood image |
| formula_001.png | 736x168 | Block equation on P03 | Latex Formula | `formula` | Rendered | `E = mc^2` | — | — | — |

**Required per non-skipped row**: `Acquire Via`, `Status`, `Reference`.

**Required per web row**: `Source pack`, `Copyright risk`, and `Selection reason`. Source pack definitions live in [`image-source-routing.md`](./image-source-routing.md).

---

## 3. Path Dispatch

For each row with `Status: Pending`:

| Acquire Via | Load reference | Run | Success status |
|---|---|---|---|
| `ai` | [`image-generator.md`](./image-generator.md) | `image_gen.py` | `Generated` |
| `web` | [`image-searcher.md`](./image-searcher.md) | `image_search.py` | `Sourced` |
| `user` | — | — | (already `Existing`) |
| `formula` | — | — | (already `Rendered`) |
| `placeholder` | — | — | (already `Placeholder`) |

> Lazy load: an all-`web` deck never reads `image-generator.md`, and vice versa.

---

## 4. Analysis Phase

Before processing any row:

1. `read_file <project_path>/design_spec.md` — extract color scheme, canvas format, target audience
2. Read [`image-source-routing.md`](./image-source-routing.md) if any `web` row exists or any `ai` row needs a concrete reference image
3. Group resource list rows by `Acquire Via`
4. Confirm `project/images/` exists

---

## 5. Verification Phase

After all rows reach terminal status:

- Every non-skipped row has a file at `project/images/<filename>`, or is marked `Needs-Manual`
- No `Pending` rows remain
- `image_prompts.json` exists when ≥1 ai row processed; every entry has `status ∈ {Generated, Failed, Needs-Manual}` (no `Pending` remaining)
- `image_sources.json` exists when ≥1 web row processed; every entry has `license_tier ∈ {no-attribution, attribution-required}`
- New web rows carry routing provenance when available: `source_pack`, `selection_reason`, `copyright_risk`, and manual review/discovery fields from [`image-source-routing.md`](./image-source-routing.md) §6.3

> `Needs-Manual` is a legitimate terminal state for ai rows — Step 7 entry waits for the user to place the file. See [`image-generator.md`](./image-generator.md) §3.2 Offline Manual Mode.

---

## 6. Failure Handling

**Hard rule**: acquisition failures MUST NOT halt the pipeline.

1. Try once
2. On recoverable failure (network, no candidates, license rejection, rate limit), retry once with broadened parameters
3. On second failure, set `Status: Needs-Manual`, log the reason in conversation, continue
4. After the phase completes, summarize all `Needs-Manual` rows for the user — list filenames, where prompts live (`images/image_prompts.md` paste-ready blocks for ai rows; refresh via `image_gen.py --render-md` if stale), and where to place generated files (`project/images/<filename>`)

`Needs-Manual` is also the entry status for **Offline Manual Mode** (no `IMAGE_BACKEND` configured, no host-native image tool in use). Affected ai rows are marked `Needs-Manual` from the start without a failed attempt — see [`image-generator.md`](./image-generator.md) §3.2.

Path-specific retry policies (provider chain, backend chain) live in the path's own reference.

---

## 7. Credits — Single Source of Truth

License / attribution data lives **only** in `project/images/image_sources.json`.

**Forbidden — credits anywhere else**:

- `notes/*.md` (TTS would speak them in the audio export)
- `total.md` (gets split, then overwritten)
- SVG `<title>` / `<desc>` (stripped by `svg_to_pptx.py`)
- A separate "Image Credits" appendix slide (lost on single-page sharing)

Executor reads the manifest per slide and renders inline credits when needed — see [`executor-base.md`](./executor-base.md) §6.1 and [`image-searcher.md`](./image-searcher.md) §7.

---

## 8. Handoff with Strategist

The `Reference` field is **intent**, not a query. Strategist writes free-form intent; the receiving role translates.

| ✅ Intent | ❌ Pre-processed |
|---|---|
| `"Diverse engineering team in modern office, natural light"` | `"team office light"` |
| `"Abstract digital waves, deep navy gradient #0A2540"` | `"use openverse, search 'waves'"` |

**Source routing handoff**: For `Acquire Via: web`, Strategist also writes `Source pack`, `Copyright risk`, and `Selection reason` in §VIII. For high-ambiguity subjects, mark the eventual query row with `needs_manual_review: true` and `discovery_only: true`. See [`image-source-routing.md`](./image-source-routing.md) §6.

### 8.1 Per-page image decision audit

Before writing any `ai` or `web` row, Strategist decides whether the page needs an external image at all.

| Page condition | Default image choice |
|---|---|
| Dense explanation / comparison / timeline / data page | Use an informational AI diagram/infographic or native SVG; avoid decorative atmosphere images |
| Sparse title / transition / ending / cover page | Use hero, atmosphere, concept, or auxiliary imagery with editable SVG text |
| Mostly structured data / tables / charts | Prefer native SVG visualization; external image only for context or texture |
| Real person / place / event with ambiguous references | Do not use img2img by default; use text-to-image symbolic support, native SVG, or manually verified assets |
| Named IP / product / historical / academic subject | Route through source packs; generic stock is allowed only for atmosphere/background support |

Every `image_prompts.json` item records `image_intent`, `page_evidence`, `text_image_relationship`, and `fallback_plan`. These fields are audit metadata: they explain why the page has that image, how the prompt relates to the page text, and what happens when the chosen acquisition path fails.

---

## 9. Handoff with Executor

Executor consumes the resource list plus:

| Artifact | Path | Purpose |
|---|---|---|
| Image files | `project/images/*.{jpg,png,webp}` | `<image>` references |
| Manifest | `project/images/image_sources.json` | `license_tier` per Sourced image |

Executor does NOT invoke `image_gen.py` / `image_search.py`.

---

## 10. Task Completion Checkpoint

```markdown
## ✅ Image Acquisition Phase Complete
- [x] {N} rows processed (`ai`: {a} / `web`: {b})
- [x] {a} `Generated`, {b} `Sourced`, {c} `Needs-Manual`
- [x] image_prompts.json / image_sources.json written
- [ ] **Next**: Auto-proceed to Executor phase
```
