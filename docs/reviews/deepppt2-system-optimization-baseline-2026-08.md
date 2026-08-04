# DeepPPT2 系统优化 Phase 0 只读基线报告（2026-08-04）

> 状态：Phase 0 只读基线产物（2026-08-04 实测，`plans/deepppt2-system-optimization-agent-brief.md` §6）。
> 权威性：**非运行权威**；`AGENTS.md`、`skills/ppt-master/SKILL.md`、`workflows/routing.md`、`workflows/generate-pptx.md` 及各 owning workflow 仍是运行权威。本报告不授权任何修改；Gate G1 未确认前不执行 Phase 1-8。
> 配套：原始数据 `.tmp/system_optimization_baseline.json`（gitignored）、`.tmp/prompt_audit.json`、`.tmp/perf_phase0.json`、`.tmp/hotspots_phase0.json`、`.tmp/smoke_*.txt`、`.tmp/gov_drift.txt`；测量脚本 `.tmp/perf_phase0.py` / `.tmp/hotspots_phase0.py` 可复跑。
> 环境记录：本批测量期间存在用户遗留高负载进程（§4.4），所有耗时数字受其影响；性能对账必须考虑该环境漂移。

---

## 0. 一句话结论

**F1-F10 复核：F1/F2/F4/F5/F6/F7 全部成立**（corpus 425,447 tokens、Generate typical 165,611 tokens、checkpoint/Dashboard 路径漂移、spec_lock 多套解析、audit 治理元数据为空）；F3 性能基线**本次不可复算**——机器存在用户遗留的疑似死循环进程（`.tmp/fix_group_filters.py` ×2，累计 CPU 53,202s / 51,968s），全部耗时测量（导出 p50 9.3s、checker 冷 1.75s）较 2026-08-03 基线慢 2-3 倍，属环境负载而非代码回归；F8/F9/F10 复核成立。**质量侧全绿**：guard / governance drift / prompt audit / smoke 双模式全部 rc=0。

## 1. 环境基线（T0.1）

| 项 | 值 |
|---|---|
| OS | Windows 11 10.0.26200 x64（Git Bash） |
| Python | 3.12.13（uv 托管 cpython-3.12.13-windows-x86_64-none；`python` shim 指向该环境；`python3` 不可用需 `python`） |
| Branch / HEAD | `main` / `bb245d6042145000ad322c04b795c71d7d2587a4`（bb245d60） |
| 最近提交 | bb245d60（governance closeout）→ 55a90be5 → 012400a9 → 3f12628e → 8bab3f01 |
| Dirty worktree | 9 个 M（`.align/lessons.md`、`docs/change-log.md`、`references/executor-base.md`、`scripts/research/asset_gate.py`、`scripts/source_to_md/doc_to_md.py`、`scripts/spec_lock_validate.py`、`scripts/svg_quality/deepppt_extensions.py`、`scripts/visual_review.py`、`workflows/stages/visual-review.md`）+ 5 个 ??（`.align/lessons-2026-08-04*.archive.md` ×2、`plans/deepppt2-system-optimization-agent-brief.md`、`scripts/pptx_render_export.py`、`scripts/svg_geometry_audit.py`）——**均为用户既有改动，本批未触碰** |
| 关键依赖（实测） | python-pptx 1.0.2、Pillow 12.2.0、PyMuPDF 1.27.2.3、Flask 3.1.3、CairoSVG 2.9.0、edge-tts 7.2.8、lxml 6.1.1、requests 2.34.2（完整清单见 `.tmp_pip_freeze.txt` 148 行） |
| 测量依赖变更 | 本批向主 Python 环境**未安装**任何包；prompt_audit 精确计数所需 `tiktoken` 缺失（PEP 668 / uv 托管环境均拒绝直接安装），改在 `.tmp/audit-venv`（一次性 venv）中安装 0.13.0 用于测量，不污染主环境，可随时删除 |

## 2. 质量基线（T0.2）

