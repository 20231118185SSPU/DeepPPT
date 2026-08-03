# 后续迁移路线图：ppt（v4.3.0）→ DeepPPT2（Phase 2-5）

> 承接 2026-08-03 完成的 Phase 1（三阶段 Confirm UI 迁移 + 完整性/审计工具）。
> 本文档是后续四个阶段的实施计划，按依赖顺序排列；每阶段独立成会话语，完成即验证、即记录。

---

## 总览

| 阶段 | 内容 | 依赖 | 工作量 | 风险 |
|---|---|---|---|---|
| **Phase 2** | SKILL.md 四路由重构（routing.md + generate-pptx.md + 工作流目录重组 + 薄入口 SKILL.md） | 无 | 1–1.5 会话 | 高（全仓引用面） |
| **Phase 3** | 原生 PPTX 增强套件（native_enhance_pptx 系列 + 交付检查 + 统一转场注册表） | Phase 2 | 1–1.5 会话 | 中 |
| **Phase 4** | 视频导出（powerpoint_video + 动效/字幕 + narration_sync） | Phase 3 | 0.5–1 会话 | 中（依赖本机 PowerPoint/ffmpeg） |
| **Phase 5** | 原生形状/结构化模板体系（pptx_shapes + semantic-svg + 模板物化工具） | Phase 2 | 1.5–2 会话 | 高（触碰 Executor 输出契约） |

**总原则**（沿用 Phase 1 的执行规范）：
- 每个阶段开始前跑 `smoke_check.py --skip-help` 建基线，结束后对比通过数
- 脚本层优先整份拷贝（ppt 套件脚本均只依赖标准库），再逐项核对 DeepPPT2 特有依赖
- 所有 workflow/reference/scripts 改动记入 `docs/change-log.md`；踩坑沉淀到 `.align/lessons.md`
- SKILL.md / 路由文件改动标注 `[NEEDS_HUMAN_REVIEW]`
- 不引入 ppt 的 sponsors/营销文档；DeepPPT2 独有体系（dashboard、deep-research、spec_lock/page_expression 合同、质量门、图片来源路由、视觉门禁）一律保留并作为新能力的适配锚点

---

## Phase 2 — SKILL.md 四路由重构（先做）

**目标**：把 900+ 行的厚入口 SKILL.md 改为「薄入口 + routing.md 分发」，让 DeepPPT2 的主流程文档与上游架构对齐，同时为 Phase 3-5 提供路由落位。

**核心事实**：ppt 的 `generate-pptx.md`（614 行）与 DeepPPT2 当前 SKILL.md 的 Step 1-7 结构一一对应（Source → Project → Template → Strategist → Image → Executor → Post-processing），提取基本是机械迁移。

### 2.1 交付物

| 交付物 | 来源 | 适配要点 |
|---|---|---|
| `workflows/routing.md` | ppt `workflows/routing.md`（139 行） | 四路由矩阵；Enhance 路由行先占位（权威文档随 Phase 3 落地）；DeepPPT2 独有工作流映射为 Generate 路由的 stage/profile |
| `workflows/generate-pptx.md` | ppt 版 + DeepPPT2 SKILL.md Step 1-8 现文 | **主体**：把 SKILL.md 的 Step 1-8 内容搬入；保留 DeepPPT2 独有内容（deep-research/briefing 前置、spec_lock/page_expression 合同、harness_gate/e2e_validate/rendered_layout_check/visual-review 门禁、split-mode、memory_manager、image-source-routing） |
| `workflows/index.md` | ppt `workflows/index.md` | 路由索引 |
| `workflows/stages/` | DeepPPT2 现有 11 个独立工作流迁入 | resume-execute / refine-spec / live-preview / verify-charts / visual-review / customize-animations / generate-audio + 新增 topic-research（DeepPPT2 的 deep-research/briefing 保留为前置流程） |
| `workflows/profiles/` | ppt `profiles/quick-generate.md` + DeepPPT2 `beautify-pptx.md` | quick-generate 为**新增**能力（用户反馈"效率不高"的对应解）；beautify 迁入 profiles/ |
| `workflows/create-template/` | ppt `create-template/`（brand/layout/deck 拆分）+ DeepPPT2 `create-brand.md` 现文 | 品牌工作流并入 create-brand 子工作流；模板治理规则保留 |
| `workflows/template-fill-pptx.md` | 现状保留（DeepPPT2 已有） | 迁移到路由结构 |
| `SKILL.md` | 压缩为薄入口 | 保留 frontmatter + 全局纪律 7-9 条 + 强制加载顺序（attribution_guard）+ 路由表 + 索引；[NEEDS_HUMAN_REVIEW] |
| `AGENTS.md` | 重写命令速查与路由提示 | 指向 routing.md；Phase 1 的 confirm 命令序列保留 |

