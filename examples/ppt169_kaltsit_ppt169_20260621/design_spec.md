# 凯尔希深度解读 - Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline. Read once by downstream roles for context.
>
> Machine-readable execution contract: `spec_lock.md` (color / typography / icon / image short form). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep both in sync; on divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | ppt169_kaltsit_ppt169_20260621 |
| **Canvas Format** | PPT 16:9 (1280x720) |
| **Page Count** | 18 |
| **Design Style** | Custom (semi-realistic dark, same as Arknights) |
| **Target Audience** | Arknights players — familiar with in-game lore, faction politics, operator backstories, and community memes |
| **Use Case** | Deep-dive character analysis presentation — narrative, not data-heavy; designed for sharing among the Arknights player community |
| **Content Strategy** | Content is drawn from the research source (arknights_kaltsit.md) with selective reshaping for dramatic pacing. Factual claims stay sourced; narrative framing, emphasis ordering, and chapter breaks are Strategist's editorial choices. The source covers 8 sections; the 18-page deck restructures them into 5 narrative chapters + intro/conclusion, adding pages for Mon3tr, Patriot, and community culture that the source treats as asides. |
| **Created Date** | 2026-06-21 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280x720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top/bottom 50px |
| **Content Area** | 1160 x 620 |

---

## III. Visual Theme

### Theme Style

- **Mode**: narrative
- **Visual style**: custom — semi-realistic dark fantasy, aligned with Arknights visual language. Strong contrast, muted environment colors with character-driven focal points. No cartoon or chibi aesthetics — the subject demands gravitas.
- **Theme**: Dark theme
- **Tone**: Cinematic, melancholic, and authoritative — the visual tone of Arknights' own story chapters. Each page reads like a frame from a visual novel cutscene: atmospheric backgrounds carry the mood, text layers deliver the analysis.

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0A1628` | Deep navy — the darkness of 13,000 years |
| **Secondary bg** | `#121E30` | Card backgrounds, section surfaces — slightly lighter navy |
| **Primary** | `#1A5C5C` | Teal-green — medical authority and Rhodes Island identity |
| **Accent** | `#D4A848` | Amber-gold — ancient warmth, Kal'tsit's eye color, key highlights |
| **Secondary accent** | `#8A94A6` | Muted silver — secondary emphasis, gradient transitions |
| **Body text** | `#E8E8E8` | Light silver — main body text for dark backgrounds |
| **Secondary text** | `#8A94A6` | Captions, annotations, subtitles |
| **Tertiary text** | `#5A6478` | Supplementary info, footers, page numbers |
| **Border/divider** | `#2A3040` | Card borders, subtle dividers |
| **Success** | `#2ECC71` | Not used in this deck (no data positivity signals) |
| **Warning** | `#C0392B` | Not used in this deck (no alert states) |

### AI Image Strategy

- **Image Rendering**: custom
- **Image Rendering Behavior**: Semi-realistic dark fantasy rendering with painterly lighting and cinematic depth of field. Characters have anatomically proportioned figures with subtle stylization (sharper features, slightly elongated proportions). Environments use atmospheric haze, volumetric light shafts, and desaturated midtones with selective color pops. Heavy use of rim lighting and shadow pools. No cell shading, no flat illustration, no photorealism — the target is the Arknights official art / promotional CG aesthetic: dramatic, painterly, slightly gritty.
- **Image Palette**: custom
- **Image Palette Behavior**: Deep navy `#0A1628` anchors 35-40% of canvas as the dominant background tone. Teal-green `#1A5C5C` occupies 15-20% in environmental elements (holographic displays, medical equipment, RI logos). Amber-gold `#D4A848` appears in 5-8% as luminous accents — eyes, light sources, warm highlights against cool environments. Desaturated cool grays `#8A94A6` / `#5A6478` fill the remaining midtones for atmospheric depth. White `#E8EDF2` appears only on Kal'tsit's coat as a focal element, never dominant.

### Gradient Scheme

