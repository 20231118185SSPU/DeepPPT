# Executor Common Guidelines

> Narrative skeleton and visual aesthetic come from this deck's locked files under [`modes/`](./modes/_index.md) and [`visual-styles/`](./visual-styles/_index.md). Technical constraints are in shared-standards.md.

---

## 1. Template Adherence Rules

### 1.0 Pre-generation Batch Read

**Hard rule**: Before the first SVG page, batch-read every template SVG this deck will reference. Read once up front, never re-read during generation.

| Source list | Read path |
|---|---|
| Chosen template's `design_spec.md` (read frontmatter to detect `replication_mode`) | `templates/design_spec.md` |
| Every distinct `<basename>` in `spec_lock.md page_layouts` | `templates/<basename>.svg` |
| Every distinct chart name in `spec_lock.md page_charts` | `templates/charts/<chart_name>.svg` |
| Chart types in `design_spec.md §VII` not covered above | `templates/charts/<chart_name>.svg` |

**Default — read each template once; re-read only on the mid-deck exception below**:
- Layout SVG already loaded in this batch
- Chart SVG already loaded in this batch

`spec_lock.md` is the only file re-read per page (§2.1).

**Exception**: user mid-deck adds pages or swaps templates introducing a basename/chart absent from the original batch → read the new file once, continue.

> Note: batched prefix reads stay in the cached prompt prefix; per-page `spec_lock.md` re-reads append below and benefit from that cache. Scattered on-demand reads of layout/chart SVGs would invalidate downstream cache and sit in the compression-vulnerable mid-context region.

Resolve the per-page template SVG via `spec_lock.md page_layouts` (authoritative). The legacy page-type table below is a **last-resort fallback** for legacy decks where `page_layouts` is missing.

**Resolution order (per page):**

1. **Mirror-mode template** (template's `design_spec.md` frontmatter has `replication_mode: mirror`) → see §1.1 below. The page is consumed as a **visual reference**, not as a placeholder shell.
2. `spec_lock.md page_layouts` has `P<NN>: <basename>` for this page → inherit the structure of `templates/<basename>.svg` (already in context from §1.0).
3. `page_layouts` exists but **no entry** for this page → **free design**, no template inheritance.
4. `page_layouts` section absent (legacy deck) **and** `templates/` directory exists → fall back to the page-type table below, matching by SVG filename keyword (cover/chapter/content/ending/toc). Read the matched file at first use if §1.0 batch did not cover it.
5. No template at all → free design.

> Note: `page_layouts` disambiguates the multiple content variants modern templates ship (e.g., `graduation_defense` has 8); the legacy table cannot.

**Templates supply structure, not skin (non-mirror)**: a chart or layout template's gradients, drop-shadows, and palette are placeholder. Inherit its geometry, label / legend placement, and series-encoding logic; re-skin every fill / stroke to the deck's `visual_style` + `spec_lock.colors` — flat styles strip the gradients and shadows, gradient / glass styles repaint their own. Forbidden — shipping a template's default `<linearGradient>` / `cardShadow` / Tailwind fills unchanged. Mirror templates are the exception: §1.1 preserves their visuals verbatim.

### 1.1 Mirror-mode templates — reference-style consumption

When the project's chosen template is a `mirror` template (`design_spec.md` frontmatter declares `replication_mode: mirror`), Executor switches to a **reference-style** consumption path that bypasses placeholder substitution:

1. **Per-page reference selection** — Strategist selects one mirror page per project page via `spec_lock.md page_layouts` (e.g., `P04: 015_content`). The basename is the mirror filename without extension; Strategist made this choice by reading `design_spec.md §V Page Roster` descriptions, not by guessing.
2. **Copy, don't fill** — open the referenced mirror SVG (already in context from §1.0). **Copy it as the starting point for the project page**, then edit text elements in place to express the project's content for `P<NN>`. Preserve every non-text element verbatim: backgrounds, decorative shapes, sprite-cropped images, charts, icon usage, color values, font families, geometry, sprite `<svg viewBox>` wrappers, and **which image** each `<image>` points at.
3. **What you may edit** — the visible text content of `<text>` / `<tspan>` elements that express slide-specific content (title, body, captions, KPI labels, dates, page numbers). Replace the source deck's example text with the project's text for this page from `design_spec.md §IX` and `notes/<NN>_*.md`.
4. **What you must not touch** — element positions, sizes, fonts, colors, fills, strokes, gradients, **which image each `<image>` points at**, `<g>` grouping, sprite-sheet `<svg viewBox>` wrappers, decorative `<rect>` / `<path>` / `<circle>` / `<polygon>` shapes, `<use data-icon="...">` markers, embedded chart data structures. Mirror's value is preserving the source deck's visual identity — any geometric / decorative drift defeats the purpose. **The `href` path is not the image**: normalizing a bare `href="cover_bg.png"` to `href="../images/<name>"` (when Step 3 relocated the asset to `images/`) points at the *same* image and changes nothing visual — that is an allowed path fix, not a fidelity edit. Leaving the bare href as-is is also fine; the exporter and live preview resolve bare hrefs against `images/` either way.
5. **Content fit** — the mirror page was chosen by Strategist because its layout matches the content slot. If the project's content for `P<NN>` legitimately needs more / fewer items than the mirror page provides (e.g. mirror shows 3 KPI cards, project has 4 metrics), keep the mirror page's visual rhythm and either drop one metric to fit or split across two pages — do **not** restructure the mirror page's grid. If neither works, surface a `warning: P<NN> content does not fit mirror reference <basename>; suggest different reference page` and proceed with the closest-fit edit.
6. **No `{{}}` substitution** — mirror SVGs do not contain placeholder markers. Do not search for `{{TITLE}}` / `{{CONTENT_AREA}}` etc.; do not invent placeholders. The whole mirror contract is "verbatim source + in-place text edit".
7. **Output filename** — follow the standard project SVG naming convention (`<NN>_<page_name>.svg` where `<NN>` matches the project page index, not the mirror source index). The mirror filename is the *reference*, not the *output*.

**Detecting mirror mode**: read the chosen template's `design_spec.md` frontmatter once during §1.0 batch read. If `replication_mode: mirror`, every page that hits `page_layouts` follows §1.1 above; pages without a `page_layouts` entry still fall through to free design (resolution rule 3 above).

**Mirror + chart pages**: chart structures inside a mirror SVG are already drawn (axis, series, labels). Treat them as visual references — replace the data labels and series text content to match the project's chart spec, but do not redraw the chart from a `templates/charts/<name>.svg` baseline. A mirror template's `page_charts` entries are normally absent for this reason.

**Legacy fallback table** (used only when `page_layouts` is absent):

| Page Type | Corresponding Template | Adherence Rules |
|-----------|----------------------|-----------------|
| Cover | `01_cover.svg` | Inherit background, decorative elements, layout structure; replace placeholder content |
| Chapter | `02_chapter.svg` | Inherit numbering style, title position, decorative elements |
| Content | `03_content.svg` | Inherit header/footer styles; **content area may be freely laid out** |
| Ending | `04_ending.svg` | Inherit background, thank-you message position, contact info layout |
| TOC | `02_toc.svg` | **Optional**: Inherit TOC title, list styles |

### Page-Template Mapping Declaration (Required Output)

Before generating each page, output which template is used:

```
📝 **Template mapping**: `templates/03a_content_image_text.svg` (or "None (free design)")
🎯 **Adherence rules / layout strategy**: [specific description]
```

- **Content pages**: template defines only header/footer; content area is free
- **No template**: generate entirely per the Design Spec

### Transition Page Centering Rule

**Hard rule**: all transition pages MUST use centered text alignment.

| Element | Alignment | Position |
|---------|-----------|----------|
| Chapter number | Center, large, semi-transparent | Top-center of content area |
| Chapter title | Center, bold | Below number |
| Chapter description | Center | Below title |
| Next hook / guiding question | Center | Bottom area |
| Decorative elements | Symmetric left/right | Top and bottom corners |

**Forbidden**: left-aligned transition pages where content clusters on the left side leaving large empty space on the right. If the project uses `transition_centered` template, inherit its centered structure. For free-design transition pages, apply the same centering discipline.

### Deep-Dive Page Pairing Rule

**Hard rule**: every content page that makes a substantive, expandable claim MUST be followed by ≥1 deep-dive page.

| Content page claim type | Deep-dive layout | Content |
|-------------------------|-----------------|---------|
| Lists multiple problems/challenges | Card layout (`deepdive_card`) | One card per problem, with data/scenario |
| Describes a process/pipeline | Timeline or step layout | Step-by-step expansion with visuals |
| Compares two approaches | Side-by-side layout | Detailed comparison with evidence |
| Presents a key metric/number | Data callout layout | Context, breakdown, source |

Deep-dive page titles MUST echo or reference the preceding content page's core claim (narrative continuity).

### Screenshot Grid Rule

When comparing two or more objects (projects, approaches, before/after), prefer the `screenshot_grid` layout over pure text comparison tables.

**Screenshot source priority**:
1. Actual project SVG output (render svg_output/ page to thumbnail)
2. Exported PPTX screenshots
3. AI-generated placeholder (last resort)

Screenshots MUST be the same dimensions within each column. Grid layout MUST be symmetric (equal column widths, aligned rows).

### Image Dimension Matching Rule (图片尺寸匹配规则)

**Hard rule**: every image in the SVG MUST match its layout slot dimensions.

| Layout slot | Target dimensions | Tolerance |
|-------------|------------------|-----------|
| Full-bleed background (cover/ending/transition) | 1280×720 | ±5% |
| Content center image | 1160×425 | ±10% |
| Deep-dive side image | 370×500 | ±10% |
| Gallery thumbnail | 370×170 | ±10% |
| Screenshot grid cell | 550×162 | ±10% |

**When image and slot dimensions differ by >20%**:
1. Do NOT use `preserveAspectRatio="xMidYMid slice"` to force-fit — it crops too aggressively and produces awkward results
2. Instead, regenerate the image at the correct dimensions (use `target_width`/`target_height` in `image_prompts.json`)
3. For web-sourced images that cannot be regenerated, resize/crop manually before embedding

**Standard image sizes for common layouts** (PPT 16:9):
- Cover/ending background: 1280×720 (16:9)
- Content page hero: 1160×425 (~11:4, landscape)
- Deep-dive side: 370×500 (3:4, portrait)
- Gallery cell: 370×170 (~2:1, wide landscape)
- Grid cell: 550×162 (~10:3, ultra-wide landscape)

---

## 2. Design Parameter Confirmation (Mandatory Step)

Before the first SVG page, output a confirmation listing: canvas dimensions, body font size, color scheme (primary/secondary/accent HEX), font plan. Prevents spec/execution drift.

### 2.1a Narrative Restatement (Mandatory)

> Long decks lose narrative coherence when later pages drift from the outline's intent. This restatement mechanism pushes each page's narrative function into the highest-attention position — right before generation begins.

**Hard rule**: Before generating each SVG page, Executor MUST restate (internally or in output):

1. **Current page's narrative function** — from `detailed_outline.json` → `narrative_function` (or inferred from `design_spec.md §IX` if no detailed outline exists)
2. **Current page's core argument** — from `detailed_outline.json` → `core_argument` (or the page's key takeaway from `§IX`)
3. **Narrative bridge** — how this page connects to the previous page's ending point (one sentence)

