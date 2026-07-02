> See [`image-base.md`](./image-base.md) for acquisition dispatch and [`image-searcher.md`](./image-searcher.md) for web-provider execution.

# Image Source Routing Reference Manual

Source routing defines which image sources are appropriate for each subject domain before `image_search.py` or `image_gen.py` receives a row.

**Trigger**: any deck with `ppt_brief.json`, `detailed_outline.json`, or `design_spec.md §VIII` image rows that require `Acquire Via: web` or reference images for `Acquire Via: ai`.

---

## 1. Source Pack Contract

**Hard rule**: Every semantically specific web row must declare a `source_pack`. Generic stock providers are not the default source of truth for people, IP, products, history, academic content, or recent events.

| Field | Meaning |
|---|---|
| `id` | Stable pack identifier, e.g. `generic_atmosphere`, `official_product`, `academic_science` |
| `domains` | Subject domains this pack covers |
| `priority_sources` | Human-readable source classes to try first |
| `allowed_providers` | Providers that may produce final downloadable assets |
| `disabled_providers` | Providers disabled by default for this pack |
| `query_builder` | Query construction rule |
| `copyright_policy` | Risk level and permitted use behavior |
| `manual_review` | Whether human review is required before final use |
| `provenance_fields` | Fields that must be preserved in `image_sources.json` |

**Per-row routing fields**:

| Field | Type | Notes |
|---|---|---|
| `source_pack` | string | One source pack id from §2 |
| `preferred_sources` | string[] | Source classes such as `official_site`, `wikimedia`, `museum_open_access` |
| `preferred_providers` | string[] | Script provider ids, when a provider is appropriate |
| `disabled_providers` | string[] | Provider ids to exclude for this row |
| `allow_generic_stock` | bool | `true` only for stock-appropriate rows |
| `discovery_only` | bool | `true` when browser / Google-style search may discover source pages but cannot auto-clear license |
| `needs_manual_review` | bool | `true` for high ambiguity or high copyright-risk subjects |
| `copyright_risk` | enum | `low` / `medium` / `high` |
| `selection_reason` | string | Why this row uses the selected source pack |

---

## 2. Source Pack Matrix

| Source pack | Use for | Priority sources | Allowed providers | Disabled / downgraded | Review |
|---|---|---|---|---|---|
| `generic_atmosphere` | Mood, background, workplace, lifestyle, abstract business scenes | Pexels, Unsplash, Pixabay, Openverse | `pexels`, `unsplash`, `pixabay`, `openverse`, `flickr` | None by default | Usually no |
| `open_licensed_commons` | Open-license general education, geography, places, public-domain style assets | Wikimedia, Openverse, Flickr CC | `wikimedia`, `openverse`, `flickr` | Generic stock only as fallback | When subject ambiguous |
| `academic_science` | Science, technology, medical, academic concepts, institutional diagrams | Wikimedia, NASA, NOAA, NIH, universities, research institutions | `wikimedia`, `nasa`, `openverse` | `pexels`, `pixabay`, `unsplash` unless atmosphere only | Medium / high |
| `historical_culture` | History, artifacts, museums, archives, cultural heritage, art | Wikimedia, Smithsonian, museum open collections, national archives | `wikimedia`, `smithsonian`, `openverse` | Generic stock except modern atmosphere | Medium |
| `anime_game_ip` | Named characters, games, anime, IP-specific key visuals, skins, official art | Official site, official wiki, publisher press kit, Fandom, Moegirl, BiliWiki | Usually none for auto-final; browser discovery only | `pexels`, `pixabay`, `unsplash`, generic Openverse | High |
| `official_product` | Product screenshots, software UI, device renders, brand assets, logos | Official site, product docs, app stores, press kits, official storefronts | URL capture / browser discovery after source-page confirmation | Generic stock | High |
| `real_person` | Executives, founders, researchers, public figures, portraits | Official bio, organization newsroom, event organizer, Wikimedia, authority media | `wikimedia` when identity is clear | Generic stock; browser as final source | High |
| `news_recent_event` | Recent event, policy, launch, incident, breaking trend | Official announcement, regulator, primary documents, authority media | Usually none for auto-final; browser discovery only | Generic stock | High |
| `data_report_capture` | Report figure, dashboard, market chart, table screenshot | Official PDF/report, data portal, company IR, institution page | URL capture after source-page confirmation | Generic stock | Medium / high |

**Default — no declared pack (may override)**: use conservative routing: `wikimedia`, `nasa`, `smithsonian`, `openverse`, then browser discovery. Do not prioritize keyed generic stock providers unless the row declares `generic_atmosphere` or `allow_generic_stock: true`.

---

## 3. Provider Applicability

