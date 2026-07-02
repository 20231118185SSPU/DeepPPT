# Workflow Routing

> Detailed routing table — loaded on demand when an agent needs to dispatch to a specific workflow. `skills/ppt-master/SKILL.md` remains the authoritative workflow; this file is a compact routing aid only.

| User Intent | Workflow | Trigger |
|-------------|----------|---------|
| Generate PPT from source material or substantive content | SKILL.md main pipeline | default |
| Topic-only generation | [`ppt-briefing`](../skills/ppt-master/workflows/ppt-briefing.md) -> user confirmation -> [`deep-research`](../skills/ppt-master/workflows/deep-research.md) -> SKILL.md main pipeline | No source material; topic / direction / thin requirements only |
| Deep research before generation | [`deep-research`](../skills/ppt-master/workflows/deep-research.md) | After confirmed `ppt-briefing`; or source-backed requests that explicitly need research depth |
| Fill existing template with new content | [`template-fill-pptx`](../skills/ppt-master/workflows/template-fill-pptx.md) | "fill this deck", "reuse this design" |
| Beautify / re-layout existing PPT | [`beautify-pptx`](../skills/ppt-master/workflows/beautify-pptx.md) | "美化", "re-layout", "内容别动" |
| Resume generation in new chat | [`resume-execute`](../skills/ppt-master/workflows/resume-execute.md) | "继续生成 projects/…" |
| Refine spec before generation | [`refine-spec`](../skills/ppt-master/workflows/refine-spec.md) | "refine the spec first" (opt-in) |
| Live preview | [`live-preview`](../skills/ppt-master/workflows/live-preview.md) | "preview", "看效果" |
| Brand identity setup | [`create-brand`](../skills/ppt-master/workflows/create-brand.md) | "set up brand" / brand asset provided |
| Visual self-check | [`visual-review`](../skills/ppt-master/workflows/visual-review.md) | Default recommended after Executor quality gates and before Step 7; skip only on explicit opt-out or `confirm_ui/result.json` `skip_visual_review: true`; chart decks run `verify-charts` first |
| Calibrate chart coordinates | [`verify-charts`](../skills/ppt-master/workflows/verify-charts.md) | decks with data charts |
| Record narration / video export | [`generate-audio`](../skills/ppt-master/workflows/generate-audio.md) | "录音", "video export" |
| Customize animations | [`customize-animations`](../skills/ppt-master/workflows/customize-animations.md) | "change animation order/effect" |
| Standalone template design | [`create-template`](../skills/ppt-master/workflows/create-template.md) | no source deck |

## Existing PPTX Boundary

Route by the role the existing deck should play:

| User intent | Route | Boundary |
|-------------|-------|----------|
| Preserve page count, page order, and per-slide wording; only improve layout / hierarchy / whitespace | [`beautify-pptx`](../skills/ppt-master/workflows/beautify-pptx.md) | Strict 1:1 page mapping; text and data values are frozen |
| Reuse the original deck's design and fill it with new content | [`template-fill-pptx`](../skills/ppt-master/workflows/template-fill-pptx.md) | Edits PPTX directly; does not enter the SVG generation pipeline |
| Treat the PPTX as source material and freely restructure story, merge / split / drop / reorder pages, or change page count | SKILL.md main pipeline + `ppt_to_md` | The Strategist may re-architect the outline freely |
| Turn the PPTX into a reusable template package | [`create-template`](../skills/ppt-master/workflows/create-template.md) | Creates a template package, not a one-off generated deck |

Ambiguous requests such as "make this PPT more professional" must be clarified with one question: should page count/order and each slide's wording be preserved, or should the deck be treated as source material and restructured?

## Other High-Risk Boundaries

- Topic-only with no source material: run [`ppt-briefing`](../skills/ppt-master/workflows/ppt-briefing.md) first, stop for user confirmation, then run [`deep-research`](../skills/ppt-master/workflows/deep-research.md) before the main pipeline. Do not replace `deep-research` with ordinary built-in WebSearch; WebSearch is only a fallback inside the workflow.
- Animation: page transitions are on by default; per-element entrance animations are off by default. Use [`customize-animations`](../skills/ppt-master/workflows/customize-animations.md) only for object-level order / effect / timing requests.
- Live preview: Step 6 starts live preview automatically. Do not apply submitted annotations during generation; the annotation-application window opens after Step 7 through [`live-preview`](../skills/ppt-master/workflows/live-preview.md).
- Visual review: follow the current `skills/ppt-master/SKILL.md` rule. As of this file, [`visual-review`](../skills/ppt-master/workflows/visual-review.md) is recommended by default after Executor quality gates and before Step 7. Skip only by explicit opt-out or `confirm_ui/result.json` `skip_visual_review: true`; for chart decks, run `verify-charts` first.

> **Routing boundaries**: beautify preserves page count/order 1:1; any change to page structure = main pipeline. Template fill edits PPTX directly; beautify regenerates through SVG pipeline. For topic-only requests with no source, `ppt-briefing` is the first entry and `deep-research` runs only after the Brief is confirmed. Source files (PDF/DOCX/URL) may also route through `deep-research`; search steps are skipped only when the source already satisfies the research depth contract.
