# 统一控制台技术设计文档

> 目标：把确认页、实时预览、质量检查、导出状态和项目产物统一到一个本地控制台中，同时不改变 PPT Master 的串行工作流、阻塞点和现有 CLI 行为。

## 1. 设计边界

### 1.1 控制台职责

| 职责 | 说明 |
|------|------|
| 状态可视化 | 展示 1-8 步管线状态、当前阻塞点、质量门、导出结果 |
| 事件推送 | 通过 SSE 推送状态变化、产物生成、质量检查、确认完成、错误 |
| 项目导航 | 聚合源文件、模板、图片、SVG、备注、导出文件、日志 |
| UI 整合 | 保留现有 Confirm UI 与 Live Preview 功能，在统一入口中进入 |
| 诊断辅助 | 展示质量报告、trace、脚本返回码和可恢复建议 |

### 1.2 控制台不做什么

| 非职责 | 原因 |
|--------|------|
| 不替代 AI 执行管线 | SKILL.md 仍是唯一工作流 authority |
| 不自动跨越 Step 4 阻塞确认 | Step 4 必须由用户明确确认 |
| 不生成 SVG 或设计内容 | Executor 仍由当前主 agent 顺序生成 |
| 不重写 Confirm UI / Live Preview 第一版 | 先聚合与桥接，避免破坏已验证交互 |
| 不引入数据库 | 状态从项目文件、锁文件、trace 和脚本输出派生 |

### 1.3 已有 Phase 1 产物

| 分支 | 已有文件 | 结论 |
|------|----------|------|
| 数据契约与事件 | `skills/ppt-master/scripts/dashboard/contracts.json` | 可作为状态模型主 schema |
| REST API | `skills/ppt-master/scripts/dashboard/api_contracts.json` | 覆盖状态、步骤、质量、产物、日志、配置、SSE |
| SSE 事件 | `skills/ppt-master/scripts/dashboard/sse_events.json` | 覆盖全量状态、进度、质量、产物、确认、错误、心跳 |
| 现有后端基础 | `confirm_ui/server.py`、`svg_editor/server.py`、`server_common.py` | Flask + 静态前端 + per-project lock 是最小迁移路径 |

---

## 2. 综合架构

### 2.1 总体结构

```
skills/ppt-master/scripts/dashboard/
├─ server.py                 # CLI 入口，创建 Flask app
├─ app_factory.py            # 注册 Blueprints、静态资源、生命周期
├─ state_reader.py           # 从项目文件派生 PipelineState
├─ artifact_registry.py      # 产物扫描、类型分类、元数据提取
├─ quality_reader.py         # 读取/归一化质量报告
├─ trace_store.py            # trace.jsonl 读写与查询
├─ watcher.py                # 轮询式文件 watcher + debounce
├─ event_bus.py              # SSE 客户端队列、事件缓存、重放
├─ bridge.py                 # Confirm UI / Live Preview 运行状态桥接
├─ contracts.json
├─ api_contracts.json
├─ sse_events.json
└─ static/
   ├─ index.html
   ├─ app.js
   └─ style.css
```

**默认技术栈**：沿用 Flask + 原生 HTML/CSS/JS。该仓库是工具包，不需要新增 React/Vite 等应用脚手架。

### 2.2 后端 Blueprints

| Blueprint | 路由 | 职责 |
|-----------|------|------|
| `ui_bp` | `/`、`/static/*` | 控制台单页入口 |
| `state_bp` | `/api/state`、`/api/step/<n>` | 管线状态与单步详情 |
| `quality_bp` | `/api/quality`、`/api/quality/<check>` | 质量门报告 |
| `artifact_bp` | `/api/artifacts`、`/api/artifacts/<type>` | 产物列表与过滤 |
| `log_bp` | `/api/log` | trace 查询、分页、过滤 |
| `events_bp` | `/api/events` | SSE 流、心跳、断线重放 |
| `bridge_bp` | `/api/bridges/confirm`、`/api/bridges/live-preview` | 读取现有 UI 运行状态与 URL |
| `config_bp` | `/api/config` | 项目配置、主题、catalog 摘要 |

### 2.3 状态来源