| 命令 | rc | 结果 |
|---|---|---|
| `attribution_guard.py` | 0 | 通过 |
| `governance_drift_check.py` | 0 | 5 PASS / 0 WARN / 0 FAIL |
| `prompt_audit.py --json` | 0 | **errors=0，warnings=1**（DUPLICATE_NEAR_CANDIDATES：184 个跨文件近重复段落对，见 §3） |
| `smoke_check.py --skip-help` | 0 | **79 passed / 0 failed / 3 skipped / 82 checks** |
| `smoke_check.py`（完整） | 0 | **160 passed / 0 failed / 4 skipped / 164 checks** |

- smoke 基线较 `.align/spec.md` 记录（78/0/3、80 checks；156/0/4、160 checks）多 2 个脚本 4 个 checks：`pptx_render_export.py`、`svg_geometry_audit.py` 为工作区未跟踪新增脚本，smoke 自动 glob 覆盖（+2 checks/脚本，符合 `.align/lessons.md` 规则）。
- prompt_audit 首跑 rc=1（缺 tiktoken）已在测量环境节记录；安装后 rc=0。

## 3. Prompt 基线（T0.3）

**Corpus**（`prompt_audit_manifest.json` documents 口径，o200k_base 编码）：

| 项 | 本次实测 | F1（2026-08 前） | 结论 |
|---|---|---|---|
| 文件数 | 172 | — | — |
| tokens | **425,447** | ~425,447 | 一致 |
| max_tokens（预算） | 430,000 | 430,000 | 余量 4,553 tokens（**1.06%**） |
| errors / warnings | 0 / 1 | 0 | 一致 |

**Load sets**（min/typical/max tokens，全部 status=pass）：

| Load set | min | typical | max | 预算 | scope |
|---|---|---|---|---|---|
| generate | 154,758 | **165,611** | 182,031 | 190,000 | on-demand（含 global） |
| global | 11,686 | 11,686 | 11,686 | 20,000 | always |
| image | 46,967 | 52,671 | 62,742 | 80,000 | on-demand |
| native | 33,961 | 33,961 | 33,961 | 40,000 | on-demand |
| research | 47,486 | 47,486 | 47,486 | 60,000 | on-demand |
| template | 53,418 | 54,695 | 56,674 | 70,000 | on-demand |

- F2 复核：Generate typical **165,611 tokens**，与 Brief 一致。
- coverage：172 文档 / 171 covered / 1 exempt（`scripts/pptx_shapes/data/NOTICE.md`，上游署名声明）/ uncovered 0。
- duplicates：exact=0、exact_accepted=22（全部带 reason，分布在共享契约表/模板 roster/自动生成 manifest 头三类）、near=100（展示上限）、near_accepted=0 → findings 1 条 warning（184 对）。
- **F7 复核成立**：manifest 中 `authority_edges: []`、`registries: []`、`schema_grammars: []` 全部为空；`references.edges` 为自动提取的 579 条链接（48 条 authority_candidate=True），load_sets 各 selector 的 `load_event` / `registry` 字段均为空字符串。
- **T3.5 基础已部分具备**：22 条 accepted 全部有具体理由；无失效豁免。

## 4. 性能基线（T0.4）

### 4.1 方法

同 2026-08-03 基线口径：`time.perf_counter()`；冷 = 独立子进程；暖 = 同进程（`try: main() except SystemExit`）；p50/p95 = nearest-rank。Fixture：`examples/ppt169_kubernetes_blueprint_2026`（10 页）与 `examples/ppt169_swiss_grid_systems`（10 页）复制至 `.tmp/fixture_kubernetes` / `.tmp/fixture_swiss`（**不触碰 examples/ 原件**）。

### 4.2 实测（n、p50、p95）

