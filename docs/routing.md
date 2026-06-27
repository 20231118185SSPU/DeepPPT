# Workflow Routing

> Detailed routing table — loaded on demand when the main pipeline or CLAUDE.md needs to dispatch to a specific workflow.

| User Intent | Workflow | Trigger |
|-------------|----------|---------|
| Generate PPT from source/topic | SKILL.md main pipeline | default |
| Deep research before generation | [`deep-research`](../skills/ppt-master/workflows/deep-research.md) | "深度调研" / "deep research" |
| Fill existing template with new content | [`template-fill-pptx`](../skills/ppt-master/workflows/template-fill-pptx.md) | "fill this deck", "reuse this design" |
| Beautify / re-layout existing PPT | [`beautify-pptx`](../skills/ppt-master/workflows/beautify-pptx.md) | "美化", "re-layout", "内容别动" |
| Resume generation in new chat | [`resume-execute`](../skills/ppt-master/workflows/resume-execute.md) | "继续生成 projects/…" |
| Refine spec before generation | [`refine-spec`](../skills/ppt-master/workflows/refine-spec.md) | "refine the spec first" (opt-in) |
| Live preview | [`live-preview`](../skills/ppt-master/workflows/live-preview.md) | "preview", "看效果" |
| Brand identity setup | [`create-brand`](../skills/ppt-master/workflows/create-brand.md) | "set up brand" / brand asset provided |
| Visual self-check | [`visual-review`](../skills/ppt-master/workflows/visual-review.md) | "视觉自检" (explicit request only) |
| Calibrate chart coordinates | [`verify-charts`](../skills/ppt-master/workflows/verify-charts.md) | decks with data charts |
| Record narration / video export | [`generate-audio`](../skills/ppt-master/workflows/generate-audio.md) | "录音", "video export" |
| Customize animations | [`customize-animations`](../skills/ppt-master/workflows/customize-animations.md) | "change animation order/effect" |
| Standalone template design | [`create-template`](../skills/ppt-master/workflows/create-template.md) | no source deck |

> **Routing boundaries**: beautify preserves page count/order 1:1; any change to page structure = main pipeline. Template fill edits PPTX directly; beautify regenerates through SVG pipeline. deep-research creates the project directory at its own Step 1. For topic-only requests with no source, run topic-research or deep-research before SKILL.md Step 1.
