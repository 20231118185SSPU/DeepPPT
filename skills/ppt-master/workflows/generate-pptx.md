---
description: Generate PPTX route authority for source intake, planning, SVG authoring, quality gates, and native PPTX export (DeepPPT2).
---

# Generate PPTX Route

> Load only after [`routing.md`](./routing.md) selects Generate PPTX. This file owns the route's Step 1–8 sequence, gates, role switching, and mandatory commands. DeepPPT2's pre-pipeline flows ([`ppt-briefing.md`](./ppt-briefing.md) → [`deep-research.md`](./deep-research.md)) and its planning chain ([`content-selection.md`](./content-selection.md) → [`detailed-outline.md`](./detailed-outline.md) → [`image-text-linking.md`](./image-text-linking.md)) stay owned by this route.

**Default Core Pipeline**: `Source Document → Create Project + Dashboard → [Template] → Strategist → [Image_Generator] → Executor Live Preview → Quality Check → Post-processing → Export`

**Generate-specific execution discipline** (mirrors SKILL.md global discipline §3-9):

- The current main agent hand-writes every SVG page; never delegate page generation or run a Python, Node, or shell generator over `svg_output/` (global discipline §6-7, §9).
- SVG pages MUST be generated sequentially page by page in one continuous pass; grouped batches are forbidden (§7).
- Before generating each SVG page, re-read `<project_path>/spec_lock.md`; every color / font / icon / image comes from that file (§8).
- Gate checklists are internal verification, not user-facing output. On success, continue automatically and emit at most one compact status line; on failure, report only the blocking items and required recovery (see [`governance/failure-recovery.md`](./governance/failure-recovery.md)).

## Cross-Cutting Authorities

| Concern | Authority | Contract |
|---|---|---|
| Route selection | [`routing.md`](./routing.md) | Owns the four-route matrix and the Generate profile/stage dispatch table |
| Main pipeline sequencing | This file | Owns Step 1–8 order, gates, role switching, and mandatory commands |
| Failure recovery | [`governance/failure-recovery.md`](./governance/failure-recovery.md) | Owns stop/continue policy and resume pointers |
| Confirm UI details | [`../scripts/docs/confirm_ui.md`](../scripts/docs/confirm_ui.md) | Owns the JSON schema, launcher behavior, staged-result contract, port strategy, and chat fallback details |
| Pre-pipeline research | [`deep-research.md`](./deep-research.md) | Owns briefing → research → content-selection chain for topic-only inputs |
| Stage / profile dispatch | [`index.md`](./index.md) | Owns the full workflow index and the PPTX route boundary |

### Quick Generate Profile Short Circuit

For an explicit quick/fast, skip-strategy, or direct-SVG request, follow [`profiles/quick-generate.md`](./profiles/quick-generate.md). It runs applicable source conversion/research and project-local resource preparation, lets the current agent decide content/visual/resource details in active context, then hand-authors SVG, runs one lockless final checker, and exports the final PPTX. It skips Strategist, Confirm UI, Design Spec/lock, and the first-page gate.

**Hard rule — no implicit downgrade or page cap**: page count neither selects nor blocks quick generation. Source preparation, images, icons, formulas, and their manifests remain valid.

## Route Tooling

## Main Pipeline Scripts

| Script | Purpose |
|--------|---------|
| `${SKILL_DIR}/scripts/source_to_md/pdf_to_md.py` | PDF to Markdown |
| `${SKILL_DIR}/scripts/source_to_md/doc_to_md.py` | Documents to Markdown — native Python for DOCX/HTML/EPUB/IPYNB, pandoc fallback for legacy formats (.doc/.odt/.rtf/.tex/.rst/.org/.typ) |
| `${SKILL_DIR}/scripts/source_to_md/excel_to_md.py` | Excel workbooks to Markdown — supports .xlsx/.xlsm; legacy .xls should be resaved as .xlsx |
| `${SKILL_DIR}/scripts/source_to_md/ppt_to_md.py` | PowerPoint to Markdown |
| `${SKILL_DIR}/scripts/pptx_intake.py` | Standard PPTX intake enrichment — canvas / identity / slide geometry / tables / native chart data |
| `${SKILL_DIR}/scripts/source_to_md/web_to_md.py` | Web page to Markdown (supports WeChat via `curl_cffi`) |
| `agent-reach doctor --json` | Multi-platform content availability check (optional; when `agent-reach` is installed. Zero-config: B站/V2EX/RSS/web/YouTube) |
| `${SKILL_DIR}/scripts/project_manager.py` | Project init / validate / manage |
| `${SKILL_DIR}/scripts/icon_sync.py` | Search icon candidates and copy chosen library icons into `<project>/icons/` at selection time; missing names reported + non-zero (re-pick gate) |
| `${SKILL_DIR}/scripts/analyze_images.py` | Image analysis |
| `${SKILL_DIR}/scripts/latex_render.py` | LaTeX formula rendering (manifest-driven PNG assets) |
| `${SKILL_DIR}/scripts/image_gen.py` | AI image generation (multi-provider) |
| `${SKILL_DIR}/scripts/image_search.py` | Web image search (batch mode for deep-dive page assets) |
| `${SKILL_DIR}/scripts/research/research_gate.py` | Deep-research depth gate — run after deep-research Step 7 before sync |
| `${SKILL_DIR}/scripts/research/asset_gate.py` | Research/image asset gate — run after image acquisition before Executor |
| `${SKILL_DIR}/scripts/dashboard/server.py` | Unified read-only Dashboard — project status, artifacts, quality reports, trace, Confirm / Live Preview bridges |
| `${SKILL_DIR}/scripts/confirm_ui/server.py` | Step 4 Eight Confirmations — interactive visual confirmation page |
| `${SKILL_DIR}/scripts/confirm_ui_gate.py` | Step 4 confirmation gate — verifies recommendations/result freshness before spec writing |
| `${SKILL_DIR}/scripts/svg_quality_checker.py` | SVG quality check (XML structure, banned features, spec_lock drift) |
| `${SKILL_DIR}/scripts/rendered_layout_check.py` | Rendered visual gate — local PNG screenshots + layout heuristics + human-review blockers for visual risks |
| `${SKILL_DIR}/scripts/spec_compliance_check.py` | spec_lock semantic compliance (unused colors, missing templates, icon inventory, image usage) |
| `${SKILL_DIR}/scripts/total_md_split.py` | Speaker notes splitting |
| `${SKILL_DIR}/scripts/finalize_svg.py` | SVG post-processing (unified entry) |
| `${SKILL_DIR}/scripts/svg_to_pptx.py` | Export to PPTX |
| `${SKILL_DIR}/scripts/update_spec.py` | Propagate a `spec_lock.md` color / font_family change across all generated SVGs |
| `${SKILL_DIR}/scripts/spec_lock_digest.py` | spec_lock integrity guard — generate/verify SHA-256 digest to detect unintended modifications |
| `${SKILL_DIR}/scripts/spec_lock_validate.py` | spec_lock structural validator — required sections, data population, canvas/mode/colors sanity |
| `${SKILL_DIR}/scripts/consulting_content_lock.py` | Optional consulting sidecar — generate `analysis/slide_content_lock.json` from detailed outline / spec_lock |
| `${SKILL_DIR}/scripts/e2e_validate.py` | End-to-end pipeline validation — page count, speaker notes, image completeness, PPTX integrity |
| `${SKILL_DIR}/scripts/pptx_quality_check.py` | Optional post-export PPTX structure QA — slide size, bounds, placeholders, image-area risk, native text, font floor |
| `${SKILL_DIR}/scripts/smoke_check.py` | Script smoke check — import + CLI --help validation for all scripts |
| `${SKILL_DIR}/scripts/harness_gate.py` | Aggregated quality gate — runs spec_compliance + svg_quality + e2e in one PASS/FAIL report |
| `${SKILL_DIR}/scripts/layout_capacity_check.py` | Pre-Executor capacity estimation — flags overfull/tight pages before SVG generation |
| `${SKILL_DIR}/scripts/vision_check.py` | External vision check — delegates PNG visual review to OpenAI/Anthropic-format vision APIs when main model lacks multimodal |
| `${SKILL_DIR}/scripts/memory_manager.py` | User profile memory management (load/consolidate/show/reset) — cross-session preference persistence |
| `${SKILL_DIR}/scripts/svg_snapshot.py` | SVG content hashing, structural diff, and editable element enumeration — revision pipeline support |
| `${SKILL_DIR}/scripts/svg_patch.py` | SVG patch engine — apply localized edits to SVG pages without full regeneration |
| `${SKILL_DIR}/scripts/beautify_inventory.py` | Beautify workflow Step 4 — extract per-page content inventory from source PPTX |
| `${SKILL_DIR}/scripts/beautify_identity.py` | Beautify workflow Step 3 — extract visual identity (palette, fonts) from source PPTX |
| `${SKILL_DIR}/scripts/pptx_to_svg.py` | Convert PPTX slides to SVG (beautify Step 4.0 source vector import) |
| `${SKILL_DIR}/scripts/svg_editor/server.py` | Browser-based SVG element annotator — interactive annotation and edit of generated SVGs; used by revision-loop and live-preview |

For complete tool documentation, see `${SKILL_DIR}/scripts/README.md`.

> **Windows note**: All `python3 ...` examples in this document should be read as `python ...` on standard Windows Python installs (python.org provides `python.exe` but not `python3.exe`). If `python3` is not recognized, substitute `python` in every command below. The scripts use `sys.executable` internally where possible.
## Route Template Index

