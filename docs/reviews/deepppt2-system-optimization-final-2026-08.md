# DeepPPT2 系统优化最终报告（2026-08-04）

> 状态：Phase 0-8 全部完成（`plans/deepppt2-system-optimization-agent-brief.md` 执行收口）。
> 权威性：**非运行权威**；`AGENTS.md`、`skills/ppt-master/SKILL.md`、`workflows/routing.md`、`workflows/generate-pptx.md` 及各 owning workflow 仍是运行权威。
> 配套：基线报告 `docs/reviews/deepppt2-system-optimization-baseline-2026-08.md`；原始数据 `.tmp/system_optimization_baseline.json`、`.tmp/audit_final.json` 等（gitignored）。

---

## 1. 修改范围与未修改范围

### 已修改（全部经 change-log 记录，8 条）

| 类别 | 文件 |
|---|---|
| 新增（canonical 层） | `scripts/spec_lock_reader.py`、`scripts/animation_constants.py`、`scripts/animation_effects.py`、`scripts/docs/trace-contract.md` |
| 状态单一事实源（Phase 1） | `scripts/project_utils.py`、`scripts/project_manager.py`、`scripts/dashboard/artifact_registry.py` |
| spec_lock parser 收敛（Phase 2） | `scripts/update_spec.py`、`scripts/e2e_validate.py`、`scripts/layout_capacity_check.py`、`scripts/svg_quality/checker.py` |
| 契约测试（Phase 2/4） | `scripts/smoke_check.py`（Test 7/8/9，+11 断言） |
| Prompt 治理（Phase 3） | `scripts/prompt_audit_manifest.json`、`references/shared-standards.md`（+1 指针行） |
| 可观测性（Phase 5） | `scripts/dashboard/trace_writer.py` |
| CLI 卫生（Phase 7） | 10 个入口脚本（`raise SystemExit(main())`） |
| 文档 | `scripts/docs/confirm_ui.md`（schema contract）、`docs/reviews/deepppt2-system-optimization-baseline-2026-08.md`、`docs/change-log.md` |

### 未修改

- **硬纪律文件**：`SKILL.md`、`workflows/routing.md`、`workflows/generate-pptx.md`、`references/executor-base.md`（内容零改动；executor-base 的 32 行为用户既有改动，本批未触碰）
- `examples/`、`projects/`（演练产物在 `.tmp/ab/`，gitignored）
- `.github/workflows/`（CI 未改——T4.7 评估完成，改动需另行批准）
- 用户既有 dirty worktree（9 M + 5 ??）全程未触碰

## 2. 每 Phase 状态与执行回执