```xml
<!-- Amber-gold highlight gradient for accent elements -->
<linearGradient id="accentGradient" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#D4A848"/>
  <stop offset="100%" stop-color="#1A5C5C"/>
</linearGradient>

<!-- Background decorative glow (amber eye motif) -->
<radialGradient id="bgDecor" cx="80%" cy="20%" r="50%">
  <stop offset="0%" stop-color="#D4A848" stop-opacity="0.08"/>
  <stop offset="100%" stop-color="#D4A848" stop-opacity="0"/>
</radialGradient>

<!-- Teal atmospheric gradient -->
<radialGradient id="tealAtmosphere" cx="20%" cy="80%" r="60%">
  <stop offset="0%" stop-color="#1A5C5C" stop-opacity="0.12"/>
  <stop offset="100%" stop-color="#1A5C5C" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: CJK-primary dark cinematic — elegant Chinese sans titles, clean body sans for dense lore text.

Two views on the same font decisions:

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Source Han Sans SC", "Microsoft YaHei"` | `"Source Han Sans SC"` | `sans-serif` |
| **Body** | `"Microsoft YaHei"` | `Arial` | `sans-serif` |
| **Emphasis** | `"Microsoft YaHei"` | `Arial` | `sans-serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `"Source Han Sans SC", "Microsoft YaHei", sans-serif`
- Body: `"Microsoft YaHei", Arial, sans-serif`
- Emphasis: `"Microsoft YaHei", Arial, sans-serif` (same as Body)
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 20px (medium density — lore-heavy narrative with room to breathe)

| Purpose | Ratio to body | Example @ body=20 | Weight |
| ------- | ------------- | ----------------- | ------ |
| Cover title (hero headline) | 3.5x | 70px | Bold / Heavy |
| Chapter / section opener | 2.2x | 44px | Bold |
| Page title | 1.8x | 36px | Bold |
| Hero number | — | — | — |
| Subtitle | 1.3x | 26px | SemiBold |
| **Body content** | **1x** | **20px** | Regular |
| Annotation / caption | 0.75x | 15px | Regular |
| Page number / footnote | 0.5x | 10px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 60-80px from top — page title, chapter number, decorative teal line
- **Content area**: Middle section — varies by page type: full-bleed image overlay for breathing pages, card grid for dense pages, centered text for transition pages
- **Footer area**: Bottom 40px — page number (right-aligned), optional source attribution

### Layout Pattern Library

This deck uses primarily:

- **Full-bleed + floating text** (#1) — breathing/chapter pages: image fills canvas, text floats over dark scrim
- **Asymmetric split (2:8)** — content pages with image on left 30%, text body on right 70%
- **Center-radiating** — TOC page with chapter nodes
- **Negative-space-driven** — transition pages: one phrase or word in vast darkness
- **Figure-text overlap** — hero moments: headline sits over image edge

### Spacing Specification

**Universal**:

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Safe margin from canvas edge | 40-60px | 60px |
| Content block gap | 24-40px | 32px |
| Icon-text gap | 8-16px | — (no icons) |

**Non-card containers** (primary container type in this deck):

- Vertical rhythm carried by whitespace, not gutters
- Line-height: 1.5x for body text (20px → 30px line spacing)
- Full-bleed text placement: text inset with scrim overlay for legibility over dark atmospheric backgrounds

---

## VI. Icon Usage Specification

Not applicable — icons are not used in this deck.

---

## VII. Visualization Reference List

Not applicable — this deck contains no data charts or structured infographics. All visual content is narrative/illustrative.

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| P01_cover_bg.png | 1280x720 | 16:9 | Atmospheric cover — Kal'tsit back on bridge, Mon3tr shadow behind, mobile city on horizon | Background | #1 full-bleed background with floating title | ai | Pending | Kal'tsit's back viewed from behind, standing on Rhodes Island ship bridge, Mon3tr's dark shadow faintly visible to her right, desolate terrain and mobile city silhouettes on the distant horizon, low horizon line emphasizing vast sky and figure's solitude | none | hero_page |
| P02_toc_bg.png | 1280x720 | 16:9 | Terra map fragments with timeline markers as luminous points — chapter overview | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | Overhead view of fragmented Terra continent map with 5 chapter light-nodes connected by arc lines, Kal'tsit's code-name "Montagne" faintly inscribed at the origin point, dark cartographic texture | none | hero_page |
| P03_chapter.png | 1280x720 | 16:9 | Amber eye opening among Precursor ruins — awakening after millennia | Background | #1 full-bleed background with floating title | ai | Pending | Extreme close-up of an amber eye slowly opening, occupying 60% of frame center, pupil reflects faint lights of a Precursor city, shattered holographic screens and crystallized time fragments radiate from the eye edges into darkness | none | hero_page |
| P04_content.png | 1280x720 | 16:9 | Young Kal'tsit in Precursor-era uniform beside Mon3tr prototype in ancient facility | Illustration | #2 left-third image + right text body | ai | Pending | Medium shot of Kal'tsit in an archaic uniform (distinct from current white coat) in the left third, facing right toward a younger Mon3tr prototype, Precursor facility's curved architecture frames both figures, vertical light beam from the ceiling | none | local |
| P05_content.png | 1280x720 | 16:9 | The Great Collapse — Precursor city disintegrating, Kal'tsit's silhouette at the edge | Illustration | #2 left-third image + right text body | ai | Pending | Wide-angle view of a Precursor city skyline dissolving into white light in the upper half, Kal'tsit's solitary silhouette at the lower third edge — tiny against the scale of annihilation, Mon3tr coiled at her feet | none | local |
| P06_chapter.png | 1280x720 | 16:9 | Babel flag in wind, two figures' backs facing a distant battlefield — transition to Babel era | Background | #1 full-bleed background with floating title | ai | Pending | Mid-distance shot of a dark blue and white Babel banner flying in upper third, two figures (Kal'tsit and Theresa) viewed from behind in the center-lower area, battlefield horizon at the bottom, wind movement in fabric | none | hero_page |
| P07_content.png | 1280x720 | 16:9 | Kal'tsit and Theresa side by side in Babel command room — idealist meets realist | Illustration | #2 left-third image + right text body | ai | Pending | Interior medium shot of two women standing side by side, holographic map between them casting blue-green light, Theresa on the right with a gentle expression and warm tones, Kal'tsit on the left with calm expression and cool tones, visual temperature contrast | none | local |
| P08_content.png | 1280x720 | 16:9 | Split composition — Doctor in shadow, Kal'tsit at edge, distance between them | Illustration | #3 right-third image + left text body | ai | Pending | Split composition, masked Doctor figure in left shadow (dark tones), Kal'tsit at right edge (half-lit half-shadow), empty space between them representing fractured trust, tense stillness | none | local |
| P09_chapter.png | 1280x720 | 16:9 | Kal'tsit's hand gripping a yellowed letter — Theresa's farewell — warm amber glow from within | Background | #1 full-bleed background with floating title | ai | Pending | Extreme close-up of a hand gripping an aged letter, the character for "home" faintly visible on the paper, Mon3tr's claw gently resting on the wrist at the edge, warm amber light glowing from inside the paper, background completely out of focus | none | hero_page |
| P10_content.png | 1280x720 | 16:9 | Kal'tsit kneeling to meet young Amiya's gaze — hand hovering, ring glowing | Illustration | #2 left-third image + right text body | ai | Pending | Low-angle medium close-up, Kal'tsit on the left kneeling down, Amiya on the right looking up, their eyes meeting at center, Kal'tsit's hand suspended above Amiya's head without touching, Amiya's ring glowing faintly — the sole warm light source | none | local |
| P11_content.png | 1280x720 | 16:9 | Patriot's massive figure falling, Kal'tsit on high ground watching — diagonal composition | Illustration | #3 right-third image + left text body | ai | Pending | Distant wide shot, Patriot's enormous silhouette collapsing in the lower-left, Kal'tsit on elevated ground at upper-right, diagonal composition, wind catching her white coat hem for dynamic movement, battlefield smoke and scattered debris | none | local |
| P12_chapter.png | 1280x720 | 16:9 | Kal'tsit's white coat suspended in black void like a flag — tactical gear visible inside | Background | #1 full-bleed background with floating title | ai | Pending | White coat floating spread-open in pure black background like a banner, dark tactical suit visible on the inner side, fabric texture and crease details rendered, the coat as both shield and identity | none | hero_page |
| P13_content.png | 1280x720 | 16:9 | Kal'tsit and Wei Yenwu face to face across negotiation table — tea reflections, Lung skyline | Illustration | #2 left-third image + right text body | ai | Pending | Frontal symmetric shot, two figures seated on opposite sides of a negotiation table, each occupying half the frame, tea cups on the table reflecting both figures, Lung city nightscape visible through the window behind, power and tension | none | local |
| P14_content.png | 1280x720 | 16:9 | Design element deconstruction — coat, amber eyes, cat ears, tactical gear, Mon3tr annotated | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Kal'tsit frontal portrait at center, surrounded by annotated design elements connected by thin lines: white coat labeled "authority and concealment", amber eyes labeled "millennial warmth", tactical gear labeled "always prepared", Mon3tr silhouette labeled "ancient inheritance", blueprint-style annotation layout | embedded | local |
| P15_chapter.png | 1280x720 | 16:9 | White coat on pure black background as suspended banner — transition to visual analysis | Background | #1 full-bleed background with floating title | ai | Pending | The white coat suspended and spread open against pure black, viewed slightly from below as if a museum piece or reliquary, inner tactical suit visible, single amber light illuminating from below, the coat as the central exhibit | none | hero_page |
| P16_content.png | 1280x720 | 16:9 | Four color silhouettes of Kal'tsit — white, teal, dark blue, amber — merging into full portrait | Illustration | #47 small multiples + centered full portrait | ai | Pending | Four identical Kal'tsit silhouettes side by side, each filled with a different color (white, teal-green, dark navy-blue, amber-gold) representing her four character facets, a single full-color complete portrait overlaid at center, dark background with subtle color-gradient reflections | none | local |
| P17_content.png | 1280x720 | 16:9 | Kal'tsit alone in RI conference room at dawn — scattered reports, cold coffee, exhaustion | Illustration | #3 right-third image + left text body | ai | Pending | Side-lit scene from a window, Kal'tsit seated on the right third of frame, empty conference room stretching to the left, scattered mission reports and a cold coffee cup on the table, dawn's cold blue light filtering through, a rare moment of visible weariness | none | local |
| P18_ending.png | 1280x720 | 16:9 | Theresa's farewell letter floating as golden text in darkness — Mon3tr's amber eyes as sole anchor | Background | #1 full-bleed background with floating title | ai | Pending | Pure black background, handwritten farewell letter text floating as golden luminous text at center reading "I hope Rhodes Island can become the home you named", Mon3tr's two amber eyes glowing faintly at the very bottom as the only visual anchor, gold text and amber eyes in tonal harmony | none | hero_page |

---

## IX. Content Outline

### Part 1: 前言 — 万年之眸

#### P01 - Cover

- **Cover impact**: Core claim — "she has existed for over 13,000 years"; hero composition — Kal'tsit's solitary back on the Rhodes Island bridge with Mon3tr's shadow, mobile city silhouettes on the horizon. The cover's spine is isolation-in-civilization: one figure against the weight of millennia. Full-bleed atmospheric image with floating title text and amber accent line.
- **Layout**: Full-bleed background (#1) with floating title — image fills canvas, title and subtitle overlay on left with dark scrim
- **Title**: 万年之眸：凯尔希深度解读
- **Subtitle**: 明日方舟最古老、最危险、最被误解的存在
- **Info**: 2026 | Arknights Deep Dive

#### P02 - TOC

- **Cover impact**: Overview of 13,000 years in six chapter markers — Terra map fragments as luminous waypoints, connecting the arc from Precursor era to Rhodes Island
- **Layout**: Full-bleed background (#1) + scrim + 6 chapter nodes positioned as constellation points over the map
- **Title**: 章节目录
- **Core message**: This presentation spans five narrative chapters across 13,000 years of Terra's history — each chapter reveals a different face of the same woman.
- **Content**:
  - 01 前文明的遗存 — 一万三千年从何而来
  - 02 巴别塔的伤痕 — 理想、背叛与告别信
  - 03 冷面下的温度 — 恨意与保护的共生
  - 04 棋局 — 当所有人都在战斗时，她在建棋盘
  - 05 设计语言 — 白大褂、琥珀瞳、猫耳

---

### Part 2: Chapter 01 — 前文明的遗存

#### P03 - Transition: Chapter 01

- **Closing impact**: The chapter title "前文明的遗存" emerges from an amber eye opening in Precursor ruins — one image, one phrase, maximum atmospheric weight.
- **Layout**: Full-bleed background (#1) with floating chapter title — image fills canvas, title centered with accent underline
- **Title**: 01 | 前文明的遗存
- **Subtitle**: 她不属于这个时代的任何已知种族

#### P04 - Content: 凯尔希的真实身份

- **Layout**: Left-third image (#2) + right text body — image on left shows young Kal'tsit in Precursor facility, text body on right
- **Title**: 她存在了超过一万三千年
- **Core message**: Kal'tsit is not a survivor — she is a relic of a fallen civilization, and her 13,000-year memory carries the weight of every era she has witnessed.
- **Content**:
  - 凯尔希的种族被标注为"未知"——这在泰拉大陆的分类体系中几乎从未出现。官方代号"Montagne"，法语中的"山"——一座从旧时代留存至今的山。
  - 她的年龄超过一万三千年。前文明建造了原石能量系统，创造了生物机械生命体，最终走向"大崩溃"。凯尔希是这场灭亡的幸存者。
  - 但她不是在灾难中侥幸活下来的普通人。游戏文本暗示，她可能参与了"源石"的创造或传播——当前泰拉大陆上所有矿石病的根源，可能与她有关。
  - 这是一万三千年份的愧疚。

#### P05 - Content: Mon3tr——沉默的守护者

- **Layout**: Left-third image (#2) + right text body — image shows the Great Collapse, text on right
- **Title**: Mon3tr 才是真正的操作员
- **Core message**: Mon3tr is not a pet or a weapon — it is Precursor military hardware with autonomous consciousness, and Kal'tsit is its command interface.
- **Content**:
  - "Mon3tr 才是真正的操作员，凯尔希只是投递系统。"——玩家社群的这句话比大多数人意识到的更接近真相。
  - Block 3，真实伤害输出，凯尔希倒下后仍然继续战斗。Mon3tr 使用的不是源石技艺，而是比源石更古老、更直接的前文明攻击方式。
  - Mon3tr 的名字是"Monster"——这不是凯尔希给它起的，而是罗德岛其他人的外号。一万三千年了，这对搭档之间的默契已经不需要语言。
  - 在前文明的设计意图中，凯尔希可能真的只是 Mon3tr 的指挥界面。

---

### Part 3: Chapter 02 — 巴别塔的伤痕

#### P06 - Transition: Chapter 02

- **Closing impact**: Babel flag in wind, two backs facing the battlefield — the transition from solitary origin to companionship and its inevitable fracture.
- **Layout**: Full-bleed background (#1) with floating chapter title
- **Title**: 02 | 巴别塔的伤痕
- **Subtitle**: 理想、背叛与一封永远的告别信

#### P07 - Content: 特蕾西娅——跨越世纪的羁绊

- **Layout**: Left-third image (#2) + right text body — image shows Kal'tsit and Theresa in Babel command room
- **Title**: 巴别塔不是罗德岛的前身——它是罗德岛的伤疤
- **Core message**: Theresa was the spiritual core of Babel; her death at the Doctor's hands is the wound that defines Kal'tsit's every subsequent decision.
- **Content**:
  - 特蕾西娅是萨卡兹族的领袖，也是巴别塔的精神核心。与凯尔希的冷硬务实不同，特蕾西娅是一个近乎理想主义的存在——她相信感染者与非感染者可以共存。
  - 然后她死了。是博士杀了她。
  - 这不是隐喻。博士在某个被模糊处理的时间点做出了导致特蕾西娅死亡的决定。凯尔希在场。她看到了一切。
  - 特蕾西娅留下了一封信："我希望罗德岛能成为你命名的家。"凯尔希保管着这封信，也保管着这个愿望。

#### P08 - Content: "我将永远恨他们"——博士的矛盾

- **Layout**: Right-third image (#3) + left text body — image shows the split composition of Doctor and Kal'tsit
- **Title**: 恨一个人恨了一万年——然后在每一刻保护他
- **Core message**: Kal'tsit's relationship with the Doctor is built on unresolved hatred and an unchosen duty — she protects the person she cannot forgive, because Theresa asked her to.
- **Content**:
  - "我将永远恨他们。"——这句话指向博士，也指向所有让这一切发生的人。
  - 但恨意之后的选择令人心碎：凯尔希没有离开。她选择留在这个杀死她最亲密同伴的人身边。
  - 她在罗德岛遭受攻击时毫不犹豫地站在博士前面。在内部会议上说："博士的判断由我来评估。"这不是信任——这是自我施加的职责。
  - 她留下来，不是因为原谅了博士。她留下来，是因为特蕾西娅请求她留下来。

---

### Part 4: Chapter 03 — 冷面下的温度

#### P09 - Transition: Chapter 03

- **Closing impact**: Kal'tsit's hand gripping Theresa's farewell letter — the amber glow of a single word "家" (home) — from systemic analysis to the emotional core.
- **Layout**: Full-bleed background (#1) with floating chapter title
- **Title**: 03 | 冷面下的温度
- **Subtitle**: "不要碰阿米娅"

#### P10 - Content: "Don't touch Amiya"

- **Layout**: Left-third image (#2) + right text body — image shows Kal'tsit kneeling before young Amiya
- **Title**: 保护、监控、和恐惧
- **Core message**: Kal'tsit's relationship with Amiya is the closest thing to maternal love she allows herself — layered with protective instinct, surveillance, and the fear of watching history repeat.
- **Content**:
  - 阿米娅是特蕾西娅的继承者——体内携带着特蕾西娅留下的力量，那枚不断发光的戒指就是证明。
  - 凯尔希对阿米娅的态度可以概括为三个层次：保护、监控、和恐惧。
  - "不要碰阿米娅。"——这句话在游戏文本中出现过多次，核心含义一致：凯尔希将阿米娅的安全视为最高优先级，高于罗德岛的利益，高于博士的安全，甚至高于她自己的生命。
  - 她同时在监控阿米娅。这不是控制欲——这是一个活了一万三千年的人在看到历史重演时的恐惧。

#### P11 - Content: 爱国者之死与道德困境

- **Layout**: Right-third image (#3) + left text body — image shows Patriot falling, Kal'tsit watching from high ground
- **Title**: 她不为死亡动容——但她记录一切
- **Core message**: Kal'tsit's pragmatism extends to accepting casualties that idealism cannot — the death of Patriot is a moral event she witnessed without flinching, because flinching is a luxury 13,000 years has cost her.
- **Content**:
  - 爱国者（Patriot）的死亡是明日方舟叙事中最沉重的场景之一。一个父亲、一个战士、一个信仰者——倒在了罗德岛的战略计算中。
  - 凯尔希不在场战斗，但她在场审视。她将感染率视为统计数字——不是因为不在乎，而是因为她在乎到必须用数字来管理。
  - "这个世界上有很多傻瓜和疯子。"——不是犬儒主义，而是一万三千年历史的归纳。
  - 她见过太多文明因为理想主义而崩溃，见过太多领袖因为仁慈而毁灭。她选择了另一条路。

---

### Part 5: Chapter 04 — 棋局

#### P12 - Transition: Chapter 04

- **Closing impact**: Kal'tsit's white coat suspended in black void like a flag — inner tactical gear visible — the coat is both shield and chess piece.
- **Layout**: Full-bleed background (#1) with floating chapter title
- **Title**: 04 | 棋局
- **Subtitle**: 当所有人都在下棋时，凯尔希在建棋盘

#### P13 - Content: 政治棋手：魏彦吾与龙门

- **Layout**: Left-third image (#2) + right text body — image shows Kal'tsit and Wei Yenwu across negotiation table
- **Title**: 永远比对方多想三步
- **Core message**: Kal'tsit is Rhodes Island's true political operator — her negotiation style is to set conditions now that force outcomes later, and her power lies not in what she can do but in what others believe she can do.
- **Content**:
  - 罗德岛在很大程度上是凯尔希的政治工具。每一个决策都在影响泰拉大陆的权力格局。
  - 与魏彦吾的谈判是明日方舟政治叙事中最精彩的段落——两个同样冷静、同样深谋远虑的人，在谈判桌上下着一盘没有棋子的棋。
  - 她的让步总是包含着更深的布局，她的威胁总是点到为止——真正的权力不在于你能做什么，而在于对方相信你能做什么。
  - 与阿米娅的理想主义相比，凯尔希的务实主义有时显得冷血。但她不是不在乎——她是在乎到必须用结构来管理。

#### P14 - Content: 维多利亚的千年棋局

- **Layout**: Right-third image (#3) + left text body — image shows design element deconstruction of Kal'tsit
- **Title**: 不成为文明本身——成为文明延续的工具
- **Core message**: Kal'tsit's political vision extends beyond any single conflict; she operates on civilizational timescales, and Rhodes Island is merely her current instrument.
- **Content**:
  - 凯尔希的谈判风格可以概括为：永远比对方多想三步。她不会在当下争论，而是在未来的某个时间点设置条件。
  - 阿米娅想要拯救每一个人，凯尔希知道这不可能。阿米娅相信对话可以解决冲突，凯尔希知道对话只是另一种施压手段。
  - 凯尔希不关心争论的结果——她只关心罗德岛能否继续运作，阿米娅能否安全成长，以及博士是否会再次做出导致灾难的决定。
  - 她不信任任何人。她保护所有人。

---

### Part 6: Chapter 05 — 设计语言

#### P15 - Transition: Chapter 05

- **Closing impact**: The white coat as a museum exhibit, suspended in darkness — from narrative to visual analysis, the coat becomes the subject of study.
- **Layout**: Full-bleed background (#1) with floating chapter title
- **Title**: 05 | 设计语言
- **Subtitle**: 白大褂、琥珀瞳、猫耳

#### P16 - Content: 白大褂、琥珀瞳、猫耳

- **Layout**: Left-third image (#2) + right text body — image shows annotated design element deconstruction
- **Title**: 每一个视觉元素都有叙事含义
- **Core message**: Kal'tsit's visual design is one of Arknights' most restrained and successful character designs — every element (white coat, amber eyes, feline ears, tactical gear) encodes a narrative truth.
- **Content**:
  - 白色大衣——高领、收腰、军装化剪裁。白色同时承载两重含义：医学权威和信息遮蔽。凯尔希穿着白色，不是为了被看见，而是为了让你只看到她选择展示的东西。
  - 琥珀色眼睛——在泰拉大陆的角色设计中，眼睛颜色通常与种族相关。琥珀色暗示着古老、温暖、和被封存的时间。
  - 种族标注"菲林"的猜测——尖耳、纤细体态指向猫科，但"菲林"只是一种视觉近似。她看起来像是属于，但不属于。
  - 色彩调板：白色（权威与遮蔽）· 青色（治愈与罗德岛标识）· 深蓝灰（战术与沉稳）· 琥珀（古老与温度）。

#### P17 - Content: "她又开始念经了"——社区认知

- **Layout**: Right-third image (#3) + left text body — image shows Kal'tsit alone in conference room at dawn
- **Title**: 从"凯尔希语录"到万年梗
- **Core message**: The Arknights community's perception of Kal'tsit — long-winded, cold, meme-worthy — is itself a design success: the gap between surface reading and deep understanding mirrors the character's own layered concealment.
- **Content**:
  - "她又开始念经了。"——玩家社群对凯尔希长篇独白的经典吐槽。但这些"念经"每一段都藏着剧情伏笔。
  - "Mon3tr 才是真正的操作员"——从战斗机制梗到叙事真相的转化。Mon3tr 的 Block 3 和真实伤害是游戏设计，但"凯尔希只是投递系统"在前文明设定中字面成立。
  - 凯尔希的社区形象经历了从"冷面指挥官"到"万年孤独的守墓人"的认知转变——这本身就是一个关于表面阅读与深度理解的故事。
  - 她不信任任何人。她保护所有人。这就是凯尔希。

---

### Part 7: 终章

#### P18 - Ending

- **Closing impact**: Theresa's farewell letter materializes as golden light in darkness — "我希望罗德岛能成为你命名的家" — Mon3tr's amber eyes are the only response. The audience leaves with the weight of a promise kept across millennia.
- **Layout**: Full-bleed background (#1) with floating title — image fills canvas, farewell text and Mon3tr eyes overlay
- **Title**: 她记得一切
- **Content**:
  - "我希望罗德岛能成为你命名的家。"——特蕾西娅
  - 一万三千年。一座山。

---

## X. Speaker Notes Requirements

One speaker note file per page, saved to `notes/`:

- **Filename**: match SVG name (e.g., `01_cover.md`)
- **Content**: script key points, timing cues, transition phrases

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. Text characters: write typography and symbols as raw Unicode (em dash `—`, en dash `–`, `©`, `®`, `→`, NBSP, etc.); HTML named entities (`&nbsp;`, `&mdash;`, `&copy;`, `&reg;` ... ) are FORBIDDEN. XML reserved chars in text MUST be escaped as `&amp;` `&lt;` `&gt;` `&quot;` `&apos;` (e.g. `R&amp;D`, `error &lt; 5%`). See shared-standards.md §1.0
8. `marker-start` / `marker-end` conditionally allowed: `<marker>` must be in `<defs>`, `orient="auto"`, shape must be triangle / diamond / circle (see shared-standards.md §1.1)
9. `clipPath` conditionally allowed **only on `<image>` elements**: `<clipPath>` in `<defs>`, single shape child (circle / ellipse / rect with rx,ry / path / polygon). Do NOT apply to shapes / groups / text — draw the target geometry directly with the matching native element. See shared-standards.md §1.2

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN (group opacity); set on each child element individually
- Image transparency uses overlay mask layer (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only; external CSS and `@font-face` FORBIDDEN
