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
- visual_style_behavior: 深色军事/神秘美学（dark military/mystery）。形状语言偏锐利几何与有机曲线混合——战术界面使用直线和锐角，记忆/情感场景使用柔和曲线。装饰密度克制：仅在关键节点使用crimson高光切割近黑背景，避免大面积装饰性图案。留白策略：大量暗色留白创造孤寂感，文字区块间距偏宽以制造"呼吸感"。纹理：轻微颗粒噪点叠加在纯色背景上增加电影质感，避免光滑平面。整体调性冷峻克制，接近Arknights官方CG的暗黑奇幻视觉。

## colors
- bg: #1C1C1C
- secondary_bg: #252525
- primary: #8B1A1A
- accent: #C0C0C0
- secondary_accent: #5A5A5A
- text: #E8E8E8
- text_secondary: #A0A0A0
- text_tertiary: #707070
- border: #3A3A3A
- image_rendering: custom
- image_rendering_behavior: 半厚涂暗黑奇幻风格（semi-realistic dark fantasy），高对比度，选择性crimson亮色穿透近黑背景，类似Arknights官方CG质感——厚重暗部、锐利边缘光、戏剧性布光。避免纯平涂或扁平矢量风格。
- image_palette: custom
- image_palette_behavior: 以#1C1C1C炭黑为基底约占60%画面，#8B1A1A深红作为选择性高光约15%（武器边缘、能量源、兜帽内衬），#C0C0C0银灰作为冷调补光约15%（战术界面、金属表面、记忆碎片），其余10%为冷蓝（石棺光芒）和暖金（特蕾西娅记忆）。

## typography
- font_family: "Source Han Sans SC", "Microsoft YaHei", sans-serif
- body_family: "Microsoft YaHei", Arial, sans-serif
- code_family: Consolas, "Courier New", monospace
- body: 20
- title: 32
- subtitle: 26
- annotation: 15
- cover_title: 60
- transition_quote: 30

## icons
- library: chunk-filled
- inventory: hexagon, crosshair, link, eye, users, clock, lock, target

## images
- cover_bg: images/cover_bg.png
- toc_bg: images/toc_bg.png
- trans_01_hook: images/trans_01_hook.png
- content_precursor: images/content_precursor.png
- content_sarcophagus: images/content_sarcophagus.png
- trans_02_awakening: images/trans_02_awakening.png
- content_amnesia: images/content_amnesia.png
- trans_03_fragments: images/trans_03_fragments.png
- content_tactics: images/content_tactics.png
- content_chessboard: images/content_chessboard.png
- trans_04_mirror: images/trans_04_mirror.png
- content_relationships: images/content_relationships.png
- content_theresa_letter: images/content_theresa_letter.png
- trans_05_mask: images/trans_05_mask.png
- content_five_layers: images/content_five_layers.png
- content_self_insert: images/content_self_insert.png
- content_community: images/content_community.png
- content_ships: images/content_ships.png
- ending_stars: images/ending_stars.png
- ending_walk: images/ending_walk.png
- dim2_sarcophagus_interior: images/web_assets/dim2_sarcophagus_interior.png | no-crop
- dim4_theresa: images/web_assets/dim4_theresa.png | no-crop
- dim3_tactical_command: images/web_assets/dim3_tactical_command.png | no-crop
- dim6_doctor_concept: images/web_assets/dim6_doctor_concept.jpg | no-crop
- dim6_doctor_full_art: images/web_assets/dim6_doctor_full_art.png | no-crop
- dim6_doctor_priestess: images/web_assets/dim6_doctor_priestess.png | no-crop

## page_rhythm
- P01: anchor
- P02: anchor
- P03: breathing
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: dense
- P09: dense
- P10: dense
- P11: dense
- P12: breathing
- P13: dense
- P14: breathing
- P15: breathing
- P16: breathing
- P17: dense
- P18: dense
- P19: dense
- P20: dense
- P21: dense
- P22: dense
- P23: breathing
- P24: breathing
- P25: dense
- P26: anchor

## page_layouts
- P01: 01_cover
- P02: 02_toc
- P03: 02_chapter
- P04: 03_content
- P05: 03a_content
- P06: 03_content
- P07: 03a_content
- P08: 03_content
- P09: 03a_content
- P10: 03_content
- P11: 03_content
- P12: 02_chapter
- P13: 03a_content
- P14: 03_content
- P15: 03_content
- P16: 02_chapter
- P17: 03_content
- P18: 03a_content
- P19: 03_content
- P20: 03_content
- P21: 03a_content
- P22: 03_content
- P23: 03_content
- P24: 02_chapter
- P25: 03_content
- P26: 04_ending

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;` …) — write as raw Unicode (`—`, `©`, `→`, NBSP, etc.); XML reserved chars `& < > " '` must be escaped as `&amp; &lt; &gt; &quot; &apos;`. See shared-standards.md §1.0
