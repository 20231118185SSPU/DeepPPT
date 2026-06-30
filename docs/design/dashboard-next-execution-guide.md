# Dashboard 后续实施执行文档

> 目标：把当前 Dashboard 从“可用的只读控制台”推进到“可诊断、可预览、可安全触发辅助命令的项目工作台”。本文档给后续编码 agent 或开发者使用，包含阶段计划、编码提示词、验收标准和风险边界。

## 1. 总原则

### 1.1 产品边界

| 原则 | 要求 |
|------|------|
| Dashboard 仍以只读为默认 | 打开页面、刷新状态、预览文件不得触发生成、确认、导出或质量脚本 |
| 执行动作必须显式 | 一键运行质量检查、启动 Confirm UI、启动 Live Preview 等动作必须有按钮、确认弹窗和清晰命令预览 |
| 不跨越 Step 4 阻塞点 | 确认中心可以显示 Confirm UI 状态和结果摘要，不得代替用户确认 |
| 不替代 Executor | Dashboard 不生成 SVG，不批量修改 SVG，不自动应用注解 |
| 前端免构建 | 继续使用 `static/index.html`、`static/app.js`、`static/style.css`，不引入 React/Vite |
| 后端轻依赖 | 默认只用 Flask + 标准库，除非已有项目依赖明确可用 |
| Chrome 安全端口 | 默认端口保持 `8765`，不要回到 Chrome 禁止的 `5060` |

### 1.2 编码风格

| 文件 | 风格 |
|------|------|
| `skills/ppt-master/scripts/dashboard/*.py` | 遵守 `docs/rules/code-style.md`，保留 CLI 可独立运行和 `main(argv=None) -> int` 风格 |
| `skills/ppt-master/scripts/dashboard/static/*.js` | 保持原生 JS，函数小而可读，状态集中在 `state` 对象，避免新增构建链 |
| `skills/ppt-master/scripts/dashboard/static/*.css` | 工具型控制台风格，卡片半径不超过 8-12px；避免装饰性圆球、单一紫蓝渐变和营销页式 hero |
| `docs/change-log.md` | 修改 `skills/ppt-master/scripts/` 后必须追加条目 |

---

## 2. 当前基线

### 2.1 已完成能力

| 能力 | 文件 |
|------|------|
| Flask Dashboard 服务 | `scripts/dashboard/server.py` |
| 管线状态读取 | `scripts/dashboard/state_reader.py` |
| 产物扫描与类型分类 | `scripts/dashboard/artifact_registry.py` |
| 文件内容预览 API | `scripts/dashboard/content_viewer.py` |
| SSE 事件与 watcher | `event_bus.py`、`watcher.py` |
| Confirm / Live Preview 状态桥接 | `bridge.py` |
| 6 个前端页面 | `static/app.js`、`static/style.css` |
| 产物按文件类别分组 | `renderArtifacts()`、`artifactGroups()` |
| SVG/PPTX 放大弹窗 | `openPreviewModal()`、`previewModalPages()`、modal CSS |

### 2.2 仍需补齐的能力

| 阶段 | 目标 |
|------|------|
| M2 | 产物预览与文件浏览交互完善 |
| M3 | 质量中心结构化解析与可读报告 |
| M4 | Confirm / Preview 桥接从“状态入口”升级为“安全启动入口” |
| M5 | Trace 日志和项目健康度 |
| M6 | 中文产品化和长期维护约束 |

---

## 3. M2：产物浏览与预览增强

### 3.1 交付范围

| 功能 | 要求 |
|------|------|
| PDF 放大弹窗 | PDF 与 SVG/PPTX 使用同一 modal 框架，支持新窗口打开 |
| SVG/PPTX 缩放 | 弹窗内提供“适配宽度 / 适配高度 / 100%”三个模式 |
| 文件搜索 | 产物页左侧支持按文件名、路径、类型过滤 |
| 排序 | 支持按修改时间、名称、大小排序 |
| 步骤筛选 | 支持按 Step 1-7 或全部筛选 |
| 选中状态持久 | 切换分组、过滤后尽量保留当前文件预览；文件被过滤掉时显示提示 |