| Phase | 状态 | 核心交付 | 回执 |
|---|---|---|---|
| 0 | ✅ | 基线报告 + 五问题 + 干净环境复测 | 基线报告 §0-§9 |
| 1 | ✅ | canonical accessors + `derive_pipeline_state` + F5 修复（exports/*.pptx → 8-export） | 会话回执 |
| 2 | ✅ | `spec_lock_reader.py` 单一 owner + JSON 契约 + Test 8/9 | 会话回执 |
| 3 | ✅ | 治理元数据（9 边/6 registry/2 grammar/13 load_event）+ generate-on-demand set，typical **-21.4%** | 会话回执 |
| 4 | ✅ | CLI 错误路径 0 静默 + gate 状态场景 + 双门全量 | 会话回执 |
| G2 | ✅ | 3 份固定 Brief 全链路演练 3/3（harness PASS + e2e 7/7） | 会话回执 |
| 5 | ✅ | trace envelope v1 + 契约文档 + null/0 语义 | 会话回执 |
| 6 | ✅ | pptx_animations 拆分（characterization 18 keys 0 diffs） | 会话回执 |
| 7 | ✅ | 入口统一 + 依赖/Provider/凭据复核 | 会话回执 |
| 8 | ✅ | 链接 0 真断链 + 四门全绿 + 双门最终态 + 本报告 | 本报告 |

## 3. 前后对比

| 指标 | Phase 0 基线 | 最终 | 变化 |
|---|---|---|---|
| Prompt corpus tokens | 425,447 | 426,574 | +1,127（契约文档化 confirm_ui/trace-contract） |
| **Generate typical tokens** | **165,662** | **130,192** | **-21.4%（目标 -20% ✓）** |
| prompt_audit errors | 0 | 0 | —（warnings 8 全部有处置记录） |
| governance drift | 5 PASS | 5 PASS | — |
| attribution guard | rc=0 | rc=0 | — |
| smoke 完整 | 160/0/4/164 | 166/0/4/170 | +6 checks（新脚本） |
| smoke --skip-help | 79/0/3/82 | 80/0/3/83 | +1 |
| smoke --integration | 170/0/4/174 | 187/0/4/191 | **+17 断言**（Test 7/8/9 + 新模块） |
| examples checker | 29/29 | 29/29 | —（0 回归） |
| examples e2e | 29/29 | 29/29 | —（0 回归） |
| 性能（干净环境） | 导出 4.2s / checker 冷 1.4s / dashboard 2.3s | 同基线 | 无性能批次（无热点） |
| CLI 错误路径静默 | 未测 | 65 入口 0 静默 + 12 缺文件 0 静默 | 新覆盖 |
| 质量门回归 | — | Test 7（状态链）+ Test 8/9（gate 13 场景） | 新覆盖 |
| CI | 3 job（smoke/svg-quality/e2e） | 未改（评估完成，`--integration` 可加待批准） | — |

## 4. Public CLI / artifact / schema 兼容性说明

- **CLI**：无参数/输出/退出码变化（10 个入口 `raise SystemExit(main())` 行为等价——main 均返回 None）
- **Artifact**：`.checkpoint.json` schema 不变；`spec_lock.md` 文件格式不变（reader 收敛到单一 owner）；`trace.jsonl` 事件新增字段（旧事件兼容）；`result.json` 无新必填字段
- **Schema**：page_expression 契约（schema_version/owner/pages-by-id + 6 字段 + content_relation/anchor + SVG lead/subtitle 组）经 G2 演练实证；spec_lock flat 模式禁 page_layouts 节

## 5. 剩余风险、关闭原因与后续观察项

| 风险 | 状态 | 说明 |
|---|---|---|
| checker anchor 检查未激活 | 旗标后待决 | `_ANCHOR_COMPARE_ENABLED=False`；激活会暴露 240+ legacy 漂移，需用户决策（先修 examples 或调整语义） |
| checker image-lock 检查禁用 | 记录 | `_parse_spec_lock_image_value` 幽灵契约（path/source/pattern/crop/legacy 五字段）需专门设计 |
| quality/validation/analysis 报告写侧未统一 | 记录 | 读侧已收敛 `find_quality_report`；写侧属 T2.9 边界 |
| conversion trace 未入统一 envelope | 记录 | 导出器内部契约，保持独立 |
| CI 未加 --integration/prompt_audit | 待批准 | 本地等价命令稳定（187 checks）；prompt_audit 需 tiktoken |
| 用户修订次数指标未采集 | 记录 | 无 artifact 承载；不伪造默认值（T5.6） |
| 演练产物 `.tmp/ab/` | 保留 | 3 份 deck 供用户检查；gitignored |

## 6. 新增依赖、删除/移动文件和回滚说明

- **新增依赖**：无（tiktoken 仅 `.tmp/audit-venv` 测量环境，不进 requirements）
- **新增文件**：spec_lock_reader.py / animation_constants.py / animation_effects.py / trace-contract.md / 基线报告 / 最终报告
- **删除/移动**：无删除；`pptx_animations.py` 内容重组（公开面完整保留）；`06_reference.svg`（仅演练 fixture，非仓库文件）
- **回滚**：全部变更可 `git checkout` 本批文件回滚；manifest/change-log 为数据/文档变更；无迁移性破坏（兼容性见 §4）

## 7. 当前 git status

- 工作区：9 个 M + 5 个 ??（用户既有改动）+ 本批改动（未 commit——按 Brief 约定，**不自动 commit/push**）
- 本批新增未跟踪：`docs/reviews/deepppt2-system-optimization-baseline-2026-08.md`、`docs/reviews/deepppt2-system-optimization-final-2026-08.md`、`scripts/spec_lock_reader.py`、`scripts/animation_constants.py`、`scripts/animation_effects.py`、`scripts/docs/trace-contract.md`、`scripts/pptx_render_export.py`（用户）、`scripts/svg_geometry_audit.py`（用户）
- `.tmp/` 全 gitignored（audit-venv、ab 演练、char_anim、perf 数据）
- 无遗留服务进程（全部 dashboard/shutdown 已验证）

---

## 附：Definition of Done 核对

- [x] Phase 0 基线可复跑（.tmp 原始数据 + 脚本）
- [x] Artifact 路径和 pipeline state 单一事实源（derive_pipeline_state + canonical accessors）
- [x] spec_lock/JSON artifacts 有 owner、统一 parser/schema、legacy 策略
- [x] Prompt authority graph/registries/schema_grammars/load_event 启用，audit 0 error
- [x] Prompt 缩减目标达成（-21.4% ≥ -20%），硬约束与代表性输出质量无回归（G2 演练 3/3）
- [x] 高风险契约有 fixture（Test 7/8/9）；CLI 错误路径非零（0 静默）
- [x] 代码重构由热点评分 + characterization 支持（仅 pptx_animations 拆分，0 diffs）
- [x] 性能无变更批次（无热点，基线健康）
- [x] Guard/governance/prompt_audit/完整 smoke 全部通过
- [x] examples checker + e2e 双门 29/29
- [x] 文档权威层级、链接（0 真断链）和 change-log 一致
- [x] 无未授权删除、依赖、外部调用、commit、push
- [x] 无遗留临时项目/服务（`.tmp/ab` 演练产物保留供检查，gitignored）
- [x] 最终报告列出修改、未修改、风险、回滚和后续观察项
