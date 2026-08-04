# DeepPPT2 系统收敛与整体优化 Agent Brief

> 状态：拟执行的完整优化契约，尚未实施。
> 权威性：非运行权威；执行时必须服从 [`AGENTS.md`](../AGENTS.md)、[`skills/ppt-master/SKILL.md`](../skills/ppt-master/SKILL.md)、[`skills/ppt-master/workflows/routing.md`](../skills/ppt-master/workflows/routing.md) 及具体 owning workflow。
> 实施状态：本文件只定义任务、边界、阶段门和验收，不代表任何代码、Prompt、工作流或 CI 变更已获执行授权。
> 适用仓库：`C:/Users/FUTIAN/Desktop/DeepPPT2`
> 制定日期：2026-08-04

---

## 0. 使用方式

本文件可直接作为后续 Agent 的执行指令。推荐使用以下入口之一：

```text
按 plans/deepppt2-system-optimization-agent-brief.md 执行 Phase 0，只读建立基线并提交阶段回执。
```

```text
按 plans/deepppt2-system-optimization-agent-brief.md 从已批准阶段继续执行；严格遵守阶段门、修改边界和验收标准。
```

**Hard rule**：创建或阅读本文件不等于批准实施。首次执行必须从 Phase 0 开始；Phase 0 完成后在 Gate G1 停止，等待用户确认具体实施范围和指标。

**Hard rule**：每次只执行一个可独立验证的变更批次。禁止把 Prompt 瘦身、状态契约迁移、核心导出器重构和性能优化混进同一批次。

**Hard rule**：本计划不是新功能路线图。执行期间默认冻结新增能力，只处理收敛、可靠性、维护性、上下文效率、性能证据和治理一致性。

---

## 1. 目标

把 DeepPPT2 从“功能扩张期”切换到“系统收敛期”，在不削弱 PPT 生成质量、不改变既有产品形态的前提下，完成以下结果：

1. 让 Skills / workflows 只负责编排、阶段门和失败恢复。
2. 让项目状态、artifact 路径和跨阶段数据格式拥有单一事实源。
3. 让脚本围绕明确领域职责组织，CLI 保持薄入口和稳定兼容层。
4. 降低 Agent 的必读 Prompt 体积和重复解释，减少上下文漂移与压缩风险。
5. 用契约测试、质量门和 trace 证明修改没有破坏生成链路。
6. 只对 profiling 和变更历史证明的热点做代码或性能优化。

最终目标不是追求抽象意义上的“代码优雅”，而是让以下变化各自只触碰一个清晰边界：

| 变化类型 | 只应主要修改 |
|---|---|
| 路由或阶段变化 | owning workflow / route registry |
| artifact 路径变化 | canonical artifact contract |
| `spec_lock` 字段变化 | canonical parser / schema / owning reference |
| Dashboard 展示变化 | Dashboard adapter，不重新定义 pipeline 事实 |
| 导出行为变化 | SVG-to-PPTX domain package |
| Provider 变化 | 对应 adapter，不污染核心流程 |
| 质量规则变化 | owning specification + matching gate + fixture |

---

## 2. 背景与基线事实

执行 Agent 必须先复核以下事实，不得把本节数字直接当成永不过期的现状：

| 编号 | 当前事实 | 证据 |
|---|---|---|
| F1 | Prompt corpus 最近实测约 `425,447 / 430,000 tokens`，已接近当前增长上限 | [`prompt_audit_manifest.json`](../skills/ppt-master/scripts/prompt_audit_manifest.json) + `prompt_audit.py --json` |
| F2 | Generate load set 最近实测 typical 约 `165,611 tokens` | 同上 |
| F3 | 性能基线整体健康：完整 smoke 约 26.1s、10 页导出 p50 约 3.7s、quality 冷启动 p50 约 1.33s | [`perf-baseline-2026-08.md`](../docs/reviews/perf-baseline-2026-08.md) |
| F4 | 项目状态存在多套推断：Dashboard、`project_manager checkpoint` 和 workflow 文档分别维护部分事实 | `dashboard/state_reader.py`、`project_manager.py`、`generate-pptx.md` |
| F5 | 已知漂移样例：正常导出位于 `exports/*.pptx`，Dashboard 按此读取，但 checkpoint 仍检查项目根 `*.pptx` | `dashboard/artifact_registry.py::latest_pptx`、`project_manager.py::checkpoint_save` |
| F6 | `spec_lock.md` 被大量脚本消费，并存在多套局部解析逻辑 | `update_spec.py`、`e2e_validate.py`、`layout_capacity_check.py`、`dashboard/state_reader.py` |
| F7 | Prompt audit 已有 load-set、重复段落和预算能力，但 `authority_edges`、`registries`、`schema_grammars` 尚未建立有效配置 | [`prompt_audit_manifest.json`](../skills/ppt-master/scripts/prompt_audit_manifest.json) |
| F8 | 仓库已有 smoke、harness、E2E、公开 examples 和 CI，不需要另建通用测试脚手架 | [`AGENTS.md`](../AGENTS.md)、[`.align/spec.md`](../.align/spec.md) |
| F9 | 前一轮仓库盘点、产物治理和迁移收口已经完成，禁止把已关闭任务重新执行一遍 | [`deep-ppt-repository-inventory-2026-08.md`](../docs/reviews/deep-ppt-repository-inventory-2026-08.md)、[`deep-ppt-reorganization-contract.md`](./deep-ppt-reorganization-contract.md) |
| F10 | 项目路线图已把 Prompt slimming 列为长期维护方向，纯速度优化是非目标 | [`docs/roadmap.md`](../docs/roadmap.md) |

