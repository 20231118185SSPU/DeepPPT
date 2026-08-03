# DeepPPT2 仓库事实盘点与治理边界报告（2026-08）

> 状态：只读审计报告（Phase 0/1 完成产物，2026-08-03 实测；§0.1 追加「治理后当前快照」）。
> 权威性：非运行规则；`AGENTS.md`、`skills/ppt-master/SKILL.md`、`workflows/routing.md`、`workflows/generate-pptx.md` 及各 owning workflow 仍是运行权威。本文档不覆盖它们，也不替代 `plans/deep-ppt-reorganization-contract.md` 的执行约束。  
> 范围：全仓 24,197 个文件（不含 `.git`）；`projects/` 只盘点不处理；`examples/` 只盘点不定位变更。  
> 标注约定：`[原文]` = 文件/命令/实测直接证据；`[推断]` = 基于证据的合理推论；`[待验证]` = 当前无法确认，需后续动作验证。所有路径、命令、字段名保留英文。

---

## 0. 总体结论

一句话判断：仓库处于「v4.3.0 大迁移刚完成、结构健康但元数据滞后」的状态——**代码与文档层健康度高**（smoke 全绿、链接 0 断链、81 个入口脚本零孤儿、gitignore 卫生良好、工作区干净），**体量与冗余集中在用户工作区与工具状态层**（`projects/` 5.3 GiB 含大量 backup 快照与多版本导出，`.codex/` 261 MB 工具状态，`examples/` 与 `projects/` 同源重复约 656 组）。

三个关键事实与用户 Brief 的对账结论：

1. **规模对账通过**：24,193（Brief）≈ 24,197（实测，+4 为本会话临时文件）；7.24 GB（GiB 口径）一致；Git 跟踪 14,534 一致；`projects/` 33 个、`examples/` 29 个一致；scripts 81 入口 / 248 py 一致。
2. **smoke 基线确认**：`--skip-help` 模式 78 passed / 0 failed / 3 skipped / 81 checks（与 Brief 完全一致）；完整模式 158 / 0 / 4 / 162 checks（与 `plans/followup-migration-roadmap.md` Phase 6 记录一致）。
3. **事实源已漂移**：`.align/spec.md` 声明「无自动化测试，无 CI 流水线」[原文]，但 `.github/workflows/ci.yml` + `deploy-pages.yml` 已存在且活跃 [原文]；`.align` 中 smoke 基线（38/41）与脚本数量也过期。漂移差异清单见 §5。→ **2026-08-03 已刷新（独立获批），见 §0.1 快照**。

## 0.1 治理后当前快照（2026-08-03 晚，追加）

> 原始 Phase 0/1 盘点基线（§1-§9）保留为只读快照；本表为本会话全部治理动作完成后的事实增量，供后续对账。执行记录详见 `plans/deep-ppt-reorganization-contract.md` §10。

| 项 | 治理前（本报告基线） | 治理后（2026-08-03 实测） |
|---|---|---|
| examples 质量门 | 29/29 checker rc=1（CI push 必红风险） | checker **29/29** + e2e **29/29** 双门全绿；CI #12/#13 连续全绿（smoke 16m52s / svg-quality 21m26s / e2e 1m38s） |
| 迁移提交 | `31298372` 未 push（ahead 1） | 已 push，重新标记为**迁移基线提交** |
| `plans/followup-migration-roadmap.md` | 计划形态（R2） | 已归档（头部状态标记，正文保留执行记录） |
| `pptx_animations` / `native_pptx_animations` | 双文件并存（R1） | 已合并（方案 A：删 native 副本，3 处 import 切换，gate 清单更新） |
| `.align` 事实 | spec/context 过期（R3） | 已刷新（spec 4 处 + context 1 处，保持 `[原文]` 标注） |
| `projects/` 体积 | 5,733.7 MB | ≈4.8 GB（34 个旧 backup 快照 ~0.9 GB 已清，`projects/README.md` 新增 Lifecycle Governance） |
| `.codex/` | 261.5 MB（R6） | 5 KB（dashboard 缓存已清，config.toml 保留） |
| Dashboard | 全流程展示 | 产物展台（四阶段导航 + research 类型 + `artifacts_index.json` 本地搜找） |
| GitHub Pages | 3 个 workflow | 仅 `deploy-pages.yml`（static.yml / jekyll-gh-pages.yml 已删）；Pages 生效 |
| prompt audit manifest | 空 load_sets（173 errors） | 7 个真实 load_sets + 1 exempt + 22 exact 重复 accepted；**rc=0 / errors=0 / coverage 172 闭合**（未 commit，待批准） |

