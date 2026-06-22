# AI 生图攻略 — Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline.
>
> Machine-readable execution contract: `spec_lock.md`. Executor re-reads `spec_lock.md` before every SVG page. Keep both in sync; on divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | AI 生图攻略 |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 16 |
| **Design Style** | story_driven × instructional × 浅色调科技风 |
| **Target Audience** | AI 工具初学者和中级用户，培训课堂场景 |
| **Use Case** | AI 生图工具培训讲义，从零到一教学 |
| **Content Strategy** | 可自由重组章节结构，提炼核心步骤为可视化流程，补充过渡页和总结页增强教学效果 |
| **Layout Template** | story_driven（浅色适配版） |
| **Created Date** | 2026-06-22 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280 × 720 px |
| **viewBox** | `0 0 1280 720` |
| **Margins** | Left/right 60px, top 40px, bottom 40px |
| **Content Area** | x: 60-1220, y: 40-680 |

---

## III. Visual Theme

### Theme Style

- **Mode**: `instructional` — 教学讲解模式，分解概念→逐步讲解→实例演示→总结回顾
- **Visual style**: story_driven template layout（自定义浅色适配）
- **Theme**: Light theme — 浅色调
- **Tone**: 科技、清晰、专业、亲和

### Color Scheme

用户确认"浅色调"。基于科技培训场景推导，采用浅色底+蓝色系主色调。

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F8FAFC` | 页面主背景，近白色 |
| **Secondary bg** | `#E8EDF2` | 卡片、区块背景，淡蓝灰 |
| **Primary** | `#2563EB` | 标题装饰、关键区块、图标，明亮蓝 |
| **Accent** | `#F97316` | 数据高亮、关键信息、CTA，活力橙 |
| **Secondary accent** | `#10B981` | 成功状态、流程节点、辅助强调，翠绿 |
| **Body text** | `#1E293B` | 正文文字，深灰蓝 |
| **Secondary text** | `#64748B` | 说明文字、标注 |
| **Tertiary text** | `#94A3B8` | 补充信息、页码 |
| **Border/divider** | `#CBD5E1` | 卡片边框、分隔线 |
| **Success** | `#10B981` | 正面指标 |
| **Warning** | `#EF4444` | 注意事项 |

### AI Image Strategy

- **Image Rendering**: `flat` — 扁平矢量插画
- **Image Palette**: `cool-tech` — 冷色科技调色板
- **Rendering × Palette 兼容**: ✓ 扁平矢量 × 科技冷色，天然适配

### Gradient Scheme