**Validation**：Phase 0 必须用当前工作区重新测量 F1-F10。数字变化不构成错误；未记录测量环境、命令、fixture 和 dirty worktree 状态才构成失败。

---

## 3. 目标架构

### 3.1 分层边界

| 层 | 责任 | 允许依赖 | 禁止拥有 |
|---|---|---|---|
| 编排层 | 路由、阶段顺序、BLOCKING、恢复指针、按需加载 | 契约层、角色/技术引用 | 具体 OOXML/SVG 实现、重复 schema |
| 契约层 | artifact 路径、项目事实、状态模型、schema、兼容版本 | 标准库、稳定数据模型 | UI 展示、Provider SDK、PPTX 渲染实现 |
| 领域层 | 转换、解析、SVG 校验、DrawingML、PPTX 构建 | 契约层、领域内部模块 | 路由选择、用户确认策略、Dashboard 状态推断 |
| 适配层 | CLI、Dashboard、Confirm UI、Live Preview、Provider | 契约层、领域层 | 重新定义领域规则或 pipeline 事实 |
| 质量层 | smoke、contract fixtures、harness、E2E、visual review、trace | 所有只读输出和明确测试入口 | 静默修改生产 artifact 以让检查通过 |

### 3.2 设计原则

1. **Artifacts are APIs**：阶段间通过版本化 artifact 交接，不依赖聊天记忆或未声明的目录扫描。
2. **One fact, one owner**：一个字段、路径、枚举或状态只能有一个 owning parser / registry / schema。
3. **Thin entry points**：顶层脚本保留兼容 CLI；实现放在高内聚内部模块。
4. **Read-only derivation first**：状态优先从现有 artifacts 确定性推导；需要持久化时写明确 snapshot，不让 snapshot 反向成为第二套事实。
5. **Fail closed at real gates**：只在会破坏正确性、可恢复性或用户明确选择时阻塞；不把主观偏好编码成 ERROR。
6. **Refactor by change reason**：按职责和变化原因拆分，不按文件行数机械拆分。
7. **Compatibility before cleanup**：先建立消费者矩阵和兼容层，再迁移，再删除；删除必须另获授权。
8. **Quality over raw speed**：任何速度改进都不得降低页面质量、可编辑性、跨渲染器一致性或质量门强度。

---

## 4. 范围与权限

### 4.1 In scope

- Skills / workflows 的加载边界、权威关系、重复规则和恢复契约。
- Prompt corpus、load sets、registry、schema grammar 和重复段落治理。
- 项目 artifact 路径、pipeline state、checkpoint、Dashboard state 的单一事实源。
- `spec_lock.md`、Confirm UI result、质量报告和 trace 的解析与 schema。
- CLI 入口一致性、退出码、配置读取、内部 helper 分层。
- `smoke_check`、`harness_gate`、E2E 和 CI 的契约回归覆盖。
- 有证据的 Python 模块拆分、重复解析消除和性能优化。
- Provider adapter、可选依赖、敏感配置和软失败边界。
- 与上述改动直接相关的 README、脚本文档、workflow、reference 和 change log。

### 4.2 Out of scope

