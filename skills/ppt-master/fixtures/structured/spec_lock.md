# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## mode
- mode: instructional

## visual_style
- style: corporate-clean
- palette: navy + slate + amber accent

## colors
- bg: #F4F6F9
- primary: #16324F
- accent: #E8A33D
- text: #1A1A1A
- text_secondary: #5A6572
- border: #C9D2DC

## typography
- font_family: Arial, "Microsoft YaHei", sans-serif
- body: 18
- title: 30
- subtitle: 22
- footer_label: 11

## icons
- library: tabler-outline
- inventory: circle-check, arrow-right, chart-bar

## images
- sample_badge: images/sample_badge.png

## decisions
- audience: 合成演示（非敏感）
- tone: 客观、克制

## page_rhythm
- P01: anchor
- P02: breathing
- P03: dense

## page_layouts
- P01: t03_content
- P02: t03_content
- P03: t03_content

## page_charts
- (none): none

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- HTML named entities in text

## pptx_structure
- mode: structured
- template_reuse_scope: layout
- template_adherence: strict

## pptx_masters
- master-default: Default Master

## pptx_layouts
- content: master-default | Content | template:t03_content

## page_pptx_layouts
- P01: content
- P02: content
- P03: content
