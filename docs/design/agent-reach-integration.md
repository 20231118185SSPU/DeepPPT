# Agent-Reach 集成技术设计文档

> 目标：将 Agent-Reach 的多平台内容采集能力接入 DeepPPT 的 deep-research 工作流，扩展素材收集的广度和深度，直接提升 PPT 内容质量。

## 1. 问题定义

### 1.1 当前素材收集能力

deep-research 工作流（`workflows/deep-research.md`）Step 2 的数据通道：

| 通道 | 工具 | 覆盖范围 | 局限 |
|------|------|----------|------|
| 搜索引擎 | IDE WebSearch / WebSearch 工具 | 通用网页索引 | 表层信息、二手内容、SEO 噪音 |
| URL 抓取 | WebFetch / `web_to_md.py` | 单个已知 URL | 需要先知道 URL，无法主动发现 |

图片采集已有独立的 provider 链（`image_search.py`：openverse → wikimedia → pexels → pixabay → browser），这部分不需要改动。

### 1.2 质量瓶颈

| 瓶颈 | 影响 |
|------|------|
| **无法采集视频知识** | YouTube/B站有大量行业讲解、技术教程、案例分析，当前完全不可达 |
| **无法覆盖垂直社区** | V2EX（技术）、雪球（金融）、LinkedIn（商业）、小红书（设计/消费）的深度讨论无法获取 |
| **搜索引擎单点** | 只有一个搜索后端，偶尔限流或返回低质量结果时无降级方案 |
| **无法获取播客/音频内容** | 行业播客中的专家访谈、趋势分析无法转化为 PPT 素材 |

### 1.3 目标

将素材来源从 **"搜索引擎能搜到的"** 扩展到 **"整个互联网上有的"**，让 Strategist 拿到更丰富的素材来设计内容，Executor 填充更精准的证据和案例。

---

## 2. 架构设计

### 2.1 核心决策：不复制框架，只接入 Channel

Agent-Reach 的价值在于它已经封装好的 13 个平台采集能力。DeepPPT 不需要它的 CLI、doctor、cookie 提取等基础设施——只需要它的 **Channel 采集函数**作为数据源。

**集成模式**：将 Agent-Reach 作为 pip 依赖引入，调用其 Channel 的核心采集方法。

### 2.2 系统架构

```
deep-research.md Step 2
│
├─ Phase 1: 搜索引擎（现有，不变）
│   └─ WebSearch + WebFetch
│
├─ Phase 2: 社交/行业平台采集（新增）
│   └─ content_collector.py
│       ├─ B站 → agent_reach.channels.bilibili
│       ├─ YouTube → agent_reach.channels.youtube
│       ├─ V2EX → agent_reach.channels.v2ex
│       ├─ 雪球 → agent_reach.channels.xueqiu
│       ├─ LinkedIn → agent_reach.channels.linkedin
│       └─ 小红书 → agent_reach.channels.xiaohongshu
│
├─ Phase 3: 视频/音频转录（新增）
│   └─ content_collector.py
│       ├─ yt-dlp 下载 → ffmpeg 压缩 → Whisper 转录
│       └─ 输出：带时间戳的文本段落
│
└─ Phase 4: 图片采集（现有，不变）
    └─ image_search.py（provider 链不变）
```

### 2.3 与现有 Provider 链的对称设计

`image_search.py` 已经实现了多 provider 降级模式：

```
openverse → wikimedia → pexels → pixabay → browser
```

新增的 `content_collector.py` 采用相同的架构模式：

```
platform_channel → fallback_channel → web_to_md (通用降级)
```

这是**复用已有的架构模式**，不是引入新范式。

---

## 3. 模块设计

### 3.1 新增文件

| 文件 | 用途 |
|------|------|
| `skills/ppt-master/scripts/content_collector.py` | 多平台内容采集 CLI，统一入口 |
| `skills/ppt-master/scripts/content_sources/` | 平台适配器目录（与 `image_sources/` 对称） |
| `skills/ppt-master/scripts/content_sources/registry.py` | 平台注册表 + 动态路由逻辑 |
| `skills/ppt-master/scripts/content_sources/source_bilibili.py` | B站采集适配器 |
| `skills/ppt-master/scripts/content_sources/source_youtube.py` | YouTube 采集适配器 |
| `skills/ppt-master/scripts/content_sources/source_v2ex.py` | V2EX 采集适配器 |
| `skills/ppt-master/scripts/content_sources/source_xueqiu.py` | 雪球采集适配器 |
| `skills/ppt-master/scripts/content_sources/source_linkedin.py` | LinkedIn 采集适配器 |
| `skills/ppt-master/scripts/content_sources/source_xiaohongshu.py` | 小红书采集适配器 |
| `skills/ppt-master/scripts/content_sources/source_rss.py` | RSS 订阅采集适配器 |
| `skills/ppt-master/scripts/health_check.py` | 工具链健康检查（probe/doctor 模式） |