- 新增 PPT 功能、模板类型、图表类型、动画效果、Provider 或产品形态。
- 把项目改造成 SaaS、桌面应用、独立工作流平台或微服务系统。
- 改变“聊天驱动 AI IDE skill”的产品定位。
- 改变逐页手写 SVG、主 Agent 顺序生成和 `spec_lock` 每页重读纪律。
- 为追求速度降低视觉质量、质量门、可编辑性或跨渲染器一致性。
- 把 `skills/ppt-master/scripts/` 整体迁成通用 Python package。
- 重写 `examples/`、清理用户 `projects/`、删除历史产物。
- commit、push、发布、部署或外部系统写入。
- 有成本的图片生成、外部研究、模型 A/B 或第三方 API 调用，除非用户另行明确批准。

### 4.3 必须单独确认的操作

| 操作 | 执行规则 |
|---|---|
| 修改 `SKILL.md` | 先说明必要性、替代方案和影响；获批后保留 `[NEEDS_HUMAN_REVIEW]` |
| 改变公开 CLI 参数、输出路径或返回码 | 先提供兼容矩阵和迁移方案 |
| 改变 artifact schema 的必填字段 | 先提供版本、旧项目兼容和回滚方案 |
| 增加依赖 | 先证明标准库或现有依赖不能完成任务 |
| 修改 CI workflow | 先记录本地等价验证和预计 CI 时间变化 |
| 删除、移动、重命名文件 | 先列消费者、回滚路径和用户授权 |
| 运行付费 API 或完整模型生成 A/B | 先列成本、样本和停止条件 |
| commit / push / deploy | 必须由用户明确授权 |

---

## 5. 执行策略

- 信息足够且低风险：按当前 phase 直接执行最小批次。
- 信息可从仓库、日志、fixture 或历史报告获得：自行读取，不向用户转嫁调查工作。
- 关键信息缺失且会改变目标、兼容边界或验收：停止，一次只问一个问题，并给推荐答案。
- 高风险操作范围、恢复、授权或验收不完整：停止，不得以“先试试”为理由执行。
- 发现 dirty worktree：区分用户改动与本批改动；禁止覆盖、恢复或格式化用户改动。
- 发现基线失败：记录失败与现有修改的关系；不得把既有失败伪装成本批回归。
- 发现实际影响超出当前 phase：输出偏离说明，重大扩范围必须等待确认。
- 每批修改前建立基线，修改后运行同一 fixture、同一命令和同一统计口径。
- 每个 phase 结束输出 execution receipt；未通过本 phase 验收不得进入下一 phase。

### 5.1 强制加载顺序

每个新会话开始时按以下顺序执行：

1. 读取 `.align/lessons.md`、`.align/spec.md`、`.align/context.md`。
2. 读取 [`AGENTS.md`](../AGENTS.md)。
3. 完整读取 [`skills/ppt-master/SKILL.md`](../skills/ppt-master/SKILL.md)。
4. 运行 `python skills/ppt-master/scripts/attribution_guard.py`。
5. 读取本文件和当前 phase 引用的 owning rules / workflows。
6. 运行 `git status --short`，记录但不修改已有工作区变化。

### 5.2 批次纪律

一个变更批次必须满足：

- 一个明确目标。
- 一个消费者矩阵或影响清单。
- 一组前后完全一致的验证命令。
- 一个可逆补丁。
- 不包含顺手重构、格式化或命名清理。

---

## 6. Phase 0 - 只读基线与决策门

**目标**：重新测量当前仓库，形成可对账的优化基线，不修改运行文件。

| ID | 任务 | 产物 | 验证 |
|---|---|---|---|
| T0.1 | 记录 branch、HEAD、dirty worktree、Python/OS、依赖版本 | baseline 报告环境节 | 命令和输出摘要可复跑 |
| T0.2 | 运行 attribution guard、governance drift、prompt audit、smoke `--skip-help` 和完整 smoke | baseline 报告质量节 | 所有 rc 和 passed/failed/skipped 有记录 |
| T0.3 | 重新测量 corpus 与各 load set 的 min/typical/max tokens | baseline 报告 Prompt 节 | 不只抄 manifest 上限 |
| T0.4 | 复核性能 p50/p95：quality、Dashboard、代表性导出、目录扫描 | baseline 报告性能节 | 同一 fixture，记录 n、冷/暖、环境 |
| T0.5 | 生成“事实 owner -> 消费者”矩阵：pipeline state、artifact 路径、`spec_lock`、Confirm result、quality/trace | baseline 报告契约节 | 每个结论含文件与符号证据 |
| T0.6 | 生成 Python 热点矩阵：LOC、churn、fan-in、fan-out、缺陷历史、职责数 | baseline 报告代码节 | 禁止仅按 LOC 排名 |
| T0.7 | 选择代表性 fixture 集：主 Generate flat、structured/native、template-fill 或 beautify、含图片/图表的复杂 deck | baseline 报告 fixture 节 | 每个 fixture 说明覆盖的契约 |
| T0.8 | 标注与既有治理计划重复、已完成或明确非目标的任务 | baseline 报告排除节 | 不重做已关闭任务 |