## 1. 事实盘点（可对账口径）

### 1.1 全仓总量

| 指标 | 数值 | 证据 |
|---|---|---|
| 文件总数（不含 `.git`） | 24,197 | `os.walk` 实测（Brief 24,193，+4 为本会话 `.tmp/` 产物） |
| 总字节 | 7.78 GB（decimal）= 7.24 GiB | 实测 |
| Git 跟踪（tracked） | 14,534 | `git ls-files -z` |
| 未跟踪（untracked） | 0 | `git status --porcelain -uall -z`；工作区干净 |
| 被忽略（ignored） | 9,663 | `git check-ignore --stdin -z` 实测 |
| tracked 且匹配 ignore 规则 | 0 | `git ls-files \| git check-ignore`（gitignore 卫生良好） |

> `[原文]` 注意：中文文件名路径在 `git ls-files` 默认输出中被 `core.quotepath` 转义为八进制（如 `examples/kalsit_deep_ppt169_20260621/images/amiya_avatar_\351\227\277…png`，共 336 个文件），与 `os.walk` 的 Unicode 路径比对会失配；必须用 `-z` 参数取未转义路径。这是本报告分类对账的已知坑（已沉淀至 `.align/lessons.md`）。

### 1.2 顶层目录职责与跟踪状态

| 顶层目录 | 文件数 | 体积 | tracked | ignored | 类别 | 职责 |
|---|---|---|---|---|---|---|
| `skills/` | 12,889 | 78.9 MB | 12,407 | 482 | public 源码 | ppt-master 技能包（scripts/workflows/references/templates）；482 ignored 为 `__pycache__` `.pyc` `[原文]` |
| `projects/` | 6,000 | 5,733.7 MB | 1（README.md） | 5,999 | runtime-state 用户工作区 | 33 个进行中项目；全 ignored |
| `examples/` | 2,016 | 1,653.8 MB | 2,016 | 0 | public 回归基线 | 29 个示例项目；CI/Pages 引用 |
| `.codex/` | 2,783 | 261.5 MB | 0 | 2,783 | runtime-state 工具 | Codex 客户端状态（含 2×36.8MB tflite 模型） |
| `docs/` | 60 | 33.5 MB | 60 | 0 | public | 用户文档 + reviews/rules/zh；大头为 `docs/assets/hero-liziqi-colors.gif` 19.8 MB |
| `.tmp/` | 375 | 14.9 MB | 0 | 375 | runtime-state 临时 | 本会话测量数据 + 既往实验产物 |
| `.align/` | 27 | <0.1 MB | 9 | 18 | 治理 | spec/context/lessons/route.conf 等 9 tracked；18 ignored 为 `.align/.runtime/` 生命周期回执 |
| `.github/` | 7 | <0.1 MB | 7 | 0 | public 配置 | workflows/ci.yml + deploy-pages.yml + ISSUE_TEMPLATE 等 |
| 根 `scripts/` | 7 | <0.1 MB | 6 | 1 | public | hermes-chrome 启动脚本 + `setup/`；`.hermes-chrome.env` ignored |
| 根文件 | 19 | 0.2 MB | 19 | 0 | public | AGENTS.md / README.md / LICENSE / requirements.txt 等 |
| `plans/` | 2 | <0.1 MB | 2 | 0 | 治理 | 迁移路线图 + 本契约 |
| 其他 dot-dir（.cursor/.roo/.kiro 等） | 8 | <0.1 MB | 8 | 0 | public | 各客户端配置，均 1-2 个文件 |