| 测量项 | n | p50 | p95 | 2026-08-03 基线 | 变化 |
|---|---|---|---|---|---|
| 解释器冷启动 `python -c pass` | 10 | 69.4 ms | 90.7 ms | 56.8 / 81.8 ms | +22% |
| 冷导入 `svg_quality` | 10 | 71.5 ms | 106.0 ms | 61.6 / 77.6 ms | +16% |
| 冷导入 `svg_to_pptx` | 10 | 107.9 ms | 124.1 ms | 98.5 / 116.8 ms | +10% |
| 冷导入 `dashboard.server` | 10 | 670.6 ms | 705.7 ms | 473.2 / 556.0 ms | +42% |
| 冷导入 `confirm_ui.server` | 10 | 660.9 ms | 714.9 ms | 445.9 / 480.7 ms | +48% |
| `os.walk` 全仓 | 10 | 811.5 ms | 1,511.1 ms | 369.4 / 424.9 ms | +120%（含 .tmp 1,604 文件；仓库本体 20,443 文件） |
| `svg_quality_checker` 冷（kubernetes） | 10 | 1,753.7 ms | 1,883.8 ms | 1,333.9 / 1,433.2 ms | +31%（rc=0 ×10，旧基线 rc=1） |
| `svg_quality_checker` 暖 | 5 | 931.3 ms | 1,075.5 ms | 374.4 / 386.1 ms | +149% |
| `dashboard --daemon` 启动 | 5 | 2,158.8 ms | 2,185.6 ms | — | — |
| dashboard 首次 HTTP | 5 | 117.7 ms | 130.6 ms | — | — |
| dashboard 启动+HTTP 合计 | 5 | 2,275.4 ms | 2,448.1 ms | 1,861.8 / 2,106.8 ms | +22% |
| `svg_to_pptx` 导出（swiss 10 页） | 3+5 | 9,342 ms（重测 n=5） | 10,254 ms | 3,724 / 4,052 ms | **+151%**（rc=0 全过） |
| `finalize_svg` 冷（kubernetes） | 3 | 560.3 ms | 605.5 ms | 482.2 / 516.2 ms | +16%（rc=0 ×3） |

### 4.3 与旧基线对比的结论

- 全部测量项同向变慢（+10% ~ +151%），且**系统化**（解释器冷启动本身 +22%）。这类全局漂移指向环境因素而非代码变化。
- 质量侧行为变好：kubernetes checker 由旧基线 rc=1（既有 ERROR）变为 rc=0 ×10（对应 2026-08-03 已完成的 29/29 修复，非本批改动）。
- 导出 p50 9.3s 为稳定值（重测 n=5 全 rc=0），与旧基线 3.7s 差 2.5 倍。

### 4.4 ⚠️ 环境负载异常（重要发现）

测量期间机器 CPU 负载 79%。查得两个 python 进程长期占用 CPU：

| PID | 命令 | 累计 CPU |
|---|---|---|
| 53080 | `python.exe .tmp/fix_group_filters.py --dry` | 53,202s |
| 50380 | `python.exe .tmp/fix_group_filters.py` | 51,968s |

- 这两个进程是**用户遗留**（非本会话启动，命令位于 `.tmp/`，疑似行插入式批量修复脚本死循环——与 `.align/lessons.md`「行插入式修复的死循环」条目高度吻合）。
- **影响**：本次全部耗时数字受其持续争抢 CPU 影响，**不能与 2026-08-03 基线直接对账**；数字已如实保留（§4.5 干净环境复测作废并替代之）。
- **处置**：已随 Gate G1 批准终止（§4.6）；复测结果见 §4.5。

### 4.5 干净环境复测（2026-08-04，用户批准终止遗留进程后）

Gate G1 确认后，按推荐终止 `.tmp/fix_group_filters.py` ×2（`taskkill`，CPU 负载 79% → 2%），重建干净 fixture 副本（`.tmp/fixture_k8s_clean` / `.tmp/fixture_swiss_clean`）复测代表性项：

| 测量项 | n | 脏环境 p50 | **干净环境 p50/p95** | 2026-08-03 基线 | 干净 vs 旧基线 |
|---|---|---|---|---|---|
| 解释器冷启动 | 10 | 69.4 ms | **46.2 / 50.8 ms** | 56.8 / 81.8 ms | **-19%** |
| `svg_quality_checker` 冷（kubernetes） | 10 | 1,753.7 ms | **1,410.8 / 1,511.4 ms**（rc=0 ×10） | 1,333.9 / 1,433.2 ms | **+6%**（阈值内） |
| `svg_to_pptx` 导出（swiss 10 页） | 5 | 9,342 ms | **4,164.3 / 5,363.0 ms**（rc=0 ×5） | 3,724 / 4,052 ms | **+12%** |
| `os.walk` 全仓 | 10 | 811.5 ms | **661.1 / 730.3 ms** | 369.4 / 424.9 ms | **+79%**（待观察） |