默认产物：

```text
docs/reviews/deepppt2-system-optimization-baseline-2026-08.md
.tmp/system_optimization_baseline.json
```

`docs/reviews/` 报告必须声明非运行权威；`.tmp/` 原始数据保持 gitignored。

### Gate G1 - 基线确认

Phase 0 完成后必须停止并向用户提交：

1. 前五个最高收益问题。
2. 每个问题的证据、风险、预计改动范围和回滚方式。
3. 建议纳入 Phase 1-8 的具体任务，以及建议取消的任务。
4. Prompt 缩减目标、性能回归阈值和是否允许运行模型 A/B 的推荐答案。

未获得用户确认，不得修改代码、workflow、reference、schema 或 CI。

---

## 7. Phase 1 - Artifact 与 Pipeline State 单一事实源

**前置**：Gate G1 已确认。

**目标**：消除 Dashboard、checkpoint、CLI 和 workflow 对项目路径与当前阶段的独立解释。

| ID | 任务 | 执行动作 | 验收 |
|---|---|---|---|
| T1.1 | Artifact registry 盘点 | 列出 project root、`analysis/`、`images/`、`svg_output/`、`svg_final/`、`exports/`、`quality/`、`validation/` 的 owner 和消费者 | 路径表无未解释冲突 |
| T1.2 | Canonical project facts | 优先评估扩展 `project_utils.py`；若职责会混杂，再新增一个纯标准库 helper | 模块不依赖 Flask、Provider、PPTX SDK |
| T1.3 | Canonical artifact accessors | 统一 latest export、SVG 列表、notes、spec、quality、confirmation 等读取函数 | Dashboard 与 checkpoint 调用同一实现 |
| T1.4 | Canonical state derivation | 抽取确定性的 `derive_pipeline_state(project)` 或等价 API | 同一 fixture 多次调用结果稳定，时间字段除外 |
| T1.5 | Checkpoint 收敛 | `.checkpoint.json` 只保存 canonical state snapshot 和可选 notes，不再独立推断另一套步骤 | `exports/*.pptx` 项目被判定为已导出 |
| T1.6 | Dashboard 适配 | `dashboard/state_reader.py` 保留展示组装，不拥有重复 artifact 规则 | Dashboard API schema 保持兼容 |
| T1.7 | Resume 契约 | 核对 continuous/split、Phase B resume、partial SVG、partial image 和 failed gate 状态 | 每种状态有 fixture 和期望 next action |
| T1.8 | 状态契约测试 | 把 fixture 加入现有 smoke/integration 体系 | 不新建通用 `tests/` 脚手架 |

**禁止**：把只读状态收敛扩展成自动执行 workflow engine。

**验证命令**：

```powershell
python skills/ppt-master/scripts/attribution_guard.py
python skills/ppt-master/scripts/smoke_check.py --skip-help
python skills/ppt-master/scripts/smoke_check.py
```

另对 Phase 0 选定的状态 fixture 运行 checkpoint、Dashboard state reader 和 resume sanity check，断言 route、current step、export path、gate state 一致。

---

## 8. Phase 2 - 数据契约与 Parser 收敛

**目标**：让跨模块 artifact 拥有一个 parser、一个 schema owner 和明确兼容策略。

### 8.1 `spec_lock.md`

| ID | 任务 | 验收 |
|---|---|---|
| T2.1 | 建立全部 parser / regex / section reader 的消费者矩阵 | 每个消费者列明所需字段、容错和错误级别 |
| T2.2 | 选择一个 canonical parser owner；优先复用和扩展现有稳定实现 | 禁止另写第五套 parser |
| T2.3 | 定义标准化只读数据模型，保留原 Markdown 为人类与 Agent 权威 artifact | 默认不改变 `spec_lock.md` 文件格式 |
| T2.4 | 统一 `flat` / `structured`、page IDs、images、typography、colors、page rhythm 等字段语义 | validator 与 checker 对同字段不再方向冲突 |
| T2.5 | 按消费者逐个迁移，保留旧入口兼容 wrapper | 每次迁移一个批次并跑同一 fixture |
| T2.6 | 为 legacy examples 建兼容 fixture | 不要求批量改写历史 examples 才能通过 parser |

### 8.2 JSON 与状态契约

