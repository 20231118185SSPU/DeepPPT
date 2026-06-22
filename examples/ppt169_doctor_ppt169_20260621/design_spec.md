# 博士：面具之下的幽灵 — Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline. Read once by downstream roles for context.
>
> Machine-readable execution contract: `spec_lock.md` (color / typography / icon / image short form). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep both in sync; on divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | ppt169_doctor_ppt169_20260621 |
| **Canvas Format** | PPT 16:9 (1280x720) |
| **Page Count** | 26 |
| **Design Style** | Custom — dark military/mystery (crimson-charcoal) |
| **Target Audience** | 明日方舟玩家与深度剧情爱好者，特别是对角色叙事、世界观构建、游戏设计哲学感兴趣的核心用户 |
| **Use Case** | 角色深度解读展示，适用于专题分享、社区内容创作、剧情解析讲座 |
| **Content Strategy** | 以研究报告为叙事骨架，保留所有核心论证与引用，将长篇散文拆解为视觉优先的逐页叙事。每个章节对应两到三页：AI生成氛围图作为情绪锚点，web素材展示真实游戏资产与官方视觉。深潜页面（Deep Dive）展开报告中被压缩的六个专题细节。 |
| **Created Date** | 2026-06-21 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280x720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top 50px, bottom 60px |
| **Content Area** | 1160 x 610 (x=60..1220, y=50..660) |

---

## III. Visual Theme

### Theme Style

- **Mode**: narrative — 线性叙事驱动，从开场钩子到结论逐步展开博士的多维身份
- **Visual style**: custom — dark military/mystery; 深色基调为主，选择性亮色（crimson）切割近黑背景，半写实暗黑奇幻风格，高对比度，强调孤寂与神秘感
- **Theme**: Dark theme
- **Tone**: 神秘、冷峻、克制、电影感

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#1C1C1C` | 页面背景 — 博士兜帽内侧的炭黑色 |
| **Secondary bg** | `#252525` | 卡片背景、区块背景 — 深灰面板 |
| **Primary** | `#8B1A1A` | 标题装饰、关键区块、图标 — 深红，兜帽内衬之红、特蕾西娅之血 |
| **Accent** | `#C0C0C0` | 数据高亮、关键信息 — 银色，战术装备、遗忘科技的冷光 |
| **Secondary accent** | `#5A5A5A` | 次要强调、渐变过渡 — 暗灰 |
| **Body text** | `#E8E8E8` | 正文主文字 — 浅灰 |
| **Secondary text** | `#A0A0A0` | 说明文字、注释 — 中灰 |
| **Tertiary text** | `#707070` | 补充信息、页脚 — 暗灰 |
| **Border/divider** | `#3A3A3A` | 卡片边框、分隔线 |
| **Success** | `#4A7C59` | 正向指标（少量使用） |
| **Warning** | `#B85450` | 问题标记（少量使用） |

### AI Image Strategy

- **Image Rendering**: custom
- **Image Rendering Behavior**: 半厚涂暗黑奇幻风格（semi-realistic dark fantasy），高对比度，选择性crimson亮色穿透近黑背景，类似Arknights官方CG的质感——厚重的暗部、锐利的边缘光、戏剧性布光。避免纯平涂或扁平矢量风格。
- **Image Palette**: custom
- **Image Palette Behavior**: 以#1C1C1C炭黑为基底约占60%画面，#8B1A1A深红作为选择性高光约15%（武器边缘、能量源、血迹、兜帽内衬），#C0C0C0银灰作为冷调补光约15%（战术界面、金属表面、记忆碎片），其余10%为冷蓝（石棺光芒、医疗舱光源）和暖金（特蕾西娅记忆、遗书文字）。第四色仅在特定页面使用，不作为deck-wide颜色。

### Gradient Scheme

