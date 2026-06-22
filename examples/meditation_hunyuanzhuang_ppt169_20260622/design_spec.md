# 冥想与混元桩 — Design Spec v2

> Human-readable design narrative. See `spec_lock.md` for machine-readable execution contract.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | 冥想与混元桩——身心修炼的入口 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 24 |
| **Design Style** | 山林养生风 · 水墨渲染 · 中国传统养生美学 |
| **Target Audience** | 对养生、身心修炼感兴趣的普通大众 |
| **Use Case** | 知识分享 / 养生讲座 / 个人修炼参考 |
| **Content Strategy** | 从调研结果中提炼核心叙事，科学证据与传统文化双线并行 |
| **Created Date** | 2026-06-22 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top 50px, bottom 40px |
| **Content Area** | 1160×630 |

---

## III. Visual Theme

### Theme Style

- **Mode**: narrative — 故事驱动，从科学证据到传统智慧到实修指南
- **Visual style**: watercolor — 水墨渲染，柔和边缘，色彩晕染
- **Theme**: Light theme（暖白底色 #F5F0E6）
- **Tone**: 温润、内省、文化底蕴、自然朴素

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F5F0E6` | 暖白——古纸温暖底色 |
| **Secondary bg** | `#EDE7D9` | 淡米色——卡片背景 |
| **Primary** | `#425066` | 黛蓝——标题、关键区块 |
| **Accent** | `#7A5230` | 茶色——数据高亮、强调 |
| **Secondary accent** | `#789262` | 竹青——辅助装饰 |
| **Body text** | `#2D2D2D` | 浓墨——正文 |
| **Secondary text** | `#555555` | 中墨——注释 |
| **Tertiary text** | `#999999` | 淡墨——辅助 |
| **Border/divider** | `#C8C0B0` | 暖灰——边框 |
| **Success** | `#789262` | 竹青 |
| **Warning** | `#B85C38` | 赭石 |

### AI Image Strategy

- **Image Rendering**: `watercolor`
- **Image Palette**: `earthy-dusty`

---

## IV. Typography System

### Font Plan

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | SimSun | Georgia | serif |
| **Body** | "Microsoft YaHei" | Arial | sans-serif |
| **Emphasis** | KaiTi | Georgia | serif |

**Per-role font stacks**:
- Title: `SimSun, Georgia, serif`
- Body: `"Microsoft YaHei", Arial, sans-serif`
- Emphasis: `KaiTi, Georgia, serif`

### Font Size Hierarchy

**Baseline**: Body font size = 22px

| Purpose | Size | Weight |
| ------- | ---- | ------ |
| Cover title | 60px | Bold |
| Chapter title | 44px | Bold |
| Page title | 36px | Bold |
| Deep-dive title | 36px | Bold |
| Subtitle | 26px | SemiBold |
| **Body content** | **22px** | Regular |
| Deep-dive body (few items) | 28-32px | Regular |
| Deep-dive body (many items) | 22-24px | Regular |
| Annotation | 15px | Regular |
| Page number | 11px | Regular |

---

## V. Layout Principles

### Deep-Dive Page Layout Rules (v2 — lesson-learned update)

| Rule | Specification |
|------|--------------|
| Text alignment | All text center-aligned unless layout requires otherwise |
| Title size | 36-44px, Bold |
| Body text size | 22-26px minimum; pages with ≤3 items → 28-36px |
| Line height | 1.6-1.8 |
| Element spacing | ≥32px between text blocks and surrounding elements |
| Layout variety | Use cards, columns, timelines, data callouts — never plain text |
| Web assets | Every deep-dive page MUST include ≥1 web-sourced image |
| Narrative continuity | Title must echo/reference preceding content page's core claim |

### Content Page Layout Variety

| Pattern | Description | Used in |
|---------|-------------|---------|
| Left image, right text | AI image left 35-45% | P04, P10 |
| Right image, left text | AI image right 35-45% | P07, P17 |
| Top image, bottom text | AI image top 40-50% | P15 |
| Full-bleed + floating text | Image fills canvas, text over overlay | P13 |

---

## VIII. Image Resource List

### AI Images (13 existing + 1 new)

| Filename | Page | Purpose | Type | Acquire Via | Status |
| -------- |------|---------|------|-------------|--------|
| P01_cover_bg.png | P01 | 封面背景 | Background | ai | Generated |
| P02_toc_bg.png | P02 | 目录背景 | Background | ai | Generated |
| P03_trans1_bg.png | P03 | 过渡→冥想科学 | Background | ai | Generated (rename from P03_transition_bg) |
| P04_content_bg.png | P04 | 内容：大脑改变 | Background | ai | Generated |
| P07_trans2_bg.png | P07 | 过渡→混元桩 | Background | ai | Generated (rename from P06_transition_bg) |
| P08_content_bg.png | P08 | 内容：母功 | Background | ai | Generated (rename from P07_content_bg) |
| P10_trans3_bg.png | P10 | 过渡→身心合一 | Background | ai | Generated (rename from P09_transition_bg) |
| P11_content_bg.png | P11 | 内容：水与山 | Background | ai | Generated (rename from P10_content_bg) |
| P13_quote_bg.png | P13 | 金句：庄子 | Background | ai | Generated |
| P15_trans4_bg.png | P15 | 过渡→实修入门 | Background | ai | Generated (rename from P14_transition_bg) |
| P16_content_bg.png | P16 | 内容：5分钟开始 | Background | ai | Generated (rename from P15_content_bg) |
| P18_content_bg.png | P18 | 内容：动静合一 | Background | ai | Generated (rename from P17_content_bg) |
| P24_ending_bg.png | P24 | 封底 | Background | ai | Generated (rename from P18_ending_bg) |

