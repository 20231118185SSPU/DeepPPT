# DeepPPT 前置构思与领域素材路由设计方案

> **Archive status (2026-07-02)**: 本文是 `PPT Briefing` 与 `Image Source Routing` 落地前的设计方案归档。核心方案已实现并同步到 `AGENTS.md`、`skills/ppt-master/SKILL.md`、`skills/ppt-master/workflows/ppt-briefing.md`、`skills/ppt-master/references/image-source-routing.md`、`skills/ppt-master/scripts/image_source_router.py`、`skills/ppt-master/scripts/rendered_layout_check.py` 和 `README.md`。后续以已提交的 workflow / reference / script 文档为准，本文仅保留设计背景和决策脉络。

## 0. 结论摘要

本轮只做方案设计，不修改运行代码。

当前 DeepPPT 的 topic-only 入口已经有 `deep-research`、`content-selection`、`detailed-outline` 和 Step 4 Eight Confirmations，但它们解决的是“调研什么”和“生成时怎么确认设计参数”，没有在调研前先确认“这到底要做成什么 PPT”。结果是：用户只给一个主题时，系统很快进入大纲、调研、图片搜索和生成链路，早期假设一旦偏离，后续产物会在错误方向上越做越完整。

图片搜索问题不是单个 provider 好坏，而是缺少领域感知路由。`image_search.py` 当前默认链路会把已配置 API key 的 Pexels/Pixabay/Unsplash/Flickr 放到前面；而 `image-searcher.md` 文档描述为 zero-config provider 优先，脚本和文档已经漂移。更重要的是，泛图库只适合氛围图、背景图、商业场景图，不适合特定人物、IP 角色、产品截图、专业概念、历史事件细节等高语义素材。

建议新增一个 topic-only 专属的 `PPT Briefing` 阶段，位于 `Topic -> deep-research` 之前；再新增一个 `Image Source Routing` 层，位于详细大纲和图片获取之间，负责按主题领域选择 source pack，禁用或降级泛图库默认优先级。

---

## 1. 已审计文件

| 类别 | 文件 |
|---|---|
| 入口与主流程 | `AGENTS.md`, `skills/ppt-master/SKILL.md` |
| 写作/代码规则 | `docs/rules/prompt-style.md`, `docs/rules/code-style.md` |
| 研究流程 | `skills/ppt-master/workflows/deep-research.md`, `workflows/research/step1_outline.md`, `step2_search_plan.md`, `step3_search.md`, `step7_visual.md` |
| 研究后规划 | `skills/ppt-master/workflows/content-selection.md`, `detailed-outline.md`, `image-text-linking.md` |
| 图片角色规则 | `skills/ppt-master/references/image-base.md`, `image-searcher.md`, `strategist.md` |
| 图片搜索代码 | `skills/ppt-master/scripts/image_search.py`, `scripts/image_sources/provider_common.py`, `scripts/image_sources/provider_browser.py`, `scripts/image_sources/` provider 列表 |

---

## 2. 当前 topic-only 流程图

```text
用户只给主题
  |
  v
SKILL.md Step 1 判断 no source content
  |
  v
deep-research workflow
  |
  +-- Step 0 初始化项目
  +-- Step 1 生成 PPT 大纲
  |     - 一次性确认主题/场景/受众/页数/语言/slug
  |     - 只有主题时基于常识建立待验证假设
  |     - 用户确认大纲
  |
  +-- Step 2 搜索计划
  |     - 4-6 个搜索维度
  |     - 每维度 3+ 搜索轮次
  |     - 用户确认搜索计划
  |
  +-- Step 3 逐页搜索
  +-- Step 4 整合
  +-- Step 5 结构化分析
  +-- Step 6 研究报告
  +-- Step 7 视觉策略/参考图
  |
  v
research_gate.py -> sync_research_outputs.py
  |
  v
SKILL.md Step 2 Content Selection
  |
  v
Step 3 Template Option
  |
  v
Step 4 Strategist / Eight Confirmations
  |
  v
Step 5 Image Acquisition
  |
  v
Step 6 Executor
```

### 当前确认点

