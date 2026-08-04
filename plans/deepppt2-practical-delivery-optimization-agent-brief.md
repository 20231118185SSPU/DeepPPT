# DeepPPT2 实际交付优化 Agent Brief

> 状态：拟执行的优化契约，尚未实施。
> 权威性：非运行权威；执行时必须服从 [`AGENTS.md`](../AGENTS.md)、[`skills/ppt-master/SKILL.md`](../skills/ppt-master/SKILL.md) 及具体 owning workflow / reference。
> 实施状态：本文件只定义目标、边界、阶段门和验收，不代表任何代码、工作流、CI 或用户项目变更已经获批。
> 适用仓库：`C:/Users/FUTIAN/Desktop/DeepPPT2`
> 制定日期：2026-08-04

---

## 0. 使用方式

本文件可直接作为后续 Agent 的执行指令。首次执行使用：

```text
按 plans/deepppt2-practical-delivery-optimization-agent-brief.md 执行 Phase 0；只读建立当前基线，提交 Gate G1 回执后停止，等待我确认实施范围。
```

用户批准 Gate G1 后，继续时使用：

```text
继续执行 plans/deepppt2-practical-delivery-optimization-agent-brief.md 中已批准的下一 Phase；每次只完成一个可独立验证的批次。
```

**Hard rule**：首次执行只能完成 Phase 0。创建、阅读或引用本文件不等于批准修改运行文件。

**Hard rule**：每个 Phase 是独立任务。禁止一次性跨 Phase 修改，禁止用后续收益为当前未验证改动辩护。

**Hard rule**：当前优化目标是降低成品缺陷、内容遗漏和人工返修，不是继续追求代码行数、抽象层数或 Prompt token 的漂亮数字。

---

## 1. 目标

把上一轮“系统收敛”成果转化为真实交付可靠性，优先改善以下结果：

| 结果 | 定义 | 最终验收方向 |
|---|---|---|
| 可交付成功率 | PPTX 可打开、结构完整、图片可见、字体风险可解释、PowerPoint 实际渲染无阻断缺陷 | 已批准 Golden Set 中 `BLOCKER=0` |
| 内容完整性 | 源材料中的关键表格、数字、图片、符号和备注不会静默丢失 | 已选转换器 fixture 对账通过；无法转换项有定位和原因 |
| 人工返修量 | 从首次预览到最终交付所需的 annotation、重生成和重导出次数 | 每次真实运行均可采集，不再是未知字段 |
| 路线回归覆盖 | 正式支持的主要路线有可复跑 fixture，而非只验证 Generate flat | Gate G1 选定路线全部有 fixture 和预期结果 |
| 中断恢复能力 | 新会话或失败门禁能得到确定、可行动的下一步 | 已批准 partial-state 场景全部返回稳定诊断 |
| 开发反馈效率 | PR 和本地修改能快速得到可信反馈 | 只在基线证明有收益后优化 CI；不得牺牲全量门禁 |

Phase 0 必须先测量当前值。除本文件明确写出的安全阈值外，禁止伪造基线或先写“提升百分比”再寻找证据。

---

## 2. 已知背景与待复核事实

以下是执行入口，不是永不过期的事实。Phase 0 必须重新核对：

