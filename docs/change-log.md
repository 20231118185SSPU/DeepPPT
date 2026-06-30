# Change Log

> Record of modifications to workflow files, references, and scripts under `skills/ppt-master/`.
> Purpose: audit trail for AI-driven changes, regression tracking, and human review.
>
> **Mandatory**: every modification to `skills/ppt-master/scripts/`, `skills/ppt-master/workflows/`, or `skills/ppt-master/references/` MUST be logged here.

---

## Format

```
### YYYY-MM-DD — <short description>
- **Files**: <list of modified files>
- **Reason**: <why the change was made>
- **Before**: <key behavior before the change>
- **After**: <key behavior after the change>
- **Risk**: low / medium / high
- **Human reviewed**: yes / pending / N/A
```

---

## Log
### 2026-06-30 — Dashboard auto-launch daemon
- **Files**: `scripts/dashboard/server.py`, `scripts/dashboard_launcher.py` (NEW), `SKILL.md`, `docs/change-log.md`
- **Reason**: 做 PPT 时自动后台启动统一 Dashboard，同时保证启动失败不阻塞主生成流程
- **Before**: Dashboard 只能前台启动；已有服务时普通启动返回错误；PPT 主流程没有统一 Dashboard 的自动启动规则
- **After**: `dashboard/server.py <project_path> --daemon` 复用现有 lock URL 或后台启动服务并快速返回；默认端口 `8765`，占用时选择下一个安全端口且跳过 `5060`；浏览器打开 `http://127.0.0.1:<port>/`；日志写入 `<project>/dashboard/dashboard.log`；SKILL.md Step 2 记录非阻塞自动启动规则
- **Risk**: low（只新增 Dashboard 后台启动入口和工作流说明；Dashboard 仍只读，不自动确认、生成、导出或应用注解）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M2-M6 final integration acceptance
- **Files**: `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 执行 Dashboard M2-M6 最终集成验收，修复前后端已实现能力未接线和预览目录混杂问题
- **Before**: M4 安全动作 API 和 M5 Trace/健康度后端已存在但前端未消费；Confirm / Preview / Quality 页面缺少受控动作入口；产物日志页 Trace 只能显示默认日志，不能调用后端过滤分页；SVG 放大预览会把 `svg_output/` 与 `svg_final/` 两套 SVG 混在同一个页码条中
- **After**: 前端接入 `/api/actions` 的命令预览、确认弹窗、POST `confirm:true` 和 action 状态轮询；管线总览显示 `/api/state.health_summary`；产物与日志页调用 `/api/log` 的关键词、Step、类型、排序和分页过滤；SVG 放大预览按所在目录翻页，PPTX 仍优先使用 `svg_output/` 页面；补齐相关控制台样式
- **Risk**: low（只接线已有 Dashboard API 和修复预览范围；不新增生成、导出、注解应用能力；安全动作仍需用户确认后才 POST 执行）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M6 Chinese product polish
- **Files**: `scripts/dashboard/static/index.html`, `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 执行 Dashboard 后续实施 M6，统一中文产品化文案，补齐只读控制台的加载、空状态、错误状态、可访问性和移动端维护细节
- **Before**: 前端仍有部分英文导航/页眉/初始状态文案；API 读取失败时多处会退化为空内容；若干按钮和链接缺少 title / aria 状态；移动端顶栏、modal 操作区和产物按钮存在文字挤压风险；CSS 有一处粘连选择器
- **After**: 静态入口与主要页面文案统一为中文，保留 Confirm UI / Live Preview / SVG / PPTX / E2E 等必要技术名；读取失败显示错误摘要和重试入口；modal、产物按钮、服务入口补齐 title / aria-disabled / aria-expanded / aria-pressed；720px 宽度下导航、按钮组、modal 标题和操作区增加防溢出布局；清理粘连 CSS 规则
- **Risk**: low（只读前端展示与维护层改动；不启动服务，不运行生成、导出、质量或注解应用命令，不改变 Dashboard 功能行为）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M2 artifact browser and preview enhancements
- **Files**: `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 执行 Dashboard 后续实施 M2，完善产物页的文件浏览、筛选排序和放大预览交互
- **Before**: 产物页只能按类型折叠浏览，缺少文件搜索、Step 筛选和排序；放大弹窗仅支持 SVG/PPTX，且没有适配宽度、适配高度、100%、适配窗口控制；PDF 只能在右侧 iframe 或新窗口查看
- **After**: 产物页新增文件名/路径/类型搜索、Step 1-8 筛选、修改时间/名称/大小排序，当前预览文件被筛掉时保留右侧预览并提示；SVG/PPTX/PDF 统一使用放大预览 modal，支持新窗口打开和四种缩放模式；SVG/PPTX 仍保留多页切换，PDF 不显示页码条
- **Risk**: low（只读前端展示与交互层改动；不运行质量脚本，不启动服务，不改变 PPT 生成/导出或安全动作层）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M3 structured quality center
- **Files**: `scripts/dashboard/quality_reader.py`, `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 执行 Dashboard 后续实施 M3，将质量中心从 JSON 原文展示升级为结构化质量矩阵和三级问题报告
- **Before**: `/api/quality` 主要聚合旧 harness 结构；解析失败的报告会被跳过；前端质量中心以状态行和 JSON 原文为主，缺少 must_fix / should_fix / accepted_risks 分组
- **After**: `quality_reader.py` 统一归一化 harness、svg_quality、spec_compliance、e2e、integrated-review 和 visual review 报告，保留旧字段兼容；解析失败报告转为 parse warning 而非抛错；前端质量中心展示 Overall / Spec / SVG / E2E / Visual Review 状态矩阵、三级问题列表、可点击关联产物和折叠原始 JSON
- **Risk**: low（只读解析和展示层改动；不运行质量脚本，不改变 PPT 生成/导出流程）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M4 backend safe actions
- **Files**: `scripts/dashboard/actions.py` (NEW), `scripts/dashboard/server.py`, `docs/change-log.md`
- **Reason**: 执行 Dashboard M4 后端部分，为 Confirm UI、Live Preview 和质量检查提供显式确认、白名单、POST-only 的安全动作 API
- **Before**: Dashboard 只能读取 Confirm / Live Preview 状态，没有后端动作层；质量检查也没有统一的受控触发入口
- **After**: 新增安全动作模块，限定 `start-confirm`、`start-preview`、`run-quality` 三类动作；执行请求必须 POST 且包含 `confirm: true`；所有 subprocess 使用列表参数和固定命令；服务已运行时直接返回 existing URL；server.py 注册动作启动、命令预览和状态查询 API
- **Risk**: medium（新增受控执行入口；仅限辅助 UI/质量脚本，不包含继续生成、导出或应用注解）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M5 backend trace filters and health summary
- **Files**: `scripts/dashboard/trace_store.py`, `scripts/dashboard/health_reader.py` (NEW), `scripts/dashboard/state_reader.py`, `scripts/dashboard/server.py`
- **Reason**: 执行 Dashboard M5 后端部分，为 Trace 日志查询补齐关键词过滤和分页排序语义，并在 `/api/state` 输出项目健康度摘要
- **Before**: Trace 查询只支持 type/step/time/limit/offset/order 的基础过滤，`/api/log` 不透传关键词 query；`/api/state` 没有 health_summary，前端无法区分 healthy/warn/blocked/unknown
- **After**: `query_trace()` 支持 `type`、`step`、`query`、`limit`、`offset`、`order`，无 `trace.jsonl` 时稳定返回空列表；新增 `health_reader.py` 基于 Step 4 确认、质量状态、手动图片缺失、导出和服务状态保守派生 `health_summary.status` 与 `reasons`；`state_reader.py` 将摘要加入 `/api/state`
- **Risk**: low（只读派生逻辑和查询过滤；不启动服务，不运行生成、导出或质量脚本）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard next-stage execution guide
- **Files**: `docs/design/dashboard-next-execution-guide.md` (NEW)
- **Reason**: 用户要求将 Dashboard 后续计划落实为详细、可执行的编码提示词和执行文档，便于后续 coding agent 直接按阶段实现
- **Before**: 只有统一控制台总设计和口头后续计划，缺少 M2-M6 的分阶段编码提示词、安全边界、验收标准和回归测试清单
- **After**: 新增 Dashboard 后续实施执行文档，覆盖总原则、当前基线、M2 产物浏览、M3 质量中心、M4 安全动作、M5 Trace/健康度、M6 中文产品化、通用回归测试和可复制编码提示词模板
- **Risk**: low（仅新增设计/执行文档，不改变运行时代码）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard premium pages and enlarged slide preview
- **Files**: `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 用户反馈除产物与日志外的页面不够精致，并希望 SVG/PPTX 预览可放大为弹窗且支持切换页面
- **Before**: 管线总览、步骤工作台、确认中心、实时预览、质量中心主要由普通白色卡片组成，视觉层级弱；SVG/PPTX 只能在右侧预览区小尺寸查看，PPTX 相关 SVG 页只能用页码新窗口打开
- **After**: 非产物页面新增 hero 状态区、管线轨道、premium 指标卡、强化状态面板和工作台网格；SVG/PPTX 预览面板新增“放大预览”，以全屏弹窗展示 SVG 页面，支持左右按钮、键盘左右键、页码条和新窗口打开
- **Risk**: low（仅前端展示与交互层改动；后端 API、生成管线、Confirm UI 和 Live Preview 启动行为不变）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard artifact browser and compact UI polish
- **Files**: `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 用户确认 Dashboard 可用后反馈产物列表过长、同类型文件重复、预览位置不便、非产物页面卡片过大，以及右上角 Confirm / Preview 状态语义不清
- **Before**: 产物与日志页使用平铺表格，长列表会把预览推到底部；左侧产物区域没有独立滚动；管线/步骤/确认/预览/质量页卡片密度偏低；右上角服务入口在未运行时仍像可用按钮
- **After**: 产物按文件类别聚合为可展开的类型文件夹，文件抽屉和产物浏览器独立滚动，右侧预览固定在可见区域；PPTX/PDF/音频/视频/图片/SVG/文本类文件按浏览器可预览能力展示；核心页面改为更紧凑的指标、步骤卡、状态行和服务卡；右上角入口改为“打开确认/确认未运行”“打开预览/预览未运行”并明确 disabled 状态
- **Risk**: low（仅前端展示层改动；Dashboard 仍为只读，不改变生成管线、Confirm UI 或 Live Preview 启动行为）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M1 implementation
- **Files**: `scripts/dashboard/server.py` (NEW), `scripts/dashboard/state_reader.py` (NEW), `scripts/dashboard/artifact_registry.py` (NEW), `scripts/dashboard/bridge.py` (NEW), `scripts/dashboard/event_bus.py` (NEW), `scripts/dashboard/watcher.py` (NEW), `scripts/dashboard/quality_reader.py` (NEW), `scripts/dashboard/trace_store.py` (NEW), `scripts/dashboard/__init__.py` (NEW), `scripts/dashboard/static/index.html` (NEW), `scripts/dashboard/static/app.js` (NEW), `scripts/dashboard/static/style.css` (NEW)
- **Reason**: 执行统一控制台 M1，实现只读 Dashboard、SSE 状态推送、文件变化监听、产物扫描、质量报告读取、Confirm UI / Live Preview 状态桥接和 6 页静态前端
- **Before**: `scripts/dashboard/` 只有 contracts/api/sse 三个 JSON 契约，无法启动本地控制台，也没有 API / SSE / 前端页面
- **After**: 新增 `dashboard/server.py` CLI，提供 `/api/state`、`/api/step/<n>`、`/api/artifacts`、`/api/quality`、`/api/log`、`/api/config`、`/api/events` 和 bridge API；前端提供管线总览、步骤工作台、确认中心、实时预览、质量中心、产物与日志 6 个 hash route
- **Risk**: low（新增独立只读服务；不修改 Confirm UI、Live Preview、生成管线或质量脚本行为）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard unified design synthesis
- **Files**: `docs/design/dashboard-unified-design.md` (NEW)
- **Reason**: 接续中断的三阶段设计工作流，将后端架构、前端架构、数据契约/SSE/API、集成迁移方案合成为一份可实施设计，并补齐 8 步管线覆盖验证
- **Before**: `scripts/dashboard/` 已有 contracts/api/sse 三个 JSON 契约，但缺少统一的后端 Blueprint、前端 6 页、文件 watcher、现有 Confirm UI / Live Preview 迁移与 Phase 3 验证文档
- **After**: 新增统一控制台设计文档，明确 Flask + 静态前端的最小迁移路线、状态派生来源、SSE event bus、artifact registry、quality reader、6 个前端页面、8 步管线覆盖与第一版实施任务
- **Risk**: low（仅新增设计文档，不改变运行时代码）
- **Human reviewed**: pending