| 状态字段 | 来源 | 备注 |
|----------|------|------|
| `project_name` / `project_path` | CLI 参数和路径 | 不从文件名猜测业务语义 |
| `canvas_format` | `spec_lock.md`、project metadata、`confirm_ui/result.json` | 初始化前可为空 |
| `steps[]` | 文件存在性 + trace 事件 + gate 检查 | trace 优先，文件派生兜底 |
| `confirm_status` | `confirm_ui/result.json` | `tier1-confirmed` / `confirmed` |
| `generation_mode` | `confirm_ui/result.json` 或 chat 写入的等价记录 | 缺失时为空 |
| `spec_lock_digest` | `spec_lock.digest` 或 digest 脚本输出 | Step 6 前校验 |
| `page_count` | `spec_lock.md` 的 `page_rhythm` | Step 4 后可得 |
| `svg_count` | `svg_output/*.svg` | Step 6 期间实时变化 |
| `quality_summary` | quality reader 归一化 | 来自多个脚本 |
| `export_path` | `exports/*.pptx` 最新文件 | 允许多个导出，默认显示最新 |
| `live_preview` | `live_preview/lock.json`、legacy lock | 复用现有锁 |
| `confirm_ui` | `.confirm_ui.lock` | 复用现有锁 |

### 2.4 文件 watcher

**默认实现**：不用外部 `watchdog` 依赖，使用后台线程轮询 mtime，500-1000 ms debounce。

| 监听路径 | 触发事件 |
|----------|----------|
| `sources/` | `artifact:new`、`pipeline:state` |
| `templates/` | `artifact:new`、`pipeline:state` |
| `confirm_ui/recommendations.json` | `confirm:needed` |
| `confirm_ui/result.json` | `confirm:done`、`pipeline:state` |
| `analysis/` | `artifact:new` |
| `images/` | `artifact:new`、Step 5 进度 |
| `design_spec.md`、`spec_lock.md` | `artifact:new`、`pipeline:state` |
| `svg_output/` | `artifact:new`、`step:progress`、`pipeline:state` |
| `notes/total.md`、`notes/*.md` | `artifact:new` |
| `svg_final/` | `artifact:new` |
| `exports/` | `artifact:new`、`pipeline:state` |
| `backup/` | `artifact:new` |
| `trace.jsonl` | 日志增量、事件重放源 |
| `live_preview/lock.json`、`.confirm_ui.lock` | UI 服务状态 |

**事件策略**：同一文件短时间多次变化只推送一次 `pipeline:state`，但关键产物仍保留 `artifact:new`。

### 2.5 SSE 事件总线

| 能力 | 设计 |
|------|------|
| 初次连接 | 立即发送 `pipeline:state` |
| 心跳 | 每 15 秒发送 `heartbeat` |
| 断线重连 | 维护最近 200 条事件 ring buffer，支持 `Last-Event-ID` |
| 多客户端 | 每个客户端一个队列，慢客户端超限断开 |
| 事件落盘 | 关键事件追加到 `trace.jsonl`，纯心跳不落盘 |
| 降级 | 前端 SSE 断开后改为每 5 秒轮询 `/api/state` |

---

## 3. 前端架构

### 3.1 页面模型

前端是一个本地单页应用，使用 hash route，不需要构建步骤。

| 页面 | Route | 主要用途 |
|------|-------|----------|
| 管线总览 | `#/pipeline` | 当前步骤、8 步进度、阻塞点、下一动作 |
| 步骤工作台 | `#/step/:n` | 单步 gate、子步骤、产物、相关日志 |
| 确认中心 | `#/confirm` | Step 4 状态、Confirm UI 链接、已确认值摘要 |
| 实时预览 | `#/preview` | Live Preview 运行状态、入口、注解/直接编辑状态 |
| 质量中心 | `#/quality` | spec compliance、svg quality、harness、e2e、visual review |
| 产物与日志 | `#/artifacts` | 文件浏览、产物过滤、trace 查询 |

### 3.2 全局布局

