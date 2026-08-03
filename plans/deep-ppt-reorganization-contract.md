# DeepPPT2 统一盘点、治理与性能优化执行契约

> **状态**：已批准执行契约（2026-08-03）。  
> **权威性**：本文档是后续模型（Agent）的可执行 Brief 与治理契约，**不覆盖** `AGENTS.md`、`skills/ppt-master/SKILL.md` 及各 workflow authority。冲突时以 `AGENTS.md` / `SKILL.md` / `workflows/routing.md` / `workflows/generate-pptx.md` 为准。  
> **配套事实报告**：`docs/reviews/deep-ppt-repository-inventory-2026-08.md`（只读盘点，2026-08-03 实测）。  
> **执行模式**：分阶段执行，每阶段独立验收；第一阶段（Phase 0/1）已完成，本契约记录其结果并约束后续阶段。

---

## 1. 目标

把 DeepPPT2 从「迁移刚完成、事实源未收敛」的状态整理为「事实对账一致、边界明确、可安全治理、有证据驱动的性能优化路径」的仓库：

1. 建立全仓可对账的事实盘点（文件数、体积、跟踪状态、重复、引用关系）。
2. 收敛权威层级与目录边界（owner / 可修改 / 可删除 / 依赖方 / 回滚方式）。
3. 以「先证据、后动手、可回滚、每批验证」的方式推进低风险整理。
4. 以 profiling 证据驱动性能优化，禁止无证据抽象。
5. `projects/` 与 `examples/` 的产物治理独立成项，另立审批。

## 2. 背景（2026-08-03 实测事实，详见盘点报告）

- 仓库 24,197 个文件、7.24 GiB（7.78 GB）；Git 跟踪 14,534 个文件，untracked = 0（工作区干净），ignored = 9,663。
- `projects/` 33 个项目、6,000 文件、约 5.3 GiB（用户工作区，全 ignored，仅 `README.md` 跟踪）。
- `examples/` 29 个示例、2,016 文件、约 1.5 GiB（全跟踪，CI/Pages 公开回归基线）。
- `skills/ppt-master/scripts/`：81 个顶层入口（`smoke_check.py` 计 81）+ 20 个子目录 167 个 py = 248 个 Python 文件。
- smoke 基线（2026-08-03 实测）：完整模式 **158 passed / 0 failed / 4 skipped / 162 checks**；`--skip-help` 模式 **78 / 0 / 3 / 81 checks**。
- 最新提交 `31298372` 完成 ppt v4.3.0 大规模迁移（重构版导出器整体替换）；`plans/followup-migration-roadmap.md` 的 Phase 2-6 已全部执行但文档仍为「计划」形态。
- 重复哈希：1,828 组 / 6,568 文件，理论可回收约 3.26 GB，集中在 `projects/backup/` 多版本快照、examples↔projects 同源拷贝、`.codex/` 工具状态、图标库拷贝进项目。
- Markdown 链接：880 个 tracked md、1,037 条链接校验，0 真断链，8 条占位链接（`xxx.md` / `url` 示例，属既有允许项）。

## 3. 对象与范围

### 3.1 对象（in scope）

| 对象 | 内容 |
|---|---|
| 源码与文档 | `skills/ppt-master/`（scripts / workflows / references / templates）、`docs/`、`AGENTS.md`、根 `scripts/`、`plans/` |
| 配置 | `.github/workflows/`（ci.yml / deploy-pages.yml）、`.gitignore`、`requirements.txt` |
| 治理元数据 | `.align/`（spec/context/lessons 漂移收敛，更新需独立获批）、`docs/change-log.md` |
| 性能 | 脚本冷/暖启动、导入、目录扫描、Dashboard、质量检查、代表性导出流程 |

### 3.2 范围外（out of scope，除非用户另行批准）

- `projects/` 历史文件（只建生命周期/归档规则，不处理文件本身）。
- `examples/` 定位变更、移出大型示例、Pages 改造（需单独发布链路设计）。
- 删除、移动、重命名任何历史产物；commit / push / 部署；有成本的外部 API 调用。
- `.env`、浏览器/会话文件、凭据、生产部署配置（敏感，禁止读写）。

## 4. 交付物