**结论**：干净环境下代表性项与 2026-08-03 基线一致（-19% ~ +12%）；§4.2 的脏环境数字作废。残余差异（导出 +12%、os.walk +79%）无代码变更支撑，属系统缓存 / Defender 扫描状态等环境差异；os.walk +79% 单列待观察（文件数反而减少 24,203→22,784，需后续 profiling 才可归因）。原始数据 `.tmp/perf_retest.json`。

### 4.6 遗留进程处置记录

| 项 | 值 |
|---|---|
| PID / 命令 | 53080（`.tmp/fix_group_filters.py --dry`）、50380（`.tmp/fix_group_filters.py`） |
| 累计 CPU（终止前） | 53,578s / 52,344s，启动于 2026-08-03 21:04 / 21:25 |
| 处置 | 用户 Gate G1 批准后 `taskkill /F` 终止（2026-08-04）；CPU 负载 79% → 2% |
| 性质判断 | 疑似行插入式批量修复死循环（`.align/lessons.md` 同款教训）；`.tmp/` 下脚本未入库，无回滚面 |

## 5. 契约矩阵（T0.5）

### 5.1 Pipeline state（当前步骤推断）

| 事实 owner（实现） | 推断方式 | 已知消费者 |
|---|---|---|
| `project_manager.py::checkpoint_save/load`（L1003） | 按 artifact 存在性推断 8 档 step（1-init … 8-export） | 仅 `project_manager.py` 自身（`checkpoint` 子命令） |
| `dashboard/state_reader.py::read_pipeline_state`（L676） | 独立再推断一套步骤（含 spec_lock 解析 `_parse_spec_lock` L234） | dashboard server / bridge / watcher |
| `workflows/generate-pptx.md` Steps 1-8 + checkpoints | 文档级阶段事实 | Agent 编排（运行权威） |

**F4 复核成立**：三套独立推断并存（checkpoint / state_reader / workflow 文档），无 canonical `derive_pipeline_state`。

### 5.2 Artifact 路径

| 路径事实 | Dashboard（`artifact_registry.py`） | checkpoint（`project_manager.py`） | 状态 |
|---|---|---|---|
| 导出 PPTX | `latest_pptx`（L304）只认 `exports/*.pptx` | `has_pptx = any(p.glob("*.pptx"))`（L1026）只认项目根 `*.pptx` | **F5 漂移成立：已导出项目会被 checkpoint 判为 `7c-export` 而非 `8-export`** |
| svg_output / svg_final / notes / images | `iter_artifact_files`（L237）+ `_artifact_type`（L71）统一路径表 | 独立 glob | 两套路径表，未共用 |

### 5.3 spec_lock.md（F6 复核成立）

直接读取 `spec_lock.md` 的脚本 **25 个**（另有 6 个间接引用）：`confirm_ui_gate.py`、`consulting_content_lock.py`、`dashboard/{artifact_registry,layout_preview,state_reader,watcher}.py`、`e2e_validate.py`、`latex_render.py`、`layout_capacity_check.py`、`project_manager.py`、`smoke_check.py`、`spec_compliance_check.py`、`spec_lock_digest.py`、`spec_lock_validate.py`、`svg_quality/{checker,cli,deepppt_extensions}.py`、`svg_to_pptx/drawingml/{context,theme_colors,theme_fonts}.py`、`svg_to_pptx/pptx_package/{cli,template_structure}.py`、`update_spec.py`、`vision_backends/backend_common.py`。无单一 canonical parser；`dashboard/state_reader.py::_parse_spec_lock`、`svg_quality/checker.py`、`spec_lock_validate.py`、`e2e_validate.py` 各自实现解析（>4 套局部逻辑，对应 Brief T2.2「禁止另写第五套」的边界）。

### 5.4 Confirm result.json