> `[原文]` 数字来自 `.tmp/inventory_scan.json`（实测输出，命令见附录）。

### 1.3 文件类型分布（Top 12）

| 扩展名 | 数量 | 说明 |
|---|---|---|
| `.svg` | 15,889 | 主体为 `templates/icons/` 三套图标库（templates 目录共 11,918 文件）`[推断]` |
| `.png` | 2,169 | 项目/示例图片资产 |
| `.md` | 1,918 | 文档 + 工作流 + 项目 notes |
| `(无扩展)` | 1,330 | 多为 `projects/` 内素材 `[推断]` |
| `.json` | 551 | 索引/清单/产物 |
| `.pyc` | 482 | 全部 ignored（`__pycache__`） |
| `.js` | 430 | confirm_ui / dashboard 前端 |
| `.py` | 265 | 其中 scripts/ 顶层 81 + 子目录 167 = 248 `[原文]` |
| `.jpeg` / `.jpg` | 373 | 图片资产 |
| `.pptx` | 101 | 导出产物（projects 91 + examples 含同源拷贝） |

### 1.4 最大文件（Top 8）

| 大小 | 路径 |
|---|---|
| 156.6 MB | `projects/zhugeliang_ppt169_20260623/exports/zhugeliang_20260624_000605.pptx` |
| 91.1 MB ×5 | `projects/march7th_hsr_ppt169_20260622/exports/`（同名多版本）+ 1 份 examples 同源 |
| 77.2 MB | `projects/deepseek_evolution_ppt169_20260621/exports/deepseek_evolution_20260621_230352.pptx` |
| 67.2 MB | deepseek_evolution 另一版本 + examples 同源 |
| 43.8 MB ×2 | `projects/yunying_ppt169_20260628/images/ref/…candidate_01.png` + `_research/step7_visual/…`（同内容两处） |

> `[原文]` `projects/` 内多版本导出是常态（如 march7th_hsr 有 7 个导出 PPTX，含 3 个 91.1 MB 同大小版本）。

### 1.5 重复哈希分析

| 重复区间 | 组数 | 说明 |
|---|---|---|
| 仅 `projects/` 内 | 764 | 主因：`projects/*/backup/` 快照（21 个项目有 backup 目录，march7th_hsr 512 MB / deepseek_evolution 175 MB / meditation 154 MB / kaos_dream 73 MB）+ 多版本导出 |
| `examples/` ↔ `projects/` | 656 | 示例从项目复制发布（如 `march7th_hsr…163526.pptx` 91.1 MB 双份）`[推断]` |
| 仅 `.codex/` | 147 | 工具状态自重复 |
| `projects/` ↔ `skills/` | 144 | `icon_sync.py` 把图标库 SVG 拷入项目 `icons/`（设计使然，非异常）`[原文]` |
| 仅 `.tmp/` | 47 | 既往实验产物 |
| 仅 `examples/` | 35 | 示例内部重复（如 meditation 的 P03/P06/P07… 背景图同内容） |
| 仅 `skills/` | 16 | 图标库内部 `[待验证]` |
| 合计 | 1,828 组 / 6,568 文件 | 理论可回收 ≈ 3.26 GB（按每组保留 1 份计） |

> **注意**：examples↔projects 同源是「发布基线」设计的一部分，清理只允许在 `projects/` 侧评估（Phase 4），`examples/` 一律不动（§4.3 红线）。

### 1.6 脚本入口与引用关系

