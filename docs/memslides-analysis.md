# MemSlides 论文分析与 PPT-master2 工程移植评估

> **论文**: MemSlides: A Hierarchical Memory Driven Agent Framework for Personalized Slide Generation with Multi-turn Local Revision
> **作者**: Ye Jin (BUPT), Yangyang Xu (Tsinghua), Jun Zhu (Tsinghua), Yibo Yang (SJTU)
> **提交日期**: 2026-06-15 | **arXiv**: 2606.17162 | **代码**: github.com/huohua325/Memslides (Apache-2.0)

---

## 阶段一：论文核心思想提取

### 1. 架构总览

MemSlides 将幻灯片生成定义为一个**有状态、多轮次的创作问题**，而非一次性的文档转换。系统由一个 LLM Agent 驱动，通过三层记忆系统（用户画像记忆 + 工具经验记忆 + 工作记忆）和一套局部修订流水线（Plan-Act-Guard）来实现个性化生成和多轮修订。

**组件关系**：
```
用户输入(x) + 用户画像记忆(P_u) + 模板(τ)
        │
        ▼
  ┌─────────────────┐
  │  Round-0 生成    │  S₀ = G_init(x, P_u, τ)
  │  (G_init)        │
  └────────┬────────┘
           │ S₀ (初始稿)
           ▼
  ┌─────────────────────────────────────┐
  │  多轮修订循环 (t = 1, 2, 3, ...)    │
  │                                     │
  │  用户反馈(f_t) → 更新会话状态(z_t)  │
  │       → Plan → Act → Guard          │
  │       → S_t = G_edit(S_{t-1}, z_t)  │
  └────────┬────────────────────────────┘
           │ 最终稿
           ▼
  ┌─────────────────┐
  │  任务结束整合    │  C(P_u, H) → 更新长期记忆
  │  (Consolidation) │
  └─────────────────┘
```

### 2. 关键创新点

| # | 创新点 | 解决的问题 | 技术手段 |
|---|--------|-----------|---------|
| 1 | **层级记忆分离** | 现有系统将个性化当作静态 prompt 前缀，无法区分持久偏好、会话约束和执行经验 | 三层记忆：用户画像记忆（跨任务持久）+ 工具经验记忆（跨任务持久）+ 工作记忆（会话级临时） |
| 2 | **局部修订流水线 (Plan-Act-Guard)** | 反复全文档重生成会覆盖已对齐内容、引入漂移、增加上下文压力 | Plan 构建执行合同（作用域+目标路径+选择器+规则ID）；Act 执行最小有效编辑；Guard 通过内容哈希绑定验证覆盖完整性 |
| 3 | **意图条件化用户画像生命周期** | 用户在不同场景（学术 vs 商务）有不同偏好，静态画像无法处理 | 按意图分桶存储 → Select-Reconcile-Route 注入 → 任务结束 Consolidation 只回写稳定信号 |
| 4 | **双粒度工具经验记忆** | Agent 在局部编辑中反复重试无效操作或重犯已知错误 | 轮次级任务经验（错误总结+教训）+ 操作级工具链片段（推理-工具-观察链的可复用片段） |
| 5 | **多角色多意图评估基准** | 没有现成基准评估 PPT 生成中的个性化程度 | 构建 Persona Profile Bank + 盲评 + 干扰角色 + 配对诊断修改评估 |

### 3. 层级记忆机制（核心创新）

#### 3.1 长期记忆（跨任务持久）

**用户画像记忆 (P_u)**：
- 按**意图**（学术/商务/教育/...）× **表现维度**（主题/内容/视觉/布局/模板/通用）组织
- 每个用户有独立的 `UserCoreProfile`（跨意图稳定偏好）和多个 `IntentProfile`（特定意图偏好）
- 存储在 SQLite 表 `user_profiles` 中，复合主键 `(user_id, intent)`
- 结构包含：ThemePreference、VisualPreference、LayoutPreference、ContentPreference、TemplatePreference、GeneralPreference
- 每个子结构携带 `confidence`、`keywords`、`notes`

**工具经验记忆**：
- `ExperienceTrace`：任务描述、推理步骤(JSON)、使用工具(JSON)、教训、适用场景、置信度、复用次数
- `ChainExperience`：工具流水线模式，包含 tool_sequence、lesson、anti_pattern
- `AtomicPreference`：细粒度偏好，带 trigger/condition、scope、confidence
- 存储在 SQLite + 向量检索（text-embedding-3-small, 1536维）+ FTS5 全文搜索
- 垃圾回收：每用户最多 500 条经验、90天过期、0.95 衰减因子