### 3.2 数据与状态设计

在 `static/app.js` 的 `state` 中追加：

```js
artifactFilters: {
  query: '',
  step: 'all',
  sort: 'mtime_desc',
},
previewModal: {
  path: '',
  index: 0,
  fit: 'contain',
},
```

| 字段 | 取值 |
|------|------|
| `query` | 任意字符串，匹配 `name/path/type` |
| `step` | `all` 或 `1`-`8` |
| `sort` | `mtime_desc`、`mtime_asc`、`name_asc`、`size_desc` |
| `fit` | `contain`、`width`、`height`、`actual` |

### 3.3 编码提示词

```text
你正在 C:\Users\FUTIAN\Desktop\DeepPPT 修改 Dashboard 前端。
必须先阅读 skills/ppt-master/SKILL.md 和 docs/design/dashboard-next-execution-guide.md。
任务：实现 M2 产物浏览与预览增强。

约束：
- 只修改 skills/ppt-master/scripts/dashboard/static/app.js、style.css，必要时修改 content_viewer.py。
- 不启动或重启 Dashboard 服务。
- 不引入 React/Vite/npm 构建链。
- Dashboard 默认只读，不运行生成或质量脚本。

实现：
1. 在 state 中增加 artifactFilters 和 previewModal.fit。
2. 在产物页增加搜索框、Step 筛选、排序下拉。
3. artifactGroups() 前先按 filters 过滤和排序。
4. PDF 也支持“放大预览”。
5. SVG/PPTX/PDF modal 顶栏增加 适配宽度 / 适配高度 / 100% / 适配窗口 控制。
6. modal 左右切换只对多页 SVG/PPTX 生效；PDF 不显示页码条，除非后端未来提供页面数组。
7. 更新 docs/change-log.md。

验收：
- node --check skills/ppt-master/scripts/dashboard/static/app.js 通过。
- python -m py_compile skills/ppt-master/scripts/dashboard/server.py skills/ppt-master/scripts/dashboard/content_viewer.py 通过。
- 产物页空列表、很多文件、当前选择文件被过滤掉三种状态都有合理显示。
```

### 3.4 验收清单

| 场景 | 标准 |
|------|------|
| 搜索 `pptx` | 只显示匹配文件或包含 pptx 的路径/类型 |
| Step 筛选 `7` | 只显示导出、备份、svg_final 等 Step 7 产物 |
| SVG 放大 | 弹窗可打开，左右键切换，Esc 关闭 |
| PPTX 放大 | 使用 SVG 页数组，可页码切换 |
| PDF 放大 | iframe 全屏预览，可新窗口打开 |
| 过滤后当前文件不可见 | 右侧预览保留但提示“当前文件不在筛选结果中”或清空选择 |

---

## 4. M3：质量中心结构化报告

### 4.1 交付范围

| 功能 | 要求 |
|------|------|
| 质量摘要 | Overall、Spec、SVG、E2E、Visual Review 独立状态 |
| 问题分组 | `must_fix`、`should_fix`、`accepted_risks` 三组展示 |
| 报告来源 | 显示每条问题来自哪个脚本和哪个文件 |
| 文件跳转 | 问题关联产物可点击打开右侧预览或产物页 |
| 原始报告 | 保留 JSON 原文折叠区，不作为主界面 |
| 空状态 | 未运行质量脚本时说明“未发现报告”，不显示错误 |

### 4.2 后端设计

优先增强 `quality_reader.py`，输出统一结构：

```json
{
  "overall": "pass|warn|fail|unknown",
  "checks": [
    {
      "id": "svg_quality",
      "label": "SVG Quality",
      "status": "pass|warn|fail|unknown",
      "source_file": "quality/svg_quality.json",
      "updated_at": "..."
    }
  ],
  "issues": {
    "must_fix": [],
    "should_fix": [],
    "accepted_risks": []
  },
  "raw": {}
}
```