### 2.2 DeepPPT2 独有工作流的去向（不删除，全部保留）

| 现有工作流 | 归位 |
|---|---|
| `ppt-briefing.md` / `deep-research.md` / `research/`（step1-7） | Generate 路由前置流程（topic-research stage 的 DeepPPT2 增强版） |
| `content-selection.md` / `detailed-outline.md` / `image-text-linking.md` | Generate 路由条件 stage |
| `revision-loop.md` / `batch-review.md` | Generate 路由辅助流程（保留独立文档） |
| `create-brand.md` | create-template 子工作流 |

### 2.3 验证
- smoke_check 基线/对比
- 全仓链接检查：`grep -rn "workflows/[a-z-]*\.md"` 逐条核对新路径（重点：SKILL.md、AGENTS.md、references/、scripts/docs/、docs/）
- 引用 attribution_guard 的门禁文件清单核对（Phase 2 不移动 scripts/，清单应保持有效）
- 用 `_smoke_` 项目跑一次 Generate 主流程入口（到 Step 4 三阶段确认完成为止）

### 2.4 风险与对策
- **全仓引用面最大**：workflows/ 路径移动会击穿 SKILL.md/AGENTS.md/references/scripts docs 中的相对链接 → 对策：迁移后做一次全仓 grep 链接核对，作为本阶段独立检查点
- 薄入口后 DeepPPT2 的独有门禁规则可能"散落" → 对策：generate-pptx.md 中保留完整门禁段落，SKILL.md 只留全局纪律

---

## Phase 3 — 原生 PPTX 增强套件

**目标**：给已完成的 PPTX 追加备注、旁白音频、自动播放时序、页间转场（append-oriented，不重建幻灯片）。

### 3.1 迁移清单

| 文件 | 行数 | 处理 |
|---|---|---|
| `scripts/native_enhance_pptx.py` | 42 | 整份拷贝（CLI shim） |
| `scripts/native_enhance_pptx_core.py` | 2490 | 整份拷贝；核对与 DeepPPT2 `generate-audio` / `notes_to_audio.py` / `animation_config.py` 的音频/时序 schema 差异，做映射 |
| `scripts/native_payloads.py` | 655 | 整份拷贝 |
| `scripts/native_narration_pptx.py` | — | 旧 CLI 兼容 shim，拷贝 |
| `scripts/pptx_opc_validation.py` | 210 | 整份拷贝 |
| `scripts/pptx_delivery_check.py` | 1133 | 整份拷贝；核对与 DeepPPT2 `pptx_quality_check.py` / `e2e_validate.py` 的职责边界（互补不重复） |
| `scripts/pptx_effects.py` | 143 | 整份拷贝 |
| `scripts/pptx_transitions.py` + `pptx_animation_presets.json` | — | **统一转场注册表**：评估 DeepPPT2 `svg_to_pptx.py` 现有转场实现，决定切换为共享注册表（推荐，消除双实现） |
| `workflows/native-enhance-pptx.md` | 393 | 适配：确认 UI 用它自己的增强计划确认（Phase 1 的三阶段流直接复用） |
| `workflows/routing.md` | — | 补全 Enhance 路由行（Phase 2 占位处） |

