# PPT Master 管线成熟度与全仓协同性审计（2026-07）

> 状态：只读审计报告。  
> 权威性：非运行规则；`skills/ppt-master/SKILL.md`、各 workflow 和 `docs/rules/` 仍是运行权威。  
> 范围：`SKILL.md`、`CLAUDE.md`、`docs/routing.md`、`docs/claude-reference.md`、`docs/rules/`、`skills/ppt-master/workflows/`、`skills/ppt-master/references/`、`skills/ppt-master/scripts/`、`docs/`。

## 0. 总体结论

一句话判断：PPT Master 已经不是一堆松散 prompt，而是一个有主干、有支路、有质量门的工作流系统；但还没有达到“全仓有机整体”满分，主要短板集中在断链、少数契约漂移、非运行设计稿混入 `workflows/`，以及目录语言规则与现状不完全一致。

我对元问题的表态：**部分同意**“有机整体性是判断项目优秀的标准”。它是优秀项目的必要条件之一，不是充分条件。一个系统可以引用可达、契约一致，但仍然因为生成质量差、工具不稳定或交互成本高而不优秀；反过来，一个单点能力很强的系统如果断链、契约漂移、孤儿文件多，规模一上来就会失控。

可度量子标准如下：

| 子标准 | 可度量口径 | 本次结论 |
|---|---|---|
| 契约闭合 | 上游 artifact 是否被下游明确读取，路径和字段是否一致 | 基本通过；`generation_mode: batch-review`、`image-text-linking` 模板数量、deep-research Step 7 参考图门槛存在漂移 |
| 引用可达 | Markdown 链接、workflow 入口、脚本路径是否存在 | 部分失败；运行入口范围有 2 个 `SKILL.md` 断链，全仓还有 `strategist.md` 断链 |
| 权威层次清晰 | `SKILL.md`、routing、workflow、reference 是否互不打架 | 部分失败；`batch-review` 与 Confirm UI 枚举、deep-research orchestrator 与 Step 7 子工作流不一致 |
| 质量门可执行 | 每条管线是否有检查、失败返回、停顿条件 | 多数通过；轻量卫星管线以 artifact gate 为主，合理；少数缺机械校验 |
| 文件归属清楚 | runtime workflow、设计稿、脚本接口是否分层摆放 | 部分失败；`img2img-support.md` 自称非运行 workflow 却位于 `workflows/` |

工具链健康度证据：`python skills/ppt-master/scripts/smoke_check.py --skip-help` 通过，结果为 50 passed、0 failed、3 skipped / 53 checks。

## 1. 基准：deep-research 成熟在哪里

`deep-research` 的成熟不是“长”，而是它把一个复杂前置阶段拆成可验证的契约链。

关键成熟特征：

| 维度 | deep-research 证据 | 可复用经验 |
|---|---|---|
| 单入口和边界 | `deep-research.md` 声明 “single entry point”，并要求 topic-only 必须先完成 `ppt-briefing`（`skills/ppt-master/workflows/deep-research.md:7-17`） | 每个复杂管线要先定义入口和禁止替代路径 |
| 触发矩阵 | 按 topic-only、深度调研、复杂主题、源文件、长聊天内容分流（`deep-research.md:74-82`） | 触发条件应是表格化、可判定的 |
| Artifact 拓扑 | `_research/step1_outline/` 到 `_research/step7_visual/`，再同步到 `analysis/`、`sources/`、`images/`（`deep-research.md:86-107`） | 中间产物应有固定目录，不能靠聊天记忆 |
| 目录完整性 | “Single project directory / no sibling folders / no staging”（`deep-research.md:110-113`） | 项目级输出必须收敛到一个 canonical project |
| 分步输入输出 | 每步都有 `Input` / `Output` 表格，如 Step 1 到 Step 7（`deep-research.md:130-248`） | 子步骤之间要用文件契约传递 |
| 机器质量门 | `research_gate.py` 必须在 sync 前通过，失败返回 gate 指定步骤（`deep-research.md:253-260`） | 不能只靠“看起来完成”；需要机器 gate |
| 完成凭证 | `RESEARCH_COMPLETE` 注释列出所有 artifact 和 next step（`deep-research.md:262-280`） | 阶段结束应留下可恢复、可审计的收据 |
| 错误恢复 | 明确搜索失败、计划过宽、质量门失败、上下文耗尽的动作（`deep-research.md:284-292`） | 失败路径也是管线的一部分 |

