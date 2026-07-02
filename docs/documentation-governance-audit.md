# DeepPPT 文档治理审计与改造方案

> 状态：独立审计草案。本文不改变 `AGENTS.md`、`skills/ppt-master/SKILL.md`、`skills/ppt-master/workflows/` 或 `docs/rules/` 的既有权威性。所有“建议上升”的规则都需要用户确认后再修改对应权威文档。
>
> 审计范围：`AGENTS.md`、`skills/ppt-master/SKILL.md`、`skills/ppt-master/workflows/`、`skills/ppt-master/workflows/research/`、`docs/routing.md`、`docs/ai-router-design.md`、`docs/ai-rules-shared.md`、`docs/rules/`、`docs/` 用户文档、架构文档、roadmap、change-log 与 `docs/design/` 设计文档。

---

## 1. 当前文档地图

### 1.1 入口与运行时规则

| 文档 | 当前职责 | 主要受众 | 当前权威状态 | 运行时读取建议 |
|---|---|---|---|---|
| `AGENTS.md` | 仓库入口、AI agent 起始约束、主流程指针、高风险 workflow 路由摘要、兼容边界、命令速查 | 通用 AI agent、维护者 | 高。仓库入口规则；但自称“只指向 SKILL.md”，实际包含大量 workflow 触发规则 | 每次进入仓库必须读；不应读取为完整执行手册 |
| `skills/ppt-master/SKILL.md` | PPT 主流程权威：步骤、门禁、角色切换、质量门、后处理、导出、上下文加载策略 | 生成 PPT 的 AI agent、维护者 | 最高流程权威。AGENTS 明确要求任何 PPT 生成或 repo 修改前读取 | PPT 生成和 repo 修改前必须读；执行时按步骤按需读取 |
| `docs/ai-rules-shared.md` | 多工具 AI assistant 共享规则摘要 | Cursor/Copilot/Kiro 等轻量入口 | 自称 common rules single source，但内容应低于 AGENTS/SKILL | 只适合轻量入口预热；不能作为最终路由权威 |
| `docs/routing.md` | workflow 路由速查表 | AI agent、维护者 | 明确声明是 compact routing aid，低于 SKILL.md | 仅当需要快速分派 workflow 时按需读 |
| `docs/ai-router-design.md` | Supervisor Router 设计草案、未来路由层模型 | 架构维护者、后续实现 agent | 明确声明 draft，不覆盖现有规则 | 不应运行时强制读取；只在路由治理/实现前读 |

### 1.2 主流程、专项流程与角色参考

| 文档层 | 当前职责 | 主要受众 | 权威状态 | 运行时读取建议 |
|---|---|---|---|---|
| `skills/ppt-master/SKILL.md` Workflow Step 1-8 | 主 SVG -> PPTX 管线执行手册 | 生成 agent | 主流程权威 | 必读；但按 Context Loading Strategy 避免一次性加载所有引用 |
| `skills/ppt-master/workflows/*.md` | 专项流程：topic briefing、deep research、template fill、beautify、resume、preview、visual review、audio 等 | 执行对应专项任务的 agent | 对本专项流程权威；不得被 routing 摘要替代 | 只有命中触发条件时读取对应文件 |
| `skills/ppt-master/workflows/research/*.md` | deep-research 的七个子步骤 | 调研 agent | deep-research 内部步骤权威 | 只在 deep-research 对应步骤读取 |
| `skills/ppt-master/references/*.md` | 角色定义、技术约束、模板/图像/执行细则 | 角色内执行 agent | 被 SKILL.md 和 workflow 调用时成为局部权威 | 按角色切换和 workflow 指令读取 |
| `skills/ppt-master/templates/**/README.md` | 模板、icon、brand 等资源说明 | 设计/模板 agent | 资源使用说明；低于 SKILL/workflow | 仅资源选择或模板创建时读取 |

### 1.3 docs/ 用户文档、架构文档、维护文档

