---
description: Deterministic selection among DeepPPT2's top-level artifact routes (Generate / Create Template / Fill / Enhance).
---

# Routing Rules

Route selection authority for DeepPPT2. Select exactly one top-level route, then activate only the child workflows, profiles, and stages owned by that route.

**Hard rule**: If this file conflicts with a route summary elsewhere in the Skill package or in a repository-level user-facing document, this file wins for route selection. After selection, the route authority owns execution.

---

## 1. Routing Discipline

| Rule | Behavior |
|---|---|
| One artifact lifecycle | Every request enters Generate PPTX, Create Template, Fill Native PPTX, or Enhance Native PPTX |
| Supporting documents are not top-level routes | Create Template child workflows, generation profiles, stages, and governance documents refine the selected route; never offer them as competing top-level routes |
| Missing prerequisite | State the missing prerequisite and stop that route; do not invent an alternative |
| Ambiguous existing-deck request | Ask one discriminator question only when needed: regenerate visible slides, fill native slide shells with new content, or preserve slides and add native behavior? |
| Explicit user override | Honor explicit route instructions only when the route preconditions are satisfied |

**Forbidden — route-choice menus**: Do not present multiple implementation paths when the request already matches one row in §2. Ordinary design choices remain at the selected route's existing confirmation gate.

---

## 2. Top-Level Route Matrix

| Route | Request shape | Authority | Preconditions | Mutation model | Output contract |
|---|---|---|---|---|---|
| Generate PPTX | Create a new presentation; regenerate an existing deck visually; use source material or a topic; optionally apply an explicit template workspace | [`generate-pptx`](./generate-pptx.md) | Source facts exist or research can gather them; explicit quick intent activates its profile | Author new SVG pages and export a new PPTX | Default: spec, lock, SVG, validation, and PPTX; Quick: optional source/resource artifacts, no spec/lock, SVG, and one PPTX |
| Create Template | Create a reusable brand or layout/deck template from one or more PPTX/SVG files, images/PDFs, direct or file-based text, documents/websites, brand assets, or a mixed reference bundle | [`create-template`](./create-template.md) | A reusable-template request exists; reference material is optional | Author a new portable workspace; never modify any reference file in place | Workspace with required `templates/`, optional `images/` / `icons/`, and optional review `exports/` |
| Fill Native PPTX | Use a raw PPTX's native slide shells and replace/fill content | [`template-fill-pptx`](./template-fill-pptx.md) | Source PPTX plus new material/topic | Clone and patch PPTX through OOXML; no SVG pipeline | New filled PPTX in project `exports/` |
| Enhance Native PPTX | Keep a finished PPTX's visible slides stable while adding notes, audio, timings, or transitions | [`native-enhance-pptx`](./native-enhance-pptx.md) | Finished source PPTX exists | Append/update scoped OOXML parts; no slide regeneration | New enhanced PPTX in project `exports/` |

---

## 3. Generate PPTX Pre-Flows, Profiles, and Stages

| Request condition | Generate-route behavior |
|---|---|
| Topic only, with no source material | Run [`ppt-briefing`](./ppt-briefing.md) first (⛔ BLOCKING brief confirmation), then [`deep-research`](./deep-research.md) (7-step research orchestrator); return to [`generate-pptx`](./generate-pptx.md) Step 1 with its products |
| Source-backed input with planning-critical factual gaps | Run [`deep-research`](./deep-research.md) for the identified gaps only |
| `research_report.md` exists and `content_selection.json` does not | Run [`content-selection`](./content-selection.md) at Step 2 (interactive dimension picking) |
| `content_selection.json` exists | Run [`detailed-outline`](./detailed-outline.md) at Step 4 before the Eight Confirmations |
| `detailed_outline.json` exists | Run [`image-text-linking`](./image-text-linking.md) at Step 5 before image acquisition |
| Explicit quick/fast, skip-strategy, or direct SVG-to-PPTX intent | Activate [`quick-generate`](./profiles/quick-generate.md): omit Strategist/confirmation/spec/lock, hand-author SVG, run the lockless final checker, and export the final PPTX |
| Existing PPTX must preserve wording, page count, and page order 1:1 | Activate the [`beautify-pptx`](./profiles/beautify-pptx.md) profile inside the main pipeline |
| Existing PPTX may be split, merged, dropped, reordered, or re-outlined | Treat the PPTX as source content through [`generate-pptx`](./generate-pptx.md) Step 1 and its PPTX intake; continue the default pipeline |
| Split-mode project resumes in a fresh chat | Run [`resume-execute`](./stages/resume-execute.md) inside the active Generate route |
| User explicitly requests spec refinement | Run [`refine-spec`](./stages/refine-spec.md) after Step 4's confirm gate and before spec writing |
| Data charts exist | Run [`verify-charts`](./stages/verify-charts.md) before post-processing |
| User requests preview, selection, or annotation application | Use the default Generate pipeline and run [`live-preview`](./stages/live-preview.md) at the stage defined there |
| User explicitly requests visual review | Run [`visual-review`](./stages/visual-review.md) before post-processing (default recommended) |
| User requests page transitions, auto-advance, or deck-wide animation settings | Default export applies page transitions; per-element animation is opt-in via [`customize-animations`](./stages/customize-animations.md) |
| User requests recorded narration or video output | Run [`generate-audio`](./stages/generate-audio.md) after post-processing |
| User asks for batch-by-batch generation with intermediate feedback | Run [`batch-review`](./batch-review.md) |
| User asks to revise generated pages after Step 6 | Run [`revision-loop`](./revision-loop.md) |