| 位置 | 确认内容 | 问题 |
|---|---|---|
| deep-research Step 1 | 主题、场景、受众、页数、语言、大纲 | 仍然已经进入“研究大纲生成”，缺少制作目标、验收标准、素材边界、叙事类型的系统构思 |
| deep-research Step 2 | 搜索维度、搜索轮次、来源类型、逐页素材计划 | 确认的是搜索计划，不是 PPT 创作蓝图 |
| content-selection | 从调研报告中选择内容维度 | 发生在研究之后，无法防止研究方向一开始就错 |
| Eight Confirmations | 画布、页数、受众、mode、style、色彩、图标、图片策略等 | 已经接近正式生成，太晚才确认核心方向 |

---

## 3. 当前图片搜索链路图

```text
Strategist / detailed-outline
  |
  v
design_spec.md §VIII Image Resource List
  |
  +-- Acquire Via: ai  -> image_gen.py --manifest
  |
  +-- Acquire Via: web -> image_search.py
         |
         +-- single query 或 --batch image_queries.json
         |
         +-- _default_provider_chain()
         |     当前脚本实际顺序:
         |       keyed providers first if key exists:
         |       pexels -> pixabay -> unsplash -> flickr
         |       then openverse -> wikimedia -> nasa -> smithsonian
         |
         +-- search_and_download()
         |     - 聚合候选
         |     - score_candidate()
         |     - 下载最优候选
         |     - 保存 candidates pool
         |
         +-- API provider 全失败后
               provider_browser fallback:
               Bing/Yandex 默认，可选 Google
               返回 Browser License / verify before public use
```

### 文档与代码漂移

| 文件 | 描述 |
|---|---|
| `references/image-searcher.md` | 写的是默认 `openverse -> wikimedia -> nasa -> smithsonian -> keyed providers -> browser fallback` |
| `scripts/image_search.py` | 实际 `_default_provider_chain()` 是已配置 key 的 `pexels/pixabay/unsplash/flickr` 优先，再追加 zero-config providers |

这个漂移会放大泛图库污染：只要环境里配置了 key，特定语义素材也会优先被商业图库候选覆盖。

---

## 4. 当前流程问题清单

### 4.1 需求模糊但继续生成的风险点

| 风险点 | 当前位置 | 影响 |
|---|---|---|
| 只有主题时直接进入 deep-research | `SKILL.md` Step 1 | 系统把“主题”误当成“制作任务”，过早构建大纲 |
| deep-research Step 1 的确认项偏基础 | `workflows/research/step1_outline.md` | 确认主题/场景/受众/页数，但没有确认叙事框架、资料深度、视觉边界、验收标准 |
| 搜索计划由初始大纲派生 | `step2_search_plan.md` | 初始大纲若错，搜索维度和素材策略一起错 |
| 视觉策略发生在研究末尾 | `step7_visual.md` | 到 Step 7 才系统讨论参考图和视觉策略，无法约束早期素材来源 |
| Content Selection 发生在研究之后 | `content-selection.md` | 只能从已有研究报告中筛选，不能修正研究前的创作定位 |
| Eight Confirmations 太晚 | `SKILL.md` Step 4 | 此时项目、研究报告、内容选择、大纲均已形成，方向调整成本高 |
| 图片 `Reference` 仍易变成通用关键词 | `image-base.md`, `image-text-linking.md` | 虽已有内容感知规则，但没有 source pack 和领域路由 |

### 4.2 图片搜索风险点

| 风险点 | 当前位置 | 影响 |
|---|---|---|
| keyed generic providers 实际默认优先 | `image_search.py` | 泛图库结果在语义不准时先进入候选池 |
| provider 链没有领域判断 | `image_search.py` | 二次元/产品/人物/历史/学术素材走同一链路 |
| `simplify_query()` 会压缩长语义 | `provider_common.py` | 对图库 API 有帮助，但会丢失 IP/角色/作品设定等关键限定 |
| browser fallback 可直接下载图片 URL | `provider_browser.py` | 适合作发现与候选池，不适合作自动版权安全下载 |
| Google Images 没有被清晰定义为“发现入口” | `image-searcher.md`, `provider_browser.py` | 容易被误用成下载源 |
| 泛图库 license 合规不等于语义正确 | provider 层 | Pexels/Pixabay 可无署名，但不保证主体是指定人物/角色/产品 |

---

