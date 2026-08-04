# DeepPPT2 实际交付优化最终报告（2026-08-04）

> 状态：Phase 0-6 全部完成（`plans/deepppt2-practical-delivery-optimization-agent-brief.md` 执行收口），追加 trace 写侧接入批次。
> 权威性：**非运行权威**；`AGENTS.md`、`skills/ppt-master/SKILL.md`、`workflows/routing.md`、`workflows/generate-pptx.md` 及各 owning workflow 仍是运行权威。
> 配套：Agent Brief `plans/deepppt2-practical-delivery-optimization-agent-brief.md`；原始证据 `.tmp/golden/`、`.tmp/fixtures/`、`.tmp/gs_recall/`、`.tmp/phase*-*.log` 等（gitignored）。
> 提交：`fe52de88`（工具链）+ `20e58d60`（Phase 1-6）+ `b2d2c141`（trace 接入）。

---

## 1. 修改范围与未修改范围

### 已修改（change-log 共 6 条新条目）

| 类别 | 文件 |
|---|---|
| 几何审计 + PowerPoint 渲染（在途工作流入库） | `scripts/svg_geometry_audit.py`、`scripts/pptx_render_export.py`、`scripts/visual_review.py`（--scale/图片 settle）、`scripts/docs/geometry-audit.md` |
| 校准修复（Phase 1） | `svg_geometry_audit.py`：line-spacing 行内 tspan（gap<=0 跳过）+ `translate()` 累积（74 条 FP 消除） |
| 内容保真（Phase 3） | 表征 fixture `fixtures/docx_complex/`、`fixtures/pptx_complex/`；损坏输入 fail-closed 断言 |
| 路线 fixture（Phase 2） | `fixtures/`（9 套：template_fill/enhance/structured/partial×15/docx/pptx/trace_calibration/space_report + rebuild 脚本 + README） |
| 运行指标（Phase 4 + 接入批） | `scripts/run_summary.py`（新增）、`scripts/image_gen.py`（attempt 埋点）、`scripts/svg_to_pptx.py`（pptx_export 埋点）、`scripts/docs/trace-contract.md`（§3 更新） |
| 中断诊断（Phase 5） | `scripts/project_utils.py`（diagnose_project）、`scripts/project_manager.py`（diagnose 子命令） |
| 空间治理（Phase 6.2） | `scripts/space_report.py`（只读 + archive dry-run） |
| 契约测试 | `scripts/smoke_check.py`（Test 10-14，+87 checks） |
| 文档/治理 | `AGENTS.md`（命令速查）、`.align/spec.md`（基线）、`.align/lessons.md`（+11 条）、`docs/change-log.md`、本报告 |

### 未修改（硬边界）

- `SKILL.md`、`workflows/routing.md`、`workflows/generate-pptx.md` 及 owning workflow 门禁行为（零改动）
- `svg_quality_checker.py` 默认行为、`_ANCHOR_COMPARE_ENABLED`（保持 False）、spec_lock 契约、converter 实现（仅加 trace 埋点）
- `.github/workflows/`（CI 未改；真实跑测经 push 触发 2 次）
- `examples/` 原件、`projects/` 用户数据（gan_hemt 仅重生成 `.spec_lock.digest`，经用户批准）
- 无新增依赖、无付费 API 调用、无删除操作

---

## 2. 前后指标

| 指标 | 前 | 后 |
|---|---|---|
| smoke integration checks | 187/191 | **270/274**（Test 8-14） |
| 完整 smoke | 166/170 | **170/174**（+4 新脚本） |
| geometry audit FP（Golden Set 44 页） | 74 | **0**（58 line-spacing + 16 rect-over-text；留 3 条已裁决：2 TP fixture 内容 + 1 FP 模型局限） |
| 已知缺陷召回 | 无测试 | **5/5** 注入复现（修复前后无回归） |
| 路线/契约 fixture | 0 | **9 套**（含 15 partial 态 + trace/space 校准） |
| 诊断/指标/空间工具 | 无 | `run_summary` / `diagnose` / `space_report` / `geometry_audit` / `pptx_render_export` |
| 真实渲染链路 | 无工具 | PowerPoint COM 44 页 Golden Set + 14 页 gan_hemt 实测 |
| 真实项目诊断 | 无 | gan_hemt：8-export ok（digest 修复后） |
| 真实运行指标 | 无 | gan_hemt 全链 run_summary：slides=14、gates.harness=PASS、pptx_export 2313ms、delivery=passed-with-warnings |