| 区域 | 内容 |
|------|------|
| 顶栏 | 项目名、当前步骤、SSE 连接状态、Confirm/Preview 快捷入口 |
| 左侧导航 | 6 个页面 + 8 步微型状态条 |
| 主区 | 当前页面内容 |
| 右侧抽屉 | 最新事件、错误、可恢复建议 |
| 底部状态 | 最新导出文件、质量总状态、运行中本地服务 |

### 3.3 组件清单

| 组件 | 数据来源 | 交互 |
|------|----------|------|
| `PipelineRail` | `/api/state.steps` | 点击进入步骤工作台 |
| `StepCard` | `/api/state` | 展示 gate、子步骤、错误 |
| `GateChecklist` | `/api/step/:n` | 标出未满足前置条件 |
| `ServiceBadge` | bridge API | 打开 Confirm UI / Live Preview |
| `QualityMatrix` | `/api/quality` | 进入单项报告 |
| `ArtifactTable` | `/api/artifacts` | 按 type / step 过滤 |
| `TraceTimeline` | `/api/log` | 按 step / type 查询 |
| `EventToast` | SSE | 新产物、质量失败、确认完成 |
| `ExportPanel` | `/api/artifacts?type=pptx` | 打开所在文件夹路径提示 |

### 3.4 关键交互

| 场景 | 交互 |
|------|------|
| Step 4 到达 | `confirm:needed` 后顶栏高亮，确认中心显示现有 Confirm UI URL |
| 用户完成确认 | `confirm:done` 后更新确认摘要，管线状态进入 Step 5/6 前置就绪 |
| SVG 页面生成 | `artifact:new` 追加页面卡片，`step:progress` 更新页数 |
| 质量失败 | `quality:update` 显示失败项、脚本、返回码、报告入口 |
| Live Preview 已运行 | 预览页直接显示 URL，不重启服务 |
| SSE 断开 | 顶栏显示轮询模式，继续读取 `/api/state` |

---

## 4. 数据契约归一化

### 4.1 契约文件

| 文件 | 用途 |
|------|------|
| `contracts.json` | `PipelineState`、`StepDetail`、`Artifact`、质量报告等共享定义 |
| `api_contracts.json` | REST endpoint 请求/响应定义 |
| `sse_events.json` | SSE 事件 payload 定义 |

**硬边界**：前端只消费这些契约定义出的形状；脚本输出差异由后端 reader 归一化。

### 4.2 脚本输出归一化

| 输入来源 | 当前输出 | 后端归一化 |
|----------|----------|------------|
| `spec_compliance_check.py --json` | `warn` | 映射为 `warning`，同时保留原始 check 名 |
| `svg_quality_checker.py` | 文本 / export JSON / integrated review | 转成 `SVGQualityReport` 或 `IntegratedReview` |
| `harness_gate.py --json` | compact JSON，默认不含 `details` | 优先读取完整运行结果；必要时补空 `details` |
| `e2e_validate.py` | 当前主要为文本输出 | 第一版解析文本；后续补 `--json` 更稳 |
| `spec_lock_digest.py verify` | exit code + 文本 | 转成 `quality:update` 的 `spec_lock_digest` |

### 4.3 trace 事件映射

| trace 类型 | SSE 映射 |
|------------|----------|
| `step_start` / `step_complete` | `pipeline:state` |
| `substep_progress` | `step:progress` |
| `artifact_created` | `artifact:new` |
| `gate_result` / `auto_check` | `quality:update` |
| `user_confirm` | `confirm:done` |
| `error` | `error` |
| `server_lifecycle` | `pipeline:state` 或 bridge 状态刷新 |

---

## 5. 现有 UI 整合与迁移

### 5.1 保留策略

| 现有能力 | 第一版处理 | 后续可选整合 |
|----------|------------|--------------|
| Confirm UI | 独立 Flask 服务继续运行，Dashboard 读取 `.confirm_ui.lock` 并展示 URL | 抽出 shared app registration，挂到 Dashboard 下 |
| Live Preview | 独立 Flask 服务继续运行，Dashboard 读取 `live_preview/lock.json` | 复用其 API，在 Dashboard 中做轻量嵌入 |
| Confirm UI catalogs | 继续由 `/api/catalogs` 动态同步 canvas | Dashboard 只读摘要，不重复维护 |
| Live Preview 注解与直接编辑 | 完全保留现有 `/api/save-all` 流程 | Dashboard 显示 pending edits / annotations 计数 |
| CLI 脚本 | 不改命令语义 | 追加 `--json` 或 trace helper，不破坏旧输出 |