## 5. 现有图库 provider 适用/不适用场景

| Provider | 适用场景 | 不适用场景 | 建议默认地位 |
|---|---|---|---|
| Pexels | 商务氛围、办公场景、人物剪影、通用背景 | 特定人物、真实产品、IP 角色、专业概念、历史事件 | 仅在 `generic_atmosphere` source pack 启用 |
| Pixabay | 通用照片、插画、低风险背景 | 精确主体、专业资料图、需要权威来源的图 | 低优先级 fallback |
| Unsplash | 高质量摄影、情绪氛围、自然/城市背景 | 需要事实准确的主体图、产品截图、角色设定 | 低优先级 fallback |
| Flickr | CC 摄影、地点、事件候选 | 版权/作者字段需复核；主体歧义高 | 候选池来源，需 review |
| Openverse | 开放版权聚合、博物馆/Commons/Flickr 线索 | 聚合页质量不均、预览图尺寸不稳、元数据不一定足以确认主体 | 开放版权 source pack，非全局默认优先 |
| Wikimedia | 百科、历史、地理、科学、人物、机构图 | 商业氛围图、现代产品官方渲染、IP 官方设定 | 学术/历史/百科 source pack 优先 |
| NASA | 航天、天文、地球科学、NASA 技术图 | 非 NASA 领域 | 航天/科学 source pack 优先 |
| Smithsonian | 历史、艺术、文化、自然史、博物馆开放藏品 | 现代商业产品、二次元/IP | 博物馆/历史 source pack 优先 |
| Browser / Google Images | 发现来源页、找官方图、专题 Wiki、产品页、候选池 | 自动下载为最终可用图；高歧义主体的无复核引用 | 发现入口，只记录 provenance 和风险 |

---

## 6. 新流程设计：PPT Briefing 阶段

### 6.1 推荐插入位置

```text
Topic-only request
  |
  v
PPT Briefing  ⛔ 用户确认
  |
  v
Deep Research
  |
  v
Content Selection
  |
  v
Detailed Outline
  |
  v
Strategist / Eight Confirmations
  |
  v
Image Source Routing
  |
  v
Image Acquisition / Generation
```

### 6.2 新 workflow 文件

建议新增：

```text
skills/ppt-master/workflows/ppt-briefing.md
```

目录 `workflows/` 现有文件主要为中文，因此该文件应使用中文，遵守 `docs/rules/prompt-style.md`。

### 6.3 产物

| 文件 | 位置 | 用途 |
|---|---|---|
| `ppt_brief.md` | `<project>/ppt_brief.md` 或 `<project>/_brief/ppt_brief.md` | 人类可读创作蓝图 |
| `ppt_brief.json` | `<project>/ppt_brief.json` 或 `<project>/_brief/ppt_brief.json` | 机器可读输入，喂给 deep-research / Strategist / source router |

建议放在项目根目录，理由是它不是研究中间产物，而是整个 PPT 项目的上游约束。`_research/` 下游步骤应读取它。

### 6.4 Brief 字段

```json
{
  "topic": "",
  "user_goal": "",
  "target_audience": "",
  "usage_context": "",
  "decision_stage": "explore | persuade | report | teach | launch | entertain",
  "page_range": {"min": 8, "max": 15, "preferred": 12},
  "narrative_frame": {
    "recommended_mode": "pyramid | narrative | instructional | showcase | briefing | custom",
    "story_arc": "",
    "opening_hook": "",
    "closing_intent": ""
  },
  "content_boundary": {
    "must_include": [],
    "must_exclude": [],
    "depth": "overview | standard | deep | expert",
    "freshness": "evergreen | recent | latest",
    "region_or_language": ""
  },
  "visual_direction": {
    "style_intent": "",
    "layout_preference": "dense | balanced | visual-led | text-led",
    "image_density": "none | low | medium | high",
    "chart_density": "none | low | medium | high"
  },
  "material_strategy": {
    "domain": "",
    "domain_confidence": 0.0,
    "preferred_source_packs": [],
    "disabled_source_packs": [],
    "generic_stock_policy": "disabled_by_default | fallback_only | allowed_for_atmosphere",
    "requires_official_assets": false,
    "requires_manual_asset_review": false
  },
  "source_strategy": {
    "tier1_sources": [],
    "tier2_sources": [],
    "platforms": [],
    "search_languages": []
  },
  "copyright_and_risk": {
    "public_distribution": false,
    "copyright_risk_level": "low | medium | high",
    "google_images_policy": "discovery_only",
    "manual_review_required": []
  },
  "acceptance_criteria": {
    "content": [],
    "visual": [],
    "asset": [],
    "delivery": []
  },
  "confirmation_items": []
}
```