| # | 交付物 | 状态 |
|---|---|---|
| D1 | `plans/deep-ppt-reorganization-contract.md`（本文档） | ✅ 2026-08-03 |
| D2 | `docs/reviews/deep-ppt-repository-inventory-2026-08.md`（事实盘点，`[原文]`/`[推断]`/`[待验证]` 三分类） | ✅ 2026-08-03 |
| D3 | 权威层级矩阵 + 目录 owner/可删性表（在 D2 §2-3） | ✅ 2026-08-03 |
| D4 | 冗余/死文件/旧路线图/漂移差异清单（在 D2 §4-5，第一阶段不处理） | ✅ 2026-08-03 |
| D5 | Phase 2 低风险整理批次（索引、导航、状态标记、重复引用），每批 smoke 前后对比 | ⏳ 待批准 |
| D6 | Phase 3 性能基线报告（p50/p95，同一 fixture 前后对比）→ 量化目标 → 优化批次 | ⏳ 待批准 |
| D7 | Phase 4 产物治理方案（active/archive/disposable 分类 + 删除清单 + 回滚副本） | ⏳ 待批准 |

## 5. 约束（红线）

1. **只读优先**：任何删除/移动/重命名必须列在已批准的批次清单中，且先提供引用证据、迁移表和回滚方案。
2. **兼容性边界**：现有 CLI、四路由（Generate / Create Template / Fill / Enhance）、项目目录结构、PPTX 产物契约、质量门行为一律保持兼容。
3. **门禁纪律**：`scripts/` 或 `workflows/` 任何修改前后必须跑 `smoke_check.py`（完整模式），失败或新增 skip 必须解释。
4. **不改入口脚本结构**：81 个顶层入口不合并、不移动，除非先提供「消费者 × 符号」矩阵与回滚方案。
5. **`attribution_guard.py` 门禁**：新增/改名关键入口脚本后必须同步 `_REQUIRED_GATE_FILES` 清单，并运行 guard 验证。
6. **链接纪律**：整理批次不得新增断链；修改 workflow 引用时按「自内向外」顺序重写，并跑全仓链接校验。
7. **临时目录纪律**：实验数据只放 `.tmp/` / `.codex-tmp/`；需要 PPT 项目结构的实验用 `projects/_smoke_*` / `_tmp_*` / `_agent_*` 前缀，结束前停服务并清理。
8. **`.align` 更新独立获批**：对 `.align/spec.md` 等过期事实只做差异报告，更新必须作为独立、获批的后续变更。
9. **性能纪律**：一次只改一个性能变量，记录前后指标/环境/fixture/回归；未经用户确认不得宣称达到性能目标。
10. **文档纪律**：所有脚本/工作流修改记入 `docs/change-log.md`；踩坑沉淀到 `.align/lessons.md`；审计/计划文档按 `docs/rules/documentation-style.md` 标注状态与权威性。

## 6. 执行策略（分阶段）

### Phase 0 — 只读盘点（✅ 已完成 2026-08-03）

- 读取 `.align` 三件套、`AGENTS.md`、`SKILL.md`、`routing.md`、`generate-pptx.md`、`.gitignore`、CI/Pages 配置。
- 建立 tracked / untracked / ignored / public / runtime-state 分类（实测：14,534 / 0 / 9,663）。
- 统计每顶层目录文件数、体积、类型、最大文件、重复哈希（详见 D2 §1）。
- 映射脚本入口、workflow、reference、template、config 职责与引用关系（81 入口 0 孤儿）。
- 检查 Markdown 链接（0 断链 / 8 占位）、路线图状态、`.align` 事实漂移、旧入口与兼容层。
- 原始测量数据保存在 `.tmp/inventory_scan.json` 等（gitignored，见 D2 附录）。

### Phase 1 — 事实源与边界收敛（✅ 已完成 2026-08-03）

- 权威层级矩阵：`AGENTS.md → SKILL.md → workflows → references → docs summaries → plans/audits`（D2 §2）。
- 每目录标注 owner、可修改、公开、可删除、依赖方、回滚方式（D2 §3）。
- 候选冗余 / 疑似死文件 / 旧路线图 / 重复资源清单（D2 §4），**不删除、不移动、不重命名**。
- `.align` 过期事实差异报告（D2 §5），更新留待独立获批变更。

### Phase 2 — 低风险整理（⏳ 仅在本契约审核后执行）

- 优先：索引、文档导航、状态标记、入口说明、重复引用。
- 候选批次（来自 D2 §4/§5，每批独立审批）：
  - `plans/followup-migration-roadmap.md` 标记为已完成/归档（Phase 2-6 已执行完毕）；
  - `pptx_animations.py` 与 `native_pptx_animations.py` 同内容副本（md5 相同）的导入面核验与合并评估（需先出消费者清单）；
  - `.align/spec.md` 事实刷新（独立获批项）；
  - 其他 D2 清单项。