| 输入 | 处理 |
|------|------|
| `harness_gate.py --json` 输出 | 作为总状态优先来源 |
| `svg_quality_checker.py --integrated-review` | 直接映射三级问题 |
| 旧版 errors/warnings | errors -> `must_fix`，warnings -> `should_fix` |
| 缺失报告 | 返回 404 或 `null`，前端显示空状态 |

### 4.3 编码提示词

```text
你正在实现 Dashboard M3 质量中心结构化报告。
必须保持 Dashboard 默认只读：不要在页面加载时运行质量脚本。

后端：
1. 修改 scripts/dashboard/quality_reader.py，新增 normalize_quality_report(project) 或扩展 quality_report(project)。
2. 兼容 harness、svg_quality、spec_compliance、e2e_validate、integrated-review 的已有文件形状。
3. 对无法解析的报告，保留 raw，并追加 parse_warning，不抛 500。
4. /api/quality 返回统一结构，同时保留旧字段兼容前端。

前端：
1. renderQuality() 改为质量矩阵 + 三级问题列表 + 原始 JSON 折叠区。
2. 问题项显示 severity、check、file/path、message、recommendation。
3. 如果 issue 有 path，点击后调用 /api/artifact 加载预览。
4. 不再把 JSON 原文作为主界面。
5. 更新 docs/change-log.md。

验收：
- py_compile 通过。
- node --check 通过。
- 无质量报告时页面正常。
- 有旧版 JSON、integrated-review JSON、无法解析 JSON 三类输入时页面都不白屏。
```

### 4.4 验收清单

| 场景 | 标准 |
|------|------|
| 无报告 | hero 显示“待生成”，无 500 |
| 有 PASS | 质量矩阵全绿，问题列表为空 |
| 有 warning | `should_fix` 可读展示 |
| 有 error | `must_fix` 置顶展示 |
| JSON 解析失败 | 显示 parse warning 和 raw 文件路径 |
| 点击 issue 文件 | 打开产物预览或跳转产物页 |

---

## 5. M4：安全启动 Confirm / Preview / Quality

### 5.1 交付范围

| 功能 | 要求 |
|------|------|
| 启动 Confirm UI | 未运行时显示“启动确认页”，点击弹出命令确认 |
| 启动 Live Preview | 未运行时显示“启动实时预览”，点击弹出命令确认 |
| 运行质量检查 | 质量中心提供手动运行按钮，但需要确认 |
| 命令预览 | 弹窗显示将运行的命令、项目路径、可能耗时 |
| 运行状态 | 显示 running / done / failed 和 stdout/stderr 摘要 |
| 禁止生成命令 | 不提供 Strategist、Executor、export 的自动继续按钮 |

### 5.2 后端 API 设计

新增 API 时使用显式 action endpoint：

| API | 方法 | 行为 |
|-----|------|------|
| `/api/actions/start-confirm` | POST | 启动 `confirm_ui/server.py <project> --daemon` |
| `/api/actions/start-preview` | POST | 启动 `svg_editor/server.py <project> --live` |
| `/api/actions/run-quality` | POST | 运行用户选择的质量脚本 |
| `/api/actions/<id>` | GET | 查询 action 状态 |

请求示例：

```json
{
  "confirm": true,
  "mode": "quick",
  "checks": ["spec", "svg", "harness"]
}
```

响应示例：

```json
{
  "action_id": "20260630-quality-001",
  "status": "running",
  "command_preview": "python ...",
  "started_at": "..."
}
```

### 5.3 安全规则

| 规则 | 要求 |
|------|------|
| POST only | 所有执行动作必须是 POST |
| 显式确认 | 前端必须传 `confirm: true` |
| 命令白名单 | 后端只允许固定脚本和固定参数组合 |
| 项目内执行 | 所有命令 cwd 为仓库根，project path 必须 resolve 在允许根内 |
| 无 shell 拼接 | 使用 `subprocess.Popen([...])` 列表参数，不使用 `shell=True` |
| 输出截断 | stdout/stderr 存 action log，API 只返回尾部摘要 |

### 5.4 编码提示词