#### 3.2 工作记忆（会话级）

纯内存 Python 数据结构，不跨会话持久化：
- `TempPreference`：本轮反馈暴露出的偏好
- `RoundExperience`：本轮编辑中的工具使用经验
- `DesignEpisode`：设计决策记录
- `ToolChainBuffer`：待合并的工具链信号
- `JobHistory`：本次任务的编辑历史

#### 3.3 记忆读写流程

| 时机 | 操作 | 说明 |
|------|------|------|
| 任务开始 | **Select → Extract → Reconcile** | S(P_u, i₀) 拉取意图匹配画像；E(q₀) 提取当前请求约束；R 合并两者，显式冲突以当前请求优先 |
| 修订轮次中 | **Read/Update 工作记忆** | Plan 读取活跃偏好和编辑状态；Guard 更新覆盖状态和哈希绑定 |
| 每轮结束 | **Buffer** | 将本轮经验信号缓冲到工作记忆，待后续合并 |
| 任务结束 | **Consolidate** | C(P_u, H) 只回写稳定交互信号到长期记忆，防止临时请求污染持久画像 |

**冲突解决优先级**：显式会话反馈 > 任务模板 > 用户画像记忆

### 4. 多轮局部修订机制

#### 4.1 Plan-Act-Guard 流水线

**Plan（执行合同构建）**：
1. 意图分类：判断修订作用域（哪些幻灯片、哪些元素类型）
2. 构建执行合同：scope、operation_kind（style / structural / diagram_layout / controlled_rewrite）、target_slide_paths、coverage_requirements
3. 生成工具策略：约束本轮可访问的 MCP 工具子集

**Act（最小有效编辑）**：
- 共享选择器的目标 → 批量 CSS 更新（`batch_update_css_rule`）
- 跨结构不同幻灯片的共同语义（标题/正文/页脚）→ 语义批量样式更新（`batch_update_semantic_style`）
- 单页内容/结构变更 → 读取"布局优先修复表面"（local layout structure, available selectors, exposed style rules）→ 应用补丁操作（`apply_slide_patch`）
- 页级操作：`insert_slide`、`delete_slide`
- 全页重写：仅限新页面或损坏状态恢复

**Guard（覆盖验证）**：
- 补丁调用绑定快照内容哈希；过期快照触发重新绑定
- 每个补丁必须指定具体操作（来自修复候选/规则/目标）
- 覆盖率要求下，阻止过早 `finalize` 直到所有目标页被修改或确认合规
- 连续 UNCHANGED 检测（阈值=3）防止无限循环
- 多个 blocking 函数：阻止记忆更新期间的变更、限制 future-only 作用域、强制 read-then-write 协议

#### 4.2 修订范围类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 局部请求 | 绑定到单页 | "第 3 页标题改为蓝色" |
| 全局规则 | 扩展到所有页 | "所有标题统一用黑体" |
| 混合请求 | 全局规则 + 局部例外 | "除第 5 页外，所有正文用宋体" |
| 仅未来规则 | 不强制应用于现有页 | "新增页用居中布局" |

### 5. 个性化策略

- **用户建模**：按意图分桶（学术/商务/教育/...），每桶独立的偏好向量
- **风格学习**：跨任务累积，通过 Consolidation 函数将反馈中的稳定信号提炼为持久偏好
- **个性化维度**：页面角色、排序、布局适配、证据强调、角色差异框架、内容密度、视觉风格
- **实验证据**（论文 Figure 6）：跨任务画像整合展示了"本地反馈线索如何变为可复用画像偏好，后又作为默认幻灯片组织模式重新出现"

### 6. 实验结果

#### 6.1 个性化对齐（Table 1，0-10 分）

| 框架 | 模型 | Content | Structure | Visual | Specificity |
|------|------|---------|-----------|--------|-------------|
| DeepPresenter | GPT-5 | 6.22 | 7.56 | 5.76 | 5.89 |
| SlideTailor | GPT-5 | 6.78 | 6.00 | 6.39 | 6.33 |
| **MemSlides** | **GLM-5** | **9.00** | **8.78** | **8.56** | **8.89** |
| **MemSlides** | **Gemini 3.1 Pro** | 7.77 | 8.64 | 8.24 | 8.56 |