### 5.2 迁移阶段

| 阶段 | 交付 | 风险 |
|------|------|------|
| M0 契约与设计 | 三个 JSON 契约 + 本文档 | 低 |
| M1 只读 Dashboard | `/api/state`、`/api/artifacts`、`/api/events`、静态 UI | 低 |
| M2 trace helper | 给关键脚本追加可选 trace 写入 | 中 |
| M3 质量报告归一化 | `quality_reader.py` 稳定读取所有报告 | 中 |
| M4 UI 桥接 | Dashboard 展示 Confirm / Preview 入口与状态 | 低 |
| M5 可选深整合 | 将现有 Flask app 重构成可挂载模块 | 中高 |

**默认上线点**：M1 + M4 即可投入使用；M2/M3 提升实时性和诊断深度，但不是第一版阻塞项。

---

## 6. 8 步管线覆盖验证

| Step | Dashboard 状态信号 | 页面能力 | 保留的管线规则 |
|------|--------------------|----------|----------------|
| 1 Source Processing | `sources/*.md`、转换日志、`research_report.md` | 展示源文件、转换产物、deep-research 条件产物 | 不替代转换脚本，不跳过 deep-research |
| 2 Project Initialization | 项目目录、project metadata、`analysis/` | 展示项目格式、分析文件、条件工作流状态 | 不创建平行项目目录 |
| 3 Template Option | `templates/`、模板 provenance、品牌/布局/整套 deck 文件 | 展示已导入模板与来源 | 只有显式路径触发模板流程 |
| 4 Strategist | `confirm_ui/recommendations.json`、`result.json`、`design_spec.md`、`spec_lock.md` | 确认中心、推荐摘要、已确认值 | Step 4 仍是阻塞点，必须用户确认 |
| 5 Image Acquisition | `images/`、`image_prompts.json`、`image_prompts.md`、`image_analysis.csv` | 图片状态、AI/web/manual 标记、缺失资源 | manifest 模式和 Needs-Manual 规则不变 |
| 6 Executor | `live_preview/lock.json`、`svg_output/*.svg`、质量 gate、`notes/total.md` | 实时页数、预览入口、质量失败聚合 | SVG 仍由主 agent 顺序生成，不并行、不脚本批量生成 |
| 7 Post-processing & Export | `notes/*.md`、`svg_final/`、`exports/*.pptx`、`backup/`、e2e | 导出面板、最新 PPTX、备份快照 | 三个后处理命令仍一条一条执行 |
| 8a Spec Review | `docs/spec-review-template.md` 填写产物、change-log | 展示可选复盘状态 | 仅在用户要求或发现可复用原则时运行 |

### 6.1 功能保全清单

| 能力 | 保全方式 |
|------|----------|
| Step 4 chat fallback | Dashboard 只是提示，不要求浏览器确认 |
| Confirm UI 两阶段确认 | 继续读取 `stage: tier1/final` |
| Split mode | `generation_mode: split` 在状态中保留，并提示 Phase B |
| Refine spec | `refine_spec: true` 在确认中心显示，不自动生成 |
| Live Preview 注解 | Dashboard 不在 Step 6 中读取或应用注解 |
| Direct edits | 只在用户点击现有页面 Apply changes 后反映到文件状态 |
| 质量门失败 | Dashboard 显示失败，不自动修复 |
| chart / audio / animation standalone workflows | 作为 Step 6/7 后的可选状态，不默认触发 |

---

## 7. 实施可行性检查

### 7.1 已满足条件

| 条件 | 证据 |
|------|------|
| 后端框架一致 | 现有 Confirm UI 与 Live Preview 都是 Flask |
| 服务锁机制可复用 | `server_common.py` 已有 lock、liveness、free port helper |
| 状态可从文件派生 | 项目目录已有固定 artifacts 结构 |
| 前端可免构建 | 现有静态 JS/CSS 已可维护复杂交互 |
| SSE 不需要额外依赖 | Flask streaming response + queue 可实现 |

