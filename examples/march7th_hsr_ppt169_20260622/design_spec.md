# 三月七——冰封记忆中的少女 — Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline.
>
> Machine-readable execution contract: `spec_lock.md`. Executor re-reads `spec_lock.md` before every SVG page. Keep both in sync; on divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | 三月七——冰封记忆中的少女 |
| **Canvas Format** | PPT 16:9 (1280x720) |
| **Page Count** | 24 |
| **Design Style** | story_driven x watercolor x narrative |
| **Target Audience** | 崩铁玩家 / 二次元爱好者，对星穹铁道角色有一定了解 |
| **Use Case** | 角色深度解读 PPT，围绕三月七的身世、设计、战斗、版本、文化五个维度展开叙事 |
| **Content Strategy** | 深度调研驱动——每章一个内容页 + 1-2 个讲解页，过渡页承上启下，金句页情感锚点 |
| **Layout Template** | story_driven（冰霜白浅色适配） |
| **Rendering Style** | watercolor（水彩手绘风，呼应二次元审美） |
| **Palette** | earthy-dusty（适配粉蓝白主色调） |
| **Created Date** | 2026-06-22 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280 x 720 px |
| **viewBox** | `0 0 1280 720` |
| **Margins** | Left/right 60px, top 40px, bottom 40px |
| **Content Area** | x: 60-1220, y: 40-680 |

---

## III. Visual Theme

### Theme Style

- **Mode**: `narrative` — 叙事驱动模式，故事线贯穿全篇，每页承载一个叙事节点
- **Visual style**: story_driven template layout（冰霜白浅色适配）
- **Theme**: Light theme — 冰霜白 #F8F4F0 为基底
- **Tone**: 温暖、梦幻、青春、带有淡淡忧伤的身世悬念

### Color Scheme

基于三月七角色视觉 DNA 提取：粉色（活力甜美）+ 冰蓝（冰属性纯净）+ 紫挑染（神秘点缀）+ 白色（冰/雪基底）。

| Role | HEX | Name | Purpose |
| ---- | --- | ---- | ------- |
| **Primary** | `#D4789C` | 三月七粉 | 标题装饰、关键区块、角色主色 |
| **Secondary** | `#7EB8D8` | 冰晶蓝 | 冰属性元素、辅色装饰 |
| **Background** | `#F8F4F0` | 冰霜白 | 页面主背景，接近白色的暖调底色 |
| **Accent** | `#9B72CF` | 紫挑染 | 点缀色，呼应角色发色挑染 |
| **Text** | `#2D2D3D` | 深紫灰 | 正文文字，呼应紫色元素 |
| **Secondary Text** | `#6B6B80` | 中紫灰 | 说明文字、标注、次要信息 |
| **Highlight** | `#FFD6E8` | 浅粉 | 数据高亮、卡片背景、强调 |
| **Border** | `#D0C8D8` | 淡紫灰 | 卡片边框、分隔线 |
| **Secondary Bg** | `#F0ECF4` | 淡紫白 | 区块背景、卡片底色 |
| **Warning** | `#E85C5C` | 警示红 | 注意事项、争议标注 |
| **White** | `#FFFFFF` | 纯白 | 文字叠加底色、图标 |

### AI Image Strategy

- **Image Rendering**: `watercolor` — 水彩手绘风格，柔和的笔触和晕染效果
- **Image Palette**: `earthy-dusty` — 自然暖调色板，适配粉蓝白主色调
- **Rendering x Palette compatibility**: 水彩 x 自然暖调，天然适配二次元角色叙事，温暖梦幻

---

## IV. Typography System

### Font Plan

**Typography direction**: 中文衬线标题 + 无衬线正文，古典与现代结合，呼应水彩手绘风格

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | SimSun | Georgia | serif |
| **Body** | "Microsoft YaHei" | Arial | sans-serif |
| **Emphasis** | KaiTi | Georgia | serif |

**Per-role font stacks**:

- Title: `SimSun, Georgia, serif`
- Body: `"Microsoft YaHei", Arial, sans-serif`
- Emphasis: `KaiTi, Georgia, serif`（用于引言、金句、重要标注）

### Font Size Hierarchy

**Baseline**: Body font size = 22px（角色解读场景，适中密度，留白呼吸感）

