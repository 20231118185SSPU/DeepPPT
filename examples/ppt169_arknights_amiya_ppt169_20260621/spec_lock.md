# Execution Lock

> Machine-readable execution contract. Executor MUST `read_file` this before every SVG page. Values not listed here must NOT appear in SVGs. For design narrative (rationale, audience, style), see `design_spec.md`.
>
> After SVG generation begins, this is the canonical source for color / font / icon / image values. Modifications should go through `scripts/update_spec.py` to keep this file and generated SVGs in sync.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## mode
- mode: narrative

## visual_style
- visual_style: custom
- visual_style_behavior: "Semi-realistic dark fantasy (半厚涂暗色调) — Arknights' signature thick-paint aesthetic with cinematic depth of field, strong chiaroscuro from a single dominant light source, atmospheric fog and Originium particle effects. Shapes are organic and layered, not geometric. Decorative density is moderate: backgrounds are dark and textured with subtle industrial-military surfaces (rusted metal, medical equipment, combat fabric), while focal elements receive rim-lighting and crystal glow. Whitespace is used sparingly and intentionally as breathing room between dense narrative beats. Typography is bold, cinematic, with tight tracking on titles."

## colors
- bg: #0A0E1A
- secondary_bg: #151B2E
- primary: #D4A848
- accent: #E87B3D
- secondary_accent: #8A94A6
- text: #E8E8E8
- text_secondary: #8A94A6
- text_tertiary: #5A6478
- border: #2A3040
- image_rendering: digital-painting
- image_palette: custom
- image_palette_behavior: "Deep navy base #0A0E1A anchors approximately 40% of each image canvas. Gold and amber accents #D4A848 appear as rim lighting, ceremonial elements, and key focal highlights at approximately 15%. Originium orange #E87B3D surfaces in crystalline glow, energy emanations, and explosive moments at approximately 8%. Secondary steel blue #8A94A6 fills atmospheric haze, fabric, and shadowed surfaces at approximately 20%. Remaining surface area uses desaturated cool grays and muted earth tones. Strong chiaroscuro with single dominant light source and cinematic depth of field."

## typography
- title_family: "Source Han Sans SC", "Microsoft YaHei", sans-serif
- font_family: "Microsoft YaHei", Arial, sans-serif
- code_family: Consolas, "Courier New", monospace
- body: 20
- title: 36
- subtitle: 26
- annotation: 15
- cover_title: 70
- chapter_title: 44

## icons
- library: none
- inventory: none

## images
- P01_cover_bg: images/P01_cover_bg.png | no-crop
- P02_toc_bg: images/P02_toc_bg.png | no-crop
- P03_transition_origin: images/P03_transition_origin.png | no-crop
- P04_content_amiya_origin: images/P04_content_amiya_origin.png | no-crop
- P05_content_rhodes_island: images/P05_content_rhodes_island.png | no-crop
- P06_transition_infection: images/P06_transition_infection.png | no-crop
- P07_content_skullshatterer: images/P07_content_skullshatterer.png | no-crop
- P08_content_frostnova: images/P08_content_frostnova.png | no-crop
- P09_transition_awakening: images/P09_transition_awakening.png | no-crop
- P10_content_demon_king: images/P10_content_demon_king.png | no-crop
- P11_content_three_forms: images/P11_content_three_forms.png | no-crop
- P12_transition_relationships: images/P12_transition_relationships.png | no-crop
- P13_content_doctor_bond: images/P13_content_doctor_bond.png | no-crop
- P14_content_chen_parallel: images/P14_content_chen_parallel.png | no-crop
- P15_transition_visual_design: images/P15_transition_visual_design.png | no-crop
- P16_content_design_symbolism: images/P16_content_design_symbolism.png | no-crop
- P17_content_community_impact: images/P17_content_community_impact.png | no-crop
- P18_ending_bg: images/P18_ending_bg.png | no-crop

## page_rhythm
- P01: anchor
- P02: anchor
- P03: breathing
- P04: dense
- P05: dense
- P06: breathing
- P07: dense
- P08: dense
- P09: breathing
- P10: dense
- P11: dense
- P12: breathing
- P13: dense
- P14: dense
- P15: breathing
- P16: dense
- P17: dense
- P18: anchor

## page_layouts
- P01: 01_cover
- P02: 02_toc
- P03: 02_chapter
- P04: 03_content
- P05: 03a_content
- P06: 02_chapter
- P07: 03_content
- P08: 03a_content
- P09: 02_chapter
- P10: 03_content
- P11: 03a_content
- P12: 02_chapter
- P13: 03_content
- P14: 03a_content
- P15: 02_chapter
- P16: 03_content
- P17: 03a_content
- P18: 04_ending

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;` …) — write as raw Unicode (`—`, `©`, `→`, NBSP, etc.); XML reserved chars `& < > " '` must be escaped as `&amp; &lt; &gt; &quot; &apos;`
