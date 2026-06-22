# Arknights Amiya Deep Dive - Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline. Read once by downstream roles for context.
>
> Machine-readable execution contract: `spec_lock.md` (color / typography / icon / image short form). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep both in sync; on divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | Arknights Amiya Deep Dive |
| **Canvas Format** | PPT 16:9 (1280x720) |
| **Page Count** | 18 |
| **Design Style** | semi-realistic dark fantasy (半厚涂暗色调) |
| **Target Audience** | Arknights players — existing fans who know Amiya as the starter character but want to understand her full narrative weight, design philosophy, and cultural significance |
| **Use Case** | Narrative-driven deep-dive deck for community sharing, content creation, or fan event presentation |
| **Content Strategy** | balanced — faithfully present the research document's narrative arc (origin → crisis → awakening → relationships → identity → community) while condensing and restructuring for 18-page visual storytelling |
| **Created Date** | 2026-06-21 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280x720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top/bottom 50px |
| **Content Area** | 1160x620 |

---

## III. Visual Theme

### Theme Style

- **Mode**: narrative
- **Visual style**: semi-realistic dark (半厚涂暗色调) — custom aesthetic combining Arknights' signature thick-paint darkness with cinematic framing
- **Theme**: Dark theme
- **Tone**: Cinematic, atmospheric, emotionally charged — the feeling of watching an Arknights animated PV

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0A0E1A` | Deep navy base — the core Arknights dark tone |
| **Secondary bg** | `#151B2E` | Card background, section background — slightly lighter navy for elevation |
| **Primary** | `#D4A848` | Title decorations, key sections — gold representing the Civilight Eterna and Arknights identity |
| **Accent** | `#E87B3D` | Originium orange — data highlights, key emphasis, Source Stone energy |
| **Secondary accent** | `#8A94A6` | Muted steel blue — secondary emphasis, gradient transitions |
| **Body text** | `#E8E8E8` | Main body text — warm off-white for readability on dark backgrounds |
| **Secondary text** | `#8A94A6` | Captions, annotations — muted to sit behind body text |
| **Tertiary text** | `#5A6478` | Supplementary info, footers — subdued for least emphasis |
| **Border/divider** | `#2A3040` | Card borders, divider lines — subtle dark steel |
| **Success** | `#4CAF50` | Positive indicators (unused in narrative deck) |
| **Warning** | `#E87B3D` | Issue markers (shares Originium orange) |

### AI Image Strategy

- **Image Rendering**: digital-painting
- **Image Palette**: custom
- **Image Palette Behavior**: Deep navy base `#0A0E1A` anchors approximately 40% of each image's canvas area, establishing Arknights' signature darkness. Gold and amber accents `#D4A848` appear as rim lighting, ceremonial elements, and key focal highlights at approximately 15%. Originium orange `#E87B3D` surfaces in crystalline glow effects, energy emanations, and explosive moments at approximately 8%. Secondary steel blue `#8A94A6` fills atmospheric haze, fabric, and shadowed surfaces at approximately 20%. The remaining surface area uses desaturated cool grays and muted earth tones to prevent palette fatigue. Images should maintain strong chiaroscuro with a single dominant light source and cinematic depth of field.

### Gradient Scheme

```xml
<!-- Title gradient — gold to Originium orange -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#D4A848"/>
  <stop offset="100%" stop-color="#E87B3D"/>
</linearGradient>

<!-- Background decorative radial — subtle Originium glow -->
<radialGradient id="bgDecor" cx="80%" cy="20%" r="50%">
  <stop offset="0%" stop-color="#D4A848" stop-opacity="0.08"/>
  <stop offset="100%" stop-color="#D4A848" stop-opacity="0"/>
</radialGradient>

<!-- Content area scrim — darkens image regions for text legibility -->
<linearGradient id="contentScrim" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#0A0E1A" stop-opacity="0.85"/>
  <stop offset="60%" stop-color="#0A0E1A" stop-opacity="0.6"/>
  <stop offset="100%" stop-color="#0A0E1A" stop-opacity="0"/>
</linearGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: CJK-primary sans-serif with strong Chinese character rendering — the deck is entirely Chinese-facing, targeting an Arknights community audience. Latin text is minimal (proper nouns only: Amiya, Rhodes Island, Originium). Title stack prioritizes a geometric sans with bold weight for cinematic punch; body stack prioritizes readability at 20px on dark backgrounds.

Two views on the same font decisions — fill both, keep them consistent:

- **Role breakdown** (table below) — lists the *pieces* per role: CJK font, Latin font, CSS generic fallback. Human-readable design language.
- **Per-role font stacks** (after the table) — the *ordered* CSS `font-family` strings that actually go into SVG `font-family=""` and `spec_lock.md`'s `*_family` lines. Order controls browser rendering (Latin-led vs. CJK-led), so this is the **actual data** — not derivable from the table alone.

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Source Han Sans SC"` | `"Microsoft YaHei"` | `sans-serif` |
| **Body** | `"Microsoft YaHei"` | `Arial` | `sans-serif` |
| **Emphasis** | `"Microsoft YaHei"` | `Arial` | `sans-serif` (same as Body) |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks** (CSS `font-family` strings, one per role):