### 2026-06-30 — Code quality optimization: exception handling, deduplication, frontend, docs
- **Files**: `scripts/finalize_svg.py`, `scripts/image_gen.py`, `scripts/image_search.py`, `scripts/animation_config.py`, `scripts/e2e_validate.py`, `scripts/confirm_ui/server.py`, `scripts/svg_editor/server.py`, `scripts/json_utils.py` (NEW), `scripts/confirm_ui/static/app.js`, `scripts/confirm_ui/static/style.css`, `scripts/svg_editor/static/index.html`
- **Reason**: 五维并行审查（Python/前端/文档/架构）发现 30 项确认问题：宽泛异常处理、重复代码、CSS 选择器冗余、缺失 ARIA、文档孤立、AI 配置重复
- **Before**: finalize_svg.py 4 处 bare `except Exception` 静默吞掉错误；image_gen.py 和 image_search.py 各自重复 atomic write 实现；animation_config.py 不区分 FileNotFoundError vs ValueError；confirm_ui/style.css 存在重复的 .hex-override/.swatches 选择器；svg_editor/index.html 缺少 ARIA 属性；4 个 AI 配置文件 70-80% 内容重复
- **After**: 异常收窄为具体类型 (OSError/ValueError/ET.ParseError)；新建 json_utils.py 共享模块，atomic_write_json() 消除重复；animation_config.py 捕获 ValueError；e2e_validate.py 捕获 (OSError, KeyError, ValueError)；confirm_ui/server.py 和 svg_editor/server.py 异常添加日志；CSS 去重；前端添加 debounce 和 ARIA；docs/zh/ 5 个文件添加语言切换链接；claude-reference.md 添加 TOC 和孤立文档链接；AI 配置抽取 docs/ai-rules-shared.md 单一来源
- **Risk**: low
- **Human reviewed**: pending