## Template Index

| Index | Path | Purpose |
|-------|------|---------|
| Layout templates | `${SKILL_DIR}/templates/layouts/layouts_index.json` | Query available page layout templates |
| Content page variants | `${SKILL_DIR}/templates/layouts/content_pages/` | Pre-built content page SVG layouts by scenario (academic / business / report). Each scenario has 6 variants; JSON sidecar describes layout type and slots. |
| Brand presets | `${SKILL_DIR}/templates/brands/brands_index.json` | Query available brand identity presets (color / typography / logo / voice) |
| Visualization templates | `${SKILL_DIR}/templates/charts/charts_index.json` | Query available visualization SVG templates (charts, infographics, diagrams, frameworks) |
| Icon library | `${SKILL_DIR}/templates/icons/` | See `${SKILL_DIR}/templates/icons/README.md`; search icons on demand with `ls templates/icons/<library>/ \| grep <keyword>` |

Discovery quality contract: every new global `layout` / `deck` template must provide `summary` and `summary_zh` in `design_spec.md` frontmatter, register those fields into the JSON index, and ship at least one root-level `.svg` preview page. Dashboard / Confirm UI depend on these fields for bilingual summaries and clickable template previews. Identity-only `brand` presets should also provide `summary_zh`; SVG logo previews are optional.
## Workflow (Steps 1-8)

## Workflow

### Step 1: Source Content Processing

🚧 **GATE**: User has provided source material (PDF / DOCX / EPUB / URL / Markdown file / text description / conversation content — any form is acceptable).

> **No source content?** When the user supplies only a topic name or requirements without any file or substantive description, run [`ppt-briefing`](ppt-briefing.md) first. It creates `ppt_brief.md` and `ppt_brief.json` in the project root and is ⛔ BLOCKING: wait for explicit user confirmation before any research. After the Brief is confirmed, run the [`deep-research`](deep-research.md) orchestrator (7-step research flow) with `ppt_brief.json` as upstream constraint, then return here with its products as input. The briefing-created project folder remains the canonical `<project_path>` for the rest of the pipeline; do not initialize a second project for the same topic-only route. Source files (PDF/DOCX/URL) also go through deep-research — the search steps are skipped only when the source already satisfies the research depth contract; analysis/narrative/visual strategy still run.
>
> **Hard rule**: Do not replace `deep-research` with the agent's built-in WebSearch. Built-in WebSearch is only a recorded fallback inside `deep-research` Step 3 after planned browser / platform / Agent-Reach search paths fail or return low-quality output.

When the user provides non-Markdown content, convert immediately:

| User Provides | Command |
|---------------|---------|
| PDF file | `python3 ${SKILL_DIR}/scripts/source_to_md/pdf_to_md.py <file>` |
| DOCX / Word / Office document | `python3 ${SKILL_DIR}/scripts/source_to_md/doc_to_md.py <file>` |
| XLSX / XLSM / Excel workbook | `python3 ${SKILL_DIR}/scripts/source_to_md/excel_to_md.py <file>` |
| CSV / TSV | Read directly as plain-text table source |
| PPTX / PowerPoint deck | `python3 ${SKILL_DIR}/scripts/source_to_md/ppt_to_md.py <file>` for Markdown content; after Step 2 `import-sources`, standard PPTX intake is also written to `<project>/analysis/` |
| EPUB / HTML / LaTeX / RST / other | `python3 ${SKILL_DIR}/scripts/source_to_md/doc_to_md.py <file>` |
| Web link | `python3 ${SKILL_DIR}/scripts/source_to_md/web_to_md.py <URL>` |
| WeChat / high-security site | `python3 ${SKILL_DIR}/scripts/source_to_md/web_to_md.py <URL>` (requires `curl_cffi`, included in `requirements.txt`) |
| Markdown | Read directly |

> **Office vector assets (EMF/WMF) from DOCX/PPTX sources**:
> `doc_to_md.py` / `ppt_to_md.py` extract embedded Office vector images (.emf/.wmf)
> alongside bitmap images. After `import-sources`, these land in `images/`
> together with `image_manifest.json` and are first-class assets in §VIII Image Resource List.
>
> **Do NOT convert EMF/WMF to PNG.** The PPT Master pipeline preserves them as external
> references (`finalize_svg.py` skips them) and `svg_to_pptx.py` embeds them as
> PPTX-native media via `image/x-emf` / `image/x-wmf` MIME — PowerPoint renders them at full vector fidelity.
> Converting via LibreOffice/Inkscape introduces CJK font substitution drift and
> rasterization loss; the original EMF/WMF is always higher fidelity than the converted PNG.
>
> Browser-based live preview cannot render EMF (will show blank) — this is expected;
> the PPTX output is the source of truth.

**✅ Checkpoint — Confirm source content is ready, proceed to Step 2.**

---

### Step 2: Project Initialization

🚧 **GATE**: Step 1 complete; source content is ready (Markdown file, user-provided text, or requirements described in conversation are all valid).

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
```

Format options: `ppt169` (default), `ppt43`, `xhs`, `story`, etc. For the full format list, see `references/canvas-formats.md`.

Import source content (choose based on the situation):

| Situation | Action |
|-----------|--------|
| Has source files (PDF/MD/etc.) | `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files...>` |
| User provided text directly in conversation | No import needed — content is already in conversation context; subsequent steps can reference it directly |

For PPTX sources, `import-sources` automatically runs the standard intake enrichment:

```bash
python3 ${SKILL_DIR}/scripts/pptx_intake.py <project_path>/sources/<source.pptx> -o <project_path>/analysis
```

For each PPTX it writes `<stem>.identity.json` (canvas, theme palette/fonts, observed usage) and `<stem>.slide_library.json` (text slots, geometry, native tables, native chart caches), and merges that deck's Strategist-facing digest into the single multi-deck index `analysis/source_profile.json` (`decks[]`, one self-contained entry per source deck, with prefixed artifact pointers). In the main generation path these are source facts and recommendation candidates, not replica constraints; beautify and template-fill workflows decide separately which fields become locked constraints.

Multi-deck: several PPTX files may be imported into one main-pipeline project — each gets its own `<stem>.*` artifacts and a deck entry in `source_profile.json`. `source_profile.json` stays the single must-read index (one entry for a one-deck project, several for a combined-source project). Stems must be distinct; re-importing the same stem replaces that deck's entry. The beautify / template-fill workflows remain single-deck (1:1 to one chosen source deck) and read that deck's `<stem>.*` artifacts.

**Import ownership policy**: leave `import-sources` unflagged by default. The script protects user originals with an asymmetric default:

| Source location / intent | Default / flag |
|--------------------------|----------------|
| User-owned files outside the repo | Default copies into `sources/`; do not add `--move` unless the user explicitly wants the originals relocated |
| Temporary or intermediate files inside the repo | Default moves into `sources/` to avoid leaving commit-prone artifacts |
| In-repo files that must remain in place | Add `--copy` |
| Disposable Step 1 intermediates that should be cleaned up | Add `--move` only for those items; if mixed with external user originals, run a separate import command |

Intermediate Markdown asset folders (e.g., `_files/`) are handled automatically with their Markdown source.

**Dashboard Auto-Launch (best-effort, non-blocking)**: after the project directory exists and sources have been imported, start or reuse the unified read-only Dashboard in the background:
```bash
python3 ${SKILL_DIR}/scripts/dashboard/server.py <project_path> --daemon
```
- The Dashboard opens at `http://127.0.0.1:<port>/`, defaulting to port `8765`; if that port is occupied, it auto-advances to the next safe port and never uses Chrome's unsafe `5060`.
- Default local behavior is to auto-open the browser. Add `--no-browser` only for headless/remote sessions or when the user explicitly asks not to pop a window.
- If a Dashboard is already running for this project, the launcher reuses the existing lock URL and does not start a duplicate service.
- Logs are written to `<project_path>/dashboard/dashboard.log`.
- Report the actual Dashboard URL, port, project path, and log path in the Step 2 checkpoint. If the browser cannot auto-open, still print the URL for the user/developer to open manually. Never rely on the default `8765` assumption in chat.
- Launch failure is non-fatal: print the warning and continue the PPT pipeline. Dashboard availability must never block Step 4 confirmation, Step 6 SVG generation, quality gates, post-processing, or export.
- Dashboard remains read-only by default. It is the unified visibility and bridge entry for service status, actual URLs/ports, logs, template previews, Confirm UI, and Live Preview. It must not auto-confirm, auto-generate, auto-export, or apply annotations; Confirm UI, Live Preview, and quality actions still require their own workflow gates and explicit user action.

**✅ Checkpoint — Confirm project structure created successfully, `sources/` contains all source files, converted materials are ready, and Dashboard URL/log path were reported (or a non-fatal launch warning was reported).**

> **Content Selection Phase (Conditional)**: if `research_report.md` exists in the project (produced by `deep-research` workflow) and `content_selection.json` does NOT yet exist, run the [`content-selection`](content-selection.md) workflow before proceeding. This interactive step parses the research report into dimensions and lets the user pick which content to include in the PPT. Skip if the user provided source files directly and skipped research — content selection applies to research-generated reports only. After content selection completes (outputs `content_selection.json`), proceed to Step 3.