| Purpose | Size | Weight |
| ------- | ---- | ------ |
| Cover title | 60px | Bold |
| Chapter title | 44px | Bold |
| Page title | 36px | Bold |
| Deep-dive title | 36px | Bold |
| Hero number | 72px | Bold |
| Subtitle | 26px | SemiBold |
| **Body content** | **22px** | **Regular** |
| Deep-dive body (few items) | 30px | Regular |
| Deep-dive body (many items) | 22px | Regular |
| Annotation / caption | 15px | Regular |
| Page number | 11px | Regular |
| Small caption | 14px | Regular |
| Card number | 28px | Bold |
| Card body | 18px | Regular |
| FAQ question | 20px | SemiBold |
| FAQ answer | 18px | Regular |

### Formula Rendering Policy

`text-only` — 本内容无数据公式，不需要公式渲染。

---

## V. Layout Principles

### Page Structure

story_driven 模板三区布局（冰霜白浅色适配版）：

- **Header area** (y=40-98): 区域名称 + 页面标题 + 装饰线
- **Content area** (y=115-540): 核心视觉区（AI 图或素材图 + 文字）
- **Footer area** (y=600-680): Takeaway 结论栏

### Layout Patterns Used

| Pattern | Pages | Usage |
| ------- | ----- | ----- |
| **Full-bleed + floating text** | P01, P24 | 封面/封底，AI 背景 + 标题叠加 |
| **Narrative bridge** | P03, P07, P11, P16, P19 | 过渡页，承上启下 |
| **Three-zone vertical** | P04, P08, P12, P17, P20, P23 | 内容页，AI 配图 + 文字 + takeaway |
| **Three-zone variant** | P05, P06, P09, P10, P13, P14, P18, P21, P22 | 讲解页，卡片式 / 结构化布局 |
| **Card grid** | P02 | 目录页，章节卡片 |
| **Centered quote** | P15 | 金句页，大字引言 |

### Spacing Specification

| Element | Value |
| ------- | ----- |
| Safe margin | 60px left/right, 40px top/bottom |
| Content block gap | 24px |
| Card gap | 16px |
| Line height | 1.6-1.8 |
| Element spacing (deep-dive) | >=32px between text blocks |

---

## VI. Icon Usage Specification

### Source

- **Library**: `tabler-outline`（线性风格，与水彩手绘形成精致对比）
- **Stroke width**: 2

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| Camera / photography | `tabler-outline/camera` | P04, P20 |
| Shield / protection | `tabler-outline/shield` | P12, P13 |
| Sword / combat | `tabler-outline/sword` | P12, P13 |
| Star / special | `tabler-outline/star` | P01, P24 |
| Users / community | `tabler-outline/users` | P19, P21 |
| Clock / timeline | `tabler-outline/clock` | P16, P18 |
| Heart / favorite | `tabler-outline/heart` | P15, P23 |
| Palette / design | `tabler-outline/palette` | P07, P08 |
| Book / story | `tabler-outline/book` | P02 |
| Quote / speech | `tabler-outline/quote` | P15, P22 |

---

## VII. Visualization Reference List

| Viz ID | Type | Description | Pages |
| ------ | ---- | ----------- | ----- |
| V01 | Timeline | 三月七版本演进时间线 (1.0 -> 3.4) | P18 |
| V02 | Comparison | 存护 / 巡猎 / 极 三种形态对比卡片 | P13 |
| V03 | Card grid | 五章 TOC 章节卡片 | P02 |
| V04 | Quote layout | 金句居中 + 背景图 | P15 |

---

## VIII. Image Resource List