```xml
<!-- Cover title accent gradient -->
<linearGradient id="titleAccent" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#2563EB"/>
  <stop offset="100%" stop-color="#10B981"/>
</linearGradient>

<!-- Subtle background decorative gradient -->
<radialGradient id="bgDecor" cx="85%" cy="15%" r="40%">
  <stop offset="0%" stop-color="#2563EB" stop-opacity="0.06"/>
  <stop offset="100%" stop-color="#2563EB" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: 现代 CJK 无衬线，标题加粗突出层次

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei"` | `Segoe UI` | `sans-serif` |
| **Body** | `"Microsoft YaHei"` | `Segoe UI` | `sans-serif` |
| **Emphasis** | `"Microsoft YaHei"` | `Segoe UI` | `sans-serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `"Microsoft YaHei", "PingFang SC", Segoe UI, sans-serif`
- Body: `"Microsoft YaHei", "PingFang SC", Segoe UI, sans-serif`
- Emphasis: same as Body (bold weight)
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 18px（中等密度，培训场景适中）

| Purpose | Ratio to body | Size | Weight |
| ------- | ------------- | ---- | ------ |
| Cover title | 4x | 72px | Bold |
| Chapter/section opener | 2.5x | 45px | Bold |
| Page title | 1.8x | 32px | Bold |
| Subtitle | 1.3x | 24px | SemiBold |
| **Body content** | **1x** | **18px** | **Regular** |
| Annotation/caption | 0.78x | 14px | Regular |
| Page number | 0.56x | 10px | Regular |

### Formula Rendering Policy

`text-only` — 本培训内容无数学公式，不需要公式渲染。

---

## V. Layout Principles

### Page Structure

story_driven 模板三区布局（浅色适配版）：

- **Header area** (y=40-98): 区域名称 + 页面标题 + 装饰线
- **Content area** (y=115-540): 核心视觉区（AI 图或素材图 + 文字）
- **Footer area** (y=600-680): Takeaway 结论栏

### Layout Patterns Used

| Pattern | Pages | Usage |
| ------- | ----- | ----- |
| **Full-bleed + floating text** | P01, P16 | 封面/封底，AI 背景+标题叠加 |
| **Narrative bridge** | P03, P07, P12 | 过渡页，承上启下 |
| **Three-zone vertical** | P04, P05, P06, P08, P09, P10, P13, P14 | 内容页/讲解页 |
| **Asymmetric split (3:7)** | P11 | 对比布局 |
| **Card grid** | P02 | 目录页，章节卡片 |

### Spacing Specification

**Universal**:

| Element | Value |
| ------- | ----- |
| Safe margin | 60px left/right, 40px top/bottom |
| Content block gap | 24px |
| Icon-text gap | 10px |

---

## VI. Icon Usage Specification

### Source

- **Library**: `tabler-outline`（线性风格，科技感轻盈）
- **Stroke width**: 2px

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| AI / robot | `tabler-outline/robot` | P04 |
| Tools / settings | `tabler-outline/tool` | P07 |
| Workflow / steps | `tabler-outline/route` | P08 |
| Generate / create | `tabler-outline/sparkles` | P10 |
| Iterate / refresh | `tabler-outline/refresh` | P13 |
| Check / success | `tabler-outline/circle-check` | P14 |
| Lightbulb / idea | `tabler-outline/bulb` | P01, P15 |
| Target / goal | `tabler-outline/target` | P09 |

---

## VII. Visualization Reference List

本培训 PPT 无可数据化图表，不需要可视化模板。

---

## VIII. Image Resource List

### AI 生成图片（视觉页背景/配图）

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| P01_cover_bg.png | 1280×720 | 16:9 | 封面背景 — AI 工具创作的概念场景 | Background | #1 full-bleed background with floating title | ai | Pending | 一个人面对电脑屏幕，屏幕上绽放出绚丽的数字艺术作品，扁平矢量风格，浅色调科技感，蓝绿色调为主 | none | hero_page |
| P02_toc_bg.png | 1280×720 | 16:9 | 目录背景 — 科技感抽象图案 | Background | #1 full-bleed background with floating title | ai | Pending | 抽象科技几何图案，扁平风格，线条连接节点，代表知识结构和流程，浅蓝白色调 | none | hero_page |
| P03_trans1_bg.png | 1280×720 | 16:9 | 过渡页1 — 从混乱到有序的转化 | Background | #1 full-bleed background with floating title | ai | Pending | 一堆散乱的图片碎片正在被智能算法重组为有序排列，扁平矢量风格，蓝绿色调 | none | hero_page |
| P05_content_ai.png | 1280×720 | 16:9 | 内容页 — 需求到成品的转化流程 | Diagram | #20 single-focus centered + #29 two-stop scrim | ai | Pending | 一条从左侧文字气泡流向右侧成品图片的流程管道，扁平风格，蓝色管道绿色节点，白色背景 | none | local |
| P07_trans2_bg.png | 1280×720 | 16:9 | 过渡页2 — 工具准备就绪 | Background | #1 full-bleed background with floating title | ai | Pending | 工具箱打开，里面是 DeepSeek 和 GPT-Image 的抽象图标，扁平矢量风格，蓝橙配色 | none | hero_page |
| P10_trans3_bg.png | 1280×720 | 16:9 | 过渡页3 — 进入生成阶段 | Background | #1 full-bleed background with floating title | ai | Pending | 一个画布上正在渲染出精美图案，数字画笔的光效，扁平风格，蓝紫渐变 | none | hero_page |
| P12_trans4_bg.png | 1280×720 | 16:9 | 过渡页4 — 迭代优化 | Background | #1 full-bleed background with floating title | ai | Pending | 循环箭头围绕一个不断精进的图案，从粗糙到精致的渐变，扁平风格，绿色调为主 | none | hero_page |
| P15_closing_bg.png | 1280×720 | 16:9 | 金句/总结背景 — AI 创作全景 | Background | #1 full-bleed background with floating title | ai | Pending | 全景式展示多种 AI 生成的精美图片拼贴在一起，扁平矢量风格，色彩丰富但和谐，蓝绿橙为主 | none | hero_page |
| P16_ending_bg.png | 1280×720 | 16:9 | 封底背景 — 呼应封面 | Background | #1 full-bleed background with floating title | ai | Pending | 与封面呼应的创作场景，但视角更广，展示完整的创作生态，扁平矢量风格，浅色调 | none | hero_page |

### 来源文档素材图（讲解页配图）

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| image_007.png | 2549×1352 | ~16:9 | DeepSeek 输入文案截图 | Existing | #44 background image + native diagram | user | Existing | 来源文档 Step 2 截图 | embedded | local |
| image_008.png | 2549×1352 | ~16:9 | DeepSeek 输出排版方案截图 | Existing | #44 background image + native diagram | user | Existing | 来源文档 Step 3 截图 | embedded | local |
| image_009.png | 2559×1481 | ~16:9 | GPT-Image 发送界面截图 | Existing | #44 background image + native diagram | user | Existing | 来源文档 GPT-Image 操作截图 | embedded | local |
| image_011.png | 2549×1352 | ~16:9 | 豆包视觉识别分析截图 | Existing | #44 background image + native diagram | user | Existing | 来源文档迭代优化截图 | embedded | local |

---

## IX. Content Outline

### Part 1: 开场 + 认知建立

#### P01 — Cover

- **Cover impact**: 核心钩子——"人人都能用 AI 画出专业级图片"。构图策略：全出血 AI 生成背景（扁平矢量，一个人面对电脑创作的场景）+ 浮动标题。标题居中偏左，白色大字带蓝色渐变装饰线。
- **Layout**: full-bleed + floating text
- **Title**: AI 生图攻略
- **Subtitle**: 从零到一掌握 AI 图片生成
- **Info**: 培训讲义 · 2026

#### P02 — TOC

- **Layout**: card grid（story_driven 目录模板，浅色适配）
- **TOC items**:
  1. 底层逻辑 — AI 如何理解图片需求
  2. 工具准备 — DeepSeek + GPT-Image
  3. 标准工作流 — 三步出图法
  4. 迭代优化 — 从满意到完美
  5. 总结 — 能力公式

#### P03 — Transition → Part 2（底层逻辑）

- **承上**: 认识 AI 生图全景
- **本章**: 01 · 底层逻辑
- **章节描述**: AI 为什么不能直接理解图片？
- **启下**: 理解了底层逻辑，我们才能写出有效的提示词

### Part 2: 底层逻辑

#### P04 — Content: 图片无法被 AI 直接理解

- **Layout**: three-zone vertical（03_content.svg 浅色版）
- **Section**: §1 底层逻辑
- **Title**: 图片的本质困境
- **Core message**: AI 无法直接"看懂"图片，优秀作品需要将创意转化为结构化文字需求
- **Takeaway**: 好的 AI 生图 = 好的需求表达

#### P05 — Content: 核心公式

- **Layout**: three-zone vertical（03a_content.svg 浅色版，变体节奏）
- **Section**: §1 底层逻辑
- **Title**: AI 生图核心公式
- **Image**: `P05_content_ai.png`（AI 生成的流程图示意图）
- **Core message**: 需求想法 → 文案拆解 → 排版设计 → 提示词生成 → AI 出图 → 迭代优化
- **Takeaway**: 六步闭环，每一步都影响最终效果

### Part 3: 工具准备

#### P07 — Transition → Part 3（工具准备）

- **承上**: 理解了底层逻辑和核心公式
- **本章**: 02 · 工具准备
- **章节描述**: 三大工具各司其职
- **启下**: 工具就绪，下一步就是实战操作

#### P08 — Content: 三大工具概览

- **Layout**: three-zone vertical（03_content.svg 浅色版）
- **Section**: §2 工具准备
- **Title**: 三大核心工具
- **Core message**: DeepSeek（文案整理）+ GPT-Image（图片生成）+ 豆包/千图（后期微调），三件套覆盖完整工作流
- **Content**:
  - DeepSeek — 文案整理、结构设计、提示词生成
  - GPT-Image / Gemini — AI 图片生成
  - 豆包、千图 — 抠图、去背景、局部修改（可选）
- **Takeaway**: 选对工具，事半功倍

#### P09 — Deep Dive: 工具配置实操

- **Layout**: three-zone vertical（讲解页，浅色卡片式）
- **Section**: §2 工具准备
- **Title**: 工具配置步骤
- **Image**: `image_007.png`（DeepSeek 界面截图）
- **Core message**: 注册账号 → 获取 API 密钥 → 配置 GPT-Image 工具
- **Content**:
  - Step 1: 访问 vip.123everything.com 注册（赠送 $0.2 额度）
  - Step 2: 控制台 → API 密钥 → 复制保存
  - Step 3: 小米工具箱 → GPT-Image2 生成器 → 填入 URL 和密钥
- **Takeaway**: 三步配置完成，即可开始创作

### Part 4: 标准工作流

#### P10 — Transition → Part 3（标准工作流）

- **承上**: 工具准备就绪
- **本章**: 03 · 标准工作流
- **章节描述**: 三步出图法
- **启下**: 跟着步骤走，人人都能出好图

#### P11 — Content: 三步出图法

- **Layout**: three-zone vertical（03_content.svg 浅色版）
- **Section**: §3 标准工作流
- **Title**: 三步出图法
- **Core message**: 明确目标 → 发送文案给 DeepSeek → 要求输出排版方案和提示词
- **Content**:
  - 步骤 1：明确目标——我要什么样的图？
  - 步骤 2：把文案发送给 DeepSeek
  - 步骤 3：要求输出结构化排版方案 + AI 绘图提示词
- **Takeaway**: 结构化需求是好图的前提

#### P12 — Deep Dive: DeepSeek 提示词技巧

- **Layout**: three-zone vertical（讲解页，浅色卡片式）
- **Section**: §3 标准工作流
- **Title**: 提示词优化技巧
- **Image**: `image_008.png`（DeepSeek 输出排版方案截图）
- **Core message**: 审阅提示词细节 + 添加负面提示词 = 大幅提升出图质量
- **Content**:
  - 核对文案细节，不满意就修改
  - 推荐负面提示词：不要卡通风、不要花哨插画、不要复杂 3D 效果、不要拥挤排版、不要杂乱背景……
  - 示例提示词模板："把上述文案以结构化方式输出，要求科研绘图风格，颜色限定为白色、蓝色、绿色和橙色"
- **Takeaway**: 负面提示词是排除干扰的利器

### Part 5: 生成与迭代

#### P13 — Transition → Part 4（生成图片）

- **承上**: 提示词准备完毕
- **本章**: 04 · 生成与迭代
- **章节描述**: 发送生成 + 迭代优化
- **启下**: 一次生成往往不够，迭代才是关键

#### P14 — Content: 生成图片 + 优秀提示词结构

- **Layout**: three-zone vertical（03_content.svg 浅色版）
- **Section**: §4 生成图片
- **Title**: 生成与提示词结构
- **Image**: `image_009.png`（GPT-Image 界面截图）
- **Core message**: 将 DeepSeek 输出发送给 GPT-Image，优秀提示词有六大要素
- **Content**:
  - ① 主题 · ② 风格 · ③ 构图 · ④ 色彩 · ⑤ 文字布局 · ⑥ 细节要求
- **Takeaway**: 六要素缺一不可

#### P15 — Deep Dive: 迭代优化方法

- **Layout**: three-zone vertical（讲解页，浅色卡片式）
- **Section**: §5 迭代优化
- **Title**: 迭代优化方法
- **Image**: `image_011.png`（豆包视觉分析截图）
- **Core message**: 用视觉 AI 分析成品 → 修改提示词 → 重新生成，直到满意
- **Content**:
  - 排版满意只改文案：上传图片到豆包/千问 → AI 提取文案 → 修改 → 重新生成
  - 排版不满意：详细描述需要增减的板块 → 修改提示词 → 重新生成
  - 关键技巧："请参考上传图片，制作一张风格一致的图片"
- **Takeaway**: 迭代能力 = AI 生图的核心竞争力

### Part 6: 总结

#### P16 — Ending

- **Closing impact**: 核心公式——AI 生图能力 = 需求表达能力 × 提示词能力 × 审美能力 × 迭代能力。构图：全出血 AI 背景 + 居中大字公式 + 底部推荐流程
- **Layout**: full-bleed + floating text（封底模板）
- **Closing**: AI 生图能力 = 需求表达 × 提示词 × 审美 × 迭代
- **Tagline**: DeepSeek → 排版设计 → GPT-Image2 → 修改优化 → 最终交付

---

## X. Speaker Notes Requirements

演讲备注保存到 `notes/` 目录：

- **Filename**: 匹配 SVG 文件名（如 `P01_cover.md`）
- **Content**: 讲解要点、时间提示、过渡语
- **深度**: 讲解页备注需详细——包含具体故事细节、数据来源、素材图讲解引导

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. Text characters: write typography & symbols as raw Unicode; HTML named entities FORBIDDEN. XML reserved chars escaped as `&amp;` `&lt;` `&gt;` `&quot;` `&apos;`
8. 浅色调适配：story_driven 模板的深色背景替换为本 spec 确认的浅色系