This restatement ensures long-deck pages maintain narrative coherence even when context compression erodes earlier pages' intent. For pages without `detailed_outline.json` context, derive the restatement from `design_spec.md §IX Content` and the page's `page_rhythm` tag.

> This mechanism complements §2.1's spec_lock re-read: §2.1 ensures **visual consistency** (colors, fonts, icons), §2.1a ensures **narrative consistency** (argument flow, content coherence).

### 2.1 Per-page spec_lock re-read (Mandatory)

> Long decks drift off the declared palette/icons mid-deck due to context compression. `spec_lock.md` is the canonical execution reference — re-read it per page to bypass model memory.

**Hard rule**: Before generating **each** SVG page, `read_file <project_path>/spec_lock.md`. Use only values from this file, not from memory. If context was auto-compacted, also `read_file <project_path>/design_spec.md` for the current page's §IX brief.

**spec_lock.md has two functional layers** — read both, but treat them differently:

| Layer | Sections | How to use |
|-------|----------|------------|
| **Decision specs** (intent) | `mode`, `visual_style`, `colors`, `typography`, `decisions` | Interpret with understanding — these express *why* the design looks the way it does. The `## decisions` section contains causal chains (WHY) that explain the reasoning. When your creative judgment conflicts with a decision, follow the decision — it was locked by the human. |
| **Harness constraints** (compliance) | `canvas`, `icons`, `images`, `page_rhythm`, `page_layouts`, `page_charts`, `forbidden` | Follow mechanically — these are machine-checkable rules. Violations are deterministic errors caught by `svg_quality_checker.py` and `spec_compliance_check.py`. Do not interpret or override. |

The partition is a thinking aid, not a structural split — both live in one file for atomicity.

**Per-block expression**: render each `design_spec.md §IX Content` block in its written texture — a full-sentence block as wrapped prose, a fragment/label block as bullets/keywords. **Never split a full-sentence block into a bullet list** — splitting loses the information that the block was continuous reasoning, not a set of parallel points; not because a bullet lays out easier, and not because an inherited template slot is shaped as a list. If a block carries no clear texture, infer the mode from its wording and the page layout.

- **Prose render recipe**: one `<text>` per paragraph; wrap lines with sibling `<tspan>` that reset `x` to the block's left edge and advance `dy` by the font size × a line-height factor. **Default — line-height by density (may override per content fit)**: ~1.4–1.5× for dense / small-body blocks (CLReq comfortable minimum), 1.6–2.0× for large-type, sparse, or `breathing` blocks. Fit about width ÷ font-size CJK glyphs per line (Latin fits roughly twice that); the last line runs short. Use the body ramp size, not a new one.
- **Template precedence**: when an inherited template slot is a bullet list but the §IX block is prose, the prose wins — widen or reflow the container to hold the paragraph, or drop that card; do not pour the sentence back into the list slot.
- **Mode precedence**: the locked mode shapes voice / register, not §IX's authored titles or page order. When a `§IX` title is a user-authored topic label, keep it — do not upgrade it to an assertion just because the mode (e.g. `pyramid`) favors them; mode title-tendencies apply only to AI-drafted titles.