```text
你正在实现 Dashboard M4 安全动作层。
重点是安全边界，不是功能越多越好。

后端：
1. 新增 scripts/dashboard/actions.py。
2. 实现固定白名单 action：start-confirm、start-preview、run-quality。
3. 所有 subprocess 使用列表参数，禁止 shell=True。
4. project path 必须 resolve 后在当前 project 内或 repo workspace 内。
5. action 状态写入 <project>/dashboard/actions/<action_id>.jsonl 或 json。
6. server.py 注册 /api/actions/... 路由。

前端：
1. Confirm/Preview 未运行时显示启动按钮。
2. 点击后弹出确认 modal，显示命令预览和说明。
3. 质量中心提供“运行质量检查”按钮，默认选择 quick harness，不自动运行。
4. 显示 action running/done/failed 状态。
5. 更新 docs/change-log.md。

禁止：
- 不添加“继续生成”“自动导出”“应用注解”等按钮。
- 不绕过 Step 4 确认。
- 不把任意用户输入拼进命令。

验收：
- py_compile 通过。
- start-confirm/start-preview 在服务已运行时返回 existing URL，不重复启动。
- run-quality 失败时页面显示错误摘要，不白屏。
```

---

## 6. M5：Trace 日志与项目健康度

### 6.1 交付范围

| 功能 | 要求 |
|------|------|
| Trace 过滤 | 按 step、type、时间、关键词过滤 |
| 日志分页 | limit/offset 或 cursor，不一次性渲染全部 |
| 健康度总览 | 基于缺失关键产物、质量状态、服务状态给出 `healthy/warn/blocked` |
| 最新事件抽屉 | 顶栏或右侧显示最近 10 条关键事件 |
| 错误恢复建议 | 仅根据已知状态给出下一步提示，不自动执行 |

### 6.2 健康度规则

| 状态 | 条件 |
|------|------|
| `healthy` | 当前步骤前置产物齐全，质量无 fail，服务状态符合当前阶段 |
| `warn` | 有 warning、缺少可选产物、服务未运行但当前阶段不强依赖 |
| `blocked` | Step 4 未确认、Step 6 质量 fail、Step 7 缺失必要图片或导出失败 |
| `unknown` | 状态来源不足 |

### 6.3 编码提示词

```text
实现 Dashboard M5 Trace 与健康度。

后端：
1. 扩展 trace_store.py 支持 type、step、query、limit、offset、order。
2. 在 state_reader.py 或新 health_reader.py 中派生 health_summary。
3. /api/state 增加 health_summary，但保持旧字段兼容。

前端：
1. 产物与日志页的 Trace 区增加过滤工具栏和分页。
2. 管线总览 hero 显示健康度 badge 和阻塞原因。
3. 新增最近事件列表，最多 10 条。
4. 不显示大段原始日志作为主界面。
5. 更新 docs/change-log.md。

验收：
- 无 trace.jsonl 时页面正常。
- 1000+ trace 行时前端不卡顿。
- health_summary 不确定时显示 unknown，不误报 healthy。
```

---

## 7. M6：中文产品化与维护

### 7.1 交付范围

| 功能 | 要求 |
|------|------|
| 文案统一 | 页面主文案中文，必要的技术名保留英文 |
| 空状态完善 | 每个页面都有明确空状态、未运行状态、无报告状态 |
| 错误状态 | API 失败显示重试入口和错误摘要 |
| 可访问性 | 所有 modal 有 `role="dialog"`、关闭按钮、Esc 关闭 |
| 响应式 | 1366px、1920px、手机宽度下不重叠 |
| 视觉一致性 | 不使用营销式 landing page，不使用大量装饰圆球或单一紫蓝配色 |

### 7.2 编码提示词

```text
实现 Dashboard M6 中文产品化与维护收敛。

任务：
1. 扫描 app.js 所有英文 UI 文案，保留必要技术名，其他改中文。
2. 为每个页面补齐 loading、empty、error 状态。
3. 检查所有 button/a 的 disabled、aria-disabled、title。
4. 检查移动端布局，避免按钮文字溢出和卡片内容重叠。
5. 梳理 CSS，去除重复规则，不改变视觉行为。
6. 更新 docs/change-log.md。

验收：
- node --check 通过。
- 页面中除 API 字段名、技术名外无突兀英文句子。
- 720px 宽度下导航、hero、modal、产物列表不重叠。
```