**Hard rule — profile, not fifth route**: The 1:1 beautify behavior uses the same Strategist → Executor → SVG export lifecycle as Generate PPTX. It changes content/page invariants; it does not define a separate artifact lifecycle.

**Hard rule — direct-generation profile, not a fifth route**: `quick-generate` stays inside Generate PPTX but owns an explicit SVG → PPTX short circuit. Page count alone never activates or blocks it.

---

## 4. Template and Master/Layout Boundary

**Hard rule — explicit paths only**: Step 3 triggers only on explicit template directory paths supplied by the user after the two-step confirmation. Bare names, style descriptions, and slug matching never trigger it (`generate-pptx.md` Step 3). Template library indexes (`brands_index.json` / `layouts_index.json` / `decks_index.json`) are discovery aids; a UI pick is only a pending Step 3 action until the explicit path is applied.

| Input | Route behavior |
|---|---|
| Explicit brand / layout / deck workspace path + current project | [`generate-pptx`](./generate-pptx.md) Step 3 (dispatch per `kind`, fuse when multiple kinds) |
| Brand identity only (colors / typography / logo / voice, no SVG roster) + reusable intent | [`create-brand`](./create-brand.md) (Create Template child) |
| Reusable layout/deck package request | [`create-template`](./create-template.md) |
| Raw PPTX called a template + new content | Fill Native PPTX unless the user explicitly asks for a reusable template workspace |
| Request to add a master directly to an existing PPTX/SVG | Unsupported; explain the Create Template → Generate PPTX lifecycle |

---

## 5. Create Template Child Workflows

DeepPPT2 keeps `create-template.md` as the Create Template route authority and `create-brand.md` as its identity-only child workflow (both at `workflows/` root). They are mutually exclusive child workflows, not additional top-level routes.

| Selected kind | Behavior |
|---|---|
| `brand` | Dispatch to [`create-brand`](./create-brand.md); write identity only and no SVG roster |
| `layout` / `deck` | [`create-template`](./create-template.md); author structure (and identity for deck) with an SVG roster |

**Hard rule — classify reusable rules, not source completeness**: A complete PPTX does not automatically select deck. Use brand when only identity is stable; use layout/deck when fixed page structures are required.

---

## 6. Native and Shared Post-Processing Boundary

| Artifact state | Narration route |
|---|---|
| Main-generated project with notes and exported deck | Shared [`generate-audio`](./stages/generate-audio.md) stage |
| Arbitrary finished PPTX that must preserve visible slides | Enhance Native PPTX (Phase 3); its narration module invokes the same shared audio-stage rules |

Object animation for generated SVG projects uses the animation stage (`customize-animations`). Native PPTX routes preserve existing object-animation fingerprints and do not silently claim an animation-editing capability.

---

## 7. Template Name Boundary

| User input | Behavior |
|---|---|
| Explicit current workspace root containing `templates/design_spec.md` | Enter [`generate-pptx`](./generate-pptx.md) Step 3 |
| Bare template/brand name or style label | Do not resolve it to a local path; treat it as a style brief |
| "What templates exist?" | List indexed workspace paths as Q&A; do not advance a route |

For that Q&A only, read the matching discovery indexes:

| Kind | Discovery index |
|---|---|
| Brand | `templates/brands/brands_index.json` |
| Layout | `templates/layouts/layouts_index.json` |
| Deck | `templates/decks/decks_index.json` |

**Forbidden — fuzzy resolution**: Never resolve a bare name to a local template directory on the user's behalf. The explicit workspace root is the only Step 3 template trigger.
