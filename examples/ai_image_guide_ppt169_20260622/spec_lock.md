# spec_lock.md — Machine-Readable Execution Contract

> Executor re-reads this file before every SVG page. All values below are the single source of truth. On divergence with design_spec.md, this file wins.

---

## mode

- mode: instructional
- mode_behavior: 教学讲解模式。分解概念→逐步讲解→实例演示→总结回顾。每页一个核心知识点，标题直接说明学什么。用实例先引入，再总结原则。步骤用编号流程，对比用并列卡片。备注语气耐心、解释性，先定义后使用。

## visual_style

- visual_style: story_driven（浅色适配版）
- visual_style_behavior: story_driven 模板的叙事结构和页面节奏，但配色从暗色切换为浅色调。保持三区布局（标题→核心视觉→takeaway），AI 生成背景图用于封面/目录/过渡/封底，内容页使用浅色纯底+AI 配图或素材图。过渡页保留承上启下叙事桥结构。

## canvas

- format: ppt169
- dim: 1280×720
- viewBox: 0 0 1280 720
- margins: 60px left/right, 40px top/bottom
- content_area: x:60-1220 y:40-680

## colors

- background: #F8FAFC
- secondary_bg: #E8EDF2
- primary: #2563EB
- accent: #F97316
- secondary_accent: #10B981
- body_text: #1E293B
- secondary_text: #64748B
- tertiary_text: #94A3B8
- border: #CBD5E1
- success: #10B981
- warning: #EF4444
- scrim: #F8FAFC (light theme, minimal scrim)

## typography

- title_family: "Microsoft YaHei", "PingFang SC", Segoe UI, sans-serif
- body_family: "Microsoft YaHei", "PingFang SC", Segoe UI, sans-serif
- code_family: Consolas, "Courier New", monospace
- body: 18px
- title: 32px
- subtitle: 24px
- cover_title: 72px
- chapter_title: 45px
- annotation: 14px
- page_number: 10px

## icons

- library: tabler-outline
- stroke_width: 2
- inventory:
  - tabler-outline/robot
  - tabler-outline/tool
  - tabler-outline/route
  - tabler-outline/sparkles
  - tabler-outline/refresh
  - tabler-outline/circle-check
  - tabler-outline/bulb
  - tabler-outline/target

## image_strategy

- rendering: flat
- palette: cool-tech

## page_rhythm

| Page | Rhythm | Notes |
|------|--------|-------|
| P01 | anchor | 封面，视觉冲击 |
| P02 | dense | 目录，信息密集 |
| P03 | breathing | 过渡页，留白呼吸 |
| P04 | anchor | 首个内容页，核心主张 |
| P05 | dense | 核心公式，信息量大 |
| P07 | breathing | 过渡页 |
| P08 | dense | 工具概览，三工具并列 |
| P09 | dense | 实操步骤，截图为主 |
| P10 | breathing | 过渡页 |
| P11 | dense | 三步流程，步骤详解 |
| P12 | dense | 提示词技巧，实操为主 |
| P13 | breathing | 过渡页 |
| P14 | dense | 六要素结构，信息量大 |
| P15 | dense | 迭代方法，截图+步骤 |
| P16 | anchor | 总结页，公式冲击 |

## page_layouts

| Page | Template | Variant |
|------|----------|---------|
| P01 | 01_cover.svg | 浅色版 |
| P02 | 02_toc.svg | 浅色版 |
| P03 | 02_chapter.svg | 浅色版 |
| P04 | 03_content.svg | 浅色版 |
| P05 | 03a_content.svg | 浅色版 |
| P07 | 02_chapter.svg | 浅色版 |
| P08 | 03_content.svg | 浅色版 |
| P09 | (executor 讲解页) | 卡片式+截图 |
| P10 | 02_chapter.svg | 浅色版 |
| P11 | 03_content.svg | 浅色版 |
| P12 | (executor 讲解页) | 卡片式+截图 |
| P13 | 02_chapter.svg | 浅色版 |
| P14 | 03_content.svg | 浅色版 |
| P15 | (executor 讲解页) | 卡片式+截图 |
| P16 | 04_ending.svg | 浅色版 |

## page_charts

（无可数据化图表，全部为空）