| 编号 | 待复核事实 | 当前证据 |
|---|---|---|
| F1 | 上一轮系统优化已完成 Prompt、状态、parser、trace 和 CLI 收敛；继续做同类重构边际收益低 | [`deepppt2-system-optimization-final-2026-08.md`](../docs/reviews/deepppt2-system-optimization-final-2026-08.md) |
| F2 | 当前工作区存在用户或前序 Agent 的未提交修改，包括真实 PowerPoint 渲染、SVG 几何审计、DOCX 表格恢复和视觉复核改动 | `git status --short`、`git diff`、[`docs/change-log.md`](../docs/change-log.md) |
| F3 | `structured`、`template-fill`、`beautify` 缺少公开实战 fixture | [`deepppt2-system-optimization-baseline-2026-08.md`](../docs/reviews/deepppt2-system-optimization-baseline-2026-08.md) |
| F4 | anchor compare 仍在 `_ANCHOR_COMPARE_ENABLED=False` 后；全局启用会产生 240+ legacy 漂移 | `skills/ppt-master/scripts/svg_quality/checker.py` |
| F5 | trace envelope 已版本化，但用户修订次数仍未形成 artifact；关键阶段的 trace 覆盖不完整 | `scripts/dashboard/trace_writer.py`、最终报告剩余风险 |
| F6 | `derive_pipeline_state()` 已统一 happy-path 状态，但现有集成测试主要覆盖 artifact 逐步出现的顺序链 | `scripts/project_utils.py`、`scripts/smoke_check.py::check_state_derivation` |
| F7 | `projects/` 最近只读测量约 4.82 GiB，前 5 个项目约 2.71 GiB；容量治理有现实价值，但不得自动清理 | Phase 0 重新测量 |
| F8 | 历史 CI 全量任务曾达到约 17-21 分钟；实际当前耗时需从 CI 记录或获批复跑取得 | [`deep-ppt-repository-inventory-2026-08.md`](../docs/reviews/deep-ppt-repository-inventory-2026-08.md) |

**Dirty-worktree rule**：F2 是最高优先级边界。先识别已有改动的来源和意图；禁止覆盖、回退、格式化或“整理”任何非本批改动。

---

## 3. 范围与授权

### 3.1 In scope

- 真实 PowerPoint 渲染、SVG 几何审计、PPTX 交付检查和 visual review 的校准与衔接。
- Generate、structured、template-fill、beautify、native enhance、resume 等已存在路线的合成 fixture 与契约回归。
- 依据真实源文件使用分布，对最高优先级转换器做内容完整性对账。
- 本地 trace、`run_summary.json`、revision / retry / gate error 等非敏感运行指标。
- partial project、failed gate 和 fresh-chat resume 的只读诊断与确定性 next action。
- 有明确基线和用户批准时的 CI 反馈优化、项目空间报告和可恢复归档设计。
- 与实际改动直接相关的 owning script、workflow/reference、smoke fixture、文档和 change log。

### 3.2 Out of scope

- 新增模板、图表、动画、Provider、生成模式或产品形态。
- 再次执行已经完成的 parser、Prompt corpus、CLI 或模块拆分优化。
- 全仓格式化、目录重组、通用 `tests/` 脚手架或把 `scripts/` 改成 Python package。
- 为让 legacy examples 通过而批量改写 240+ anchor 数据。
- 没有真实失败证据时统一所有 quality / validation / conversion trace schema。
- 没有 profiling 证据时做运行性能优化。
- 自动删除 `projects/`、历史图片、源文件、导出物或任何用户工作成果。
- commit、push、发布、部署或外部系统写入。

### 3.3 必须单独确认

| 操作 | 解除条件 |
|---|---|
| 使用 `projects/` 中真实用户 deck 作为长期 fixture | 用户明确指定项目；不得复制敏感源内容到公开目录 |
| 把新检查从 advisory 升级为阻断门 | 提交校准数据、误报率、legacy 影响和回滚开关，等待批准 |
| 修改公开 CLI、artifact 必填字段或 schema | 提交兼容矩阵、版本策略和旧项目行为，等待批准 |
| 修改 `SKILL.md`、routing 或 owning workflow 的门禁行为 | 说明为何不能只改脚本/参考文件，并等待批准 |
| 修改 `.github/workflows/` | 先提供本地等价验证、预计耗时和回滚方案，等待批准 |
| 新增依赖 | 证明标准库和现有依赖不能完成任务，列许可证与体积，等待批准 |
| 运行付费 API、图片生成、模型 A/B 或外部研究 | 列样本、成本和停止条件，等待批准 |
| 删除、移动、重命名、清理、归档用户文件 | 展示精确路径、可恢复方式和 dry-run，等待批准 |
| commit / push / deploy | 用户明确授权 |