> **Research-to-Generation Conditional Chain**: when `deep-research` was used, three conditional workflows execute in sequence across later steps. Each is skipped when its trigger artifact is absent (user provided source files directly):
>
> | Step | Workflow | Trigger | Output |
> |------|----------|---------|--------|
> | Step 2 | [`content-selection`](content-selection.md) | `research_report.md` exists | `content_selection.json` |
> | Step 4 | [`detailed-outline`](detailed-outline.md) | `content_selection.json` exists | `detailed_outline.json` — feeds Eight Confirmations |
> | Step 5 | [`image-text-linking`](image-text-linking.md) | `detailed_outline.json` exists | Enriches `image_prompts.json` / `image_queries.json` |

---

### Step 3: Template Option `[NEEDS_HUMAN_REVIEW]`

🚧 **GATE**: Step 2 complete; project directory structure is ready.

**Two-step confirmation.** ⛔ **BLOCKING**: After Step 2, ask the user ONE question before proceeding:

> 请选择设计方式：
> A. **自由设计** — 系统根据源文档自动设计配色、字体、版式（默认）
> B. **选择模板** — 从模板库中选择一个预设模板作为设计基础

- If user chooses **A (free design)** or does not respond → proceed directly to Step 4 as free design. Do NOT query any `*_index.json`. Do NOT proactively suggest templates.
- If user chooses **B (choose template)** → list entries from `brands_index.json` / `layouts_index.json` / `decks_index.json` with their paths. Wait for the user to provide an explicit template directory path. Then apply the template per the rules below.

**Route visibility**: every Dashboard / Confirm UI surface must describe the default as **Free design**, not as a missing or skipped error. The route is:

**Route visibility**: every Dashboard / Confirm UI surface must describe this default as **Free design**, not as a missing or skipped error. The route is:

| Route | Meaning | Evidence |
|---|---|---|
| `Free design` | No explicit template directory path was applied; Strategist designs freely from source + confirmations | No project `templates/` files |
| `Template applied` | Step 3 copied an explicit brand / layout / deck template package into `<project>/templates/` | `<project>/templates/design_spec.md` exists and declares `kind` |
| `Template expected but missing` | A template path was selected or `templates/` exists, but no valid template contract landed | `templates/` exists without a readable `design_spec.md kind` |

Template library indexes are discovery aids only. A UI may list `brands_index.json` / `layouts_index.json` / `decks_index.json`, but a user choice from that list is only a **pending Step 3 action** until the explicit path is applied and Step 4 recommendations/spec are regenerated.

**Template flow triggers ONLY on explicit directory paths** supplied by the user after the two-step confirmation. The trigger rule is mechanical, not interpretive:

| User response to Step 3 question | Step 3 action |
|---|---|
| **A (free design)** or no response | Skip Step 3, proceed to Step 4 as free design |
| **B (choose template)** → then provides explicit template directory path | Read each spec's `kind`, dispatch per the kind matrix below, fuse if multiple |
| **B (choose template)** → bare template names, style descriptions, or vague intent | List template library entries and wait for explicit path; do NOT auto-apply |

There is no slug matching, no name lookup, no fuzzy resolution. A name without a path does not trigger — the user must give a path the AI can `cd` into.

> Style descriptions ("麦肯锡风格" / "Keynote 风" / "极简风" / etc.) never trigger Step 3. They flow into Strategist's Eight Confirmations as a style brief (color / typography / tone in confirmations e–g).

> Bare names ("academic_defense", "招商银行", "anthropic") do NOT trigger Step 3 even if a matching directory exists in the library. The user must give a path. AI must not "helpfully" resolve a name to a path.

> After the user chooses "B (choose template)", list entries from `brands_index.json` / `layouts_index.json` / `decks_index.json` together with their paths. Listing alone does not advance the pipeline; the user must send a path back to trigger Step 3. If the Confirm UI records a `template_selection` with `action: "apply_template"`, stop before spec writing and rerun Step 3/4 with that path; never treat the selection as already applied.

> To create a new layout or deck, read [`create-template.md`](create-template.md). To create a new brand, read [`create-brand.md`](create-brand.md).

#### Three template kinds

The architecture has three independent reference bundles. Full schema in [`docs/zh/templates-architecture.md`](../../../docs/zh/templates-architecture.md). Summary:

| Kind | Physical dir | Contains | Frontmatter |
|---|---|---|---|
| **brand** | `templates/brands/<id>/` | identity-only segment: color / typography / logo / voice / icon style | `kind: brand` |
| **layout** | `templates/layouts/<id>/` | structure-only segment: canvas / page structure / page types / SVG roster | `kind: layout` |
| **deck** | `templates/decks/<id>/` | full replica: identity + structure + middle (template overview) segments | `kind: deck` |

**Segment ownership** (governs fusion override priority):

| Segment | Sections | Owner kind on fusion |
|---|---|---|
| Identity | Color Scheme / Typography / Logo / Voice & Tone / Icon Style | brand |
| Structure | Canvas / Page Structure / Page Types / SVG Roster | layout |
| Middle | Template Overview (use cases / design intent) | deck (no other kind writes this) |

#### Single-path dispatch

| User path's `kind` | Step 3 action |
|---|---|
| `kind: brand` | `design_spec.md` + non-image assets → `<project>/templates/`; logo / illustration / icon **bitmaps** → `<project>/images/`. Strategist locks identity segment as truth; structure stays free. |
| `kind: layout` | `design_spec.md` + SVG roster → `<project>/templates/`; any **bitmap** assets → `<project>/images/`. Strategist locks structure; identity decided in Eight Confirmations e–g. |
| `kind: deck` | `design_spec.md` + template SVGs → `<project>/templates/`; logos / backgrounds / other **bitmaps** → `<project>/images/`. Strategist locks all segments; Eight Confirmations narrows to deck-content fields (audience / page count / outline / tone tweaks). |

```bash
TEMPLATE_DIR=<user-supplied path>
# POSIX shell example (`bash`, Git Bash, WSL). In Windows PowerShell, use the
# equivalent Copy-Item / Get-ChildItem / Move-Item operations with literal paths;
# keep the same split: bitmaps to images/, non-image template assets to templates/.
# Bitmaps join the project's single runtime image pool (images/, referenced as
# ../images/); the spec + template SVGs + other non-image assets stay in
# templates/ as design reference the Strategist/Executor read but never render.
cp -r ${TEMPLATE_DIR}/* <project_path>/templates/
find <project_path>/templates -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.gif' -o -iname '*.webp' -o -iname '*.bmp' \) -exec mv {} <project_path>/images/ \;
```

The same split applies to all three kinds — bitmaps always land in `images/`, the rest in `templates/`. The spec's `kind` field tells Strategist how to read the `templates/` side; downstream code doesn't distinguish. (Template SVGs in `templates/` are reference material only — the rendered pages live in `svg_output/` and reference images via `../images/`.)

#### Multi-path fusion

When the user gives two or more paths of **different kinds**, Step 3 fuses them into a single `<project>/templates/design_spec.md`. **Default granularity is segment-level integer replacement** — entire identity / structure / middle segments are taken from the highest-priority source for that segment, no implicit field-level mixing.

Override priority by segment:

| Combination | Identity from | Structure from | Middle from |
|---|---|---|---|
| brand only | brand | (free design) | (none) |
| layout only | (free design) | layout | (none) |
| deck only | deck | deck | deck |
| brand + layout | brand | layout | (none) |
| brand + deck | brand (overrides deck) | deck | deck |
| layout + deck | deck | layout (overrides deck) | deck |
| brand + layout + deck | brand | layout | deck |

Field-level micro-adjustment (e.g. "use anthropic brand but primary changed to #FF0000") is **not** part of Step 3 fusion — it flows into Strategist Eight Confirmations e–g as a normal user request.

#### Same-kind multiple paths — conflict resolution

When the user gives two paths of the **same kind** (e.g. `brands/anthropic` + `brands/google`), Step 3 surfaces a conflict prompt before fusing — like resolving a git merge conflict:

```
AI: 你给了两个 brand，检测到段级冲突：
    - Color Scheme（Anthropic 橙红 vs Google 多色）
    - Typography（Styrene/AnthropicSans vs GoogleSans/Roboto）
    - Logo（Anthropic 标 vs Google 标）
    - Voice & Tone（restrained vs friendly）
    - Icon Style（stroke vs filled）

    要 (a) 全部按 Anthropic / (b) 全部按 Google / (c) 逐段挑？
```

Rules:
- Default: no implicit ordering — every cross-source segment difference is reported as a conflict
- Only when the user picks `(c)` does AI walk through each segment one by one
- Field-level conflicts are out of scope — segment-level only
- Three or more same-kind paths are not supported — ask the user to converge to at most two

#### Fused spec provenance

When fusion happens (any multi-path case), the resulting `<project>/templates/design_spec.md` carries a provenance block immediately under its H1:

```markdown
> **Fused from:**
> - deck: `templates/decks/招商银行/` （base）
> - brand: `templates/brands/anthropic/` （identity override）
> - layout: `templates/layouts/academic_defense/` （structure override）
> - conflicts resolved: Color Scheme from anthropic（user picked a）
```

Single-path Step 3 does **not** add provenance (the source is self-evident from the copied files).

**✅ Checkpoint — Default path proceeds to Step 4 without user interaction. If the user supplied one or more explicit template paths, those have been dispatched (or fused) into `<project_path>/templates/` before advancing.**

---

### Step 4: Strategist Phase (MANDATORY — cannot be skipped)