- **schema owner 明确**：`scripts/docs/confirm_ui.md`（「Confirm UI schema | This document」）。
- 消费者：`confirm_ui/server.py`（写入）、`confirm_ui_gate.py`（门禁）、`dashboard/{bridge,state_reader,watcher}.py`、`memory_manager.py`。
- 现状：schema 集中在 server + 文档；gate 与 dashboard 读同一 `result.json`。**无显式 schema_version 字段**（T2.7 待办候选）。

### 5.5 Quality / trace

| 事实 | owner | 备注 |
|---|---|---|
| `trace.jsonl`（dashboard 事件） | `dashboard/trace_writer.py`（append，无显式 schema version）+ `trace_store.py`（读/过滤） | harness_gate 等写事件；事件 envelope 未版本化（T5.2 候选） |
| conversion trace `<输出>.pptx.trace.json`（`--conversion-trace`） | `svg_to_pptx/pptx_package/{builder,cli}.py` 等 | **第二套 trace**，路径/flag 与 dashboard 不同（`.align/lessons.md` 已记录） |
| 质量报告 | `svg_quality`（`validation/svg_quality_report.json`）、`rendered_layout_check`（`quality/rendered_visual_gate.json`）、`pptx_quality_check`（`--json-out`） | 各报告 schema 无统一版本声明（T2.9 候选） |

## 6. 代码热点矩阵（T0.6）

249 个 `.py`、总 LOC 134,938。**不按 LOC 单独排名**；综合 LOC / churn（git log 全史）/ fan-in / fan-out：

| 文件 | LOC | churn | fan_in | fan_out | 备注（职责面） |
|---|---|---|---|---|---|
| `svg_quality/checker.py` | 7,099 | 1 | 4 | 25 | Brief 候选①；v4.3.0 迁移单次重写（churn=1 系 git 历史被 reorg 合并），职责：SVG 结构/禁令/drift 检查多合一 |
| `svg_to_pptx/pptx_package/builder.py` | 6,044 | 1 | 1 | 36 | Brief 候选②；PPTX 构建主装配 |
| `svg_to_pptx/drawingml/elements.py` | 5,026 | 1 | 1 | 24 | Brief 候选③；DrawingML 元素库 |
| `pptx_animations.py` | 3,932 | 18 | 12 | 15 | Brief 候选④；动画（迁移后并入 native 副本，双路线消费者） |
| `svg_to_pptx/drawingml/utils.py` | 3,459 | 1 | 7 | 12 | 高 fan_in |
| `svg_to_pptx/pptx_package/template_structure.py` | 3,456 | 1 | 3 | 16 | structured 模板结构 |
| `pptx_transitions.py` | 2,769 | 1 | 20 | 11 | fan_in 最高档 |
| `native_enhance_pptx_core.py` | 2,490 | 2 | 4 | 22 | Brief 候选⑥；Enhance 路线核心 |
| `confirm_ui/server.py` | 2,230 | 13 | 0 | 22 | Brief 候选⑥；churn 高 |
| `svg_to_pptx/pptx_package/cli.py` | 2,142 | 1 | 1 | 29 | 导出 CLI |
| `narration_sync.py` | 1,938 | 2 | 0 | 23 | Brief 候选⑦ |
| `prompt_audit.py` | 1,858 | 1 | 0 | 15 | Brief 候选⑧ |
| `project_manager.py` | 1,319 | **31** | 2 | 16 | churn 全仓最高；checkpoint 漂移 owner |
| `image_gen.py` | 1,527 | 23 | 0 | 17 | churn 第二 |
| `svg_editor/server.py` | 1,194 | 19 | 0 | 22 | churn 第三 |

缺陷/教训映射（`.align/lessons.md` + 历史报告）：checker（emoji 禁区、checker/e2e 契约面差异、`spec_lock mode` 跨节误读、懒加载负优化 +25% 已回退）、导出器（tspan_flattener 配套、spec_lock 主题契约硬门、trace 路径变化、整包替换调用面）、`pptx_animations`（上游严格校验器 vs 组动画冲突）、`narration_sync`（`--recorded-narration` 默认查找位置）、`prompt_audit`（load-set selector 契约、BUDGET_CORPUS 不受 exempt 影响、`--json` 键名）、`project_manager`（新项目缺完整 spec_lock 契约）。