### 6.5 用户确认机制

`PPT Briefing` 必须是 topic-only 的第一个 BLOCKING 阶段。用户未确认前，不进入 deep-research。

确认摘要建议包含：

| 项目 | 展示内容 |
|---|---|
| 目标 | 这份 PPT 要帮助谁做什么决策/理解/行动 |
| 受众 | 受众身份、知识背景、阅读耐心 |
| 叙事 | 推荐的故事线和开场/结尾 |
| 页数 | 建议范围与理由 |
| 内容边界 | 要讲/不讲什么 |
| 资料深度 | 概览、标准、深度、专家级 |
| 视觉 | 风格方向、版式倾向、图表密度 |
| 素材 | 领域 source pack、禁用 source、是否人工复核 |
| 验收 | 用户确认“做到什么算完成” |

---

## 7. 领域感知素材路由设计

### 7.1 新 reference 和脚本

建议新增：

```text
skills/ppt-master/references/image-source-routing.md
skills/ppt-master/scripts/image_source_router.py
```

其中 reference 规定角色行为和 source pack；脚本负责读取 `ppt_brief.json`、`detailed_outline.json`、`image_queries.json`，给每条 web/AI reference row 标注路由策略。

### 7.2 路由输入

| 输入 | 用途 |
|---|---|
| `ppt_brief.json.material_strategy.domain` | Deck 级主题领域 |
| `detailed_outline.json.pages[].visual_need` | 每页主体、图片类型、参考图需求、槽位尺寸 |
| `image_queries.json.items[]` | 即将执行的 web 搜索任务 |
| `design_spec.md §VIII` | 最终图片资源列表 |
| `visual_strategy.json.reference_images[]` | deep-research 阶段已批准参考图 |

### 7.3 路由输出

建议扩展 `image_queries.json` item，保持旧字段兼容：

```json
{
  "filename": "p05_zhongli_ref.jpg",
  "query": "Genshin Impact Zhongli official art full body",
  "slide": "P05",
  "purpose": "reference:image subject for character page",
  "orientation": "portrait",
  "status": "Pending",
  "source_pack": "anime_game_ip",
  "preferred_sources": ["official_site", "official_wiki", "fandom", "moegirl"],
  "disabled_providers": ["pexels", "pixabay", "unsplash"],
  "allow_generic_stock": false,
  "discovery_only": true,
  "needs_manual_review": true,
  "copyright_risk": "high",
  "selection_reason": "IP-specific character; generic stock cannot satisfy subject identity"
}
```

### 7.4 Source Pack 定义

每个 source pack 至少包含：

| 字段 | 说明 |
|---|---|
| `id` | source pack 标识 |
| `domains` | 适用主题 |
| `priority_sources` | 优先来源 |
| `allowed_providers` | 可自动下载的 provider |
| `disabled_providers` | 默认禁用 provider |
| `query_builder` | 查询构造规则 |
| `copyright_policy` | 版权风险和使用要求 |
| `manual_review` | 是否需要人工确认 |
| `provenance_fields` | 必须保存的来源字段 |

---

## 8. 图片来源路由矩阵