MemSlides 相比 DeepPresenter 平均提升：Content +1.37, Structure +0.53, Visual +1.66, Specificity +1.19

#### 6.2 工具经验记忆消融（Table 3）

| 指标 | 有工具记忆 | 无工具记忆 | 提升 |
|------|-----------|-----------|------|
| 闭环完成率 | 0.963 | 0.815 | +18% |
| 严格验证率 | 0.534 | 0.310 | +72% |
| 首次正确编辑时间 | 242.5s | 609.5s | -60% |
| 核心工具时间比 | 0.327x | 1.000x | -67% |

### 7. 技术实现细节

- **LLM 骨架**：GPT-5 / GLM-5 / Gemini 3.1 Pro（框架无关）
- **幻灯片格式**：HTML+CSS 文件，每页一个 `slide_XX.html`
- **导出流水线**：Playwright DOM 提取 → pptxgenjs（Node.js）组装 PPTX
- **存储后端**：SQLite + JSON blobs + 向量检索（text-embedding-3-small）
- **工具协议**：MCP（Model Context Protocol），工具定义在 `mcp.json`
- **项目结构**：完整的 Python 包，CLI 入口 `python -m memslides {generate|revise|template}`

---

## 阶段二：可移植性评估

### 逐项映射表

| 创新点 | 可行性 | 价值 | 优先级 | 理由 |
|--------|--------|------|--------|------|
| **层级记忆分离** | **高** | **高** | **P0** | PPT-master2 已有文件状态体系（design_spec.md + spec_lock.md），添加用户画像层只需在 projects/ 下新建 memory.json + 首尾注入；与现有管线零冲突。工具经验记忆可独立实现为项目级 .lessons/ 目录 |
| **局部修订 (Plan-Act-Guard)** | **中** | **高** | **P1** | 核心价值巨大（避免全文档重生成），但需要将 SVG 从"不可分割的渲染产物"重新定义为"可打补丁的结构化文档"。PPT-master2 的 SVG 是手写文本，天然可局部编辑，但缺乏 CSS 选择器语义。需要设计 SVG-native 的 patch 操作集 |
| **意图条件化画像** | **高** | **中** | **P1** | 实现简单——在 memory.json 中按 intent 分桶，首次生成时根据 Eight Confirmations 的 mode+visual_style 自动选择/创建意图桶。但 PPT-master2 的 Eight Confirmations 已经提供了显式偏好收集通道，价值主要在跨任务累积 |
| **双粒度工具经验** | **中** | **中** | **P2** | 需要向量检索基础设施（SQLite+embeddings），对 PPT-master2 的文件状态范式是架构性新增。短期可简化为 Markdown 日志 + 关键词检索，长期再升级为向量方案。价值需要多轮使用才能体现 |
| **多角色评估基准** | **低** | **低** | **P2** | PPT-master2 已有 svg_quality_checker.py 和 visual-review 工作流。Persona Profile Bank 是评估层创新，对生产流程无直接提升，可在系统成熟后参考构建 |

### 可行性判定理由

#### 高可行性：层级记忆分离 + 意图条件化画像

PPT-master2 的现有架构天然适配：
- **文件状态范式不变**：用户画像以 JSON 文件存储在 `projects/<name>/memory/` 下，与现有的 design_spec.md + spec_lock.md 共存
- **注入点明确**：SKILL.md Step 4 的 Eight Confirmations 是天然的"意图识别 + 偏好采集"入口；Consolidation 可在 Step 7（导出后）自动触发
- **不改动核心管线**：Strategist → Image_Generator → Executor 的角色分工和串行执行不受影响

#### 中可行性：局部修订 Plan-Act-Guard

需要解决的核心问题：
- **SVG 语义差距**：MemSlides 用 HTML/CSS 的 DOM 选择器（`.title`, `.footer`）实现局部定位；SVG 没有 CSS 选择器语义，需要用 `id`、`data-` 属性或结构路径（`/svg/g[3]/text[1]`）替代
- **Patch 操作集设计**：需要定义 SVG-native 的操作类型——`update_text`、`update_fill`、`update_transform`、`insert_element`、`delete_element`——而非 CSS batch update
- **快照哈希机制**：Guard 需要内容哈希来检测陈旧快照；SVG 是纯文本文件，直接 SHA-256 即可，比 HTML 更简单
- **与 live-preview 的关系**：现有的 live-preview annotation 机制是"浏览器中选元素→写指令→AI 改"，与 Plan-Act-Guard 理念一致但粒度不同，可以作为 Guard 的 UI 层