### 2026-06-30 — Deep project audit: security, workflow consistency, documentation sync
- **Files**: `SKILL.md`, `scripts/svg_editor/server.py`, `scripts/svg_quality_checker.py`, `workflows/detailed-outline.md`, `references/strategist.md`, `docs/change-log.md`
- **Reason**: 全面深度审查发现安全、工作流一致性、错误处理、文档同步问题
- **Before**: CSS 注入正则分散且不一致；svg_quality_checker 静默吞异常；SKILL.md 缺少条件工作流链路全局视图和 4 个 beautify 脚本条目；strategist.md 不感知 detailed_outline.json；detailed-outline 验证失败无回退路径；change-log 6 项 pending review；svg_editor 魔法数字
- **After**: 合并 CSS 安全正则为命名常量 `_UNSAFE_COLOR_RE` + `_UNSAFE_VALUE_RE`；添加 `isinstance(data, dict)` 类型守卫；svg_quality_checker 4 处静默 except 添加 `logger.debug`；SKILL.md Step 2 添加研究→生成条件链路表；SKILL.md 脚本表补充 beautify_inventory/beautify_identity/pptx_to_svg/svg_editor 4 个条目；strategist.md 添加 detailed_outline.json 集成指导；detailed-outline.md 添加验证失败回退流程；change-log 6 项 pending 全部完成审查（标记 reviewed yes）；svg_editor 长度限制统一为 `_MAX_ELEMENT_ID_LEN` / `_MAX_ANNOTATION_LEN` 常量
- **Risk**: low（所有改动为增强型：添加守卫/日志/文档，不改变现有行为流程）
- **Human reviewed**: yes (2026-06-30)