---

## 4. 执行策略

- 信息足够且低风险：只执行当前已批准 Phase 的最小批次。
- 信息可从仓库、文件、日志、fixture 或历史报告获得：自行读取，不向用户转嫁调查工作。
- 关键信息缺失且会改变目标、fixture、兼容边界或验收：停下来，一次只问一个问题，并给推荐答案。
- 高风险操作的信息、范围、恢复、授权或验收不完整：停止；不得以“先试试”为理由执行。
- 只读分析阶段：禁止修改任何文件。
- 代码修改阶段：先建立同口径基线，再做最小修改，再运行同一验证。
- 发现实际影响超出当前 Phase：说明偏离；改变范围时必须等待确认。
- 发现现有基线失败：记录失败与 dirty worktree 的关系；禁止把既有失败伪装成本批回归或顺手修复。
- 每个 Phase 结束必须提交 execution receipt；未达到本 Phase 验收不得进入下一 Phase。

---

## 5. 强制加载与批次纪律

每个新会话按以下顺序执行：

1. 读取 `.align/lessons.md`、`.align/spec.md`、`.align/context.md`。
2. 读取 [`AGENTS.md`](../AGENTS.md)。
3. 完整读取 [`skills/ppt-master/SKILL.md`](../skills/ppt-master/SKILL.md)。
4. 运行 `python skills/ppt-master/scripts/attribution_guard.py`。
5. 读取本文件、上一阶段回执和当前 Phase 涉及的 owning rules / workflows。
6. 运行 `git status --short` 和目标文件 diff；记录但不改变既有工作区。

每个代码批次必须具备：

- 一个目标和一个明确排除范围。
- 目标文件及其消费者清单。
- 修改前后完全一致的验证命令。
- 明确的 public API / schema / artifact 兼容判断。
- 可逆补丁；禁止混入顺手重构。

修改 `scripts/` 或 `workflows/` 前后必须按仓库规则运行 smoke baseline。新增脚本必须满足模块导入无副作用、`--help` 成功、错误路径返回非零。

---

## 6. Phase 0 - 只读交付基线

**目标**：确认当前工作区事实、选择可公开复跑的 Golden Set、定义实施范围；不修改任何文件。

### 任务

| ID | 动作 | 输出 / 验收 |
|---|---|---|
| T0.1 | 记录 branch、HEAD、Python、OS、PowerPoint/PowerShell 可用性和 `git status --short` | 环境表；不打印凭据或 `.env` |
| T0.2 | 对当前 dirty files 做“用户改动 / 已验证在途改动 / 未知来源”分类 | 文件级 ownership 表；未知项不得修改 |
| T0.3 | 运行 guard、`.align/check-commands.txt` 中无参数命令、完整 smoke 和 integration smoke | 每条命令记录 rc、passed/failed/skipped |
| T0.4 | 复核 `svg_geometry_audit.py`、`pptx_render_export.py`、`visual_review.py` 和 `pptx_delivery_check.py` 的当前实现、帮助和 change-log 回执 | 当前能力、缺口、是否已验证的矩阵 |
| T0.5 | 只统计 `projects/*/sources/` 的文件扩展名和数量，不读取或输出内容 | 转换器使用优先级依据 |
| T0.6 | 复核 examples / synthetic fixture 对正式路线的覆盖 | route × fixture × gate 矩阵 |
| T0.7 | 测量 `projects/` 总容量、项目数和前五大目录；只报告，不清理 | 容量快照 |
| T0.8 | 从现有非敏感 examples 提出 3-5 套 Golden Set；如需真实用户 deck，单独列为待确认 | 每套说明覆盖缺陷与运行成本 |
| T0.9 | 制定 Phase 1 的校准样本、缺陷 taxonomy、误报统计方法和停止条件 | 可判定的 Phase 1 验收 |

