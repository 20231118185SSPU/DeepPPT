---
description: 深度调研 Step 7 — 视觉策略。研究领域视觉惯例，生成图片提示词，收集参考图片。
---

# Step 7: 视觉策略（Visual Strategy）

> 调研的最后一步。研究主题领域的视觉设计惯例，为每种页面类型生成 AI 图片提示词，收集参考图片。

**输入**: `_research/step6_narrative/research_report.md` + `_research/step5_analysis/research_analysis.json`
**输出**: `_research/step7_visual/visual_strategy.json` + `ref/`

---

## 7.1 领域视觉研究

在搜索阶段（Step 3）已收集的图片基础上，补充研究：

1. **色彩惯例**: 该领域常见的色彩搭配
   - 科技：蓝色系、深色背景
   - 医疗：绿色/蓝色、白色背景
   - 金融：深蓝/金色、专业感
   - 教育：明亮色彩、亲和力
   - 发布会：黑色/深灰、产品为焦点

2. **排版风格**: 该领域 PPT 的常见排版模式
   - 信息密度偏好（简约 vs 密集）
   - 图文比例偏好
   - 标题风格（大标题 vs 小标题）

3. **图标语义**: 该领域常用的图标和视觉隐喻

---

## 7.2 AI 图片提示词

为每种页面类型生成图片生成提示词：

**硬规则**:
- 提示词仅包含：**主体 + 意图 + 构图**
- ❌ 不包含风格词汇（如"扁平化"、"极简"、"科技感"）
- ❌ 不包含颜色代码（HEX）
- ❌ 不包含字体指令

> 风格和颜色由 Strategist 在 Eight Confirmations 中决定，此处不预设。

### 提示词模板

```json
{
  "page_type": "cover",
  "prompt": "A panoramic view of a futuristic cityscape at sunset, symbolizing technological advancement and ambition. Wide-angle composition with a central focal point.",
  "intent": "开场封面，传达主题的宏大愿景",
  "composition": "宽幅全景，中心焦点"
}
```

```json
{
  "page_type": "content",
  "prompt": "A close-up of a human hand and a robotic hand reaching towards each other, with glowing data streams flowing between them. Centered composition, dramatic lighting.",
  "intent": "人机协作内容页的配图",
  "composition": "居中对称，戏剧性光照"
}
```

---

## 7.2a 视觉优先级分类

为每页分配 `visual_priority`（见 executor-base.md §19），决定渲染策略：

| 页面角色 | visual_priority | 理由 |
|---------|----------------|------|
| cover | **HIGH** | 封面是第一印象，需要全屏 AI 背景 |
| hook | **HIGH** | 开场钩子需要视觉冲击力 |
| ending | **HIGH** | 结尾页是最后印象 |
| content (产品展示) | **HIGH** | 产品/关键数据页需要突出 |
| transition | normal | 过渡页标准处理 |
| evidence | normal | 论据页标准处理 |
| deep_dive | LOW | 深度分析页以信息密度为主 |
| toc | LOW | 目录页功能性优先 |
| synthesis | normal | 总结页标准处理 |

**规则**:
- HIGH 页 ≥ 总页数的 20%，≤ 40%（太多则失去冲击力）
- 每个 HIGH 页必须有 AI 生成的全屏背景图提示词
- LOW 页不需要背景图，使用纯色背景即可

---

## 7.3 参考图片收集

⛔ **MANDATORY CHECKPOINT**: `_research/step7_visual/ref/` 必须包含至少 1 张参考图片。

收集规则：

| 主题类型 | 最少参考图 | 说明 |
|---------|-----------|------|
| 游戏/IP | 2+ | 需要角色、场景原画 |
| 历史人物 | 1+ | 需要历史照片或画像 |
| 产品发布 | 2+ | 需要产品图、渲染图 |
| 科技/数据 | 1+ | 数据可视化参考 |
| 通用 | 1+ | 色彩/排版参考 |

收集方式：
1. 从 Step 3 搜索结果中筛选高质量图片
2. 使用 `image_search.py` 补充搜索
3. 使用 Playwright 截图特定网页

```bash
# 搜索参考图片
python3 ${SKILL_DIR}/scripts/image_search.py \
  "{领域} design reference {主题}" \
  --filename ref_01.jpg \
  -o <project>/_research/step7_visual/ref/
```

---

## 7.4 输出 JSON

`_research/step7_visual/visual_strategy.json`:

```json
{
  "domain_conventions": {
    "color_palette": ["#1a1a2e", "#16213e", "#0f3460"],
    "typography_style": "large titles, minimal body text",
    "density": "sparse",
    "mood": "professional, authoritative"
  },
  "color_recommendations": {
    "background": ["#0d1117", "#161b22", "#1c1c2e"],
    "primary": ["#58a6ff", "#388bfd"],
    "accent": ["#f78166", "#d29922"],
    "body_text": ["#c9d1d9", "#8b949e"]
  },
  "image_prompts": [
    {
      "page_type": "cover",
      "page_id": "P01",
      "visual_priority": "HIGH",
      "prompt": "...",
      "intent": "...",
      "composition": "..."
    },
    {
      "page_type": "content",
      "page_id": "P04",
      "visual_priority": "normal",
      "prompt": "...",
      "intent": "...",
      "composition": "..."
    },
    {
      "page_type": "deep_dive",
      "page_id": "P09",
      "visual_priority": "LOW",
      "prompt": "...",
      "intent": "...",
      "composition": "..."
    }
  ],
  "reference_images": [
    {
      "path": "ref/ref_01.jpg",
      "source": "Pexels",
      "purpose": "色彩和排版参考"
    }
  ]
}
```

---

## 交接 — 调研完成

所有 7 步完成。产出物清单：

```
_research/
├── step1_outline/outline.md + outline.json
├── step2_search_plan/search_plan.json
├── step3_search/p{NN}_*.md + search_manifest.json + images/
├── step4_consolidated/consolidated.md
├── step5_analysis/research_analysis.json
├── step6_narrative/research_report.md
└── step7_visual/visual_strategy.json + ref/
```

**下一步**: 将产物同步到主流程目录，进入 SKILL.md 主管线：

```bash
# 同步到主流程目录
cp _research/step6_narrative/research_report.md sources/
cp _research/step5_analysis/research_analysis.json analysis/
cp _research/step7_visual/visual_strategy.json analysis/
cp -r _research/step7_visual/ref/* images/ref/
cp -r _research/step3_search/images/* images/web_assets/
```

然后进入 Content Selection → Detailed Outline → Eight Confirmations → Executor。
