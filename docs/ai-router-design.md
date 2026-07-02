# AI Supervisor Router Design

> Draft design for a top-level AI routing layer. `AGENTS.md`, `skills/ppt-master/SKILL.md`, and the individual files in `skills/ppt-master/workflows/` remain authoritative. This document is a proposed dispatch and supervision layer; it must not override an existing workflow rule by itself.

---

## 1. Current Routing Diagnosis

DeepPPT already has strong individual workflows, but the entry behavior is distributed across `AGENTS.md`, `SKILL.md`, `docs/routing.md`, and many workflow files. That creates these practical failure modes for AI agents:

| Problem | Impact |
|---|---|
| Route selection is scattered | The agent may choose the generic main pipeline when a standalone workflow should own the task |
| PPTX input has multiple meanings | Template fill, beautify, main-pipeline restructuring, and template creation can be confused |
| Quality gates are local to workflows | The final deck may skip chart calibration, visual review, post-export validation, or annotation handling |
| Blocking points are easy to miss | Topic brief confirmation, research outline/search-plan confirmation, Eight Confirmations, batch approval, and refine-spec approval require hard stops |
| Optional workflows are not consistently surfaced | Split mode, refine-spec, live preview, visual review, and audio export may appear as disconnected features |
| Failure recovery is workflow-specific | Agents lack a uniform policy for missing artifacts, failed gates, stale preview services, and manual image fallbacks |

**Observed rule gaps to align later**:

| Area | Current source | Observation |
|---|---|---|
| Topic-only routing | `AGENTS.md`, `SKILL.md`, `ppt-briefing.md`, `docs/routing.md` | The authoritative path is `ppt-briefing` -> user confirmation -> `deep-research`; `docs/routing.md` compresses this and can read as if `deep-research` is the first entry. |
| Batch review activation | `SKILL.md`, `batch-review.md` | `SKILL.md` says batch review is opt-in by user request; `batch-review.md` also lists "long deck + quality emphasis" as a trigger. Treat this as a recommendation to surface, not an automatic route, until reconciled. |
| Visual review concurrency | `visual-review.md`, `SKILL.md` | Visual review may use review subagents after SVG generation. This does not violate the "no sub-agent SVG generation" rule, but the boundary should be explicit. |

---

## 2. Design Goals And Non-Goals

**Goals**:

| Goal | Router behavior |
|---|---|
| Make the first route correct | Classify user intent before any project work starts |
| Preserve workflow authority | Dispatch to the owning workflow instead of copying its implementation |
| Enforce completion discipline | Track gates, blocking points, quality checks, export, validation, and hand-back |
| Reduce unnecessary clarification | Ask only when routing would otherwise be unsafe or ambiguous |
| Standardize failure handling | Convert missing state, failed gates, and unsupported requests into consistent next actions |
| Keep route state visible | Maintain a compact route state: selected workflow, project path, current phase, blockers, next gate |

**Non-goals**:

| Non-goal | Boundary |
|---|---|
| Replace `SKILL.md` | `SKILL.md` remains the execution authority for the main SVG pipeline |
| Rewrite workflows | The router links to workflows and defines hand-off contracts only |
| Implement a code orchestrator now | CLI/script automation is a future step, not part of this draft |
| Add hidden automatic choices | Existing explicit-path, confirmation, and opt-in rules stay intact |
| Treat all workflows equally | High-frequency and high-risk paths get detailed routing; low-frequency paths stay as extension routes |

---

## 3. Supervisor / Workflow Architecture

The router acts like a supervisor. It owns intent classification, route selection, gate supervision, and recovery. Each workflow acts like a specialist that owns its procedure.

```text
User request
  -> Supervisor Router
      -> classify intent and inputs
      -> choose route or ask one clarification
      -> create route state
      -> hand off to workflow owner
      -> monitor gates / blocking points / artifacts
      -> run required post-workflow quality steps
      -> export / validate / report
```

**Supervisor responsibilities**:

| Responsibility | Output |
|---|---|
| Intent classification | `route_type`, confidence, ambiguous axes |
| Input inventory | Files, URLs, topic, existing project path, template path, brand asset, user constraints |
| Workflow dispatch | One primary workflow plus conditional satellite workflows |
| Gate supervision | Required artifacts, hard stops, quality checks, validation receipts |
| Exception handling | Retry, fallback, ask user, or stop with missing artifact list |
| Completion audit | Evidence that route exit criteria were met |

**Specialist workflow responsibilities**:

| Workflow type | Owns |
|---|---|
| Main pipeline | Source conversion, project setup, Eight Confirmations, spec, images, SVG generation, export |
| `ppt-briefing` | Topic-only creative brief and confirmation |
| `deep-research` | Research plan, search, consolidation, analysis, narrative, visual strategy |
| `template-fill-pptx` | Direct PPTX cloning and text/table/chart replacement |
| `beautify-pptx` | 1:1 content-faithful re-layout through SVG pipeline |
| `resume-execute` | Phase B execution from existing Phase A artifacts |
| `refine-spec` | Opt-in spec review and revision before image/SVG work |
| `create-brand` | Brand library package creation |
| `verify-charts` | Data-chart coordinate calibration before post-processing |
| `visual-review` | Rendered visual self-check after Executor and before export |
| `live-preview` | Preview re-entry and post-export annotation application |

---

## 4. User Intent Classification

The router should classify intent by both artifacts and verbs. Artifacts often matter more than wording.

| Class | Primary signals | Default route |
|---|---|---|
| Topic-only deck | Topic, goal, or one-line requirement; no file, URL, long text, or substantive source | `ppt-briefing` -> confirmed `deep-research` -> main pipeline |
| Source-material deck | PDF, DOCX, URL, Markdown, XLSX, substantive chat text | Main pipeline Step 1 |
| Existing PPTX as source | PPTX and user wants a new story, merge/split/drop/reorder, or page count can change | `ppt_to_md` + main pipeline |
| Existing PPTX as template | PPTX plus new content/topic; user wants original design reused or filled | `template-fill-pptx` |
| Existing PPTX to beautify | PPTX plus "beautify/re-layout"; preserve wording, page count, and order | `beautify-pptx` |
| Existing project continuation | `projects/<x>` plus continue/resume wording | `resume-execute` |
| Pre-generation spec review | Explicit "review/refine spec before generation" | `refine-spec` after Eight Confirmations |
| Brand setup | Logo, brand site, branded PPTX/PDF, or "set up brand" | `create-brand` |
| Brand application | Explicit brand directory path in initial generation request | Main pipeline Step 3 template/brand application |
| Chart-sensitive deck | Data charts in spec/SVG | `verify-charts` between Executor and post-processing |
| Visual QA | Default after Executor gates unless skipped | `visual-review` |
| Preview / select / annotate | User says preview, live preview, see effect, click/select element | `live-preview` or Step 6 live auto-start |
| Post-generation revision | User asks to modify generated pages | `revision-loop` or `live-preview` annotation path |
| Narration / video | User asks for voiceover, narrated PPT, video export | `generate-audio` after post-processing |
| Object animation | User asks reveal order/effects/timing | `customize-animations` after SVG/PPTX context exists |
| Template library creation | User wants reusable template, not one-off deck | `create-template` |

---

## 5. Routing Decision Tree

```text
Start
  |
  |-- Does the user name an existing project path and ask to continue?
  |     -> resume-execute
  |
  |-- Does the user ask for preview, element selection, or annotation application?
  |     -> live-preview
  |
  |-- Does the user ask to create/update a reusable brand?
  |     -> create-brand
  |
  |-- Does the user ask to create/update a reusable template?
  |     -> create-template
  |
  |-- Is there an existing PPTX?
  |     |
  |     |-- New content/topic should be filled into the PPTX design?
  |     |     -> template-fill-pptx
  |     |
  |     |-- Same page count/order and wording must be preserved?
  |     |     -> beautify-pptx
  |     |
  |     |-- Page count/order may change, or story should be re-architected?
  |     |     -> ppt_to_md + main pipeline
  |     |
  |     |-- Ambiguous "make it better/professional"?
  |           -> ask the PPTX boundary question once
  |
  |-- Is there only a topic or thin prompt?
  |     -> ppt-briefing -> user confirmation -> deep-research -> main pipeline
  |
  |-- Is there source material or substantive chat content?
  |     -> main pipeline Step 1
  |
  |-- Is the request post-export narration, animation, or revision?
        -> extension workflow after checking required project artifacts
```