- Title: `"Source Han Sans SC", "Microsoft YaHei", sans-serif`
- Body: `"Microsoft YaHei", Arial, sans-serif`
- Emphasis: same as Body
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 20px

| Purpose | Ratio to body | Example @ body=20 | Weight |
| ------- | ------------- | ----------------- | ------ |
| Cover title (hero headline) | 3.5x | 70px | Heavy |
| Chapter / section opener | 2.2x | 44px | Bold |
| Page title | 1.8x | 36px | Bold |
| Subtitle | 1.3x | 26px | SemiBold |
| **Body content** | **1x** | **20px** | Regular |
| Annotation / caption | 0.75x | 15px | Regular |
| Page number / footnote | 0.55x | 11px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 0–80px from top — title + gold decorative underline or accent bar
- **Content area**: 80–650px — image region + text blocks, governed by page rhythm (dense vs breathing)
- **Footer area**: 650–720px — page number, subtle source attribution, decorative line

### Layout Pattern Library

This narrative deck uses the story_driven template family. The core layout strategies are:

- **Full-bleed background + floating text** (`breathing` pages — cover, transitions, ending): image fills the entire canvas; title and supporting text float over a dark scrim region, using negative space as a design element.
- **Asymmetric split — 40% image / 60% text** (`dense` content pages using 03_content.svg): image occupies the left or right portion with the content narrative flowing alongside.
- **Asymmetric split — 60% image / 40% text** (`dense` content pages using 03a_content.svg): image is the dominant element with text on the opposite side providing context and analysis.

### Spacing Specification

**Universal** (any container type):

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Safe margin from canvas edge | 50px | 50px |
| Content block gap | 28px | 28px |
| Text line spacing | 1.5x | 1.5x body size = 30px |

**Non-card containers** (primary layout mode — this deck avoids card grids in favor of text-and-image flow):

- Vertical rhythm carried by whitespace, not gutters.
- Line-height: 1.5x for body text (20px body = 30px leading), 1.4x for titles.
- Full-bleed text placement: text inset at least 60px from canvas edges; legibility over image backgrounds requires a scrim overlay of 0.7–0.85 opacity.

---

## VI. Icon Usage Specification

### Source

- **No icons used in this deck.** The narrative content does not require iconography. Visual storytelling relies entirely on AI-generated images and typography.

---

## VII. Visualization Reference List