注意：用户提示中已说明 deep-research 自身有“散落暂存目录”的遗留坑。本报告不把这个坑提炼为基准；相反，报告只把 `deep-research.md:110-113` 中已经写明的“单项目目录、无 staging”作为正向结构特征。该遗留坑本次未进一步定位到具体代码路径，故不作为 P0/P1 结论。

## 2. 评分 Rubric

所有运行型 workflow 使用同一 rubric。0 = 缺失；1 = 隐含、局部或依赖上游记忆；2 = 明确、可执行、可检查。N/A 只在该维度确实不适用于 workflow 角色时使用，并从分母中剔除。

| 编号 | 维度 | 0 分 | 1 分 | 2 分 |
|---|---|---|---|---|
| R1 | 触发与边界 | 没有触发条件或边界 | 有触发词但边界不完整 | 有 When to Run / When NOT to Run / route boundary |
| R2 | 输入输出契约 | 不说明 artifact | 只说明人类语义产物 | 明确路径、格式、字段或目录 |
| R3 | 步骤完整性 | 只有目标，无过程 | 有步骤但缺顺序或关键动作 | 步骤顺序、命令、角色或循环完整 |
| R4 | 质量门/验证 | 无验证 | 人工确认或轻量检查 | 有明确 gate、脚本、阈值或失败动作 |
| R5 | 失败降级/恢复 | 无失败路径 | 有一两个边界处理 | 失败场景可返回、重跑、降级或停止 |
| R6 | 可恢复性/重入 | 无恢复线索 | 可从 artifact 推断恢复 | 明确 fresh session、resume、checkpoint 或 idempotent 重跑 |
| R7 | 与主管线衔接 | 不说明回到哪里 | 只泛称“继续” | 明确接入 SKILL.md 哪一步或下游 workflow |
| R8 | 术语、语言、权威一致性 | 与权威冲突或位置错误 | 有混用/轻微漂移 | 与本层权威和目录规则一致 |

“轻量但够用”的判定：如果一个卫星 workflow 只负责一个 post-export 动作或一个短暂停顿点，它不需要复制 deep-research 的 7 步结构；只要 R1/R2/R7 清楚、R4/R5 与风险匹配，就不按篇幅扣分。

## 3. 19 个 workflow 评分卡

| Workflow | 角色判断 | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | 总分 | 结论 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `deep-research.md` | 基准管线 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16/16 | 最成熟；但有子步骤契约漂移，见 P1-2 |
| `ppt-briefing.md` | topic-only 前置 brief | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 1 | 13/16 | 轻量但够用 |
| `content-selection.md` | 研究后内容筛选 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 1 | 14/16 | 合格 |
| `detailed-outline.md` | 详细逐页大纲 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 1 | 14/16 | 合格 |
| `refine-spec.md` | 生成前 spec 复核 | 2 | 2 | 2 | 1 | 1 | N/A | 2 | 2 | 12/14 | 轻量但够用 |
| `revision-loop.md` | 生成后局部修订 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 1 | 14/16 | 合格 |
| `batch-review.md` | 分批审阅卫星 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 0 | 12/16 | 功能设计合格，但存在契约漂移 |
| `visual-review.md` | 视觉自检 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 15/16 | 合格，接近成熟 |
| `verify-charts.md` | 图表坐标校准 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 16/16 | 成熟 |
| `beautify-pptx.md` | 1:1 美化重排 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 14/16 | 合格 |
| `template-fill-pptx.md` | 直接 PPTX 填充 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 14/16 | 合格 |
| `create-template.md` | 模板资产创建 | 1 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 13/16 | 合格；入口触发可更显式 |
| `create-brand.md` | 品牌 preset 创建 | 2 | 2 | 2 | 1 | 1 | N/A | 2 | 2 | 12/14 | 轻量但够用 |
| `live-preview.md` | 预览/注解应用 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | 14/16 | 轻量但够用 |
| `resume-execute.md` | Phase B 重入 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 15/16 | 合格，恢复性强 |
| `customize-animations.md` | 对象级动画 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 15/16 | 合格 |
| `generate-audio.md` | 旁白/视频导出 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | 14/16 | 轻量但够用 |
| `image-text-linking.md` | 横切图文语义约束 | 2 | 2 | 2 | 2 | 1 | N/A | 2 | 1 | 12/14 | 角色合理，但内部模板描述漂移 |
| `img2img-support.md` | 非运行设计稿 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 0 | N/A | 作为 runtime workflow 不合格；作为历史设计稿位置不合格 |