| ID | 任务 | 验收 |
|---|---|---|
| T2.7 | 为 `confirm_ui/result.json` 明确 schema version、字段 owner、legacy defaults 和最终确认条件 | server、gate、Dashboard 使用同一字段定义 |
| T2.8 | 统一 Step ID、Step name、generation mode、route name 等枚举来源 | 文档、UI catalog、Dashboard contract 不再各自维护不一致枚举 |
| T2.9 | 复核 quality reports、`trace.jsonl`、conversion trace 和 checkpoint schema | 每种 JSON/JSONL 有 schema/version 或明确稳定契约 |
| T2.10 | 增加坏输入 fixture：缺字段、未知字段、旧版本、冲突模式、坏路径 | 错误路径 rc 非零且提示可行动 |

**Compatibility gate**：任何新必填字段必须提供旧项目读取策略。禁止通过批量修改所有历史项目来掩盖 reader 不兼容。

---

## 9. Phase 3 - Prompt 与 Skill 编排瘦身

**目标**：减少必读上下文和多处规则定义，同时保持所有硬门与生成质量。

### 9.1 治理元数据

| ID | 任务 | 验收 |
|---|---|---|
| T3.1 | 在 `prompt_audit_manifest.json` 声明 concern-level `authority_edges` | 无 authority cycle；每条边引用真实文件 |
| T3.2 | 为 modes、visual styles、image catalogs、template indexes 等建立 `registries` | 实际成员、索引和文档数量声明一致 |
| T3.3 | 为 `spec_lock`、Confirm result、page expression、generation mode 等建立 `schema_grammars` | 非 owner 文件中的重复语法定义被发现并收敛 |
| T3.4 | 为 selector 补真实 `load_event` 和 route/stage 选择依据 | 按需加载不再只是 token 上限模拟 |
| T3.5 | 所有 accepted duplicate 保留具体理由；删除失效豁免 | audit 0 error，open warning 有处置记录 |

### 9.2 文档拆分与加载策略

| ID | 任务 | 验收 |
|---|---|---|
| T3.6 | 对 `strategist.md`、`executor-base.md`、`generate-pptx.md`、shared standards 和 image role 文档做段落级 load analysis | 先列每段 load event，再移动内容 |
| T3.7 | 把必读内容限制为身份、硬约束、当前阶段输入输出和失败动作 | 案例、长解释、低频 catalog 改为按需引用 |
| T3.8 | 避免“核心摘要 + 原文”双份规则；只能有一个 owner | 摘要只做指针，不重写 schema 或完整步骤 |
| T3.9 | 路由级 context pack 独立：global、research、generate、image、template、native | 一条请求只加载适用 route/stage |
| T3.10 | 保留 Step 6 每页重读 `spec_lock.md`、逐页手写 SVG、禁止子代理生成 SVG 等硬纪律 | hard-rule diff 清单逐项通过 |

### 9.3 Prompt 验证

默认实验目标：Generate typical load-set tokens 相对 Phase 0 基线降低至少 20%，且不得通过单纯提高 `max_tokens`、扩大 exempt 或漏登记文档达成。

最终指标由 Gate G1 用户确认；未确认时不得把默认实验目标宣布为正式目标。

验证必须包含：

1. `prompt_audit.py --json` 前后对比。
2. hard-rule presence 清单。
3. 三类代表性任务的 route/load-set 演练。
4. 至少三份固定 Brief 的 Strategist / Executor 输出对比。
5. 质量门结果和人工纠正次数对比。

### Gate G2 - 模型 A/B 授权

若验证需要实际调用付费模型、图片生成或外部研究，先提交样本数、预计成本、模型、输入、输出保留位置和停止条件，等待用户授权。静态 audit 与本地 fixture 不需要该授权。

---

## 10. Phase 4 - 契约回归、质量门与 CI

**目标**：让每个高风险边界拥有可重复的回归证据。

| ID | 任务 | 验收 |
|---|---|---|
| T4.1 | 在现有 smoke integration 中加入 artifact/state/parser/route fixture | 不创建与仓库约定冲突的测试脚手架 |
| T4.2 | 对所有顶层 CLI 做坏参数和缺文件 rc 探测 | 错误路径不得静默 rc=0 |
| T4.3 | 覆盖 checkpoint、split resume、partial project、legacy project | next action 与 owning workflow 一致 |
| T4.4 | 覆盖 `spec_lock` mode、page IDs、images、digest 和 page expression | checker、validator、E2E 不互相矛盾 |
| T4.5 | 覆盖 Confirm UI final result、chat fallback、pending template selection、stale result | gate 结果确定且可恢复 |
| T4.6 | 复核 `harness_gate --read-only` 不写项目；写模式产物 schema 稳定 | 只读验证不会污染 fixture |
| T4.7 | 评估是否把 contract/drift check 加入现有 CI | 只有本地等价命令稳定后才改 CI |
| T4.8 | 最终对公开 examples 运行 checker + E2E 双门 | 不能只证明文件存在 |