| 文档类别 | 文件 | 当前职责 | 适合运行时读取吗 |
|---|---|---|---|
| 用户入门 | `docs/getting-started.md`、`docs/zh/getting-started.md`、`docs/windows-installation.md`、`docs/zh/windows-installation.md` | 面向用户安装和首次使用 | 不适合执行流程时作为权威；适合回答用户问题 |
| FAQ/定位 | `docs/faq.md`、`docs/zh/faq.md`、`docs/why-ppt-master.md`、`docs/zh/why-ppt-master.md` | 解释能力边界、定位、常见问题 | 不适合覆盖 workflow；适合用户解释 |
| 技术架构 | `docs/technical-design.md`、`docs/zh/technical-design.md`、`docs/templates-architecture.md`、`docs/zh/templates-architecture.md` | 架构背景、设计理由、数据模型 | 设计/维护时读；执行时只按 workflow 引用读 |
| 使用专题 | `docs/templates-guide.md`、`docs/zh/templates-guide.md`、`docs/audio-narration.md`、`docs/zh/audio-narration.md`、`docs/zh/animations.md` | 用户视角专题说明 | 不应作为 workflow 权威；可作为解释材料 |
| 路线与变更 | `docs/roadmap.md`、`docs/zh/roadmap.md`、`docs/change-log.md` | 路线图、非目标、AI 修改审计轨迹 | 维护时读；运行时不应读 |
| 设计草案 | `docs/design/*.md`、`docs/ai-router-design.md`、`docs/memslides-analysis.md` | 方案、评估、已归档设计或未来实现建议 | 不应当作已生效规则，除非文档明确已落地并指向权威文件 |
| 审计/模板 | `docs/skill-alignment-audit-2026-06-25.md`、`docs/spec-review-template.md` | 历史审计、生成后规则沉淀模板 | 维护时读；不能覆盖当前权威 |
| 开发规则 | `docs/rules/*.md` | prompt/code 等贡献规则 | 修改对应文件时按需读 |

### 1.4 workflow 触发与边界索引

| Workflow | 标题/用途 | 当前触发 | 关键边界 |
|---|---|---|---|
| `ppt-briefing.md` | topic-only 前置 Brief | 用户只有主题/方向/关键词，无文件、URL、长文本或实质内容 | 先产出 `ppt_brief.md/json`，必须等待用户确认；确认后才进入 deep-research |
| `deep-research.md` | 7 步深度调研 orchestrator | topic-only brief 确认后；content-quality-first 请求；源文件也可进入但搜索步骤可跳过 | 不得用内置 WebSearch 替代；七步分别产物和 gate |
| `content-selection.md` | 调研后内容维度筛选 | `research_report.md` 存在且尚无 `content_selection.json` | 交互式 BLOCKING，输出结构化选择 |
| `detailed-outline.md` | 每页详细大纲 | `content_selection.json` 已确认 | 发生在 Eight Confirmations 前；输出驱动 Strategist 和 image-text-linking |
| `image-text-linking.md` | 图文语义联动 | `detailed_outline.json` 存在且有图片行 | 不替代 image-generator/image-searcher，只增强 prompt/query |
| `template-fill-pptx.md` | 使用原 PPTX 设计填充新内容 | PPTX + 新材料/主题 + 明确复用原设计/填回模板 | 直接编辑 PPTX，不进入 SVG pipeline；源页可复用/重排 |
| `beautify-pptx.md` | 保留内容的 PPTX 美化/重排 | PPTX + 美化/重新排版 + 内容保持 | 严格 1:1 页数/顺序/文字；任何拆分/合并/改页数都转主流程 |
| `create-template.md` | 创建 deck/layout 模板 | 用户要创建可复用模板 | 模板 brief 确认前不得写最终模板目录/设计规格 |
| `create-brand.md` | 创建 brand-only 模板 | 用户明确 set up/extract brand 或提供品牌资产 | 不自动触发；输出到 `templates/brands/<id>/`，裸品牌名不触发应用 |
| `resume-execute.md` | Phase B 续跑 | 用户说继续生成 `projects/<x>` | 只在 Phase A 文件齐全时进入 Step 6/7；缺失时不得自动重跑 Phase A |
| `refine-spec.md` | 生成前 spec review | 用户显式要求 refine/review spec 或 Confirm UI 选择 | 默认关闭；在图片/SVG 前硬停等待批准 |
| `verify-charts.md` | chart 坐标校准 | deck 含数据图表，SVG 完成后 Step 7 前 | 以 design spec 图表列表为权威，不能默默从 SVG 猜 |
| `visual-review.md` | 渲染后视觉自检 | Executor gates 后、Step 7 前默认推荐；可显式跳过 | 是视觉 rubric 层，不是 SVG 生成；可使用 review subagents |
| `batch-review.md` | 分批生成+中间反馈 | 用户显式“分批审阅/batch review”；frontmatter 还提到 20+ 页/高质量项目 | 默认不启用；触发措辞需要收敛 |
| `revision-loop.md` | 生成后局部修订 | Step 6 后用户要求修改/调整/revise | 用 snapshot/patch，不完整重生成 |
| `live-preview.md` | 启动预览或应用注解 | 用户要 preview/看效果/选元素；或 Step 7 后要求应用注解 | 生成中不得应用注解；应用注解必须已有 PPTX export |
| `customize-animations.md` | 对象级动画定制 | 用户要求动画顺序、效果、时序或开启元素动画 | 默认导出只有页间转场；元素动画 opt-in |
| `generate-audio.md` | 旁白/视频导出 | 用户要求 narration/audio/video；文档还写可导出后主动 offer | 不应直接调用 `notes_to_audio.py`，必须走 workflow |
| `img2img-support.md` | img2img 支持实现方案 | 实现级设计文档，不像运行 workflow | 应迁入 `docs/design/` 或标注 implementation draft，避免被当作运行流程 |