## 4. 协同性机械扫描结果

### a. 链接完整性：不通过

运行入口范围（`SKILL.md` / `CLAUDE.md` / `docs/routing.md` / `docs/claude-reference.md` / workflows）发现 2 个实断链：

| 证据 | 问题 |
|---|---|
| `skills/ppt-master/SKILL.md:797` 链接 `../docs/spec-review-template.md` | 从 `skills/ppt-master/` 解析为 `skills/docs/spec-review-template.md`，目标不存在；真实文件在 repo 根 `docs/spec-review-template.md` |
| `skills/ppt-master/SKILL.md:799` 链接 `../docs/change-log.md` | 同上，真实文件在 repo 根 `docs/change-log.md` |

全仓 Markdown 额外发现 reference 层断链：

| 证据 | 问题 |
|---|---|
| `skills/ppt-master/references/strategist.md:471` 链接 `../image-renderings/_index.md` / `../image-palettes/_index.md` | 从 `references/` 向上一级会解析到 `skills/ppt-master/image-renderings/`，目标不存在；实际目录是 `skills/ppt-master/references/image-renderings/` 和 `skills/ppt-master/references/image-palettes/` |
| `skills/ppt-master/references/strategist.md:590` 同样链接 | 同一断链重复出现 |

排除项：`docs/rules/prompt-style.md` 中的 `xxx.md` 是格式示例（`docs/rules/prompt-style.md:13`、`:146-150`）；`docs/roadmap.md:57` / `docs/zh/roadmap.md:57` 中的 `[text](url)` 是 Markdown 语法示例，不计入断链。

### b. 路由覆盖：运行 workflow 通过，目录语义不通过

机械引用图显示 18 个运行 workflow 均可从 `SKILL.md`、`docs/routing.md`、`docs/claude-reference.md` 或其他 workflow 到达。子工作流未进入 routing 表是合理的，例如 `content-selection`、`detailed-outline`、`image-text-linking` 在 `SKILL.md` 的条件链路中出现（`skills/ppt-master/SKILL.md:238-246`、`:397-399`、`:545`）。

唯一不可达文件是 `skills/ppt-master/workflows/img2img-support.md`。它自称：

| 证据 | 含义 |
|---|---|
| `img2img-support.md:3-7` | frontmatter 标记 `status: non-runtime-draft`、`runtime_workflow: false` |
| `img2img-support.md:10-23` | 标题和说明写明 “Not a Runtime Workflow”，且“do not invoke this file from workflow routing” |
| `skills/ppt-master/SKILL.md:109-125` | Standalone Workflows 表未列出 `img2img-support` |

因此它不是运行断路，但它放在 `workflows/` 会污染“workflow 文件即运行流程”的目录语义。按协同性标准评为 P1，而非 P0。

### c. 契约一致性：部分不通过