**PPTX boundary question**:

> Should the original page count/order and each slide's wording be preserved, or should the PPTX be treated as source material and restructured into a new story?

| Answer | Route |
|---|---|
| Preserve page count/order/wording | `beautify-pptx` |
| Reuse design with new content | `template-fill-pptx` |
| Restructure story or change page count/order | Main pipeline |

---

## 6. Routing Decision Table

| User request shape | Required inputs | Route | Blocking points | Exit evidence |
|---|---|---|---|---|
| "Make a PPT about X" | Topic only | `ppt-briefing` -> `deep-research` -> main | Brief confirmation; research outline/search plan; Eight Confirmations | Exported PPTX plus validation |
| "Make PPT from this PDF/DOCX/URL" | Source file/URL | Main pipeline | Eight Confirmations | Exported PPTX plus validation |
| "Use this PPT template and fill it with this content" | PPTX + content/topic | `template-fill-pptx` | Ask for source material if topic lacks facts | Filled PPTX, read-back validation |
| "Beautify this PPT, content unchanged" | PPTX | `beautify-pptx` | Beautify plan confirmation | Native PPTX, 1:1 page count, text/data fidelity |
| "Continue projects/x" | Project path | `resume-execute` | Stop if Phase A artifacts missing | SVGs/export produced from existing project |
| "Let me review the spec first" | Any generation route | `refine-spec` satellite | Spec approval before image/SVG work | Approved synchronized `design_spec.md` + `spec_lock.md` |
| "Extract brand from this logo/site/deck" | Brand asset or verbal brand spec | `create-brand` | Ask update/replace/new id if brand exists | `templates/brands/<id>/design_spec.md` registered |
| "Use this brand path" | Explicit brand directory path | Main Step 3 | Same-kind template conflict prompt if needed | Brand copied/fused into project templates |
| Deck includes data charts | Generated SVGs | `verify-charts` | Manual verify for unsupported chart geometry | Per-page chart receipt |
| Generated deck before export | SVGs + rendered screenshots | `visual-review` | User decision for `needs_human` items | Clean review table or accepted issues |
| "Preview / see effect / click element" | Project path or active project | `live-preview` | None for start; export gate for annotation apply | URL or applied annotations + re-export |

---

## 7. Priority Pipeline Contracts

This section defines entry, exit, gates, and fallback. It intentionally does not restate each workflow's steps.

### 7.1 Topic-Only PPT

| Contract | Rule |
|---|---|
| Entry | User gives only topic, direction, keywords, or thin requirements |
| Route | `ppt-briefing` -> explicit user confirmation -> `deep-research` -> main pipeline |
| Exit | Native PPTX exported, validated, and project artifacts remain in one canonical project folder |
| Quality gates | Brief confirmation; research depth contract; `research_gate.py`; content selection when `research_report.md` exists; Eight Confirmations; image asset gate; Executor static/render gates; `verify-charts` if needed; `visual-review` unless skipped; Step 7 export validation |
| Fallback | If user refuses research or provides source material later, reclassify as source-material deck. If research fails, return to the exact research step reported by the gate. |

### 7.2 Source-Material PPT

| Contract | Rule |
|---|---|
| Entry | User provides PDF, DOCX, URL, Markdown, XLSX, PPTX-as-source, or substantive chat content |
| Route | Main pipeline Step 1; source files may still enter `deep-research` when quality/depth requires it |
| Exit | Exported native PPTX plus `e2e_validate.py` result |
| Quality gates | Source conversion success; project validation; Dashboard best-effort launch; Eight Confirmations; `confirm_ui_gate.py`; optional `refine-spec`; image acquisition terminal statuses; asset gate; Executor gates; visual review; post-export validation |
| Fallback | If conversion fails, report exact source and converter. If source facts are too thin, use targeted `deep-research` rather than inventing content. |