### 1.5 deep-research 子步骤

| 子步骤 | 产物 | 关键门禁 |
|---|---|---|
| `research/step1_outline.md` | `_research/step1_outline/outline.md/json` | 范围确认 BLOCKING；不得在 Step 1 用内置 WebSearch 补事实 |
| `research/step2_search_plan.md` | `_research/step2_search_plan/search_plan.json` | 搜索维度、轮次、来源、素材计划需用户确认 |
| `research/step3_search.md` | `_research/step3_search/pNN_*.md`、manifest、images | 必须执行 Step 2 计划，不得发散通用搜索 |
| `research/step4_consolidate.md` | `_research/step4_consolidated/consolidated.md` | 来源数量/缺口检查 |
| `research/step5_analysis.md` | `_research/step5_analysis/research_analysis.json` | 深度分析页比例 gate |
| `research/step6_narrative.md` | `_research/step6_narrative/research_report.md` | 叙事深度合同，不满足返回 Step 3 |
| `research/step7_visual.md` | `_research/step7_visual/visual_strategy.json`、`ref/` | `research_gate.py` 通过后才可 sync；参考图要求已加强 |

---

## 2. 文档权威层级模型

### 2.1 推荐权威等级

| 等级 | 层级 | 文件 | 可包含内容 | 不应包含内容 |
|---|---|---|---|---|
| A0 | 仓库入口最高约束 | `AGENTS.md` | 必读指针、最高兼容边界、安全边界、权威层级、少量高风险路由索引 | 详细 step 命令、workflow 内部步骤、长段专项规则 |
| A1 | 主流程权威 | `skills/ppt-master/SKILL.md` | 主 pipeline、全局执行纪律、主流程 gate、角色切换、质量门、后处理/export、上下文加载策略 | 专项 workflow 全部细节、设计草案、用户教程 |
| A2 | 专项流程权威 | `skills/ppt-master/workflows/*.md` | 某一 workflow 的 entry/exit/gate/fallback/commands | 全局主流程复制、无关 workflow 路由全集 |
| A3 | 角色/技术局部权威 | `skills/ppt-master/references/*.md`、`templates/**/README.md` | 被 SKILL/workflow 调用的角色行为、SVG/PPT 技术约束、资源使用规则 | 入口路由、项目治理原则 |
| A4 | 规则与贡献规范 | `docs/rules/*.md` | 编辑代码/prompt/workflow/docs/change 时的风格、评审、变更管理规则 | 具体 PPT 生成流程命令；与 A0-A3 冲突的行为规则 |
| A5 | 路由/架构摘要 | `docs/routing.md`、`docs/technical-design.md`、`docs/templates-architecture.md` | 速查、设计解释、架构对齐 | 新增权威规则，除非同步上升到 A0-A3 |
| A6 | 用户文档与草案 | `docs/getting-started.md`、`faq`、`roadmap`、`docs/design/*`、审计文档 | 解释、教程、计划、非目标、设计建议、历史审计 | 运行时强制规则，除非明确“已落地并链接权威文件” |

### 2.2 冲突裁决规则

| 冲突场景 | 裁决 |
|---|---|
| `AGENTS.md` vs `SKILL.md` 主流程细节 | `SKILL.md` 胜出；`AGENTS.md` 应改成指针或摘要 |
| `docs/routing.md` vs workflow 文件触发条件 | workflow 文件胜出；routing.md 只做同步摘要 |
| `docs/ai-router-design.md` vs 已有权威文件 | 已有权威文件胜出；ai-router-design 只能记录建议 |
| 用户文档 vs workflow/SKILL | workflow/SKILL 胜出；用户文档需更新解释 |
| `docs/rules/*.md` vs 当前既有文件 | 当前文件是事实基线；规则文件要么调整为 de facto，要么提出迁移计划 |

---

## 3. 现有冲突与重复规则清单

### 3.1 P0：必须立即对齐的实际冲突