### 3.2 适配要点
- **音频路径冲突**：DeepPPT2 的 `generate-audio`（edge-tts 逐页旁白）与 native_enhance 的音频注入需统一 schema（audio 配置、timing 来源）；决定 generate-audio 是否改走 native 管线
- `attribution_guard.py` 门禁文件清单追加 `native_enhance_pptx.py` 等新入口
- `pptx_opc_validation` 可接入 `e2e_validate.py` 之后作为 export 后结构校验（可选）

### 3.3 验证
- smoke_check；`_smoke_` 项目：导出 PPTX → init/plan/validate/apply → 用 `pptx_opc_validation` + `pptx_delivery_check` 验证输出 → 打开检查备注/转场
- generate-audio 全链路回归（不因 schema 统一而破坏现有旁白导出）

---

## Phase 4 — 视频导出（2026-08-03 已执行：动画链完整移植 + 4 个视频脚本）

**目标**：用本机 PowerPoint 把带旁白的 PPTX 编码为视频，含动效规划与字幕对齐。用户选择**完整移植动画链**（而非推迟动画依赖项）。

### 4.1 实际迁移清单（完成）

| 文件 | 处理 |
|---|---|
| `scripts/powerpoint_video.py` / `video_subtitles.py` / `video_motion_plan.py` / `narration_sync.py` | 整份拷贝；narration_sync 改 3 处 import（`native_pptx_animations` / `svg_to_pptx.pptx_narration` / 本地 animation_config） |
| `scripts/slide_roster.py` | 整份拷贝（动画校验链依赖，44 行） |
| `svg_to_pptx/animation_config.py` | 以 ppt 版（1505 行）替换（259 行），import 适配 5 处 |
| `scripts/animation_config.py`（顶层） | 同步替换为 ppt 版（152 行） |
| `svg_to_pptx/semantic_markers.py` | 新增最小版（is_static_page_frame 链，完整语义标记待 Phase 5） |
| `svg_to_pptx/drawingml_converter.py` | trace 每条记录增加 `page_role` |
| `svg_to_pptx/pptx_builder.py` | 构建后增强：用共享校验器（validate_generated_transition/animation_xml）从**实际写入的 slide XML** 推导 `motion`（advance_after_ms）与 `animation`（rows[]）写入 trace；best-effort，失败只省略字段不阻断导出；不替换现有时序 XML 写入路径 |

### 4.2 适配要点（实际）
- 环境依赖：PowerPoint 本体（Windows，`--check` 探测）、stable-ts（`video_subtitles` 可选，文档化 `pip install stable-ts`）、ffmpeg/ffprobe（本机已装）、numpy（已装）
- `generate-audio` 增加 Step 4.5 视频导出分支；`docs/audio-narration.md`（en/zh）增补自动导出章节
- animations.json schema 升级（slide 级 transition/animation 作用域、defaults.effect `none`）——customize-animations 回归验证

### 4.3 验证（执行）
- smoke_check 64→69（+5 新脚本自动纳入）
- 动画链 e2e：trace 字段（page_role/animation.rows/motion.advance_after_ms）→ video_motion_plan 生成 motion plan
- narration_sync 三子命令 e2e；`powerpoint_video --check` 探测如实报告

## Phase 5 — 原生形状/结构化模板体系（2026-08-03 已执行：预设形状套件 + 规范文档迁移；structured 导出按回退条款记为 opt-in 路线图项）

**目标**：Office 预设形状渲染、布尔运算、Master/Layout/Placeholder 语义元数据 → 结构化导出。

### 5.1 迁移清单