---

## 8. 通用回归测试

### 8.1 每轮必跑

```powershell
node --check skills/ppt-master/scripts/dashboard/static/app.js
python -m py_compile skills/ppt-master/scripts/dashboard/server.py skills/ppt-master/scripts/dashboard/content_viewer.py skills/ppt-master/scripts/dashboard/quality_reader.py
```

如修改新增 Python 文件，把文件加入 `py_compile` 列表。

### 8.2 手动验证

| 验证 | 步骤 |
|------|------|
| 打开 Dashboard | `python skills/ppt-master/scripts/dashboard/server.py examples/ppt169_swiss_grid_systems --port 8765` |
| 强制刷新 | Chrome 中 `Ctrl+F5` |
| 产物预览 | 进入 `产物与日志`，展开 SVG/PPTX/PDF，点击文件 |
| 弹窗切换 | 点击 `放大预览`，用左右按钮、键盘方向键、页码条切换 |
| 服务状态 | Confirm/Preview 未运行时按钮必须 disabled 或显示启动确认 |
| SSE 降级 | 断开后页面显示轮询模式且继续可用 |

### 8.3 不应做的验证

| 禁止 | 原因 |
|------|------|
| 自动跑完整 PPT 生成 | Dashboard 改动不应触发主生成管线 |
| 自动执行导出 | 导出属于 Step 7 工作流，不属于只读 Dashboard 验证 |
| 重置项目目录 | 可能删除用户产物 |
| 修改 `.env` 或浏览器会话文件 | 敏感文件 |

---

## 9. 通用编码提示词模板

后续每次可以把下面模板交给编码 agent：

```text
你在 C:\Users\FUTIAN\Desktop\DeepPPT 工作。
先阅读：
1. skills/ppt-master/SKILL.md
2. AGENTS.md
3. docs/design/dashboard-next-execution-guide.md
4. 与本阶段相关的现有文件：scripts/dashboard/server.py、state_reader.py、quality_reader.py、static/app.js、static/style.css

任务阶段：M{n} - {阶段名称}
目标：{用 2-4 条写清楚具体要交付什么}

硬约束：
- 不修改生成管线语义，不跨越 Step 4 阻塞确认。
- 不引入前端构建链。
- 不自动启动或重启长运行服务，除非用户明确要求。
- 不运行 destructive 命令，不改 .env，不改浏览器会话文件。
- 修改 scripts/dashboard/ 后必须更新 docs/change-log.md。

实现要求：
- 保持 Dashboard 默认只读；如果新增执行动作，必须 POST + 白名单 + 确认弹窗 + 命令预览。
- 前端必须处理 loading、empty、error 三种状态。
- 失败时页面不能白屏，后端不能 500 泄漏 traceback 给用户。
- CSS 避免营销页式 hero、装饰圆球、单一紫蓝主题；保持工具型控制台风格。

验收命令：
node --check skills/ppt-master/scripts/dashboard/static/app.js
python -m py_compile {本次涉及的 Python 文件}

最终报告：
- 列出修改文件。
- 列出已完成能力。
- 列出验证命令和结果。
- 如果未启动服务，明确说明让用户 Ctrl+F5 或手动启动。
```

---

## 10. 推荐实施顺序

| 顺序 | 阶段 | 原因 |
|------|------|------|
| 1 | M3 质量中心结构化报告 | 直接提升 PPT 生成闭环价值，能更快定位问题 |
| 2 | M2 产物浏览增强 | 改善高频查看产物体验 |
| 3 | M5 Trace 与健康度 | 提升长流程诊断能力 |
| 4 | M4 安全启动动作 | 涉及执行安全，等只读诊断稳定后再做 |
| 5 | M6 中文产品化 | 最后统一收敛文案和视觉一致性 |

**默认下一步**：先做 M3。质量中心从 JSON 原文升级为 `must_fix / should_fix / accepted_risks` 结构化报告，是对后续 PPT 生成最有价值的改进。