| 问题 | 涉及文件 | 观察 | 建议 |
|---|---|---|---|
| Topic-only 入口冲突 | `AGENTS.md`、`SKILL.md`、`ppt-briefing.md` vs `docs/routing.md`、`docs/ai-rules-shared.md` | 当前权威路径是 `ppt-briefing -> 用户确认 -> deep-research`。但 `docs/routing.md` 表格和底部说明、`docs/ai-rules-shared.md` 仍可读成 deep-research 是第一入口 | 用户确认后更新 `docs/routing.md` 与 `docs/ai-rules-shared.md`，统一为 ppt-briefing 先行；不要修改 SKILL/AGENTS |
| Dashboard 默认浏览器行为冲突 | `AGENTS.md`、`SKILL.md` vs `docs/ai-rules-shared.md` | AGENTS/SKILL：本地默认 `--daemon` 自动开浏览器，`--no-browser` 只在 headless/remote/用户要求时加。ai-rules-shared 示例仍写 `--daemon --no-browser` | 更新 `docs/ai-rules-shared.md` 示例；保留非阻塞/只读边界 |
| `docs/ai-rules-shared.md` 权威措辞过强 | `docs/ai-rules-shared.md` vs `AGENTS.md`/`SKILL.md` | 文档自称 common rules 的 single source of truth，但又说 SKILL 是 authoritative。容易让轻量入口把它当更高权威 | 改为“shared summary / common baseline”，明确低于 AGENTS/SKILL |
| Batch-review 触发边界不清 | `SKILL.md`、`batch-review.md`、`docs/ai-router-design.md` | SKILL：用户请求才启用；workflow frontmatter：20+ 页或高质量项目“适用”；正文又说默认不启用 | 明确“20+ 页/高质量”只能作为向用户提示的推荐信号，不是自动触发 |

### 3.2 P1：重复、分散、易漂移

| 问题 | 涉及文件 | 风险 | 建议 |
|---|---|---|---|
| PPTX 路由边界重复 | `AGENTS.md`、`SKILL.md`、`docs/routing.md`、`docs/ai-router-design.md`、`docs/ai-rules-shared.md`、`docs/claude-reference.md`、`templates-guide.md` | 任一文件更新后容易遗漏其他入口 | 保留 A0/A1/A2 中的权威表；其他文档只链接 `docs/routing.md` 或标注“摘要” |
| Visual review 默认规则重复 | `AGENTS.md`、`SKILL.md`、`visual-review.md`、`docs/routing.md`、`ai-rules-shared.md` | “默认推荐/on by default/显式跳过”表述易漂移 | 以 SKILL Step 6 + `visual-review.md` 为权威；routing/共享规则只写一句摘要 |
| Live preview 注解窗口重复 | `AGENTS.md`、`SKILL.md`、`live-preview.md`、`docs/routing.md` | 生成中不可应用注解、Step 7 后应用的规则分散 | 保留在 SKILL Step 6/7 与 live-preview；其他处只链接 |
| Template/brand explicit path 规则重复 | `SKILL.md`、`create-brand.md`、`create-template.md`、`templates-guide.md`、`templates-architecture.md` | 裸名称不触发、索引只 discovery 的规则分散 | `SKILL.md` 保留执行权威，`docs/templates-architecture.md` 保留数据模型，用户文档只讲用法 |
| Change-log 责任范围偏窄 | `docs/change-log.md`、`docs/rules/README.md` | 当前 mandatory 只覆盖 `skills/ppt-master/scripts/workflows/references`，但 AGENTS、docs/routing、docs/ai-rules-shared 也会影响 agent 行为 | 新增 change-management 规则，规定入口/路由/规则文档修改也要记录或至少审计 |
| `docs/spec-review-template.md` 可能鼓励过快改权威规则 | `SKILL.md` Step 8a、`docs/spec-review-template.md` | 模板写“execute persist actions immediately”，可能绕过用户确认或治理检查 | 改成“提出修改并按 change-management 执行；高权威文件需确认” |

### 3.3 P2：结构和风格问题

| 问题 | 观察 | 建议 |
|---|---|---|
| `workflows/` 混入实现设计文档 | `img2img-support.md` 是实现计划，不是运行 workflow | 移到 `docs/design/` 或保留但加 Archive/Draft/Not runtime workflow 标头 |
| workflow 文件结构不统一 | 有些有 Trigger/Boundary/Gate，有些是长叙事或实现说明 | 新增 `docs/rules/workflow-style.md`，统一 Entry/Exit/Gates/Fallback/Authority |
| docs 根目录语言混杂 | 根目录主要英文，但已有中文审计/论文/设计内容；AGENTS 又要求目录内语言一致 | 制定文档语言规则：用户文档英中成对；审计/内部设计可按任务语言，但长期规则应有固定位置 |
| 设计草案落地状态不统一 | `docs/design/ppt-briefing-image-routing-design.md` 有 Archive status，其他设计文档状态不一 | 设计文档必须有 `Status: draft / active design / implemented / archived` 和权威链接 |
| 运行时读取策略仅在 SKILL 内 | AI 修改文档时缺少“读什么/不读什么”的规则 | 新增 `agent-governance.md`，规定读取顺序和草案不得变权威 |