Brief §12.1 初始候选 8 个模块全部位于 LOC/churn 双高区；按评分维度（churn 1 的迁移重写文件以 LOC + fan-out + 职责数见长），`checker.py` / `builder.py` / `elements.py` 达到「可进入 characterization」门槛（≥7 分需逐项核验后由用户批准，本报告仅列观察）。

## 7. Fixture 集（T0.7）

| Fixture | 类型 | 覆盖契约 |
|---|---|---|
| `examples/ppt169_swiss_grid_systems`（14 SVG，flat，charts=True，checker+e2e 双门绿，导出 rc=0） | 主 Generate flat 典型 | spec_lock flat 模式、svg_quality、finalize、svg_to_pptx 导出、e2e |
| `examples/ppt169_kubernetes_blueprint_2026`（10 SVG，flat，0 图，charts=True） | 纯图表 deck | page_charts / verify-charts 边界；曾导出 traceback 的历史回归靶子（已修复）；性能 fixture |
| `examples/ppt169_ai_image_guide_ppt169_20260622`（15 SVG，24 图，instructional，charts=True） | 图片密集 + 非 flat 叙事 | 图片链路（analyze/images manifest）、非 flat mode、资产门 |
| `templates/decks/中国电信`（deck 模板工作区） | structured 契约（文档级） | `pptx_structure.mode: structured` 的契约声明（`references/semantic-svg.md` / `pptx-structure-interface.md`）——**仓库无项目级 structured fixture**，如 Phase 1-8 需要须合成（`_agent_` 前缀）或经用户批准 |

**如实标注**：template-fill / beautify 路线在 examples/ 与 projects/ 均无现成公开 fixture（其输入是用户自有 PPTX）；structured 模式无实战项目。这些路线的契约回归（Brief T1.7/T4.3）需要合成 fixture，属 Phase 4 待用户确认项。

## 8. 排除项（T0.8）

**已关闭任务（2026-08-03 治理完成，禁止重做）**：全仓盘点（`deep-ppt-repository-inventory-2026-08.md`）；examples 29/29 checker + e2e 双门修复；CI #12/#13 全绿；prompt audit manifest 治理（7 load_sets + 22 accepted + coverage 闭合，`55a90be5` 已提交）；动画双文件合并；`.align` 事实刷新；projects/ backup 清理（5.73→4.8 GB）；`.codex` 清理（261 MB→5 KB）；Dashboard 产物展台化；Pages workflow 精简；README 刷新；性能基线初版（`perf-baseline-2026-08.md`）；懒加载 import 实验（已回退，方向关闭——Brief §13.1 Known constraint）。

**非目标（Brief §4.2 + roadmap F10）**：新增 PPT 功能/模板/图表/动画/Provider；产品形态改造（SaaS/桌面/微服务）；整体转 Python package；重写 examples/、清理 projects/、删除历史产物；纯速度优化（roadmap 仅把 Prompt slimming 列为长期方向）。

## 9. 发现与 Gate G1 提交

Phase 0 完成，停止于 Gate G1。向用户提交：

### 9.1 前五个最高收益问题（草案，待用户确认）