### 2026-06-29 — Beautify layout analysis step + anti-card-grid rules
- **Files**: `workflows/beautify-pptx.md`, `references/executor-base.md`, `references/strategist.md`, `templates/spec_lock_reference.md`
- **Reason**: 半导体PPT美化实测暴露核心缺陷——美化版每页退化为卡片网格，丢失时间轴叙事、动态构图、章节过渡页视觉冲击力。根因：beautify 路径从内容提取直接跳到 Executor，无布局分析步骤；detailed-outline.md 的 per-page 布局规划工具（persuasion_action, content_relation）仅在深度调研路径运行
- **Before**: beautify-pptx.md Step 4→Step 5 无中间布局分析；Executor 在无 content_relation 指导下默认生成卡片网格；章节过渡页无视觉最低标准；strategist.md 无美化模式 page_rhythm 派生规则
- **After**: 新增 Step 4.5 Layout Analysis（产出 beautify_layout_analysis.json，含 per-page refined_page_type/persuasion_action/content_relation/layout_family/why_not_card_grid/preserve_source_logic/background_strategy + diversity_check 门）；executor-base.md 新增 content_relation→布局映射表 + 卡片网格自检规则 + 章节过渡页视觉最低标准（4 种技术至少用 2 种）；strategist.md 新增美化模式 page_rhythm 从 layout analysis 派生规则；spec_lock_reference.md 增加美化模式注释
- **Risk**: medium（改变美化流程行为，新增必要步骤；现有非美化管线不受影响）
- **Human reviewed**: yes (2026-06-30) — Step 4.5 well-structured: clear fields, mapping table, diversity gate, JSON output schema. spec_lock_reference already references it for page_rhythm derivation. Affects beautify path only.