- `skills/ppt-master/scripts/` 顶层 81 个 `.py` 入口 [原文]，全部被 workflows / references / scripts-docs / docs 至少引用一次 —— **0 孤儿入口** [原文]（扫描范围：`workflows/`、`references/`、`scripts/docs/`、`scripts/README.md`、`SKILL.md`、`AGENTS.md`、`docs/`、根 `README.md`）。
- 引用最多的入口：`svg_to_pptx.py`（109 处）、`svg_quality_checker.py`（94）、`image_gen.py`（83）、`finalize_svg.py`（66）、`project_manager.py`（61）。
- 子目录 20 个，共 167 个 py：`svg_to_pptx/`（41）、`pptx_to_svg/`（19）、`image_backends/`（16）、`template_fill_pptx/`（16）、`dashboard/`（14）、`image_sources/`（11）、`pptx_shapes/`（8）、`svg_finalize/`（8）、`tts_backends/`（7）、`svg_quality/`（6）、`source_to_md/`（5）、`vision_backends/`（5）、`research/`（4）、`confirm_ui/`（2）、`template_import/`（2）、`svg_editor/`（3）等。
- 兼容层（同名新旧并存）：`pptx_to_svg.py`（thin wrapper）↔ `pptx_to_svg/` 包；`svg_to_pptx.py`（thin wrapper）↔ `svg_to_pptx/` 包；`template_fill_pptx.py`（thin wrapper）↔ `template_fill_pptx/` 包；`scripts/animation_config.py`（152 行顶层 shim）↔ `svg_to_pptx/animation_config.py`（1,505 行全版）[原文]。

### 1.7 workflow / reference / template 结构

| 目录 | 文件数 | 说明 |
|---|---|---|
| `workflows/` | 31 md | routing.md（4 路由权威）+ generate-pptx.md（Step 1-8）+ index.md + 14 根级工作流 + stages/（7）+ profiles/（2）+ governance/（1）+ research/ |
| `references/` | 149（101 md） | 角色定义 + modes/ + visual-styles/ + image-renderings/ + image-palettes/ + 技术约束 |
| `templates/` | 11,918（26 md） | icons/ 三库为主体；brands/layouts/decks/charts 各带 JSON 索引；`design_spec_reference.md` / `spec_lock_reference.md` |
| `.github/workflows/` | 2 | ci.yml（smoke + svg-quality + e2e 三 job，paths 过滤）；deploy-pages.yml（index.html/viewer.html/examples 变更触发） |

## 2. 权威层级矩阵

| 层级 | 文件 | 拥有什么 | 可被谁覆盖 |
|---|---|---|---|
| L1 仓库入口 | `AGENTS.md` | 必读、兼容边界、安全约束、高险路由指针 | 仅用户显式指令 |
| L2 主工作流 | `SKILL.md` | 全局执行纪律、加载顺序、四路由表 | L1 不覆盖其运行内容 |
| L3 路由权威 | `workflows/routing.md` | 路由选择矩阵与边界 | 冲突时 routing.md 胜出（routing.md §1 自述）[原文] |
| L4 路由执行 | `workflows/generate-pptx.md` 等 | Step 1-8、门禁、合同 | 仅该路由激活 |
| L5 技术参考 | `references/*.md` | 角色行为、SVG/PPT 约束 | 被 SKILL/workflow 加载时生效 |
| L6 规则 | `docs/rules/*.md` | 编辑风格、治理、变更管理 | 不覆盖 L1-L5 |
| L7 摘要 | `docs/routing.md`、`docs/ai-rules-shared.md` | 摘要/分发 | 与权威冲突时更新摘要而非改运行时 |
| L8 草稿/审计/计划 | `docs/reviews/*`、`docs/design/*`、`plans/*` | 提案/发现/契约 | 非运行权威；推荐不视为已批准 |

> 冲突规则（`docs/rules/agent-governance.md` §1 [原文]）：遵循最高适用层；摘要与权威冲突时更新摘要。

## 3. 目录 owner / 可修改性 / 可删性 / 依赖方 / 回滚