| 契约 | 证据 | 判定 |
|---|---|---|
| `confirm_ui/result.json.generation_mode` | `batch-review.md:16` 接受 `generation_mode: "batch-review"`；但 Confirm UI catalog 只有 `continuous` / `split`（`scripts/confirm_ui/static/catalogs.json:446-458`），Confirm UI 文档也只承认 `split`（`scripts/docs/confirm_ui.md:124`），SKILL 只对 `generation_mode: "split"` 作 Phase A 停止处理（`SKILL.md:591`） | 不通过 |
| deep-research Step 7 参考图门槛 | orchestrator 只要求至少 1 张参考图（`deep-research.md:247`）；子工作流要求“所有需要参考图页面”都有参考图，且“只满足至少 1 张不再合格”（`workflows/research/step7_visual.md:109`） | 不通过 |
| `image-text-linking` prompt 模板数量 | Step 2 标题称 “6-part mandatory structure”（`image-text-linking.md:66`）；输出表却称 prompt follows “4-part template”（`image-text-linking.md:272`） | 不通过 |
| `skip_visual_review` | SKILL、routing、visual-review 均以 explicit opt-out 或 `confirm_ui/result.json.skip_visual_review: true` 跳过（`SKILL.md:681`、`docs/routing.md:16`、`visual-review.md:76`） | 通过 |
| `content_selection.json` -> `detailed_outline.json` -> `image_prompts.json` / `image_queries.json` | `SKILL.md:244-246` 给全局链路，`detailed-outline.md:411-426` 和 `image-text-linking.md:252-275` 给下游契约 | 通过 |
| PPTX intake channel ownership | `SKILL.md:203-211`、`:403-405`、`beautify-pptx.md:65-84`、`template-fill-pptx.md:68-86` 对 `source_profile.json`、`<stem>.identity.json`、`<stem>.slide_library.json` 的读法区分清楚 | 通过 |

### d. 脚本引用：运行引用基本通过，存在接口级孤儿/维护脚本

已引用脚本路径在运行范围内基本存在。`smoke_check.py --skip-help` 对 53 个脚本的 import 层检查全部通过。

接口级孤儿或弱引用脚本：

| 脚本 | 扫描结论 | 分级 |
|---|---|---|
| `skills/ppt-master/scripts/batch_validate.py` | 未被 SKILL/workflows/references/docs 作为运行接口引用；只在自身 docstring 出现 | P2 |
| `skills/ppt-master/scripts/console_encoding.py` | 未作为用户运行接口引用；可能是内部 helper [推测] | P2 |
| `skills/ppt-master/scripts/pptx_animations.py` | 未在运行文档中引用；只在自身 docstring 出现 | P2 |
| `skills/ppt-master/scripts/generate_examples_index.py` | 有脚本文档/自身生成内容引用，但不在主运行管线中 | P2 |
| `skills/ppt-master/scripts/rotate_images.py` | 有 `scripts/docs/conversion.md` 引用，但不在主运行管线中 | P2 |
| `skills/ppt-master/scripts/update_repo.py` | 有 `scripts/README.md` 引用，属于维护脚本 | P2 |

这不是正确性破坏，但建议区分“runtime script table”和“maintenance/internal script table”。

### e. 语言规则：不通过严格规则，运行风险低

仓库规则说 workflows、references、docs 目录应保持目录内单语言。机械扫描显示：

| 目录 | 结果 |
|---|---|
| `skills/ppt-master/workflows/` | 26 个 Markdown（含 `research/` 子步骤），8 个偏中文，13 个中英混合候选 |
| `skills/ppt-master/references/` | 95 个 Markdown，大体偏英文，只有少量中文示例 |
| `docs/` | 40 个 Markdown，`docs/zh/` 中文合理；根 `docs/` 含多份中文审计/设计稿 |

文件级例子：

| 文件 | 证据 |
|---|---|
| `ppt-briefing.md` | 中文主体和中文触发描述（`ppt-briefing.md:7-11`） |
| `content-selection.md` | 英文 workflow 结构中混入中文说明（`content-selection.md:57-61`） |
| `detailed-outline.md` | 英文结构中含中文咨询模式段落（`detailed-outline.md:38-40`） |
| `image-text-linking.md` | 中文引言 + 英文横切说明（`image-text-linking.md:7-9`） |
| `docs/rules/documentation-style.md` | 新审计/治理稿允许按 review language，但需状态和权威声明（`documentation-style.md:39-48`） |

判定：这是 P2 风格/治理漂移，不是当前运行 P0。新建本报告放入 `docs/reviews/`，全文件中文，并在首屏声明非权威，符合审计文档例外。

### f. 权威冲突：部分不通过