### 3.2 `content_collector.py` 接口设计

CLI 接口，与 `image_search.py` 对称：

```bash
# 单平台采集
python3 content_collector.py search "量子计算发展趋势" \
    --platform bilibili --top 5 \
    -o projects/demo/sources/collected

# 多平台并行采集（按调研维度自动选择平台）
python3 content_collector.py batch collect_plan.json \
    -o projects/demo/sources/collected

# 视频转录
python3 content_collector.py transcribe "https://www.bilibili.com/video/BV..." \
    -o projects/demo/sources/collected

# 健康检查
python3 content_collector.py doctor
```

### 3.3 `collect_plan.json` 格式

由 deep-research Step 2 的搜索计划自动生成：

```json
{
  "topic": "量子计算发展趋势",
  "queries": [
    {
      "dimension": "核心技术原理",
      "platforms": ["bilibili", "youtube"],
      "query": "量子计算原理讲解 量子比特 量子纠缠",
      "top": 3,
      "include_transcript": true
    },
    {
      "dimension": "行业应用案例",
      "platforms": ["v2ex", "linkedin"],
      "query": "量子计算 应用 商业化",
      "top": 5,
      "include_transcript": false
    },
    {
      "dimension": "市场与投资趋势",
      "platforms": ["xueqiu"],
      "query": "量子计算 投资 市场规模",
      "top": 5,
      "include_transcript": false
    }
  ]
}
```

### 3.4 平台适配器接口

每个适配器实现统一接口（与 Agent-Reach 的 Channel ABC 对称）：

```python
class ContentSource(ABC):
    """内容采集源抽象基类。"""

    name: str                    # 平台标识
    requires_config: bool        # 是否需要 API key / cookie

    @abstractmethod
    def search(self, query: str, top: int = 5) -> list[ContentItem]:
        """搜索平台内容，返回结构化结果。"""
        ...

    @abstractmethod
    def fetch_detail(self, url: str) -> ContentDetail:
        """获取单条内容的详细信息（全文/转录/评论摘要）。"""
        ...

    def check(self) -> SourceStatus:
        """检查平台可用性。返回 ok / missing_dep / config_needed / error。"""
        ...

@dataclass
class ContentItem:
    url: str
    title: str
    platform: str
    snippet: str           # 摘要/前200字
    published_date: str    # 发布日期
    author: str
    content_type: str      # video / post / article / discussion
    engagement: dict       # {views, likes, comments}（平台有的字段）
    relevance_score: float # 0-1，由采集器初步评分

@dataclass
class ContentDetail:
    url: str
    full_text: str         # 全文或转录文本
    sections: list[dict]   # {timestamp, text}（视频转录）或 {heading, text}（文章）
    images: list[str]      # 内嵌图片 URL
    metadata: dict         # 平台特有元数据
```

### 3.5 动态路由逻辑

`registry.py` 核心逻辑——根据调研维度自动选择平台组合：

```python
# 维度 → 平台映射
DIMENSION_PLATFORM_MAP = {
    "技术原理": ["bilibili", "youtube", "v2ex"],
    "行业案例": ["linkedin", "xueqiu", "v2ex"],
    "市场数据": ["xueqiu", "linkedin"],
    "设计灵感": ["xiaohongshu"],
    "用户讨论": ["v2ex", "xiaohongshu"],
    "学术研究": ["youtube"],       # 学术讲座视频
    "趋势预测": ["linkedin", "xueqiu"],
}
```

当首选平台不可达时，自动降级到同维度的备选平台（与 `image_search.py` 的 provider fallback 模式一致）。

---

## 4. 视频/音频转录管线

### 4.1 管线架构

