# DeepSeek Evolution - Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline. Read once by downstream roles for context.
>
> Machine-readable execution contract: `spec_lock.md` (color / typography / icon / image short form). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep both in sync; on divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | DeepSeek Evolution |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 30 |
| **Design Style** | dark-tech + narrative |
| **Target Audience** | AI/技术从业者 + 对 AI 发展感兴趣的泛科技受众 |
| **Use Case** | 技术分享会 / 行业分析 / 内部培训 |
| **Content Strategy** | balanced — 从调研结果重构叙事，保留所有核心事实，重组为故事弧线 |
| **Created Date** | 2026-06-21 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280 × 720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top/bottom 50px |
| **Content Area** | 1160 × 620 |

---

## III. Visual Theme

### Theme Style

- **Mode**: `narrative` — 故事弧线结构：起源→铺垫→突破→震撼→影响→展望。DeepSeek 从幻方量化到震动华尔街的天然叙事结构。
- **Visual style**: `dark-tech` — 暗色画布 + 发光强调 + 几何精度。匹配 AI/科技/颠覆性主题，视觉语言呼应 NVIDIA GTC 主题演讲风格。
- **Theme**: Dark theme
- **Tone**: 科技、颠覆、精确、震撼

### Color Scheme

> 从 DeepSeek 品牌蓝(#4D6BFE) + 金融冲击金色(#FFB800) + 暗色科技底色(#0A1628) 三锚点推导。

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0A1628` | 深海蓝黑主背景 |
| **Secondary bg** | `#122240` | 卡片、区块背景 |
| **Primary** | `#4D6BFE` | 标题装饰、关键区块、图标、DeepSeek品牌蓝 |
| **Accent** | `#FFB800` | 关键数据高亮（5930亿、557万）、金融冲击感 |
| **Secondary accent** | `#00D4AA` | 技术突破、创新点的辅助强调 |
| **Body text** | `#E8ECF1` | 正文主文字（亮色） |
| **Secondary text** | `#8899B0` | 注释、来源标注 |
| **Tertiary text** | `#5A6A80` | 页码、辅助信息 |
| **Border/divider** | `#1E3A5F` | 卡片边框、分隔线 |
| **Success** | `#00D4AA` | 正向指标（技术突破） |
| **Warning** | `#FF6B35` | 警示/冲击指标（股价暴跌） |

### AI Image Strategy

- **Image Rendering**: `digital-dashboard` — 暗色科技仪表盘风格，polished UI/data-viz 美学，匹配 dark-tech 视觉风格
- **Image Palette**: `tech-neon` — 充满活力、未来感、高对比度，AI/SaaS/产品发布适用

### Gradient Scheme

```xml
<!-- 标题渐变 -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#4D6BFE"/>
  <stop offset="100%" stop-color="#00D4AA"/>
</linearGradient>

<!-- 背景装饰渐变 -->
<radialGradient id="bgDecor" cx="80%" cy="20%" r="50%">
  <stop offset="0%" stop-color="#4D6BFE" stop-opacity="0.15"/>
  <stop offset="100%" stop-color="#4D6BFE" stop-opacity="0"/>
</radialGradient>

<!-- 数据高光渐变 -->
<linearGradient id="accentGlow" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#FFB800" stop-opacity="0.3"/>
  <stop offset="100%" stop-color="#FFB800" stop-opacity="0"/>
</linearGradient>
```

---

## IV. Typography System

**Typography direction**: CJK-primary + Latin secondary，暗色调下的高可读性 sans-serif

### Font Plan

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei"` | `Inter` | `sans-serif` |
| **Body** | `"Microsoft YaHei"` | `Inter` | `sans-serif` |
| **Emphasis** | `"Microsoft YaHei"` | `Inter` | `sans-serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Inter, "Microsoft YaHei", sans-serif`
- Body: `"Microsoft YaHei", Inter, sans-serif`
- Emphasis: `Inter, "Microsoft YaHei", sans-serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 20px

| Purpose | Ratio to body | px value | Weight |
| ------- | ------------- | -------- | ------ |
| Cover title (hero headline) | 3x | 60px | Bold |
| Chapter / section opener | 2.2x | 44px | Bold |
| Page title | 1.6x | 32px | Bold |
| Hero number (数据页大数字) | 4x | 80px | Bold |
| Subtitle | 1.3x | 26px | SemiBold |
| **Body content** | **1x** | **20px** | **Regular** |
| Annotation / caption | 0.75x | 15px | Regular |
| Page number / footnote | 0.6x | 12px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 50px — 页面标题 + 章节标识
- **Content area**: 570px — 主要内容区域
- **Footer area**: 50px — 页码 + 来源标注

### Layout Pattern Library

| Pattern | 适用页面 |
| ------- | -------- |
| **Full-bleed + floating text** | 封面、封底、过渡页、内容页（AI 背景图全出血 + 浮动文字） |
| **Asymmetric split (3:7)** | 讲解页（左侧小图/数据 + 右侧详细文字） |
| **Symmetric split (5:5)** | 对比页（左右分栏 + 主色分隔线） |
| **Center-radiating** | 金句页（居中大字 + 辐射状氛围背景） |
| **Top-bottom split** | 时间线页（上方标题 + 下方水平时间轴） |
| **Three/four column cards** | 讲解页多要点（圆角矩形卡片 + 要点列表） |
| **Z-pattern / waterfall** | 故事型讲解页（图文交替引导视线） |

---

## VI. Icon System

- **Library**: tech-focused line icons
- **Style**: 发光线框 (glow wireframe) — 1.5px 描边 + 主色(#4D6BFE)发光效果
- **Size**: 标准 24×24px，强调 32×32px
- **常用符号**: GPU芯片、神经网络节点、数据流、代码矩阵、上升/下降箭头、全球网络

---

## VII. Visualization

### 数据可视化规范

- **图表底色**: `#122240`（secondary bg）
- **网格线**: `#1E3A5F`（border/divider），0.5px
- **数据线/柱**: 主色 `#4D6BFE`，高光数据用 `#FFB800`
- **标签文字**: `#8899B0`（secondary text）
- **大数字**: 80px Bold，`#FFB800` 强调关键数字
- **来源标注**: 12px，`#5A6A80`（tertiary text），右下角

---

## VIII. Image Strategy

### AI 生成图（16 张）

| Page | Filename | Content Description | Aspect | Size |
| ---- | -------- | ------------------- | ------ | ---- |
| P01 | P01_cover_bg.png | DeepSeek 品牌蓝+芯片矩阵+数据流光效，中央DeepSeek logo意象 | 16:9 | 2K |
| P02 | P02_toc_bg.png | 暗色科技节点连接图，8个章节节点发光连线 | 16:9 | 2K |
| P03 | P03_trans_ch1.png | 华尔街金融区夜景+蓝色数字雨，震撼氛围 | 16:9 | 2K |
| P04 | P04_content_impact.png | NVIDIA绿+红色暴跌K线+金色数字5930亿飞散 | 16:9 | 2K |
| P07 | P07_trans_ch2.png | GPU服务器集群走廊+蓝色光线+Scaling Law曲线 | 16:9 | 2K |
| P08 | P08_content_scaling.png | 上升曲线+堆积的GPU芯片+算力符号 | 16:9 | 2K |
| P11 | P11_trans_ch3.png | 杭州天际线+量化交易数据流+蓝色光效 | 16:9 | 2K |
| P12 | P12_content_liang.png | 人物剪影+从金融数据到AI神经网络的转型视觉 | 16:9 | 2K |
| P14 | P14_trans_ch4.png | DNA双螺旋+代码矩阵+神经网络结构融合 | 16:9 | 2K |
| P15 | P15_content_v2.png | 神经网络节点爆炸+MLA压缩光效+MoE专家分区 | 16:9 | 2K |
| P17 | P17_content_v3.png | 金色557万数字+破碎的美元符号+对比光效 | 16:9 | 2K |
| P19 | P19_trans_ch5.png | 大脑轮廓+强化学习信号波+思维链涌现光效 | 16:9 | 2K |
| P20 | P20_content_r1.png | 纯RL训练过程可视化+aha moment闪光瞬间 | 16:9 | 2K |
| P22 | P22_quote_aha.png | 大面积留白+思维链涌现的光效意象+反思符号 | 16:9 | 2K |
| P23 | P23_trans_ch6.png | 全球地图+震动波从杭州向外扩散+股市红线 | 16:9 | 2K |
| P24 | P24_content_sputnik.png | Sputnik卫星意象+AI领域震动波+全球连线 | 16:9 | 2K |
| P27 | P27_trans_ch7.png | 开源代码瀑布+全球开发者网络+协作连线 | 16:9 | 2K |
| P28 | P28_content_open.png | 从服务器到桌面的光束+开源符号+代码流 | 16:9 | 2K |
| P30 | P30_ending_bg.png | 开放式星空+地平线+问号光效+未来城市轮廓 | 16:9 | 2K |

### 网络素材图（10 张，通过 Playwright 本地浏览器下载）

| Page | Filename | Content Description | Source Direction |
| ---- | -------- | ------------------- | --------------- |
| P05 | web_nvidia_crash_data.png | NVIDIA 2025-01-27 股价走势图/日K线 | 财经网站截图 |
| P06 | web_sputnik_comparison.png | 1957 Sputnik vs 2025 DeepSeek 对比信息图 | 科技媒体配图 |
| P09 | web_training_cost_trend.png | GPT-3→GPT-4→前沿模型训练成本趋势图 | 数据分析文章图表 |
| P10 | web_scaling_vs_algorithm.png | 算力路线 vs 算法路线对比图 | 技术分析文章 |
| P13 | web_highflyer_story.png | 幻方量化/梁文锋相关图片 | 企业报道配图 |
| P16 | web_mla_architecture.png | MLA 架构原理图解/KV缓存压缩示意 | 论文/技术博客配图 |
| P18 | web_v3_vs_gpt4.png | DeepSeek-V3 vs GPT-4 成本/性能对比图 | 对比分析文章 |
| P21 | web_r1_training_detail.png | R1-Zero/R1 训练流程详解图 | 论文/技术博客配图 |
| P25 | web_ai_stock_timeline.png | 2025-01-27 全球 AI 板块走势时间线 | 财经网站截图 |
| P26 | web_industry_reactions.png | OpenAI/Meta/Google 各自反应策略对比 | 科技媒体配图 |
| P29 | web_deepseek_vs_llama.png | DeepSeek vs Llama 下载量/生态对比图 | HuggingFace/社区数据 |

---

## IX. Content Outline

| Page | Type | Title | Image Source | Deep Dive? |
| ---- | ---- | ----- | ------------ | ---------- |
| P01 | cover | DeepSeek：从零到震撼 AI 界 | AI图 P01_cover_bg.png | — |
| P02 | toc | 八章概览 | AI图 P02_toc_bg.png | — |
| P03 | transition | → §1 华尔街最贵的一天 | AI图 P03_trans_ch1.png | — |
| P04 | content | 5930亿美元的震撼：NVIDIA单日暴跌17% | AI图 P04_content_impact.png | — |
| P05 | deep_dive(data) | NVIDIA市值损失数据 + AI板块连锁反应 | 网络素材 web_nvidia_crash_data.png | 数据展开：具体数字、连锁跌幅 |
| P06 | deep_dive(compare) | Sputnik时刻：1957 vs 2025 两次冲击对比 | 网络素材 web_sputnik_comparison.png | 对比展开：历史映射、冲击本质 |
| P07 | transition | → §2 时代背景：算力焦虑 | AI图 P07_trans_ch2.png | — |
| P08 | content | Scaling Law之辩：更大的模型=更好的AI？ | AI图 P08_content_scaling.png | — |
| P09 | deep_dive(data) | 训练成本飙升趋势：GPT-3→GPT-4→前沿模型 | 网络素材 web_training_cost_trend.png | 数据展开：成本曲线、倍数关系 |
| P10 | deep_dive(compare) | 算力路线 vs 算法路线 | 网络素材 web_scaling_vs_algorithm.png | 对比展开：OpenAI/Meta路线 vs DeepSeek路线 |
| P11 | transition | → §3 幻方量化的底牌 | AI图 P11_trans_ch3.png | — |
| P12 | content | 梁文锋：从量化交易到 AGI | AI图 P12_content_liang.png | — |
| P13 | deep_dive(story) | 幻方量化发展史 + 从量化到AI的转型故事 | 网络素材 web_highflyer_story.png | 故事展开：量化基金→AI实验室的完整故事 |
| P14 | transition | → §4 技术演进：四代模型的进化之路 | AI图 P14_trans_ch4.png | — |
| P15 | content | V2 架构革命：MLA + DeepSeekMoE | AI图 P15_content_v2.png | — |
| P16 | deep_dive(data) | MLA 原理图解：KV缓存压缩 93% | 网络素材 web_mla_architecture.png | 数据展开：MLA机制图解、与MHA/GQA对比 |
| P17 | content | V3 成本颠覆：557万 vs 1亿美元 | AI图 P17_content_v3.png | — |
| P18 | deep_dive(compare) | V3 vs GPT-4 全面对比 | 网络素材 web_v3_vs_gpt4.png | 对比展开：成本/性能/硬件/效率四维对比 |
| P19 | transition | → §5 R1 推理觉醒 | AI图 P19_trans_ch5.png | — |
| P20 | content | R1-Zero：推理能力从纯 RL 中涌现 | AI图 P20_content_r1.png | — |
| P21 | deep_dive(story) | R1-Zero "Aha Moment" + R1 两阶段训练详解 | 网络素材 web_r1_training_detail.png | 故事展开：纯RL涌现→冷启动SFT→GRPO |
| P22 | quote | "aha moment"——模型自发涌现反思 | AI图 P22_quote_aha.png | — |
| P23 | transition | → §6 行业冲击：Sputnik 时刻 | AI图 P23_trans_ch6.png | — |
| P24 | content | Sputnik 时刻：全球 AI 股震动 | AI图 P24_content_sputnik.png | — |
| P25 | deep_dive(data) | 2025-01-27 全球 AI 股走势时间线 | 网络素材 web_ai_stock_timeline.png | 数据展开：各股跌幅、市值损失 |
| P26 | deep_dive(compare) | 行业巨头反应：OpenAI/Meta/Google 策略 | 网络素材 web_industry_reactions.png | 对比展开：三方策略调整 |
| P27 | transition | → §7 开源改变格局 | AI图 P27_trans_ch7.png | — |
| P28 | content | 开源：从 DeepSeek 到每个人的桌面 | AI图 P28_content_open.png | — |
| P29 | deep_dive(compare) | DeepSeek vs Llama：中美开源 AI 双雄 | 网络素材 web_deepseek_vs_llama.png | 对比展开：下载量/许可/生态对比 |
| P30 | ending | 当创新门槛被拉低，下一个颠覆者是谁？ | AI图 P30_ending_bg.png | — |

---

## X. Speaker Notes

> 演讲备注写在 `notes/total.md`。讲解页(P05/P06/P09/P10/P13/P16/P18/P21/P25/P26/P29)的备注必须详细：包含具体数据来源、故事细节、过渡语、素材图讲解引导。Presenter 仅凭备注即可完成有深度的演讲。

---

## XI. Technical Constraints

- **SVG viewBox**: `0 0 1280 720`
- **字体**: PPT-safe stack，每组以预装字体结尾
- **图片路径**: AI图 `images/PXX_xxx.png`，网络素材 `images/web_assets/xxx.png`
- **无 rgba**: 使用 `stop-opacity` 替代
- **圆角**: 统一 8px（卡片），4px（按钮/小元素）
- **阴影**: dark-tech 风格下慎用，仅在需要层次感时使用 `drop-shadow(0 4px 12px rgba(0,0,0,0.3))` 的 SVG 等效