**Hard rule**：不能为了让 CI 变绿而降低 ERROR、跳过 examples、吞退出码或把失败改成 warning。

---

## 11. Phase 5 - 运行可观测性与优化数据

**目标**：复用现有 Dashboard 和 `trace.jsonl`，得到足以指导后续优化的数据，不建设新服务。

| ID | 任务 | 验收 |
|---|---|---|
| T5.1 | 盘点 trace event writer、reader、Dashboard contract 和 harness trace | 事件 owner 明确 |
| T5.2 | 统一最小 event envelope：schema version、timestamp、route、step、operation、status、duration、error code、artifact refs | reader 对旧事件保持兼容 |
| T5.3 | 记录关键阶段开始/完成/失败/重试，不记录源文全文、Prompt 正文、密钥或隐私内容 | trace 可分享而不暴露敏感数据 |
| T5.4 | Dashboard 只展示 canonical state 和 trace，不自行计算另一套结果 | state 与 event 含义一致 |
| T5.5 | 定义优化指标：阶段耗时、失败率、重试率、gate 错误分布、用户修订次数、Prompt tokens | 每项能从现有 artifact 或明确回执获得 |
| T5.6 | 对无真实信号的指标保持未采集，不伪造默认值 | `null` 与 `0` 语义区分 |

---

## 12. Phase 6 - Python 代码结构收敛

**目标**：只拆分真正具有多重职责和高变化风险的模块，保持公共行为不变。

### 12.1 热点选择评分

每个候选模块按以下维度评分 0-2：

| 维度 | 0 | 1 | 2 |
|---|---|---|---|
| Churn | 很少修改 | 偶尔修改 | 高频修改 |
| Defects | 无已知缺陷 | 偶发 | 重复缺陷 |
| Responsibilities | 单一 | 两类 | 三类以上 |
| Fan-in | 低 | 中 | 高 |
| Testability | 已隔离 | 部分耦合 | 难以单测/fixture |
| Change blast radius | 局部 | 跨文件 | 跨 route / export |

总分低于 7：默认不重构，只记录观察。总分达到 7：可进入 characterization；达到 9 且用户批准后才进行结构拆分。

初始候选仅用于审计，不代表必须修改：

- `svg_quality/checker.py`
- `svg_to_pptx/pptx_package/builder.py`
- `svg_to_pptx/drawingml/elements.py`
- `pptx_animations.py`
- `native_enhance_pptx_core.py`
- `confirm_ui/server.py`
- `narration_sync.py`
- `prompt_audit.py`

### 12.2 单模块重构流程

| ID | 任务 | 验收 |
|---|---|---|
| T6.1 | 建消费者 × 符号矩阵 | 所有 import 和 CLI 消费点已知 |
| T6.2 | 写 characterization fixture | 重构前能证明当前行为 |
| T6.3 | 按职责抽取内部模块 | 新模块至少有两个真实消费者或显著降低一个复杂职责 |
| T6.4 | 保留原 import / CLI wrapper | public API 无未声明破坏 |
| T6.5 | 每抽取一块立即跑目标 fixture + smoke | 禁止整文件搬完后才验证 |
| T6.6 | 对比 LOC 不是主要验收；比较职责、重复、依赖边和缺陷面 | 不以“文件变小”宣布成功 |

**禁止**：引入 DI framework、plugin framework、event bus 或抽象基类，只为让架构看起来统一。

---

## 13. Phase 7 - 性能、依赖与 CLI 卫生

### 13.1 性能优化

性能工作只处理 Phase 0/5 数据证明的瓶颈，优先级如下：

1. 重复 Prompt 加载和上下文体积。
2. 重复 artifact 扫描和 `spec_lock` 解析。
3. 可安全复用的模板 / registry / index 读取。
4. 进程启动和非必达重依赖。
5. 核心导出或质量检查内部热点。

每个性能批次必须：

- 使用同一 fixture、环境和采样方法。
- 至少报告 p50/p95 和样本数。
- 一次只改一个变量。
- 同时运行质量与行为回归。
- 结果无改善或变慢时恢复本批自己的修改。

