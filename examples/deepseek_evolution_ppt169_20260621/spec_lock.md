# Execution Lock

> Machine-readable execution contract. Executor MUST `read_file` this before every SVG page. Values NOT listed here must NOT appear in SVGs. For design narrative (rationale, audience, style), see `design_spec.md`.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #0A1628
- bg_secondary: #122240
- card_bg: #122240
- primary: #4D6BFE
- accent: #FFB800
- secondary_accent: #00D4AA
- text: #E8ECF1
- text_secondary: #8899B0
- text_tertiary: #5A6A80
- border: #1E3A5F
- success: #00D4AA
- warning: #FF6B35

## typography
- title_family: Inter, "Microsoft YaHei", sans-serif
- body_family: "Microsoft YaHei", Inter, sans-serif
- emphasis_family: Inter, "Microsoft YaHei", sans-serif
- code_family: Consolas, "Courier New", monospace
- cover_title: 60
- chapter_title: 44
- page_title: 32
- hero_number: 80
- subtitle: 26
- body: 20
- annotation: 15
- page_number: 12

## icons
- library: chunk
- inventory: chip, cpu, globe, chart-line, bolt, code, server, brain, network, arrow-trend-up, arrow-trend-down, scale, users, book-open, lightbulb, rocket, star, layers, terminal, key

## images
### AI generated (visual pages)
- P01_cover_bg: images/P01_cover_bg.png
- P02_toc_bg: images/P02_toc_bg.png
- P03_trans_ch1: images/P03_trans_ch1.png
- P04_content_impact: images/P04_content_impact.png
- P07_trans_ch2: images/P07_trans_ch2.png
- P08_content_scaling: images/P08_content_scaling.png
- P11_trans_ch3: images/P11_trans_ch3.png
- P12_content_liang: images/P12_content_liang.png
- P14_trans_ch4: images/P14_trans_ch4.png
- P15_content_v2: images/P15_content_v2.png
- P17_content_v3: images/P17_content_v3.png
- P19_trans_ch5: images/P19_trans_ch5.png
- P20_content_r1: images/P20_content_r1.png
- P22_quote_aha: images/P22_quote_aha.png
- P23_trans_ch6: images/P23_trans_ch6.png
- P24_content_sputnik: images/P24_content_sputnik.png
- P27_trans_ch7: images/P27_trans_ch7.png
- P28_content_open: images/P28_content_open.png
- P30_ending_bg: images/P30_ending_bg.png

### Web assets (deep dive pages)
- web_nvidia_crash_data: images/web_assets/web_nvidia_crash_data.png
- web_sputnik_comparison: images/web_assets/web_sputnik_comparison.png
- web_training_cost_trend: images/web_assets/web_training_cost_trend.png
- web_scaling_vs_algorithm: images/web_assets/web_scaling_vs_algorithm.png
- web_highflyer_story: images/web_assets/web_highflyer_story.png
- web_mla_architecture: images/web_assets/web_mla_architecture.png
- web_v3_vs_gpt4: images/web_assets/web_v3_vs_gpt4.png
- web_r1_training_detail: images/web_assets/web_r1_training_detail.png
- web_ai_stock_timeline: images/web_assets/web_ai_stock_timeline.png
- web_industry_reactions: images/web_assets/web_industry_reactions.png
- web_deepseek_vs_llama: images/web_assets/web_deepseek_vs_llama.png

## page_rhythm
- P01: anchor        # 封面 — 视觉冲击
- P02: breathing     # 目录 — 节奏缓冲
- P03: anchor        # 过渡1 — 钩子
- P04: anchor        # 内容1 — 5930亿
- P05: dense         # 讲解 — 数据展开
- P06: dense         # 讲解 — 对比展开
- P07: anchor        # 过渡2
- P08: anchor        # 内容2 — Scaling Law
- P09: dense         # 讲解 — 成本趋势
- P10: dense         # 讲解 — 路线对比
- P11: anchor        # 过渡3
- P12: anchor        # 内容3 — 梁文锋
- P13: dense         # 讲解 — 故事展开
- P14: anchor        # 过渡4
- P15: anchor        # 内容4a — V2
- P16: dense         # 讲解 — MLA原理
- P17: anchor        # 内容4b — V3
- P18: dense         # 讲解 — V3对比
- P19: anchor        # 过渡5
- P20: anchor        # 内容5 — R1-Zero
- P21: dense         # 讲解 — R1详解
- P22: breathing     # 金句 — 节奏缓冲
- P23: anchor        # 过渡6
- P24: anchor        # 内容6 — Sputnik
- P25: dense         # 讲解 — 股市时间线
- P26: dense         # 讲解 — 巨头反应
- P27: anchor        # 过渡7
- P28: anchor        # 内容7 — 开源
- P29: dense         # 讲解 — 双雄对比
- P30: anchor        # 封底 — 前瞻

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