```
URL 输入
│
├─ yt-dlp 提取视频信息 + 下载音频流（仅音频，不下载视频）
│   └─ 输出：临时 .m4a / .opus 文件
│
├─ ffmpeg 压缩 + 分片
│   └─ 16kHz mono WAV，每片 ≤ 25MB（Whisper API 限制）
│
├─ Whisper API 转录
│   ├─ 首选：Groq Whisper（免费、快速）
│   └─ 备选：OpenAI Whisper API
│
└─ 输出：带时间戳的文本段落
    └─ 格式：[{start: "00:01:23", end: "00:02:45", text: "..."}]
```

### 4.2 降级策略

| 条件 | 行为 |
|------|------|
| yt-dlp 不可用 | 跳过视频采集，打印安装提示，继续其他平台 |
| ffmpeg 不可用 | 跳过音频转录，仅获取视频标题/描述/字幕（如有） |
| Whisper API 不可用 | 尝试 yt-dlp 内置字幕提取（`--write-auto-sub`），无字幕则跳过转录 |
| 所有视频源失败 | 不阻断流程，其他平台采集继续 |

---

## 5. 健康检查模块

### 5.1 `health_check.py` 设计

借鉴 Agent-Reach 的 `probe_command()` 模式——实际执行命令而非仅检查路径：

```bash
python3 health_check.py
```

输出示例：

```
DeepPPT 环境健康检查
====================

Tier 0 — 核心依赖（缺失则阻断）
  ✅ python3        3.11.5
  ✅ node           v20.10.0

Tier 1 — 导出依赖（缺失则无法导出 PPTX）
  ✅ ffmpeg         6.0
  ⚠️ inkscape       未安装 — SVG 精细化渲染不可用，svg_to_pptx.py 将使用基础转换

Tier 2 — 采集增强（缺失则跳过对应平台）
  ✅ yt-dlp         2024.01.01
  ✅ gh             2.40.0
  ❌ groq           未配置 — 视频转录将降级到 OpenAI Whisper 或字幕提取

Tier 3 — 可选平台
  ✅ bilibili       可达（API 正常）
  ⚠️ xiaohongshu    需要 cookie — 运行 `content_collector.py setup-cookie` 配置
  ✅ v2ex            可达（公开 API）

结论：核心功能就绪。2 项警告不影响主流程。
```

### 5.2 集成点

在 SKILL.md 的 deep-research 工作流入口处，增加可选的健康检查步骤：

```markdown
## Step 0: 环境检查（可选）

当调研需要视频/社交平台数据时，在 Step 2 前运行：
```bash
python3 ${SKILL_DIR}/scripts/health_check.py
```
根据报告决定哪些数据源可用，调整搜索计划。
```

---

## 6. deep-research 工作流改造

### 6.1 Step 2 改造方案

当前 Step 2 只有"搜索引擎 + URL 抓取"。改造后增加平台采集阶段：

```markdown
## Step 2: Multi-dimensional search（改造后）

### 2.1 Generate search plan（不变）

### 2.2 Execute search（改造）

**Phase 1 — 搜索引擎（保留现有）**
[现有逻辑不变]

**Phase 2 — 社交/行业平台采集（新增）**

根据搜索维度，为每个维度选择 1-2 个高价值平台：

```bash
# 生成采集计划
python3 ${SKILL_DIR}/scripts/content_collector.py plan \
    --topic "<topic>" \
    --dimensions "dim_1,dim_2,..." \
    -o projects/<topic_slug>/collect_plan.json

# 执行采集
python3 ${SKILL_DIR}/scripts/content_collector.py batch \
    projects/<topic_slug>/collect_plan.json \
    -o projects/<topic_slug>/sources/collected
```

平台选择规则：
| 维度类型 | 优先平台 | 备选平台 |
|----------|----------|----------|
| 技术/科学 | B站、YouTube | V2EX |
| 商业/金融 | 雪球、LinkedIn | 通用搜索 |
| 设计/视觉 | 小红书 | Pinterest（via browser） |
| 社会/文化 | B站、V2EX | 通用搜索 |
| 用户观点 | V2EX、小红书 | Reddit（via browser） |

**Phase 3 — 视频转录（新增，按需）**

对 Phase 1/2 发现的高价值视频 URL，提取转录文本：

```bash
python3 ${SKILL_DIR}/scripts/content_collector.py transcribe \
    "<video_url>" \
    -o projects/<topic_slug>/sources/collected
```

仅对以下条件触发：
- 搜索维度需要深度知识（技术原理、行业分析）
- 视频标题/描述与维度高度相关
- 视频长度 ≥ 5 分钟（短视频信息密度不足）

**Phase 4 — 图片采集（不变）**
[现有 image_search.py 逻辑不变]
```