**No data visualization pages in this deck.** This is a narrative/character-analysis presentation, not a data-heavy briefing. All content is prose-driven with image accompaniment. No chart templates are needed.

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| P01_cover_bg.png | 1280x720 | 16:9 | Amiya face-forward half-portrait, Rhodes Island landship silhouette behind her, Originium crystal particles drifting in the sky — establishing the girl-against-the-world scale contrast | Background | #1 full-bleed background with floating title | ai | Pending | A young woman with long dark hair and rabbit ears penetrating through a hooded cloak, gazing at the viewer with steady yet sorrowful eyes. Behind her, the massive dark silhouette of a landship stretches across the upper background. Originium crystal particles drift from lower-right to upper-left, guiding the eye from the foreground figure to the distant world. Main light source from upper-left 45 degrees, rim-lighting her face and ear edges. Bottom third left dark for title overlay. Composition: centered, half-body portrait, low-angle upward tilt conveying both youth and burden. | none | hero_page |
| P02_toc_bg.png | 1280x720 | 16:9 | Wide-angle bird's-eye of the Terra wasteland — giant Originium crystals erupting from the earth, city ruins on the horizon — sets the grand, harsh, beautiful-at-same-time tone | Background | #1 full-bleed background with floating title | ai | Pending | A wide panoramic view of a barren wasteland. Foreground: cracked, desolate ground textures with clusters of small Originium crystals. Midground: the silhouettes of ruined industrial cities stretching along the horizon. Sky: heavy cloud cover with a single golden light beam piercing through a gap, casting warm light on the desolate scene. Overall cool tone with the golden beam as the only warm accent, suggesting hope amid desolation. Composition: wide-angle, horizon at lower third, vast open space above for overlay text. | none | hero_page |
| P03_transition_origin.png | 1280x720 | 16:9 | A small girl's silhouette in the Kazdel ruins, collapsed buildings and Originium dust fog surrounding her, ominous orange-red sky above — from world-scale to personal-scale | Background | #1 full-bleed background with floating title | ai | Pending | Low-angle upward shot. A small girl silhouette (approximately child height, with Cautus ears) stands with her back to the viewer at the right lower-third golden-ratio point. She faces a massive complex of ruined buildings on the left. The sky fills the upper half with an ominous orange-red glow emanating from the horizon. Originium dust fog forms translucent layers in the midground. Ground debris and rubble textures are detailed, implying war. Composition: child at small scale against vast destruction, conveying vulnerability. | none | hero_page |
| P04_content_amiya_origin.png | 1160x425 | ~2.7:1 | Young Amiya in a Kazdel underground shelter, held by Kal'tsit's hand, surrounded by Sarkaz refugees and crude medical facilities — the meeting that changed everything | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Indoor scene. Light comes from a wall gap on the left and an oil lamp on a table. Kal'tsit stands on the left, posture slightly bent, face directed toward a young Amiya on the right, who looks up at her. Background contains blurred refugee figures providing environmental narrative. Warm light limited to the area between the two figures, fading to darkness around the edges, creating a convergent light structure. The shelter is rough stone and metal, with improvised medical cots in the background. | none | local |
| P05_content_rhodes_island.png | 1160x425 | ~2.7:1 | Amiya standing on the Rhodes Island bridge command room, holographic strategic map behind her, Doctor's chair empty in the corner — young leader with vast responsibility | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Medium shot, front-facing. Amiya stands center-right, facing the viewer but with gaze slightly left toward a holographic blue strategic map projection. Blue holo-light illuminates her face. Left midground shows control consoles and operator silhouettes in motion. An empty chair sits at lower-right, its outline traced by faint backlight, suggesting the Doctor's presence or absence. Overall cool blue-gray command room tone with Amiya's clothing retaining subtle warm accents. | none | local |
| P06_transition_infection.png | 1280x720 | 16:9 | Close-up of Originium crystals growing from an infected person's hand, dark-red light pulsing inside the crystals, blurred city lights in background — the physical reality of Oripathy | Background | #1 full-bleed background with floating title | ai | Pending | Extreme close-up macro composition. A hand (dark-skinned, knuckles rough, possibly Sarkaz features) extends from the bottom of frame toward center. Originium crystals grow from the fingertips toward the wrist, translucent with dark-red light pulsing inside. Background is heavily blurred city neon light bokeh. Focus is on the growing edge of the crystal formation, implying irreversibility of infection. Deep shadows with selective illumination on the crystal surfaces. | none | hero_page |
| P07_content_skullshatterer.png | 1160x425 | ~2.7:1 | The Skullshatterer confrontation: Amiya casting Arts with her staff, facing Misha in a bone mask, explosive light and debris filling the space between them | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Dynamic diagonal composition. Amiya in the lower-left, staff extended toward upper-right, Arts energy streaming from the staff tip in an arc. Skullshatterer (Misha) in the upper-right, bone mask partially shattering under the Arts light, revealing a young face beneath. The space between them filled with explosive particles and Originium fragments, forming a visual conflict axis. Cool-purple Arts energy and warm-orange explosions create strong warm-cold contrast. | none | local |
| P08_content_frostnova.png | 1160x425 | ~2.7:1 | FrostNova collapsing in a snowstorm, her ice crystals dissipating in radiating petals, Amiya's outstretched hand reaching but unable to touch her — the most heartbreaking scene | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Horizontal composition. FrostNova at center-right, half-kneeling in snow, ice crystals radiating outward from her body and dissolving like falling petals. Amiya on the left, arm reaching toward FrostNova but with visible distance between them. Blizzard blowing right to left, snow and ice particles filling the frame. Cool white and pale blue dominant tone, FrostNova's dissolving crystals carrying faint purple glow. Emotional weight conveyed through the gap between the reaching hand and the dissolving figure. | none | local |
| P09_transition_awakening.png | 1280x720 | 16:9 | Extreme close-up of Amiya's Sarkaz horn growing from her forehead, Originium crystals and dark-purple energy veins spreading across the horn surface — beautiful and terrifying | Background | #1 full-bleed background with floating title | ai | Pending | Extreme close-up starting from Amiya's right forehead horn base extending to the horn tip. The horn surface shows a gradient: natural horn-textured base transitioning upward into Originium crystal coverage, with dark-purple energy veins flowing inside the crystals. Background pure black, only the faint purple glow from the horn tip provides edge-light silhouette. Horn tip extends past the frame top edge, implying limitless power spreading. Mesmerizing, unsettling beauty. | none | hero_page |
| P10_content_demon_king.png | 1160x425 | ~2.7:1 | Episode 8 Demon King awakening: Amiya floating in the void, full Sarkaz Demon King pose, massive dark-purple Originium wing-structures expanding behind her, spatial rifts and collapsing debris | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Center-symmetric composition. Amiya suspended at exact center, body slightly curved, arms spread wide. Originium wing-structures extend to both sides filling most of the frame width, creating symmetrical oppressive grandeur. Spatial rifts radiate from the four corners toward center. Collapsing building fragments and crystal shards spiral around Amiya in a vortex trajectory. Primary palette deep purple and black, but Amiya's eyes and core Arts array emit gold-white light as the sole hope-source in the composition. | none | local |
| P11_content_three_forms.png | 1160x425 | ~2.7:1 | Amiya's three forms side by side: Caster (blue staff, calm), Guard (black sword, fierce), Medic (white staff, compassionate), three silhouettes sharing the same baseline | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Triptych composition. Three Amiyas spaced evenly across the frame, each facing a different direction (Caster right, Guard forward, Medic left) but with feet aligned on the same baseline. Each form has its own color domain: Caster blue, Guard dark-purple, Medic white-gold. Originium vein patterns connect the three forms along the baseline, suggesting shared origin. Background gradient varies per form but merges into a unified gold light band across the center. Visual message: three forms, one person. | none | local |
| P12_transition_relationships.png | 1280x720 | 16:9 | A Rhodes Island corridor, two shadows cast on opposite walls — Amiya's sharp silhouette and the Doctor's blurred human-shaped outline — shadows converging at the end | Background | #1 full-bleed background with floating title | ai | Pending | Corridor perspective composition with vanishing point at upper-center. Left wall casts Amiya's clear shadow with distinct ear outlines; right wall casts the Doctor's blurred human-form shadow. The two shadows converge toward the corridor end. Faint corridor lights along both walls, reflective metal floor surface. Real figures do not appear — only shadows and the corridor space itself. Cool blue-gray tone, with a faint warm glow where the shadows merge at the far end. | none | hero_page |
| P13_content_doctor_bond.png | 1160x425 | ~2.7:1 | Amiya and Doctor's backs sitting together on the Rhodes Island observation deck, facing Terra's night sky — distant city lights and stars above — a quiet moment amid chaos | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Wide cinematic composition. Two figures from behind occupy the lower third, sitting on deck railing. Doctor on left, Amiya on right, with comfortable spacing between them but relaxed postures. They face an open night vista — faint city lights forming a glow band on the distant horizon, sky above with stars (some replaced by tiny Originium particles). Focus on the connection between the two figures and the vast world ahead. Deep blue night sky dominant, city lights providing warm orange accent points. | none | local |
| P14_content_chen_parallel.png | 1160x425 | ~2.7:1 | Amiya and Ch'en facing each other in a rainy Lungmen street, an umbrella blown upward by wind between them, neon signs reflecting on wet cobblestones | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Medium confrontation composition. Amiya on the left, Ch'en on the right, approximately two steps apart. A wind-caught umbrella rises between them along the central vertical axis, acting as a visual separator. Rain pours from above, wet cobblestone ground reflects background neon signs in pink, blue-purple, and orange tones. Both figures' expressions show complex emotions in their mutual gaze — understanding, reluctant respect, kinship. Cool base tone with rich warm reflections from the neon. | none | local |
| P15_transition_visual_design.png | 1280x720 | 16:9 | A concept art workstation view: Amiya's costume detail sketches, Arts geometry patterns, horn structural breakdown diagrams scattered on a dark designer's desk | Background | #1 full-bleed background with floating title | ai | Pending | Flat-lay top-down composition on a dark wood-textured desk. Scattered across the surface: character costume line-art details, Originium crystal geometry analysis diagrams, color sample swatches, horn structural cross-sections. Elements connected by annotation arrows and measurement lines. Design tools (pencils, compass, ruler) scattered between the sheets. Layout intentionally loose but organized, like a concept artist's working desk. Paper in cream/off-white with graphite-gray line art, desk is dark wood grain. | none | hero_page |
| P16_content_design_symbolism.png | 1160x425 | ~2.7:1 | Amiya's silhouette at center with six design elements radiating outward: rabbit ears, staff geometry, crystal structure, costume texture, three-form color samples, horn evolution — visual semiotics breakdown | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Center-radiation composition. Amiya's full-body silhouette at the exact center, filled solid black. From six key feature points, analysis leader lines extend outward: rabbit ears (upper-left), staff/weapon (upper-right), costume structure (left-center), crystal texture patterns (right-center), three-form color domains (lower-left), Sarkaz horn evolution (lower-right). Each leader line terminates in a magnified detail diagram or illustration. Dark background, analysis elements in white line-art with color accent from the deck palette. | none | local |
| P17_content_community_impact.png | 1160x425 | ~2.7:1 | A mosaic collage of various Amiya fan-art styles — hand-drawn, pixel art, watercolor, 3D render, chibi — arranged as a patchwork with the official Amiya silhouette as a central negative-space outline | Illustration | #44 background image + native network/architecture diagram | ai | Pending | Mosaic collage composition. The frame is divided into irregular rectangular tiles of varying sizes, each containing a different art style representation of Amiya (abstract color blocks representing hand-drawn, pixel, watercolor, 3D, and chibi styles). The central area preserves a clean Amiya official-art silhouette outline as negative space, contrasting with the dense surrounding mosaic. Rich color variety from the diverse styles converging, with the central outline rendered in white stroke forming the visual focal point. | none | local |
| P18_ending_bg.png | 1280x720 | 16:9 | Amiya at the bow of the Rhodes Island deck facing sunrise, hair and cloak blown by wind, the full landship behind her with crew silhouettes on deck — from protected child to leading guardian | Background | #1 full-bleed background with floating title | ai | Pending | Low-angle upward shot. Amiya stands at the deck's forward railing at center-right, body slightly leaning toward the sunrise. Golden morning light from the right horizon backlights her complete silhouette and flowing hair. Behind her, the full Rhodes Island deck spreads across the frame with crew member silhouettes scattered across the deck. Sky transitions from deep blue on the left to gold-orange at the horizon. Overall palette moves from cool to warm, left to right, echoing the full emotional arc — from darkness to hope. | none | hero_page |