### AI 生成图片

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| P01_cover_bg.png | 1280x720 | 16:9 | 封面背景 — 三月七在星穹列车窗边，手持相机拍摄窗外星空，粉色短发在星光中飘动，冰晶雪花装饰 | Background | #1 full-bleed background with floating title | ai | Pending | 三月七在星穹列车窗边，手持相机拍摄窗外星空，粉色短发在星光中飘动，冰晶雪花装饰，水彩风格 | none | hero_page |
| P02_toc_bg.png | 1280x720 | 16:9 | 目录背景 — 三月七的相机和照片散落在星穹列车桌面上，每张照片对应一个章节主题 | Background | #1 full-bleed background with floating title | ai | Pending | 相机和照片散落在星穹列车桌面上，每张照片对应一个章节主题，水彩风格 | none | hero_page |
| P03_trans1_bg.png | 1280x720 | 16:9 | 过渡页1 — 巨大的六相冰晶悬浮在宇宙中，冰晶内隐约可见少女轮廓，神秘光芒 | Background | #1 full-bleed background with floating title | ai | Pending | 巨大的六相冰晶悬浮在宇宙中，冰晶内隐约可见少女轮廓，神秘光芒，水彩风格 | none | hero_page |
| P04_content1_ai.png | 1280x720 | 16:9 | 内容页 — 三月七从冰晶中苏醒的瞬间，粉色头发从黑色渐变为粉色，冰碎片四散 | Image | #44 background image + native diagram | ai | Pending | 三月七从冰晶中苏醒的瞬间，粉色头发从黑色渐变为粉色，冰碎片四散，水彩风格 | embedded | local |
| P07_trans2_bg.png | 1280x720 | 16:9 | 过渡页2 — 设计台面上的角色设计稿、彩色铅笔、粉蓝紫色颜料，设计师工作场景 | Background | #1 full-bleed background with floating title | ai | Pending | 设计台面上的角色设计稿、彩色铅笔、粉蓝紫色颜料，设计师工作场景，水彩风格 | none | hero_page |
| P08_content2_ai.png | 1280x720 | 16:9 | 内容页 — 三月七的核心视觉元素：粉发、蝴蝶结、冰晶、相机，以设计图标注风格呈现 | Image | #44 background image + native diagram | ai | Pending | 三月七的核心视觉元素：粉发、蝴蝶结、冰晶、相机，以设计图标注风格呈现，水彩风格 | embedded | local |
| P11_trans3_bg.png | 1280x720 | 16:9 | 过渡页3 — 三月七的三种形态剪影并排：持弓（存护）、持剑（巡猎）、量子光芒（极），渐变过渡 | Background | #1 full-bleed background with floating title | ai | Pending | 三月七的三种形态剪影并排：持弓、持剑、量子光芒，渐变过渡，水彩风格 | none | hero_page |
| P12_content3_ai.png | 1280x720 | 16:9 | 内容页 — 三月七持剑战斗姿态，仙舟风格服饰，冰与虚数能量交织 | Image | #44 background image + native diagram | ai | Pending | 三月七持剑战斗姿态，仙舟风格服饰，冰与虚数能量交织，水彩风格 | embedded | local |
| P15_quote_bg.png | 1280x720 | 16:9 | 金句页 — 三月七背影站在星穹列车门口，望向星空，冰晶与樱花交织飘落 | Background | #1 full-bleed background with floating title | ai | Pending | 三月七背影站在星穹列车门口，望向星空，冰晶与樱花交织飘落，水彩风格 | none | hero_page |
| P16_trans4_bg.png | 1280x720 | 16:9 | 过渡页4 — 星穹列车在星海中行驶，车窗外掠过贝洛伯格、仙舟罗浮、匹诺康尼的剪影 | Background | #1 full-bleed background with floating title | ai | Pending | 星穹列车在星海中行驶，车窗外掠过各世界剪影，水彩风格 | none | hero_page |
| P17_content4_ai.png | 1280x720 | 16:9 | 内容页 — 三月七在不同世界的身影：冰原、仙舟、梦境，以照片拼贴形式呈现 | Image | #44 background image + native diagram | ai | Pending | 三月七在不同世界的身影：冰原、仙舟、梦境，照片拼贴形式，水彩风格 | embedded | local |
| P19_trans5_bg.png | 1280x720 | 16:9 | 过渡页5 — 漫展 cosplay 人群的剪影，中央是三月七的标志性形象 | Background | #1 full-bleed background with floating title | ai | Pending | 漫展 cosplay 人群的剪影，中央是三月七的标志性形象，水彩风格 | none | hero_page |
| P20_content5_ai.png | 1280x720 | 16:9 | 内容页 — 三月七手持相机微笑，周围环绕着同人画作、表情包、cosplay 照片的碎片 | Image | #44 background image + native diagram | ai | Pending | 三月七手持相机微笑，周围环绕着同人画作和表情包碎片，水彩风格 | embedded | local |
| P23_content6_ai.png | 1280x720 | 16:9 | 内容页 — 冰封记忆中的春天：冰晶与樱花交织，三月七在春光中回眸 | Image | #44 background image + native diagram | ai | Pending | 冰晶与樱花交织，三月七在春光中回眸，温暖希望感，水彩风格 | embedded | local |
| P24_ending_bg.png | 1280x720 | 16:9 | 封底背景 — 三月七手持相机对镜头微笑，粉色头发在风中飘动，背景是星穹列车与星空 | Background | #1 full-bleed background with floating title | ai | Pending | 三月七手持相机对镜头微笑，星穹列车与星空背景，水彩风格 | none | hero_page |