### 7.2 编码前需要处理的差异

| 差异 | 处理 |
|------|------|
| `contracts.json` 使用 `warning`，部分脚本输出 `warn` | `quality_reader.py` 统一映射 |
| `harness_gate.py --json` 当前不输出完整 `details` | 第一版补空 details；后续让 `--json` 保留 details |
| `e2e_validate.py` 当前缺少稳定 JSON 输出 | 第一版解析文本；后续加 `--json` |
| SVG 文件名不一定全是 `P*.svg` | artifact registry 扫描全部 `.svg`，质量脚本仍遵守自身规则 |
| 多个本地 UI 可能争抢 5050 | dashboard 使用独立端口，Confirm/Preview 继续 auto-advance |

### 7.3 风险与约束

| 风险 | 规避 |
|------|------|
| 控制台被误解为执行器 | 页面文案只显示状态与入口，不提供“自动继续”按钮 |
| watcher 推断错误 | trace 事件优先，文件派生仅作为兜底 |
| 脚本输出变化导致解析失败 | reader 保留 raw stdout/stderr 并标记 `parse_error` |
| 长时间 SSE 客户端堆积 | per-client queue 上限 + 慢客户端断开 |
| 过早深度整合现有 UI | 先链接/桥接，再重构挂载 |

---

## 8. 第一版实施任务

### 8.1 后端

1. 新建 `server.py` / `app_factory.py`，支持：
   - `python3 skills/ppt-master/scripts/dashboard/server.py <project_path>`
   - `--port`、`--no-browser`、`--shutdown`
2. 实现 `state_reader.py`：
   - 读取项目结构，输出 `PipelineState`
   - Step 4 / Step 6 / Step 7 必须优先准确
3. 实现 `artifact_registry.py`：
   - 扫描固定目录
   - 分类为 `ArtifactType`
   - 提供 size、mtime、step
4. 实现 `event_bus.py` + `watcher.py`：
   - 初始 state
   - 文件变化触发 state/artifact/quality/confirm 事件
5. 实现 `quality_reader.py`：
   - 读取已存在报告
   - 必要时运行轻量 `--json` 命令要由用户/agent 显式触发，Dashboard 本身默认不跑重活

### 8.2 前端

1. 建立 6 个 hash route。
2. 顶栏显示 SSE 状态与当前 step。
3. 管线总览先交付，其他页面可用同一数据源逐步补。
4. 质量中心必须能展示失败详情，不只展示红绿状态。
5. 产物页支持 type / step 过滤。

### 8.3 验收

| 验收项 | 标准 |
|--------|------|
| JSON 契约可解析 | `contracts.json`、`api_contracts.json`、`sse_events.json` 全部合法 |
| 空项目可打开 | 无 `spec_lock.md` 时显示 Step 1/2 pending，不报 500 |
| Step 4 项目可打开 | 识别 recommendations/result 和确认状态 |
| Step 6 项目可打开 | 识别 svg_count、live preview URL、质量状态 |
| Step 7 项目可打开 | 识别最新 PPTX 和 backup |
| SSE 可恢复 | 断线后 fallback polling 可继续更新 |
| 现有 UI 不回归 | Confirm UI / Live Preview 原命令仍可独立运行 |

---

## 9. Phase 3 验证结论

| 检查项 | 结论 |
|--------|------|
| 8 步管线覆盖 | 已覆盖，Step 4 和 Step 6 的阻塞/串行约束保留 |
| 现有功能保留 | Confirm UI、Live Preview、质量脚本、导出脚本均保持原命令 |
| API 完整性 | 已有契约覆盖必要 REST 与 SSE；实现时需做脚本输出归一化 |
| 实施复杂度 | 第一版为中低复杂度，可在现有 Flask/静态前端模式内完成 |
| 最大风险 | 不在技术栈，而在状态推断准确性；用 trace 优先 + 文件兜底处理 |

**下一步**：进入 M1，只实现只读 Dashboard 和桥接入口；不要先重构 Confirm UI / Live Preview。