#### 低可行性/高成本：工具经验记忆

- 需要引入向量检索依赖（embeddings API + SQLite FTS5），与 PPT-master2"零外部依赖"的脚本风格冲突
- 短期替代方案：将经验以 Markdown 追加到 `<project>/.lessons/` 目录，用关键词匹配检索
- 长期：如果项目发展到有足够多的生成-修订循环，向量检索的价值才显现

---

## 阶段三：工程落地计划

### 总体策略

```
分支结构:

main
  └── feature/memsli → 分支一：层级记忆 + 画像系统（P0，约 3-4 天）
  └── feature/revision → 分支二：局部修订流水线（P1，约 5-7 天，依赖分支一）
  └── feature/tool-memory → 分支三：工具经验记忆（P2，独立，约 3-4 天）
```

**合并顺序**：分支一 → main → 分支二 → main → 分支三（可选）

---

### 分支一：层级记忆 + 意图条件化画像 (P0)

**目标**：让 PPT-master2 具备跨任务的用户偏好记忆能力

#### 改动范围

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| **新增** | `skills/ppt-master/memory/profile_schema.py` | UserProfile 数据模型（Python dataclass），对齐 MemSlides 的 ThemePreference/VisualPreference/LayoutPreference/ContentPreference 结构 |
| **新增** | `skills/ppt-master/memory/profile_store.py` | JSON 文件读写 + 意图分桶逻辑，存储到 `projects/<name>/memory/user_profiles.json` |
| **新增** | `skills/ppt-master/memory/orchestrator.py` | 记忆编排：Select → Extract → Reconcile（任务开始）、Consolidate（任务结束） |
| **新增** | `skills/ppt-master/memory/consolidator.py` | 任务结束时的画像整合逻辑：对比 Eight Confirmations 结果与预设偏好，将稳定信号回写 |
| **修改** | `skills/ppt-master/references/strategist.md` | Step 4 开头注入记忆读取指令：加载用户画像 → 与当前请求 Reconcile → 注入为隐式偏好提示 |
| **修改** | `skills/ppt-master/SKILL.md` | Step 4 前新增"记忆加载"子步骤；Step 7 后新增"记忆整合"子步骤 |
| **新增** | `scripts/memory_manager.py` | CLI 工具：`memory_manager.py load <project> --intent academic` / `memory_manager.py consolidate <project>` / `memory_manager.py show <project>` |

#### 实现步骤（按 commit 粒度）

**Commit 1**：`feat(memory): add UserProfile data model and schema`
- 创建 `skills/ppt-master/memory/__init__.py`
- 实现 `profile_schema.py`：定义 `UserProfile`、`ThemePreference`、`VisualPreference`、`LayoutPreference`、`ContentPreference`、`GeneralPreference` dataclass
- 每个 Preference 子类有 `values: dict`、`confidence: float`、`sources: list[str]`（记录偏好来源：initial_request / eight_confirmations / consolidation / user_explicit）
- 验证：`python -c "from skills.ppt-master.memory.profile_schema import UserProfile; print(UserProfile())"`

**Commit 2**：`feat(memory): implement JSON profile store with intent bucketing`
- 实现 `profile_store.py`：JSON 文件存储，路径 `projects/<name>/memory/user_profiles.json`
- 支持 CRUD：`get_profile(user_id, intent)`、`update_profile(user_id, intent, profile)`、`list_intents(user_id)`
- 意图映射表：将 Eight Confirmations 的 mode 值（academic / business / narrative / ...）映射为 intent bucket key
- 验证：单元测试——创建、读取、更新、意图切换

**Commit 3**：`feat(memory): implement orchestrator with Select-Extract-Reconcile`
- 实现 `orchestrator.py`：
  - `load_memory(project_path, intent)` → Select 意图匹配画像
  - `reconcile(profile_preferences, current_request)` → 合并，显式请求优先
  - `format_memory_prompt(profile)` → 输出可注入 Strategist prompt 的偏好摘要段落
- 验证：给定一个已有画像 + 新请求，验证 Reconcile 冲突解决正确