### Web 素材图（讲解页配图）

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| P05_web_origin.png | varies | ~16:9 | 讲解页 — 三月七角色设定图、六相冰截图、剧情 CG | Existing | #44 background image + native diagram | web | Pending | 三月七角色设定图 + 六相冰剧情 CG 截图 | embedded | local |
| P06_web_relations.png | varies | ~16:9 | 讲解页 — 列车成员合影 / 关系图、开拓者与三月七截图 | Existing | #44 background image + native diagram | web | Pending | 星穹列车成员合影或关系图截图 | embedded | local |
| P09_web_design.png | varies | ~16:9 | 讲解页 — 夏一可公开的原画设计稿、配色分析 | Existing | #44 background image + native diagram | web | Pending | 夏一可 2025.4.8 微博公开的原画设计稿 | embedded | local |
| P10_web_symbols.png | varies | ~16:9 | 讲解页 — 冰晶 / 相机 / 蝴蝶结 / 盾牌 / 剑的特写截图 | Existing | #44 background image + native diagram | web | Pending | 游戏内冰晶、相机、蝴蝶结、盾牌、剑的特写截图 | embedded | local |
| P13_web_forms.png | varies | ~16:9 | 对比页 — 存护 / 巡猎 / 极 三形态立绘对比 | Existing | #44 background image + native diagram | web | Pending | 三种形态官方立绘截图对比 | embedded | local |
| P14_web_data.png | varies | ~16:9 | 讲解页 — 技能数据图表、光锥遗器搭配截图 | Existing | #44 background image + native diagram | web | Pending | Prydwen 技能数据 / 光锥遗器搭配截图 | embedded | local |
| P18_web_timeline.png | varies | ~16:9 | 时间线页 — 版本更新时间线图 | Existing | #44 background image + native diagram | web | Pending | 版本更新时间线图或版本 key visual 拼接 | embedded | local |
| P21_web_community.png | varies | ~16:9 | 讲解页 — 人气投票数据、同人创作统计 | Existing | #44 background image + native diagram | web | Pending | 社区人气投票数据截图 / Pixiv 同人统计 | embedded | local |
| P22_web_memes.png | varies | ~16:9 | 讲解页 — 经典表情包、名场面截图 | Existing | #44 background image + native diagram | web | Pending | 三月七经典表情包、游戏名场面截图 | embedded | local |

---

## IX. Content Outline

### Part 1: Opening

#### P01 — Cover

- **Cover impact**: "我叫三月七！虽然我也不记得自己叫这个名字了"。构图策略：全出血 AI 生成背景（三月七在列车窗边拍摄星空的水彩场景）+ 浮动标题。标题居中偏下，白色大字带粉色装饰线。
- **Layout**: full-bleed + floating text
- **Title**: 三月七——冰封记忆中的少女
- **Subtitle**: 一个没有过去的人，用相机和冰晶重新定义自己
- **Info**: 崩坏星穹铁道角色深度解读 · 2026
- **Image source**: P01_cover_bg.png (ai)

#### P02 — TOC

- **Layout**: card grid (story_driven 目录模板，冰霜白浅色适配)
- **TOC items**:
  1. 身世之谜 — 六相冰中醒来的少女
  2. 视觉 DNA — 夏一可与紫色挑染的诞生
  3. 战斗成长 — 从盾到剑的三种形态
  4. 版本叙事 — 从 1.0 到 3.4 的成长弧
  5. 文化符号 — 看板娘与社区记忆
- **Image source**: P02_toc_bg.png (ai)

---

### Part 2: 身世之谜