| 文件 | 行数 | 处理 |
|---|---|---|
| `scripts/pptx_shapes/`（models/loader/registry/semantic_hash/formula/xml_safety/errors/data） | 1795 | 整份拷贝 |
| `scripts/preset_shape_svg.py` / `shape_boolean_svg.py` | 422 | 整份拷贝 |
| `scripts/compact_svg_coordinates.py` | — | **Phase 1 推迟项，此时迁入**（模板作者工作流配套） |
| `scripts/svg_authoring_view.py` / `slide_roster.py` | — | Phase 1 推迟项，评估后迁入（slide_roster 数值排序修复如与 svg_to_pptx 现有顺序逻辑冲突则跳过） |
| `references/semantic-svg.md` / `pptx-structure-interface.md` / `native-shape-authoring.md` / `native-data-interface.md` / `shared-standards-core.md` / `svg-effects.md` | — | 规范文档迁移 + **接口映射**到 DeepPPT2 的 spec_lock/page_expression 合同体系（不照搬） |
| 模板物化工具 | — | `mirror_template_materialize.py` / `template_preview_pptx.py` / `template_text_slots.py` / `extract_svg_pictures.py` / `slice_images.py`，对接 DeepPPT2 模板治理（register_template / templates 目录） |

### 5.2 适配要点（最深的一层）
- **structured 导出模式**：semantic-svg 的 `data-pptx-master/layout/placeholder` 元数据 → 真实 `p:sldMaster`/`p:sldLayout` 继承，会改变 Executor 的输出契约 → 先以「规范文档 + 增量启用」方式落地：默认不开启，`spec_lock` 中显式声明 structured 模式才启用，避免破坏现有 40+ 页流程
- Executor 角色文档（executor-base.md）需要新增 structured 模式章节或独立 executor-structured 参考（ppt 已拆分 5 个 executor 角色文件——是否跟随拆分在本阶段单独评估，不预设）
- 模板物化工具与 DeepPPT2 `create-template` / 模板预览（Phase 1 的 `/template-file` 路由）复用同一 templates 目录事实源

### 5.3 验证
- smoke_check；`_smoke_` 项目：预设形状 SVG → 导出 → OPC 校验 Master/Layout 结构 → PowerPoint 打开人工确认
- 非 structured 模式回归：现有导出路径 0 变化

### 5.4 执行结果（2026-08-03，全部完成）
- **脚本闭环**：`pptx_shapes/`（187 预设）+ `preset_shape_svg.py` + `prstgeom_to_svg.py`（beautify 反向闭环）+ `preset_authoring/registry_to_svg/svg_markup` 加性迁移完成，`fmt_num` 已在 DeepPPT2 的 `pptx_to_svg/emu_units.py`（此前盘点路径有误，实际无需补移植）
- **物化工具**：`template_preview_pptx.py`（适配 flat 面 + 本地 viewBox 锁 + 补回 `@contextmanager`）、`template_text_slots.py`、`extract_svg_pictures.py`、`slice_images.py`、`compact_svg_coordinates.py`、`svg_authoring_view.py`、`slide_roster.py` 可用；**`mirror_template_materialize.py` 按回退条款删除并推迟**（依赖 template_structure 3456 行 + ppt drawingml 包重构）
- **规范文档**：6 份（semantic-svg / pptx-structure-interface / native-shape-authoring / native-data-interface / shared-standards-core / svg-effects）迁移 + 每份头部「DeepPPT2 接口映射」注记（锚定 spec_lock/page_expression 合同、flat/structured 边界）
- **structured 导出（回退条款落地）**：`spec_lock.md` 模板新增 `## pptx_structure`（`mode: flat|structured`，默认 flat，当前仅 flat 有 wiring）；`svg_to_pptx.shape_boolean` 因符号面不兼容（ast diff：paths 14 / utils 102 缺失）与 `mirror_template_materialize` 一并记为延期的 opt-in 路线图项，specs 先行、接线后补；`shape_boolean_svg.py` 缺省核心时输出清晰降级信息
- **验证**：预设形状/物化工具 e2e 15/15；Phase 3（native enhance）与 Phase 4（视频/动画链）回归全过；smoke 156 passed / 0 failed / 4 skipped（160 checks）；`_smoke_*` 已清理