| 冲突 | 证据 | 影响 |
|---|---|---|
| Batch review 的 Confirm UI 入口不存在 | `batch-review.md:16` vs `catalogs.json:446-458`、`confirm_ui.md:124`、`SKILL.md:591` | 用户即使在 UI 选择 generation mode，也无法产生 `batch-review` 值；workflow 中的触发入口是死契约 |
| deep-research 参考图门槛不一致 | `deep-research.md:247` vs `research/step7_visual.md:109` | orchestrator 可能低估 Step 7 质量门 |
| image-text-linking 内部模板数量不一致 | `image-text-linking.md:66` vs `image-text-linking.md:272` | 下游 prompt QA 不知道按 4 段还是 6 段验收 |
| 非运行设计稿位于 workflow 目录 | `img2img-support.md:10-23` | 对“19 个工作流”的人工和机械审计都造成噪音 |

## 5. 问题清单

### P0：破坏正确性或可达性的缺陷

| 编号 | 问题 | 证据 | 建议 |
|---|---|---|---|
| P0-1 | `SKILL.md` 中指向 `docs/` 的相对链接错误 | `SKILL.md:797`、`SKILL.md:799` 链接 `../docs/...`，从 `skills/ppt-master/` 解析不到 repo 根 `docs/` | 改为 `../../docs/spec-review-template.md` 和 `../../docs/change-log.md` |
| P0-2 | `strategist.md` 中 image rendering / palette 索引链接错误 | `strategist.md:471`、`:590` 使用 `../image-renderings/_index.md` 和 `../image-palettes/_index.md`，实际目录在同级子目录 `references/image-renderings/`、`references/image-palettes/` | 改为 `./image-renderings/_index.md` 和 `./image-palettes/_index.md` |

### P1：削弱质量或造成契约漂移

| 编号 | 问题 | 证据 | 影响 | 建议 |
|---|---|---|---|---|
| P1-1 | `batch-review` 声称可由 `confirm_ui/result.json` 触发，但 UI 枚举不支持该值 | `batch-review.md:16` 写 `generation_mode: "batch-review"`；`catalogs.json:446-458` 只有 `continuous` / `split`；`confirm_ui.md:124` 只承认 `split`；`SKILL.md:591` 也只处理 `split` | UI 路径不可达，只有聊天显式请求能触发；文档会误导 agent | 二选一：删除 result.json 触发语；或把 Confirm UI schema、catalog、SKILL Step 4/5 全量支持 `batch-review` |
| P1-2 | deep-research orchestrator 与 Step 7 子工作流的参考图质量门不一致 | `deep-research.md:247` 至少 1 张；`research/step7_visual.md:109` 要所有需要参考图页面都有参考图，且“至少 1 张不再合格” | 主 orchestrator 可能允许过低素材门槛 | 以 Step 7 子工作流为准，更新 orchestrator checkpoint |
| P1-3 | `image-text-linking` 同文件内 prompt 模板数量漂移 | `image-text-linking.md:66` 写 6-part mandatory structure；`image-text-linking.md:272` 写 4-part template | prompt 生成和 QA 阈值不一致 | 统一为一个模板名称，并在输出表列出对应字段 |
| P1-4 | `img2img-support.md` 是非运行设计稿，却放在 `workflows/` | `img2img-support.md:3-7`、`:10-23` 自称 non-runtime；`SKILL.md:109-125` 不列入 Standalone Workflows | 机械枚举会把它算成第 19 个 workflow，但 runtime 可达性为 N/A | 迁到 `docs/design/`，或保留但从“workflow 清单”排除并在目录 README 标记非运行文件 |

### P2：打磨项