1. **checkpoint 与 Dashboard 的导出路径/状态漂移**（F5，§5.2）：checkpoint 认项目根 `*.pptx`、Dashboard 认 `exports/*.pptx` → 已导出项目状态判定不一致。风险低、改动小（收敛到 `project_utils` / canonical accessor，T1.2-T1.5）、回滚 = 恢复 checkpoint 读取逻辑。证据：`project_manager.py:1026` vs `artifact_registry.py:304`。
2. **spec_lock 25 个直接消费者 + ≥4 套局部解析**（F6，§5.3）：任何字段语义调整（如 2026-08-03 的 `mode` 跨节误读缺陷）都要逐一核对全部消费者。收益 = 单点修改；风险中（T2.2-T2.5 需兼容 wrapper）；回滚 = 保留旧解析入口。
3. **Prompt corpus 预算余量仅 1.06%（4,553/430,000 tokens）**（§3）：新文档/新模板/新 workflow 必然突破；generate typical 165,611 距预算 190,000 尚有 15%（但 global 11,686 为 always-load 恒定成本）。收益 = 可扩展性 + 上下文效率（T3.x）；风险低（audit-only，不触碰运行文件）。
4. **trace 两套并存且无 schema 版本**（§5.5）：`trace.jsonl`（dashboard）与 `<pptx>.trace.json`（conversion trace）格式/路径/flag 各异。收益 = 可观测性一致（T5.1-T5.2）；风险低。
5. **prompt audit 治理元数据全空**（F7，§3）：`authority_edges`/`registries`/`schema_grammars` 均为 []，selector `load_event`/`registry` 全空 → 按需加载只有 token 模拟、无真实路由依据（T3.1-T3.4）。风险低。

### 9.2 环境遗留（已随 G1 确认处置完毕）

- ✅ `.tmp/fix_group_filters.py` ×2 疑似死循环进程——已终止（§4.6），性能复测完成（§4.5，与旧基线一致）。
- ⏳ `.tmp/audit-venv`（一次性 tiktoken 测量环境）——保留至 Phase 3（prompt audit 复测仍需使用），后续清理。

### 9.3 建议纳入 Phase 1-8 的任务 / 建议取消的任务

- **建议纳入（高收益低风险）**：T1.2-T1.5（canonical state/artifact accessors + checkpoint 收敛）、T2.2-T2.4（canonical spec_lock parser + 字段语义）、T3.1-T3.5（authority_edges/registries/schema_grammars + accepted duplicates 处置）、T5.1-T5.5（trace envelope 统一）、T7.1-T7.2（依赖分类 + Provider 懒导入复核）。
- **建议取消或延后**：Phase 6 对 `svg_quality/checker.py` / `svg_to_pptx/pptx_package/builder.py` / `drawingml/elements.py` 的结构拆分——三者 churn=1（迁移单次重写）且为导出/检查核心，无重复缺陷面，评分需逐项核验（≥9 才可拆），当前无证据支持拆分；`prompt_audit.py` 无拆分必要（fan_in=0）。Phase 4 的 structured/template-fill/beautify fixture 需先合成 fixture（无现成公开 fixture），纳入需用户确认成本。
- **未列入任何 Phase**：性能优化仅保留「有 Phase 0/5 数据证明的瓶颈」；本次因环境异常无干净性能基线，**不建议**在复测前启动任何性能批次。

### 9.4 指标与授权推荐（默认值，待用户确认）

| 项 | 推荐 |
|---|---|
| Prompt 缩减目标 | Generate typical 165,611 → ≤132,489（-20%），以 Phase 0 复测（干净环境）为分母；不通过提高 max_tokens / 扩大 exempt / 漏登记文档达成 |
| 性能回归阈值 | 复测干净基线后：代表性流程 p50/p95 变慢 >10% 视为回归（同 Brief §13.1 默认）；低于 10% 且无维护性收益不保留 |
| 模型 A/B 授权 | **暂不授权**：Phase 3 验证先走静态 audit + 本地 fixture（无需付费调用）；实际付费 A/B 待 G2 单独提交样本数/成本/停止条件 |

---

## 10. 附注

- `.tmp/` 中 `_agent_page_expression_ab_20260718`、`_agent_page_expression_phase2_20260719` 为既往会话残留（`perf-baseline-2026-08.md` §4 已记录，未动）。
- 本批测量产生的 `.tmp/fixture_kubernetes` / `.tmp/fixture_swiss` 副本及其导出文件均在 `.tmp/` 内，`examples/` 原件未被修改（可 `git status examples/` 复核）。
- `docs/reviews/` 新增报告不写 `docs/change-log.md`（按 `.align/lessons.md` 惯例：change-log 只记脚本/工作流/路由变更）。
- 当前 git status 与本批产物：`docs/reviews/deepppt2-system-optimization-baseline-2026-08.md`（新增，未提交）+ `.tmp/` 原始数据（gitignored）；未 commit、未 push。