**Commit 4**：`feat(memory): implement consolidator for job-end profile update`
- 实现 `consolidator.py`：
  - `consolidate(project_path, intent, confirmations_result)` → 对比预设偏好与本次确认结果
  - 信号稳定性判定：如果某偏好维度在本次和上次任务中一致（confidence ≥ 0.7），回写；否则跳过
  - 合并策略：已存在偏好取加权平均，新偏好写入时 confidence 设为 0.5（首次观察）
- 验证：模拟两次任务后的画像累积

**Commit 5**：`feat(memory): add CLI memory_manager.py`
- 实现 `scripts/memory_manager.py`：
  - `load <project> --intent <intent>` — 加载并显示画像
  - `consolidate <project>` — 手动触发整合
  - `show <project>` — 查看所有意图画像
  - `reset <project> --intent <intent>` — 重置特定意图画像
- 验证：CLI 运行各子命令

**Commit 6**：`docs: integrate memory into SKILL.md and strategist.md`
- 修改 `SKILL.md`：Step 4 前新增"Step 3.5 记忆加载"，说明何时/如何加载用户画像
- 修改 `strategist.md`：在 Eight Confirmations 前注入一段"用户画像偏好注入"指令，格式为：
  ```
  ## 用户画像偏好（自动生成，用户显式指令优先级更高）
  - 主题偏好：深色背景、蓝灰调色板
  - 内容偏好：要点密度中等、每页不超过 4 个核心论点
  - 布局偏好：左侧文字 + 右侧图表的二栏结构
  ```
- 修改 `SKILL.md`：Step 7 后新增"Step 7.5 记忆整合"，说明导出完成后自动触发 Consolidation
- 验证：走一遍完整的 SKILL.md 流程，确认记忆注入和整合步骤不干扰现有管线

#### 依赖与风险

| 依赖 | 说明 | 风险 |
|------|------|------|
| Python 3.8+ | dataclass、json、pathlib | 无——PPT-master2 已有 |
| 无外部依赖 | 纯文件系统存储 | 无 |

| 风险 | 缓解 |
|------|------|
| 画像注入导致 Strategist 输出偏离用户期望 | Reconcile 机制确保显式请求优先于画像偏好；注入格式为"建议"而非"强制" |
| Consolidation 误将临时偏好写入长期记忆 | 使用 confidence 阈值 + 双次一致性检验 |
| JSON 文件并发写入冲突 | PPT-master2 是单线程串行管线，不存在并发问题 |

#### 验证方式

1. **冷启动测试**：无画像 → 生成一版 → 导出 → 检查 `user_profiles.json` 是否创建
2. **偏好累积测试**：连续生成 2 片不同 PPT，都选择"深色主题" → 第 3 次生成时画像自动建议深色主题
3. **冲突解决测试**：画像偏好"左对齐"但用户在某次显式要求"居中" → 该次使用居中，不覆盖画像中的左对齐
4. **意图隔离测试**：学术演示偏好不影响商务演示的画像

#### 预估工作量

**3-4 天**（一人用 Claude Code 辅助）
- Day 1：数据模型 + 存储层 (Commits 1-2)
- Day 2：编排器 + 整合器 (Commits 3-4)
- Day 3：CLI 工具 + 文档集成 (Commits 5-6)
- Day 4：集成测试 + 边界情况修复

---

### 分支二：局部修订流水线 (P1)

**目标**：实现多轮局部修订，避免全文档重生成

#### 改动范围

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| **新增** | `skills/ppt-master/references/reviser.md` | Reviser 角色定义——从 Executor 中拆分出的修订专用角色 |
| **新增** | `workflows/revision-loop.md` | 多轮修订工作流：用户反馈 → Plan → Act → Guard → 循环/完成 |
| **新增** | `scripts/svg_patch.py` | SVG 补丁引擎：解析 SVG、应用局部修改、验证哈希 |
| **新增** | `scripts/svg_snapshot.py` | SVG 快照管理：生成内容哈希、检测变更、生成 diff |
| **修改** | `scripts/svg_editor/server.py` | 扩展 live-preview 服务器，支持 Plan-Act-Guard 的执行合同显示和验证状态 |
| **修改** | `skills/ppt-master/SKILL.md` | Step 6 后新增可选的"Step 6.5 修订循环"入口 |

#### SVG 补丁操作集设计