| 目录 | owner | 可修改 | 公开 | 可删除 | 依赖方 | 回滚方式 |
|---|---|---|---|---|---|---|
| `skills/ppt-master/` | 本仓库 | ✅（含门禁） | ✅ | ❌ | SKILL 全链路、CI、docs | git revert + smoke 回归 |
| `docs/` | 本仓库 | ✅ | ✅ | ❌ | 用户阅读、链接扫描 | git revert |
| `AGENTS.md` / `README.md` 等根文件 | 本仓库 | ✅ | ✅ | ❌ | 所有 Agent 入口 | git revert |
| `.github/` | 本仓库 | ✅ | ✅ | ❌ | GitHub CI/Pages | git revert |
| `plans/` | 本仓库 | ✅ | ✅ | 归档后可标记 | 后续阶段执行 | git revert |
| `projects/` | 用户 | 仅生命周期规则 | ❌（gitignored） | 仅用户批准 + 清单 + 回滚副本 | 生成工作流运行期 | 云同步/备份（git 不含） |
| `examples/` | 本仓库（公开基线） | ✅ | ✅ | ❌（默认） | CI 三 job、GitHub Pages | git revert |
| `.codex/` 等客户端 dot-dir | 各自工具 | 工具自管 | ❌ | 用户确认后 | 工具运行期 | 工具重建 |
| `.tmp/` / `.codex-tmp/` | 开发期 | ✅ | ❌ | ✅（会话结束清理） | 无 | 无（可再生） |
| `.align/` | 治理协议 | 更新须独立获批 | ❌ | ❌ | align 协议 | 文件级恢复 |

## 4. 候选冗余 / 疑似死文件 / 旧路线图 / 重复资源（第一阶段不处理）

> 以下全部仅列出证据，**不删除、不移动、不重命名**。处置归 Phase 2/4 审批。

| # | 类别 | 证据 | 建议处置（待批） |
|---|---|---|---|
| R1 | 同内容双文件 | `scripts/pptx_animations.py` 与 `scripts/native_pptx_animations.py` md5 完全相同（`c6d7c928…`，各 145,406 B）；`svg_to_pptx/` 内 3 个消费点 import 旧名 `pptx_animations` | Phase 2 核验消费面后合并/留名，需「消费者×符号」矩阵 |
| R2 | 已执行计划未归档 | `plans/followup-migration-roadmap.md` Phase 2-6 已于 2026-08-03 全部执行，文档仍为计划形态（含「待确认事项」已过时） | Phase 2 标记为已完成/归档，或归档至 docs |
| R3 | `.align` 事实过期 | spec.md「无 CI 流水线」「无自动化测试」与 `.github/workflows/` 存在矛盾；smoke 基线 38/41 过期（现 78/81） | 独立获批后刷新 spec/context（本报告只做差异报告） |
| R4 | backup 快照冗余 | `projects/*/backup/`：march7th_hsr 512 MB / deepseek_evolution 175 MB / meditation 154 MB / kaos_dream 73 MB；内含整份 `svg_output/images` 副本（如 meditation 每个备份 12+ 份 4-5 MB 背景图） | Phase 4：归档策略（保留最新一份或移出工作区） |
| R5 | 多版本导出 | `projects/march7th_hsr_ppt169_20260622/exports/` 7 个 PPTX（3×91.1 MB + 68.8 + …）；deepseek_evolution 4 个 | Phase 4：生命周期规则（如仅保留最终版） |
| R6 | 工具状态体积 | `.codex/` 2,783 文件 / 261.5 MB（含 tflite 模型、dashboard-cdp 状态） | 用户确认后清理（Phase 4） |
| R7 | `.tmp/` 历史产物 | 375 文件 / 14.9 MB（含既往会话残留 374 个，本会话新增 6 个测量文件） | 会话结束清理；本会话测量数据按 Brief 保留在 `.tmp/` |
| R8 | 图标库进项目 | 144 组 projects↔skills 重复 = `icon_sync.py` 设计行为 | 不改（设计使然） |
| R9 | 大体积 .gif | `docs/assets/hero-liziqi-colors.gif` 19.8 MB（docs 33.5 MB 大头） | `[待验证]` 是否仍被引用；Pages 会整体上传 |
| R10 | 占位链接 | 8 处 `xxx.md` / `url` 占位（prompt-style.md ×5、roadmap.md ×2、pipeline-coherence-audit ×1） | 既有允许项（示例/占位），不视为断链 |
| R11 | 空目录 | `.agents/` 为空 | `[待验证]` git 不含空目录，仅本地存在 |

## 5. 漂移差异报告（.align 及其余事实源 vs 实测）