> Note: block-level phrasing, applied *within* the page's `page_rhythm` density (below), not against it.

**If `spec_lock.md` is missing**: emit `warning: spec_lock.md missing — generating without execution lock` once, then proceed using `design_spec.md` values. Expected only for legacy projects; new projects MUST have it (see [strategist.md](strategist.md) §6 step 4).

**Forbidden — values outside the lock**:

- Colors (fill / stroke / stop-color) MUST come from `colors`
- Icons MUST come from `icons.inventory`; library MUST equal `icons.library`
- Font family from `typography`: use role override (`title_family` / `body_family` / `emphasis_family` / `code_family`) if declared, else fall back to `font_family`
- Font sizes follow a **ramp anchored on `typography.body`**, not a closed menu. Use the declared slots when they fit. Intermediate sizes (e.g., 40px hero number, 13px annotation) are allowed if the ratio to `body` falls within the role's band (see `design_spec.md §IV ramp table`). Sizes outside every band require extending the lock first.
- Images MUST reference files listed under `images`; no invented filenames
- Formula PNGs are images with `Acquire Via: formula` / `Status: Rendered`; place them only from the listed file path and never recreate the formula as text.

If a page needs a value not in `spec_lock.md`, surface it — do not silently invent one.

**Per-page layout rhythm — `page_rhythm` section**:

Before drawing each page, look up its entry in `page_rhythm` (key format `P<NN>` matching the page index in §IX of `design_spec.md`) and apply the corresponding layout discipline:

| Tag | Layout discipline |
|-----|-------------------|
| `anchor` | Structural page (cover / chapter / TOC / ending). With a template, follow the matching template verbatim. In free design (no template), realize the page's §IX intent — for the cover deliver its `Cover impact` and for a closing page its `Closing impact` (the committed hook / takeaway + composition), never a default centered title + subtitle or a generic "Thank you" sign-off. |
| `dense` | Information-heavy. Card grids, multi-column layouts, KPI dashboards, tables, and charts are all permitted. This is the baseline behavior. |
| `breathing` | Low-density impact page. Avoid **multi-card grid layouts** — do not organize content as multiple parallel rounded containers (3-card row, 4-card KPI grid, 2×2 matrix rendered as cards). Use naked text blocks, dividers, whitespace, or full-bleed imagery as the content structure. Single rounded visual elements (hero image corners, callouts, tags, one emphasis block) are fine — the rule is about grid structure, not about the `rx` attribute. Proportions follow information weight (not a preset ratio). Typical forms: hero quote, single large number with one-line interpretation, full-bleed image with floating caption, section transition. |

> Without rhythm variation, every page defaults to card grids (the "AI-generated" look). `page_rhythm` is the only narrative lever that survives context compression.

**Missing `page_rhythm` section** → emit `warning: spec_lock.md missing page_rhythm — defaulting all pages to dense` once, fall back to `dense` for all pages.

**Tag not found for current page** → emit `warning: spec_lock.md page_rhythm tag not found for P<NN> — falling back to dense` once per deck (aggregate; do not repeat per page), fall back to `dense`. Do not invent a tag.

**Per-page template lookup — `page_layouts` section**:

Before drawing each page, look up its entry in `page_layouts` to decide which basename to inherit (the SVG itself was loaded in §1.0):

- Entry present (e.g., `P04: 03a_content_image_text`) → inherit the corresponding SVG already in context. The basename **must match** an actual file in the chosen template directory; if it doesn't, emit `warning: page_layouts P<NN> references missing file <basename>.svg — falling back to free design` and proceed.
- No entry for this page → free design, no inheritance. **Not an error** — Strategist intentionally left this page free.
- Whole section absent → see §1 fallback (legacy page-type matching).

Do **not** invent a layout entry, and do **not** assume a template just because `templates/` exists — if `page_layouts` is present but silent for this page, that silence is the instruction.

**Per-page chart reference — `page_charts` section**:

Before drawing each page, look up its entry in `page_charts` to decide which chart structure applies (the SVG itself was loaded in §1.0):

- Entry present (e.g., `P09: timeline_horizontal`) → adapt the corresponding chart SVG already in context. Apply project colors/typography/density; do not copy verbatim. Cross-reference `templates/charts/charts_index.json` for the chart's purpose summary if needed.
- No entry for this page → either no chart on this page, or a chart that didn't match any catalog template (Strategist's `no-template-match` fallback). Design the visualization from scratch using `design_spec.md §VII` for guidance.
- Whole section absent → no chart pages in this deck.

---

## 3. Execution Guidelines

- **Proximity**: group related elements with tight spacing; separate unrelated groups
- **Spec adherence**: follow color, layout, canvas format, and typography in the spec
- **Template structure**: if templates exist, inherit the visual framework
- **Main-agent ownership**: SVG generation must run in the main agent (not sub-agents) — pages share upstream context for cross-page visual continuity
- **Generation rhythm**: lock global design context first, then generate pages sequentially in one continuous context. No batched groups (e.g., 5 at a time).
- **Phased batch generation** (recommended):
  1. **Visual Construction Phase**: generate all SVG pages sequentially for visual consistency. Use layout judgment for chart marks during the draft. **MUST embed plot-area markers** per §3.1 below on every chart page — coordinate calibration is a post-generation step (see [`workflows/verify-charts.md`](../workflows/verify-charts.md)) that depends on these markers.
  2. **Quality Check Gate**: run `python3 scripts/svg_quality_checker.py <project_path>` on `svg_output/`. Any `error` (banned features, viewBox mismatch, spec_lock drift, non-PPT-safe font, etc.) MUST be fixed on the offending page before proceeding — regenerate and re-check. Address `warning`s when straightforward. Do NOT defer to after `finalize_svg.py` — finalize rewrites SVG and masks some violations.
  3. **Logic Construction Phase**: after SVGs pass the quality check, batch-generate speaker notes for narrative continuity.

### 3.1 Chart Plot-Area Marker (MANDATORY on every chart page)

> The [`verify-charts`](../workflows/verify-charts.md) workflow enumerates chart pages from `design_spec.md §VII`, then reads each page's plot-area marker to feed `svg_position_calculator.py`. Missing marker → verify-charts has to re-derive the plot area from axis lines, paying the cost on every run.

**Hard rule**: every SVG page that contains a data visualization chart includes a plot-area marker inside `<g id="chartArea">`, placed **after axis lines** and **before the first data element** (bar, line, area, point).

**Rectangular plot area** (bar / horizontal_bar / grouped_bar / stacked_bar / line / area / stacked_area / scatter / waterfall / pareto / butterfly):

```xml
<!-- chart-plot-area: x_min,y_min,x_max,y_max -->
```

**Radial charts** (pie / donut / radar):

```xml
<!-- chart-plot-area: pie | center: cx,cy | radius: r -->
<!-- chart-plot-area: donut | center: cx,cy | outer-radius: r1 | inner-radius: r2 -->
<!-- chart-plot-area: radar | center: cx,cy | radius: r -->
```

**How to determine coordinate values**:

| Value | Derivation |
|-------|------------|
| `x_min` | X coordinate of the Y-axis line (leftmost data boundary) |
| `y_min` | Y coordinate of the topmost grid line (highest data boundary) |
| `x_max` | X coordinate of the rightmost axis endpoint or grid line |
| `y_max` | Y coordinate of the X-axis baseline |
| `cx, cy` | Center point of pie/donut/radar (accounting for `transform="translate()"`) |
| `r` | Outer radius of the chart |