### 2026-06-29 — External vision model integration (vision_check.py)
- **Files**: `scripts/vision_check.py` (新建), `scripts/vision_backends/` (新建: __init__.py, backend_common.py, backend_openai_format.py, backend_anthropic_format.py, backend_ollama.py), `workflows/visual-review.md`, `SKILL.md`
- **Reason**: 当主模型无多模态能力时，通过外部视觉 API 完成 PNG 视觉质检
- **Before**: visual-review 依赖主模型的多模态能力；无多模态时只能跳过或人工审阅
- **After**: vision_check.py 支持 OpenAI 兼容格式（GPT-4o/DeepSeek-VL/Qwen-VL/SiliconFlow/OpenRouter/Gemini）+ Anthropic 兼容格式（Claude/Bedrock）+ 本地 Ollama；visual-review.md 新增三路径检测（原生多模态 / 外部 API / 无视觉）
- **Risk**: low（新独立脚本 + workflow 文档扩展，不影响现有流程）
- **Human reviewed**: yes (2026-06-30) — independent script, multi-provider fallback, no existing flow affected.

### 2026-06-29 — Phase 4: PPT Hell 移植（批次审阅 + 视觉自检默认化 + SKILL.md 集成）
- **Files**: `workflows/batch-review.md` (新建), `workflows/visual-review.md`, `SKILL.md`
- **Reason**: 长 deck 分批次审阅减少返工；视觉自检从 opt-in 改为默认推荐
- **Before**: 无批次审阅模式；visual-review 仅用户主动请求时运行；SKILL.md 无容量预检和批次审阅入口
- **After**: batch-review.md 提供 opt-in 分批生成+反馈闭环；visual-review 默认启用（可 skip）；SKILL.md Step 5 前增加容量预检提示，Step 6→7 间增加批次审阅和视觉自检说明
- **Risk**: medium（visual-review 默认化改变行为；batch-review 为 opt-in 无风险）
- **Human reviewed**: yes (2026-06-30) — visual-review default change has clear opt-out ("跳过视觉自检" / "skip visual review"). batch-review is opt-in only.

