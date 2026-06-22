# spec_lock.md — Machine-Readable Execution Contract

> Executor re-reads this file before every SVG page. All values below are the single source of truth. On divergence with design_spec.md, this file wins.

---

## mode

- mode: narrative
- mode_behavior: 叙事驱动模式。故事线贯穿全篇，每页承载一个叙事节点。过渡页承上启下，内容页一个核心主张配一张 AI 图，讲解页结构化展开证据和细节。金句页情感锚点。整体节奏：呼吸 -> 沉浸 -> 呼吸 -> 沉浸。

## visual_style

- visual_style: story_driven（冰霜白浅色适配）
- visual_style_behavior: story_driven 模板的叙事结构和页面节奏，配色从暗色切换为冰霜白浅色系。保持三区布局（标题 -> 核心视觉 -> takeaway），AI 生成背景图用于封面 / 目录 / 过渡 / 金句 / 封底，内容页和讲解页使用浅色纯底 + AI 配图或 web 素材图。过渡页保留承上启下叙事桥结构。所有 AI 图统一 watercolor rendering。

## canvas

- format: ppt169
- dim: 1280x720
- viewBox: 0 0 1280 720
- margins: 60px left/right, 40px top/bottom
- content_area: x:60-1220 y:40-680

## colors

- primary: #D4789C
- secondary: #7EB8D8
- background: #F8F4F0
- accent: #9B72CF
- text: #2D2D3D
- secondary_text: #6B6B80
- highlight: #FFD6E8
- border: #D0C8D8
- secondary_bg: #F0ECF4
- warning: #E85C5C
- white: #FFFFFF
- warm_gold: #FFD6E8
- scrim: #F8F4F0 (light theme, minimal scrim)

## typography

- title_family: SimSun, Georgia, serif
- body_family: "Microsoft YaHei", Arial, sans-serif
- emphasis_family: KaiTi, Georgia, serif
- cover_title: 60px
- chapter_title: 44px
- page_title: 36px
- deep_dive_title: 36px
- hero_number: 72px
- subtitle: 26px
- body_size: 22px
- deep_dive_body_few: 30px
- deep_dive_body_many: 22px
- annotation: 15px
- page_number: 11px
- small_caption: 14px
- card_number: 28px
- card_body: 18px
- faq_question: 20px
- faq_answer: 18px

## icons

- library: tabler-outline
- stroke_width: 2
- inventory:
  - tabler-outline/camera
  - tabler-outline/shield
  - tabler-outline/sword
  - tabler-outline/star
  - tabler-outline/users
  - tabler-outline/clock
  - tabler-outline/heart
  - tabler-outline/palette
  - tabler-outline/book
  - tabler-outline/quote

## image_rendering

- rendering: watercolor
- palette: earthy-dusty
- consistency: all AI images use watercolor + earthy-dusty; web assets keep original style

## page_rhythm

| Page | Rhythm | Notes |
|------|--------|-------|
| P01 | anchor | 封面，视觉冲击，全出血 AI 背景 |
| P02 | dense | 目录，五章卡片信息密集 |
| P03 | breathing | 过渡页 -> 身世之谜，留白呼吸 |
| P04 | anchor | 内容页：冰中醒来的少女，核心视觉 |
| P05 | dense | 讲解页：身世之谜详解，四张卡片 |
| P06 | dense | 讲解页：人物关系网，中心 + 环绕卡片 |
| P07 | breathing | 过渡页 -> 视觉 DNA，留白呼吸 |
| P08 | anchor | 内容页：设计师夏一可，核心视觉 |
| P09 | dense | 讲解页：设计师访谈与原画，引言 + 画廊 |
| P10 | dense | 讲解页：视觉符号体系，五符号卡片 |
| P11 | breathing | 过渡页 -> 战斗成长，留白呼吸 |
| P12 | anchor | 内容页：三种形态，核心视觉 |
| P13 | dense | 讲解页：形态对比，三列对比卡片 |
| P14 | dense | 讲解页：战斗数据，大数字 + 说明 |
| P15 | anchor | 金句页，"我忍你很久了！"，情感锚点 |
| P16 | breathing | 过渡页 -> 版本叙事，留白呼吸 |
| P17 | anchor | 内容页：版本叙事弧，核心视觉 |
| P18 | dense | 讲解页：版本时间线，水平轴 + 节点 |
| P19 | breathing | 过渡页 -> 文化符号，留白呼吸 |
| P20 | anchor | 内容页：看板娘，核心视觉 |
| P21 | dense | 讲解页：社区文化数据，统计卡片 |
| P22 | dense | 讲解页：经典台词，语录拼贴 |
| P23 | anchor | 内容页：冰封记忆中的春天，核心视觉 |
| P24 | anchor | 封底，全出血 AI 背景，情感收束 |

## cover_impact

- hook: "我叫三月七！虽然我也不记得自己为什么叫这个名字了"
- composition: 全出血 AI 生成背景（三月七在列车窗边拍摄星空的水彩场景）+ 浮动标题
- title_position: 居中偏下，白色大字
- accent_line: 粉色 #D4789C 装饰线

## closing_impact

- hook: 冰封记忆中的少女，用相机和冰晶重新定义了自己
- composition: 全出血 AI 生成背景（三月七对镜头微笑，星穹列车与星空）+ 居中大字
- tagline: 三月七——崩坏星穹铁道 · 角色深度解读

## deep_dive_design_rules

- title: 36px, Bold, must echo/reference the preceding content page's core claim
- body_text: 22-26px minimum; for pages with fewer items (<=3), enlarge to 28-30px
- text_alignment: center-aligned unless layout specifically requires otherwise (e.g., timeline)
- line_height: 1.6-1.8
- element_spacing: >=32px between text blocks
- layout_variety: cards, columns, timelines, data callouts, FAQ — never plain text paragraphs
- web_assets: every deep-dive page MUST include >=1 web-sourced image
- narrative_continuity: title must explicitly reference preceding content page's core message
- deduplication: no two deep-dive pages may share the same data point, quote, or evidence block