---

## 4. AI agent 读取文档的推荐顺序

### 4.1 普通 repo 修改

1. `AGENTS.md`
2. `skills/ppt-master/SKILL.md` 的 Global Execution Discipline、Compatibility、Context Loading Strategy
3. 根据修改对象读取对应规则：
   - Python：`docs/rules/code-style.md`
   - references prompt：`docs/rules/prompt-style.md`
   - workflow：建议新增 `docs/rules/workflow-style.md`
   - docs：建议新增 `docs/rules/documentation-style.md`
   - 入口/路由：建议新增 `docs/rules/agent-governance.md`
4. 读取目标文件及其直接引用的权威文件
5. 不读取无关 workflow、设计草案或 roadmap，除非任务明确涉及

### 4.2 PPT 生成

1. `AGENTS.md`
2. `skills/ppt-master/SKILL.md`
3. 命中专项场景时读取对应 workflow：
   - topic-only：`ppt-briefing.md`，用户确认后 `deep-research.md`
   - existing PPTX：先用 PPTX route boundary 分类，再读 `template-fill-pptx.md` / `beautify-pptx.md` / 主流程
   - 续跑：`resume-execute.md`
   - preview/annotation：`live-preview.md`
   - charts：`verify-charts.md`
   - visual QA：`visual-review.md`
4. 按 SKILL 的角色切换协议读取 references
5. 不把 `docs/ai-router-design.md`、roadmap、用户教程当执行规则

### 4.3 文档治理/架构修改

1. `AGENTS.md`
2. `SKILL.md` Context Loading Strategy 与相关段落
3. `docs/rules/README.md` 和相关 rule
4. 目标文档及直接权威上游
5. `docs/change-log.md` 判断是否需记录
6. `docs/ai-router-design.md`、`docs/design/*` 只作为建议输入

---

## 5. 文档修改决策树

```text
要新增或修改一条规则？
  |
  |-- 它会改变 AI agent 进入仓库后的最高行为、安全边界或权威层级吗？
  |     -> 需要用户确认后进入 AGENTS.md；详细执行仍链接 SKILL/workflow
  |
  |-- 它会改变主 PPT 生成 pipeline 的步骤、gate、质量门、导出或角色切换吗？
  |     -> 需要用户确认后进入 SKILL.md；同步 routing 摘要
  |
  |-- 它只属于某个专项流程的 entry/exit/gate/fallback/commands 吗？
  |     -> 修改对应 workflows/<name>.md；只在 routing/AGENTS 保留触发摘要
  |
  |-- 它是角色行为、SVG/PPT 技术约束、prompt 执行约束吗？
  |     -> 修改 references/；必要时在 SKILL/workflow 增加读取指针
  |
  |-- 它是代码、prompt、workflow、文档编辑风格或变更管理规范吗？
  |     -> 放 docs/rules/<topic>.md；更新 docs/rules/README.md
  |
  |-- 它是未来架构、尚未实现的路由/脚本/orchestrator 方案吗？
  |     -> 放 docs/design/ 或 docs/*-design.md，并标注 draft/non-authoritative
  |
  |-- 它是用户说明、FAQ、教程、roadmap 或非目标吗？
        -> 放 docs/ 或 docs/zh/；必须链接权威文件，不得声明为执行权威
```

---

## 6. 新增/修改文档的放置规则