| 领域 | 识别信号 | 优先来源 | 禁用/降级来源 | 查询构造 | 版权/复核 |
|---|---|---|---|---|---|
| 二次元 / 游戏角色 / IP | 角色名、作品名、官方设定、皮肤、剧情、同人高发词 | 官方站、官方 Wiki、专题 Wiki、Fandom、萌娘百科、PRTS、BiliWiki、游戏官网素材页 | Pexels、Pixabay、Unsplash 默认禁用；Openverse/Wikimedia 仅当确有百科图且主体匹配 | `作品名 + 角色名 + official art/key visual/官方原画/设定图`，加排除 `stock photo/PPT模板/mockup` | 高版权风险；Google Images 只能发现来源页；必须人工确认主体和授权 |
| 游戏 / 产品界面 / 软件 | 产品官网、应用名、UI、dashboard、screenshot | 官网、产品页、文档、App Store/Steam/发布稿、官方 YouTube 截图、浏览器 URL capture | 泛图库禁用；Openverse 通常无效 | `品牌 + 产品名 + feature/page/screenshot`；优先直接 URL capture | 截图通常需用途复核；记录 URL、时间、页面标题 |
| 真实人物 | 全名、职位、机构、portrait、founder、CEO | 官方 bio、公司新闻稿、会议主办方、权威媒体、Wikipedia/Wikimedia | 泛图库禁用；browser 只作候选 | `全名 + 身份标签 + official portrait` | 高歧义；必须记录 source_page_url；人工确认同名风险 |
| 品牌 / 产品 | 品牌名、型号、发布会、官方图、logo、packshot | 官网、新闻稿、产品页、品牌素材包、监管/专利/电商官方旗舰页 | 泛图库禁用，除非只要场景氛围图 | `品牌 + 产品型号 + official product image/rendering/press kit` | 商标/版权风险；公开发布需复核 |
| 学术 / 科普 | 论文、理论、自然科学、技术原理、实验图 | Wikipedia、Wikimedia、NASA、NOAA、NIH、大学/研究机构、论文图表、博物馆开放库 | Pexels/Unsplash 仅背景氛围 | `概念 + diagram/schema/visualization + institution` | 优先开放版权；图表数据需来源 |
| 历史 / 文化 / 博物馆 | 年代、人物、文物、事件、地点、艺术品 | Wikimedia、Smithsonian、博物馆开放库、国家档案馆、图书馆数字馆藏 | Pexels/Unsplash 仅现代场景背景 | `事件/人物/文物 + archive/photo/portrait` | 记录馆藏页、license、作者 |
| 新闻 / 近期事件 | 最近、趋势、事故、政策、发布 | 官方公告、新闻稿、权威媒体、监管机构、Google Images 发现来源 | 泛图库禁用 | `事件名 + 日期 + 官方/新闻源` | 高时效和版权风险；通常人工确认 |
| 商业氛围 / 背景图 | 办公、会议、团队、城市、自然、抽象 | Pexels、Unsplash、Pixabay、Openverse | 无需禁用，但仍要内容匹配 | 简短英文名词短语 | 低语义风险；仍记录 license |
| 数据图 / 报告截图 | chart、dashboard、报告页、市场规模 | 官方报告 PDF、行业数据库、URL capture、svg-native 重绘 | 泛图库禁用 | `报告名/机构 + chart/table/figure + 年份` | 优先重绘为 SVG；截图需来源标注 |

---

## 9. 默认搜索后端调整方案

### 9.1 默认策略

| 情况 | 默认 provider 策略 |
|---|---|
| 未声明 source pack | 走 conservative chain：Wikimedia/NASA/Smithsonian/Openverse，然后 browser discovery；keyed generic 不自动优先 |
| `generic_atmosphere` | 启用 Pexels/Pixabay/Unsplash/Flickr，并按质量排序 |
| `anime_game_ip` | 禁用 Pexels/Pixabay/Unsplash；browser/Google 只发现来源页；结果 `Needs-Manual` 或候选池 |
| `official_product` | 优先 URL capture / official site；泛图库禁用 |
| `academic_science` | NASA/Wikimedia/机构库优先；图库 fallback 仅氛围 |
| `historical_culture` | Wikimedia/Smithsonian/博物馆库优先；图库 fallback 仅现代背景 |

### 9.2 Google Images 使用规则

Google Images 只能作为 discovery path：

| 必须做 | 禁止做 |
|---|---|
| 记录 Google/Bing/Yandex 搜索查询 | 把 Google 缩略图当最终下载源 |
| 打开并记录原始来源页 URL | 无来源页时直接用于 PPT |
| 标记 `discovery_only: true` | 把 browser result 直接当版权安全图片 |
| 记录 `copyright_risk` 和 `manual_review_required` | 用它驱动人物/IP/产品 img2img |
| 鼓励 URL capture 官方页面 | 默认下载搜索结果图片 |

### 9.3 兼容旧项目