### 7.3 Template Fill

| Contract | Rule |
|---|---|
| Entry | Existing PPTX is a design/template library; user wants new content filled into it |
| Route | `template-fill-pptx` only |
| Exit | New PPTX in `<project>/exports/`, generated by direct OOXML fill |
| Quality gates | PPTX intake; page-to-layout rationale; `fill_plan.json`; `check-plan`; `apply`; read-back via `ppt_to_md.py` |
| Fallback | If content is only a topic without facts, ask for source material or run a research-backed content path before fill. If no source slide fits a target message, choose fewer/repeated slides or ask whether to switch to main pipeline. |
| Forbidden | Do not enter SVG generation, `finalize_svg.py`, or `svg_to_pptx.py` for this route |

### 7.4 Beautify Existing PPTX

| Contract | Rule |
|---|---|
| Entry | Existing PPTX should keep page count, page order, text strings, and data values 1:1 |
| Route | `beautify-pptx` |
| Exit | New native PPTX generated through SVG pipeline; source wording/data fidelity validated |
| Quality gates | Canvas match; PPTX intake; identity and inventory extraction; layout analysis; beautify plan confirmation; full Confirm UI seeded from source; standard Executor gates; `verify-charts` if chart pages exist; `visual-review`; read-back validation |
| Fallback | If user wants to split/merge/drop/reorder or rewrite content, switch to main pipeline. If a crowded page cannot be made readable 1:1, flag the v1 ceiling and ask whether to accept or re-route. |

### 7.5 Resume Execute

| Contract | Rule |
|---|---|
| Entry | User names `projects/<x>` and asks to continue/resume |
| Route | `resume-execute` |
| Exit | Phase B completes: SVGs, notes, export, validation |
| Quality gates | `spec_lock.md`, `design_spec.md`, required `images/`, required `templates/`; Step 6/7 gates from `SKILL.md` |
| Fallback | If Phase A artifacts are missing, stop and list missing files. Do not silently restart Phase A. |

### 7.6 Refine Spec

| Contract | Rule |
|---|---|
| Entry | User explicitly asks to review/refine/revise the full spec before generation, or confirms `refine_spec: true` |
| Route | Satellite workflow after Eight Confirmations and before image/SVG work |
| Exit | User explicitly approves synchronized `design_spec.md` and `spec_lock.md` |
| Quality gates | No image acquisition or Executor entry until approval; every approved change lands in both files |
| Fallback | If spec and lock diverge, treat `spec_lock.md` as execution truth and reconcile before continuing |

### 7.7 Brand Creation And Application

| Contract | Rule |
|---|---|
| Entry: creation | User asks to set up/extract a brand or provides brand asset for future use |
| Route: creation | `create-brand` |
| Exit: creation | Brand package saved under `skills/ppt-master/templates/brands/<id>/` and indexed |
| Entry: application | User supplies an explicit brand directory path in a generation request |
| Route: application | Main pipeline Step 3 template path dispatch/fusion |
| Quality gates | Do not overwrite existing brand without update/replace/new-id decision; bare brand names are discovery only |
| Fallback | If user only mentions a brand style for one deck without a path, treat it as a style brief in Eight Confirmations, not brand application |

### 7.8 Chart Verification

| Contract | Rule |
|---|---|
| Entry | Deck has data-driven chart geometry and SVG generation has completed |
| Route | `verify-charts` before Step 7 post-processing |
| Exit | Receipt line count equals chart page count from `design_spec.md §VII` |
| Quality gates | Use authoritative chart list from spec; pass calculator or manual verification per page; rerun SVG quality checker after edits |
| Fallback | If §VII is absent, report that authoritative enumeration is unavailable. Do not guess silently from SVG contents. |

### 7.9 Visual Review