| 内容类型 | 放置位置 | 必须包含 | 禁止 |
|---|---|---|---|
| 仓库入口约束 | `AGENTS.md` | 权威层级、必读 SKILL、兼容/安全边界、少量高风险路由索引 | workflow 全流程复制、长命令清单扩张 |
| 主流程规则 | `skills/ppt-master/SKILL.md` | step、gate、blocking、role switch、quality/export、context loading | 实现草案、历史背景长篇解释 |
| 专项 workflow | `skills/ppt-master/workflows/<name>.md` | Title、When to run、When not、Inputs/Gates、Steps、Exit evidence、Fallback | 全局路由全集、无关主流程复制 |
| deep-research 子步骤 | `skills/ppt-master/workflows/research/stepN_*.md` | 输入、输出、gate、交接 | 跳出 orchestrator 的独立入口规则 |
| 角色/技术 reference | `skills/ppt-master/references/` | 命令式行为、技术约束、可检查标准 | 用户教程、roadmap、设计故事 |
| 代码/prompt/workflow/docs 规则 | `docs/rules/` | prescriptive rules、scope、examples、conflict handling | 具体业务流程步骤 |
| 用户教程/FAQ | `docs/`、`docs/zh/` | 用户场景、示例、链接权威 | 自称 workflow 权威 |
| 架构解释 | `docs/technical-design.md`、`docs/templates-architecture.md` | 设计理由、数据模型、权威链接 | 新流程强制规则，除非已同步 SKILL/workflow |
| 设计草案/实施计划 | `docs/design/` | Status、Non-authoritative 声明、目标、落地文件列表 | 伪装成已生效规则 |
| 审计报告 | `docs/*audit*.md` | 范围、发现、建议、需确认项 | 直接覆盖权威规则 |

---

## 7. 语言和风格一致性规则

### 7.1 语言规则

| 目录/类型 | 建议语言策略 |
|---|---|
| `skills/ppt-master/workflows/` | 单文件内不要中英文脚手架混杂；新 workflow 镜像同类文件语言。中文 workflow 可保留中英关键词如 `GATE/BLOCKING` |
| `skills/ppt-master/references/` | 遵循 `docs/rules/prompt-style.md`；标题/结构尽量英文，内容按既有文件 |
| `docs/` 用户文档 | 英文为根目录主版本，中文放 `docs/zh/`；若只写中文审计/内部方案，文件需明确“草案/审计”属性 |
| `docs/design/` | 可以按方案作者语言，但必须单文件语言一致，并写 Status |
| `docs/rules/` | 建议使用英文文件名；正文可先中文，但长期最好逐步形成英文主版本或双语摘要 |

### 7.2 风格规则

| 规则 | 说明 |
|---|---|
| 权威文件少解释，多命令 | A0-A3 文件以行为规则、gate、fallback 为主；设计动机放 docs/technical-design 或 docs/design |
| 草案必须标状态 | 第一屏写 `Status: draft/non-authoritative/implemented/archived` |
| 摘要必须链接权威 | routing、FAQ、getting-started 只写摘要，并链接 SKILL/workflow |
| 禁止“隐形升级” | 不能因为某设计文档写了建议，就让 agent 当成执行规则 |
| 每个规则只有一个 owner | 其他文件可引用/摘要，不重复完整规则 |

---

## 8. Workflow 文档治理规则

建议为所有 `skills/ppt-master/workflows/*.md` 采用统一骨架：

```markdown
# <Workflow Name>

> Authority: standalone workflow for <scope>. It does not override SKILL.md outside this scope.

## When to Run
...

## When NOT to Run
...

## Inputs
...

## Gates
...

## Steps
...

## Exit Evidence
...

## Fallback / Recovery
...

## Integration With SKILL.md
...
```

治理要求：

| 规则 | 说明 |
|---|---|
| 每个 workflow 只拥有自己的流程 | 不复制其他 workflow 的步骤；交叉点写链接和 handoff |
| 触发条件必须可判定 | 用 artifact + user intent，不用泛泛“适用于”当自动触发 |
| 默认/推荐/强制分离 | `Default`、`Recommended`、`Hard rule`、`BLOCKING` 语义必须明确 |
| Gate 必须有 evidence | 文件存在、命令通过、用户确认、receipt 行数等 |
| 运行 workflow 不等于修改主流程 | 如果 workflow 需要改变主 pipeline，先提“建议上升到 SKILL” |
| 实现计划不得混在 workflows | `img2img-support.md` 这类实现方案应迁到 `docs/design/` 或标注非运行 workflow |

---

## 9. docs/rules/ 扩展建议

当前 `docs/rules/` 只有：

| 文件 | 覆盖范围 | 缺口 |
|---|---|---|
| `prompt-style.md` | `skills/ppt-master/references/` | 不覆盖 workflow、AGENTS、用户文档 |
| `code-style.md` | `skills/ppt-master/scripts/` Python | 不覆盖 docs、workflow、变更管理 |
| `README.md` | rule index | 缺少 rule owner、适用路径、修改 checklist |

建议新增：