🚧 **GATE**: Step 3 complete; default free-design path taken, or (if triggered) template files copied into the project.

First, load any existing user profile memory (cross-session preferences):
```bash
python3 ${SKILL_DIR}/scripts/memory_manager.py load <project_path>
```
If a memory file exists, read the output and note the user's historical preferences for the detected intent. These preferences will be injected as a soft recommendation layer during the Eight Confirmations — explicit user instructions always take priority over profile memory.

Then, read the role definition:
```
Read references/strategist.md
```

> **Layout pattern selection**: when planning the page structure, check for scenarios that match reusable layout patterns — screenshot comparison grids (`screenshot_grid`), project galleries (`gallery`), deep-dive card pages (`deepdive_card`), and centered transition pages (`transition_centered`). See strategist.md §b.1 for the full selection table and hard rules. All transition pages default to centered layout. Keep a claim and its dominant evidence on one page when they remain legible and traceable; add a deep-dive only when the evidence genuinely needs a separate canvas. [NEEDS_HUMAN_REVIEW]

> **Detailed Outline (Conditional)**: if `content_selection.json` exists (from the content-selection workflow), Strategist MUST run the [`detailed-outline`](detailed-outline.md) workflow **before** the Eight Confirmations. This generates `detailed_outline.json` — a per-page plan with core arguments, content bullets, narrative functions, visual needs, evidence refs, layout slots, and content/deep-dive pairings. The detailed outline feeds into the Eight Confirmations as the content basis (page count, outline structure), into §VIII as the image acquisition basis, and into Step 5 as the image-text context source. Skip if `content_selection.json` does not exist (user provided source files directly). Its `layout_suggestion` values are per-page structure suggestions, not Step 3 template packages; users adjust them before SVG generation through `refine_spec`, not by retroactively applying a template package.
>
> **Hard rule**: When `research_report.md` exists, Strategist must not draft a thin §IX directly from memory or headings. `content_selection.json` + `detailed_outline.json` are the content contract; if they are missing or too thin, return to the relevant workflow instead of entering Eight Confirmations.

> ⚠️ **Mandatory gate**: before writing `design_spec.md`, Strategist MUST `read_file templates/design_spec_reference.md` and follow its full I–XI section structure. See `strategist.md` Section 1.

**`<project_path>/analysis/` is the project's intermediate-analysis folder: the canonical home for machine-extracted source/asset facts — the PPTX intake bundle (`source_profile.json` index + per-deck `<stem>.identity.json` / `<stem>.slide_library.json`) and `image_analysis.csv`. It holds facts, not design contracts — `design_spec.md` / `spec_lock.md` stay at the project root.** The MUST-read contract covers only the **compact structured data files (`.json` / `.csv`)**; other artifacts that may live under `analysis/` (e.g. a beautify `source_svg_import/` vector reference package) are NOT bulk-read — they are read selectively only when a specific workflow step calls for them. Before the Eight Confirmations, Strategist MUST read the auto-extracted fact files already in `analysis/` — currently `source_profile.json` (PPTX intake), when present. This file is the multi-deck index: read it once for the `decks[]` digests (canvas / chart / table entries per source deck), then open a specific deck's `<stem>.identity.json` / `<stem>.slide_library.json` only if you need its full raw facts. Use these entries as **factual source context** (format default + content facts); when several decks are present, synthesize across all of them. The source's **palette / typography / visual identity are a reference, not a constraint**: the main pipeline may inherit them where they fit the content and the confirmed style, or design fresh where they don't — the Strategist's judgment, never an obligation to either keep or discard. (Template-fill preserves the native source design by editing cloned slides directly; beautify defaults to the source identity but still follows the confirmed values; the main pipeline treats source identity as reference only and defaults to fresh design.) (`image_analysis.csv` lands later, at the image-analysis step below, and is the authoritative regenerated image-fact view there — re-derived from the live `images/` folder, not a durable store.)

**Channel ownership — read each fact once from its owning channel.** In the main pipeline the **content contract is the Markdown** (`sources/<stem>.md`): text, tables, and chart data values all come from there (`ppt_to_md` now transcribes native chart data into Markdown tables). The `analysis/` chart / table entries are a **structural digest** for outline decisions (which slides carried charts, type, series names) — not a second copy of the values; do NOT also pull chart values from `<stem>.slide_library.json` in the main pipeline. The `<stem>.slide_library.json` full structured data is owned by the direct-PPTX workflows: template-fill uses it as the native fill contract; beautify uses it for native chart / table data while keeping slide text from the Markdown.

**Eight Confirmations** (full template: `templates/design_spec_reference.md`):

⛔ **BLOCKING**: present the Eight Confirmations as a single bundled recommendation set and **wait for explicit user confirmation or modification** before outputting Design Specification & Content Outline. This is the single core confirmation point — once confirmed, all subsequent steps proceed automatically.

1. Canvas format
2. Page count range
3. Target audience
4. Style objective
5. Color scheme
6. Icon usage approach
7. Typography plan, including formula rendering policy
8. Image usage approach

**Confirm UI Auto-Launch (Mandatory — default visual confirmation surface)**: by default the Eight Confirmations are presented through an interactive local page (color swatches, live font previews, candidate picks); the chat path is the always-valid fallback. Steps:

1. Write the recommendations as **three ordered stage files** under `<project_path>/confirm_ui/` (full schema + field mapping: [`scripts/docs/confirm_ui.md`](../scripts/docs/confirm_ui.md)). The active stage file must exist before its launch/wait; skipping the write or launching without it is execution failure. To regenerate a stage, overwrite that same stage file and have the page refresh — never create revision-suffixed files, and never change an earlier confirmed stage:

   | Stage file | You author | Page returns |
   |---|---|---|
   | `recommendations.stage1.json` — **Communication contract** | `primary_language` (BCP-47 tag, **required** — the server canonicalizes it and 409s otherwise), plus free-text `audience`, `communication_intent`, `audience_outcome`, `core_message`, `delivery_context`, `artifact_afterlife`, `content_divergence` (any may be blank; blank = balanced), and `recommend.canvas` | `result.json` `stage: "stage1"`, `status: "stage1-confirmed"` |
   | `recommendations.stage2.json` — **Complete deck solution** | `design_directions` with **≥3 coordinated candidates** (each: localized `name`, `visual_style`, `icons`, 6-role `color.palette`, `typography` with CJK/Latin `heading` + `body`, `css` preview stacks, `body_size`; plus `image_strategy.rendering` when the plan may include AI), `custom_candidates` (AI-authored `mode` / `visual_style` custom behavior proposals; `image_strategy` custom when AI), optional `template_application` (required when a template is installed), `page_count`, and `recommend` for `delivery_purpose` / `mode` / `visual_style` / `icons` / `image_usage` | `result.json` `stage: "stage2"`, `status: "stage2-confirmed"` |
   | `recommendations.stage3.json` — **Production mechanics** | `recommend` for `image_ai_path` (only when the confirmed usage may include AI), `formula_policy`, `generation_mode`, `refine_spec`, plus the proactive booleans `proactive_speaker_notes` (default `true`), `proactive_custom_animations` (default `false`), `proactive_narration_audio` (default `false`) | `result.json` `stage: "final"`, `status: "confirmed"` |

   Field rules (both file kinds): **enumerable** fields (canvas / mode / visual_style / icons / formula policy / generation mode; plus image usage with a Custom path; plus AI source only when image usage may include `ai`) — the page lists common options from `confirm_ui/static/catalogs.json` (canvas synced live from `config.CANVAS_FORMATS`), so you only name the recommended canonical `id` in a `recommend` block; **generative** fields (color, typography, generated-image style) and `design_directions` — author **≥3 candidates** each (creative recommendations always offer real choice, never a single silent option — same rule as strategist h.5; fewer than 3 only on the honest-shortfall exception, with a stated reason). Color candidates carry the user-facing core `palette` (background / secondary_bg / primary / accent / secondary_accent / body_text); typography splits CJK + Latin for `heading` and `body` with `css` stacks plus `body_size` (and per-role `sizes` for title/subtitle/annotation where required); image usage uses `ai` / `web` / `provided` / `placeholder` / `none`, or a custom prose plan when several sources must be combined (never write bare `"custom"`). `content_divergence` is a **free-text** field in the contract — the user states in their own words how closely to follow the source vs how freely to reshape it (blank = balanced; facts stay sourced at every level). It is consumed by Strategist when authoring `§IX`, recorded in `design_spec.md §I`, carries no page-count coupling, and is **not** written to `spec_lock.md`. Each stage file declares `"stage": "stageN"`. Set `lang` to the page language; visible candidate text should match `lang`, or provide bilingual `name_zh` / `name_en` and `note_zh` / `note_en` fields. The server also exposes read-only `template_route` and template-library discovery data plus the `detailed_outline.json` page-plan preview; if a template is selected, `result.json.template_selection` is a pending Step 3 action and the confirm gate must block spec writing until Step 3/4 are rerun. Reuse the same candidate thinking as strategist h.5.

