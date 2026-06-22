# spec_lock.md v2 — Machine-readable execution contract

> Executor re-reads this file before every SVG page. On divergence with `design_spec.md`, this file wins.

---

## canvas

- format: ppt169
- width: 1280
- height: 720
- viewbox: 0 0 1280 720
- margin_left: 60
- margin_right: 60
- margin_top: 50
- margin_bottom: 40

---

## colors

- background: #F5F0E6
- secondary_bg: #EDE7D9
- primary: #425066
- accent: #7A5230
- secondary_accent: #789262
- body_text: #2D2D2D
- secondary_text: #555555
- tertiary_text: #999999
- border: #C8C0B0
- success: #789262
- warning: #B85C38
- white: #FFFFFF
- warm_gold: #D4C5A9

---

## typography

- title_family: SimSun, Georgia, serif
- body_family: "Microsoft YaHei", Arial, sans-serif
- emphasis_family: KaiTi, Georgia, serif
- code_family: Consolas, "Courier New", monospace

- body_size: 22
- cover_title: 60
- chapter_title: 44
- page_title: 36
- deep_dive_title: 36
- hero_number: 72
- hero_headline: 48
- subtitle: 26
- deep_dive_body_few: 30
- deep_dive_body_many: 22
- annotation: 15
- page_number: 11
- small_caption: 14
- card_number: 28
- card_body: 18
- data_label: 16
- error_item: 14
- faq_question: 20
- faq_answer: 18

- line_height: 1.6
- letter_spacing_title: 0.15em
- element_spacing_min: 32

---

## icons

- library: chunk-filled
- source: templates/icons/

---

## image_rendering

- rendering: watercolor
- palette: earthy-dusty

---

## page_rhythm

| Page | Type | Image Source | Layout Pattern | Title |
| ---- | ---- | ------------ | -------------- | ----- |
| P01 | cover | ai | full-bleed + floating title | 冥想与混元桩 |
| P02 | toc | ai | full-bleed + floating TOC | 目录 |
| P03 | transition | ai | full-bleed + floating text | 第一章 · 冥想改变大脑 |
| P04 | content | ai | left-image 35% + right-text 65% | 8周，大脑的物理结构改变了 |
| P05 | deep_dive | web+ai | top-data + bottom-image | 8周改变大脑：关键MRI研究数据 |
| P06 | deep_dive | web+ai | hero-number + 3-cards | 冥想的循证医学证据 |
| P07 | transition | ai | full-bleed + floating text | 第二章 · 站出来的功夫 |
| P08 | content | ai | right-image 35% + left-text 65% | 站桩为拳学之母 |
| P09 | deep_dive | web+ai | timeline + philosophy-cards | 母功的传承谱系 |
| P10 | transition | ai | full-bleed + floating text | 第三章 · 两条路，一个终点 |
| P11 | content | ai | left-image 35% + right-text 65% | 水与山的对话 |
| P12 | deep_dive | web+ai | 3-column-cards + comparison | 站桩的生理密码 |
| P13 | quote | ai | negative-space-centered | 庄子·心斋 |
| P14 | deep_dive | web+ai | symmetric-5:5-split | 冥想 vs 站桩：详细对比 |
| P15 | transition | ai | full-bleed + floating text | 第四章 · 你的第一个10分钟 |
| P16 | content | ai | top-image 40% + bottom-text 60% | 从5分钟开始 |
| P17 | deep_dive | web | cards-grid + progression-bar | 混元桩七步要领与进阶路线 |
| P18 | deep_dive | — | two-column-split | 呼吸与意念：内在维度 |
| P19 | deep_dive | web | 3-stage-cards + demographic-rows | 三位一体练习方案 |
| P20 | transition | ai | full-bleed + floating text | 第五章 · 动静合一 |
| P21 | content | ai | full-bleed + floating-centered | 动静合一 |
| P22 | deep_dive | — | 3-column-cards | 站桩练体·静坐练心·太极练合一 |
| P23 | deep_dive | — | faq-cards | 开始修炼前的常见问题 |
| P24 | ending | ai | full-bleed + floating text | 身心合一，动静皆修 |

---

## cover_impact

钩子："你的大脑只需要8周"——用哈佛MRI研究的反直觉发现打破"冥想是玄学"的偏见。全出血水墨山林背景 + 标题浮于留白区域。

---

## closing_impact

"你的身体就是最好的实验室"——科学精神与传统修炼智慧合二为一。黄昏山巅逆光站桩剪影，视觉上与封面呼应但色调更暖。

---

## deep_dive_design_rules

- text_alignment: center (default)
- title_size: 36px Bold
- body_size: 22-26px (many items), 28-36px (few items)
- line_height: 1.6
- element_spacing: ≥32px
- layout: structured (cards/columns/timeline/data-callouts), never plain text
- web_assets: every deep_dive page has ≥1 web-sourced image
- narrative_continuity: title echoes preceding content page's core claim