| 声明位置 | 过期声明 `[原文]` | 实测事实 `[原文]` | 影响 |
|---|---|---|---|
| `.align/spec.md` 分支与提交规范 | 「无自动化测试，无 CI 流水线」 | `.github/workflows/ci.yml`（smoke + svg-quality + e2e 三 job）、`deploy-pages.yml` 存在；smoke_check 含集成测试（commit `101e713b`） | 后续模型可能误判 CI 不存在 |
| `.align/spec.md` 测试与验证命令 | 「无自动化测试（`tests/`、`test_*.py`、unittest/pytest 均禁止）」 | 无 `tests/` 目录属实；但 smoke_check 自带集成测试 + CI 自动运行，声明过窄 | 语义过窄 |
| `.align/spec.md` 技术栈 | （无明确版本声明） | Python 3.12.13（uv 托管 cpython-3.12-windows-x86_64）实测 | 可补 |
| `.align/context.md` 架构决策 | 「仓库不包含自动化测试」 | smoke_check 自带集成测试 + CI 运行 | 语义过窄 |
| `plans/followup-migration-roadmap.md` | 计划形态（Phase 2-5「待执行」） | Phase 2-6 已全部执行完毕（change-log 2026-08-03 记录） | 后续模型可能重复执行 |
| 根 `requirements.txt` | 与 skill requirements 关系未注明 | 根文件仅为 `-r skills/ppt-master/requirements.txt` 转发 | 非问题，记录即可 |
| `docs/roadmap.md` | — | 内容为最新（2026-06 条目），与现状一致 | 无需处理 |

> **勘误（2026-08-03 修正）**：初版 §5 曾列「spec.md 测试与验证命令含 smoke 基线 38/41 过期」——核对原文后证实 `spec.md` 只记录命令、未记录基线数字（38/41 系 change-log 2026-06-27 的旧基线，张冠李戴）。此行为上表「语义过窄」行替代；当前基线为 `--skip-help` 78/0/3（81 checks）、完整模式 158/0/4（162 checks）。

> 处置原则：本报告只做差异报告；`.align` 更新必须作为独立、获批的后续变更。→ **2026-08-03 已获批执行**（spec.md / context.md 刷新完成，见契约 §10.2 执行记录）。

## 6. 链接与门禁健康度

| 检查 | 结果 |
|---|---|
| Markdown 链接 | 880 个 tracked md、1,037 条链接，0 真断链；8 条占位（`xxx.md`/`url` 示例）`[原文]`；与 change-log Phase 2 记录（9 条占位 → 现 8 条）一致 |
| 路由表目标文件 | `routing.md` §2-7 引用的工作流/配置文件逐一存在 `[原文]` |
| attribution_guard | 门禁清单存在；guard 脚本可导入、smoke 通过 `[原文]`；本会话未改动任何被锁文件 |
| gitignore 卫生 | tracked 且匹配 ignore 规则 = 0 `[原文]` |
| 工作区状态 | clean（untracked 0）`[原文]` |
| CI 契约面 | ci.yml 引用 `skills/ppt-master/requirements.txt`（存在）；e2e job 按 `examples/*/spec_lock.md` + `exports/*.pptx` 循环（29 个示例全部具备）`[原文]` |

## 7. 性能粗基线（Phase 3 前置，单次测量非 p50/p95）

> 测量环境：Windows 10.0.26200 x64、Python 3.12.13（uv 托管）、Git Bash。方法：`time.perf_counter()` 单次冷进程计时。

| 项 | 耗时 | 备注 |
|---|---|---|
| 全仓 os.walk（24,203 文件） | 0.33 s | 不含 `.git` |
| 冷导入 `svg_quality` | 0.06 s | scripts/ 目录内 |
| 冷导入 `svg_to_pptx` | 0.09 s | 重构版导出器包 |
| 冷导入 `svg_to_pptx + svg_quality` | 0.12 s | 组合 |
| 冷导入 `pptx_to_svg` | 0.26 s | |
| 冷导入 `dashboard.server` | 0.40 s | |
| 冷导入 `confirm_ui.server` | 0.50 s | |
| smoke_check 完整模式单次 | ≈ 26.1 s（2026-08-03 实测修正：初版「≈3 分钟」系后台任务观测误判；完整 p50/p95 基线见 `docs/reviews/perf-baseline-2026-08.md`） | 实测 |