#### P03 — Transition -> Section 1

- **承上**: 三月七——没有过去、用日期命名的少女
- **本章**: 01 . 身世之谜
- **章节描述**: 在冰中沉睡了多久？她的真实身份是什么？
- **启下**: 在冰中沉睡了多久？她的真实身份是什么？
- **Image source**: P03_trans1_bg.png (ai)

#### P04 — Content: 冰中醒来的少女

- **Layout**: three-zone vertical (03_content.svg 浅色版)
- **Section**: S1 身世之谜
- **Title**: 冰中醒来的少女
- **Core message**: 三月七被封印在六相冰中，苏醒后丧失全部记忆，以被发现日期命名——这不是一个简单的失忆故事，而是游戏中最大的悬念之一。
- **Content blocks**:
  - 发现在宇宙中漂浮的巨大六相冰晶体内
  - 苏醒后对过去一无所知，用日期给自己命名
  - 冰属性力量可能与被冰封的身世直接相关
  - 与星神浮黎（掌管记忆）有深层关联
- **Visualization**: 冰碎片四散的苏醒瞬间
- **Takeaway**: 这个没有过去的人，用相机和冰晶重新定义了自己是谁
- **Image source**: P04_content1_ai.png (ai)

#### P05 — Deep Dive: 身世之谜详解

- **Layout**: structured cards（3 张信息卡片 + 1 张配图）
- **Title**: 身世之谜：六相冰、浮黎与黑天鹅
- **Content blocks**:
  - 卡片 1 — 六相冰：宇宙中漂浮的巨大冰晶，封印了三月七，解冻后完全失忆
  - 卡片 2 — 浮黎关联：星神浮黎掌管记忆，多方线索暗示三月七身份与其相关
  - 卡片 3 — 黑天鹅线索：流光忆庭的忆域迷因对三月七表现出特殊兴趣
  - 卡片 4 — 净璃和解：3.3 版本"净璃"形态开始与"过去的自己"和解
- **Web asset**: P05_web_origin.png — 三月七角色设定图、六相冰截图、剧情 CG
- **Image source**: P05_web_origin.png (web)

#### P06 — Deep Dive: 人物关系网

- **Layout**: relationship cards（中心角色 + 环绕关系卡片）
- **Title**: 人物关系网：她身边的每一个人
- **Content blocks**:
  - 核心关系 — 开拓者：失去记忆后最重要的人
  - 列车伙伴 — 姬子（大姐姐）、丹恒（沉默可靠）、瓦尔特（成熟指引）
  - 新朋友 — 流萤（Firefly）：匹诺康尼挚友
  - 仙舟羁绊 — "明璃"：仙舟罗浮获得的新名字和剑术
  - 暗线 — 黑天鹅：了解她秘密的存在
- **Web asset**: P06_web_relations.png — 列车成员合影 / 关系图、开拓者与三月七截图
- **Image source**: P06_web_relations.png (web)

---

### Part 3: 视觉 DNA

#### P07 — Transition -> Section 2

- **承上**: 三月七的身世与记忆主题
- **本章**: 02 . 视觉 DNA
- **章节描述**: 她为什么是粉色头发？设计师是怎么创造出她的？
- **启下**: 她为什么是粉色头发？设计师是怎么创造出她的？
- **Image source**: P07_trans2_bg.png (ai)

#### P08 — Content: 设计师夏一可与紫色挑染

- **Layout**: three-zone vertical (03_content.svg 浅色版)
- **Section**: S2 视觉 DNA
- **Title**: "我总想设计个紫色渐变挑染女孩"
- **Core message**: 主美夏一可的一句话催生了三月七——紫色渐变挑染是她的创作原点，粉蓝白配色从角色自身视觉 DNA 生长出来。
- **Content blocks**:
  - 夏一可：四川美术学院视觉传达专业，2022 年 7 月加入项目组
  - "我总想设计个拥有紫色渐变挑染头发的女孩"
  - "性格外向活泼，想穿得可爱但不想太幼齿"
  - 建模趣闻：没有时间建模，直接用衣服图片拼贴
  - 2025.4.8 在微博公开全部原画设计图