**Known constraint**：不要重复“把每次必达的 checker import 移进函数”实验；历史实测该方向完整运行约慢 25%。只有包内部依赖图或调用条件已经改变时才可重新评估。

**Default regression threshold**：未获另行确认时，代表性流程 p50 或 p95 变慢超过 10% 视为回归；低于 10% 但无维护性收益的变化也不保留。

### 13.2 依赖与 Provider

| ID | 任务 | 验收 |
|---|---|---|
| T7.1 | 对照 requirements 与 import 使用面，标记核心、可选和仅开发依赖 | 不删除未完成消费者核验的依赖 |
| T7.2 | 保持 Provider SDK 懒导入和软失败 | 无 Provider 凭据时核心 CLI 仍可 import / `--help` |
| T7.3 | 统一 Provider adapter 的输入、输出、错误和 provenance 契约 | Provider 特例不泄漏到编排层 |
| T7.4 | 复核 `.env`、credentials、浏览器/session 文件处理 | 不读取或打印秘密值 |
| T7.5 | 新依赖必须附必要性、体积、许可证和替代方案 | 默认优先标准库/现有依赖 |

### 13.3 CLI 卫生

| ID | 任务 | 验收 |
|---|---|---|
| T7.6 | 顶层入口统一 `main(argv=None) -> int` + `raise SystemExit(main())` | 坏参数 rc 非零 |
| T7.7 | 统一 stdout/stderr、JSON 输出和人类提示边界 | 机器调用不依赖横幅文本 |
| T7.8 | 复核 Windows `python` / `python3`、路径和编码行为 | PowerShell 与 CI 环境均通过 |
| T7.9 | 维护 runtime pipeline / workflow satellite / maintenance / internal helper 分类 | 新入口能找到 owner 和文档 |

---

## 14. Phase 8 - 文档、治理与最终交付

| ID | 任务 | 验收 |
|---|---|---|
| T8.1 | 更新实际 owning workflow / reference；摘要文件只链接，不复制完整规则 | 权威层级无反转 |
| T8.2 | 脚本或 workflow 改动按仓库惯例写 `docs/change-log.md` | plans/reviews 本身不写 change log |
| T8.3 | 运行全仓 Markdown 链接分类检查 | 真断链为 0；代码块占位不误修 |
| T8.4 | 运行 prompt audit、governance drift、guard、完整 smoke | 所有 open error 为 0 |
| T8.5 | 对代表性 fixture 运行 harness、E2E、PPTX structure QA 和必要视觉检查 | 结果逐项记录 |
| T8.6 | 对公开 examples 跑 CI 本地等价检查或由获批 CI 证明 | checker + E2E 双门 |
| T8.7 | 生成最终前后对比报告 | 指标、风险和未做事项完整 |
| T8.8 | 清理本批 `.tmp/` / disposable project / 服务进程 | 无遗留服务和临时项目 |

默认最终报告：

```text
docs/reviews/deepppt2-system-optimization-final-2026-08.md
```

报告必须包含：

1. 修改范围与未修改范围。
2. 每个 Phase 的任务状态和 execution receipt。
3. Prompt tokens、性能、测试、CI 和质量门前后对比。
4. Public CLI / artifact / schema 兼容性说明。
5. 剩余风险、关闭原因和后续观察项。
6. 新增依赖、删除/移动文件和回滚说明；没有则明确写“无”。
7. 当前 git status；不得自动 commit、push 或 deploy。

---

## 15. 阶段验证矩阵

| 变更类型 | 最小验证 | 扩展验证 |
|---|---|---|
| 仅 plan / review 文档 | 状态头、链接、git diff | 不要求 smoke |
| `references/` Prompt | prompt audit、hard-rule diff | 固定 Brief A/B |
| workflow / routing | guard、governance drift、smoke | route 演练、resume fixture |
| shared parser / state | targeted fixture、smoke | Dashboard/checkpoint/harness 交叉验证 |
| CLI | import、`--help`、坏参数 rc | 真实命令 smoke |
| exporter / checker | targeted fixture、完整 smoke | representative export、checker + E2E |
| Dashboard / Confirm UI | schema、API/bridge fixture | 浏览器交互与服务清理 |
| CI | 本地等价命令 | 获批后远程 CI |
| 性能 | 同 fixture p50/p95 | 质量回归与跨环境抽查 |

基础命令按当前 Windows 环境使用：