**Phase 6（2026-08-03 执行完毕）——重构版导出器整体迁移**：

用户基于实际痛点（排版/文字元素溢出诊断不足）决定放弃"保持 opt-in"路线，完整迁移 ppt 的重构版导出器与诊断体系：

1. **包体**：`svg_to_pptx/` 整体替换为 ppt 重构版 40,328 行（drawingml 9 模块 + pptx_package 10 模块 + native_objects 10 模块 + shape_boolean/text_outline/canvas_contract/geometry_properties）；`svg_finalize/` 全套配套升级；`pptx_animations.py` 升级 3932 版
2. **checker**：`svg_quality/` 包（8,448 行）整体迁移——真实文字度量硬错误、transform 感知 bounds 溢出契约、21 类 SVG→DrawingML 语法契约；DeepPPT2 特有 8 项检查 + must_fix/should_fix 分级 + --integrated-review 以 `svg_quality/deepppt_extensions.py` 增量保留
3. **消费面**：9 个顶层脚本 import 适配（native_enhance/narration_sync/template_preview/template_fill×2/delivery_check/shape_boolean/薄壳）；CLI 加回全部 DeepPPT2 特有 flag（--svg-snapshot/--only/--native/--no-compat/--cache-dir/--no-cache/--keep-cache/--workers）
4. **structured 导出：已接线**（原 opt-in 路线图项落地）——`pptx_structure.mode: structured` 编译真实 Master/Layout 部件；`svg_to_pptx.shape_boolean` 真实核心可用（skia-pathops 可选）
5. **验证**：溢出诊断 3/3（负 letter-spacing → cx=-70104 硬错误；文本超模块 bounds → 379.8% 量化溢出）；Phase 3/4/5 + quick 全量回归全过；smoke 158 passed / 0 failed / 4 skipped（162 checks）

**行为契约变化（迁移后需注意）**：
- release 导出要求 spec_lock.md 完整主题契约（canvas/typography font_family+title_family+body_family/colors/pptx_structure.mode）——DeepPPT2 的 lock 模板已含全部字段
- `--quick-generate` 恢复质量报告指纹门（checker --stage final --json 产物 → 导出校验匹配）
- `--conversion-trace` 默认写 `validation/<stem>.trace.json`（旧版写 pptx 旁）
- `use_native_shapes=False`（纯 PNG 图片模式）按 ppt 设计废弃；`--svg-snapshot` 经新 builder legacy 渲染实现
- `--recorded-narration` 二次导出默认读项目根 `narration_animations.json`

---

## 跨阶段注意事项

1. **attribution_guard 门禁清单**：每阶段新增关键入口脚本后，追加到 `_REQUIRED_GATE_FILES`（scripts 不移动，Phase 2 无需改）
2. **docs/ 用户文档**：`docs/technical-design.md` / README 功能对比表在 Phase 2/5 完成后各更新一次（避免每阶段都改）
3. **每阶段结束时**：`docs/change-log.md` 追加、`.align/lessons.md` 沉淀、临时 `_smoke_*` 目录清理、确认无残留服务进程
4. **Phase 2 之前的待确认事项**（不阻塞计划，但影响 Phase 2 交付）：
   - quick-generate profile 是否纳入（推荐纳入——对应"效率不高"诉求）
   - Phase 3 是否让 generate-audio 改走 native 增强管线（统一音频注入路径）
   - Phase 5 structured 导出模式是否默认开启（推荐默认关闭、显式启用）

---

## 推荐执行顺序回顾

**Phase 2（重构）→ Phase 3（原生增强）→ Phase 4（视频）→ Phase 5（形状/模板）**

理由：
- Phase 2 先行让 Phase 3-5 的工作流文档直接落位路由架构，避免二次搬迁（脚本层与架构无关，随时可迁，但工作流文档是架构载体）
- Phase 4 依赖 Phase 3 的音频/时序注入
- Phase 5 对 Executor 契约改动最深，放到最后、基于稳定后的路由架构做接口映射