- **Visualization**: 视觉元素标注风格的角色设计图
- **Takeaway**: 三月七的视觉 DNA 从一句话开始生长为一个完整的角色世界
- **Image source**: P08_content2_ai.png (ai)

#### P09 — Deep Dive: 设计师访谈与原画

- **Layout**: quote + gallery（设计师语录 + 原画展示区）
- **Title**: 夏一可的设计台：从灵感到成品
- **Content blocks**:
  - 语录 1："因为没有时间建模，就直接把那些衣服的图片贴在身上"
  - 语录 2："性格外向活泼，想穿得可爱但不想太幼齿"
  - 设计过程：多个版本设计稿 -> 最终成品的演变
  - 2025.4.8 微博原画公开事件
- **Web asset**: P09_web_design.png — 夏一可公开的原画设计稿、配色分析
- **Image source**: P09_web_design.png (web)

#### P10 — Deep Dive: 视觉符号体系

- **Layout**: icon grid（5 个符号卡片 + 说明文字）
- **Title**: 五大视觉符号：定义三月七的语言
- **Content blocks**:
  - 符号 1 — 粉发 + 紫挑染：角色主色，活力与神秘并存
  - 符号 2 — 冰晶 / 六相冰：身世之谜的物化象征
  - 符号 3 — 相机：记录一切以防遗忘，角色核心道具
  - 符号 4 — 蝴蝶结发带：少女感与辨识度的关键
  - 符号 5 — 盾与剑：从存护到巡猎的成长映射
- **Web asset**: P10_web_symbols.png — 冰晶 / 相机 / 蝴蝶结 / 盾牌 / 剑的特写截图
- **Image source**: P10_web_symbols.png (web)

---

### Part 4: 战斗成长

#### P11 — Transition -> Section 3

- **承上**: 三月七的视觉 DNA 和设计师故事
- **本章**: 03 . 战斗成长
- **章节描述**: 从弓箭到剑——她在战斗中如何成长？
- **启下**: 从弓箭到剑——她在战斗中如何成长？
- **Image source**: P11_trans3_bg.png (ai)

#### P12 — Content: 三种形态的战斗成长

- **Layout**: three-zone vertical (03a_content.svg 浅色版，变体节奏)
- **Section**: S3 战斗成长
- **Title**: 从盾到剑：三种形态的战斗成长
- **Core message**: 三种形态不是简单的强度升级，而是映射了角色从"依赖保护"到"独立战斗"到"掌控记忆"的完整成长弧。
- **Content blocks**:
  - 存护（1.0 · 冰 · 四星）：单体护盾 + 冻结控制，新手期最可靠的免费盾辅
  - 巡猎（2.4 · 虚数 · 四星）：仙舟罗浮学习剑术，首个通过剧情免费获得的新命途角色
  - 极 · 三月七（3.4 · 量子 · 四星）：量子巡猎，全新武器与"记忆重构"能力
- **Visualization**: 三种形态并排的战斗剪影
- **Takeaway**: 三种形态映射了从依赖保护到独立战斗到掌控记忆的完整成长弧
- **Image source**: P12_content3_ai.png (ai)

#### P13 — Deep Dive: 形态对比

- **Layout**: comparison table（三列对比卡片）
- **Title**: 存护 vs 巡猎 vs 极：三种形态全对比
- **Content blocks**:
  - 对比维度：属性、命途、武器、核心机制、解锁方式
  - 存护 — 冰 / 存护 / 弓 / 护盾 + 反击 / 1.0 默认
  - 巡猎 — 虚数 / 巡猎 / 剑 / 师父系统 + 强化普攻 / 2.4 剧情免费
  - 极 — 量子 / 巡猎 / 裁 . 流光拾遗 / 记忆重构 / 3.4 版本
  - 核心差异：防御者 -> 追击副 C -> 量子输出
- **Web asset**: P13_web_forms.png — 存护 / 巡猎 / 极 三形态立绘对比
- **Image source**: P13_web_forms.png (web)

#### P14 — Deep Dive: 战斗数据

- **Layout**: data callouts（关键数据大数字 + 说明卡片）
- **Title**: 数据里的三月七：强度与搭配
- **Content blocks**:
  - 数据 1 — 4 款皮肤：默认 + 水手服 + 风神装 + 盛裁绽华
  - 数据 2 — 8 次 UP 卡池 (1.0-4.3)
  - 数据 3 — 星魂名称与记忆主题：E1"记忆中的你"、E4"不愿再失去"、E6"就这样，一直..."
  - 数据 4 — 配音阵容：中文诺亚 / 花玲、日文小仓唯、英文 Skyler Davenport