---

## IX. Content Outline

### Part 1: Opening — Origin

#### P01 - Cover

- **Cover impact**: The girl who inherited a kingdom — hook through contradiction: a fourteen-year-old with rabbit ears is the most dangerous being on Terra. Full-bleed cover image of Amiya facing the viewer with the Rhodes Island landship behind her; title floats in the dark lower third.
- **Layout**: Full-bleed background image (#1) with floating title text in the lower portion over a dark scrim
- **Title**: 从被守护者到守护者
- **Subtitle**: 阿米娅 — 明日方舟的灵魂角色深度解读
- **Info**: 明日方舟深度研究 | 2026

#### P02 - Table of Contents

- **Layout**: Full-bleed background image (#1) with floating text overlay
- **Title**: 目录
- **Core message**: This deck traces Amiya's complete arc — from orphan to Demon King to the leader who chooses healing over destruction — across six narrative chapters.
- **Content**:
  - 01 起源 — 她不是你想象中的新手角色
  - 02 危机 — 感染者的现实与失去的重量
  - 03 觉醒 — 魔王之力与命运的抉择
  - 04 羁绊 — 连接两个世界的人
  - 05 身份 — 用画面讲故事的典范
  - 06 回响 — 社区、文化与永恒的回声

### Part 2: Act I — Origin

#### P03 - Transition: World Setting

- **Layout**: Full-bleed transition page (02_chapter.svg)
- **Title**: 起源
- **Core message**: Before understanding Amiya, you must understand the world she was born into — a world torn apart by Originium.
- **PREV_SECTION_LABEL**: 开场
- **PREV_SECTION_SUMMARY**: 这是你熟悉但可能从未真正了解过的那个女孩
- **CHAPTER_NUM**: 01
- **CHAPTER_TITLE**: 源石世界的重量
- **CHAPTER_DESC**: 源石是文明的基石也是诅咒——阿米娅的故事，从这片被撕裂的大地开始
- **NEXT_HOOK**: 但在理解她之前，我们需要先理解她所处的世界——一个被源石撕裂的世界

#### P04 - Content: Amiya's Origin

- **Layout**: Asymmetric split with image area (03_content.svg)
- **Title**: 一个14岁的兔族少女，继承了一整个文明的重量
- **Core message**: Amiya is not a generic starter character — she is the heir to the Sarkaz Demon King, carrying the memories, will, and power of an entire civilization.
- **Content**:
  - 她是游戏中唯一拥有三种职业形态的干员，从术师到近卫到医疗，每一次形态变化都对应着主线剧情中的关键转折
  - 她的E2提升会改变稀有度（5星→6星），这在全游戏中独一无二
  - 她体内流淌的不是单纯的卡特斯血脉，而是奇美拉（Chimera）——多种力量的融合体
  - 你以为她是吉祥物，但她是整个故事的脊梁

#### P05 - Content: Rhodes Island Role

- **Layout**: Asymmetric split with image area (03a_content.svg)
- **Title**: 药与剑——罗德岛的使命
- **Core message**: Rhodes Island is the last bastion for the Infected — a pharmaceutical company that is really a resistance movement, led by a teenage girl.
- **Content**:
  - 特蕾西娅死后，巴别塔被重组为罗德岛——表面是制药公司，实际上是感染者权益的最后堡垒
  - 阿米娅担任最高执政官，凯尔希担任医疗主管，博士是被阿米娅从冷冻舱中唤醒的战术指挥官
  - 源石既是泰拉文明运转的核心能源，也是这个世界最大的诅咒——矿石病无药可治
  - 阿米娅自身的矿石病细胞-源石融合率为19%，体表分布源石结晶，血液源石结晶密度0.27u/L

### Part 3: Act II — Crisis and Loss

#### P06 - Transition: Infected Crisis

- **Layout**: Full-bleed transition page (02_chapter.svg)
- **Title**: 危机
- **Core message**: The Infected face systemic discrimination, forced labor, and death — Amiya carries this entire crisis on young shoulders.
- **PREV_SECTION_LABEL**: 起源
- **PREV_SECTION_SUMMARY**: 阿米娅不是你想象中的新手角色——她承载着远超年龄的重量
- **CHAPTER_NUM**: 02
- **CHAPTER_TITLE**: 失去与觉醒之路
- **CHAPTER_DESC**: 天真在碎裂中被锻造为信念——阿米娅的成长，是用泪水和牺牲写成的
- **NEXT_HOOK**: 但这个使命如何变成一个14岁少女肩上的真实重量？答案在主线剧情里

#### P07 - Content: Skullshatterer / Misha

- **Layout**: Asymmetric split with image area (03_content.svg)
- **Title**: 善意无法拯救所有人
- **Core message**: Misha's death shattered Amiya's innocence — the first proof that good intentions are not enough in a world built on structural injustice.
- **Content**:
  - 碎骨（Skullshatterer）——米莎（Misha），一个阿米娅曾想要保护的感染者少女，最终选择了联合运动的暴力道路
  - 阿米娅被迫在战场上与米莎对峙，而米莎最终死去
  - 这是阿米娅第一次经历"善意无法拯救所有人"的残酷现实
  - 她的天真在这一刻开始碎裂

#### P08 - Content: FrostNova Tragedy

- **Layout**: Asymmetric split with image area (03a_content.svg)
- **Title**: 如果敌人和我们承受着同样的苦难
- **Core message**: FrostNova's death proved that enemies are not born evil — they are victims of the same oppressive system. Amiya wept, and her resolve deepened.
- **Content**:
  - 霜星（FrostNova）——爱国者的女儿，联合运动的精英战士——她的悲惨身世揭示了一个真相
  - 霜星在战斗中自我牺牲，阿米娅哭了——整个游戏中最具情感冲击力的场景之一
  - 阿米娅开始追问：如果敌人和我们承受着同样的苦难，那"战争"本身是否就是错误的？
  - 她从不妖魔化敌人——她记得每一个倒下者的名字

### Part 4: Act III — Awakening

#### P09 - Transition: Awakening

- **Layout**: Full-bleed transition page (02_chapter.svg)
- **Title**: 觉醒
- **Core message**: The real trial has not yet come — in Episode 8, Amiya will face the power sleeping inside her.
- **PREV_SECTION_LABEL**: 危机
- **PREV_SECTION_SUMMARY**: 阿米娅经历了失去、幻灭和泪水——从天真走向了对世界复杂性的认知
- **CHAPTER_NUM**: 03
- **CHAPTER_TITLE**: 魔王的苏醒
- **CHAPTER_DESC**: 在第八章的战场上，她从被保护的孩子蜕变为接受命运的领袖
- **NEXT_HOOK**: 但真正的考验还没有到来。在第八章，她将面对自己体内沉睡的力量

#### P10 - Content: Episode 8 Demon King

- **Layout**: Asymmetric split with image area (03_content.svg)
- **Title**: 拔出诅咒之剑的那一刻
- **Core message**: Episode 8 is Amiya's absolute narrative climax — she stops being a symbol and becomes a warrior-leader, accepting the Demon King's power as her own responsibility.
- **Content**:
  - 面对爱国者（Patriot）——乌萨斯传奇战士，常规战术失效，魔王之力在极限压力下觉醒
  - 她拔出诅咒之剑，释放出萨卡兹王族血统的全部力量——她短暂地失去了控制
  - 在精神领域中，她选择了接受——不是作为诅咒，而是作为自己主动承担的责任
  - 从"一个被保护的孩子"蜕变为"一个主动接受命运的领袖"

#### P11 - Content: Three Forms

- **Layout**: Asymmetric split with image area (03a_content.svg)
- **Title**: 蓝、黑、白——三种力量，一个完整的阿米娅
- **Core message**: Amiya's three class forms are not just gameplay mechanics — they are a narrative thesis about identity: power, combat, and compassion must coexist in a leader.
- **Content**:
  - 术师（蓝）：被保护的领导者——知识与潜力
  - 近卫（黑/紫）：拔剑而战的魔王继承者——力量与决断
  - 医疗（白）：选择治愈而非毁灭的温柔——牺牲与奉献
  - 终极技能「奇美拉」完美诠释了核心命题——巨大的力量必然伴随着巨大的代价

### Part 5: Interlude — Bonds

#### P12 - Transition: Relationships

- **Layout**: Full-bleed transition page (02_chapter.svg)
- **Title**: 羁绊
- **Core message**: A person cannot carry this weight alone — every relationship around Amiya shapes who she becomes.
- **PREV_SECTION_LABEL**: 觉醒
- **PREV_SECTION_SUMMARY**: 阿米娅在接受魔王之力后，从被保护者变成了真正的领袖
- **CHAPTER_NUM**: 04
- **CHAPTER_TITLE**: 连接两个世界的纽带
- **CHAPTER_DESC**: 从博士到陈晖洁，从凯尔希到每一个离去者——阿米娅的力量来自传承，但她的人格来自身边每一个人
- **NEXT_HOOK**: 但一个人不可能独自承担这样的重量——她身边的每一个人，都在塑造着她

#### P13 - Content: Doctor Bond

- **Layout**: Asymmetric split with image area (03_content.svg)
- **Title**: "如果是和您一起，我觉得，非常幸福"
- **Core message**: The Doctor is Amiya's emotional anchor — not a protector-child dynamic, but two people who share the weight of the world.
- **Content**:
  - 她为博士私下拉小提琴——"一首有些怀旧的曲子"
  - 她在演讲前紧张时请求博士握住她的手
  - 这不是简单的"角色对玩家的好感"——这是一个肩负着超越年龄重量的少女，对唯一能让她卸下防备之人的信任
  - "那些离去者的名字，我都记得"——她既是在确认自己的力量，也是在为自己可能吓到同伴而难过

#### P14 - Content: Ch'en Parallel

- **Layout**: Asymmetric split with image area (03a_content.svg)
- **Title**: 从对立到同盟——跨越偏见的镜像
- **Core message**: Amiya and Ch'en represent two paths confronting the same crisis — compassion versus order — and their convergence is the game's core message about bridging prejudice.
- **Content**:
  - 阿米娅代表感染者，陈代表统治阶层——她们从制度性冲突走向相互理解
  - 两人都背负着沉重的继承——阿米娅是萨卡兹王冠，陈是龙族血脉
  - "如果阿米娅出了什么事，我会来找你。这不是开玩笑。"——陈的保护欲
  - 她们的和解，就是这个游戏核心信息的缩影：跨越偏见

### Part 6: Act IV — Identity

#### P15 - Transition: Visual Identity

- **Layout**: Full-bleed transition page (02_chapter.svg)
- **Title**: 身份
- **Core message**: The changes inside Amiya are expressed through the genius of Arknights' visual design language.
- **PREV_SECTION_LABEL**: 羁绊
- **PREV_SECTION_SUMMARY**: 阿米娅的力量来自传承，但她的人格来自身边每一个人
- **CHAPTER_NUM**: 05
- **CHAPTER_TITLE**: 用画面讲故事的典范
- **CHAPTER_DESC**: 兔耳穿过兜帽——明日方舟最强大的品牌资产背后，是一整套精密的视觉叙事系统
- **NEXT_HOOK**: 而这些内在的变化，都被鹰角用极其精妙的视觉设计语言表达了出来

#### P16 - Content: Design Symbolism

- **Layout**: Asymmetric split with image area (03_content.svg)
- **Title**: 每一个设计元素都承载着叙事信息
- **Core message**: Amiya's visual design is not just aesthetically pleasing — every element encodes thematic meaning, from the hood to the crown to the three-color system.
- **Content**:
  - 标志性剪影：兔耳穿过兜帽——即使完全遮光也能一眼辨识
  - 五大符号体系：黑王冠（魔王继承）、魔王之剑（力量与决断）、兜帽（谦逊与隐藏）、指环（与特蕾西娅的羁绊）、源石结晶（感染与牺牲）
  - 三色设计语言：术师·蓝（知识与潜力）、近卫·黑紫（力量与决断）、医疗·白（治愈与奉献）
  - 设计师唯@W（原始立绘）和海猫（艺术总监）通过这套色彩语言，让角色成长直观地刻进了视觉记忆

#### P17 - Content: Community Impact

- **Layout**: Asymmetric split with image area (03a_content.svg)
- **Title**: 她不只是游戏角色——她是明日方舟本身
- **Core message**: Amiya transcends the game to become a cultural symbol — the "little donkey" nickname, fan art ecosystem, and emotional resonance prove she belongs to the community as much as to Hypergryph.
- **Content**:
  - 阿米娅是明日方舟的品牌符号本身——从Logo到周边，从周年庆到线下活动
  - "小驴"的爱称：看似调侃的昵称承载着玩家对这个角色的深厚感情，代表了玩家将她"去神话化"、视为家人般的亲切感
  - 第八章魔王觉醒被广泛认为是明日方舟剧情的巅峰时刻
  - 她既是"你（玩家）"的陪伴者，又拥有独立于玩家的完整人格——她的成长不是你的"升级"，而是她的故事

### Part 7: Closing

#### P18 - Ending

- **Closing impact**: From the ruins of Chernobog to the bow of the Rhodes Island — the girl who never stopped walking forward. Full-bleed image of Amiya at sunrise on the deck, facing the future she is building for everyone. The golden light closes the loop opened by the dark cover.
- **Layout**: Full-bleed background image (#1) with floating quote text over a dark scrim
- **Content**: "博士，我们的脚下，是一条漫长的道路......也许这是一次没有终点的旅行，但如果是和您一起，我觉得，非常幸福。" ——阿米娅

---

## X. Speaker Notes Requirements

One speaker note file per page, saved to `notes/`:

| Filename | Script Notes |
| -------- | ------------ |
| 01_cover.md | Hook: "Every Arknights player knows Amiya. But do you really know her?" Introduce the core contradiction — she looks like a mascot, but she is the narrative spine of the entire game. Pause for impact after the subtitle reveal. |
| 02_toc.md | Quick overview of the six-act structure. Set expectations: this is not a gameplay guide, it is a character deep-dive covering lore, story arc, design philosophy, and cultural impact. Transition smoothly into Act 1. |
| 02_chapter_01.md | Set the world-building tone. Emphasize Originium's dual nature as both civilization's foundation and its curse. Use the transitional hook to create anticipation for Amiya's personal story. Slow pacing, atmospheric delivery. |
| 03_content_amiya_origin.md | Present Amiya's identity revelation: "You think she is a mascot. She is the heir to the Demon King." Detail the Chimera nature, the unique triple-class mechanic as narrative device, and the 5-to-6 star promotion as story metaphor. Build surprise through layered reveals. |
| 03a_content_rhodes_island.md | Explain Rhodes Island as more than a game setting — it is the organizational embodiment of Amiya's mission. Introduce the Babel-to-RI lineage and the Civilight Eterna inheritance. Mention her infection rate (19%) as a concrete detail that grounds the abstract mission in personal stakes. |
| 02_chapter_02.md | Emotional pivot: shift from "who she is" to "what she has lost." Prepare the audience for the heaviest section of the deck. Slow pacing, empathetic delivery. |
| 03_content_skullshatterer.md | Deliver the Misha episode as Amiya's first loss of innocence. Emphasize the moral complexity — Misha was not evil, she was desperate. The lesson: good intentions are necessary but not sufficient. Moderate pacing with emotional weight. |
| 03a_content_frostnova.md | This is the emotional peak of the deck's middle section. FrostNova's death is one of gaming's most celebrated tragic moments. Deliver with gravity. Emphasize: Amiya wept — and crying was not weakness, it was moral clarity. Quote Amiya's refusal to dehumanize enemies. Allow a moment of silence after delivery. |
| 02_chapter_03.md | Energy shift: from grief to transformation. The audience has felt the weight of loss; now they will see what that weight produced. Build anticipation for the Demon King awakening. Faster pacing, forward momentum. |
| 03_content_demon_king.md | This is the narrative climax — Episode 8. Describe the Patriot confrontation with cinematic intensity. Emphasize the moment of choice: Amiya accepted the Demon King power not as fate but as responsibility. The "I am no longer a child who needs protection" line is the deck's emotional peak. Deliver with maximum intensity. |
| 03a_content_three_forms.md | Analytical shift after the emotional climax. Break down the three forms as a design thesis: blue/knowledge, black/purple/power, white/compassion. Explain Chimera skill as gameplay-story integration — true damage at the cost of HP mirrors the narrative cost of wielding Demon King power. Measured, insightful delivery. |
| 02_chapter_04.md | Transition from Amiya's inner growth to her external relationships. Frame: "A person cannot carry this alone." Prepare for a warmer, more intimate section. Gentle pacing. |
| 03_content_doctor_bond.md | The emotional core of the Doctor-Amiya relationship. Describe the violin scene, the hand-holding before speeches, the "very happy" line with tenderness. Emphasize: this is not a typical gacha game affection system — it is a genuine bond between two people who share impossible burdens. Intimate, quiet delivery. |
| 03a_content_chen_parallel.md | The Ch'en-Amiya dynamic as the game's thesis on prejudice. Explain the structural parallel: Infected leader meets authority enforcer, mutual growth ensues. Ch'en's protective threat ("I will come for you") shows she has crossed the empathy barrier. Analytical but warm delivery. |
| 02_chapter_05.md | Meta-narrative shift: now analyzing HOW Arknights tells Amiya's story through design. Frame: "The changes inside Amiya are written into her visual identity." Prepare for a more analytical, design-focused section. |
| 03_content_design_symbolism.md | Design analysis: rabbit ears through hood as brand anchor, five symbolic systems (crown, sword, hood, ring, crystals), three-color growth language. Credit to artist 唯@W and art director 海猫. This page rewards the audience's visual literacy — they have been seeing these symbols all along without fully decoding them. |
| 03a_content_community_impact.md | Close the content arc with community impact. The "little donkey" nickname as cultural evidence. Emphasize: Amiya is not just a Hypergryph product — she belongs to the global community. Fan art, cosplay, lore discussion — all prove she has transcended the screen. Celebratory, inclusive tone. |
| 04_ending.md | Final page. Slow, deliberate delivery. Read the Amiya quote in full — "our feet stand on a long road... maybe a journey without end, but if it is with you, Doctor, I feel very happy." Let the silence after the quote carry the weight. The deck's thesis: Amiya teaches us not how to become stronger, but how to remain gentle while becoming strong. End with the sunrise metaphor — from darkness to hope. |

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. Text characters: write typography & symbols as raw Unicode (em dash `—`, en dash `–`, `©`, `®`, `→`, NBSP, etc.); HTML named entities (`&nbsp;`, `&mdash;`, `&copy;`, `&reg;` …) are FORBIDDEN. XML reserved chars in text MUST be escaped as `&amp;` `&lt;` `&gt;` `&quot;` `&apos;`
8. `marker-start` / `marker-end` conditionally allowed: `<marker>` must be in `<defs>`, `orient="auto"`, shape must be triangle / diamond / circle
9. `clipPath` conditionally allowed **only on `<image>` elements**: `<clipPath>` in `<defs>`, single shape child (circle / ellipse / rect with rx,ry / path / polygon)

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN (group opacity); set on each child element individually
- Image transparency uses overlay mask layer (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only; external CSS and `@font-face` FORBIDDEN