2. Launch the page **in the background** (the child server runs detached; `--daemon` returns as soon as the server is healthy). Then wait for the Stage-1 browser confirmation with a long tool timeout — 600000 ms — so the `--wait-only` (≈590 s budget) can complete:
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --daemon
   # Post the actual URL + Stage-1 summary/chat fallback, then wait:
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage1
   ```
   Page opens at `http://localhost:5050` — the **same port as the Step 6 live preview** (they never run at once: this page shuts down at the end of Step 4, freeing the port). If another project already holds 5050, the launcher **auto-advances to the next free port** (5051, …) and serves this project there — read the actual URL, port, project path, and `<project_path>/confirm_ui/server.log` from the launch output and report them before asking the user to use the page.

   **Three-stage confirmation flow**: the page presents the stages in order; between waits the page shows an in-browser "deriving…" state while it polls for the next stage file. After Stage 1 is confirmed, immediately re-derive the Stage-2 solution from the user's actual Stage-1 answers (design directions, color / typography / generated-image-style candidates, page count, icon / image-usage picks), write `recommendations.stage2.json` without changing Stage 1, and launch the second wait:
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage2
   ```
   After Stage 2 is confirmed, write `recommendations.stage3.json` (production mechanics only) and launch the final wait:
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only
   ```
   The page polls `/api/session` / `/api/recommendations` until the next stage payload arrives; stage-skip files (more than one stage ahead of the confirmed result) return HTTP 409 and exit code 2 — rewrite the missing stage file and re-run the wait.
   
   **Launch or wait failure is non-fatal**: if it fails or times out (flask missing, port blocked, no GUI / remote / web host, browser never confirms in time), do **NOT** troubleshoot. The detached page stays open, so a slow user may confirm after the wait returns — therefore **on any non-zero exit, re-check `<project_path>/confirm_ui/result.json` once (a fresh `status: confirmed` / `stage1-confirmed` / `stage2-confirmed` for the awaited stage) before** dropping to the chat-summary fallback below.