| Contract | Rule |
|---|---|
| Entry | Executor complete; static gates pass; rendered layout gate has current screenshots |
| Route | `visual-review` by default unless user explicitly skips or `skip_visual_review: true` |
| Exit | Review aggregate is clean, fixed, or user-accepted for `needs_human` items |
| Quality gates | Vision capability check; rendered PNG sanity; no edits outside SVG pages under review |
| Fallback | If no vision path exists, record `vision_available: false` and require manual review before export |

### 7.10 Live Preview And Modifications

| Contract | Rule |
|---|---|
| Entry | User asks to preview, select/click an element, or apply browser annotations |
| Route | `live-preview` unless Step 6 already has live preview running |
| Exit | Preview URL reported, or annotations/direct edits applied and deck re-exported |
| Quality gates | Annotation application requires at least one exported PPTX; direct browser edits require re-export via chat |
| Fallback | If preview is already running, report the URL and do not restart. If annotations exist before export, finish Step 7 first. |

---

## 8. Clarification Strategy

Ask one bundled question only when routing would otherwise be unsafe. Prefer conservative defaults when the answer can be inferred from artifacts and explicit verbs.

| Ambiguity | Clarifying question |
|---|---|
| Existing PPTX, vague "optimize/make professional" | Preserve original page count/order and wording, or restructure into a new story? |
| PPTX plus new content but unclear whether design or content is source | Should this deck provide the design template, or should its content be reworked into a new deck? |
| Topic-only but user expects factual claims | Do you want me to create and confirm a brief first, then research before generation? |
| Brand mention without path | Is this a one-off style preference, or do you want to create/use a brand package path? |
| Template/brand same-kind conflict | Which package wins by segment, or should the user reduce to one? |
| Missing source facts for template fill | Please provide source material, or confirm that research should be performed before filling the template. |
| Object animation request before SVG exists | Should I first complete generation, then tune animations on the generated object IDs? |

**Do not ask**:

| Case | Default |
|---|---|
| No template path | Free design |
| No refine-spec request | Auto-proceed after Eight Confirmations |
| No batch-review request | Default continuous Executor |
| No per-element animation request | Page transitions only; no element builds |
| Visual review not skipped | Run recommended visual review |

---

## 9. Multi-Route Priority Rules

When signals conflict, route by the highest-priority rule that applies.

| Priority | Rule |
|---:|---|
| 1 | Existing project resume beats new generation if user says continue/resume and names `projects/<x>` |
| 2 | Direct post-generation operations beat new routing when user asks preview, annotations, re-export, revision, animation, or audio on an existing project |
| 3 | Explicit standalone workflow intent beats generic PPT creation (`create-brand`, `create-template`, `template-fill`, `beautify`) |
| 4 | PPTX role boundary decides among template-fill, beautify, and main pipeline |
| 5 | Topic-only must go through `ppt-briefing` before `deep-research` |
| 6 | Explicit template/brand directory path triggers Step 3; bare names do not |
| 7 | `refine-spec` and batch review are opt-in satellites, not primary routes |
| 8 | Quality satellites run by artifact condition: charts -> `verify-charts`; Executor complete -> `visual-review`; preview request -> `live-preview` |

**Conflict handling examples**:

| User says | Router decision |
|---|---|
| "Beautify this PPT and split crowded pages" | Main pipeline, because page count changes |
| "Fill this template but rewrite the whole story" | Ask whether design reuse or story restructuring is primary |
| "Use Anthropic brand" with no path | Treat as style guidance; do not apply brand package |
| "Continue projects/x and review spec first" | If Phase A is complete, resume Phase B; refine-spec is too late unless user wants to reopen spec intentionally |
| "Preview and apply annotations" before export | Start preview if needed; delay annotation application until Step 7 output exists |

---

## 10. Integration Suggestions

**With `AGENTS.md`**:

| Suggestion | Status |
|---|---|
| Add a short "Supervisor Router" pointer to this document | Future, non-authoritative |
| Keep `SKILL.md` as the execution authority | Required |
| Clarify topic-only path as `ppt-briefing` first | Should become authoritative |

**With `SKILL.md`**:

| Suggestion | Status |
|---|---|
| Add a compact route preflight before Step 1 | Future |
| Keep detailed execution steps where they are | Required |
| Add a small route-state checklist to checkpoints | Future |
| Clarify batch-review activation relative to opt-in language | Should be reconciled |