### 6.2 调研质量提升量化

| 指标 | 当前 | 集成后 |
|------|------|--------|
| 数据源类型 | 2 种（搜索引擎 + URL） | 10+ 种（+B站/YouTube/V2EX/雪球/LinkedIn/小红书/RSS） |
| 视频知识 | 0 | 可获取 YouTube/B站视频转录文本 |
| 垂直社区洞察 | 0 | V2EX 技术讨论、雪球金融分析、LinkedIn 商业观点 |
| 单维度平均信息源 | 3-5 个 URL | 8-15 个 URL + 2-3 条视频转录 |
| 搜索可靠性 | 单后端，失败即失败 | 多后端降级，部分失败不影响整体 |

---

## 7. 依赖与安装

### 7.1 新增 Python 依赖

```
# requirements.txt 新增
agent-reach>=0.1.0       # 多平台采集 Channel
yt-dlp>=2024.1.0         # 视频下载（Agent-Reach 已依赖）
```

### 7.2 外部工具依赖

| 工具 | 用途 | 必需/可选 |
|------|------|----------|
| python3 | 核心运行时 | 必需 |
| node | SVG 渲染 | 必需 |
| ffmpeg | 音频转码 | 可选（Tier 1） |
| yt-dlp | 视频下载 | 可选（Tier 2） |
| groq CLI / API key | Whisper 转录 | 可选（Tier 2） |

### 7.3 安装步骤

```bash
# 1. 安装 Python 依赖
pip install agent-reach yt-dlp

# 2. 验证环境
python3 skills/ppt-master/scripts/health_check.py

# 3. 可选：配置平台 cookie（小红书、雪球等需要登录态的平台）
python3 skills/ppt-master/scripts/content_collector.py setup-cookie
```

---

## 8. 实施路线

### Phase 1：基础框架（1-2 天）

1. 创建 `content_sources/` 目录结构 + `registry.py` + `ContentSource` ABC
2. 实现 `content_collector.py` CLI 框架（search / batch / transcribe / doctor 子命令）
3. 实现 `health_check.py`（probe_command 模式，检查全部依赖）

**交付物**：CLI 可运行 `doctor` 子命令，输出环境健康报告。

### Phase 2：核心平台接入（2-3 天）

1. 实现 B站 + YouTube 适配器（覆盖视频采集需求）
2. 实现 V2EX + 雪球适配器（覆盖垂直社区需求）
3. 实现视频转录管线（yt-dlp → ffmpeg → Whisper）
4. 实现 `batch` 子命令（并行采集 + 结果合并）

**交付物**：`content_collector.py search "话题" --platform bilibili` 可用。

### Phase 3：工作流集成（1-2 天）

1. 改造 `deep-research.md` Step 2，增加 Phase 2/3
2. 在 SKILL.md 增加健康检查入口
3. 端到端测试：一个完整的深度调研流程，验证多平台素材汇入效果

**交付物**：深度调研的素材来源从 2 种扩展到 8+ 种。

### Phase 4：扩展平台（按需）

- LinkedIn（需 OAuth）
- 小红书（需 cookie）
- RSS 订阅
- Exa 语义搜索

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Agent-Reach 版本变动导致 API 不兼容 | 采集函数签名变化 | pin 版本号，适配器层隔离变化 |
| 平台反爬 | 采集失败 | 多平台降级，单平台失败不阻断 |
| 视频转录质量 | Whisper 转录有错 | 仅作为素材参考，不作为直接引用；保留原始视频 URL 供人工核查 |
| 采集内容质量参差 | 低质量内容污染调研 | relevance_score 过滤 + 源分级（与现有 Tier 1-4 体系对齐） |
| 外部工具缺失 | 部分平台不可用 | health_check.py 前置检测 + 清晰的降级路径 |

---

## 10. 成功标准

| 指标 | 标准 |
|------|------|
| **平台覆盖** | ≥6 个平台可通过 CLI 采集内容 |
| **视频转录** | B站/YouTube 视频可通过转录管线获取文本 |
| **健康检查** | `health_check.py` 正确检测所有依赖状态 |
| **工作流集成** | deep-research Step 2 自动使用多平台采集 |
| **降级可靠性** | 任一平台失败不阻断整体调研流程 |
| **内容质量** | 多平台采集的素材在 cross-verification 中可被验证 |