**Per-page verification** — after writing each chart SVG, confirm the marker exists:

```bash
grep "chart-plot-area" <project_path>/svg_output/<current_page>.svg
```

> All chart templates in `templates/charts/` include this marker as a reference. If you are drawing a chart and the marker is absent, you have a bug.
- **Technical specs**: see [shared-standards.md](shared-standards.md) for SVG/PPT constraints
- **Card containers — use the documented patterns**: when a content page needs section cards (4 quadrants, parallel aspects, capability blocks, info cards), use the patterns codified in [`templates/charts/CHART_STYLE_GUIDE.md`](../templates/charts/CHART_STYLE_GUIDE.md) §11 — half-rounded section tab (§11.1), nested card border without stroke (§11.2), card-grid skeletons (§11.3), diagonal dashed connector for cross-quadrant relationships (§11.5), ground-anchor ellipse as a non-filter depth marker (§11.6), bidirectional interaction arrows for paired protocols (§11.7). Do not reinvent the "tinted full-rounded rect + white cover-rect to hide the bottom corners" hack; it survives in older templates but breaks SVG→PPTX color editing. Reference templates: [`labeled_card.svg`](../templates/charts/labeled_card.svg), [`quadrant_text_bullets.svg`](../templates/charts/quadrant_text_bullets.svg), [`kpi_cards.svg`](../templates/charts/kpi_cards.svg), [`matrix_2x2.svg`](../templates/charts/matrix_2x2.svg), [`team_roster.svg`](../templates/charts/team_roster.svg), [`client_server_flow.svg`](../templates/charts/client_server_flow.svg).
- **Reference — prefer semantic shapes over preset stacks (not a constraint)**: when a slide needs to express "ascending / converging / breaking through / stacking" — i.e., a relationship that goes beyond a generic arrow — prefer a single custom `<polygon>` or `<path>` that encodes the semantics geometrically, rather than stacking multiple preset arrows. A converging-tip path or a podium polygon reads faster than three arrows pointing at a label. Examples of this technique appear in many imported corporate decks; see `projects/01_template_import/svg_output/slide_01.svg` shape-158 for a reference (gradient-filled inward-pointing arrow). Do not codify these as templates — they are page-specific; the rule is just "consider polygon before stacking presets."
- **Reference — visual depth through restraint (not a constraint)**: layered depth comes from rhythm (flat vs lifted, dense vs spacious), not from shadows everywhere. Shadow typically suits 2-3 genuinely floating elements per page (cards on photos, primary CTA, overlays); keep peer-grid cards, dividers, body containers flat. Reach for typography weight, spacing, accent bars, subtle tints **before** shadow. Full rules in shared-standards.md §6.

### SVG File Naming Convention