| 编号 | 问题 | 证据 | 建议 |
|---|---|---|---|
| P2-1 | 目录语言规则与现状不一致 | workflows 中 `ppt-briefing.md:7-11` 中文、`beautify-pptx.md:5-11` 英文；多文件中英混合 | 明确“workflow 文件可英文标题 + 中文正文”是否是允许模式；否则分目录或逐步统一 |
| P2-2 | 部分运行脚本/维护脚本没有清楚分层 | `batch_validate.py`、`console_encoding.py`、`pptx_animations.py` 等未在 runtime 文档中出现 | 在 `scripts/README.md` 分 runtime / maintenance / internal helper 三类 |
| P2-3 | 轻量 workflow 的 Exit Evidence 不完全统一 | `generate-audio.md:156-163` 有 completion report；`live-preview.md:48-69` 偏步骤，没有统一 completion block | 不要求重写，但后续编辑时按 `workflow-style.md:19-26` 补齐 Exit Evidence |
| P2-4 | `create-template.md` 入口触发不如其他 workflow 显式 | `create-template.md:11-32` 定义用途和流程，但缺独立 `When to Run` 表 | 后续编辑时补 `When to Run / When NOT to Run`，不必机械大改 |
| P2-5 | `visual-review.md` 使用 Claude-Code `TeamCreate`/`Agent` 术语，与跨宿主兼容说明并存 | `visual-review.md:117-141` | 已有 host compatibility fallback，保留即可；可在报告/路由中标注“支持降级为顺序执行” |

## 6. 哪些是真不合格，哪些只是轻量但够用

真不合格或需要修正后再视为协同合格：

| Workflow / 文件 | 判定 |
|---|---|
| `img2img-support.md` | 作为运行 workflow 不合格；作为历史设计稿本身合格，但位置不合格 |
| `batch-review.md` | 主体流程合格，但 `generation_mode: "batch-review"` 入口契约不合格 |
| `image-text-linking.md` | 横切角色合理，但 6-part / 4-part 描述不一致，需修正后才算契约稳定 |
| `deep-research.md` | 仍是成熟基准；但 Step 7 参考图 gate 与子工作流漂移，属于基准自身的局部 P1 |

轻量但够用：

| Workflow | 理由 |
|---|---|
| `refine-spec.md` | 只插入一个 pre-generation hard stop，不需要机器 gate；它明确默认 OFF、同步 `design_spec.md` / `spec_lock.md`、批准后回到 Step 5/6（`refine-spec.md:23-58`） |
| `live-preview.md` | 是服务重开和注解应用流程，入口、停止条件、Step 7 后 gate 清楚（`live-preview.md:11-23`、`:48-69`） |
| `generate-audio.md` | post-export 卫星，依赖 `notes/*.md`，一次性询问参数，顺序执行，不需要 deep-research 级复杂度（`generate-audio.md:11-23`、`:81-163`） |
| `customize-animations.md` | 动画对象级定制，有 `list-groups` / scaffold / validate / export 闭环（`customize-animations.md:9-16`、`:25-49`、`:247-263`） |
| `create-brand.md` | 品牌 preset 创建轻量合理；它明确 never auto-trigger、输出 brand path、下游必须 explicit path（`create-brand.md:13-22`、`:173-214`） |

## 7. 值得沉淀进 `docs/rules/` 的规范建议

1. **Workflow 目录纯度规则**：`skills/ppt-master/workflows/` 默认只放运行 workflow；历史设计稿和实现方案放 `docs/design/`。若必须保留非运行文件，frontmatter 必须有 `runtime_workflow: false`，并且目录索引/审计脚本默认排除。
2. **枚举字段双端一致规则**：任何 `confirm_ui/result.json` 字段新增枚举值，必须同时更新 workflow、`SKILL.md` 消费逻辑、`scripts/docs/confirm_ui.md`、`confirm_ui/static/catalogs.json`。本次 `generation_mode: batch-review` 是反例。
3. **Orchestrator 不得弱化子工作流 gate**：顶层 workflow 可以摘要，但不能给出比子 workflow 更低的质量门。若摘要和子 workflow 冲突，以子 workflow 为准并更新摘要。
4. **Markdown 链接 CI 规则**：对 `SKILL.md`、`CLAUDE.md`、`docs/routing.md`、`docs/claude-reference.md`、`workflows/`、`references/` 跑相对链接检查；允许忽略 fenced code 和显式示例占位符。
5. **脚本接口分层规则**：`scripts/README.md` 应把脚本分成 runtime pipeline、workflow satellite、maintenance、internal helper。未进入任一分类的脚本视为 P2 孤儿候选。
6. **语言规则现实化**：如果 workflows 允许“英文结构标题 + 中文主体说明”，把它写成规则；如果不允许，制定渐进迁移计划。当前“目录内单语言”与实际文件状态不完全一致。

## 8. 后续修复优先级建议

最小修复批次：