PPT-master2 的 SVG 是手写纯文本文件，天然可解析。需要定义以下操作：

```python
# 操作类型
PATCH_OPS = {
    "update_text":      {"target": "element_id", "new_text": "string"},
    "update_fill":      {"target": "element_id", "fill": "hex_color"},
    "update_font_size": {"target": "element_id", "font_size": "number"},
    "update_transform": {"target": "element_id", "transform": "string"},
    "replace_image":    {"target": "image_id", "href": "path"},
    "insert_element":   {"after": "element_id", "svg_fragment": "string"},
    "delete_element":   {"target": "element_id"},
    "update_attribute": {"target": "element_id", "attr": "name", "value": "string"},
}
```

**关键设计**：所有可编辑元素必须有 `id` 属性。当前 Executor 生成的 SVG 已经要求 id 唯一性（svg_quality_checker.py 检查项），这为补丁系统提供了天然基础。

#### 实现步骤

**Commit 1**：`feat(revision): add SVG snapshot and diff utilities`
- 实现 `scripts/svg_snapshot.py`：
  - `snapshot(svg_path)` → 计算 SHA-256 哈希
  - `diff(before_svg, after_svg)` → 基于 XML 结构的变更检测（新增/删除/修改的元素）
  - `validate_hash(svg_path, expected_hash)` → 验证快照是否过期
- 验证：对同一 SVG 计算两次哈希应相同；修改后哈希应不同

**Commit 2**：`feat(revision): implement SVG patch engine`
- 实现 `scripts/svg_patch.py`：
  - `parse_svg(svg_path)` → ElementTree 解析
  - `apply_patch(svg_path, operations, expected_hash)` → 验证哈希 → 应用操作 → 保存
  - `list_editable_elements(svg_path)` → 列出所有带 id 的元素及其类型/文本
  - 每个 PATCH_OP 的具体实现
- Guard 逻辑：expected_hash 不匹配时拒绝操作并报错
- 验证：创建测试 SVG → 应用各种操作 → 检查输出正确性

**Commit 3**：`feat(revision): add Reviser role definition`
- 创建 `references/reviser.md`：
  - 角色：从 Executor 拆分出的修订专用角色
  - 能力：读取 SVG 快照、构建补丁计划、调用 patch 工具、验证结果
  - 约束：只能修改指定范围内的元素；不能重新生成完整页面（除新建页外）
  - 与 Executor 的区别：Executor 从零生成；Reviser 在现有基础上打补丁
- 验证：角色定义文档完整，与 strategist.md / executor-base.md 风格一致

**Commit 4**：`feat(revision): implement revision-loop workflow`
- 创建 `workflows/revision-loop.md`：
  - 入口条件：用户说"修改"/"调整"/"修订" 或在 live-preview 中提交标注
  - Plan 阶段：读取用户反馈 → 分类作用域（局部/全局/混合）→ 构建执行合同
  - Act 阶段：调用 svg_patch.py 执行补丁
  - Guard 阶段：验证补丁覆盖完整性 → 检查哈希一致性 → 检查连续 UNCHANGED
  - 循环条件：用户继续反馈 → 回到 Plan；用户说"完成"/"导出" → 退出循环
- 验证：模拟一轮修订流程

**Commit 5**：`feat(revision): extend live-preview for Plan-Act-Guard integration`
- 修改 `scripts/svg_editor/server.py`：
  - 新增执行合同显示面板：当前作用域、目标元素、操作列表
  - 新增验证状态显示：已修改/待修改/已验证
  - 支持从浏览器提交修订反馈（直接映射为补丁操作）
- 验证：浏览器中操作 → 补丁应用 → 状态更新

**Commit 6**：`docs: add revision-loop to SKILL.md pipeline`
- 修改 `SKILL.md`：Step 6 和 Step 7 之间新增可选的 Step 6.5
- 说明入口条件、工作流程、与 live-preview 的关系
- 验证：文档完整性检查

#### 依赖与风险

| 依赖 | 说明 |
|------|------|
| Python xml.etree.ElementTree | 标准库——SVG 解析 |
| 分支一的 memory 模块 | Reviser 需要读取工作记忆中的编辑状态 |
| svg_quality_checker.py | 修订后需重新运行质量检查 |