> `[待验证]` p50/p95 与 Dashboard 启动、质量检查、代表性导出（如 `examples/ppt169_kubernetes_blueprint_2026`）的正式基线，留待 Phase 3 按契约 §6 建立。

## 8. 风险与待决策项

### 8.1 风险

1. `.align` 过期事实被后续模型当作运行依据（§5）——中风险，差异报告已隔离。
2. 重复清理误伤 examples（公开基线）——高风险，处置仅限 `projects/` 侧且须独立审批。
3. `pptx_animations` / `native_pptx_animations` 双文件长期并存增加维护面——低风险，但需 Phase 2 决策。
4. `projects/` 无生命周期规则，backup/多版本持续膨胀（当前 5.3 GiB 中大量可回收）——中风险。
5. Pages 上传整仓（`upload-pages-artifact path: '.'`）[原文]，体积与示例扩展直接相关——中风险，改造需单独设计。

### 8.2 待决策项

| # | 决策 | 建议（供用户参考，不代替用户决定） |
|---|---|---|
| D1 | `plans/followup-migration-roadmap.md` 归档方式 | 标记已完成并归档（Phase 2 首批） |
| D2 | `.align/spec.md` / `context.md` 刷新 | 批准后作为独立变更执行（含 CI 事实、smoke 基线、Python 版本） |
| D3 | `pptx_animations.py` 与 `native_pptx_animations.py` 是否合并 | 先出 3 消费点符号面矩阵，再定（Phase 2） |
| D4 | `projects/` 生命周期规则（active/archive/disposable + backup 策略） | Phase 4 单独立项 |
| D5 | `.codex/` 261 MB 是否清理 | 用户确认后执行 |
| D6 | 性能优化目标阈值 | 基线报告后单独确认（契约 §6） |

## 9. 附录：证据与命令

### 9.1 原始测量数据（gitignored，位于 `.tmp/`）

| 文件 | 内容 |
|---|---|
| `.tmp/inventory_scan.json` | 全仓扫描结果：state_by_top / top_stats / ext_stats / largest_200 / dup_groups / size_buckets |
| `.tmp/inventory_scan.log` | 扫描汇总输出 |
| `.tmp/analyze_inventory.log` | 目录分解与重复分析输出 |
| `.tmp/link_check.log` | 链接检查结果 |
| `.tmp/smoke_baseline.log` | smoke 完整模式基线（158/0/4） |
| `.tmp/smoke_baseline_skiphelp.log` | smoke `--skip-help` 基线（78/0/3） |
| `.tmp/inventory_scan.py` / `analyze_inventory.py` / `link_check.py` | 测量脚本（可复跑） |

### 9.2 关键命令

```bash
git ls-files -z | wc -l                      # tracked 计数（-z 防 quotepath 转义）
git status --porcelain -uall -z              # untracked 计数
git check-ignore --stdin -z                  # ignored 分类
git ls-files -z | tr '\0' '\n' | git check-ignore --stdin   # tracked 且匹配 ignore（=0）
python skills/ppt-master/scripts/smoke_check.py             # 完整基线
python skills/ppt-master/scripts/smoke_check.py --skip-help # 文档口径基线
python .tmp/inventory_scan.py                # 复跑全仓扫描（约 2 分钟）
python .tmp/link_check.py                    # 复跑链接检查
```

### 9.3 复跑说明

- 扫描脚本会重新统计当前文件系统状态；若 `.tmp/` 或 `projects/` 内容变化，数字会随之变化——对账时以扫描当次输出为准。
- smoke 完整模式约 26.1 s（160 checks，2026-08-03 实测修正；初版「≈3 分钟」系后台任务观测误判）；`--skip-help` 模式约 2.3 s，数字应与本文档一致（除非脚本集变更）。