```xml
<!-- Title gradient — deep crimson to silver -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#8B1A1A"/>
  <stop offset="100%" stop-color="#C0C0C0"/>
</linearGradient>

<!-- Background decorative gradient (rgba forbidden, use stop-opacity) -->
<radialGradient id="bgDecor" cx="80%" cy="20%" r="50%">
  <stop offset="0%" stop-color="#8B1A1A" stop-opacity="0.12"/>
  <stop offset="100%" stop-color="#8B1A1A" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: 现代中文无衬线 + 冷峻感

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Source Han Sans SC"`, `"Microsoft YaHei"` | — | `sans-serif` |
| **Body** | `"Microsoft YaHei"` | `Arial` | `sans-serif` |
| **Emphasis** | `"Microsoft YaHei"` | `Arial` | `sans-serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `"Source Han Sans SC", "Microsoft YaHei", sans-serif`
- Body: `"Microsoft YaHei", Arial, sans-serif`
- Emphasis: `"Microsoft YaHei", Arial, sans-serif` (same as Body)
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 20px

| Purpose | Ratio to body | Actual px | Weight |
| ------- | ------------- | --------- | ------ |
| Cover title (hero headline) | 3x | 60px | Bold |
| Chapter / section opener | 2.4x | 48px | Bold |
| Page title | 1.6x | 32px | Bold |
| Subtitle | 1.3x | 26px | SemiBold |
| **Body content** | **1x** | **20px** | Regular |
| Annotation / caption | 0.75x | 15px | Regular |
| Page number / footnote | 0.6x | 12px | Regular |
| Transition large quote | 1.5x | 30px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: y=40..100, 含章节指示标签（13px tertiary text）+ 页面标题（32px bold primary text）+ 装饰线
- **Content area**: y=110..620, 核心内容区域，含AI图/web素材 + 文字内容
- **Footer area**: y=640..720, 页码 + 来源标注

### Layout Pattern Library

本deck以单列全幅图+浮动文字为主体结构，穿插对比卡片和数据区块：

| Pattern | Suitable Scenarios |
| ------- | ----------------- |
| **Full-bleed + floating text** | 氛围页、过渡页 — AI图铺满背景，文字叠加半透明遮罩 |
| **Asymmetric split (3:7)** | 内容页 — 左侧文字+数据，右侧AI图或web素材 |
| **Single column centered** | 开场钩子、引言页 — 大字号居中 + 简短文字 |
| **Three column cards** | 关系网页、对比页 — 并排卡片展示多个人物/概念 |
| **Negative-space-driven** | 引言页、关键台词页 — 单句大字 + 大面积留白 |

### Spacing Specification

**Universal**:

| Element | Current Project |
| ------- | --------------- |
| Safe margin from canvas edge | 60px |
| Content block gap | 28px |
| Icon-text gap | 10px |

**Card-based layouts**:

| Element | Current Project |
| ------- | --------------- |
| Card gap | 24px |
| Card padding | 24px |
| Card border radius | 10px |
| Single-row card height | 560px |
| Double-row card height | 270px each |
| Three-column card width | 370px each |

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `templates/icons/`
- **Usage method**: SVG placeholder `<use data-icon="library/icon-name" .../>`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 章节标记 | `chunk-filled/hexagon` | P02 (TOC items) |
| 战术标记 | `chunk-filled/crosshair` | P09, P10 |
| 关系连接 | `chunk-filled/link` | P12, P13 |
| 面具/身份 | `chunk-filled/eye` | P15, P16 |
| 社区/讨论 | `chunk-filled/users` | P18 |
| 前文明 | `chunk-filled/clock` | P04, P05 |
| 失忆/记忆 | `chunk-filled/lock` | P07 |
| 棋局/策略 | `chunk-filled/target` | P10 |

---

## VII. Visualization Reference List

本deck不使用chart-library模板可视化。所有数据展示（gacha主角对比表、关系图谱）由Executor自行设计。选手对比数据（P17）使用自制散点图/表格。

---

## VIII. Image Resource List

> Deep-dive页面（P06, P08, P14, P17, P19, P25）使用预置web素材，不需要AI生成。

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| cover_bg.png | 1280x720 | 16:9 | 封面氛围背景 — 蒙面人物站在石棺前，冷蓝色光芒，罗德岛舰桥暗色轮廓 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | 神秘蒙面人物站在发光石棺前，身后暗色舰桥剪影，低地平线，冷蓝主光源，斗篷轻微飘动 | none | hero_page |
| toc_bg.png | 1280x720 | 16:9 | 目录页氛围背景 — 泰拉大陆地图碎片与节点标记 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | 地图碎片散落，关键节点以光点散布，红色连接线以博士为中心辐射，暗色调 | none | hero_page |
| trans_01_hook.png | 1280x720 | 16:9 | 过渡页01 — 蒙面人形轮廓与星辰微光 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | 黑暗中蒙面人形轮廓，面具反射星辰微光，脚下破碎全息碎片飘散，极度特写 | none | hero_page |
| content_precursor.png | 1280x720 | 16:9 | §2 前文明设施内部 — 全息星图与博士/普瑞赛斯剪影 | Illustration | #44 background image + native diagram | ai | Pending | 巨大全息星图悬浮，博士剪影在左，柔和光晕（普瑞赛斯）在右，红色航线标注星图 | none | local |
| content_sarcophagus.png | 1280x720 | 16:9 | §2 石棺 — 前文明废弃设施中舱门微开的石棺 | Illustration | #44 background image + native diagram | ai | Pending | 石棺居中，冷蓝光从舱门缝隙涌出，周围倒塌全息屏幕和时间结晶废墟 | none | local |
| trans_02_awakening.png | 1280x720 | 16:9 | 过渡页02 — 石棺舱门打开，白雾涌出 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | 第一人称视角从石棺内向外看，舱门形成画框，白雾从下方涌出，模糊人影在光亮中 | none | hero_page |
| content_amnesia.png | 1280x720 | 16:9 | §3 博士第一人称 — 阿米娅面孔从模糊渐清晰 | Illustration | #44 background image + native diagram | ai | Pending | 第一人称视角，阿米娅面孔居中唯一清晰区域，周围失焦处理，画面边缘色散效果 | none | local |
| trans_03_fragments.png | 1280x720 | 16:9 | 过渡页03 — 记忆碎片悬浮，能力完整 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | 破碎记忆碎片从中央向外辐射悬浮，每块碎片映着模糊场景，背景纯黑 | none | hero_page |
| content_tactics.png | 1280x720 | 16:9 | §4 战术指挥 — 博士手在全息地图上指点 | Illustration | #44 background image + native diagram | ai | Pending | 俯瞰视角，戴手套的手指点全息战术地图，箭头和战术符号标注，干员虚影分布边缘 | none | local |
| content_chessboard.png | 1280x720 | 16:9 | §4 棋局隐喻 — 悬浮棋盘与博士落子 | Illustration | #44 background image + native diagram | ai | Pending | 巨大棋盘斜置画面上方，棋子为各势力符号，博士剪影在右下落子，背景远处燃烧城市 | none | local |
| trans_04_mirror.png | 1280x720 | 16:9 | 过渡页04 — 博士面对破碎镜子 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | 博士背对观众面向破碎镜子，碎片映着不同角色面孔，红色光从裂缝透出 | none | hero_page |
| content_relationships.png | 1280x720 | 16:9 | §5 三联画 — 凯尔希/阿米娅/特蕾西娅关系并置 | Illustration | #44 background image + native diagram | ai | Pending | 三等分画面，左侧凯尔希背对（冷蓝），中央阿米娅手拉手（暖金），右侧特蕾西娅遗像（银），暗色丝线连接 | none | local |
| content_theresa_letter.png | 1280x720 | 16:9 | §5 特蕾西娅遗书 — 金色文字浮现黑暗 | Illustration | #44 background image + native diagram | ai | Pending | 纯黑背景，遗书手写体金色光线文字居中偏上，博士剪影在下方伸手无法触碰，'家'字最亮 | none | local |
| trans_05_mask.png | 1280x720 | 16:9 | 过渡页05 — 博士面具特写，表面反射多张面孔 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | 极度特写面具占画面中央70%，表面反射多个角色面孔，边缘裂痕透暗红光 | none | hero_page |
| content_five_layers.png | 1280x720 | 16:9 | §6 五层面具 — 同心圆解构设计哲学 | Diagram | #44 background image + native diagram | ai | Pending | 博士面具剪影居中，五层同心圆从外到内展开（代入/谜团/普遍性/隐藏知识/NPC异化），每层不同深浅红色 | none | local |
| content_self_insert.png | 1280x720 | 16:9 | §6 gacha主角对比 — 博士在设计谱系中的位置 | Diagram | #44 background image + native diagram | ai | Pending | 三角形散点图，X轴'过去信息量'，Y轴'代入感'，博士在多过去/低代入角，连线红色虚线 | none | local |
| content_community.png | 1280x720 | 16:9 | §7 社区文化 — 万千面孔投射到面具上 | Illustration | #44 background image + native diagram | ai | Pending | 博士面具居中，周围同心圆排列无数小面孔投影，面具为所有面孔汇聚焦点，银灰暗红色调 | none | local |
| content_ships.png | 1280x720 | 16:9 | §7 博士配对图谱 — 四条光线连接四人 | Diagram | #44 background image + native diagram | ai | Pending | 博士在中央，四条不同颜色光线向外延伸连接阿米娅/凯尔希/W/普瑞赛斯剪影 | none | local |
| ending_stars.png | 1280x720 | 16:9 | 结论 — 面具之下是星空 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | 博士双手举起面具，下方露出宇宙星空而非面孔，泰拉大陆轮廓在星空中可见 | none | hero_page |
| ending_walk.png | 1280x720 | 16:9 | 尾声 — 博士背影走向地平线 | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | 博士背影在画面底部三分之一走向地平线，罗德岛轮廓左侧，阿米娅舰桥目送，底部金色手写字'家' | none | hero_page |

---

## IX. Content Outline

### Part 1: 开场 (P01-P03)

#### Slide 01 - Cover

- **Cover impact**: 博士的石棺苏醒瞬间——蒙面人物背对观众面对发光石棺，冷蓝光从缝隙中涌出照亮黑暗，暗示万年沉睡后的孤独苏醒。构图：全幅AI图 + 浮动标题叠加两层遮罩。
- **Layout**: Full-bleed AI background + floating centered title block with scrim overlay
- **Title**: 面具之下的幽灵
- **Subtitle**: 明日方舟博士深度解读
- **Info**: 深度研究报告 · 2026
- **Image source**: AI (cover_bg.png)

#### Slide 02 - TOC

- **Layout**: Full-bleed AI background + floating TOC items
- **Title**: 目录
- **Content**:
  - 01 开场钩子 — 一个没有名字的人
  - 02 前文明的幽灵 — 万年前的遗物
  - 03 苏醒与失忆 — 石棺开启之后
  - 04 战术天才的悖论 — 记忆空白，能力完整
  - 05 关系网 — 恨与保护的编织
  - 06 面具之下 — 设计哲学
  - 07 社区与文化 — 面具上的万千面孔
  - 08 结论 — 面具之下的空
- **Image source**: AI (toc_bg.png)

#### Slide 03 - Transition: Hook to Precursor

- **承上**: 博士是谁？一个没有记忆却被所有人记住的人
- **启下**: 但在理解他为什么失去记忆之前，我们需要知道他在失去记忆之前，究竟是什么
- **Layout**: Full-bleed AI background + top/bottom text blocks with scrim
- **Image source**: AI (trans_01_hook.png)

---

### Part 2: 前文明的幽灵 (P04-P06)

#### Slide 04 - Content: 前文明起源

- **Layout**: Asymmetric split (3:7) — 左侧文字，右侧AI图
- **Title**: 上一个文明的遗物
- **Core message**: 博士不属于当前泰拉文明，他属于前文明——一个拥有远超当前时代科技水平的失落文明。
- **Content**:
  - 博士的种族档案充满空白和问号——这不是信息缺失，而是刻意的叙事选择
  - 前文明创造了源石（Originium），建造了石棺冷冻系统，留下了生物机械造物
  - "方舟计划"（Project Ark）——博士在前文明时代参与的重大项目，与源石本质和泰拉命运密切相关
- **Image source**: AI (content_precursor.png)

#### Slide 05 - Content: 石棺与普瑞赛斯

- **Layout**: Asymmetric split (3:7) — 左侧文字，右侧AI图
- **Title**: 方舟计划与普瑞赛斯
- **Core message**: 普瑞赛斯是博士记忆中最深层的谜团——一个可能亲手将博士放入石棺的前文明同伴。
- **Content**:
  - 石棺（Sarcophagus）：博士沉睡万年的冷冻保存装置
  - 普瑞赛斯（Priestess）：前文明核心成员，与博士共同推进方舟计划
  - 她的名字是少数能让凯尔希失去冷静的词语之一——暗示前文明时代的三角关系
- **Image source**: AI (content_sarcophagus.png)

#### Slide 06 - Deep Dive: 前文明完整设定

- **Layout**: Full-bleed web asset background + floating text overlay
- **Title**: [Deep Dive] 前文明完整设定
- **Core message**: 前文明的科技树、源石起源理论、石棺技术原理与"大崩溃"事件时间线。
- **Content**:
  - 源石起源：前文明创造的万能能源，同时是矿石病的根源
  - 方舟计划：前文明为应对大崩溃制定的"人类种子计划"
  - 石棺技术：冷冻保存系统，博士在其中沉睡超过万年
  - 凯尔希与Mon3tr：同属前文明遗存的证据链
- **Web asset**: `dim2_sarcophagus_interior.png` — 石棺内部场景，展示冷冻保存装置的真实游戏视觉
- **Image source**: web_asset (dim2_sarcophagus_interior.png)

---

### Part 3: 苏醒与失忆 (P07-P08)

#### Slide 07 - Content: 博士苏醒

- **Layout**: Asymmetric split (4:6) — 左侧文字，右侧AI图
- **Title**: 你什么都回忆不起来
- **Core message**: 博士从石棺中苏醒，完全失忆——不是记忆模糊，是彻底的、完全的空白。
- **Content**:
  - Episode 0开场：博士从石棺中苏醒，第一个看到的是阿米娅
  - 阿米娅的第一句话是"博士"——一个你还不配拥有的名字
  - 凯尔希的反应是冰冷的审视，她的措辞暗示她知道更多
  - 失忆可能是自愿的——一种为了逃避过去所做的选择
- **Image source**: AI (content_amnesia.png)

#### Slide 08 - Deep Dive: 特蕾西娅之死上下文

- **Layout**: Asymmetric split (3:7) — 左侧文字，右侧web素材
- **Title**: [Deep Dive] 特蕾西娅之死
- **Core message**: 博士在萨卡兹内战中做出了导致特蕾西娅死亡的决定——这是所有关系链的原点。
- **Content**:
  - 萨卡兹内战背景：卡兹戴尔的权力斗争
  - 博士的决策逻辑：被迫还是主动？凯尔希的道德审判不接受"被迫"为"无罪"
  - 特蕾西娅遗书："我希望罗德岛能成为你命名的家"
  - W的称呼——"凶手"：最直言不讳的审判者
- **Web asset**: `dim4_theresa.png` — 特蕾西娅官方视觉素材
- **Image source**: web_asset (dim4_theresa.png)

---

### Part 4: 战术天才的悖论 (P09-P11)

#### Slide 09 - Content: 失忆与能力的分离

- **Layout**: Full-bleed AI background + floating text blocks
- **Title**: 失忆抹不去的能力
- **Core message**: 记忆可以被清空，但战术直觉不能——博士的"如何思考"从未被触及。
- **Content**:
  - 苏醒后仍然拥有最出色的战术指挥能力
  - 杜宾教官的评价：博士的战术水平不是"学习"出来的
  - 两层来源：前文明知识积淀内化为本能 + 不被源石技艺思维框架束缚
- **Image source**: AI (content_tactics.png)

#### Slide 10 - Content: 棋局隐喻

- **Layout**: Asymmetric split (4:6) — 左侧文字，右侧AI图
- **Title**: 棋局隐喻
- **Core message**: 博士的战术不是已知规则的对弈，而是发明规则后在规则之内碾压对手。
- **Content**:
  - 棋局隐喻：不是国际象棋，而是你发明规则的游戏
  - 阿米娅的盲目信任："无论多么艰难的任务，只要有博士在，就一定能完成"
  - 游戏机制的设计哲学：玩家本身就是博士，每一次作战都是博士的战术指挥
- **Image source**: AI (content_chessboard.png)

#### Slide 11 - Deep Dive: 塔防玩法与叙事映射

- **Layout**: Asymmetric split (3:7) — 左侧文字，右侧web素材
- **Title**: [Deep Dive] 战术指挥的游戏机制
- **Core message**: 明日方舟的塔防玩法是博士"战术天才"的亲身体验——机制即叙事。
- **Content**:
  - 每一次作战部署 = 博士的战术指挥
  - 高难度关卡通过 = 博士天才的玩家亲自证明
  - 博士不出现在战场 = 指挥者永远在后方
  - 杜宾教官的教学 = 博士能力的NPC侧写
- **Web asset**: `dim3_tactical_command.png` — 游戏内战术指挥界面
- **Image source**: web_asset (dim3_tactical_command.png)

---

### Part 5: 关系网 (P12-P15)

#### Slide 12 - Transition: Tactics to Relationships

- **承上**: 博士的战术能力不受失忆影响——前文明知识已内化为本能
- **启下**: 但能力再强，博士也只是一个被关系网束缚的人——而这张网的每一根线都通向痛苦
- **Layout**: Full-bleed AI background + top/bottom text blocks
- **Image source**: AI (trans_04_mirror.png)

#### Slide 13 - Content: 凯尔希与阿米娅

- **Layout**: Two-column split (5:5) — 左侧凯尔希，右侧阿米娅
- **Title**: 恨与保护的编织
- **Core message**: 凯尔希恨博士但保护他，阿米娅信任博士并将他视为情感锚点——两种截然相反的情感纽带同时存在。
- **Content**:
  - 凯尔希："我将永远恨他们" — 但她会在攻击时站在博士身前
  - 这不是信任，是特蕾西娅遗愿下的自我施加职责
  - 阿米娅："如果是和您一起，我觉得，非常幸福"
  - 一个肩负超越年龄重量的少女，对唯一能让她卸下防备之人的信任
- **Image source**: AI (content_relationships.png)

#### Slide 14 - Content: 特蕾西娅的遗书

- **Layout**: Negative-space-driven — 大面积暗色 + 金色遗书文字浮出
- **Title**: 特蕾西娅的幽灵
- **Core message**: 特蕾西娅的遗书说"我希望罗德岛能成为你命名的家"——被特蕾西娅信任的人，正是杀了她的人。
- **Content**:
  - "我希望罗德岛能成为你命名的家"
  - 这里的"你"指的是博士——被特蕾西娅信任的人，即使那个人杀了她
  - 博士伸手却无法触碰——永远隔着一层无法跨越的距离
- **Image source**: AI (content_theresa_letter.png)

#### Slide 15 - Quote Page: 凯尔希的审判

- **Layout**: Single column centered — 大字号引言 + 暗色背景
- **Title**: 凯尔希的话
- **Core message**: 凯尔希将博士的失忆称为一种"逃避"——不是医学判断，而是道德审判。
- **Content**:
  - "你什么都回忆不起来。"——阿米娅
  - "博士可能永远无法恢复记忆。"——凯尔希
  - 在凯尔希看来，失忆不是解脱，是另一种形式的背叛
- **Image source**: AI (背景使用crimson渐变 + 纹理，无需独立AI图)

---

### Part 6: 面具之下 (P16-P19)

#### Slide 16 - Transition: Design Philosophy

- **承上**: 博士被恨、被保护、被信任、被审判——关系网的每一根线都通向特蕾西娅之死
- **启下**: 但在所有谜团之上，还有一个更表面却同样深邃的问题——为什么我们永远看不到博士的脸？
- **Layout**: Full-bleed AI background + top/bottom text blocks
- **Image source**: AI (trans_05_mask.png)

#### Slide 17 - Content: 五层面具

- **Layout**: Center-radiating — 同心圆解构 + 浮动文字注释
- **Title**: 五层面具
- **Core message**: 博士的面具和兜帽承载着五层设计含义——从玩家代入到NPC异化，每层都服务于叙事。
- **Content**:
  - 第一层：玩家代入 — 任何种族、性别、外貌的人都可以是博士
  - 第二层：叙事谜团 — 面孔是身份最直接的标识，遮住面孔 = 失忆的视觉符号
  - 第三层：普遍性 — 博士不属于任何特定种族或文化
  - 第四层：隐藏的知识 — 面具之下是万年记忆和方舟计划的秘密
  - 第五层：NPC设计异化 — "反立绘"效果越看不见越好奇
- **Image source**: AI (content_five_layers.png)

#### Slide 18 - Content: 糟糕的自我插入角色

- **Layout**: Asymmetric split (4:6) — 左侧文字/数据，右侧AI图
- **Title**: 糟糕的自我插入角色
- **Core message**: 博士是gacha主角设计中最极端的案例——过去信息量最大，但通过失忆机制强行制造代入空间。
- **Content**:
  - 传统gacha：空白画布 → 所有角色示好
  - 博士打破模式：太多过去，无法简单视为"玩家容器"
  - 但又被强制套入自我插入框架：无声音、无独立行动
  - 对比：FGO藤丸立香（极少过去/极高代入）vs 博士（极多过去/中等偏低代入）
- **Image source**: AI (content_self_insert.png)

#### Slide 19 - Deep Dive: 面具设计五层与gacha谱系

- **Layout**: Asymmetric split (3:7) — 左侧文字，右侧web素材
- **Title**: [Deep Dive] 面具设计与角色谱系
- **Core message**: 博士面具设计的五层理论与gacha主角设计谱系的系统对比分析。
- **Content**:
  - 面具 = 镜子：反射每个注视者的想象
  - 兜帽 = 茧：包裹从一个时代到另一个时代的蜕变
  - 石棺 = 子宫/坟墓：同一个容器中的死亡与重生
  - 性别模糊：官方从未指定博士性别，服务于"不属于任何分类"的核心设定
- **Web asset**: `dim6_doctor_concept.jpg` — 博士概念设计图
- **Image source**: web_asset (dim6_doctor_concept.jpg)

---

### Part 7: 社区与文化 (P20-P23)

#### Slide 20 - Content: 社区理论构建

- **Layout**: Three-column cards — 平行展示主流社区理论
- **Title**: 面具上的万千面孔
- **Core message**: 博士是明日方舟社区中讨论量最大、分歧最多、共识最少的角色——每个人在面具上看到不同的脸。
- **Content**:
  - "博士是前文明的执政官" — 方舟计划是"人类种子计划"
  - "失忆是自愿的" — 博士在杀死特蕾西娅后主动清除记忆
  - "博士与普瑞赛斯是同一人" — 同一意识的两个投射
  - "石棺不止一个" — 前文明可能埋设了多个石棺
- **Image source**: AI (content_community.png)

#### Slide 21 - Content: 同人创作与配对

- **Layout**: Asymmetric split (4:6) — 左侧文字/列表，右侧AI图
- **Title**: 博士配对图谱
- **Core message**: 博士与其他角色的配对在社区中极其活跃——每段关系都映射着博士身份的一个侧面。
- **Content**:
  - 博士×阿米娅：信赖与依赖，最"官方暗示"
  - 博士×凯尔希：恨与保护的极端张力，"互相折磨"
  - 博士×W：凶手与追杀者的危险吸引力
  - 博士×普瑞赛斯：被遗忘的爱，跨越万年的牵绊
- **Image source**: AI (content_ships.png)

#### Slide 22 - Deep Dive: 社区理论深度分析

- **Layout**: Asymmetric split (3:7) — 左侧文字，右侧web素材
- **Title**: [Deep Dive] 社区理论与争议
- **Core message**: 围绕博士身份的社区理论网络——NGA、Reddit、Bilibili三大平台的分析焦点与核心争议。
- **Content**:
  - NGA：前文明执政官理论的系统性论证
  - Reddit：Doctor as terrible self-insert的跨文化讨论
  - Bilibili：剧情解析视频中的可视化时间线重构
  - 鹰角的叙事策略：每一条新线索同时增加答案和问题
- **Web asset**: `dim6_doctor_full_art.png` — 博士完整立绘，社区讨论核心视觉素材
- **Image source**: web_asset (dim6_doctor_full_art.png)

#### Slide 23 - Quote Page: 社区评价

- **Layout**: Single column centered — 大字号引言 + 暗色背景
- **Title**: 一句话
- **Core message**: "博士是一个糟糕的自我插入角色"——这个评价精准捕捉了博士的设计悖论，也恰恰说明了他为什么出色。
- **Content**:
  - "terrible self-insert" — 社区对博士最著名的评价
  - 过去信息量最大，但代入空间仍然存在
  - 矛盾不矛盾——它们是同一枚硬币的两面
- **Image source**: AI (背景使用crimson渐变 + 纹理，无需独立AI图)

---

### Part 8: 结论 (P24-P26)

#### Slide 24 - Transition: Final

- **承上**: 博士在社区中引发无数理论、同人创作与配对讨论
- **启下**: 最终，面具之下究竟是什么？
- **Layout**: Full-bleed AI background + centered text
- **Image source**: AI (复用trans_05_mask.png或ending_stars.png)

#### Slide 25 - Deep Dive: 普瑞赛斯-博士-凯尔希三角关系

- **Layout**: Asymmetric split (3:7) — 左侧文字，右侧web素材
- **Title**: [Deep Dive] 前文明三角关系
- **Core message**: 凯尔希、博士与普瑞赛斯之间存在未被揭示的前文明三角关系——跨越万年仍在这个时代投下阴影。
- **Content**:
  - 普瑞赛斯与博士：方舟计划的共同推进者，可能的亲密关系
  - 凯尔希的反应：听到"Priestess"时短暂失去冰冷面具
  - 三角关系的当代映射：凯尔希恨博士的根源可能不只是特蕾西娅之死
  - 记忆碎片中的温暖 vs 现实中的冰冷审视
- **Web asset**: `dim6_doctor_priestess.png` — 普瑞赛斯视觉素材
- **Image source**: web_asset (dim6_doctor_priestess.png)

#### Slide 26 - Ending

- **Closing impact**: 面具之下是空的，但正是这份空，让每一个人在其中看到了不同的脸——博士证明了一种角色设计的可能性：空白画布与惊天过往可以共存。
- **Layout**: Full-bleed AI background + centered closing text
- **Title**: 面具之下的空
- **Content**:
  - 他没有面孔，所以每个人都能在面具上看到自己
  - 他没有记忆，所以每一次选择都是全新的开始
  - "博士，无论发生什么，我都会在您身边。" ——阿米娅
- **Image source**: AI (ending_stars.png)

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
7. Text characters: write typography & symbols as raw Unicode (em dash `—`, en dash `–`, `©`, `®`, `→`, NBSP, etc.); HTML named entities (`&nbsp;`, `&mdash;`, `&copy;`, `&reg;` …) are FORBIDDEN. XML reserved chars in text MUST be escaped as `&amp;` `&lt;` `&gt;` `&quot;` `&apos;` (e.g. `R&amp;D`, `error &lt; 5%`). See shared-standards.md §1.0
7. `marker-start` / `marker-end` conditionally allowed: `<marker>` must be in `<defs>`, `orient="auto"`, shape must be triangle / diamond / circle (see shared-standards.md §1.1)
8. `clipPath` conditionally allowed **only on `<image>` elements**: `<clipPath>` in `<defs>`, single shape child (circle / ellipse / rect with rx,ry / path / polygon). Do NOT apply to shapes / groups / text — draw the target geometry directly with the matching native element (`<circle>` / `<ellipse>` / `<rect rx>` / `<polygon>` / `<path>`). See shared-standards.md §1.2

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN (group opacity); set on each child element individually
- Image transparency uses overlay mask layer (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only; external CSS and `@font-face` FORBIDDEN