| 旧行为 | 兼容策略 |
|---|---|
| 旧 `image_queries.json` 没有 `source_pack` | 按 conservative 默认链处理，或在脚本中用 legacy mode 保持原行为 |
| 用户显式 `--provider pexels` | 继续尊重显式 provider |
| 旧项目已生成 `image_sources.json` | 不重写 provenance；只在新搜索任务中应用路由 |
| 环境已配置图库 key | key 保留可用，但不再自动优先 |
| 已有 provider 文件 | 不删除，只通过路由和默认链降级 |

---

## 10. 接入主流程的建议改动点

| 阶段 | 文件 | 改动 |
|---|---|---|
| Topic-only 路由 | `AGENTS.md`, `SKILL.md` | 将 no source content 从 `deep-research first` 改为 `ppt-briefing -> user confirm -> deep-research` |
| 新工作流 | `workflows/ppt-briefing.md` | 定义 Creative Brief 产物、确认项和交接 |
| deep-research Step 1/2 | `workflows/research/step1_outline.md`, `step2_search_plan.md` | 读取 `ppt_brief.json`，不得再只凭主题生成大纲和搜索计划 |
| detailed-outline | `workflows/detailed-outline.md` | 将 `ppt_brief` 的叙事框架、内容边界、素材策略写入逐页计划 |
| image-text-linking | `workflows/image-text-linking.md` | 除内容关键词外，注入 source pack 和禁用 provider |
| image reference | `references/image-source-routing.md` | 定义 source pack 与 Google discovery policy |
| image-searcher | `references/image-searcher.md` | 更新 provider 默认链，说明 keyed generic fallback policy |
| image-base | `references/image-base.md` | 增加 source routing handoff |
| Strategist | `references/strategist.md` | §VIII 写入 source pack / risk / manual review 字段 |
| 搜索脚本 | `scripts/image_source_router.py` | 新增路由层 CLI |
| 搜索脚本 | `scripts/image_search.py` | 支持 `source_pack`, `disabled_providers`, `allow_generic_stock`, `discovery_only`, `needs_manual_review` |
| provider 公共层 | `scripts/image_sources/provider_common.py` | 候选评分增加 source_pack 语义约束；保留旧评分兼容 |
| browser provider | `scripts/image_sources/provider_browser.py` | 明确 browser candidate 的 discovery/provenance 字段，不自动视作许可安全 |
| gates | `scripts/research/asset_gate.py` | 检查高风险 source pack 是否有 manual review / provenance |

---

## 11. 分阶段实施计划

### Phase 1：文档与流程接入

1. 新增 `workflows/ppt-briefing.md`。
2. 更新 `SKILL.md` 和 `AGENTS.md` topic-only 路由。
3. 更新 `deep-research.md`，声明 deep-research 消费 `ppt_brief.json`。
4. 更新 `research/step1_outline.md` 和 `step2_search_plan.md`，把 Brief 作为上游约束。

验收：

- topic-only 请求必须先产出 `ppt_brief.md/json`。
- 用户未确认 Brief 前不进入 deep-research。

### Phase 2：Source Routing 规范

1. 新增 `references/image-source-routing.md`。
2. 更新 `image-base.md`、`image-searcher.md`、`image-text-linking.md`。
3. 更新 `detailed-outline.md` 的 `visual_need`，增加 source routing 字段。
4. 更新 `strategist.md`，让 §VIII 可记录 source pack、risk、manual review。

验收：

- 每个 web row 都能说明为什么走某类来源。
- 高歧义主体必须默认 `needs_manual_review: true`。

### Phase 3：路由脚本

1. 新增 `scripts/image_source_router.py`。
2. 输入 `ppt_brief.json`、`detailed_outline.json`、`image_queries.json`。
3. 输出增强后的 `image_queries.json` 或 `image_source_routes.json`。
4. 支持 dry-run，显示每条 row 的 source pack 与禁用 provider。

验收：

- 不联网也能为 query manifest 打路由标签。
- 泛图库不会出现在 IP/产品/人物 source pack 的默认 provider 中。

### Phase 4：`image_search.py` 默认链调整