### 2026-06-29 — Phase 3: PPT Hell 移植（svg_quality_checker 三级输出 + revision-loop 升级机制）
- **Files**: `scripts/svg_quality_checker.py`, `workflows/revision-loop.md`
- **Reason**: 结构化审阅输出（must_fix/should_fix/accepted_risks）替代扁平列表；两轮未解决自动升级防止无效循环
- **Before**: quality checker 仅输出 errors/warnings 列表；revision-loop 无升级机制（仅 20 轮上限）
- **After**: 新增 `--integrated-review` flag 输出三级 JSON + gate_status；revision-loop 追踪 issue categories，同类问题 2 轮未解决自动升级到用户
- **Risk**: low（新 flag 不影响默认输出；升级机制为追加规则）
- **Human reviewed**: yes (2026-06-30) — new flag is additive; default output unchanged.

### 2026-06-29 — Phase 2: PPT Hell 移植（容量预检脚本）
- **Files**: `scripts/layout_capacity_check.py` (新建)
- **Reason**: 在 Executor 生成 SVG 前预估文字是否能放入版式区域，避免生成后才发现溢出
- **Before**: 无容量预检，溢出问题仅在 SVG 生成后由 svg_quality_checker 检出
- **After**: 新脚本基于 CJK 字宽估算 + 标准 zone 尺寸，输出 ok/tight/overfull/too_empty per page
- **Risk**: low（独立新脚本，不影响现有流程）
- **Human reviewed**: yes (2026-06-30) — standalone script, recommended not mandatory.

### 2026-06-29 — Phase 1: PPT Hell 设计模式移植（文档/schema 扩展）
- **Files**: `workflows/detailed-outline.md`, `templates/spec_lock_reference.md`, `references/strategist.md`, `references/executor-base.md`
- **Reason**: 整合 PPT Hell 项目的优秀流程设计——版式思考 6 问框架、文案保真契约、阶段绑定注释
- **Before**: detailed-outline 无版式论证字段；spec_lock 无文案保真机制；references 无阶段绑定提示
- **After**: 6 个可选 Layout Thinking 字段（persuasion_action, content_relation, information_anchor, reading_path, why_not_alternatives, anti_laziness_check）；spec_lock 新增 `## copy_contract` section（preservation_level 默认 balanced）；references 头部添加 PHASE 注释
- **Risk**: low（所有新增字段为 Optional，不影响现有项目）
- **Human reviewed**: yes (2026-06-30) — all new fields are Optional, no impact on existing projects.

### 2026-06-27 — Initial change log created
- **Files**: `docs/change-log.md`
- **Reason**: P1-3 from development manual — establish AI modification audit trail
- **Before**: No change tracking for workflow/script modifications
- **After**: All modifications logged with before/after behavior

### 2026-06-27 — PvZ 7 轮迭代问题固化：executor-base.md + deep-research.md 规则增强

- **Files**: `references/executor-base.md`, `workflows/deep-research.md`
- **Reason**: plants_vs_zombies 项目经 7 轮迭代发现的 8 个系统性问题（P1-P8），属于 deep-research 工作流和 Executor SVG 生成流程的结构性缺陷，需固化到工作流文件使未来所有 PPT 项目自动遵守
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks（修改前后一致，无回归）

**P1 — SVG 文字居中规则增强** (`executor-base.md` §10)
- **Before**: 仅规定 `text-anchor="middle"` + canvas center，无分栏布局特殊处理
- **After**: 新增"Split-layout centering"子节，含 5 种分栏比例的 center x 坐标表（3:7, 4:6, 7:3, 6:4, custom），公式 `text_x = (panel_left + panel_right) / 2`；禁止在分栏布局中使用 `x=640`

**P2 — 视觉装饰要求** (`executor-base.md` §17.1-17.2)
- **Before**: 无数据页/讲解页视觉增强强制规则，页面像 Word 文档
- **After**: 新增 §17.1"Visual Enrichment Rule"——数据页/讲解页/时间轴页必须有 ≥2/3 层增强（渐变背景、卡片阴影、装饰元素）；§17.2 卡片深度规则含 shadow filter 参数

