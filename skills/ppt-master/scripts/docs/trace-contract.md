# Trace Contract — `<project>/trace.jsonl`

> Owner: `dashboard/trace_writer.py`（写入）、`dashboard/trace_store.py`（读取）。
> 权威性：非运行规则；envelope 由 `trace_writer._normalize_event` 强制（system-optimization T5.2）。

## 1. Event envelope（v1）

每行一个 JSON 对象，必填 + 可选槽位：

| 字段 | 类型 | 必填 | 语义 |
|---|---|---|---|
| `schema_version` | int | ✓（v1 起） | 1；旧事件无此字段，reader 必须容忍 |
| `ts` | str | ✓ | ISO-8601 UTC 时间戳 |
| `type` | str | ✓ | 事件类型（`step_start` / `step_complete` / `gate_result` / `artifact_created` / `bridge_status` / `error` …） |
| `operation` | str | ✓ | 默认等于 `type`；调用方可覆盖为更细的操作名 |
| `detail` | str | ✓ | 人类可读摘要（不含正文内容） |
| `route` | str \| null | 可选 | 顶层路由（generate / template / native …），未知为 null |
| `step` | int \| null | 可选 | 流水线步骤号 |
| `status` | str \| null | 可选 | PASS / FAIL / running … |
| `duration_ms` | int \| null | 可选 | 操作耗时；未测量为 null（**不是 0**） |
| `error_code` | str \| null | 可选 | 失败时的稳定错误码；成功为 null |
| artifact refs | str | 可选 | `path` / `report_path` / `artifact_type` 等自由槽位 |

**null 与 0 语义（T5.6）**：`duration_ms: null` = 未测量；`duration_ms: 0` = 实测 0ms。`error_code: null` = 无错误。统计时 null 必须排除，不得当 0 计入。

**敏感禁令（T5.3）**：事件不得包含源文全文、Prompt 正文、密钥、凭据、浏览器会话或用户隐私内容。只记录元数据（步骤名、状态、路径、耗时、错误码）。

## 2. 读取契约

- `trace_store.load_trace(project)`：逐行解析，坏行跳过；`query_trace` 支持按查询串过滤。
- reader 必须容忍无 `schema_version` 的旧事件（v1 前由 `trace_event` 直接写入）。
- Dashboard `/api/log` 直接消费 trace_store，不自行计算第二套事件。

## 3. 优化指标来源（T5.5）

| 指标 | 来源 | 说明 |
|---|---|---|
| 阶段耗时 | trace `ts` 差（`step_start` → `step_complete`） | 同一 `operation`/`step` 配对 |
| 失败率 | `status == "FAIL"`（或 `type == "error"`）事件数 / 事件总数 | 按 route/step 分组 |
| 重试率 | 相同 `operation` 短时间内重复事件 | 需要 operation 命名稳定 |
| gate 错误分布 | `quality/harness.json` details + trace `gate_result.failed_scripts` | 每 gate 独立计数 |
| 图片生成/搜索尝试 | `image_gen.py` 每 manifest 尝试发 `image_gen_attempt`（operation `image_gen:<stem>`，status PASS/FAIL，error_code；**不含 prompt 正文**） | `run_summary.image_attempts` 消费 |
| PPTX 导出/重导出 | `svg_to_pptx.py` 包装器每次导出发 `pptx_export`（status/duration_ms） | `run_summary.pptx_reexport_count` 消费 |
| Live Preview 标注数 | `<project>/annotations.jsonl`（svg_editor server 写入） | `run_summary.live_preview_count` 消费；无文件时回退 trace 事件 |
| SVG 重生成次数 | **未采集**（重生成是 agent 手改 SVG，无脚本钩子） | `run_summary` 报 null + not-wired |
| 用户修订次数 | **未采集**（无 artifact 承载；确认修订回执时可手工记录） | 不伪造默认值 |
| Prompt tokens | `prompt_audit.py --json` 回执 | 阶段回执附带 |

未采集的指标保持"无数据"状态，不填默认 0 或占位值。