### Phase 0 验证命令

```powershell
python skills/ppt-master/scripts/attribution_guard.py
python skills/ppt-master/scripts/smoke_check.py --skip-help
python skills/ppt-master/scripts/smoke_check.py
python skills/ppt-master/scripts/smoke_check.py --integration
```

如果命令因当前 dirty worktree 或既有环境失败，报告事实并定位，不得在 Phase 0 修复。

### Gate G1 - 实施范围确认（BLOCKING）

Phase 0 完成后必须停止，并向用户提交：

1. 当前基线和既有失败。
2. Golden Set 推荐及是否涉及用户项目。
3. Phase 1 目标文件、预计改动和不改范围。
4. 将继续保持 advisory 的检查。
5. 需要单独授权的操作。

未收到明确批准，不得进入 Phase 1。

---

## 7. Phase 1 - 真实成品质量闭环 V1

**目标**：让 PowerPoint 实际渲染成为最终视觉依据，并用校准数据决定哪些检查可阻断交付。

### 任务

| ID | 动作 | 验收 |
|---|---|---|
| T1.1 | 对当前几何审计和 PowerPoint 渲染改动建立消费者、输出和退出码矩阵 | 不覆盖在途改动；public behavior 明确 |
| T1.2 | 在已批准 Golden Set 上运行 SVG 静态门、geometry audit、导出、PPTX delivery check、PowerPoint PNG render 和人工/视觉复核 | 每页有统一 defect record |
| T1.3 | 缺陷分类至少区分文字交叠、裁切、z-order 遮挡、空白/缺失图片、字体风险、断言不可见、内容数据不一致 | 每类有严重度和修复动作 |
| T1.4 | 对每条 geometry rule 标注 TP / FP / FN；复现既有已知缺陷 | 已知缺陷召回 100%；统计口径可复跑 |
| T1.5 | 只修复有 fixture 证明的工具缺陷或漏检；一次只改一个规则 | 修改前后用同一 Golden Set 对比 |
| T1.6 | 保持新检查 advisory；只有 precision `>=95%`、Golden Set 无误阻断且用户批准时才可升级 | 默认行为不变；升级有独立开关和回滚 |
| T1.7 | 将最终复核顺序写入 owning workflow / script doc；摘要文件只链接 | 权威层级不反转 |

### 代表性命令

```powershell
python skills/ppt-master/scripts/svg_geometry_audit.py <project_path>
python skills/ppt-master/scripts/svg_to_pptx.py <project_path>
python skills/ppt-master/scripts/pptx_delivery_check.py <exported_pptx>
python skills/ppt-master/scripts/pptx_render_export.py --pptx <exported_pptx> -o <project_path>/quality/pptx_render
python skills/ppt-master/scripts/e2e_validate.py <project_path> --pptx <exported_pptx>
```

### Phase 1 验收

- 已批准 Golden Set 中已知视觉缺陷全部被复现或由 PowerPoint PNG 明确裁决。
- 最终 PowerPoint render 中 `BLOCKER=0`；warning 均有接受或修复记录。
- advisory 默认行为不变；未获批不得打开 `_ANCHOR_COMPARE_ENABLED` 或 `--strict` 全局门禁。
- 不新增依赖，不改变 PPTX 输出结构，不降低现有门禁。
- guard、smoke、目标 fixture harness / E2E 全绿。

### Gate G2 - 硬门升级确认（仅在提出升级时 BLOCKING）

如 Agent 建议把某条 advisory 检查升级为 ERROR，必须先提交 precision、误报样例、legacy 影响和回滚开关。用户未批准时，Phase 1 可按 advisory 完成，但不得升级。

---

## 8. Phase 2 - 跨路线 Golden Fixtures

**目标**：让正式支持路线拥有最小、合成、非敏感、可重复的回归依据。

### 执行规则