| 新文件 | 范围 | 核心规则 |
|---|---|---|
| `docs/rules/documentation-style.md` | `docs/`、`docs/zh/`、`docs/design/`、审计文档 | 文档类型、语言策略、状态标记、用户文档不得称权威 |
| `docs/rules/workflow-style.md` | `skills/ppt-master/workflows/` | workflow 骨架、entry/exit/gate/fallback、触发边界、非运行草案迁出 |
| `docs/rules/agent-governance.md` | `AGENTS.md`、`docs/ai-rules-shared.md`、`docs/routing.md`、AI 入口文件 | 权威层级、入口文件能写什么、摘要与权威同步、草案不生效 |
| `docs/rules/change-management.md` | 规则、workflow、references、scripts、AI 入口、routing、docs/design | 哪些改动必须记录 change-log、何时需要用户确认、风险等级、回滚策略 |

---

## 10. 建议上升、保留与降级的规则

### 10.1 建议上升到 `AGENTS.md`

需要用户确认后再改：

| 规则 | 理由 |
|---|---|
| 文档权威层级 A0-A6 的短表 | 入口处明确“谁说了算”，避免 agent 把 docs 草案当权威 |
| `docs/routing.md` 只是速查，不能覆盖 SKILL/workflow | 解决权威不清 |
| AI 修改权威文档前必须读取 `docs/rules/` 对应规则 | 让治理规则成为入口约束 |
| 设计草案不得自动生效 | 避免 `docs/ai-router-design.md` 之类被误用 |

不建议上升到 AGENTS：

| 内容 | 原因 |
|---|---|
| 具体 Confirm UI schema、image manifest、Step 7 命令细节 | 属于 SKILL/workflow |
| 每个 workflow 的完整触发和步骤 | 会让 AGENTS 继续膨胀 |

### 10.2 建议上升到 `SKILL.md`

需要用户确认后再改：

| 规则 | 理由 |
|---|---|
| 主流程进入前的 route preflight 小节 | 当前路由分散；可在 Step 1 前用 5-7 行分类 |
| topic-only 必须 `ppt-briefing -> confirm -> deep-research` 的权威表述 | SKILL 已有，可微调成更显眼的 route preflight |
| batch-review 只 opt-in，20+ 页只是“建议提示” | 解决 workflow/SKILL 表述边界 |
| route state 最小字段（可选） | 若未来实现 supervisor，可先定义轻量 artifact，不做 orchestrator |

不建议上升到 SKILL：

| 内容 | 原因 |
|---|---|
| Supervisor Router 完整设计 | 仍是设计草案，应留在 `docs/ai-router-design.md` |
| docs 目录治理细则 | 属于 `docs/rules/agent-governance.md` / documentation-style |

### 10.3 应保留在 workflow 的规则

| 规则 | Owner |
|---|---|
| beautify 1:1 页数/文字冻结、identity extraction、layout analysis | `beautify-pptx.md` |
| template-fill 直接 OOXML 填充、不进 SVG、source slide 可复用 | `template-fill-pptx.md` |
| resume Phase B sanity check | `resume-execute.md` |
| visual-review 并行 review team 与 vision fallback | `visual-review.md` |
| live-preview 注解应用和直接编辑细节 | `live-preview.md` |
| generate-audio voice/backend 推荐流程 | `generate-audio.md` |

### 10.4 应保留在 docs 草案/架构文档的内容

| 内容 | 位置 |
|---|---|
| Supervisor Router 完整分类表、route_state schema、自动化机会 | `docs/ai-router-design.md` |
| Dashboard 下一阶段实施计划 | `docs/design/dashboard-next-execution-guide.md` |
| Agent-Reach 集成设计 | `docs/design/agent-reach-integration.md`，落地后同步 workflow/reference |
| MemSlides 移植评估 | `docs/memslides-analysis.md` 或 `docs/design/` |

---

## 11. 分阶段迁移计划

### P0：必须立即对齐的冲突

建议修改文件：

| 文件 | 修改建议 | 是否需用户确认 |
|---|---|---|
| `docs/routing.md` | topic-only 行改为 `ppt-briefing -> 用户确认 -> deep-research -> main pipeline`；底部删除“deep-research is the single entry point”的误导表述 | 是 |
| `docs/ai-rules-shared.md` | 降级 single source of truth 措辞；topic-only 改为 ppt-briefing 先行；Dashboard 示例去掉默认 `--no-browser` | 是 |
| `skills/ppt-master/workflows/batch-review.md` | 明确 20+ 页/高质量是“建议提示用户选择”，非自动触发 | 是 |

### P1：整理重复规则和治理入口

建议修改文件：