### Web Assets (new — for deep-dive pages)

| Filename | Page | Purpose | Acquire Via | Status |
| -------- |------|---------|-------------|--------|
| dd_mri_brain.png | P05 | MRI脑结构变化对比图 | web | Pending |
| dd_cortex_thickening.png | P05 | 前额叶皮层增厚示意图 | web | Pending |
| dd_jama_2014.png | P06 | JAMA 2014荟萃分析图表 | web | Pending |
| dd_mbsr_evidence.png | P06 | MBSR临床证据汇总 | web | Pending |
| dd_yiquan_lineage.png | P09 | 意拳传承谱系图 | web | Pending |
| dd_wang_xiangzhai.png | P09 | 王芗斋照片 | web | Pending |
| dd_standing_posture.png | P12 | 站桩标准姿势图解 | web | Pending |
| dd_fascia_network.png | P12 | 筋膜网络/张力整体示意 | web | Pending |
| dd_meditation_vs_standing.png | P14 | 冥想vs站桩对比信息图 | web | Pending |
| dd_brain_pathways.png | P14 | 自上而下vs自下而上神经通路 | web | Pending |
| dd_practice_timeline.png | P17 | 进阶时间线路线图 | web | Pending |
| dd_three_in_one.png | P19 | 静坐-站桩-太极三位一体方案图 | web | Pending |
| dd_demographic_guide.png | P19 | 按人群推荐指南 | web | Pending |

---

## IX. Content Outline

### Part 1: 冥想科学 (P01-P06)

#### P01 - Cover
- **Cover impact**: "你的大脑只需要8周"——哈佛MRI研究打破"冥想是玄学"的偏见
- **Layout**: Full-bleed AI image + floating title
- **Title**: 冥想与混元桩
- **Subtitle**: 身心修炼的入口

#### P02 - 目录
- **Layout**: Full-bleed AI image + floating TOC
- **Title**: 目录
- **Content**: 5章概览

#### P03 - 过渡 → §1
- **Layout**: Full-bleed AI image + floating text
- **Chapter title**: 第一章 · 冥想改变大脑

#### P04 - 内容：8周改变大脑
- **Layout**: Left image (35%), right text (65%)
- **Title**: 8周，大脑的物理结构改变了
- **Core message**: 哈佛MRI研究证明冥想可改变大脑物理结构
- **Takeaway**: 仅8周MBSR训练，即可观察到可测量的脑结构变化

#### P05 - 讲解页：大脑研究数据（承接P04）
- **Layout**: Top-bottom split — 大号数据+MRI图
- **Title**: 8周改变大脑：关键MRI研究数据
- **Core message**: Sara Lazar 2005首次MRI证据 + Holzel 2011的8周MBSR脑结构变化
- **Content**: 4个脑区变化卡片 + 关键数据 + 效果量
- **Web assets**: dd_mri_brain.png, dd_cortex_thickening.png

#### P06 - 讲解页：循证医学地图（承接P04）
- **Layout**: Data page — hero number + 3 data cards
- **Title**: 冥想的循证医学证据：JAMA荟萃分析
- **Core message**: 2014 JAMA 47项RCT + 2024 BMJ 200项RCT + MBCT vs抗抑郁药
- **Content**: 效果量数据 + 免疫增强证据 + 端粒酶研究
- **Web assets**: dd_jama_2014.png, dd_mbsr_evidence.png

### Part 2: 混元桩源流 (P07-P09)

#### P07 - 过渡 → §2
- **Layout**: Full-bleed AI image + floating text
- **Chapter title**: 第二章 · 站出来的功夫

#### P08 - 内容：站桩为拳学之母
- **Layout**: Right image (35%), left text (65%)  ← 变体版式
- **Title**: 站桩为拳学之母
- **Core message**: 王芗斋创立意拳，抛弃套路只保留站桩
- **Takeaway**: "站桩为拳学之母"——王芗斋《大成拳论》

#### P09 - 讲解页：传承时间线+核心概念（承接P08）
- **Layout**: Top-bottom split — timeline + philosophical cards
- **Title**: 母功的传承谱系：从形意拳到现代养生
- **Core message**: 1885-2000+的四阶段演变 + "混元"的道家哲学根源
- **Content**: 7节点时间线 + 4阶段色块 + 3层"混元"含义
- **Web assets**: dd_yiquan_lineage.png, dd_wang_xiangzhai.png