1. 根据 Phase 0 的真实使用频率排序，不默认所有路线同优先级。
2. fixture 先在 `.tmp/` 或 `_smoke_*` 中验证；只有用户批准后才能加入受跟踪目录。
3. 每套 3-5 页，内容合成且不含用户品牌、个人信息、密钥或受限素材。
4. 不创建通用 `tests/`；优先接入现有 smoke / harness / E2E 体系。
5. 二进制 fixture 必须记录来源、许可证、大小和可重建方式。

### 候选覆盖

- Generate flat。
- Generate structured。
- Fill Native PPTX / template-fill。
- Beautify 1:1。
- Enhance Native PPTX。
- Phase B resume、partial SVG、failed gate。
- 含图片、图表、合并表格或 symbol run 的复杂输入。

### Phase 2 验收

- Gate G1 选定路线全部有至少一个 fixture；未覆盖路线明确列为 excluded，不伪装完成。
- 每套 fixture 有输入、执行命令、预期 artifact、预期 gate 结果和清理方式。
- 快速契约检查进入 smoke；耗时的真实渲染保留为手动或获批的完整门。
- fixture 不依赖网络、付费 API、浏览器登录态或用户私有文件。
- 相关 checker、harness、E2E 和 PPTX delivery check 全绿。

---

## 9. Phase 3 - 源内容完整性对账

**目标**：优先解决真实使用最多的源格式，禁止表格、数字、图片、符号或备注静默丢失。

### 执行规则

1. 依据 Phase 0 的 source extension 统计选择最多两个转换器；不得先写全格式抽象框架。
2. 先写 characterization fixture，再修改转换器。
3. 对 DOCX 至少覆盖 `vMerge`、`gridSpan`、多段落 cell、`w:sym`、图片和普通表格。
4. 对第二种格式只覆盖真实使用中出现的高风险结构。
5. 无法保真转换的元素必须产生可行动 warning；不得静默吞掉。
6. 不引入新依赖，除非用户在看到标准库/现有依赖限制后批准。

### 建议 artifact

若 Phase 0 证明有必要，可新增版本化 `source_fidelity_report.json`，最小字段为：

- `schema_version`、converter、source type。
- 源与输出的 heading / table / row / cell / image / note 计数。
- 关键结构的 normalized digest 或非敏感摘要。
- unsupported / dropped / warning 列表及源位置。
- `status`：passed / warning / failed。

禁止在报告中复制完整源文、Prompt、凭据或个人信息。

### Phase 3 验收

- 选定 fixture 的结构计数和关键数字对账一致。
- 任意故意损坏 fixture 都能得到非零退出或明确 warning，不能返回“成功且无提示”。
- 现有正常转换结果无未声明格式回归。
- smoke 增加目标契约断言；不新建通用测试框架。

---

## 10. Phase 4 - 本地运行指标闭环

**目标**：让后续优化由真实运行数据决定，同时保持本地、非敏感和低侵入。

### 最小指标

- route、slide count、阶段开始/结束和 `duration_ms`。
- gate status、error code、retry count。
- 图片生成/搜索尝试次数，不记录 Prompt 正文。
- Live Preview annotation count、SVG regeneration count、PPTX re-export count。
- 最终 delivery / E2E / visual result。
- 未采集值为 `null`，真实零值为 `0`。

### 执行规则

- 复用 `trace_writer.py` envelope，不建设外部 telemetry 服务。
- trace 写失败不得阻断主流程；聚合失败必须可诊断。
- 最终生成版本化 `quality/run_summary.json`；Dashboard 展示是可选消费者，不是 owner。
- 对 trace 和 summary 做敏感字段负面测试，禁止源文、Prompt、URL query、密钥和文件内容进入事件。

### Phase 4 验收

- 校准集每次完整运行都能生成 schema-valid summary。
- 已实际测量字段不为 `null`；未发生事件记 `0`，未接入测量记 `null`。
- 同一 trace 多次聚合结果一致。
- 可回答“哪一步最慢、为何失败、重试多少、人工改了几次”。