- **Web asset**: P14_web_data.png — 技能数据图表、光锥遗器搭配截图
- **Image source**: P14_web_data.png (web)

---

### Part 5: 金句页

#### P15 — Quote

- **Layout**: centered quote + full-bleed AI background（金句页模板）
- **Section**: 三月七
- **Quote**: "我忍你很久了！"
- **Attribution**: ——战斗中果断决绝，与日常生活中的活泼形成反差
- **Core message**: 这句战斗台词是三月七性格反差的极致表达——日常是小太阳，战斗时是决绝的战士
- **Visualization**: 三月七背影望向星空，冰晶与樱花飘落
- **Image source**: P15_quote_bg.png (ai)

---

### Part 6: 版本叙事

#### P16 — Transition -> Section 4

- **承上**: 三种形态映射角色成长
- **本章**: 04 . 版本叙事
- **章节描述**: 从 1.0 到 3.4，她在每个版本经历了什么？
- **启下**: 从 1.0 到 3.4，她在每个版本经历了什么？
- **Image source**: P16_trans4_bg.png (ai)

#### P17 — Content: 从 1.0 到 3.4 的版本叙事弧

- **Layout**: three-zone vertical (03_content.svg 浅色版)
- **Section**: S4 版本叙事
- **Title**: 从 1.0 到 3.4：三月七的版本叙事弧
- **Core message**: 三月七的版本成长不是单纯的强度迭代，而是剧情、形态、主题三线并进的叙事弧——每个版本都在回答"我是谁"这个问题。
- **Content blocks**:
  - 1.0-1.x（2023）：起点——失忆少女寻找自我，贝洛伯格 + 仙舟罗浮
  - 2.0-2.4（2024）：蜕变——匹诺康尼梦境高光，觉醒巡猎命途获新名"明璃"
  - 3.0-3.4（2025）：升华——"净璃"与过去的自己和解，"极"第三形态降临
- **Visualization**: 照片拼贴风格的世界穿越
- **Takeaway**: 每个版本都在回答同一个问题——"我是谁"
- **Image source**: P17_content4_ai.png (ai)

#### P18 — Deep Dive: 版本演进时间线

- **Layout**: timeline（水平时间轴 + 节点事件卡片）
- **Title**: 版本时间线：关键节点全记录
- **Content blocks**:
  - 1.0 (2023.4) — 首发登场，确立失忆主题
  - 1.1 — 水手服皮肤（免费）
  - 1.6 — 芭芭拉联动皮肤（免费）
  - 2.0 (2024) — 匹诺康尼：梦境与记忆的深度共鸣
  - 2.4 — 觉醒巡猎命途，获名"明璃"（剧情免费）
  - 3.0 (2025) — 翁法罗斯新篇章
  - 3.3 — "净璃"形态：与过去的自己和解
  - 3.4 — "极 . 三月七" + 新皮肤"盛裁绽华"
- **Web asset**: P18_web_timeline.png — 版本更新时间线图
- **Image source**: P18_web_timeline.png (web)

---

### Part 7: 文化符号

#### P19 — Transition -> Section 5

- **承上**: 从 1.0 到 3.4 的版本成长弧
- **本章**: 05 . 文化符号
- **章节描述**: 在玩家心中，她是什么？
- **启下**: 在玩家心中，她是什么？
- **Image source**: P19_trans5_bg.png (ai)

#### P20 — Content: 星穹铁道的看板娘

- **Layout**: three-zone vertical (03a_content.svg 浅色版，变体节奏)
- **Section**: S5 文化符号
- **Title**: 星穹铁道的看板娘
- **Core message**: 三月七不只是一个门面——她拥有"可战斗 + 有成长弧"的叙事深度，同时保留"可爱门面"属性，"可甜可飒"。
- **Content blocks**:
  - 官方定位：游戏启动页核心形象、宣传物料主力、叙事锚点
  - 深度类比：琪亚娜（战斗 + 成长弧）+ 派蒙（可爱门面）= 三月七
  - 在社区里她是"老婆""女儿""77""小太阳"
  - Pixiv 标签作品以万级计
  - 漫展 cosplay 出镜率最高的角色之一