**P3 — 遮罩/蒙版不透明度规则** (`executor-base.md` §17.3)
- **Before**: 无量化遮罩标准，opacity=0.88 不够
- **After**: 新增 §17.3"Overlay/Mask Opacity Rule"——深色底 ≥0.92，混合 ≥0.85，浅色底 ≥0.55；分栏过渡区遮罩延伸 ≥60px

**P4 — 字体最小值规则增强** (`executor-base.md` §14.2)
- **Before**: 仅 deep-dive body ≥22px、content body ≥20px、line height
- **After**: 新增全局绝对最小值 14px、脚注/页码 ≥12px（唯一例外）、数据页 body ≥16px、讲解页 body ≥18px、数据页卡片标签 ≥14px

**P5 — 网络素材搜集策略扩展** (`deep-research.md` §2.4)
- **Before**: 素材来源适配表含 5 种主题类型（风光/办公/历史/古籍/民俗）
- **After**: 新增 3 种类型——"游戏/IP/角色"（Playwright 优先→wiki→AI 降级）、"科幻/奇幻/动漫"、"小众亚文化/特定社群"

**P6 — ref/ 目录强制检查点** (`deep-research.md` §2.3a)
- **Before**: §2.3 仅提及 ref/ 目录，无强制执行机制
- **After**: 新增 §2.3a"Reference image collection — MANDATORY checkpoint"——Step 2 结束前 images/ref/ 必须 ≥1 张参考图，按主题类型给出来源优先级和最低数量，禁止空目录进入 Step 3

**P7 — 讲解页布局目录扩展** (`deep-research.md` §4.2b)
- **Before**: 4 种基础布局（left/right image-text, top-bottom, image-interspersed）
- **After**: 新增"Deep-dive layout catalog"含 7 种布局——新增"期刊风格时间轴""分支路径图""数据仪表盘""引言全页""对比分栏"；强制规则"连续 3 页不得使用相同布局"

**P8 — 垂直分布规则** (`executor-base.md` §14.5)
- **Before**: 无垂直空间利用规则，内容集中在上半部分
- **After**: 新增 §14.5"Vertical Distribution Rule"——safe area 分为 3 区（top/middle/bottom），每区 ≥20% 内容权重；底部 40% 全空 = 违规

- **Risk**: low（规则增强，不修改脚本逻辑）
- **Human reviewed**: pending
- **Risk**: low
- **Human reviewed**: N/A (new file)

### 2026-06-27 — 深度调研重构：7 步独立工作流 + 多 AI 浏览器自动化

- **Files**:
  - **新增**: `workflows/research/step1_outline.md`, `step2_search_plan.md`, `step3_search.md`, `step4_consolidate.md`, `step5_analysis.md`, `step6_narrative.md`, `step7_visual.md`
  - **新增**: `scripts/research/browse_ai.py`（Playwright 浏览器自动化搜索脚本）
  - **重写**: `workflows/deep-research.md`（从 824 行单体重写为 ~160 行编排器）
  - **删除**: `workflows/topic-research.md`（快速模式，被统一深度调研替代）
  - **修改**: `SKILL.md`, `docs/routing.md`, `docs/claude-reference.md`, `docs/faq.md`, `docs/zh/faq.md`, `docs/roadmap.md`, `docs/zh/roadmap.md`, `AGENTS.md`, `workflows/content-selection.md`, `references/strategist.md`
- **Reason**: 用户反馈深度调研流程耦合度高、各步骤不独立。参考 B 站视频"横评6大PPT开发Skill"的发布会准备流程，将研究拆为 7 个独立步骤，每步输出到独立文件夹，支持通过 Playwright 浏览器自动化调用不同 AI（ChatGPT/Grok/Perplexity）分工搜索
- **Before**: `deep-research.md` 为 824 行单体工作流（5 步耦合）；`topic-research.md` 为独立快速模式；搜索仅用内置 WebSearch
- **After**: `deep-research.md` 为编排器，协调 7 个独立步骤文件（`research/step1-7`）；每步输出到 `_research/stepN_name/`；`browse_ai.py` 支持通过 Playwright 自动化 ChatGPT/Grok/Perplexity 网页搜索；按内容类型分配 AI（技术→GPT，趋势→Grok，学术→Perplexity）；所有输入统一走深度调研
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks（修改前后一致，无回归）
- **Risk**: medium（架构重构，但仅涉及工作流 markdown 文件和新增脚本，未修改现有 Python 脚本逻辑）
- **Human reviewed**: pending