- 每批：修改前 smoke → 修改 → 修改后 smoke → 更新 `docs/change-log.md`。

### Phase 3 — 基于证据的性能优化（⏳）

- 先建立基线：冷/暖启动、导入、目录扫描、Dashboard 启动、质量检查、代表性导出流程的 p50/p95（≥10 次采样）。已记录的粗基线（单次测量，非 p50/p95）：`svg_to_pptx` 冷导入 0.09s、`svg_quality` 0.06s、`dashboard.server` 0.40s、`confirm_ui.server` 0.50s、全仓 walk 0.33s；完整 smoke 一次约 3 分钟。
- 只优化被 profiling 证明的瓶颈（重复扫描 / 重复解析 / 重复上下文读取 / 非必要 eager import / 重复索引加载）。
- 手段优先：缓存、懒加载、索引复用、路由级上下文裁剪；禁止无证据抽象。
- 目标阈值在基线报告后单独与用户确认，不得自行臆定。

### Phase 4 — 产物治理（⏳ 另立审批）

- `projects/`：active / archive / disposable 分类 + 生命周期与归档规则；删除仅限用户明确批准且具备清单与回滚副本。
- `examples/`：默认保留为公开 CI/Pages 回归基线；移出大型示例或改造 Pages 必须单独设计发布链路、迁移清单和回滚步骤。
- 候选（仅列出，不执行）：`projects/backup/` 多版本快照（march7th_hsr 512 MB / deepseek_evolution 175 MB / meditation 154 MB 等，共约 1 GB 级重复）、`.codex/` 261 MB 工具状态（gitignored，需确认是否可清）。

## 7. 验收标准

1. 盘点报告能对账顶层目录、tracked/ignored 状态、文件数和体积（D2 已满足：所有数字与 git/文件系统实测一致）。
2. 所有结论有路径、命令或文件证据；无法确认的内容标注 `[待验证]`。
3. Markdown 链接、路由表、脚本入口、关键产物契约无新增断裂（基线：0 断链；路由表逐行目标文件均存在）。
4. 初始 smoke 基线完整记录（158/0/4 完整模式、78/0/3 `--skip-help`）；修改后不得出现未解释的失败或新增跳过。
5. 代表性 `examples/` 通过 SVG 质量检查与 E2E 验证（CI 三 job 的本地等价物）。
6. 性能优化提供同一 fixture 的前后 p50/p95 数据，且无关键工作流回归。
7. 第一阶段无删除/移动/重命名历史产物，无 commit / push / 部署，无有成本外部 API 调用。
8. 新增依赖说明必要性；可选 Provider（image / tts / vision 后端）继续懒加载。
9. Agent 完成后输出：修改范围、未修改范围、剩余风险、可沉淀规则、下一阶段建议。

## 8. 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| `.align/spec.md` 事实过期（「无 CI」等）被后续模型当作事实 | 中 | 差异报告先行（D2 §5）；更新独立获批 |
| `followup-migration-roadmap.md` 计划形态误导后续执行 | 中 | Phase 2 优先归档标记 |
| 重复哈希清理误伤 examples↔projects 同源资产 | 高 | examples 是公开回归基线，清理只允许在 projects/ 侧（Phase 4 独立审批） |
| 性能优化引入无证据抽象或破坏质量门 | 中 | 一次一变量 + 前后 p50/p95 + smoke 回归 |
| 整理批次引入断链（链接纪律失效） | 中 | 每批全仓链接校验 + 路由表逐行核验 |
| `projects/` 被误当作临时区 | 中 | 遵循 agent-governance §5：`_smoke_*` 前缀 + 结束清理 |

## 9. 沉淀规则

- 每阶段结束：`docs/change-log.md` 追加（脚本/工作流变更）；`.align/lessons.md` 沉淀踩坑/纠正/新约定；`_smoke_*` 清理；确认无残留服务进程。
- 审计/计划类文档（本契约、D2、既有 audits）不进入 change-log（既有惯例，见 D2 §9）。
- `.align/decisions.log.md`：高风险决策/架构决策/权限决策由沉淀门追加。
- 性能结论必须带环境、fixture、采样数；「宣称达到目标」需用户确认。

## 10. 下一阶段建议

### 10.1 Phase 2 首批 — 已执行（2026-08-03）

1. ✅ **归档 `plans/followup-migration-roadmap.md`**：头部已加「状态：已归档（2026-08-03）」标记，正文保留为执行记录；引用者均为记录性文本（`docs/change-log.md`、盘点报告、本契约），无运行时依赖。
2. ✅ **动画双文件导入面核验**（未删任何文件）：