- **Visualization**: 相机 + 微笑 + 同人碎片环绕
- **Takeaway**: 可甜可飒——三月七是星穹铁道名副其实的招牌角色
- **Image source**: P20_content5_ai.png (ai)

#### P21 — Deep Dive: 社区文化数据

- **Layout**: data cards（数据统计卡片 + 排名信息）
- **Title**: 社区里的三月七：数据与热爱
- **Content blocks**:
  - Pixiv 同人量级：万级标签作品
  - 人气投票排名：Top 10-15（中上位圈）
  - cosplay 入门成本：约 300-1500 元
  - 经典台词传播："拍照！我要拍下来！" 最高频被制作成表情包
  - 争议面：存护形态强度偏弱、"饭圈化"、出场频率疲劳
  - 整体风评以正面为主
- **Web asset**: P21_web_community.png — 人气投票数据、同人创作统计
- **Image source**: P21_web_community.png (web)

#### P22 — Deep Dive: 经典台词与名场面

- **Layout**: quote mosaic（多句台词 + 名场面描述）
- **Title**: 她说过的话，玩家都记得
- **Content blocks**:
  - "我叫三月七！虽然我也不记得自己为什么叫这个名字了。"
  - "这回我可没惹麻烦，还救了大家，所以我就不谦虚了，我真厉害！"
  - "照片才不小！"
  - "我忍你很久了！"
  - 为自己准备了六十七个不同的"身世故事"——一个没有过去的人，用想象力填补记忆的空白
  - 《纽约时报》2025.6 描述："粉发少女，用发带遮住一只眼睛"
- **Web asset**: P22_web_memes.png — 经典表情包、名场面截图
- **Image source**: P22_web_memes.png (web)

---

### Part 8: Closing

#### P23 — Content: 冰封记忆中的春天

- **Layout**: three-zone vertical (03_content.svg 浅色版)
- **Section**: 结语
- **Title**: 冰封记忆中的春天
- **Core message**: 三月七不只看板娘——她是"没有过去的人如何定义自己"这个永恒命题的游戏化身。冰封的是记忆，绽放的是春天。
- **Content blocks**:
  - 核心命题："没有过去的人如何定义自己"
  - 她用相机记录一切以防遗忘——记忆可以失去，但当下值得被记住
  - 六十七个身世故事——想象力是对遗忘的反抗
  - "净璃"和解——不需要找回过去，接受完整的自己
- **Visualization**: 冰晶与樱花交织，春光中的回眸
- **Takeaway**: 冰封的是记忆，绽放的是春天——这就是三月七
- **Image source**: P23_content6_ai.png (ai)

#### P24 — Ending

- **Closing impact**: 以三月七的故事收束全篇。构图：全出血 AI 生成背景（三月七对镜头微笑，星穹列车与星空）+ 居中大字结尾。
- **Layout**: full-bleed + floating text (封底模板)
- **Closing**: 冰封记忆中的少女，用相机和冰晶重新定义了自己
- **Tagline**: 三月七——崩坏星穹铁道 · 角色深度解读
- **Image source**: P24_ending_bg.png (ai)

---

## X. Speaker Notes Requirements

演讲备注保存到 `notes/` 目录：

- **Filename**: 匹配 SVG 文件名（如 `P01_cover.md`）
- **Content**: 讲解要点、时间提示、过渡语
- **深度**: 讲解页备注需详细——包含具体故事细节、数据来源、素材图讲解引导
- **语气**: 亲切、有感染力，面向崩铁玩家群体，可适当使用游戏内梗和社区用语

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. Text characters: write typography and symbols as raw Unicode; HTML named entities FORBIDDEN. XML reserved chars escaped as `&amp;` `&lt;` `&gt;` `&quot;` `&apos;`
8. 浅色调适配：story_driven 模板的深色背景替换为本 spec 确认的冰霜白浅色系
9. 水彩风格一致性：所有 AI 生成图片统一 watercolor rendering + earthy-dusty palette
10. Deep-dive 页面：每页 >=1 张 web 素材图，文字居中，标题 36px，正文 22-30px