| Provider | Appropriate | Not appropriate |
|---|---|---|
| Pexels | Generic atmosphere, workplace, lifestyle, abstract business scenes | Named people, IP characters, product screenshots, historical evidence, academic diagrams |
| Pixabay | Generic photos / illustrations, low-risk background support | Precise identity, specialist figures, official product imagery |
| Unsplash | High-quality mood, nature, city, editorial-feeling generic photography | Fact-critical subjects, official product renders, named entities |
| Flickr | CC photo candidates, events, places | Final use without metadata review; high-ambiguity subjects |
| Openverse | Open-license aggregation, Commons / museum / Flickr leads | Treating aggregate metadata as sufficient for all high-risk subjects |
| Wikimedia | Encyclopedic, geographic, scientific, historical, institutional subjects | Generic commercial atmosphere as a first choice |
| NASA | Space, astronomy, Earth science, NASA technology | Non-NASA domains |
| Smithsonian | History, art, culture, natural history, open collection assets | Modern products, IP characters, generic office scenes |
| Browser / Google Images | Discovering official source pages and candidate provenance | Auto-downloading final license-cleared assets for high-risk rows |

**Hard rule**: Google Images and browser search are discovery paths. They may identify source pages, official pages, and candidate pools; they do not by themselves create a license-safe final asset.

---

## 4. Discovery-Only Policy

**Mandatory**: Rows with `discovery_only: true` must preserve discovery provenance and usually end as `Needs-Manual` unless a license-cleared source page is opened and verified.

| Discovery item | Required record |
|---|---|
| Search engine | `discovery_source`, e.g. `google_images`, `bing_images`, `browser_search` |
| Query | `search_query` |
| Candidate source page | `source_page_url` |
| Download URL | `download_url` only after source page is verified |
| Risk | `copyright_risk` |
| Review | `manual_review_status` |

**Forbidden — discovery misuse**:

- Use a Google thumbnail URL as the final source
- Treat browser result metadata as a cleared license
- Use a weak search hit as an AI `reference_image` for a person, character, product, place, or event
- Drop `source_page_url` for high-risk material

---

## 5. Routing Decisions

| Subject signal | Route |
|---|---|
| Named character, IP, game, anime, official art | `anime_game_ip`; disable generic stock; discovery only; manual review |
| Named product, software UI, logo, screenshot, press render | `official_product`; official pages first; generic stock disabled |
| Real person portrait or named role | `real_person`; official bio / Wikimedia only when identity is clear; manual review |
| Scientific concept, institution, paper figure | `academic_science`; prioritize institutions / NASA / Wikimedia |
| Historical event, artifact, artwork, archive | `historical_culture`; prioritize Wikimedia / Smithsonian / archives |
| Recent event, policy, launch, trend | `news_recent_event`; authoritative source pages; manual review |
| Market chart, report figure, dashboard screenshot | `data_report_capture`; prefer native SVG redraw or URL/PDF capture |
| Office team, abstract background, city mood, lifestyle scene | `generic_atmosphere`; stock providers allowed |

**High ambiguity default**: if the row could depict the wrong person, character, product, event, artwork, place, or institution, set `needs_manual_review: true` and `copyright_risk: high`.

---

## 6. Handoff Fields

### 6.1 `design_spec.md §VIII`

**Mandatory**: Web rows in §VIII must express source routing.

| Column / field | Required for |
|---|---|
| `Source pack` | Every `Acquire Via: web` row |
| `Copyright risk` | Every `Acquire Via: web` row |
| `Selection reason` | Every `Acquire Via: web` row |
| `Manual review` | High-risk or discovery-only rows |
| `Reference` | Intent, not a provider command |

### 6.2 `image_queries.json`

**Mandatory**: Authoritative batch rows should carry routing fields while preserving legacy fields.

```json
{
  "filename": "p05_product_ui.jpg",
  "query": "ProductName official dashboard screenshot",
  "slide": "P05",
  "purpose": "product UI evidence for feature comparison",
  "orientation": "landscape",
  "status": "Pending",
  "source_pack": "official_product",
  "preferred_sources": ["official_site", "product_docs", "press_kit"],
  "preferred_providers": [],
  "disabled_providers": ["pexels", "pixabay", "unsplash"],
  "allow_generic_stock": false,
  "discovery_only": true,
  "needs_manual_review": true,
  "copyright_risk": "high",
  "selection_reason": "Specific product UI; generic stock cannot prove identity or license."
}
```

### 6.3 `image_sources.json`

**Mandatory**: Sourced and fallback records preserve routing provenance.

| Field | Required when |
|---|---|
| `source_pack` | New routed row |
| `selection_reason` | New routed row |
| `copyright_risk` | New routed row |
| `manual_review_status` | `needs_manual_review: true` |
| `discovery_source` | Browser / Google / search-engine discovery |
| `source_page_url` | Final asset source or candidate source page |

---

## 7. Validation

| Check | Required behavior |
|---|---|
| `generic_atmosphere` rows | May use Pexels / Pixabay / Unsplash / Flickr |
| IP / person / product rows | Generic stock disabled or explicitly justified as atmosphere only |
| Browser / Google rows | Mark `discovery_only: true` unless final source-page license is verified |
| High ambiguity rows | `needs_manual_review: true` |
| §VIII web rows | Include `Source pack`, `Copyright risk`, and `Selection reason` |

**Checkpoint output**:

```markdown
## ✅ Image Source Routing Complete
- [x] Every web row has a `source_pack`
- [x] Generic stock is enabled only for stock-appropriate rows
- [x] Discovery-only rows are marked and carry provenance requirements
- [x] High-risk rows have `needs_manual_review: true`
```