**With `workflows/`**:

| Suggestion | Status |
|---|---|
| Add a common "Entry / Exit / Gates / Fallback" header to high-risk workflows | Future |
| Avoid duplicating global routing prose in every workflow | Recommended |
| Keep standalone workflows independently runnable from a fresh chat where documented | Required |

**With `docs/routing.md`**:

| Suggestion | Status |
|---|---|
| Keep it as the compact quick reference | Recommended |
| Align topic-only row with `ppt-briefing` -> `deep-research` | Should be updated later |
| Link this document as the supervisor-level design | Future |

---

## 11. Rules Suitable For Future Authority

These rules are good candidates to move upward into `AGENTS.md` or `SKILL.md` after review:

| Candidate rule | Suggested authority |
|---|---|
| Supervisor preflight must classify PPTX role before any PPTX route | `AGENTS.md` or `SKILL.md` |
| Topic-only always starts with `ppt-briefing`, not `deep-research` directly | `AGENTS.md` and `docs/routing.md` alignment |
| A route state must track project path, selected workflow, current phase, blockers, and next gate | `SKILL.md` |
| Template-fill, beautify, and main-pipeline PPTX boundaries should be stated as one shared table | `AGENTS.md` / `docs/routing.md` |
| Chart verification is conditionally mandatory before Step 7 for data-driven chart geometry | `SKILL.md` already mostly covers; can be made more explicit |
| Visual review is default unless explicit opt-out; it is not SVG generation delegation | `SKILL.md` / `visual-review.md` |
| Batch review requires explicit opt-in unless the project decides to promote "long deck + quality emphasis" to an authority rule | Needs decision |

---

## 12. Automation Opportunities

The router can be automated incrementally without building a full orchestrator first.

| Automation | Purpose |
|---|---|
| `route_intent.py` | Inspect user-supplied paths and classify likely route; emit confidence and required clarification |
| `project_state.py` | Read a project folder and report phase, missing artifacts, running dashboard/preview URLs |
| `gate_audit.py` | Aggregate required gates for the selected route and show pass/fail/missing |
| `pptx_role_linter.py` | Detect ambiguous PPTX prompts and force the boundary question |
| `research_readiness_check.py` | Verify `ppt_brief`, research artifacts, `research_gate`, sync outputs |
| `phase_b_ready.py` | Validate `resume-execute` prerequisites |
| `chart_route_check.py` | Detect data-driven chart pages from `design_spec.md §VII` and require `verify-charts` receipt |
| `visual_review_ready.py` | Verify static gates, rendered PNGs, skip flags, and vision availability |
| `route_state.json` | Persist selected route, checkpoints, user confirmations, and next action under each project |

Suggested minimal route-state schema:

```json
{
  "route": "topic-only | source-main | template-fill | beautify | resume | brand | extension",
  "project_path": "projects/example",
  "primary_workflow": "skills/ppt-master/workflows/...",
  "satellite_workflows": ["verify-charts", "visual-review"],
  "current_phase": "step4-confirmation",
  "blocking": true,
  "required_artifacts": [],
  "completed_gates": [],
  "open_risks": [],
  "next_action": ""
}
```

---

## 13. Supervisor Completion Audit

Before the router declares a request complete, it should answer:

| Audit question | Expected answer |
|---|---|
| Was the selected route justified by user intent and artifacts? | Yes, with ambiguous axes resolved |
| Were all workflow hard stops honored? | Yes, with explicit user confirmations recorded |
| Did the route produce its expected artifact? | PPTX, brand package, template package, preview URL, or validation report |
| Were conditional quality workflows considered? | Charts, visual review, live preview annotations, post-export validation |
| Were failures handled by the owning workflow's fallback? | Yes, no silent skip |
| Did the final response identify the canonical output path and residual risks? | Yes |

**Draft status**: this document is a routing design proposal. It is not an executable workflow and does not change authority until specific rules are promoted into `AGENTS.md`, `SKILL.md`, or the relevant workflow files.