---

## 11. Phase 5 - 中断恢复与只读诊断

**目标**：在不自动执行或覆盖 artifact 的前提下，为 partial project 提供确定性 blocker 和 next action。

### 场景

- 空项目 / 只有 sources。
- confirmation pending、stale 或 malformed。
- `spec_lock.md` 缺失、digest 不一致或 mode 冲突。
- 图片部分完成或 manifest 失败。
- SVG 页数不足、命名冲突或 quality gate 失败。
- `svg_final/` 已存在但未导出。
- PPTX 已导出但 delivery / E2E 失败。
- split-mode Phase B resume。

### 输出契约

只读诊断至少返回：

- 当前 route / step / status。
- evidence artifacts。
- blockers（稳定 error code + 可行动说明）。
- 唯一 recommended next action。
- 可选 command preview；禁止自动执行。

### Phase 5 验收

- 已批准场景每种至少一个 fixture。
- 相同 fixture 重复诊断结果稳定，时间字段除外。
- 保持现有 `derive_pipeline_state()` 返回字段兼容。
- project manager 与 Dashboard 使用同一诊断 owner，不各写一套。
- 坏输入 fail closed；诊断命令不修改项目。

---

## 12. Phase 6 - 可选效率优化

本 Phase 默认不执行。Phase 1-5 的数据证明收益且用户单独批准后，才可选择一个子任务。

### 12.1 CI 反馈时间

候选手段：`setup-python` pip cache、examples 分片、PR 只跑受影响快速集、main / scheduled 保留全量集。

约束：

- 先记录当前 CI p50 / p95 和各 job 分解。
- 不得以跳过完整门禁换速度。
- 修改 workflow 前必须通过 3.3 授权门。
- 推荐目标为 PR p95 `<=8 min`；若 Phase 0 证明不现实，在 Gate 回执中提出新阈值。

### 12.2 项目空间治理

候选手段：只读 size report、按 artifact 类型列占用、可恢复 archive 设计、显式 `--dry-run`。

约束：

- 默认只报告，不删除。
- 图片、sources、spec、用户 annotations 和最终 exports 默认视为不可再生。
- 清理命令必须列出精确路径、预计释放量和恢复方式，并再次等待用户确认。
- 禁止 bulk-clean `projects/`。

---

## 13. 验证矩阵

按改动范围运行，不得用不相关绿灯替代目标验证：

| 变更 | 最低验证 |
|---|---|
| 任意 repo 修改 | attribution guard |
| `scripts/` 修改 | 修改前后 `smoke_check.py --skip-help`；目标 fixture；完整 smoke |
| CLI 新增/修改 | import、`--help`、坏参数 rc 非零、stdout/stderr 边界 |
| workflow / reference 修改 | governance drift；prompt audit；链接检查；对应运行契约 |
| SVG quality 规则 | characterization fixture；Golden Set TP/FP/FN；examples spot/full 按影响面 |
| 导出或 PPTX 检查 | `svg_to_pptx`、`pptx_delivery_check`、PowerPoint render、E2E |
| source converter | 正常/合并/符号/坏输入 fixture；内容计数与关键值对账 |
| trace / summary | schema、legacy event、null/0、敏感字段负面测试 |
| pipeline diagnosis | happy path + partial states + deterministic repeat |
| CI workflow | 本地等价命令；获批后的真实 CI 结果 |

当 workflow / reference 或 Prompt corpus 被修改时，至少运行：

```powershell
python skills/ppt-master/scripts/governance_drift_check.py
python skills/ppt-master/scripts/prompt_audit.py
```

最终涉及真实项目导出时，至少运行：

```powershell
python skills/ppt-master/scripts/harness_gate.py <project_path> --quick
python skills/ppt-master/scripts/e2e_validate.py <project_path> --pptx <exported_pptx>
python skills/ppt-master/scripts/pptx_delivery_check.py <exported_pptx>
```