Format: `<NN>_<page_name>.svg` (two-digit number from 01; name matches the deck's language and the page title in the Design Spec).

Examples: `01_封面.svg` / `02_目录.svg` / `03_核心优势.svg`; `01_cover.svg` / `02_agenda.svg` / `03_key_benefits.svg`.

---

## 4. Icon Usage

Strategist chooses the library and inventory; Executor only implements. Library details and one-library rule: [`../templates/icons/README.md`](../templates/icons/README.md). This section defines placeholder syntax.

> **Resolution is project-first.** Strategist copied the chosen icons into `<project_path>/icons/<lib>/` (via `icon_sync.py`); `finalize_svg.py embed-icons` embeds from there, falling back to the global library per-icon. **Custom icons**: drop an `.svg` into `<project_path>/icons/<lib>/` (any `<lib>`, e.g. `custom/`) and reference it as `data-icon="<lib>/<name>"` — it embeds like any other. Reference only icons in the `spec_lock.md` inventory.

**Built-in icons — Placeholder method (recommended)**:

```xml
<!-- chunk-filled (straight-line geometry, sharp corners, structured) -->
<use data-icon="chunk-filled/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- tabler-filled (bezier-curve forms, smooth & rounded contours) -->
<use data-icon="tabler-filled/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- tabler-outline (light, line-art style — screen-only decks) -->
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- phosphor-duotone (single color + 20% backplate — soft depth without solid weight) -->
<use data-icon="phosphor-duotone/house" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- simple-icons (brand logos — used alongside the deck's primary library, only for real company/product marks) -->
<use data-icon="simple-icons/github" x="100" y="200" width="48" height="48" fill="#181717"/>

<!-- tabler-outline with thin / bold stroke (stroke-style libraries only) -->
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587" stroke-width="1.5"/>
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587" stroke-width="3"/>
```

> ⚠️ **Color**: ALWAYS use `fill="#HEX"` on `<use data-icon="...">`. NEVER use `stroke` or `fill="none"`, even for stroke-style libraries.
>
> **stroke-width** (stroke-style libraries only, currently `tabler-outline`): allowed values `{1.5, 2, 3}`. If `spec_lock.md icons.stroke_width` is declared, all placeholders MUST use that value deck-wide. Default `2` if absent (legacy). Ignored on non-stroke libraries.
>
> Icons are auto-embedded by `finalize_svg.py` — no need to run `embed_icons.py` manually.

**Searching for icons** — use terminal, zero token cost:
```bash
ls skills/ppt-master/templates/icons/chunk-filled/ | grep home
ls skills/ppt-master/templates/icons/tabler-filled/ | grep home
ls skills/ppt-master/templates/icons/tabler-outline/ | grep chart
ls skills/ppt-master/templates/icons/phosphor-duotone/ | grep house
ls skills/ppt-master/templates/icons/simple-icons/ | grep github
```

**Abstract concept → icon name** (names for `chunk-filled`; tabler libraries use their own equivalents — verify with `ls | grep`):

| Concept | chunk-filled | tabler-filled / tabler-outline |
|---------|-------|-------------------------------|
| Growth / Increase | `arrow-trend-up` | same |
| Decline / Decrease | `arrow-trend-down` | same |
| Success / Complete | `circle-checkmark` | `circle-check` |
| Warning / Risk | `triangle-exclamation` | `alert-triangle` |
| Innovation / Idea | `lightbulb` | `bulb` |
| Strategy / Goal | `target` | same |
| Efficiency / Speed | `bolt` | same |
| Collaboration / Team | `users` | same |
| Settings / Config | `cog` | `settings` |
| Security / Trust | `shield` | same |
| Money / Finance | `dollar` | `currency-dollar` |
| Time / Deadline | `clock` | same |
| Location / Region | `map-pin` | same |
| Communication | `comment` | `message` |
| Analysis / Data | `chart-bar` | same |
| Process / Flow | `arrows-rotate-clockwise` | `refresh` |
| Global / World | `globe` | `world` |
| Excellence / Award | `star` | same |
| Expand / Scale | `maximize` | same |
| Problem / Issue | `bug` | same |

> For self-evident names (home, user, file, search, arrow, etc.) — just `grep chunk-filled/` directly without consulting the table.

> ⚠️ **Icon validation**: only use icons from the Design Spec's approved inventory. Verify each via `ls | grep` before use. Mixing libraries within one deck is FORBIDDEN.

---

## 5. Visualization Reference

Chart SVGs referenced in **VII. Visualization Reference List** are loaded once via the §1.0 batch read. This section governs adaptation only.

**Hard rule**: adapt the loaded chart SVG; do not improvise from memory and do not replicate verbatim. Apply project colors, typography, content; preserve visualization type.

**Adaptation rules**:
- **Preserve**: visualization type (bar/line/pie/timeline/process/framework…) as specified
- **Adapt**: data, labels, colors (project scheme), dimensions
- **Freely adjust**: composition, axis ranges, grid, legend, spacing, decoration — as long as the chart stays accurate and readable
- **Forbidden**: changing visualization type without spec justification; omitting data points or structural elements from the outline

> Templates: `templates/charts/` (70 types). Index: `templates/charts/charts_index.json`

### 5.1 Chart Coordinate Calibration

Coordinate calibration runs as a **standalone post-generation workflow**, not inside the executor pipeline. After SVG generation completes, if the deck contains data charts, run [`workflows/verify-charts.md`](../workflows/verify-charts.md) before post-processing.

The executor's only obligation here is upstream: embed the `<!-- chart-plot-area ... -->` marker on every chart page during initial draft (§3.1). Verify-charts enumerates chart pages from `design_spec.md §VII` (authoritative deck plan) and uses the marker to feed `svg_position_calculator.py`.

> Do NOT run `svg_position_calculator.py` during the initial draft. The calculator calibrates already-generated SVGs against their declared plot areas; running it before the SVG exists has nothing to compare against.

---

## 6. Image Handling

Handle images by their status in the Design Spec's Image Resource List. Status enum and lifecycle: [`svg-image-embedding.md`](svg-image-embedding.md).

| Status | Source | Handling |
|--------|--------|----------|
| **Existing** | User-provided | Reference images directly from `../images/` directory |
| **Generated** | Generated by Image_Generator | Reference images directly from `../images/` directory |
| **Sourced** | Web-acquired by Image_Searcher | Reference from `../images/`. **Read [`image_sources.json`](image-searcher.md) to decide attribution** — see §6.1 below. |
| **Rendered** | Deterministic formula PNG | Reference from `../images/`; use `preserveAspectRatio="xMidYMid meet"` |
| **Needs-Manual** | Acquisition failed and file is absent | Use dashed border placeholder unless the expected file exists |
| **Placeholder** | Not yet prepared | Use dashed border placeholder |

**Reference syntax**: see [`svg-image-embedding.md`](svg-image-embedding.md).

**Template-bundled images**: when a template (deck / layout / brand) is applied, its bitmaps are copied into the project's `images/` alongside every other runtime image (SKILL.md Step 3). Reference them the same way — `../images/<name>` — and do **not** reproduce a template SVG's bare sibling href (e.g. `href="cover_bg.png"`): the template SVG is reference material, the rendered page lives in `svg_output/` and must point at `../images/`. Mirror templates (§1.1) are the one exception — they copy hrefs verbatim, and the exporter resolves those bare hrefs against `images/`.

**Placeholder**: Dashed border `<rect stroke-dasharray="8,4" .../>` + description text

**`no-crop` images**: when a `spec_lock.md images` entry ends with ` | no-crop`, size the container to the image's native ratio (from `analyze_images.py` or file dims) and use `preserveAspectRatio="xMidYMid meet"`. Untagged entries are croppable — default to `slice`.

**Formula images**: rows with `Acquire Via: formula` or `Type: Latex Formula` MUST be treated as no-crop even if a legacy `spec_lock.md` forgot the flag. Use the dimensions from `design_spec.md §VIII`, `analysis/image_analysis.csv`, or `images/formula_manifest.json`; do not normalize all formulas to one height unless the spec explicitly states that layout choice.

### 6.1 Inline Attribution for Sourced Images (web path)

Whenever the slide uses an image with `Status: Sourced`, look up the corresponding entry in `project/images/image_sources.json` and act on `license_tier`:

| `license_tier` | Action on this slide |
|---|---|
| `no-attribution` | Embed the `<image>` element only. **No credit element needed.** |
| `attribution-required` | Embed the `<image>` element **plus** a small inline `<text>` credit element per the visual spec in [image-searcher.md §7](./image-searcher.md). |

The credit text is **not** rendered by post-processing or export — it must be present in the SVG you produce. The shape of the credit element (size, position, color, multi-image source line, hero gradient overlay) is specified in [image-searcher.md §7](./image-searcher.md). Do not invent a different style.

Use `attribution_text` from the manifest entry as the **starting point**, then compress for the small-text constraint (drop URL, drop filename, keep "via Provider / License"). For CC0/PD images that landed in the `attribution-required` tier only because of upstream metadata quirks (rare), credits are still safe to render.

`svg_quality_checker.py` treats missing CC BY / CC BY-SA inline attribution as an **error**. Fix the offending SVG before post-processing.

**The manifest is the single source of truth for credits.** Do not duplicate license info into speaker notes or any other artifact.

---

## 7. Font Usage

Source of truth: `spec_lock.md typography`. Use `font_family` as default; override per role with `title_family` / `body_family` / `emphasis_family` / `code_family` if declared. LaTeX formulas that Strategist rendered are PNG images, not a `code_family` text role.

If `spec_lock.md` is absent, consult [`strategist.md`](strategist.md) §g — do not invent a stack.

**Hard rule**: every SVG `font-family` stack MUST end with a pre-installed family (Microsoft YaHei / SimHei / SimSun / Arial / Calibri / Segoe UI / Times New Roman / Georgia / Consolas / Courier New / Impact / Arial Black). PPTX has no runtime fallback — missing fonts degrade to Calibri.

---

## 8. Speaker Notes Generation Framework

### Task 1. Generate Complete Speaker Notes Document

After all SVG pages are finalized, enter Logic Construction Phase and write the full notes to `notes/total.md`. Batch-writing (not per-page) lets transitions plan coherently.

**Pure spoken narration**: notes are read aloud verbatim by `notes_to_audio.py` (TTS). Write only what should be spoken. No visible markers, no labeled meta-lines, no enumerated key-point lists, no duration annotations — anything you write outside the heading will be vocalized.

**Per-page structure**: `# <number>_<page_title>` heading (the `#` heading line is the only thing stripped before TTS), pages separated by `---`. Body is 2–5 natural sentences carrying the page's core message. Page-to-page transitions live inside the opening sentence as natural prose ("接下来……" / "Having framed X, let's turn to Y") — no bracketed `[过渡]` / `[Transition]` tags.

**Concrete examples** — same shape applies to any language; just write naturally in that language.

中文 deck：

```
# 02_市场格局

在明确了行业背景之后，我们来看具体的市场格局。当前线上零售集中度持续上升，前三大平台合计份额已经达到百分之六十八，腰部玩家正在被快速挤压，留给新进入者的窗口期不超过十八个月。这意味着我们的策略必须聚焦，而不是铺开。
```

英文 deck：

```
# 02_market_landscape

Having framed the industry backdrop, let's look at the actual market landscape. Online retail concentration keeps rising — the top three platforms now hold sixty-eight percent of combined share, mid-tier players are being squeezed fast, and the window for new entrants is under eighteen months. This means our strategy has to focus, not spread.
```

> 日本語 / 한국어 / 其他语言：照搬同样的结构，用对应语言自然书写即可。

**Number readability**: TTS reads digits and symbols literally. Prefer fully-spelled forms in the language being spoken when literal pronunciation would be awkward (e.g. Chinese "百分之六十八" reads better than "68%"; "1-2分钟" reads as "一减二分钟"). Plain integers and percentages in English are fine as-is.

**Common mistakes to avoid**:
- Leaving any bracketed stage marker (`[过渡]` / `[Transition]` / `[Pause]` / `[Data]` / `[Scan Room]` / `[Interactive]` / `[Benchmark]` etc.) in the text — they will be read aloud literally.
- Adding `要点：① …` / `Key points: (1) …` / `时长：2分钟` / `Duration: 2 minutes` / `Flex: …` lines — TTS will speak "要点 一 …".
- Mixing languages within one deck's notes.

### Task 2. Split Into Per-Page Note Files

Auto-split `notes/total.md` into per-page files in `notes/`.

**Naming**: match SVG names (`01_cover.svg` → `notes/01_cover.md`); `slide01.md` also supported (legacy).

---

## 9. Next Steps After Completion

> **Auto-continuation**: After Visual Construction Phase (all SVG pages) and Logic Construction Phase (all notes) are complete, the Executor proceeds directly to the post-processing pipeline.

**Post-processing & Export** (same canonical pipeline as [shared-standards.md §5](shared-standards.md)):

```bash
# 1. Split speaker notes
python3 scripts/total_md_split.py <project_path>

# 2. SVG post-processing (auto-embed icons, images, etc.)
python3 scripts/finalize_svg.py <project_path>

# 3. Export PPTX
python3 scripts/svg_to_pptx.py <project_path>
# Output (default-flow mode):
#   exports/<project_name>_<timestamp>.pptx           ← native pptx (canonical output)
#   backup/<timestamp>/svg_output/                    ← Executor SVG source backup (always written)
#
# Add --svg-snapshot to additionally emit:
#   exports/<project_name>_<timestamp>_svg.pptx      ← SVG snapshot pptx (sibling of native pptx)

---

## 10. Text Centering & Fill Rule (文字居中与铺满规则)

**Hard rule**: all text content MUST be centered within its content frame.

| Element | Alignment | Fill behavior |
|---------|-----------|---------------|
| Page titles | `text-anchor="middle"`, x = canvas center (640 for 1280-wide) | Span the full content width (60px margins) |
| Body text / cards | `text-anchor="middle"` or centered `<text>` blocks | Fill the card/area width with appropriate padding (20-30px inner padding) |
| Takeaway line | `text-anchor="middle"` | Span full content width |
| Hero numbers | `text-anchor="middle"` | Centered in their container |

**Split-layout centering (分栏布局居中公式)**: for layouts dividing the canvas into image and text regions (e.g., left-image/right-text or right-image/left-text), text MUST be centered **within its own panel**, not against the full canvas:

| Layout type | Text panel x-range (1280-wide) | Center x for `text-anchor="middle"` |
|---|---|---|
| Left-image / Right-text (3:7) | x=384 to x=1230 | x = (384 + 1230) / 2 = **807** |
| Left-image / Right-text (4:6) | x=512 to x=1230 | x = (512 + 1230) / 2 = **871** |
| Right-image / Left-text (7:3) | x=50 to x=896 | x = (50 + 896) / 2 = **473** |
| Right-image / Left-text (6:4) | x=50 to x=768 | x = (50 + 768) / 2 = **409** |
| Custom split | x=left_edge to x=right_edge | x = **(left_edge + right_edge) / 2** |

**Formula**: `text_x = (panel_left + panel_right) / 2` with `text-anchor="middle"`. For multi-line text blocks, all `<tspan>` elements use the same `x` value (the panel center), and lines wrap within the panel width minus 20-30px inner padding on each side.

**Forbidden**: using `x=640` (canvas center) for text in a split layout where the text panel does not span the full canvas — this misaligns text to one side of the panel.

**Text spacing**: text blocks within a card/area MUST use the full available width. Do NOT cluster text in a narrow column when the card is wide. Use `x` positioning to center text within each container, and use `font-size` and `dy` spacing to fill the vertical space appropriately.

**Forbidden**: text aligned to the left margin (`text-anchor="start"`) when the content area is wide and the text is short — this creates an ugly left-heavy layout. Center everything unless the layout specifically requires left alignment (e.g., timeline nodes).

## 11. Color Contrast Rule (色彩对比规则)

**Hard rule**: text color MUST provide sufficient contrast against its background.

| Background type | Text color | Examples |
|----------------|-----------|----------|
| Dark background (#0A0E1A, #0D1117, #121828) | Light text (#E8EDF5, #E6EDF3, #FFFFFF) | Dark-tech decks |
| Light background (#FFFFFF, #F5F0E6, #F8F4F0) | Dark text (#1D2430, #0D1117, #333333) | Academic/corporate decks |
| Colored card (#161B22) | Light text (#E8EDF3) | Card interiors |
| Accent background (#00D4FF, #FF6B6B) | Dark text (#0A0E1A, #FFFFFF) | Highlight badges |

**Automatic derivation**: when the project uses a dark theme (bg color lightness < 30%), ALL body text MUST be light (lightness > 70%). When the project uses a light theme (bg lightness > 70%), ALL body text MUST be dark (lightness < 30%). The spec_lock.md `text` field provides the canonical body text color — use it.

**Forbidden**: dark text on dark background or light text on light background. If a card has the same darkness as the page background, add a subtle border (`stroke` on the card `<rect>`) to create visual separation.

## 12. AI Image Type Distinction Rule (AI 生图类型区分规则)

**Hard rule**: AI image prompts MUST be classified into two distinct types, with different prompt strategies.

### Type A: Concept Images (概念图)

Used for: cover, TOC, transition, ending backgrounds.

**Prompt strategy**: describe the **atmosphere, mood, and visual metaphor**. NO text, NO data, NO specific informational content. These images are pure visual backdrop for text overlays.

**Example prompt**: "Deep space dark background, glowing cyan data streams forming abstract network topology, holographic UI elements floating in space, cinematic lighting, no text letters numbers signs watermarks"

### Type B: Informational Images (讲解配图)

Used for: deep-dive side images, data page illustrations, comparison page visuals.

**Prompt strategy**: describe **specific informational content** — diagrams, charts, data visualizations, comparison layouts, annotated illustrations. The image itself should convey information that the SVG text then enhances (not duplicates).

**Example prompt**: "Vertical infographic showing 5-step research pipeline with labeled stages, flow arrows connecting each step, data icons at each node, clean diagram style on dark background, informational visualization"

**Key distinction**: 
- Concept images = "what does it feel like?" (emotion, atmosphere)
- Informational images = "what does it show?" (data, structure, comparison)

**Forbidden**: using a concept-style prompt (atmospheric, no information) for a deep-dive page that needs to convey specific data or comparison content.

**When informational images are needed but AI cannot generate them well** (real screenshots, actual data charts, specific UI captures): use web-sourced assets instead. See Rule 13.

## 13. Dual-Track Image Enforcement Rule (双轨图片强制执行规则)

**Hard rule**: the dual-track image strategy MUST be enforced — visual pages use AI images, information pages use web-sourced assets.

| Page type | Image source | Enforcement |
|-----------|-------------|-------------|
| Cover, TOC, Transition, Ending | AI concept images | Type A prompts |
| Content (hero image) | AI concept images | Type A prompts |
| **Deep-dive, Comparison, Data, Timeline** | **Web-sourced assets** | **Playwright/curl download, NOT AI** |
| Gallery thumbnails | Real project screenshots | Render from svg_output/ |

**Enforcement in ppt-deep-research skill Step 7**:
- Step 7A (AI generation): ONLY generates images for `Acquire Via: ai` rows (cover/transition/content/ending)
- Step 7B (web assets): MUST acquire real images for ALL deep-dive/comparison/data/timeline pages
- Before Step 8 (SVG generation): verify every deep-dive page has ≥1 web-sourced image in `web_assets/`

**Web asset acquisition priority**:
1. Playwright browser capture (preferred — actual page screenshots, real UI, real charts)
2. Direct curl/wget download (fallback for static images)
3. AI informational image (last resort — Type B prompt, NOT Type A)

**Forbidden**: filling deep-dive pages with AI concept images instead of web-sourced assets. A deep-dive page showing an atmospheric AI image instead of real data/screenshots is a quality failure.

**When the topic has no obvious web sources** (e.g., fictional topics, personal projects): use AI informational images (Type B) as fallback, but the prompt MUST describe specific informational content, NOT atmospheric visuals.
```

## 14. Layout Quality Rules (版式质量规则)

**Hard rule**: every SVG page must pass these layout quality checks before moving to the next page.

### 14.1 Whitespace control
- Safe margins: left/right 50px, top/bottom 40px
- Content must fill ≥75% of the safe area for text pages, ≥85% for image+text pages
- Adjacent element gap > 40px = **whitespace violation** — reduce gap or enlarge elements
- Empty corners or dead zones are forbidden — fill with content, decorative elements, or background images

### 14.2 Font size minimums
- **Global absolute minimum**: all visible text ≥ **14px** (body, labels, data, cards — everything except footnotes)
- **Footnotes / source annotations / page numbers**: ≥ **12px** (only exception to the 14px floor)
- Deep-dive page body text: **≥ 22px** (never use 15-16px for body)
- Deep-dive page titles: **≥ 32px**
- Content page body text: **≥ 20px**
- Data page / KPI dashboard body text: **≥ 16px**
- Data page card labels: **≥ 14px**
- Explanation page (讲解页) body text: **≥ 18px**
- Line height: **1.5x–1.6x** (not default tight spacing)
- Text-to-image visual weight ratio: 1:3 to 1:4 (text must not look tiny next to a large image)

### 14.3 Centering discipline
- All text inside content boxes must be horizontally centered (`text-anchor="middle"`)
- Multi-line text blocks: left-align content, center the block within its container
- Titles: always centered on the page
- Data cards / info boxes: text centered within each card

### 14.4 Complex pages → AI-generated full images
- Relationship networks, data dashboards, complex comparison layouts: do NOT hand-draw in SVG
- Instead: generate one AI image that contains the full visual, then overlay only title + minimal annotations in SVG
- The AI image must use a character reference when depicting characters (see Rule 15)

### 14.5 Vertical Distribution Rule (垂直分布规则)

**Hard rule**: content MUST be evenly distributed across the full vertical safe area. Concentrating all content in the upper 50% while leaving the lower half empty is a layout failure.

| Canvas | Safe area (y-range) | Minimum content coverage |
|---|---|---|
| 1280×720 (PPT 16:9) | y=50 to y=680 (630px usable) | Content spans ≥ 80% of safe area height |
| 960×720 (PPT 4:3) | y=50 to y=680 | Same |

**Distribution rules**:
- Divide the safe area into **3 vertical zones**: top (y=50–260), middle (y=260–470), bottom (y=470–680)
- Each zone MUST contain ≥ **20%** of the page's total content weight (text blocks, images, cards, or decorative elements)
- A page where the bottom 40% is entirely empty background = **vertical distribution violation**
- Exception: `breathing` pages with intentional negative space (hero number, full-bleed image with floating caption) — the dominant visual element must still touch ≥ 2 zones

**Forbidden**: stacking all cards, text, and data in the top half of the canvas. If content does not fill the full height, enlarge elements, increase spacing, or add decorative fills in the lower region.

## 15. Character Consistency Rule (角色一致性规则)

**Hard rule**: any AI-generated image depicting a named character MUST include a reference image.

### 15.1 Reference image requirement
- Use `image_gen.py --reference-image <path>` for any image containing a character
- Reference images come from `projects/<name>/ref/` (collected during research phase)
- **Forbidden**: generating a character image without `--reference-image`
- If no reference image exists, search for one before generating

### 15.2 Per-image generation (no batch for character images)
- Character images MUST be generated one at a time, not via `--manifest` batch mode
- Each image gets its own tailored prompt based on the specific page layout
- Verify the generated image matches the character before proceeding

### 15.3 Size-first design
- Design the page layout FIRST → determine exact image dimensions and position
- THEN write the image prompt with matching aspect ratio and size
- Image dimensions in the prompt MUST match the `<image>` element's `width`/`height` in the SVG

## 16. Web Asset Visual Review Rule (网络素材视觉审查规则)

**Hard rule**: every web-sourced image MUST pass visual review before use.

### 16.1 Post-download review
After downloading a web image, verify:
1. Image content matches the page's topic/theme
2. If the image depicts a game/character, it is from the correct game/property
3. Image quality is sufficient (not a thumbnail, not blurry, not watermarked)

### 16.2 Rejection criteria
- Image depicts wrong game, wrong character, or unrelated content → mark as `Needs-Manual`
- Image is a generic stock photo unrelated to the specific topic → re-search with refined query
- Image has visible watermarks, text overlays, or UI elements from unrelated apps → reject

### 16.3 Review method
Use a sub-agent or visual model to evaluate each downloaded image against the page description:
- Prompt: "Does this image directly relate to '{page topic}'? Is the content from the correct game/property? Answer YES/NO with reasoning."
- Any NO → re-search or mark Needs-Manual

## 17. Visual Enrichment & Overlay Rules (视觉增强与遮罩规则)

### 17.1 Visual Enrichment Rule (P2)

**Hard rule**: data pages, explanation pages (讲解页), and timeline pages MUST NOT use flat solid-color backgrounds without decorative elements. Every such page needs at least **2 of the following 3** visual enrichment layers:

| Layer | Implementation | Examples |
|---|---|---|
| **Gradient background** | `<linearGradient>` or `<radialGradient>` on the page background `<rect>`, using project colors with subtle opacity variation | Primary→secondary_accent at 5-15% opacity shift; radial glow at 10% opacity in one corner |
| **Card shadow / depth** | Drop shadow or layered card effect on content containers | `<filter>` with `feDropShadow` (dx=0, dy=4, stdDeviation=8, opacity=0.15-0.25); or layered rects with slight offset |
| **Decorative elements** | Geometric shapes, lines, dots, or accent bars that reinforce the page's visual theme | Accent bar at card top (3-4px, primary color); corner decorative shapes; subtle dot grid pattern; divider lines between sections |

**Minimum requirements by page type**:

| Page type | Required enrichment | Forbidden |
|---|---|---|
| Data / KPI dashboard | Gradient bg + card shadow | Pure `#FFFFFF` or `#0A0E1A` flat fill with no decoration |
| Explanation / timeline | Gradient bg OR decorative shapes + card shadow | Flat solid background with plain text blocks |
| Comparison / side-by-side | Accent bar or divider between sections + card shadow | Two flat cards with no visual separation |
| Content (hero image) | Image itself is the enrichment; overlay scrim sufficient | — (image pages exempt) |
| Breathing / quote | Single decorative element (accent bar, dot, line) | — (minimal enrichment ok) |

### 17.2 Card & Container Depth Rules

**Hard rule**: cards and content containers MUST have visual depth cues. Flat cards on flat backgrounds create the "Word document" look.

| Depth technique | When to use | Specification |
|---|---|---|
| Subtle shadow | Cards that float above the background | `<filter id="cardShadow"><feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.18"/></filter>` — apply via `filter="url(#cardShadow)"` |
| Accent top-bar | Cards with section labels | `<rect>` at card top, 3-4px height, width = card width, fill = `primary` color |
| Border stroke | Cards that need separation from similar-bg parent | `stroke` = `border/divider` color from spec_lock, `stroke-width="1"` |
| Tinted background | Cards on light themes | `fill` = `secondary_bg` (slightly different from page background) |

**Shadow usage discipline** (complements shared-standards.md §6): shadow suits 2-3 genuinely floating elements per page. Peer-grid cards in a 3×2 layout should stay flat with border stroke or tint instead — shadow on every card in a grid reads as over-design.

### 17.3 Overlay / Mask Opacity Rule (P3)

**Hard rule**: when text overlays an image (content pages, cover, transitions), the overlay scrim MUST be opaque enough to guarantee text readability. The overlay is a `<rect>` covering the image area with the page's background color and an opacity value.

| Background darkness | Minimum overlay opacity | Recommended range |
|---|---|---|
| Dark image on dark theme (bg lightness < 30%) | ≥ **0.92** | 0.92–0.96 |
| Medium-contrast (mixed image, any theme) | ≥ **0.85** | 0.85–0.92 |
| Light image on light theme (bg lightness > 70%) | ≥ **0.55** | 0.55–0.70 |

**Split-layout transition zone rule**: for layouts where one half is image and the other is text (left-image/right-text etc.), the transition zone between image and text panels is where conflicts occur. The image-side scrim MUST extend **at least 60px past the panel boundary** into the text panel to prevent edge bleed. Alternatively, use a gradient scrim that fades from full opacity at the panel boundary to zero over 80-120px.

**Forbidden**: overlay opacity < 0.80 on any page where body text sits on top of the image. Opacity 0.88 was found insufficient in practice — 0.92+ is required for reliable readability across varied image content.

## §18 Animation Rhythm Enforcement

The Executor MUST produce animations that match content rhythm. The guiding principle: *shorter timing for repeated scan content, longer timing for conceptual pivots, section transitions, hero diagrams, and final takeaways*.

### §18.1 Per-Page-Type Animation Defaults

| Page type | Transition | Object animation | Notes |
|-----------|-----------|-----------------|-------|
| Cover (P01) | `fade` 0.5s | `fade` 0.6s, `after-previous` cascade | Dramatic reveal |
| TOC (P02) | `none` | `fly` 0.4s, `after-previous` stagger 0.15s | Sequential entry |
| Hook / Opening | `fade` 0.35s | `fade` 0.5s | Let content breathe |
| Content (dense) | `fade` 0.25s | `auto` 0.35s, stagger 0.12s | Fast scan rhythm |
| Content (breathing) | `fade` 0.35s | `fade` 0.5s, stagger 0.20s | Slower, conceptual |
| Deep-dive: data dashboard | `fade` 0.3s | `wipe` 0.5s, `after-previous` | Data group by group |
| Deep-dive: comparison | `fade` 0.3s | `fly` 0.4s, left+right `with-previous` | Panels enter from sides |
| Deep-dive: timeline | `fade` 0.3s | `fly` 0.35s, `after-previous` stagger 0.15s | Nodes appear sequentially |
| Deep-dive: quote | `fade` 0.4s | `fade` 0.6s | Slow, contemplative |
| Transition | `fade` 0.4s | `fade` 0.5s | Bridge moment |
| Synthesis / Summary | `fade` 0.35s | `fade` 0.5s, stagger 0.15s | Building to close |
| Ending | `fade` 0.5s | `fade` 0.6s | Final impression |

### §18.2 Forbidden Animation Patterns

- **Same animation for every page** — "animation for animation's sake". Vary by page type per §18.1.
- **Zoom / swivel / blinds / checkerboard** on content pages — these are distracting. Reserve for hero images only.
- **Duration < 0.15s** — invisible to the viewer.
- **Duration > 1.0s** — feels sluggish, wastes audience time.
- **All groups `with-previous`** — everything appearing at once has no rhythm. Use `after-previous` cascade for sequential entry.
- **No animation at all** (transition: none + animation: none on content pages) — static decks feel like documents, not presentations.

### §18.3 Key Data Emphasis Rules

| Content type | Recommended animation | Duration |
|-------------|----------------------|----------|
| KPI / single big number | `appear` or `fade` | 0.3–0.4s |
| Chart / graph | `wipe` left-to-right | 0.4–0.5s |
| Comparison table columns | `fly` from left/right | 0.35–0.45s |
| Bullet list items | `fly` top-down, stagger 0.10s | 0.30s each |
| Hero image / product shot | `zoom` or `dissolve` | 0.5–0.6s |

## §19 Visual Priority Page Rules

Pages are classified by visual impact priority. The Executor MUST adapt rendering strategy per priority level.

### §19.1 Priority Classification

| Priority | Typical pages | Rendering strategy |
|----------|--------------|-------------------|
| **HIGH** | Cover, product showcase, hero section, key data reveal | Full-bleed AI background image + semi-transparent overlay + minimal text |
| **normal** | Standard content, evidence blocks, analysis | Standard layout per template |
| **LOW** | TOC, transition, footnotes, sources | Clean and minimal; solid background acceptable |

### §19.2 HIGH Priority Page Rules

When `visual_priority: HIGH` in `spec_lock.md` page roster:

1. **Background**: MUST use an AI-generated full-bleed background image (via `image_gen.py`). The image fills the entire canvas (0,0 → canvas_width × canvas_height).
2. **Overlay**: Semi-transparent dark overlay, opacity ≥ 0.85 (per §17.3 dark-theme rules). Ensures WCAG 4.5:1 contrast for overlaid text.
3. **Text**: Maximum 60 Chinese characters (or 80 Latin words). Title ≥ 48px. No bullet lists — use a single powerful statement or number.
4. **Animation**: `fade` 0.6s for the entire page. No per-element cascade — the page is a single visual moment.
5. **Layout**: Center-aligned text on the overlay. Use the full canvas width. No split layouts, no cards, no borders.

### §19.3 LOW Priority Page Rules

When `visual_priority: LOW`:

1. **Background**: Solid color from `spec_lock.md` palette. No background image required.
2. **Text**: Standard font sizes per §14.2. Can be information-dense.
3. **Animation**: `fade` 0.25s transition, `auto` 0.30s objects. Keep it quick — these are functional pages, not showpieces.