| 风险 | 缓解 |
|------|------|
| 补丁操作破坏 SVG 结构完整性 | Guard 的哈希验证 + 质量检查双重保护 |
| 元素 id 不一致导致定位失败 | svg_quality_checker.py 已强制 id 唯一性 |
| 修订范围过大退化为全文重写 | 强制限制单次修订最大元素数（如 10 个），超过则要求用户确认 |

#### 验证方式

1. **单元素修订**：修改某个标题颜色 → 验证只有该元素变化，其他不变
2. **批量样式修订**："所有标题改大一号" → 验证所有 `<text>` 元素 font-size 变化
3. **哈希过期检测**：手动修改 SVG 后尝试补丁 → 应报错"快照过期"
4. **修订后质量检查**：补丁应用后自动运行 svg_quality_checker.py
5. **修订后导出**：修订 → re-export → PPTX 中反映变更

#### 预估工作量

**5-7 天**（一人用 Claude Code 辅助）
- Day 1：快照 + diff 工具 (Commit 1)
- Day 2-3：SVG 补丁引擎 (Commit 2)
- Day 4：Reviser 角色 + 工作流定义 (Commits 3-4)
- Day 5：live-preview 集成 (Commit 5)
- Day 6-7：文档 + 集成测试 (Commit 6 + 修复)

---

### 分支三：工具经验记忆 (P2)

**目标**：让系统从每次生成-修订循环中学习，逐步提升 SVG 生成质量

#### 改动范围

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| **新增** | `memory/lesson_store.py` | 经验教训存储：Markdown 文件 + 关键词索引 |
| **新增** | `memory/lesson_logger.py` | 自动记录：质量检查失败 → 教训；修订操作 → 经验 |
| **修改** | `scripts/svg_quality_checker.py` | 质量检查失败时自动写入教训文件 |
| **修改** | `references/executor-base.md` | 注入"加载相关教训"指令 |

#### 简化设计（不引入向量检索）

MemSlides 的向量检索方案需要 embedddings API 依赖，与 PPT-master2 的轻量脚本风格不符。替代方案：

```
projects/<name>/.lessons/
  ├── index.json          # 关键词倒排索引
  ├── 2026-06-23_001.md   # 教训文件（含 frontmatter）
  └── ...
```

教训文件格式：
```markdown
---
date: 2026-06-23
category: svg_quality
keywords: [font-size, consistency, color-mismatch]
scope: element_type:page_title
severity: error
---

在深色主题 PPT 中，页标题的 font-size 应 ≥ 28px 以确保可读性。
上次生成的 05_content.svg 标题 font-size=22px，被 svg_quality_checker 标记为警告。
修复方式：将标题 font-size 提升到 32px。
```

检索：Executor 生成前，根据当前页的布局类型 + 主题关键词，在 `.lessons/index.json` 中做关键词匹配，top-5 注入 prompt。

#### 预估工作量

**3-4 天**（一人用 Claude Code 辅助）

---

## 总结与建议

### 立即行动项

1. **先做分支一（记忆系统）**——这是所有 MemSlides 创新的基础设施，且改动最小、风险最低
2. 分支一合入 main 后，**用几个真实 PPT 项目测试画像累积效果**，再决定是否推进分支二

### 不建议直接移植的部分

| 部分 | 原因 |
|------|------|
| HTML/CSS 渲染管线 | PPT-master2 的 SVG→DrawingML 管线在原生可编辑性上有不可替代的优势；HTML→PPTX 的 pptxgenjs 方案会丢失精细的布局控制 |
| MCP 工具协议 | PPT-master2 是 Claude Code 工作流包，不是独立服务；用文件 + CLI 更符合现有风格 |
| 向量检索 | 依赖过重，短期用关键词匹配足够 |
| 单 Agent 架构 | PPT-master2 的三角色分工已经过实践验证，拆分的职责边界比单 Agent + 记忆分层更适合 Claude Code 的上下文管理模式 |

### 值得借鉴但需要适配的设计理念

| 理念 | PPT-master2 适配方案 |
|------|---------------------|
| **记忆读写生命周期** | Eight Confirmations = Select-Extract-Reconcile；导出后 = Consolidate |
| **"最小有效编辑"原则** | 修订时只改用户提到的元素，不重生成整页——通过 SVG 补丁实现 |
| **冲突解决优先级** | 显式用户指令 > Eight Confirmations > 用户画像 > 系统默认 |
| **稳定性回写** | Consolidation 时只写入 confidence ≥ 0.7 的偏好，防止噪声 |
