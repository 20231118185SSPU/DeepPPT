> Status: implemented audit.
> Authority: non-authoritative; `skills/ppt-master/SKILL.md`, template workflows, and template indexes remain authoritative.
> Implemented in: user-confirmed deletion of the low-score candidates recorded below.

# Template Quality Audit - 2026-07-04

## Scope

This audit covers the current template library under:

- `skills/ppt-master/templates/layouts/`
- `skills/ppt-master/templates/layouts/content_pages/`
- `skills/ppt-master/templates/brands/`
- `skills/ppt-master/templates/layouts/layouts_index.json`
- `skills/ppt-master/templates/brands/brands_index.json`

Deletion was executed after explicit user confirmation on 2026-07-04. The deleted candidates were `pixel_retro`, `content_pages/creative`, `content_pages/project_management`, and `event_presentation`; their index entries were removed from `layouts_index.json` and `brands_index.json`.

## Rubric

| Dimension | Weight | Review question |
|---|---:|---|
| Visual design | 30% | Does the template have coherent palette, typography, spacing, and hierarchy? |
| Usefulness | 25% | Is the intended scenario specific and likely to recur? |
| Completeness | 20% | Does the package have a useful page/variant set and expected preview assets? |
| Code quality | 15% | Are SVG/design assets organized consistently enough for Dashboard and agents? |
| Documentation | 10% | Is `design_spec.md` or index metadata clear, bilingual where required, and discoverable? |

Score interpretation: `>= 3.5` retain, `< 3.5` proposed deprecate/delete after user confirmation.

## Scoring Table

| Template | Type | Score | Decision | Notes |
|---|---|---:|---|---|
| `academic_defense` | layout | 4.2 | Retain | Complete 5-page academic deck, clear bilingual metadata, strong recurring use case. |
| `ai_ops` | layout | 4.4 | Retain | Best fit for architecture-heavy technical decks; 6 pages including `reference_style.svg`. |
| `government_blue` | layout | 4.0 | Retain | Useful formal reporting template; overlaps with `government_red` but visual tone differs enough. |
| `government_red` | layout | 3.8 | Retain | Useful for formal government contexts; keep unless user wants a smaller government pack. |
| `medical_university` | layout | 4.1 | Retain | Specific vertical, complete page roster, clear metadata. |
| `pixel_retro` | layout | 3.4 | Deleted after confirmation | Niche style and lower general utility; user confirmed removal. |
| `psychology_attachment` | layout | 4.0 | Retain | Specific counseling/training niche with adequate completeness and documentation. |
| `story_driven` | layout | 4.3 | Retain | Strong match for long research decks and narrative workflows; 6-page package. |
| `content_pages/_shared` | content variants | 4.0 | Retain | Small but broadly useful utility set. |
| `content_pages/academic` | content variants | 4.5 | Retain | Deepest content-page family, including chart variants. |
| `content_pages/business` | content variants | 4.1 | Retain | Good pitch/proposal coverage. |
| `content_pages/creative` | content variants | 3.3 | Deleted after confirmation | Only 4 variants and a saturated purple/pink/yellow palette; user confirmed removal. |
| `content_pages/data_analysis` | content variants | 4.0 | Retain | Chart-first scenario is clear; useful complement to chart templates. |
| `content_pages/project_management` | content variants | 3.3 | Deleted after confirmation | Only 4 variants and relatively one-note purple palette; user confirmed removal. |
| `content_pages/report` | content variants | 4.2 | Retain | Strong operational reporting coverage. |
| `content_pages/tech_sharing` | content variants | 4.3 | Retain | Distinct code/terminal/architecture variants with recurring use cases. |
| `anthropic` | brand | 3.8 | Retain | Clear identity preset with SVG logo previews. |
| `event_presentation` | brand | 3.2 | Deleted after confirmation | Useful keynote style, but no root SVG/logo preview; user confirmed removal. |
| `google` | brand | 3.8 | Retain | Clear identity preset with SVG logo previews. |

## Proposed Deprecation Or Rework List

These candidates were confirmed by the user and removed from the template library:

| Candidate | Action taken | Reason | Future replacement path |
|---|---|---|---|
| `pixel_retro` | Deleted | Very niche and less reusable than technical/business templates. | Recreate later only as an opt-in novelty template with stronger previews. |
| `content_pages/creative` | Deleted | Thin variant set and visually saturated palette. | Rebuild as a fuller portfolio/case-study/image-grid family with rebalanced colors. |
| `content_pages/project_management` | Deleted | Thin variant set; overlaps with report/business planning pages. | Merge roadmap/gantt/checklist ideas into `report` or rebuild with sprint/risk/dependency/status variants. |
| `event_presentation` | Deleted | Brand preset has no SVG preview assets, lowering Dashboard discoverability. | Recreate as a full deck/layout template or brand with root SVG previews. |

## Recommended New Template Directions

| Direction | Scenario | Why it fills a gap |
|---|---|---|
| Tech startup pitch | Seed/Series-A fundraising, product-market fit, launch strategy | Current business pages cover tactics, but no full modern startup pitch narrative exists. |
| Academic conference minimal | Paper talks, lab seminars, conference keynotes | Complements `academic_defense` with a lighter, figure-first white layout. |
| Consulting strategy report | Executive strategy, market entry, transformation roadmap | Needed for dense, structured, board-level decks with tables, issue trees, and recommendations. |
| Education/training courseware | Workshops, internal training, classroom modules | Current psychology/medical templates are vertical-specific; no general training deck package exists. |
| Formal public-sector data report | Government/statistical office reporting with tables and charts | Existing government templates are presentation-oriented; data-heavy public reporting needs stronger table/chart layouts. |

## Quality Standard For Future Templates

New global layout/deck templates should meet these minimums before registration:

- `design_spec.md` frontmatter includes `summary` and `summary_zh`.
- At least one root-level `.svg` preview exists; full deck layouts should include a coherent page roster.
- `layouts_index.json` or `brands_index.json` mirrors the template id and bilingual discovery metadata.
- Scenario is specific enough for agents to choose or reject it without guessing.
- Palette avoids being dominated by a single hue family unless brand identity explicitly requires it.
- Content-page families should target at least 5 variants unless the family is intentionally shared utility content.

## Closed Decisions

1. `pixel_retro` removed from the template library.
2. `content_pages/creative` and `content_pages/project_management` removed from the template library.
3. `event_presentation` removed from the brand library.

## Remaining Future Choice

Pick 2-3 new template directions to implement first.