---

## 3. 关键决策与校准结论

1. **advisory 保持**：text-overlap 实测 precision 67%（2TP/1FP）< 95% 升级线 → 无任何检查升级为硬门；`--strict` 需 Gate G2。
2. **PowerPoint 渲染为最终裁决**：Chromium 与 PPT 字体度量差异（雅黑行高/字宽 headroom）已文档化；几何审计只作第一道防线。
3. **null/0 语义落地**：run_summary 未接入测量记 null + not-wired（SVG 重生成），真实零值记 0，写入方实测 duration 优先。
4. **单一 owner**：诊断/状态均收敛于 `project_utils`（derive + diagnose），project_manager/Dashboard 消费同源。
5. **fixture 纪律**：全部合成非敏感（零用户数据/零网络/零付费 API），二进制可经 rebuild 脚本重建；测试走 smoke --integration（CI 自动）。
6. **trace 埋点**：image attempt（无 prompt 正文，白盒断言防泄漏）、pptx_export、annotations.jsonl 计数；SVG 重生成（agent 手改）如实未采集。

---

## 4. 未完成项与剩余风险

### 未完成（如实保留）

| 项 | 原因 | 状态 |
|---|---|---|
| beautify AI 重排版步骤 fixture | 非确定性（需 Strategist LLM），无法复跑 | 确定性端点已覆盖（ppt_to_md + svg_to_pptx） |
| SVG 重生成次数指标 | agent 手改 SVG，无脚本钩子 | run_summary 报 null + not-wired（已文档化） |
| 首次真实 CI 结果确认 | gh 未认证 + 匿名 API 限流 | push 已触发 2 次（20e58d60 / b2d2c141），结果需在 Actions 页人工确认 |
| CI 反馈时间优化（12.1） | Phase 6 默认不执行，未获单独批准 | 未选择 |

### 剩余风险

- 几何审计 0.22 descent 模型对个别拉丁字体（Arial Black）高估 → 已记录，borderline 以 PowerPoint 渲染裁决。
- advisory 检查升级前 precision 需 ≥95% + Gate G2；当前 67%。
- `_ANCHOR_COMPARE_ENABLED=False` 保持；全局启用会产生 240+ legacy 漂移（历史事实，未复核数字）。
- 在途改动时间线不一致已于 fe52de88 解决（change-log 记录与代码同批入库）。

---

## 5. 回滚方式

- 逐批可逆补丁：删除新脚本（run_summary/space_report/diagnose 分支/埋点行）+ 还原 smoke 区块 + 移除 fixtures/ 目录即可。
- 未改变任何既有门禁默认值、未改 PPTX 输出结构、未动 SKILL.md/路由 → 无跨批耦合回滚。
- 真实用户项目仅 gan_hemt `.spec_lock.digest` 重生成（内容与 spec_lock 重新对齐，可再 generate 覆盖）。

---

## 6. 验证矩阵回执

| 变更 | 最低验证 | 结果 |
|---|---|---|
| 任意 repo 修改 | attribution guard | rc=0（每批） |
| scripts/ 修改 | 修改前后 smoke | 每批同命令对比，无回归 |
| CLI 新增/修改 | import/--help/坏参数 rc/边界 | run_summary/diagnose/space_report 全过 |
| SVG quality 规则 | characterization fixture + Golden Set TP/FP/FN | 召回 5/5；FP 74→0 |
| 导出/PPTX 检查 | svg_to_pptx/delivery/render/e2e | Golden Set 44 页 + gan_hemt 14 页全绿 |
| source converter | 正常/合并/符号/坏输入 fixture | DOCX/PPTX 保真对账 + 3/3 坏输入 fail-closed |
| trace/summary | schema/legacy/null-0/敏感负面 | Test 11 + Test 14 全 PASS |
| pipeline diagnosis | happy + partial + 确定性 | Test 12：15/15 + 确定性 + 只读 |
| CI workflow | 本地等价命令 | push 触发，远端结果待人工确认 |