### Part 3: 身心合一 (P10-P14)

#### P10 - 过渡 → §3
- **Layout**: Full-bleed AI image + floating text
- **Chapter title**: 第三章 · 两条路，一个终点

#### P11 - 内容：水与山的对话
- **Layout**: Left image (35%), right text (65%)
- **Title**: 水与山的对话
- **Core message**: 冥想=水（自上而下），站桩=山（自下而上），共享Alpha波等效果
- **Takeaway**: 王芗斋的智慧——站桩本身就是冥想

#### P12 - 讲解页：站桩生理机制（承接P11）
- **Layout**: Three-column cards + side diagram
- **Title**: 站桩的生理密码：放松中维持结构
- **Core message**: 站桩的独特之处在于"放松中维持结构"——与靠墙静蹲的最大化收缩策略形成对比
- **Content**: 3机制卡片（自主神经/筋膜/肌骨）+ 对比表
- **Web assets**: dd_standing_posture.png, dd_fascia_network.png

#### P13 - 金句页：庄子心斋
- **Layout**: Negative-space-driven — 大留白 + 居中大字
- **Quote**: "无听之以耳而听之以心，无听之以心而听之以气"
- **Attribution**: 《庄子·人间世·心斋》

#### P14 - 讲解页：冥想vs站桩对比（承接P11）
- **Layout**: Symmetric 5:5 split — 左栏冥想右栏站桩
- **Title**: 冥想 vs 站桩：详细对比
- **Core message**: 两者不是二选一，而是互补的两条路径
- **Content**: 8维度对比表 + 各自独有收益 + 按人群推荐
- **Web assets**: dd_meditation_vs_standing.png, dd_brain_pathways.png

### Part 4: 实修入门 (P15-P19)

#### P15 - 过渡 → §4
- **Layout**: Full-bleed AI image + floating text
- **Chapter title**: 第四章 · 你的第一个10分钟

#### P16 - 内容：从5分钟开始
- **Layout**: Top image (40%), bottom text (60%)  ← 变体版式
- **Title**: 从5分钟开始
- **Core message**: 入门方案：5分钟起，每周增加1分钟
- **Takeaway**: "宁短不懈，宁轻不伤"

#### P17 - 讲解页：混元桩七步要领+进阶路线（承接P16）
- **Layout**: Cards grid (7 steps) + progression timeline
- **Title**: 混元桩七步要领与进阶路线
- **Core message**: 正确的结构是一切的基础 + 5阶段进阶时间线
- **Content**: 7步卡片 + 5阶段进度条 + 10大常见错误
- **Web assets**: dd_practice_timeline.png

#### P18 - 讲解页：呼吸与意念（承接P16）
- **Layout**: Two-column split — 呼吸方法 | 意念心法
- **Title**: 呼吸与意念：站桩的内在维度
- **Core message**: 从自然呼吸到腹式呼吸 + 从听息法到守丹田
- **Content**: 3级呼吸法 + 4种意念技术 + 安全原则
- **Web assets**: (纯结构化布局，无需额外素材)

#### P19 - 讲解页：三位一体方案（承接P16）
- **Layout**: Three stage cards + demographic recommendation rows
- **Title**: 静坐·站桩·太极：三位一体练习方案
- **Core message**: 先站桩激活身体→再静坐沉淀心念→太极作为动态桥接
- **Content**: 3阶段方案 + 5类人群推荐
- **Web assets**: dd_three_in_one.png, dd_demographic_guide.png

### Part 5: 整合之路 (P20-P24)

#### P20 - 过渡 → §5
- **Layout**: Full-bleed AI image + floating text
- **Chapter title**: 第五章 · 动静合一

#### P21 - 内容：动静合一
- **Layout**: Full-bleed image + floating text (center)  ← 变体版式
- **Title**: 动静合一
- **Core message**: 站桩练体、静坐练心、太极练合一
- **Takeaway**: 你的身体就是最好的实验室

#### P22 - 讲解页：修炼三维度（承接P21）
- **Layout**: Three-column cards with colored top borders
- **Title**: 站桩练体·静坐练心·太极练合一
- **Core message**: 三个维度的具体收获和科学支撑
- **Content**: 3维度详解卡片 + 科学证据支撑
- **Web assets**: (纯结构化布局)

#### P23 - 讲解页：常见问题与注意事项
- **Layout**: FAQ cards layout
- **Title**: 开始修炼前的常见问题
- **Core message**: 帮助观众消除入门顾虑
- **Content**: 5-6个FAQ（站桩腿抖怎么办/每天要多久/饭后能练吗/需要老师吗/多久见效/能替代吃药吗）
- **Web assets**: (纯结构化布局)

#### P24 - 封底
- **Closing impact**: "你的身体就是最好的实验室"——科学精神与传统智慧合二为一
- **Layout**: Full-bleed AI image + floating closing text
- **Content**: 身心合一，动静皆修 · 从今天开始，站5分钟