3. **Always also print the eight recommendations as a short summary in chat, with the actual URL, port, project path, and log path from the launch output.** This keeps the chat fallback valid whether or not the browser opened. If the page never appears, the user simply confirms or edits in chat as before. If the launch command was not attempted, do not proceed; write `recommendations.stage1.json` and launch or explicitly honor a user opt-out.
4. This is the ⛔ BLOCKING wait. Preferred page path: the `--wait-only` commands return after the page writes `<project_path>/confirm_ui/result.json` for the awaited stage; after the final wait, read that file once and use its values — proceed only when it carries `stage: "final"`, `status: "confirmed"`. On a non-zero exit, re-check `result.json` once (per step 2) — a fresh `status: confirmed` still wins. Chat fallback path: only if no fresh result exists (page didn't open, wait timed out with no confirmation, or the user replies in chat with edits) take the chat values directly and write an equivalent `<project_path>/confirm_ui/result.json` with `status: "confirmed"`, `stage: "final"`, `confirmed_at`, `fallback_confirmed: true`, and the same fields the UI would have returned. Either path converges. A confirmed `result.json` is an explicit user choice: `generation_mode: "split"` means split mode was chosen; `refine_spec: true` means the refine-spec workflow was chosen; each proactive boolean is its own choice. If `template_selection.action == "apply_template"`, stop here: apply the selected explicit path through Step 3, regenerate Step 4 recommendations, and re-confirm. Do not write `design_spec.md` from the current confirmation.
5. **Close the confirm page (Mandatory cleanup — every path).** Once you have the confirmed values (page **or** chat), shut the confirm server down before leaving Step 4 so it cannot keep holding port 5050 (which Step 6 live preview reuses):
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --shutdown
   ```
   This is **idempotent and required regardless of whether Confirm was clicked**: clicking Confirm already shuts the page down (this is then a no-op), but the chat-fallback path leaves the page running — without this cleanup it would block the live preview launch. Run it after reading the confirmation and before proceeding to Step 5.
6. **Confirm gate (Mandatory)** — before writing `design_spec.md` / `page_expression.json` / `spec_lock.md`, run:
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui_gate.py <project_path>
   # Chat fallback only, after writing fallback_confirmed result.json:
   python3 ${SKILL_DIR}/scripts/confirm_ui_gate.py <project_path> --allow-fallback
   ```
   Any FAIL means return to the Eight Confirmations step; do not write `design_spec.md`, `page_expression.json`, or `spec_lock.md` until the gate passes.

**Honoring the confirmation (result.json is authoritative — Mandatory)**: the confirmed values **override your own recommendations** when you write `design_spec.md` / `page_expression.json` / `spec_lock.md`. A user who changed any field changed it on purpose. In particular, map `image_usage` to §VIII `Acquire Via` (its value names differ from §h options — translate):

| `result.json.image_usage` | §VIII `Acquire Via` | h.5 + Step 5 generation |
|---|---|---|
| `ai` (or a custom plan that includes AI) | `ai` rows | Run h.5 (lock rendering + palette); Step 5 generates |
| `web` | `web` rows | None |
| `provided` | **`user`** rows | None — never generate |
| `placeholder` | `placeholder` rows | None |
| `none` | no image rows (§h option A) | None |

When the confirmed `image_usage` is not `ai` (and the plan has no AI part), do **NOT** run h.5, do **NOT** write `ai` rows, and do **NOT** generate images in Step 5 — regardless of what you recommended. The same "confirmed value wins" rule applies to every field (color → §III, typography → §IV, etc.).

**Opt-out**: if the user has said they don't want the page (e.g. "不要网页" / "just confirm in chat" / "纯聊天确认"), skip the launch entirely (step 2) and present the Eight Confirmations in chat as before — steps 1, 3, 4 still apply (recommendations summary in chat; wait; take chat values).

The page is a **confirmation surface only** — Strategist still authors every recommendation; the page never generates content.

**Mandatory — split-mode note** (not a ninth confirmation): after listing the eight confirmation details, you MUST append exactly one short line (rendered in the user's language, prefixed with 💡) about generation mode. Pick the variant by qualitative read of Phase A signals — recommended page count, source-material bulk, whether `deep-research` ran with substantial web-search accumulation:

| Signal read | Line content |
|---|---|
| Heavy (long page count / bulky sources / heavy web-fetch accumulation) | State estimated page count and large source size; **strongly recommend** switching to [split mode](stages/resume-execute.md) after Step 5 — stop this chat, open a fresh window and input `继续生成 projects/<project_name>` to enter Phase B (SVG generation + export); no response or "continue" = default continuous mode. **Hard warning**: continuous mode with 40+ pages risks context-compression drift and degraded SVG quality; if page count ≥ 40, print an additional ⚠️ warning before proceeding. |
| Normal (default) | State scale is moderate, default continuous mode generates in one go; if mid-way window switch is desired, input `继续生成 projects/<project_name>` after Step 5 to switch to [split mode](stages/resume-execute.md). |

This line is required output every run — the user must always see the mode choice exists. Whether to act on it is the user's call. When the Confirm UI is used, this choice also appears as the in-page generation-mode toggle and is captured in `result.json` (`generation_mode`); the chat-summary fallback still prints this line.

**Mandatory — spec-refinement note** (not a ninth confirmation): after the split-mode line, you MUST append one short opt-in line (rendered in the user's language, prefixed with 💡) telling the user they may **refine the spec first** — Strategist will produce the full design spec, then stop for review/revision of any part of it before any generation, via the [refine-spec](stages/refine-spec.md) workflow. This is where the user can inspect and adjust page count, page order, per-page `layout_suggestion` / `page_layouts`, page rhythm, chart/image strategy, color, and typography before SVG generation. Default is OFF: no request → the spec is written in one go and the pipeline auto-proceeds as usual. Only when the user explicitly asks in chat (e.g. "refine the spec first") or confirms `refine_spec: true` through Confirm UI does the [refine-spec](stages/refine-spec.md) workflow take over after the Eight Confirmations. This line, like the split-mode line, is required output every run — the user must see the choice exists; whether to act on it is theirs. When the Confirm UI is used, this choice also appears as the in-page refine-spec toggle and is captured in `result.json` (`refine_spec`); the chat-summary fallback still prints this line. Do not call this Step 8a: Step 8a Spec Review is post-export workflow learning, not pre-generation spec approval.

**Formula rendering policy lives inside item 7 (Typography plan)**:

| Policy | Behavior |
|---|---|
| `mixed` (default) | Strategist renders complex formula-worthy expressions as PNG assets; simple inline expressions remain editable text / Unicode |
| `render-all` | Strategist renders every formula-worthy expression as PNG assets |
| `text-only` | No formula rendering; formulas remain editable text / Unicode |

After the Eight Confirmations are approved and **before outputting `design_spec.md` / `spec_lock.md`**, if the confirmed formula policy is `mixed` or `render-all` and the content contains formula-worthy expressions, Strategist MUST:

1. Identify explicit LaTeX and any source expressions that should be faithfully structured as formulas.
2. Write `<project_path>/images/formula_manifest.json` with only the formulas selected for rendering.
3. Run:
   ```bash
   python3 ${SKILL_DIR}/scripts/latex_render.py <project_path>
   ```
4. Include the rendered formula PNGs as `Acquire Via: formula`, `Status: Rendered`, `Type: Latex Formula` rows in `design_spec.md §VIII Image Resource List`; also list them in `spec_lock.md images` with `| no-crop`.

The formula renderer uses a provider fallback chain by default: `codecogs,quicklatex,mathpad,wikimedia`. The first three are color-aware; Wikimedia is an availability fallback. Formula PNGs are transparent by default: manifest `background` is the temporary render matte and transparency-removal reference, not a retained final background unless `transparent: false` is set for that item. Do not scan `spec_lock.md` for `$...$` or `$$...$$`. Dollar-delimited math in source material is only a signal for Strategist; the renderer consumes the explicit manifest.

If the user provided images or formula PNGs were rendered, run analysis **before outputting the design spec**. It writes `analysis/image_analysis.csv` — the authoritative regenerated image-fact view in the `analysis/` folder, which MUST be read before authoring §VIII:
```bash
python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images
```

> 🔁 **Image facts are regenerated on demand, never a durable store.** `images/` is a live working folder — pictures are extracted from the source at import, the user may drop or replace files at any time, and Step 5 writes web/AI images into it. The single source of truth is therefore the **current contents of `images/`**, and `analysis/image_analysis.csv` is a *regenerated view* of it, not a fact to keep in sync. Re-run `analyze_images.py <project_path>/images` immediately **before any step that reads image facts** so the view reflects the live folder: before the §h image-usage recommendation (see [strategist.md](../references/strategist.md) §h), here before authoring §VIII, after Step 5 acquisition (so web/AI files join the view), and again any time the user says they added or replaced images. This is the staleness strategy — re-derive on use, no cache to invalidate.

> ⚠️ **Image handling**: NEVER directly read / open / view image files (`.jpg`, `.png`, etc.). All image info comes from `analyze_images.py` output (`analysis/image_analysis.csv`) or the Design Spec's Image Resource List.

**Output**:
- `<project_path>/design_spec.md` — human-readable design narrative
- `<project_path>/page_expression.json` — Strategist-owned per-page expression contract; Executor re-reads the current page object before every SVG
- `<project_path>/spec_lock.md` — machine-readable execution contract (skeleton: `templates/spec_lock_reference.md`); Executor re-reads before every page

**✅ Checkpoint — Phase deliverables complete, auto-proceed to next step**:
```markdown
## ✅ Strategist Phase Complete
- [x] Read the auto-extracted facts already in `analysis/` (e.g. `source_profile.json`) before the Eight Confirmations
- [x] Eight Confirmations completed (user confirmed via Confirm UI `result.json` or chat fallback)
- [x] Split-mode note appended below the eight items (heavy or normal variant)
- [x] Spec-refinement opt-in line appended (default OFF; only the user's explicit request enters the refine-spec workflow)
- [x] Design Specification & Content Outline generated
- [x] Page expression contract (page_expression.json) generated
- [x] Execution lock (spec_lock.md) generated
- [ ] **Next**: Auto-proceed to [Image_Generator / Executor] phase
```

**spec_lock integrity seal** — immediately after the checkpoint above, run:
```
python3 ${SKILL_DIR}/scripts/spec_lock_digest.py generate <project_path>
```
This seals `spec_lock.md` and, when present, `page_expression.json` so Step 6 can verify that neither machine contract was modified accidentally.

---

### Step 5: Image Acquisition Phase (Conditional)

🚧 **GATE**: Step 4 complete; Design Specification & Content Outline generated and user confirmed. Any formula rows already have `Acquire Via: formula` and `Status: Rendered`.

> **Capacity pre-check (recommended)**: Before image acquisition, run layout capacity estimation to catch text overflow risks early:
> ```bash
> python3 ${SKILL_DIR}/scripts/layout_capacity_check.py <project_path>
> ```
> Review any `overfull` pages and adjust outline content or layout before generating images. This saves token cost by preventing SVG regeneration due to overflow.

> **Trigger**: At least one row in the resource list has `Acquire Via: ai` and/or `Acquire Via: web`. If every row is `user`, `formula`, or `placeholder`, skip to Step 6.
>
> **Asset gate**: after all image acquisition and `analyze_images.py` complete, run `python3 ${SKILL_DIR}/scripts/research/asset_gate.py <project_path>` before entering Executor. Any FAIL means return to Image Acquisition / deep-research Step 7 as reported by the gate; do not generate SVG until it passes.

> **Image-Text Linking (Conditional)**: if `detailed_outline.json` exists (from the detailed-outline workflow), run the [`image-text-linking`](image-text-linking.md) workflow before generating image prompts or search queries. This ensures every AI image prompt includes the corresponding page's `core_argument` + `content_bullets` context, target slot dimensions, and text-image link; every web search keyword is extracted from `content_bullets` rather than generic topic words. Minimum AI prompt length: 80 characters. Required reference images and target dimensions must be carried into the manifest/query files. Skip if `detailed_outline.json` does not exist.

**Always load the common framework**:

```
Read references/image-base.md
```

Then **lazy-load the path-specific reference** for each row that actually needs it:

| Acquire Via | Load reference (only if any such row exists) | Run |
|---|---|---|
| `ai` | `references/image-generator.md` | `python3 ${SKILL_DIR}/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json` |
| `web` | `references/image-searcher.md` | `python3 ${SKILL_DIR}/scripts/image_search.py ...` (≥2 web rows → `--batch images/image_queries.json`) |
| `user` / `placeholder` | (skip) | (skip) |

A deck with only `ai` rows never loads `image-searcher.md`; a deck with only `web` rows never loads `image-generator.md`. A mixed deck loads both, processes each row through its own path, and writes both `image_prompts.json` and `image_sources.json`.

> ⚠️ **In-pipeline ai path MUST use manifest mode** — even when only 1 ai row exists. Write `images/image_prompts.json` first, then run `image_gen.py --manifest`, then `image_gen.py --render-md` to produce the `image_prompts.md` sidecar. The positional form (`image_gen.py "prompt" ...`) is reserved for **out-of-pipeline one-off testing / single-image fixups** — it skips manifest + sidecar, leaving no audit trail.

> ⚠️ **web path — batch multiple rows**: when ≥2 rows are `Acquire Via: web`, write all queries into `images/image_queries.json` and run `image_search.py --batch` once (concurrent acquisition, status written back), instead of one CLI call per row. A single web row may use the positional single-query form. See [image-searcher.md](../references/image-searcher.md) §5.

> ⚠️ **Honor the confirmed image source**: the `ai` generation path (Path A = `image_gen.py` API / Path B = host-native tool / Offline Manual) is **not** auto-only — a confirmed choice other than `auto` wins, whether it came from chat (canonical) or, when the page was used, `result.json.image_ai_path`. `host-native` forces Path B even when `IMAGE_BACKEND` is configured; `api` forces Path A; `manual` forces offline. The `--manifest` command above is Path A. Full selection rule: [image-generator.md](../references/image-generator.md) §7 Path Selection.

Workflow:

0. **Confirm layout-driven image dimensions** — before generating any image, verify that each row in `design_spec.md §VIII` has a `Dimensions` column filled with target pixel values derived from the SVG layout slot (see strategist.md §h.5a). Write `target_width` and `target_height` into `image_prompts.json` for each `ai` row and `min_width` / `min_height` into `image_queries.json` for each `web` row. This ensures generated or sourced images fit the SVG layout without awkward cropping or scaling.
0a. **Confirm reference-image readiness** — any AI row depicting a person, product, object, real place, character, or IP-specific subject must include `reference_image` pointing to a vetted local file or URL. Abstract concept backgrounds may omit it. Missing required references block that row until Step 3/7 visual research supplies one.
1. Extract all rows with `Status: Pending` and `Acquire Via ∈ {ai, web}` from the design spec
2. Generate prompts (ai rows) and/or run search (web rows) per [image-base.md](../references/image-base.md) §2 dispatch table
3. Verify every row reaches a terminal status: `Generated` (ai success), `Sourced` (web success), or `Needs-Manual`
4. Re-derive image facts now that web / AI files are in the folder — `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` — so `analysis/image_analysis.csv` reflects every acquired image (real measured sizes) before the Executor lays them out. Image facts are regenerated on use, never a stale store (see Step 4's image-facts note).

**✅ Checkpoint — Confirm acquisition attempted for every row**:
```markdown
## ✅ Image Acquisition Phase Complete
- [x] image_prompts.json created (when any ai rows processed)
- [x] image_prompts.md sidecar rendered (when any ai rows processed)
- [x] image_sources.json created (when any web rows processed)
- [x] Each row: status is `Generated` / `Sourced` / `Needs-Manual` (no `Pending` remaining)
- [x] AI rows with concrete subjects include vetted `reference_image` paths
- [x] AI/web rows carry layout-derived target dimensions
- [x] analyze_images.py re-run so image_analysis.csv covers the acquired web / AI images
- [x] asset_gate.py passed before Executor
```

**Default — auto-proceed to Step 6.** Only when the user's Step 4 response explicitly opted into split mode (in chat or via Confirm UI `result.json` with `generation_mode: "split"`), output the Phase A hand-off below and stop this conversation:

  ```markdown
  ## ✅ Phase A Complete
  - [x] Spec: `design_spec.md`, `page_expression.json`, `spec_lock.md`
  - [x] Resources: `sources/`, `images/`, `templates/`
  - [ ] **Next**: open a fresh chat window and input `继续生成 projects/<project_name>` to enter Phase B via the [`resume-execute`](stages/resume-execute.md) workflow.
  ```

> On acquisition failure, do NOT halt — follow the Failure Handling rule in [image-base.md](../references/image-base.md) §5: retry once, then mark the row `Needs-Manual`, report to user, and continue to the checkpoint above.

---

### Step 6: Executor Phase

🚧 **GATE**: Step 4 (and Step 5 if triggered) complete; all prerequisite deliverables are ready. If Step 5 acquired AI/web assets, `python3 ${SKILL_DIR}/scripts/research/asset_gate.py <project_path>` must pass before Executor starts.

**spec_lock integrity check (⛔ BLOCKING)** — before reading any references, verify the contract:
```
python3 ${SKILL_DIR}/scripts/spec_lock_digest.py verify <project_path>
```
Exit code 0 = integrity confirmed; exit code 2 = **MISMATCH** — `spec_lock.md` or `page_expression.json` was modified since Step 4. If mismatch, **do NOT proceed** — investigate before continuing; re-run `generate` only if the change was intentional. This is a hard gate: Executor MUST NOT start with a mismatched machine contract.

**spec_lock structural validation** — also before reading references, verify the contract has all required sections:
```
python3 ${SKILL_DIR}/scripts/spec_lock_validate.py <project_path>
```
Exit code 0 = all required sections present with data; exit code 1 = structural errors (missing sections or empty data). If errors, **do NOT proceed** — return to Strategist and fix the spec_lock before generating SVGs.

Read the execution references for this deck's locked `mode` + `visual_style` (from `spec_lock.md`):
```
Read references/executor-base.md                  # REQUIRED: common guidelines
Read references/shared-standards.md               # REQUIRED: SVG/PPT technical constraints
Read references/modes/<locked-mode>.md            # narrative skeleton (spec_lock.md `mode`)
Read references/visual-styles/<locked-style>.md   # aesthetic (spec_lock.md `visual_style`)
```

> Read executor-base + shared-standards + the one locked mode file + the one locked visual-style file. For `mode: custom` or `visual_style: custom`, skip that preset file and follow `mode_behavior` / `visual_style_behavior` from `spec_lock.md` instead. Never glob `modes/` or `visual-styles/`.

**Design Parameter Confirmation (Mandatory)**: before the first SVG, output key design parameters from the spec (canvas dimensions, color scheme, font plan, body font size). See executor-base.md §2.

**Live Preview Auto-Startup (Mandatory)**: before the first SVG, automatically start the browser editor in live mode and keep it running continuously through Executor + Step 7 export:
```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --live
```
- Start it immediately when Executor begins; `svg_output/` may be empty. Editor opens at `http://localhost:5050`; if another project already holds it, the launcher **auto-advances to the next free port** — read the actual URL, port, project path, and `<project_path>/live_preview/server.log` from the launch output and report them before generating the first SVG.
- Run it as a long-running side process/session; do not wait for it to exit before generating SVG pages. Do not wait for user confirmation after startup.
- **Service must keep running** until one of: (a) the user clicks **Exit preview** in the browser, or (b) the user explicitly asks in chat to stop it. Generation continues even if the user closes the editor.
- **Do NOT read or apply submitted annotations during generation.** Users may annotate at any time, but Executor proceeds without touching them. The window to apply annotations opens only after Step 7 completes — see [`stages/live-preview.md`](stages/live-preview.md).
- The editor also supports **staged direct edits** (text content + SVG element attributes previewed immediately, then written to `svg_output/` only when the user clicks **Apply changes**; `Ctrl+Z` / Undo drops staged edits) alongside annotation; re-export stays chat-driven. Full scope and editor details: see [`stages/live-preview.md`](stages/live-preview.md) Notes.

**Pre-generation Batch Read (Mandatory)**: before the first SVG, batch-read every distinct layout SVG referenced in `spec_lock.page_layouts` and every distinct chart SVG referenced in `spec_lock.page_charts` (plus any §VII backup charts). One read per file, up front — do not re-read these during page generation. See executor-base.md §1.0.

> Image facts: trust the `analysis/image_analysis.csv` regenerated at the end of Step 5. If `images/` changed since (the user swapped or added files), re-run `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` before laying images out — facts are re-derived on use, never a stale store (Step 4 image-facts note).

**Per-page contract re-read (Mandatory)**: before **each** SVG page, `read_file <project_path>/spec_lock.md` and the current page object from `<project_path>/page_expression.json`. Use only the lock's colors / fonts / icons / images, plus its per-page `page_rhythm` / `page_layouts` / `page_charts` lookups (resolves to template SVGs already loaded in the batch read above), and render the page-expression assertion/evidence/bridge contract. Resists context-compression drift on long decks. See executor-base.md §2.1.

> ⚠️ **Main-agent only**: SVG generation MUST stay in the current main agent — page design depends on full upstream context. Do NOT delegate to sub-agents.
> ⚠️ **Generation rhythm**: generate pages sequentially, one at a time, in the same continuous context. Do NOT batch (e.g., 5 per group).
> ⚠️ **Needs-Manual dependency check**: if Step 5 left any `Needs-Manual` image row and the planned SVG layout depends on that file, pause before authoring the dependent SVG and wait for the user to place the file in `project/images/<filename>`. The Step 7 image readiness gate is only a final fallback for unresolved manual assets, not the normal time to discover a broken dependency.

**Visual Construction Phase**: generate SVG pages sequentially, one at a time, in one continuous pass → `<project_path>/svg_output/`

**Quality Check Gate (Mandatory)** — after all SVGs, BEFORE annotation handling and speaker notes:

> **Canonical auto-gate sequence (run before presenting to user)**: Static gates MUST pass first; rendered visual gate or an explicit human visual confirmation is also required before export. Run exactly these four commands, in this order:
> If any fails, fix before presenting to user.
> 1. `python3 ${SKILL_DIR}/scripts/spec_compliance_check.py <project_path>`
> 2. `python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path>`
> 3. `python3 ${SKILL_DIR}/scripts/harness_gate.py <project_path> --quick`
> 4. `python3 ${SKILL_DIR}/scripts/rendered_layout_check.py <project_path> --render`
>
> **Why steps 1–2 before step 3?** Steps 1–2 provide granular per-script error output for debugging; step 3 (harness) re-runs the same checks internally but produces the unified PASS/FAIL report and dashboard trace. The redundancy is intentional — steps 1–2 are for the developer, step 3 is for the pipeline.

- **svg_quality_checker**: XML structure, banned features, viewBox, spec_lock drift (undeclared colors/fonts/sizes).
- **spec_compliance_check**: semantic compliance — unused declared colors, missing templates, icon inventory, image usage. Complements the structural checker with inverse-direction validation.
- **harness_gate --quick**: aggregated static shortcut — spec compliance + SVG quality; e2e is skipped.
- **rendered_layout_check**: local screenshot/geometry gate — catches collision, text-line contact, abnormal whitespace, and revision-regression confirmation needs that static checks cannot prove. With `--render`, screenshots are written to `<project_path>/quality/screenshots/` and listed in `quality/rendered_visual_gate.json`; inspect those PNGs before accepting `needs_human_review` items. [NEEDS_HUMAN_REVIEW]
- Any `error` (banned SVG features, viewBox mismatch, spec_lock drift, missing templates, etc.) MUST be fixed before proceeding — return to Visual Construction, regenerate that page, re-run check.
- `warning` entries (low-res image, non-PPT-safe font tail, unused declared color, etc.): fix when straightforward, otherwise acknowledge and release.
- Run against `svg_output/` (not after `finalize_svg.py` — finalize rewrites SVG and masks violations).
- **Script pass is not visual pass**: `svg_quality_checker.py`, `spec_compliance_check.py`, and `harness_gate.py --quick` passing only proves static/script compliance. A deck is not visually cleared until `rendered_layout_check.py` passes cleanly or records `needs_human_review` items that a human explicitly accepts from the rendered screenshots.

**Logic Construction Phase**: generate speaker notes → `<project_path>/notes/total.md`

**✅ Checkpoint — Confirm all SVGs and notes are fully generated and quality-checked, then complete the chart / visual-review interlocks below before Step 7 post-processing**:
```markdown
## ✅ Executor Phase Complete
- [x] Live preview started and kept available at the reported URL
- [x] All SVGs generated to svg_output/
- [x] svg_quality_checker.py passed (0 errors)
- [x] spec_compliance_check.py passed (0 errors)
- [x] rendered_layout_check.py passed or human visual confirmation recorded
- [x] Speaker notes generated at notes/total.md
```

> **Chart pages?** If this deck contains data charts (bar / line / pie / radar / etc.), run the standalone [`verify-charts`](stages/verify-charts.md) workflow before Step 7 to calibrate coordinates. AI models routinely introduce 10–50 px errors when mapping data to pixel positions; verify-charts eliminates that class of error. Skip if no chart pages.

> **Visual self-check (recommended — default on)**: After static gates and the rendered visual gate pass or have explicit human confirmation, run the [`visual-review`](stages/visual-review.md) workflow to catch higher-level visual issues (hierarchy, rhythm, collision) that structural checks cannot detect. Skip only when the user explicitly says "跳过视觉自检" / "skip visual review", or when `skip_visual_review: true` is set in confirm_ui result.json. [NEEDS_HUMAN_REVIEW]

> **Batch-review mode (opt-in)?** When the user requests batch-by-batch generation ("分批审阅" / "batch review" / "逐批确认"), follow [`batch-review.md`](batch-review.md). Executor pauses every N pages to collect visual feedback; later batches absorb style corrections from earlier ones. Never auto-activate — default pipeline runs straight-through. [NEEDS_HUMAN_REVIEW]

---

### Step 7: Post-processing & Export

🚧 **GATE**: Step 6 complete; all SVGs generated to `svg_output/`; speaker notes `notes/total.md` generated.

🚧 **Image readiness GATE** (when Step 5 left ai rows in `Needs-Manual`): every expected file must exist at `project/images/<filename>` before running 7.1.

> If files are missing: PAUSE, list the missing filenames, point the user to `images/image_prompts.md` (each `### Image N:` block is paste-ready for ChatGPT / Gemini / Midjourney; auto-generated from `image_prompts.json`) and the required placement `project/images/<filename>`. Resume Step 7.1 only after all expected files are in place. `finalize_svg.py` and `svg_to_pptx.py` do not detect missing files at this layer — proceeding with gaps produces a deck with broken image references.

> ⚠️ Run the three sub-steps **one at a time** — each must complete successfully before the next.
> ❌ **NEVER** combine them into a single code block or shell invocation.

Canonical three-command pipeline (mirrors `references/shared-standards.md` §5):

**Step 7.1** — Split speaker notes:
```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Step 7.2** — SVG post-processing (icon embedding / image crop & embed / text flattening / rounded rect to path):
```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
```

> `finalize_svg.py` defaults to `--layout-mode suggest`: layout overflow
> detection reports suggestions without shrinking text or rewriting layout.
> Use `--layout-mode auto-fix` only when you explicitly want the legacy font-size
> shrink behavior after reviewing rendered screenshots. [NEEDS_HUMAN_REVIEW]

**Step 7.3** — Export PPTX (embeds speaker notes by default):
```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>
# Output (default-flow mode):
#   exports/<project_name>_<timestamp>.pptx           ← native pptx (canonical output, reads svg_output/)
#   backup/<timestamp>/svg_output/                    ← Executor SVG source backup (always written)
#
# Add --svg-snapshot to additionally emit the SVG-image preview pptx alongside the native pptx:
#   exports/<project_name>_<timestamp>_svg.pptx      ← SVG preview pptx (reads svg_final/)
```

> The native pptx consumes `svg_output/` directly so the converter can preserve
> high-fidelity primitives (icon `<use>` placeholders, image `preserveAspectRatio`
> → `srcRect`, rounded rect `rx/ry` → `prstGeom roundRect`). The `svg_output/`
> snapshot in `backup/<timestamp>/` is always written so the project can be
> re-exported from frozen SVG sources without re-running the LLM. The SVG-rendered
> preview pptx is opt-in via `--svg-snapshot` — live preview already provides the
> SVG visual reference, so it's only needed when you want a self-contained file
> to share. Pass `-s output` or `-s final` to force a single source if you need it.

> **Last-mile native edits (opt-in, OfficeCLI)**: after Step 7 export, ordinary
> content/layout rework still goes back through the SVG pipeline. Only when the
> user *explicitly* asks for a last-mile native edit on the exported PPTX
> (text/color/position of specific objects, preserving native format) do you
> enter the shared [`native-revision`](stages/native-revision.md) child — never
> automatically. Such a revision is a derivative: it records `svg_divergence`
> and does not write back to `svg_output/`.

> **Paragraph editability vs line fidelity** — by default, mergeable dy-stacked
> paragraph blocks collapse into one editable PowerPoint text frame with multiple
> `<a:p>`, improving body-text editing and resize/reflow behavior. Add `--no-merge`
> only when the user explicitly asks for strict line-layout fidelity or when a
> layout-tight page must keep every dy-stacked line as its own text frame. The
> merge detector is conservative; mixed-layout text falls back to per-line frames.

**Optional animation flags** (page transitions are on by default; per-element entrance is off by default — turn it on only when the user asks for it):
- `-t <effect>` — page transition. Default `fade`. Options: `fade` / `push` / `wipe` / `split` / `strips` / `cover` / `random` / `none`.
- `-a <effect>` — per-element entrance animation. **Default `none`** — pages appear as a whole, no auto-firing element builds (the unsolicited cascade reads as the "AI deck" tell). Opt in with `auto` (map effect from group id: chart→wipe, card-/step-/pillar-→fly, title/takeaway→fade; image-like ids `hero` / `figure-` / `image` / `img-` / `kpi` cycle a richer pool — zoom / dissolve / circle / box / diamond / wheel — so multiple images vary across the deck), a specific effect like `fade`, or `mixed` for the legacy 16-effect cycle. Requires top-level `<g id="...">` groups (already required by Executor).
- `--animation-trigger {on-click,with-previous,after-previous}` — Start mode (matches PowerPoint's animation-pane Start dropdown). Default `after-previous` (click-free cascade; pace via `--animation-stagger`). Use `on-click` for presenter-paced reveals, or `with-previous` for all-at-once.
- `--animation-config <path>` — optional object-level sidecar. Default: `<project_path>/animations.json` when present.
- `--auto-advance <seconds>` — kiosk-style auto-play.

**Optional custom animations** (only when the user asks to tune animation order/effects/timing for specific objects):

Run the standalone [`customize-animations`](stages/customize-animations.md) workflow. Default export applies page transitions but no per-element entrance animation; create `animations.json` (or pass `-a auto`) only when the user asks for element animation or object-level customization.

**Optional recorded narration** (only when the user asks for narrated/video export):

Run the standalone [`generate-audio`](stages/generate-audio.md) workflow. The AI picks a narration backend (`edge` by default, or a configured cloud provider such as ElevenLabs / MiniMax / Qwen / CosyVoice for high-quality or cloned voices), asks the user once (backend + voice + rate/settings + embed-or-not, all with recommended values), then executes `notes_to_audio.py` and (if chosen) re-exports the PPTX with `--recorded-narration audio`.

Do NOT call `notes_to_audio.py` directly without going through the workflow — `--voice` / `--voice-id` is required and the workflow produces the locale/provider-aware recommendation that makes the choice meaningful.

Full effect list, anchor logic, and limits: [`references/animations.md`](../references/animations.md).

> ❌ **NEVER** substitute `cp` for `finalize_svg.py` — finalize performs multiple critical processing steps
> ❌ **NEVER** force `-s output` for the legacy/preview pptx (PowerPoint's internal SVG parser drops icons and rounded corners). The default auto-split already gives native the high-fidelity source it needs without touching legacy.
> ❌ **NEVER** use `--only` (it suppresses one of the two output files)

> **Post-export annotation window**: the preview service from Step 6 typically remains running after export. If the user submitted annotations in the browser (during Executor or after export) and now asks to apply them — they may quote the browser prompt (`Changes saved to svg_output...` / `修改已保存到 svg_output...`), say "apply my annotations" / "应用注解" / equivalent — run [`live-preview`](stages/live-preview.md) Step 2 to apply and re-export. Annotations submitted during generation are also handled here, not earlier.

> **Direct edits in the browser**: the user may also stage text / SVG attribute edits in the preview. These land in `svg_output/` only after the user clicks **Apply changes**. If they ask to "re-export" / "重新导出" after applying such edits, just re-run Step 7.2–7.3 (finalize + export); no annotation-application step is needed unless they also saved AI-needed annotations.

> **Preview not running?** Any time the user mentions "live preview", "preview", "看效果", or wants to select/click a slide element and the service is not running, run [`live-preview`](stages/live-preview.md) Step 1 to start it. If the service is already running, just point them at the URL — do not restart.

**Step 7.4** — Post-export validation (recommended):
```bash
python3 ${SKILL_DIR}/scripts/e2e_validate.py <project_path> --pptx exports/<exported_file>.pptx
```
Validates page count consistency, speaker notes completeness, image file presence, and PPTX structural integrity. Reports PASS/WARN/FAIL per check. Non-blocking — warnings and failures are informational, not gating.

**Step 7.4b** — Optional strict PPTX structure QA:
```bash
python3 ${SKILL_DIR}/scripts/pptx_quality_check.py <project_path>/exports/<exported_file>.pptx --json-out <project_path>/quality/pptx_quality.json
```
Checks the exported PPTX package directly via ZIP/XML: slide size / aspect ratio, negative or out-of-bounds shapes, placeholder text, large/full-slide image risk, native text shape count, and minimum font size. Exit code 0 = no errors, 1 = quality errors, 2 = argument/input/package error. This complements SVG/spec/render gates; it does not replace `svg_quality_checker.py`, `spec_compliance_check.py`, `rendered_layout_check.py`, or `e2e_validate.py`.

**Step 7.5** — Memory consolidation (automatic, no user action needed):
```bash
python3 ${SKILL_DIR}/scripts/memory_manager.py consolidate <project_path>
```
This reads the Eight Confirmations choices from `confirm_ui/result.json` and updates the user profile memory with stability-weighted preferences. Stable signals (confirmed across multiple jobs) are written back to `memory/user_profiles.json`; transient one-off choices are filtered out. The next PPT generation for the same intent will automatically pick up these preferences.

---

### Step 8a: Spec Review (Recommended)

> After delivery, review which decisions should be permanently locked into spec or workflow rules. Guiding principle: "Will this recur in future generations?" If yes → update spec/workflow. If one-off → skip. Spec thickness = your refusal to repeat decisions.

**Recommended — not BLOCKING**: this step is advisory. Run it when the user asks for a post-generation review, or when you notice a pattern of repeated corrections.

Steps:
1. Which user corrections were principle-level (not one-off)?
2. Which design decisions should be locked into spec_lock?
3. Which workflow rules need updating?

Use [`docs/spec-review-template.md`](../../../docs/spec-review-template.md) as the structured template. For each decision, ask: "Will this recur in future generations?" If yes → update spec/workflow. If one-off → skip.

> Also see [`docs/change-log.md`](../../../docs/change-log.md) for tracking all workflow/script modifications.