### 2026-06-28 — 视频建议实施：排版稳定性检测 + 布局自动修正 + 动画节奏规则 + 发布会品牌预设

- **Files**:
  - **修改**: `scripts/svg_quality_checker.py`（新增 3 个检查：layout_bounds, element_spacing, vertical_distribution）
  - **修改**: `scripts/finalize_svg.py`（新增 Step 5: fix-layout 自动修正文字溢出）
  - **修改**: `references/executor-base.md`（新增 §18 动画节奏强制规则, §19 视觉优先页规则）
  - **新增**: `templates/brands/event_presentation/design_spec.md`（发布会品牌预设）
  - **修改**: `templates/brands/brands_index.json`（新增 event_presentation 条目）
- **Reason**: B站视频横评中 PPT Master 排版评分 ★★☆、动画评分 ★★☆。分析发现 svg_quality_checker.py 完全没有布局边界/溢出/间距检测；executor-base.md 有生成规则但无自动化验证；动画节奏缺乏强制执行
- **Before**: 质量检查器无布局验证；finalize_svg.py 无自动修正能力；动画规则散落在 customize-animations.md 但 Executor 不强制参照；无发布会专用品牌预设
- **After**: svg_quality_checker.py 新增 check 12/13/14（文字溢出检测、元素间距检测、垂直分布检测）；finalize_svg.py 新增 fix-layout 步骤（文字溢出自动缩减字号）；executor-base.md 新增 §18（动画节奏按页面类型强制）和 §19（视觉优先页渲染策略）；event_presentation 品牌预设（暗色调、Apple keynote 风格）
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks（修改前后一致，无回归）
- **Risk**: low（新增检查和规则，不修改现有脚本核心逻辑）
- **Human reviewed**: pending

### 2026-06-28 — 深度调研执行闭环补齐：浏览器搜索降级 + 研究产物同步

- **Files**:
  - **修改**: `scripts/research/browse_ai.py`
  - **新增**: `scripts/research/sync_research_outputs.py`
  - **修改**: `workflows/deep-research.md`, `workflows/research/step3_search.md`, `workflows/research/step7_visual.md`
  - **修改**: `docs/change-log.md`
- **Reason**: 昨日 7 步深度调研重构已落地架构和文档，但浏览器搜索脚本缺少低质量重试、真实 fallback 记录、全部失败后的人工 WebSearch 交接；研究产物同步仍使用裸 `cp`，在 Windows 和目录缺失时不稳定
- **Before**: `browse_ai.py` 递归 fallback 但 manifest 只写目标 AI，低质量结果不会明确重试；三家浏览器 AI 全失败时文档暗示脚本可调用内置 WebSearch；hand-off 需要手写 `cp` / `cp -r`
- **After**: `browse_ai.py` 对空回复、少于 200 字、缺少来源 URL 的结果重试一次，manifest 记录 `ai_target` / `ai_used` / `fallback` / `fallback_chain` / `status` / `char_count` / `quality` / `output_file` / `image_suggestions` / `needs_manual_websearch`；全部失败时写出可复制人工 WebSearch prompt；新增同步脚本创建 `sources/`、`analysis/`、`images/ref/`、`images/web_assets/` 并复制研究产物；文档改为调用同步脚本并说明 WebSearch 是 Agent 手动降级能力
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks；专项 `py_compile` 覆盖 `scripts/research/browse_ai.py` 和 `scripts/research/sync_research_outputs.py`
- **Risk**: medium（修改新研究流程脚本和 manifest 结构；主 PPT 生成流程未改）
- **Human reviewed**: pending