1. 修 P0 链接：`SKILL.md:797/799`、`strategist.md:471/590`。
2. 统一 `batch-review` 入口契约：删除不支持的 `generation_mode: "batch-review"`，或全栈支持。
3. 统一 deep-research Step 7 参考图 gate。
4. 统一 `image-text-linking` 的 6-part / 4-part 描述。
5. 决定 `img2img-support.md` 的归属：迁移到 `docs/design/` 或保留但从运行 workflow 统计中排除。

本报告未执行任何修复；除新建本文件外，未修改现有仓库文件。

## 9. 修复状态（2026-07-03）

> 状态：本节记录同日修复批次结果。修复细节见 `docs/change-log.md` 中 “2026-07-03 — Pipeline coherence audit repair batch”。

| 编号 | 状态 | 修复说明 |
|---|---|---|
| P0-1 | 已修复 | `skills/ppt-master/SKILL.md` 中 `docs/spec-review-template.md` 与 `docs/change-log.md` 的相对链接改为从 `skills/ppt-master/` 可达的 `../../docs/...`。 |
| P0-2 | 已修复 | `skills/ppt-master/references/strategist.md` 中 image rendering / palette 索引链接改为同级 `image-renderings/_index.md`、`image-palettes/_index.md`。 |
| P1-1 | 已修复 | `skills/ppt-master/workflows/batch-review.md` 删除不可能由 Confirm UI 产生的 `generation_mode: "batch-review"` 触发语，保留聊天显式请求触发。 |
| P1-2 | 已修复 | `skills/ppt-master/workflows/deep-research.md` 的 Step 7 checkpoint 改为逐页参考图覆盖门槛：`visual_strategy.json` 中每个需要参考图的页面必须有对应 approved `ref/` 文件，仅项目级至少 1 张不合格。 |
| P1-3 | 已修复 | `skills/ppt-master/workflows/image-text-linking.md` 统一为 6-part prompt template，并同步验证表与输出描述。 |
| P1-4 | 已修复 | `skills/ppt-master/workflows/img2img-support.md` 通过 `git mv` 迁至 `docs/design/img2img-support.md`，保留 `status: non-runtime-draft` 和 `runtime_workflow: false`，README 指向新路径。 |
| P2-1 | 已修复 | 按用户决策走规则现实化：`docs/rules/documentation-style.md`、`CLAUDE.md`、`AGENTS.md`、`docs/claude-reference.md` 改为目录主模式；不迁移或改写现有混合语言 workflow。 |
| P2-2 | 已修复 | `skills/ppt-master/scripts/README.md` 将顶层脚本分为 runtime pipeline / workflow satellite / maintenance / internal helper，覆盖全部顶层 `*.py`。 |
| P2-3 | 已修复 | 为缺失的轻量 workflow 补最小 Exit Evidence / completion block；保留既有 completion 段不重构。 |
| P2-4 | 已修复 | `skills/ppt-master/workflows/create-template.md` 补 `When to Run` / `When NOT to Run` 入口边界，并补 Exit Evidence。 |
| P2-5 | 已修复 | `docs/routing.md` 的 visual-review 行补充：多代理评审在不支持并行子代理的宿主上降级为顺序执行。 |

勘误：P2-2 中关于 `batch_validate.py` “只在自身 docstring 出现”的描述有误。复核发现它已被 `skills/ppt-master/scripts/README.md` 引用，并在 `skills/ppt-master/scripts/docs/project.md` 中有文档说明，因此不是孤儿脚本。本次分层修复将 `batch_validate.py` 归入 maintenance；真正缺少全仓 Markdown 运行引用的是 `pptx_animations.py` 与 `console_encoding.py`，已作为 internal helper 写入脚本 README。

后续项：只读侦察发现 `skills/ppt-master/scripts/research/research_gate.py` 的参考图机器 gate 仍弱于新文档门槛。当前脚本只要求 `visual_strategy.json.reference_images[]` 中 reviewed reference image 记录数不少于 1；它尚未逐页比对 `per_page_visual_strategy` 中需要参考图的页面，也未验证对应文件实际存在于 `_research/step7_visual/ref/`。本批次按约束未修改 `.py` 文件。
