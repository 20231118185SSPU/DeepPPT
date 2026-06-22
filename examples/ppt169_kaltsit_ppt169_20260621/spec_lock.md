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
- visual_style_behavior: Semi-realistic dark fantasy aligned with Arknights visual language. Strong contrast with muted environment colors and character-driven focal points. Cinematic depth of field, atmospheric haze, volumetric light shafts, desaturated midtones with selective color pops (amber eyes, teal medical accents). Rim lighting and shadow pools define form. No cell shading, no flat illustration, no photorealism. Painterly texture with slightly gritty finish — the Arknights promotional CG aesthetic. Whitespace is not used for breathing; darkness and shadow serve that role. Decoration is minimal and atmospheric — light gradients, subtle particle effects, distant environmental detail.

## colors
- bg: #0A1628
- secondary_bg: #121E30
- primary: #1A5C5C
- accent: #D4A848
- secondary_accent: #8A94A6
- text: #E8E8E8
- text_secondary: #8A94A6
- text_tertiary: #5A6478
- border: #2A3040
- image_rendering: custom
- image_rendering_behavior: Semi-realistic dark fantasy rendering with painterly lighting and cinematic depth of field. Characters have anatomically proportioned figures with subtle stylization (sharper features, slightly elongated proportions). Environments use atmospheric haze, volumetric light shafts, and desaturated midtones with selective color pops. Heavy use of rim lighting and shadow pools. No cell shading, no flat illustration, no photorealism — the target is the Arknights official art / promotional CG aesthetic: dramatic, painterly, slightly gritty.
- image_palette: custom
- image_palette_behavior: Deep navy #0A1628 anchors 35-40% of canvas as the dominant background tone. Teal-green #1A5C5C occupies 15-20% in environmental elements (holographic displays, medical equipment, RI logos). Amber-gold #D4A848 appears in 5-8% as luminous accents — eyes, light sources, warm highlights against cool environments. Desaturated cool grays #8A94A6 / #5A6478 fill the remaining midtones for atmospheric depth. White #E8EDF2 appears only on Kal'tsit's coat as a focal element, never dominant.

## typography
- font_family: "Microsoft YaHei", Arial, sans-serif
- title_family: "Source Han Sans SC", "Microsoft YaHei", sans-serif
- body: 20
- title: 36
- subtitle: 26
- annotation: 15
- cover_title: 70
- chapter_title: 44

## icons
Not applicable — no icons used in this deck.

## images
- P01_cover_bg: images/P01_cover_bg.png | no-crop
- P02_toc_bg: images/P02_toc_bg.png | no-crop
- P03_chapter: images/P03_chapter.png | no-crop
- P04_content: images/P04_content.png
- P05_content: images/P05_content.png
- P06_chapter: images/P06_chapter.png | no-crop
- P07_content: images/P07_content.png
- P08_content: images/P08_content.png
- P09_chapter: images/P09_chapter.png | no-crop
- P10_content: images/P10_content.png
- P11_content: images/P11_content.png
- P12_chapter: images/P12_chapter.png | no-crop
- P13_content: images/P13_content.png
- P14_content: images/P14_content.png
- P15_chapter: images/P15_chapter.png | no-crop
- P16_content: images/P16_content.png
- P17_content: images/P17_content.png
- P18_ending: images/P18_ending.png | no-crop

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
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;` ...) — write as raw Unicode (`—`, `©`, `→`, NBSP, etc.); XML reserved chars `& < > " '` must be escaped as `&amp; &lt; &gt; &quot; &apos;`. See shared-standards.md §1.0