1. 修改 `_default_provider_chain()`：keyed generic 不再默认优先。
2. 支持 per-item `source_pack`、`preferred_providers`、`disabled_providers`。
3. 支持 `discovery_only`：browser/Google 结果进入候选池和 provenance，不自动最终采用。
4. 保留 `--provider` 显式覆盖。

验收：

- 已配置 Pexels key 时，特定语义素材不会自动先查 Pexels。
- 明确商业氛围图时仍能使用 Pexels/Pixabay/Unsplash。

### Phase 5：Gate 与可观测性

1. `asset_gate.py` 检查高风险素材是否有 `source_page_url`、`copyright_risk`、`manual_review_required`。
2. Dashboard/日志展示 source pack、provider chain、fallback reason。
3. `image_sources.json` 增加 `source_pack`、`selection_reason`、`copyright_risk`、`manual_review_status`。

验收：

- fallback 结果有来源、关键词、选择理由、版权风险记录。
- Google Images/browser 结果不会以“许可已清”姿态进入最终素材。

---

## 12. 风险与兼容性分析

| 风险 | 影响 | 缓解 |
|---|---|---|
| 前置 Brief 增加交互时间 | topic-only 生成不再“一句话就跑” | 只对 topic-only 强制；有完整源材料可跳过或简化 |
| 用户不想细填 Brief | 可能中断动线 | 提供推荐默认值，但仍要求确认 |
| source pack 判断错误 | 可能漏掉可用来源 | 允许用户在 Brief 中覆盖；router dry-run 可见 |
| 泛图库降级后找图变慢 | 商务氛围图可能少一步 | `generic_atmosphere` 明确启用图库 |
| Google discovery 不能自动下载 | 增加人工复核 | 这是版权与语义准确性的必要代价 |
| 旧项目 manifest 无新字段 | Gate 误报 | Gate 对旧项目字段缺失降级为 warning；新项目强制 |
| 文档和脚本再次漂移 | 行为不一致 | 引入路由脚本作为单一执行入口，reference 反链脚本 |

---

## 13. 验收问题回答

### 为什么泛图库不适合作为默认核心来源？

泛图库擅长“看起来像某类场景”的照片，不擅长“就是这个主体”。它们的 license 可能合规，但标题、标签和摄影主体通常无法证明特定人物、角色、产品、历史事件或专业概念的准确性。对于语义要求高的 PPT，错误主体比没有图片更糟。

### 新的 PPT Briefing 阶段解决了哪些需求模糊问题？

它在调研前确认目标、受众、使用场景、叙事框架、页数范围、内容边界、资料深度、视觉方向、素材策略、版权风险和验收标准，防止系统把一个模糊主题直接扩展成错误的大纲和搜索计划。

### 不同领域分别走哪些素材来源？

二次元/游戏/IP 走官方站、专题 Wiki、萌娘百科/Fandom/PRTS 等；人物/品牌/产品走官网、新闻稿、产品页和 Google Images 发现来源；学术/科普/历史走 Wikipedia/Wikimedia、NASA、学术机构、博物馆开放库；商业氛围图才走 Pexels/Pixabay/Unsplash 等泛图库。

### Google Images 如何使用才不造成版权和来源不可追踪风险？

只作为发现入口。必须记录查询、搜索引擎、原始来源页、版权风险、人工复核状态；不能把 Google 缩略图或 browser 下载 URL 当作许可安全的最终素材。

### 旧流程如何兼容？

只对 topic-only 强制 Brief；旧 `image_queries.json` 没有 source pack 时走 conservative 默认或 legacy 兼容；显式 `--provider` 继续有效；不删除现有 provider；已生成的 `image_sources.json` 不回写破坏。

### 用户确认点在哪里？

新增确认点在 `PPT Briefing` 结束、deep-research 之前。现有 deep-research Step 1/2、content-selection、Eight Confirmations 仍保留，但它们不再承担“从零创作定位”的职责。

### 后续代码实施应改哪些文件？

优先改 `SKILL.md`、`AGENTS.md`、新增 `workflows/ppt-briefing.md`、新增 `references/image-source-routing.md`、更新 `deep-research` 相关 workflow、`image-text-linking.md`、`image-base.md`、`image-searcher.md`、`strategist.md`，再新增 `scripts/image_source_router.py` 并调整 `scripts/image_search.py` 默认链和 manifest 字段。