| 模块 | md5 | 大小 | 消费点（import 语句） |
|---|---|---|---|
| `scripts/pptx_animations.py`（旧名） | `c6d7c928…` | 145,406 B | `svg_to_pptx/animation_config.py:13`（12 符号）、`svg_to_pptx/pptx_package/builder.py:41`（9 符号）、`svg_to_pptx/pptx_package/cli.py:29`（4 符号） |
| `scripts/native_pptx_animations.py`（新名） | 同上（内容相同） | 145,406 B | `native_enhance_pptx_core.py:51`（2 符号）、`narration_sync.py:54`（4 符号）、`pptx_delivery_check.py:46`（3 符号） |

   符号并集约 15 个，双文件内容相同 → 纯路径替换即可（无符号缺失）。`attribution_guard._REQUIRED_GATE_FILES` 含 `native_pptx_animations.py`、不含 `pptx_animations.py`。

   **合并方案 A — 已执行（2026-08-03，用户批准）**：以 `pptx_animations.py` 为规范名（与上游同名、导出器侧 3 消费点零改动），删除 `native_pptx_animations.py`，native 侧 3 个 import 改为 `from pptx_animations import`，gate 清单 `native_pptx_animations.py` → `pptx_animations.py`，README / native-enhance-pptx 文档提及同步。验证：smoke 156 passed / 0 failed / 4 skipped（160 checks，80 scripts，-2 checks = 被删脚本的 import+help）；attribution_guard 通过；3 个改 import 脚本 import + --help 双 PASS。回滚：git revert。
   **方案 B**：保留新名删旧名 → 需改导出器侧 3 个 import（违背「导出器零改动」初衷），未采用。
   **方案 C**：维持双文件现状，未采用。

### 10.2 后续建议（按序，均需批准）

1. ✅ **`.align/spec.md` / `context.md` 事实刷新 — 已执行（2026-08-03，用户批准）**：spec.md 4 处（CI 存在性、测试语义、Python 3.12.13 实测、smoke 基线 78/0/3 + 158/0/4）、context.md 1 处（「仓库不包含自动化测试」→ 无 tests/ + CI 强制验证），均保持 `[原文]` 标注并加修订注记；另修正盘点报告 §5 一处张冠李戴（spec.md 原文无「38/41」基线数字）。align-check.sh 一键验证通过（smoke --skip-help PASS）。
2. ✅ **Phase 3 性能基线 — 已执行（2026-08-03）**：报告见 `docs/reviews/perf-baseline-2026-08.md`（p50/p95：smoke 完整 26.1s、导出 p50 3.7s、quality 冷 p50 1.33s/暖 0.37s、dashboard 启动 1.86s 等；原始数据 `.tmp/perf_baseline.json`）。**未做任何优化**；优化目标阈值待用户按报告确认。基线过程中发现 CI 风险（§10.3），优先于性能处理。
3. 🔄 **CI 风险处置（发现于 Phase 3 基线）**：✅ 选项 A 已执行（模板 `- mode: flat` bug 修复 + 29 个 legacy spec_lock 回填，5/29 变绿）；⏳ 24 个仍红示例按 A-E 类分类（清单见 `docs/reviews/perf-baseline-2026-08.md` §3.3），B-F 类修复或 CI 门禁调整待用户决策；pritzker 特例（回填 flat 与 page_layouts 节冲突）待单独判断。
4. ✅ **Phase 4 产物治理 — 已执行（2026-08-03，用户批准）**：`projects/README.md` 新增 Lifecycle Governance（active/archive/disposable 三档 + backup/dashboard/validation 可清理清单 + artifacts_index.json 搜找说明）；清理 34 个旧 backup 快照（~0.9 GB，project_manager 官方标注 safe to delete old timestamps）+ `.codex/dashboard-check`/`dashboard-cdp` 缓存（256 MB，保留 config.toml）→ projects/ 5.73 GB → 4.8 GB、.codex 261 MB → 5 KB。
5. ✅ **Dashboard 重定位为产物展台 — 已执行（2026-08-03，用户批准）**：定位 = 产物在线观看平台（制作 PPT 思路与相关产物集中展示；Confirm UI 不动）。实施：默认路由改产物展台；四阶段导航（制作思路/设计契约/生成页面/导出成品 + 计数 + 点击过滤）；新增 research 类型（`_research/`、research_report、content_selection/detailed_outline/visual_strategy）；`/api/artifacts` 响应写 `<project>/dashboard/artifacts_index.json`（本地 grep/jq 搜找）。浏览器实测通过；smoke 77/0/3。