| 文件 | 修改建议 | 是否需用户确认 |
|---|---|---|
| `docs/rules/README.md` | 加入新增 rule 文件索引和“选择哪个 rule”说明 | 是 |
| 新增 `docs/rules/documentation-style.md` | 文档类型、语言、草案状态、用户文档边界 | 是 |
| 新增 `docs/rules/workflow-style.md` | workflow 统一骨架和触发/gate 语义 | 是 |
| 新增 `docs/rules/agent-governance.md` | AGENTS/SKILL/routing/ai-rules-shared 权威层级 | 是 |
| 新增 `docs/rules/change-management.md` | 哪些文档改动必须记录、确认和回滚 | 是 |
| `AGENTS.md` | 加一小段“Document authority hierarchy”，链接 docs/rules；不复制本报告全文 | 是，且应最小化 |

### P2：后续结构优化

建议修改文件：

| 文件 | 修改建议 | 是否需用户确认 |
|---|---|---|
| `skills/ppt-master/workflows/img2img-support.md` | 迁到 `docs/design/img2img-support.md` 或加非运行 workflow 标记 | 是 |
| `docs/design/*.md` | 补 `Status`、`Authority`、`Implemented in` | 可批量小改，但仍需确认 |
| `docs/spec-review-template.md` | 将“execute persist actions immediately”改为按 change-management 执行，高权威文件需确认 | 是 |
| `docs/claude-reference.md` 与其他平台入口 | 逐步减少复制，改为链接 AGENTS/SKILL/routing | 是，建议单独阶段 |

---

## 12. 风险和回滚策略

| 风险 | 影响 | 控制策略 | 回滚 |
|---|---|---|---|
| 误把草案升级为权威 | agent 执行未实现流程 | 草案必须标 non-authoritative；权威变更只改 A0-A3 | revert 对应权威文件修改即可 |
| 一次性大改 AGENTS/SKILL | 入口行为改变面太大 | P0 先改摘要冲突；A0/A1 只加短规则 | 使用 git diff 审查，必要时回滚单文件 |
| workflow 触发收敛导致功能不可见 | 用户不知道可选能力 | 在 routing/AGENTS 保留短摘要，用户文档保留说明 | 恢复摘要，不恢复重复细节 |
| 语言重排引发文档迁移成本 | 中英文文档不同步 | 先制定规则，不立即移动所有旧文档 | 新规则只约束新增/大改文档 |
| change-log 负担过重 | 小文档修改成本上升 | change-management 区分高/中/低风险；只对 agent 行为和 skill 文件强制 | 调整 rule，不改历史 |

---

## 13. 后续可自动化检查项

| 检查 | 目的 |
|---|---|
| `docs_authority_lint.py` | 扫描 `docs/design/` 是否缺少 Status/Authority |
| `routing_consistency_check.py` | 比对 `docs/routing.md`、`AGENTS.md`、`SKILL.md` 的 workflow 名称和关键触发摘要 |
| `topic_only_rule_check.py` | 检测文档中是否仍写 “topic-only -> deep-research first” |
| `dashboard_command_check.py` | 检测默认 Dashboard 示例是否误带 `--no-browser` |
| `workflow_header_check.py` | 检查 workflow 是否有 When to Run / When NOT / Gates / Exit Evidence |
| `rule_index_check.py` | 检查 `docs/rules/*.md` 是否都登记在 README |
| `change_log_scope_check.py` | 修改 `skills/ppt-master/scripts/workflows/references` 时提醒更新 change-log |
| `draft_authority_phrase_check.py` | 禁止 draft/design 文档出现 “MUST/authoritative” 且无 non-authoritative 声明 |

---

## 14. 下一阶段建议先改哪些文件

最低风险顺序：

1. 修改 `docs/routing.md`：只修 topic-only 路由摘要，明确 ppt-briefing 先行。
2. 修改 `docs/ai-rules-shared.md`：降级权威措辞、修 topic-only、修 Dashboard 默认命令。
3. 修改 `skills/ppt-master/workflows/batch-review.md`：把 20+ 页/高质量改为“提示用户选择”，不是自动激活。
4. 新增 `docs/rules/agent-governance.md` 和 `docs/rules/documentation-style.md`，再更新 `docs/rules/README.md`。
5. 经用户确认后，在 `AGENTS.md` 加一个很短的“Document Authority”段落，链接 `docs/rules/agent-governance.md`。
6. 后续再处理 workflow-style、change-management、`img2img-support.md` 迁移和设计文档 Status 标注。

所有 P0/P1 改动都建议先由用户确认，因为它们会影响未来 AI agent 的读取和路由行为。本文只作为后续修改 `AGENTS.md`、`SKILL.md`、`docs/rules/` 和路由摘要的依据。
