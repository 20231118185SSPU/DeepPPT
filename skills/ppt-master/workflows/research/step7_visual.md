---
description: 深度调研 Step 7 — 视觉策略。研究领域视觉惯例，生成图片提示词，收集参考图片。
---

# Step 7: 视觉策略（Visual Strategy）

> 调研的最后一步。研究主题领域的视觉设计惯例，为每种页面类型生成 AI 图片提示词，收集参考图片。

**输入**: `_research/step6_narrative/research_report.md` + `_research/step5_analysis/research_analysis.json`
**输出**: `_research/step7_visual/visual_strategy.json` + `ref/`

**Hard rule**: 先做逐页版式策略，再决定图片尺寸和图片获取方式。不得先生成 16:9 通用图片再让 Executor 强行裁剪到版式槽位。

**Hard rule**: 视觉策略是独立交付物。它消费叙事报告和结构化分析，但不重写叙事、不补事实、不生成 SVG。

**Machine gate**: Step 7 完成后必须运行 `python3 ${SKILL_DIR}/scripts/research/research_gate.py <project>`，通过后才允许 `sync_research_outputs.py`。失败必须返回 gate 打印的步骤补齐，不得继续生成 PPT。

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
- 提示词仅包含：**主体 + 意图 + 构图 + 页面文字呼应**
- ❌ 不包含未确认的风格词汇（如"扁平化"、"极简"、"科技感"）
- ❌ 不包含未确认的颜色代码（HEX）
- ❌ 不包含字体指令

> 风格和颜色由 Strategist 在 Eight Confirmations 中决定，此处不预设。

### 7.2b 双轨图片策略

| 页面类型 | 图片策略 | 要求 |
|----------|----------|------|
| cover / toc / transition / ending / breathing content | Type A 概念图 | 可纯文生图；如包含人物、产品、物品、地点、IP 主体，必须绑定参考图 |
| content with `content_mode: image_with_text` | Type B 信息图 | 图片本身承载结构、流程或对比；文字必须呼应页面 core argument |
| deep_dive / comparison / data / timeline | 网络素材优先 | 必须先使用 Step 3 下载素材；失败才允许 AI Type B 或 svg-native 信息卡 |

**图生图参考规则**：任何包含人物、物品、产品、真实场景、IP 角色或可识别对象的 AI 图，都必须有 `reference_image`。只有抽象背景、概念氛围、几何纹理可以不带参考图。

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

⛔ **MANDATORY CHECKPOINT**: `_research/step7_visual/ref/` 必须包含所有需要参考图页面的参考图片。只满足”至少 1 张”不再合格。

### 7.3a 语义搜索上下文（Mandatory）

参考图搜索查询必须包含从页面内容派生的语义上下文，禁止使用通用主题词。

为每张参考图搜索构建 `semantic_context` 对象：

| 字段 | 说明 | 正确示例 | 错误示例 |
|------|------|---------|---------|
| `subject` | 具体主体名（角色名、产品名、系列名） | “原神·钟离” | “游戏角色” |
| `scene` | 具体场景或语境 | “岩王帝君形态站姿全身” | “PPT背景” |
| `style` | 需要的视觉风格 | “游戏官方原画风格” | “科技感” |
| `negative_keywords` | 排除词列表 | [“stock photo”, “template”, “PPT模板”, “mockup”] | (无) |

**关键词派生规则**:

| 规则 | 说明 |
|------|------|
| 从 content_bullets 派生 | 关键词必须从页面 `content_bullets` 和 `core_argument` 中提取，禁止仅用主题名 |
| 包含专有名词 | 角色名、品牌名、产品名、作品名必须出现在搜索词中 |
| 添加排除词 | 每次搜索必须携带 `negative_keywords`：至少排除 “stock photo”, “template”, “PPT模板” |
| 游戏/IP 话题 | 系列名 + 角色名 + “official art” / “官方原画” / “key visual” |
| 产品话题 | 品牌 + 产品名 + “product photo” / “产品图” / “渲染图” |
| 人物话题 | 全名 + 身份标签 + “portrait” / “肖像” / “照片” |
| 场景/地点 | 地名 + 场景描述 + “photography” / “实拍” |

**Hard rule**: 搜索结果审查时，subject_match 不通过的图片不得进入 `approved: true`。即使图片质量高，主体不匹配就不合格。

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

每张参考图必须写入 `visual_strategy.json.reference_images[]`，并通过审查：

| 字段 | 要求 |
|------|------|
| `page_id` | 绑定到具体页面 |
| `path` | 本地文件路径 |
| `source_url` | 来源 URL 或说明 |
| `subject_match` | 是否匹配该页主体 |
| `style_match` | 是否可支撑统一视觉风格 |
| `cropping_risk` | 低 / 中 / 高 |
| `approved` | 只能 `true` 的图进入 AI manifest |

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
  "per_page_visual_strategy": [
    {
      "page_id": "P04",
      "page_type": "content",
      "content_mode": "image_with_text",
      "layout_plan": {
        "image_area": {"x": 60, "y": 150, "width": 760, "height": 430},
        "text_area": {"x": 850, "y": 150, "width": 370, "height": 430}
      },
      "image_strategy": "ai_type_b",
      "target_image_size": {"width": 760, "height": 430},
      "text_image_link": "图片展示流程，文字解释关键判断",
      "reference_images": ["ref/ref_p04_product.png"]
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

**下一步**: 先运行研究 gate，再将产物同步到主流程目录，进入 SKILL.md 主管线：

```bash
python3 ${SKILL_DIR}/scripts/research/research_gate.py <project>
python3 ${SKILL_DIR}/scripts/research/sync_research_outputs.py <project>
```

`research_gate.py` FAIL 时，按输出的 Return to 步骤补齐搜索、分析、叙事或视觉策略，然后重新运行 gate。只有 PASS 才能 sync。

然后进入 Content Selection → Detailed Outline → Eight Confirmations → Executor。