---

## 14. 风险与恢复

| 风险 | 禁止动作 | 恢复策略 |
|---|---|---|
| dirty worktree 冲突 | checkout/reset/覆盖用户改动 | 停止目标文件修改，提交冲突清单 |
| advisory 误报 | 未校准直接升硬门 | 保持默认关闭或 warning；用开关回滚 |
| legacy examples 大面积漂移 | 批量改 240+ anchor | 新 schema / 新项目生效；legacy 保持兼容 |
| PowerPoint COM 不可用 | 用 Chromium 冒充最终真相 | 记录环境限制；不宣称完成真实渲染验收 |
| fixture 泄露用户内容 | 复制真实 deck 到 examples | 使用合成 fixture；真实项目只做获批本地校准 |
| source report 泄露内容 | 写入全文或敏感路径 | 只存计数、digest、位置和安全摘要 |
| CI 提速降级覆盖 | 跳过全量门禁 | PR 快速集 + main/scheduled 全量集 |
| 空间治理误删 | 自动清理或宽泛 glob | 只读报告、dry-run、精确路径、显式确认 |

任一 Phase 无法满足验收时，停止在该 Phase。困难、耗时或数据不足不等于可以降低门槛。

---

## 15. Phase Execution Receipt

每个 Phase 结束必须使用以下格式：

```markdown
## Phase <N> Execution Receipt

- Status: PASS / FAIL / BLOCKED
- Scope completed:
- Files changed:
- Existing dirty files preserved:
- Baseline commands and results:
- Post-change commands and results:
- Golden fixtures used:
- Public CLI / schema / artifact changes: none / list
- New dependencies: none / list
- Regressions or false positives:
- Rollback:
- Temporary artifacts and services cleaned:
- Pending user decisions:
- Recommended next Phase:
```

`PASS` 必须引用实际命令、结果和 artifact；计划中的命令不能作为完成证据。

---

## 16. Definition of Done

只对用户明确批准并实际执行的 Phase 判定完成。整体计划完成需要：

- [ ] Phase 0 基线和 Gate G1 决策可对账。
- [ ] 已批准 Golden Set 的 PowerPoint 真实渲染 `BLOCKER=0`。
- [ ] 升级为硬门的检查均有 `>=95%` precision、legacy 影响和回滚开关；未获批项保持 advisory。
- [ ] Gate G1 选定路线全部有非敏感、可复跑 fixture。
- [ ] 已选转换器的高风险结构对账通过，无静默丢失。
- [ ] 完整运行可生成非敏感 `run_summary.json`，revision / retry / gate error 可解释。
- [ ] 已批准 partial-state 场景均返回稳定 blocker 和唯一 next action。
- [ ] guard、smoke、目标 harness、E2E、delivery check 和必要真实渲染全部通过。
- [ ] Prompt / workflow 改动通过 prompt audit、governance drift 和链接检查。
- [ ] 无未授权依赖、删除、CI、API、commit、push 或 deploy。
- [ ] 无遗留服务；本批临时目录已清理或明确列出保留原因和命令。
- [ ] 脚本 / workflow 改动已按仓库惯例更新 `docs/change-log.md`；计划和 review 文件本身不写 change log。
- [ ] 最终报告列出前后指标、未完成项、剩余风险和回滚方式。

---

## 17. 契约回验

- Q1 意图保真：本 Brief 优化真实 PPT 交付质量、内容完整性和返修成本，没有把目标替换为通用代码重构。
- Q2 无擅自决策：fixture、真实用户项目、硬门升级、CI、依赖、删除和外部成本均保留用户确认门。
- Q3 可独立执行：首次只执行 Phase 0；每个后续 Phase 均有输入、边界、命令和停止条件。
- Q4 验收可判定：每个 Phase 都有实际命令、量化阈值或 fixture 对账，不以“更稳定”“更优雅”宣布完成。