```powershell
python skills/ppt-master/scripts/attribution_guard.py
python skills/ppt-master/scripts/governance_drift_check.py
python skills/ppt-master/scripts/prompt_audit.py --json
python skills/ppt-master/scripts/smoke_check.py --skip-help
python skills/ppt-master/scripts/smoke_check.py
python skills/ppt-master/scripts/harness_gate.py <project_path> --quick --read-only
python skills/ppt-master/scripts/e2e_validate.py <project_path> --pptx <project_path>/exports/<deck>.pptx
python skills/ppt-master/scripts/pptx_quality_check.py <project_path>/exports/<deck>.pptx --json-out <project_path>/quality/pptx_quality.json
```

命令参数必须替换为本 phase 已确认的 fixture。不得照抄占位符执行。

---

## 16. 风险与恢复

| 风险 | 触发信号 | 恢复动作 |
|---|---|---|
| Prompt 瘦身丢失硬约束 | route/load 演练或 A/B 出现遗漏 | 恢复本批移动，重新划分 core/on-demand |
| Parser 收敛改变 legacy 语义 | examples 或旧项目 fixture 失败 | 保留 compatibility adapter，不批量改历史 artifact |
| State 收敛覆盖 route 特例 | Dashboard/checkpoint/resume 结果不一致 | 回到 consumer matrix，新增明确 route-specific rule |
| 代码拆分丢符号或副作用 | import/真实 E2E 失败 | 恢复本批抽取，核对装饰器、入口和符号面 |
| 缓存产生陈旧状态 | 修改 artifact 后读到旧值 | 取消缓存或把 mtime/digest 纳入 key |
| 性能优化负收益 | 同 fixture p50/p95 变差 | 恢复本批，不保留理论优化 |
| CI 变慢或不稳定 | 本地与 CI 时间/结果明显偏离 | 撤回 CI 变更，保留本地 gate 后重新设计 |
| 用户改动被覆盖 | diff 出现非本批内容 | 立即停止，恢复自己的冲突改动而不是用户改动 |

任何失败恢复必须遵循 [`failure-recovery.md`](../skills/ppt-master/workflows/governance/failure-recovery.md)。禁止使用 `git reset --hard`、`git checkout --` 或批量清理来恢复用户工作区。

---

## 17. Phase Execution Receipt 模板

每个 phase 完成后输出以下内容，并写入对应 baseline/final report：

```markdown
## Phase <N> Execution Receipt

- Scope completed: <task IDs>
- Files changed: <paths or none>
- Existing user changes preserved: <yes/no + evidence>
- Baseline commands: <commands + results>
- Post-change commands: <commands + results>
- Metrics before/after: <tokens/performance/quality as applicable>
- Compatibility impact: <none or exact impact>
- Deviations: <none or declared deviation>
- Remaining risks: <list>
- Next gate: <G1/G2/user approval/next phase>
```

没有实际命令结果时只能写“verification planned”，禁止写“passed”。

---

## 18. Definition of Done

只有同时满足以下条件，整体优化才能标记完成：

- [ ] Phase 0 基线可复跑，所有数字有环境、命令和 fixture。
- [ ] Artifact 路径和 pipeline state 有单一事实源，Dashboard 与 checkpoint 一致。
- [ ] `spec_lock` 和关键 JSON artifacts 有明确 owner、统一 parser/schema 和 legacy 策略。
- [ ] Prompt authority graph、registries、schema grammars 和 load events 已启用且 audit 无 open error。
- [ ] 达到用户确认的 Prompt 缩减目标，硬约束与代表性输出质量无回归。
- [ ] 高风险契约有 fixture；CLI 错误路径返回非零。
- [ ] 所有代码重构均由热点评分和 characterization evidence 支持。
- [ ] 性能变更有同 fixture p50/p95，且质量门无回归。
- [ ] Guard、governance drift、prompt audit、完整 smoke 全部通过。
- [ ] 代表性 projects 和公开 examples 的适用 checker/E2E 门通过。
- [ ] 文档权威层级、链接和 change log 与实际实现一致。
- [ ] 无未授权删除、依赖、外部调用、commit、push 或 deploy。
- [ ] 无遗留临时项目、服务或本批日志污染。
- [ ] 最终报告列出修改、未修改、风险、回滚和后续观察项。

---

## 19. 契约回验

- Q1 意图保真：本 Brief 只优化既有系统的编排、契约、Prompt、可靠性、代码结构和证据化性能，不新增产品能力。
- Q2 无擅自决策：高风险改动、正式指标、模型 A/B、删除、依赖、CI、commit/push 均保留明确确认门。
- Q3 可独立执行：每个 phase 包含前置条件、任务 ID、产物、验证和停止条件。
- Q4 验收可判定：Definition of Done 可由命令、指标、fixture、diff 和清单逐项验证。

