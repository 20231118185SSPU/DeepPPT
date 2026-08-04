# Change Log

> Record of modifications to workflow files, references, and scripts under `skills/ppt-master/`.
> Purpose: audit trail for AI-driven changes, regression tracking, and human review.
>
> **Mandatory**: every modification to `skills/ppt-master/scripts/`, `skills/ppt-master/workflows/`, or `skills/ppt-master/references/` MUST be logged here.

---

## Format

```
### YYYY-MM-DD — <short description>
- **Files**: <list of modified files>
- **Reason**: <why the change was made>
- **Before**: <key behavior before the change>
- **After**: <key behavior after the change>
- **Risk**: low / medium / high
- **Human reviewed**: yes / pending / N/A
```

---

## Log
### 2026-08-04 — Phase 7 依赖/Provider/CLI 卫生：入口统一 SystemExit + 盘点验证
- **Files**: `analyze_images.py`、`finalize_svg.py`、`gemini_watermark_remover.py`、`generate_examples_index.py`、`image_gen.py`、`pptx_animations.py`、`svg_patch.py`、`svg_quality_checker.py`、`total_md_split.py`、`vision_check.py`（10 个入口 `main()` 裸调用 → `raise SystemExit(main())`）
- **Reason**: `plans/deepppt2-system-optimization-agent-brief.md` Phase 7 T7.6；裸调用会在 main 未来返回非 0 int 时静默丢 rc（当前 main 均返回 None，错误靠内部 sys.exit——行为零变化，契约显式化）。
- **Before**: 10 个入口 `if __name__ == "__main__": main()`（无 SystemExit 包装）；依赖/Provider/凭据边界无系统复核。
- **After**: 全部 85 个顶层入口统一 `raise SystemExit(main())`（复核 NONE 裸调用）；T7.1 依赖盘点（requirements 无未使用依赖，5 个"未见"均为别名 bs4/PIL/fitz/pptx/google）；T7.2 Provider 软失败验证（backend 按需 `__import__` + ImportError 友好 pip 提示；无凭据 --help 全 rc=0）；T7.3 三 backend 接口一致；T7.4 凭据仅经 require_api_key 读环境变量，无值打印/写入；T7.7 JSON 输出纯净（harness/spec_compliance/prompt_audit --json 实测）；T7.8 29 脚本 utf8 处理；T7.9 分类（19 satellite 子目录 + 85 顶层 + 8 helper）。
- **Verified**: guard rc=0；完整 smoke 166/0/4/170（与上批一致）；integration 187/0/4/191；governance drift 5 PASS；13.1 性能结论：无热点批次（干净基线健康 + Known constraint 不重试懒加载）。
- **Risk**: low（10 个入口行为等价——main 均返回 None，SystemExit(None)=exit 0；坏参数 rc 由 argparse/内部 sys.exit 决定，实测不变）
- **Human reviewed**: pending

### 2026-08-04 — Phase 6 pptx_animations 拆分：animation_constants + animation_effects 抽取
- **Files**: `skills/ppt-master/scripts/animation_constants.py`（新增：动画常量/预设目录/效果池，295 行）、`skills/ppt-master/scripts/animation_effects.py`（新增：效果归一化/目标类/语义池，~700 行）、`skills/ppt-master/scripts/pptx_animations.py`（保留时序/校验组 + 全公开面 re-export，2993 行）
- **Reason**: `plans/deepppt2-system-optimization-agent-brief.md` Phase 6（热点评分 10/12 达拆分门槛，用户批准）；pptx_animations churn 18、8 消费者、77 顶层符号——常量/效果/时序/校验四职责混于 3900 行。
- **Before**: 单文件 3900 行四职责混排；任何动画改动触及全部消费者。
- **After**: 严格单向依赖链 constants←effects←pptx_animations（AST 验证无环）；`pptx_animations.py` 保留全部 35 个公开符号 + 消费者所用私有符号（公开面完整性检查 missing=0）；7/7 真实消费者 import 通过。
- **Verified**: characterization fixture 18 keys 前后 0 diffs（旧版 git HEAD vs 新版行为一致）；guard rc=0；完整 smoke 162→166（+2 新模块 ×2 checks）/0/4/170；integration 187/0/4/191；带动画导出（-a auto -t fade）rc=0 且 8/8 slide 含 p:timing XML。
- **Risk**: low-medium（机械抽取 + 兼容面验证；残余风险=未覆盖的动画边缘路径——characterization 覆盖核心 API，导出抽查覆盖端到端）
- **Human reviewed**: pending

### 2026-08-04 — Phase 5 运行可观测性：trace event envelope v1 + trace 契约文档
- **Files**: `skills/ppt-master/scripts/dashboard/trace_writer.py`（envelope 规范化：schema_version/operation/route/status/duration_ms/error_code 槽位）、`skills/ppt-master/scripts/docs/trace-contract.md`（新增：envelope 契约 + 敏感禁令 + 指标来源表 + null/0 语义）
- **Reason**: `plans/deepppt2-system-optimization-agent-brief.md` Phase 5（T5.1-T5.6）；trace 事件无统一 envelope（各写点自由传字段）、无 schema 版本、指标来源未文档化。
- **Before**: `trace_event` 只写 {ts, type, detail} + 自由 extra；无 schema_version；reader 已容错但契约未文档化。
- **After**: `trace_writer._normalize_event` 强制 v1 envelope（schema_version=1、operation 默认=type、route/status/duration_ms/error_code 显式 null 槽位——null=未测量、0=实测，T5.6）；旧事件（无 schema_version）reader 继续容忍（实测新旧混合可读）；敏感禁令与指标来源表写入 trace-contract.md（阶段耗时/失败率/重试率/gate 错误分布可从 trace+harness.json 获取；用户修订次数明确"未采集"不伪造）。
- **Verified**: guard rc=0；smoke --skip-help 80/0/3/83；integration 183/0/4/187（与上批一致）；envelope 单测（新事件带 schema_version/operation/null 槽、调用方值保留、旧事件原样可读）；Dashboard /api/log 读 trace_store 正常。
- **Risk**: low（写侧纯增量字段；reader 兼容性实测通过；无运行行为变化）
- **Human reviewed**: pending

### 2026-08-04 — Phase 4 契约回归：CLI 错误路径探测 + gate 状态场景 + 双门全量
- **Files**: `skills/ppt-master/scripts/smoke_check.py`（integration Test 9：confirm_ui_gate 状态场景 5 断言）；其余为验证记录（无运行代码变更）
- **Reason**: `plans/deepppt2-system-optimization-agent-brief.md` Phase 4（Gate G1 已批准）；T4.2 全 CLI 错误路径无回归覆盖；T4.5 gate 状态场景（pending template/stale/fallback）无断言；T4.8 双门全量未跑。
- **Before**: Test 8 只覆盖 gate 坏输入；CLI 错误路径无系统探测；e2e 全量未验证。
- **After**: T4.2 探测 65 个 argparse CLI 入口坏参数 0 静默 + 12 个项目类 CLI 缺文件 0 静默；Test 9 覆盖 pending template_selection / chat fallback（±--allow-fallback）/ stale confirmed_at / fresh browser result；T4.6 harness_gate `--read-only` 实测零写入（hash 对比）+ 写模式 quality/harness.json（12 键）与 trace.jsonl（gate_result envelope）schema 稳定；T4.8 examples checker 29/29 + e2e 29/29 双门全绿。
- **Verified**: guard rc=0；完整 smoke 162/0/4/166；integration 183/0/4/187（+5 Test 9）；governance drift 5 PASS；T4.7 CI 评估完成（smoke job 可加 `--integration`，预计 +60s；prompt_audit 需 tiktoken——**本批未改 CI**，待批准）。
- **Risk**: low（纯验证 + 测试追加）
- **Human reviewed**: pending

### 2026-08-04 — Phase 3(9.1-9.2) Prompt 治理元数据 + 加载策略收敛：Generate typical -21.2%
- **Files**: `skills/ppt-master/scripts/prompt_audit_manifest.json`（authority_edges 9 条 + registries 6 个 + schema_grammars 2 个 + 13 个 selector load_event + 新建 generate-on-demand load set）、`skills/ppt-master/references/shared-standards.md`（§7 加 svg-effects on-demand 指针 1 行）
- **Reason**: `plans/deepppt2-system-optimization-agent-brief.md` Phase 3（Gate G1 已批准）；F7 治理元数据全空；Generate typical 165,611 中 9 个文档为按需/低频（svg-effects 13.5k 无任何必读引用、animations 仅 Step 7 引用、semantic-svg/pptx-structure-interface 仅 structured 模式、README 工具索引、batch-review/revision-loop/reviser 可选流程、visual-review 仅 stages 版引用）。
- **Before**: authority_edges/registries/schema_grammars = []；selector load_event 全空；generate fixed 23 个文档（165,662 typical）；svg-effects 无可发现指针。
- **After**: 9 条权威边（全真实链接、无环）+ 6 个 registry（modes 5/visual_styles 18/renderings 20/palettes 14/type_templates 11/charts 71，index 链接与数量声明一致）+ 2 个 schema grammar owner（spec_lock_reference、confirm_ui）+ 13 个 load_event；9 个按需文档移入新 `generate-on-demand` load set（coverage 闭合 171+1，非 exempt 扩大、非漏登记）；generate typical **165,662 → 130,528（-21.2%）**，全部 load set status=pass。
- **Verified**: prompt_audit rc=0 / errors=0 / warnings=8（7 个 schema multi-def 候选=编排文档行为描述已记录 + 1 个 near-duplicates 184 对）；guard rc=0；smoke --skip-help 80/0/3/83；完整 smoke 162/0/4/166；integration 178/0/4/182；governance drift 5 PASS；hard-rule 文件（SKILL.md/generate-pptx/routing/executor-base）本批零改动；每按需文档有既有引用路径（svg-effects 新指针补全）。
- **Risk**: low-medium（文档内容零修改，仅加载配置变窄——硬约束与质量规则不动；残余风险=Agent 少读按需文档的可能行为差异，需真实演练/固定 Brief A/B 验证，属 G2/用户授权范围）
- **Human reviewed**: pending

### 2026-08-04 — Phase 2(8.2) JSON 契约：result.json schema 文档化 + confirm_ui_gate 坏输入回归
- **Files**: `skills/ppt-master/scripts/docs/confirm_ui.md`（新增 result.json schema contract 声明）、`skills/ppt-master/scripts/smoke_check.py`（integration Test 8：confirm_ui_gate 坏输入断言）
- **Reason**: `plans/deepppt2-system-optimization-agent-brief.md` T2.7-T2.10（Gate G1 已批准）；result.json 无 schema_version 且无消费者读取；gate 是 fail-closed 门禁但坏输入行为无回归覆盖。
- **Before**: result.json schema 约定散落在文档与代码；坏输入行为（缺 status/stage、坏 confirmed_at、坏路径）无自动化断言。
- **After**: confirm_ui.md 显式声明 schema contract（无强制 schema_version——加了零读者；字段 owner=本文档；legacy 单次 result 兼容策略；未知字段容忍；坏输入 rc 非零且提示可行动）；smoke `--integration` Test 8 覆盖 5 种坏输入 + 1 种合法含未知字段。
- **Verified**: guard rc=0；完整 smoke 162/0/4/166（与上批一致）；`--skip-help` 80/0/3/83；`--integration` 178/0/4/182（+5 Test 8）；T2.8 枚举盘点（generation_mode 值域 continuous/None 与文档一致；route 三值与 generate-pptx.md 一致——无代码变更）；T2.9 复核（quality 报告读侧已收敛 find_quality_report、trace.jsonl 读写同源、checkpoint schema Phase 1 已定——无代码变更）。
- **Risk**: low（文档 + 测试追加；无运行行为变化）
- **Human reviewed**: pending

### 2026-08-04 — Phase 2(8.1) spec_lock 单一 parser owner：spec_lock_reader + 消费者迁移
- **Files**: `skills/ppt-master/scripts/spec_lock_reader.py`（新增：canonical spec_lock.md reader）、`skills/ppt-master/scripts/update_spec.py`（`parse_lock` 变兼容 wrapper）、`skills/ppt-master/scripts/e2e_validate.py`（两个自研解析改为 canonical wrapper）、`skills/ppt-master/scripts/layout_capacity_check.py`（`parse_spec_lock` 改为 canonical wrapper）、`skills/ppt-master/scripts/svg_quality/checker.py`（幽灵 import 消除 + `_ANCHOR_COMPARE_ENABLED` 旗标）
- **Reason**: `plans/deepppt2-system-optimization-agent-brief.md` T2.1-T2.6（Gate G1 已批准）；F6 多套局部解析：e2e/layout_capacity/checker 各自维护 section 正则；checker 的 `_parse_spec_lock` 来自不存在的 `project_management.project_specs`（try/except 静默降级，anchor/typography 检查从未生效）。
- **Before**: parse_lock（update_spec）被 state_reader/spec_compliance 复用，其余消费者自研；checker 幽灵 import 静默禁用检查；`- body: 18px` 与 `18` 两种格式；page_rhythm 表格格式仅 e2e 支持。
- **After**: `spec_lock_reader.py`（纯标准库）成为唯一 parser owner（`parse_spec_lock` + `page_ids`/`images`/`narrative_mode`/`structure_mode`/`canvas_dimensions`/`body_size` 类型化 accessor；images 支持 label/无 label/`| no-crop`/`# 注释`；body 支持 px 后缀）；`update_spec.parse_lock` 委托（兼容）；e2e/layout_capacity 迁移为 wrapper（语义零变化，表格格式与 P 过滤保留在消费者）；checker 幽灵 import 消除（接入 canonical，anchor 检查保留在 `_ANCHOR_COMPARE_ENABLED=False` 旗标后——激活会暴露 examples 240+ legacy 漂移，激活决策待用户）。
- **Verified**: parse_lock wrapper ≡ canonical（严格相等）；e2e 差分 29/29 一致；layout_capacity 差分 63 项目 0 差异（含 `18px` 变体）；page_ids 交叉验证 31 示例 0 异常（表格 3 项目行为保留）；`--all examples` checker rc=0（与幽灵基线一致，0 回归）；guard rc=0；完整 smoke 160→162（spec_lock_reader +2 checks）/0/4/166；integration 173/0/4/177。
- **Risk**: low（所有消费者迁移保持语义零变化；唯一行为风险是 checker anchor 检查激活——已用旗标隔离并实测 0 回归）
- **Human reviewed**: pending

### 2026-08-04 — Phase 1 状态单一事实源：canonical artifact accessors + derive_pipeline_state + checkpoint 收敛
- **Files**: `skills/ppt-master/scripts/project_utils.py`（新增 canonical accessors + `derive_pipeline_state`）、`skills/ppt-master/scripts/dashboard/artifact_registry.py`（`latest_pptx` 委托 + `quality/`/`validation/` 补入扫描表）、`skills/ppt-master/scripts/project_manager.py`（`checkpoint_save` 收敛）、`skills/ppt-master/scripts/smoke_check.py`（integration Test 7 状态契约断言）
- **Reason**: `plans/deepppt2-system-optimization-agent-brief.md` Phase 1（Gate G1 已批准）；F4/F5 漂移：checkpoint 认项目根 `*.pptx`（导出后误判 7c-export）、Dashboard 认 `exports/*.pptx`，两套状态推断并存；`quality/`/`validation/` 未注册。
- **Before**: checkpoint 独立推断 8 档 step（项目根 `*.pptx`）；`artifact_registry.latest_pptx` 自带 exports glob；`_SCAN_DIRS` 缺 quality/validation；`content_selection.md`/`detailed_outline.md`（过时，实际产物为 .json）。
- **After**: `project_utils.py` 成为纯标准库 canonical accessor 层（latest_export/has_export/svg_pages/final_svg_pages/notes_total/spec_lock_path/design_spec_path/confirmation_result/find_quality_report + `PROJECT_ARTIFACT_DIRS` 17 目录注册 + `derive_pipeline_state`）；`checkpoint_save` 委托 derive（exports/*.pptx → 8-export，F5 修复；content_selection 改认 .json）；dashboard `latest_pptx` 委托同源；smoke `--integration` 新增 Test 7 状态链断言（1-init→8-export + 确定性）。
- **Verified**: guard rc=0；完整 smoke 160/0/4/164（与基线一致）；`--integration` 171/0/4/175（+1 Test 7）；`checkpoint save` 对已导出项目判 8-export（F5 断言）；derive 状态链 11 步 + 确定性断言全过；Dashboard /api/artifacts 兼容（type 集不变）；真实项目 chip_journal/rudeus 判 8-export。
- **Risk**: low（checkpoint 行为变化仅导出判定修正 + .md→.json 收敛，两处均与实际产物一致；dashboard 仅委托 + 展示新增 quality/validation 条目）
- **Human reviewed**: pending

### 2026-08-04 — 审计工具落地：svg_geometry_audit + pptx_render_export + visual_review --scale + 布局预算规则
- **Files**: `skills/ppt-master/scripts/svg_geometry_audit.py`（新增：字形盒级几何审计）、`skills/ppt-master/scripts/pptx_render_export.py`（新增：PowerPoint COM Slide.Export 渲染导出）、`skills/ppt-master/scripts/visual_review.py`（`--scale N`，默认 1.0 零变化）、`skills/ppt-master/references/executor-base.md`（§14.7 垂直/横向预算规则 + 图片最小尺寸）、`skills/ppt-master/workflows/stages/visual-review.md`（Step 4b PowerPoint 真实渲染复核 + --scale 放大复核）
- **Reason**: 全链路测试暴露 4 处"底部文字×页脚"字形交叠（2.4–13px）、P11 断言撞卡片 2px、P13 断言超条底 3-4px——视觉模型全页检查对 12-13px 小字有盲区，且 Chromium 与 PowerPoint 字体度量不同；需把"保守布局原则"固化为可计算工具与规则。
- **Before**: 无字形盒级审计（rendered_layout_check 为行盒级）；无 PowerPoint 真实渲染复核工具；visual_review 固定 1280×720；布局约束无底部/横向预算规则。
- **After**: `svg_geometry_audit.py`（text-text 字形交叠/tspan dy 累积/页脚贴边 ≥6px/后绘 rect 遮挡/文字超 rect 底/图片短边 ≥150px；宽度复用 svg_to_pptx 权威度量；输出 quality/geometry_audit.json，--strict 有 error exit 1）；`pptx_render_export.py`（Windows+Office COM 渲染，非 Windows exit 2 优雅退出）；`visual_review.py --scale 2` 渲染 2560×1440；executor-base §14.7 固化预算规则。
- **Verified**: 修复前备份回归——工具精确复现全部 4 处手工修复问题（P05 -2.4px、P07 9.2px、P11 13.0px、P13 -3.4px + 超条底 5.3px），并新发现 P07 修复残留（来源×下一步 x 重叠 34.5px，已修）；当前项目 0 error 0 warning（1 info 为设计性图注白条）；smoke 156→160 passed 0 failed（2 新脚本自动进 import+--help 覆盖）；pptx_render_export 14 页渲染 + e2e 7/7。
- **Risk**: low（2 新脚本 advisory 定位不改现有 gate；visual_review 默认路径零变化；PowerPoint COM 仅 Windows 可用）
- **Human reviewed**: pending

### 2026-08-04 — 全链路能力测试 6 项短板修复（spec_lock 模式感知 / docx 表格恢复 / 渲染等待 / 词边界 / font-size / 断言契约文档）
- **Files**: `skills/ppt-master/scripts/spec_lock_validate.py`、`skills/ppt-master/scripts/research/asset_gate.py`、`skills/ppt-master/scripts/svg_quality/deepppt_extensions.py`、`skills/ppt-master/scripts/visual_review.py`、`skills/ppt-master/scripts/source_to_md/doc_to_md.py`、`skills/ppt-master/references/executor-base.md`；项目侧：`projects/gan_hemt_trap_test_ppt169_20260804/`（P05 箱线图 8 值修正、test_report.md 更新、浏览器预览复核修复 P04/P05 两处文字遮挡——P05 ⑦ 标注 x=962→940 避卡片、P04 蓝圈 ⑦ 移位 + 白色遮盖图片图例区 + SVG 重绘正确编号图例）
- **Reason**: `projects/gan_hemt_trap_test_ppt169_20260804/test_report.md` 测试暴露 6 项短板，按用户批准顺序（①⑤⑥③②④）实施；docx 表格恢复复核对账又暴露初版 P05 图表漏 8 个源值（⑤ 1 个 0.63、⑥ 7 个且误归 0.57）。
- **Before**: ① validate 在 flat 模式强制要求 `page_layouts`（与 checker 冲突，flat 项目恒 exit 1）；⑤ asset_gate 拉丁词条子串匹配（"discipline" 命中 "ip"）+ `detailed_outline.json` 无条件强制（直接源项目恒 FAIL）；⑥ 宽度估计用页面首个 font-size（150px 装饰数字串扰）；③ visual_review 100ms 固定等待（图片空白）；② doc_to_md 摊平合并表格、Wingdings 圈号丢失；④ executor-base.md 未写断言精确契约。
- **After**: ① validate 模式感知（flat 免查、出现报 WARN）；⑤ 词边界 `\b…\b` + research_active 条件化；⑥ 逐元素 font-size；③ load/error 事件 Promise 等待（单图 3s 上限）；② stdlib XML 恢复原生表格（gridSpan 列重复、vMerge 重启格归属、Wingdings 2 F06A–F073 与 Wingdings F081–F08A 双字体圈号映射）；④ §2.1 补「Exact assertion contract」段（id 精确 `lead`/`subtitle`、单 `<text>` 整句、≥body、对应检查名）。
- **Verified**: 各修复针对测试项目复验通过（flat spec_lock PASS；直接源 asset_gate PASS；P05 坐标公式复核 0 mismatch；渲染门 must_fix 0）；P05 重导出 e2e_validate 7/7、pptx_quality 仅 5× 设计意图 FULL_SLIDE_IMAGE_RISK（SHAPE_OUTSIDE_SLIDE 已消解）；smoke_check 156/0/4/160 与基线一致。
- **Risk**: low–medium（doc_to_md 行为变化：转换输出追加 `## 原生表格（docx tables 恢复，含合并单元格）` 节；其余为门禁/渲染/文档修复）
- **Human reviewed**: pending

### 2026-08-04 — prompt audit manifest 重写（真实 load-set 设计）+ 治理收口
- **Files**: `skills/ppt-master/scripts/prompt_audit_manifest.json`（重写：7 个 load_sets（global/research/generate/image/template/native，glob 条目带 `select` 按需语义，子集 `include: ["global"]`）+ 1 个 coverage exempt（`pptx_shapes/data/NOTICE.md` 上游版权声明）+ 22 个 exact 重复 accepted（模板族共享契约表/自动生成头/共享引用句）+ corpus `max_tokens` 400k→430k、generate 预算 190k）；配套同步：`plans/deep-ppt-reorganization-contract.md`（D5/D6/D7 与 Phase 2/3/4 状态、`31298372` 标记为迁移基线提交、CI 风险关闭记录）、`docs/reviews/deep-ppt-repository-inventory-2026-08.md`（§0.1 治理后当前快照，原始 Phase 0 基线保留）、`docs/reviews/perf-baseline-2026-08.md`（§3 标记历史 CI 风险已关闭）、`.align/lessons.md`（51→48 条 + 归档最旧 6 条至 `.align/lessons-2026-08-03.archive.md` + 追加 3 条 audit 教训）、`.align/spec.md`（smoke 基线勘误 78/0/3+158/0/4 → 77/0/3/80+156/0/4/160）、`.align/decisions.log.md`（8 条已批准决策）
- **Reason**: 治理收口——原 manifest 为空壳（load_sets 空、duplicates 无 accepted），audit 报 173 errors（1×BUDGET_CORPUS + 172×LOAD_COVERAGE_GAP）；需按 SKILL.md 加载纪律与四路由归属建立真实 load-set 契约。
- **Before**: `prompt_audit.py --json --skip-near-duplicates` rc=1：172 文档 / 424,278 tokens / max_tokens 400,000 / 173 errors / 1 warning；coverage 0 covered + 0 exempt + 172 uncovered；22 exact duplicates 全 open。
- **After**: rc=0：errors 0 / warnings 0；coverage 171 covered + 1 exempt = 172 闭合；22/22 exact accepted；7 个 load_set 预算全部通过（generate max 180,862 ≤ 190,000 等）。near-duplicate 184 对候选保留为 advisory warning（模板 design_spec 共享规则族启发式噪音）。
- **Smoke check**: 156 passed, 0 failed, 4 skipped / 160 checks（完整模式）；77/0/3/80（--skip-help）；attribution_guard rc=0；governance_drift_check 5 PASS；svg_quality_checker --all examples 29/29 rc=0；git diff --check 干净
- **Risk**: low（audit-only 配置 + 治理文档；未改任何运行时/CLI/质量门契约）
- **Human reviewed**: pending

### 2026-08-03 — README 全面更新（v4.3.0 迁移收尾 + Dashboard 产物展台 + CI/Pages 上线）
- **Files**: `README.md`、`docs/change-log.md`
- **Reason**: 仓库介绍对齐 2026-08-03 大规模迁移收尾后的实际状态：重构版导出器/诊断包、structured 接线、29 示例双门全绿、CI/Pages 上线、Dashboard 产物展台定位、Phase 4 治理。
- **Before**: README 停留在 2026-08-03 五阶段迁移条目（structured 仍为 opt-in 描述）；Dashboard 描述为"统一只读 Dashboard"；无 CI 徽章；项目结构树仍指向旧 workflows 平铺布局。
- **After**: 顶部加 CI 徽章；Overview/简介补 v4.3.0 迁移收尾与产物展台；差异化表更新 Dashboard/门禁/排版三行；更新日志顶部新增 2026-08-03 收尾条目；项目结构树更新为四路由 + stages/profiles 架构与 29 示例状态。链接检查 0 断链。
- **Risk**: low（文档更新；0 断链验证）
- **Human reviewed**: pending

### 2026-08-03 — Dashboard 定位为产物展台（制作思路 → 导出成品 四阶段 + 本地搜找索引）+ Phase 4 产物治理
- **Files**: `skills/ppt-master/scripts/dashboard/artifact_registry.py`（新增 research 类型：`_research/`、`research_report.md`、`content_selection.json`、`detailed_outline.json`、`visual_strategy.json`；新增 `phase` 阶段字段（idea/design/generate/export + 中文标签）；`list_artifacts` 新增 `phase_filter` 与 `write_index`（写 `<project>/dashboard/artifacts_index.json` 供本地搜找））、`skills/ppt-master/scripts/dashboard/server.py`（`/api/artifacts` 支持 `phase` 参数 + 每次响应写索引）、`skills/ppt-master/scripts/dashboard/static/app.js`（默认路由改 `#/artifacts` 产物展台；新增四阶段导航条（制作思路/设计契约/生成页面/导出成品，计数 + 点击过滤）；筛选栏新增阶段下拉；`artifactTypeOrder` 加 research）、`skills/ppt-master/scripts/dashboard/static/style.css`（phase-nav/phase-chip 样式）、`projects/README.md`（新增 Lifecycle Governance：active/archive/disposable 三档 + backup/dashboard 可清理清单 + artifacts_index.json 搜找说明）、`docs/change-log.md`
- **Reason**: 用户对 Dashboard 的新定位——产物在线观看平台：集中展示项目产生的产物（制作 PPT 的思路与相关产物），确认 UI 保持现状；产物治理方便本地搜找。Confirm UI 未改动。
- **Before**: Dashboard 默认管线总览；产物视图无阶段概念、无 research（制作思路）产物分类、无本地索引；backup 旧快照与 .codex 缓存累计 ~1.2 GB。
- **After**: 默认进入产物展台；四阶段导航（含计数与过滤）；research 产物（content_selection/detailed_outline/_research 等）入分类；`/api/artifacts` 响应即写 `dashboard/artifacts_index.json`（类型/阶段/大小/mtime，可 grep/jq 搜找）；Phase 4 清理：34 个旧 backup 快照（~0.9 GB，官方标注 safe to delete）+ `.codex/dashboard-check`/`dashboard-cdp` 缓存（256 MB，保留 config.toml）→ projects/ 5.73 GB → 4.8 GB。
- **Smoke check**: 77 passed, 0 failed, 3 skipped / 80 checks（dashboard/server.py PASS）
- **Risk**: low（dashboard 独立服务加性改动 + 自动生成产物清理；浏览器实测四阶段过滤与布局正常）
- **Human reviewed**: pending

### 2026-08-03 — examples e2e 缺口修复：声明对齐 + svg 命名兼容（checker+e2e 双门 29/29 全绿）
- **Files**: `examples/deepseek_evolution_ppt169_20260621/spec_lock.md`（删 7 条过期 images 声明）、`examples/ppt169_doctor_ppt169_20260621/spec_lock.md`（删 20 条过期 images 声明，声明名与磁盘漂移如 `cover_bg.png` vs `p01_cover_bg.png`）、`examples/ppt169_kaltsit_ppt169_20260621/spec_lock.md`（删 6 条 + 15 个 svg 重编号）、`examples/ppt169_arknights_amiya_ppt169_20260621/spec_lock.md` + 15 个 svg 重编号、`examples/ppt169_kimsoong_loyalty_programme/svg_output/`（10 个 `slide_NN_*.svg` → `NN_*.svg`）、`docs/reviews/perf-baseline-2026-08.md`、`docs/change-log.md`
- **Reason**: e2e 全量 24/29 的 5 个既有缺口收尾（用户批准「删声明」方案）：deepseek/doctor/kaltsit 的 spec_lock `images` 声明与磁盘漂移（过期/错名）；arknights/kaltsit 的 `02_chapter_*`/`03_content_*`/`03a_content_*` 命名使 `normalize_svg_page_id` 重复映射或不识别（03a 前缀返回 None），按 design_spec 页序重编号为唯一前缀（03-07/08-12/13-17/18_ending）；kimsoong 的 `slide_NN` 命名全部不识别，改数字前缀。
- **Before**: e2e 24/29（5 个缺口：deepseek 7 图 / doctor 20 图 / kaltsit 6 图 + 编号 / arknights 编号 / kimsoong 命名）。
- **After**: **checker 29/29 + e2e 29/29 双门全绿**（实测）；改名示例导出 rc=0 抽查通过；smoke 156/0/4 无回归。
- **Smoke check**: 156 passed, 0 failed, 4 skipped / 160 checks（scripts 未改）
- **Risk**: low（声明删减 + 文件重命名，全部机械；导出抽查验证；可 git revert）
- **Human reviewed**: pending

### 2026-08-03 — examples 质量修复 L2/L3：设计层与语义层（29/29 checker 全绿）
- **Files**: 20 个示例的 `svg_output/*.svg` 与 `spec_lock.md`（汇总见 `docs/reviews/perf-baseline-2026-08.md` §3.3；代表性：attention `15_ablations.svg` line→rect、liziqi `03/04/09` filter 与渐变、home_design_trends `04/06/07` filter 重构、kimsoong `slide_03` clipPath、kubernetes marker 拆分、5 个示例 emoji 替换、4 个示例删 page_layouts 节、liziqi/lin_huiyin 补 page_rhythm 节）、`docs/reviews/perf-baseline-2026-08.md`、`docs/change-log.md`
- **Reason**: 完成 CI 门禁治理剩余层（基线报告 §3.3 分类）。L3 语义层：4 个 legacy 示例的 `page_layouts` 节与 flat mode 冲突（该节为 structured 专属，legacy 内容为页面-布局标签且消费方有容错）→ 删节。L2 设计层：B 类零宽 stroke 渐变（objectBoundingBox 无 bbox）→ line→rect 等值转换；C 类 emoji（checker 禁 2600-26FF/2700-27BF/1Fxxx）→ 合法 Unicode 替换（✓→√、✕→×、✦→◇、★→◆、⚠→!、⚡→▶、💡→!）；D 类 `<g>` filter → 移背景 rect 或单图内层 g；E 类 kimsoong `inset()` → 本地 clipPath。补充：liziqi/lin_huiyin 的 typography title 行与 page_rhythm 节（e2e 契约）。
- **Before**: checker 红 19 个（L1 后 10/29 绿）；e2e 未全量验证。
- **After**: **checker 29/29 全绿**；导出抽查 5 个重度修改示例 rc=0；e2e 全量 24/29（5 个既有资产缺口：deepseek/doctor spec_lock images 声明与磁盘文件名漂移、arknights/kaltsit 声明 18 页 vs svg_output 13 页、kimsoong slide_NN 命名与 e2e P 编号解析不兼容——非本批引入，待独立处理）；smoke 156/0/4 无回归。
- **Smoke check**: 156 passed, 0 failed, 4 skipped / 160 checks（scripts 未改，无变化）
- **Risk**: medium（改动 20 个公开示例的 SVG/spec_lock 数据；全部机械/等值转换，导出与 e2e 抽查验证；可 git revert）
- **Human reviewed**: pending

### 2026-08-03 — examples 质量修复 L1（机械层）：162 SVG 补 width/height + 4 个 spec_lock 契约行 + doctor 图片格式 + kubernetes marker
- **Files**: `examples/*/svg_output/*.svg`（8 个示例 162 文件：根元素补 `width`/`height`，值取自 viewBox）、`examples/deepseek_evolution_ppt169_20260621/spec_lock.md`（+`- title: 32`）、`examples/march7th_hsr_ppt169_20260622/spec_lock.md`（+`- title: 36`/`- body: 22`）、`examples/meditation_hunyuanzhuang_ppt169_20260622/spec_lock.md`（+`- title: 36`/`- body: 22`）、`examples/ppt169_lin_huiyin_architect/spec_lock.md`（+`font_family`/`title_family`/`body_family`，映射自旧行名 font_title/font_body）、`examples/ppt169_doctor_ppt169_20260621/images/web_assets/dim6_doctor_concept.jpg`（WEBP 容器→真 JPEG）、`dim6_doctor_full_art.png`（WEBP→真 PNG）、`examples/ppt169_kubernetes_blueprint_2026/svg_output/05_pod_lifecycle.svg` + `09_api_spine.svg`（marker 按 stroke 颜色拆分 arrowCyanDark/arrow09CyanDark/arrow09CyanGreen）、`docs/reviews/perf-baseline-2026-08.md`、`docs/change-log.md`
- **Reason**: 继续 CI 门禁治理（基线报告 §3.3 分类）：A 类 root width/height（8 示例）、typography 契约行（3+1 示例，legacy 用旧行名 page_title/body_size/font_title 等，映射有据）、doctor 2 个图片扩展名与魔数不符（RIFF/WEBP 伪装 .jpg/.png，checker 正确拦截）、kubernetes marker fill 与 line stroke 颜色不匹配（按颜色拆分 marker，视觉不变）。
- **Before**: 29 示例中绿 0 个（本轮起点）；上述 4 类 ERROR 各自命中。
- **After**: 绿 10/29（+fashion_weekly/deepseek/march7th/meditation/kubernetes；此前回填 5 个）。剩余 19 个 = L2 设计层 15 个（零宽 stroke ×6、emoji ×7、filter ×2、clip-path ×1）+ L3 语义层 4 个（page_layouts 与 flat 冲突：arknights_amiya/kaltsit/pritzker/doctor），待用户决策。
- **Smoke check**: 未触碰 scripts/ 逻辑（SVG 数据 + spec_lock 数据），不适用；以 checker 全量 29 示例验证代替（前后 rc 对比）
- **Risk**: low（全部机械映射/格式修复；width/height 与 viewBox 一致渲染不变；marker 拆分视觉不变；图片重编码视觉不变；可 git revert）
- **Human reviewed**: pending

### 2026-08-03 — 修复 spec_lock_validate 的 mode 跨节误读（pptx_structure 与叙事 mode 冲突）
- **Files**: `skills/ppt-master/scripts/spec_lock_validate.py`（mode 值读取限定在 `## mode` 节内）、`docs/reviews/perf-baseline-2026-08.md`（§3.3 补记）、`docs/change-log.md`
- **Reason**: 回填 29 个 legacy spec_lock 的 `## pptx_structure` + `- mode: flat` 后，`spec_lock_validate.py` 用 `re.search(r"^- mode:\s*(\S+)")` 全局搜索第一个 `- mode:` 行——`pptx_structure` 节在 `## mode` 节之前，导致所有含该节的项目（含全部新项目）把 `- mode: flat` 误读为叙事模式，产生系统性 `Unusual mode value: flat` 警告且真实叙事模式值被忽略。
- **Before**: 全局 `- mode:` 搜索；任何含 pptx_structure 节的项目误读 mode 值（flat → Unusual WARN，narrative 等真实值被忽略）。
- **After**: mode 读取限定在 `## mode` 节内（复用 `section_content_pattern`）；legacy 示例不再误报 Unusual WARN（缺必需节 FAIL 为既有状态），完整 lock（pptx_structure flat + mode narrative）PASS 无 WARN。
- **Smoke check**: 156 passed, 0 failed, 4 skipped / 160 checks（修改前后一致，spec_lock_validate import + --help 双 PASS）
- **Risk**: low（单处正则作用域修正；PASS/FAIL 语义不变；回滚 = git revert）
- **Human reviewed**: pending

### 2026-08-03 — CI 门禁治理：spec_lock `pptx_structure.mode` 模板 bug 修复 + 29 个 legacy 示例回填
- **Files**: `skills/ppt-master/templates/spec_lock_reference.md`（`pptx_structure` 节：`- pptx_structure.mode: flat` → `- mode: flat`，更正与 checker 矛盾的 legacy 注释）、`examples/*/spec_lock.md`（29 个 legacy 示例追加 `## pptx_structure` + `- mode: flat`，按原行尾 CRLF×22 / LF×7）、`docs/reviews/perf-baseline-2026-08.md`（§3.3 分类清单）、`plans/deep-ppt-reorganization-contract.md`、`docs/change-log.md`
- **Reason**: Phase 3 基线测量发现 CI 风险——29/29 examples `svg_quality_checker` rc=1。根因链：v4.3.0 迁移后 release 契约要求 spec_lock 显式声明 `pptx_structure.mode`（解析器 `_PPTX_STRUCTURE_MODE_RE` 只匹配 `- mode:` 行），但模板写的是 `- pptx_structure.mode: flat`（按模板回填必然失败），且 29 个 legacy 示例从未回填、迁移提交未 push（`main` 领先 `origin/main` 1 提交）——一旦 push，CI svg-quality job 必红。用户未直接答复决策时按最佳判断执行最低风险可逆选项（A：机械回填 + 模板修复）。
- **Before**: 模板格式与解析器不匹配；29/29 examples checker rc=1（spec_lock mode missing + 内容 ERROR）。
- **After**: 模板与解析器一致；回填后 5/29 变绿（brutalist / cangzhuo / global_ai_capital / lin_huiyin_architect_revised / swiss_grid）；24 个仍红示例已按 A-E 类归类（root width/height ×8、零宽 stroke ×6、emoji ×5、filter ×2、特例 ×3），修复或 CI 门禁调整待决策；pritzker 特例（page_layouts 节与 flat 冲突）待单独判断。
- **Smoke check**: 未触碰 scripts/ 入口逻辑（仅模板与示例数据），不适用；checker 全量验证代替（29 个示例前后 rc 对比已记录）
- **Risk**: low（机械回填 + 模板格式修正，可 git revert；不改任何 SVG 内容）
- **Human reviewed**: pending

### 2026-08-03 — Phase 2 治理首批执行：动画双文件合并（方案 A）+ 迁移路线图归档
- **Files**: `scripts/native_pptx_animations.py`（删除，同内容双名副本）、`scripts/native_enhance_pptx_core.py`、`scripts/narration_sync.py`、`scripts/pptx_delivery_check.py`（import `native_pptx_animations` → `pptx_animations`，各 1 行）、`scripts/attribution_guard.py`（gate 清单 `native_pptx_animations.py` → `pptx_animations.py`）、`scripts/README.md`（Enhance 路由脚本列表）、`workflows/native-enhance-pptx.md`（`--describe-transition` 命令名与模块说明）、`plans/followup-migration-roadmap.md`（归档标记）、`plans/deep-ppt-reorganization-contract.md`、`docs/change-log.md`
- **Reason**: 按 `plans/deep-ppt-reorganization-contract.md` Phase 2 首批与用户批准的执行方案 A——v4.3.0 迁移后 `pptx_animations.py` 与 `native_pptx_animations.py` 为同内容双名副本（md5 `c6d7c928…`，各 145,406 B），消除冗余并统一模块名：保留与上游同名的 `pptx_animations.py`，native 侧 3 个消费点改 import（导出器侧 3 个消费点零改动），gate 清单与文档提及同步。
- **Before**: 双文件并存；native 侧 3 脚本 import `native_pptx_animations`；gate 清单列 `native_pptx_animations.py`；smoke 81 scripts（158 passed / 0 failed / 4 skipped / 162 checks）。
- **After**: 单一 `pptx_animations.py`（3 消费点导出器侧 + 3 消费点 native 侧）；gate 清单指向 `pptx_animations.py`；README 脚本列表与 native-enhance `--describe-transition` 说明同步；smoke 80 scripts（156 passed / 0 failed / 4 skipped / 160 checks，-2 checks 为被删脚本的 import+help 两项，无新增失败/跳过），attribution_guard 通过。
- **Smoke check**: 156 passed, 0 failed, 4 skipped / 160 checks（基线 158/0/4 / 162）；attribution_guard 通过
- **Risk**: low（纯路径替换 + 清单同步；3 个消费脚本 import 与 --help 双 PASS；回滚 = git revert）
- **Human reviewed**: pending

### 2026-08-03 — Phase 6：重构版导出器迁移（flat 版 → ppt drawingml/pptx_package 体系 + svg_quality 诊断包）
- **Files**: `scripts/svg_to_pptx/`（整体替换为 ppt 重构版 40,328 行：`drawingml/` 9 模块、`pptx_package/` 10 模块含 template_structure/template_validation、`native_objects/` 10 模块、`shape_boolean.py`/`text_outline.py`/`canvas_contract.py`/`geometry_properties.py`）、`scripts/svg_quality/`（新增：checker.py 7084 行 + svg_contracts.py + cli.py + `deepppt_extensions.py` 迁移的 DeepPPT2 特有检查）、`scripts/svg_quality_checker.py`（薄入口替换）、`scripts/pptx_animations.py`（旧版 659 → 新版 3932）、`scripts/resource_paths.py`（新增）、`scripts/svg_finalize/`（全套升级）、`scripts/svg_to_pptx/pptx_package/cli.py`（+DeepPPT2 特有 flag：--svg-snapshot/--only/--native/--no-compat/--cache-dir/--no-cache/--keep-cache/--workers，--quick-generate 冲突检查扩展）、`scripts/native_enhance_pptx_core.py`（import 面 + notesMaster 适配）、`scripts/narration_sync.py`、`scripts/pptx_delivery_check.py`、`scripts/template_preview_pptx.py`（恢复 ppt 原版）、`scripts/template_fill_pptx/notes.py`+`transitions.py`（NATIVE_TRANSITIONS）、`scripts/shape_boolean_svg.py`（真实核心）、`scripts/README.md`、`references/` 4 份接口映射注记更新、`templates/spec_lock_reference.md`（pptx_structure 注记更新）、`workflows/profiles/quick-generate.md`（恢复 --stage final --json 指纹契约）、`docs/change-log.md`
- **Reason**: 用户基于实际痛点（排版/文字元素溢出诊断不足）决定完整迁移 ppt 的重构版导出器与诊断体系。新体系提供真实文字度量硬错误（`estimate_single_line_text_frame_width`、负 letter-spacing 非正框宽）、transform 感知 bounds 溢出契约（量化溢出比 + 修复建议）、21 类 SVG→DrawingML 语法契约；旧 checker 只有字符计数启发式 + 忽略 transform 的安全边距（全 warning）。
- **Before**: flat 版导出器（5,000 行）无契约校验；checker 对溢出只报 warning；`--quick-generate` 无质量报告指纹要求；`svg_to_pptx.shape_boolean`/structured 为文档化 deferred 项。
- **After**: 重构版导出器 + 诊断包整体接线；DeepPPT2 特有 8 项检查（WCAG 对比度/narrative/间距/重叠/留白等）与 must_fix/should_fix 分级及 --integrated-review 以 `svg_quality/deepppt_extensions.py` 增量保留；全部 DeepPPT2 CLI flag 加回；`--quick-generate` 恢复报告指纹门（checker --stage final --json → 导出校验）；溢出诊断验证 3/3（负 letter-spacing → cx=-70104 硬错误；文本超模块 bounds → 379.8% 量化溢出硬错误）；smoke 158 passed / 0 failed / 4 skipped（162 checks，较迁移前 +2）。
- **Risk**: 高（核心导出器整体替换）——已通过 Phase 3/4/5 + quick + overflow 全量回归；`use_native_shapes=False`（PNG 图片模式）按 ppt 设计废弃，`--svg-snapshot` 以新 builder 的 legacy 渲染模式实现（`_svg.pptx` 兄弟文件）；release 导出现要求 spec_lock.md 完整主题契约（canvas/typography/colors/pptx_structure.mode）
- **Human reviewed**: pending

### 2026-08-03 — 遗留项收尾：quick-generate 落地 + 复盘修复（五阶段迁移收官）
- **Files**: `skills/ppt-master/workflows/profiles/quick-generate.md`（新增，引用适配到 DeepPPT2 的 image-base/image-searcher 体系、checker 无 stage/json 契约如实标注）、`scripts/project_manager.py`（init `--quick-generate`：仅建 svg_output/、无 README）、`scripts/svg_quality_checker.py`（`--quick-generate` lockless 声明 + 残留 spec_lock.md 警告）、`scripts/svg_to_pptx/pptx_cli.py`（`--quick-generate` 冲突检查 + notes 默认关 + `--with-notes`）、`scripts/svg_to_pptx.py`（**存量 bug 修复**：入口丢弃 `main()` 返回值，所有错误路径静默 rc=0，改 `raise SystemExit(main())`）、`scripts/attribution_guard.py`（gate 清单 +`preset_shape_svg.py`/`template_preview_pptx.py`）、`scripts/README.md`（+模板作者/原生形状工具行 + shape_boolean deferred 标注）、`docs/technical-design.md`（+Native Enhance & Export Suite 章节、Standalone Workflows 完整清单）、`README.md`（对比表 +5 能力行、更新日志 2026-08-03 条目）、`.github/copilot-instructions.md`（3 个相对链接修复）、`docs/change-log.md`、`plans/followup-migration-roadmap.md`、`.align/lessons.md`
- **Reason**: 完成 roadmap 遗留项收尾——quick-generate 直通 profile（routing.md 在 Phase 2 已预留触发行但 profile 与 CLI 支持一直缺失，属悬空引用）纳入 DeepPPT2；docs/README 功能对比按跨阶段注意事项更新；structured wiring 经用户确认保持文档化 opt-in（完整移植需引入约 2 万行重构版导出器体系，与"项目轻量"目标冲突）。
- **Before**: routing.md 引用不存在的 `profiles/quick-generate.md`；三个 CLI 无 `--quick-generate` 支持；`svg_to_pptx.py` 入口丢弃退出码（失败静默）；scripts/README 未覆盖 Phase 5 新工具；README/technical-design 未反映五阶段迁移。
- **After**: quick-generate 全链路可用（init 最小工作区 → lockless checker → flat 导出，e2e 5/5，冲突检查与残留 lock 警告生效）；`svg_to_pptx.py` 错误路径正确返回 rc=1；文档与脚本面一致；smoke 156 passed / 0 failed / 4 skipped（160 checks）。
- **Risk**: low（quick-generate 为加性 flag，默认导出路径零改动；入口 rc 修复只影响错误退出码，不影响成功路径）
- **Human reviewed**: pending

### 2026-08-03 — Phase 5：原生形状套件 + 规范文档迁移 + structured 导出 opt-in 声明
- **Files**: `skills/ppt-master/scripts/pptx_shapes/`（`__init__.py` `models.py` `loader.py` `registry.py` `semantic_hash.py` `formula.py` `xml_safety.py` `errors.py` `data/`，187 预设），`skills/ppt-master/scripts/preset_shape_svg.py`，`skills/ppt-master/scripts/shape_boolean_svg.py`（适配：缺省核心按回退条款优雅降级），`skills/ppt-master/scripts/pptx_to_svg/preset_authoring.py`、`preset_registry_to_svg.py`、`preset_svg_markup.py`、`prstgeom_to_svg.py`，`skills/ppt-master/scripts/compact_svg_coordinates.py`、`svg_authoring_view.py`、`slide_roster.py`、`template_preview_pptx.py`（适配：flat 面调用 + 本地 viewBox 锁 + 补回 `@contextmanager`）、`template_text_slots.py`、`extract_svg_pictures.py`、`slice_images.py`，`skills/ppt-master/scripts/svg_to_pptx/theme_fonts.py`（+`MasterTextStyleSpec`）、`svg_to_pptx/drawingml_utils.py`（+`font_px_to_hpt`/字号常量），`skills/ppt-master/references/semantic-svg.md`、`pptx-structure-interface.md`、`native-shape-authoring.md`、`native-data-interface.md`、`shared-standards-core.md`、`svg-effects.md`（新增 + 每份头部 DeepPPT2 接口映射注记），`skills/ppt-master/templates/spec_lock_reference.md`（+`## pptx_structure`），`docs/change-log.md`，`plans/followup-migration-roadmap.md`
- **Reason**: 完成五阶段迁移计划的最后阶段——把 ppt v4.3.0 的原生形状（preset catalog）与结构化模板规范体系迁入，并与 DeepPPT2 的 spec_lock/page_expression 合同体系做接口映射（不照搬）。structured 导出模式按批准计划的回退条款落地：默认关闭、显式声明、wiring 如实标注为延期的 opt-in 路线图项（`svg_to_pptx.shape_boolean`、`mirror_template_materialize` 依赖 ppt 的 drawingml 包重构，符号面 diff 证实不可低损移植）。
- **Before**: 无 preset 形状能力；Executor 只能用基础图元/手写 path；无 structured 规范文档；spec_lock 无导出结构声明；模板预览工具缺失。
- **After**: `preset_shape_svg.py`/`prstgeom_to_svg.py`/`pptx_shapes`（187 预设）闭环可用（渲染 + 校验 + beautify 反向转换）；6 份规范文档带 DeepPPT2 接口映射；`template_preview_pptx.py` 在 flat 面跑通（structured 专用参数明确标注为延期面）；spec_lock 新增 `pptx_structure.mode: flat|structured`（默认 flat）；`shape_boolean_svg.py` 缺省核心时给出清晰降级信息而非原始 traceback。验证：预设形状/物化工具 e2e 15/15，Phase 3/4 回归全过，smoke 156 passed / 0 failed / 4 skipped（160 checks）。
- **Risk**: 中（structured 导出 wiring 未落地，spec_lock 已明示禁止当前填写 `structured`；boolean 核心依赖可选包 skia-pathops）
- **Human reviewed**: pending

### 2026-07-25 — Selective reference-repository absorption and contract hardening
- **Files**: `README.md`, `skills/ppt-master/SKILL.md`, `skills/ppt-master/references/strategist.md`, `skills/ppt-master/references/executor-base.md`, `skills/ppt-master/scripts/chart_recall.py`, `skills/ppt-master/scripts/docs/chart-recall.md`, `skills/ppt-master/scripts/spec_compliance_check.py`, `skills/ppt-master/scripts/svg_quality_checker.py`, `skills/ppt-master/scripts/research/research_gate.py`, `skills/ppt-master/scripts/README.md`, `skills/ppt-master/scripts/dashboard/contracts.json`, `skills/ppt-master/scripts/dashboard/quality_reader.py`, `skills/ppt-master/scripts/dashboard/state_reader.py`, `skills/ppt-master/templates/design_spec_reference.md`, `skills/ppt-master/templates/spec_lock_reference.md`, `skills/ppt-master/templates/charts/README.md`, `skills/ppt-master/templates/charts/charts_index.json`, `skills/ppt-master/workflows/deep-research.md`, `skills/ppt-master/workflows/detailed-outline.md`, `skills/ppt-master/workflows/stages/refine-spec.md`, `skills/ppt-master/workflows/stages/resume-execute.md`, `skills/ppt-master/workflows/research/step1_outline.md`, `skills/ppt-master/workflows/research/step5_analysis.md`, `skills/ppt-master/workflows/research/step6_narrative.md`, `docs/change-log.md`
- **Reason**: Update and audit the latest `ppt` (`1912f011`), `PPT Hell` (`be343d2e`), and `CyberPPT` (`980e5576`) repositories, then absorb only bounded improvements that fit DeepPPT's existing workflow and license boundary. PPT Hell is AGPL-3.0, so only its collect-then-fix quality principle was independently expressed; no code or contract text was copied.
- **Before**: Structural-page exceptions, page-expression lifecycle handoffs, Dashboard digest reporting, chart selection, consulting evidence, and SCR alternatives were only partially aligned across their owning files. Broad composition heuristics also appeared as should-fix warnings, which could encourage filling intentional whitespace. Checker guidance allowed repeated invocations between individual fixes.
- **After**: Structural pages accept real values or reasoned exceptions across all six machine page kinds, while content pages remain strict. `page_expression.json` is carried through continuous, split, resume, and refine paths and sealed with the lock digest. Dashboard contracts expose digest status with strict schema/type handling. `chart_recall.py` returns up to the requested 3-8 deterministic candidates from the live 71-item catalog, gates low/none-confidence semantic fallback, and rejects empty, duplicate, or nonexistent selected keys. Decision-oriented research records traceable evidence and exactly 2-3 SCR alternatives plus one resolved recommendation; machine comments do not count toward narrative depth. Executor QA batches fixes before one re-check, while sparse vertical composition, one-sided whitespace, and large image-text gaps are review-only signals that must not be "fixed" with filler. The root `README.md` now mirrors these production-facing capabilities and their intended scope.
- **Verification**: Baseline `smoke_check.py --skip-help` was `51 passed, 0 failed, 3 skipped / 54`. Final `smoke_check.py --skip-help --governance --integration` passed `63 passed, 0 failed, 3 skipped / 66`; `--dashboard-e2e` passed `53 passed, 0 failed, 3 skipped / 56`, then removed both disposable projects and released ports 8765/8766. `py_compile` passed for every modified Python file and both changed JSON contracts parsed. Focused fixtures passed valid content/structural contracts and rejected missing, hidden, or undersized assertions; all six structural page kinds and invalid non-string `page_kind` values were exercised. Chart recall validated the live 71-item fallback shape and returned non-zero for empty, duplicate, normalized-duplicate, invalid, and disallowed-fallback inputs. Complete/missing SCR, bad recommendation references, evidence routing, comment-excluded body depth, Dashboard schema/type cases, digest status mapping, and a read-only quick Harness PASS were also verified. `git diff --check` passed.
- **Risk**: medium (main-pipeline semantic validation, Strategist/Executor prompt behavior, optional deep-research outputs, and read-only Dashboard contracts changed; export architecture, template assets, Confirm UI behavior, and reference-repository local modifications remain untouched).
- **Human reviewed**: pending

### 2026-07-19 — Productionize page-expression runtime contracts
- **Files**: `skills/ppt-master/scripts/spec_compliance_check.py`, `skills/ppt-master/scripts/spec_lock_validate.py`, `skills/ppt-master/scripts/spec_lock_digest.py`, `skills/ppt-master/scripts/harness_gate.py`, `skills/ppt-master/scripts/dashboard/artifact_registry.py`, `skills/ppt-master/scripts/dashboard/watcher.py`, `skills/ppt-master/scripts/dashboard/state_reader.py`, `skills/ppt-master/scripts/dashboard/quality_reader.py`, `skills/ppt-master/scripts/dashboard/contracts.json`, `skills/ppt-master/templates/spec_lock_reference.md`, `skills/ppt-master/scripts/README.md`, `docs/claude-reference.md`, `docs/change-log.md`
- **Reason**: Close the production gap left by the first page-expression phase: enforce the runtime contract, seal both machine contracts, and expose the sidecar through existing Dashboard observability.
- **Before**: `page_expression.json` was authored and consumed by the generation guidance but was not part of the runtime compliance gate, digest drift check, or Dashboard root-file/watch/state surfaces.
- **After**: Main-pipeline compliance requires schema version 1, Strategist ownership, complete page coverage, six content fields with explicit string/list shapes, reasoned structural exceptions, allowed relation vocabulary, a non-empty information anchor, no `## page_expression` lock section, and an editable verbatim assertion in top-level `lead`/`subtitle` at or above `typography.body`. Hidden descendant runs, transparent text, and below-body tspan overrides do not satisfy visibility. `template-fill` and `beautify` retain explicit compatibility warnings. New digests cover `spec_lock.md` plus `page_expression.json`; spec_lock-only digests remain compatible for projects without the sidecar, while sidecar projects fail closed until re-sealed. Harness verifies a present digest, and Dashboard registry/watcher/state/quality surfaces observe the sidecar.
- **Verification**: Baseline smoke remained `51 passed, 0 failed, 3 skipped / 54`; valid content and structural fixtures passed compliance and non-read-only quick harness gates, while the invalid fixture returned `FAIL` for a missing `takeaway` and invisible assertion. A legacy digest with a sidecar returned non-zero drift, and disposable hidden-tspan / 14px-tspan cases returned non-zero contract errors. The refreshed valid export is `.tmp/_agent_page_expression_phase2_20260719/valid_content/exports/valid_content_20260719_020820.pptx`; `e2e_validate --pptx` reported `6 passed, 1 warning, 0 errors`, and `pptx_quality_check` reported `errors: []` with two intentional image-area warnings. Dashboard API/state exposed the sidecar and a watcher mutation produced `pipeline:state`.
- **Risk**: medium (new main-pipeline blocking validation and digest enforcement; preservation routes remain compatible with explicit warnings; no visual language or template changes).
- **Human reviewed**: pending

### 2026-07-18 — Mandatory page-expression contract and composition-first execution
- **Files**: `skills/ppt-master/references/strategist.md`, `skills/ppt-master/references/executor-base.md`, `skills/ppt-master/references/visual-styles/editorial.md`, `skills/ppt-master/templates/design_spec_reference.md`, `skills/ppt-master/templates/spec_lock_reference.md`, `docs/change-log.md`
- **Reason**: Upgrade main-pipeline content pages from generic content containers to a reviewable expression chain: one assertion, dominant evidence, necessary explanation, a clear takeaway, and a narrative bridge.
- **Before**: §IX carried a `Core message` but no complete per-page expression contract; an Executor could choose cards or columns before defining the evidence relationship; the claim could remain in the spec instead of appearing on the slide; global fill, centering, empty-corner, three-zone, decoration, shadow, and deep-dive quotas could override page intent.
- **After**: Every main-pipeline content page carries `question` / `assertion` / `evidence` / `visual_act` / `takeaway` / `next_beat` in human-reviewable §IX and in Strategist-owned `page_expression.json`, the sole per-page machine truth. Structural-page exceptions require a reason and never invent evidence. Executor re-reads the current page contract, renders the assertion verbatim as `lead` or `subtitle` at `>= body`, and selects one page-scale composition action from `content_relation + information_anchor + visual_act` before considering cards or columns. Generic occupancy and decoration quotas are now intent-aware defaults or removed.
- **Verification**: Baseline and post-change `python skills/ppt-master/scripts/smoke_check.py --skip-help` both passed `51 passed, 0 failed, 3 skipped / 54`. A controlled five-page P04-P08 experiment held source facts, images, palette, typography, and page order constant. Both variants passed static, rendered, export, and PPTX structure gates. Two independent anonymous reviews both selected B on 5/5 pages; the final refreshed rubric scored A `4.4/10` versus B `10.0/10` (`+5.6`). Full evidence is retained under `.tmp/_agent_page_expression_ab_20260718/AB_REPORT.md`.
- **Risk**: medium (main-pipeline Strategist and Executor behavior changes; templates, scripts, standalone preservation routes, and external reference projects remain unchanged).
- **Human reviewed**: pending

### 2026-07-17 — Live preview reliability and first-page quality preflight
- **Files**: `skills/ppt-master/scripts/server_common.py`, `skills/ppt-master/scripts/confirm_ui/server.py`, `skills/ppt-master/scripts/svg_editor/server.py`, `skills/ppt-master/scripts/svg_editor/static/app.js`, `skills/ppt-master/scripts/docs/confirm_ui.md`, `skills/ppt-master/references/executor-base.md`, `docs/change-log.md`
- **Reason**: Absorb upstream `6b7f8909`, `4c7e9635`, `cb9a4bf3`, and `fa3161cf`, plus the per-page QA discipline visible in the reference projects, without replacing DeepPPT's existing pipeline or user-owned work-in-progress.
- **Before**: Live Preview only resolved the shared icon library, refreshes could return to the first slide or render stale responses, malformed lock PIDs could raise during shutdown, and staged Confirm UI recommendations could skip a confirmation stage. Executor quality checks started only after all pages were authored.
- **After**: Project icons resolve before the shared fallback; the selected slide is persisted in the URL hash and survives temporary rewrites; lock PIDs are normalized and stale locks can be cleared safely; skipped Confirm UI stages fail fast with a repair directive; the Executor checks the first SVG before drawing page 2.
- **Risk**: medium (preview/confirmation lifecycle behavior and an Executor reference gate changed; PPTX export semantics remain unchanged).
- **Human reviewed**: pending

### 2026-07-04 — Dashboard template preview polish and release docs
- **Files**: `skills/ppt-master/scripts/dashboard/static/app.js`, `skills/ppt-master/scripts/dashboard/static/style.css`, `README.md`, `docs/change-log.md`
- **Reason**: 用户在浏览 Dashboard 时发现确认中心模板预览展示不完整、放大后无法切换其他预览画面，并且“产物与日志”的产物类型显示重叠；提交前同步项目介绍和日志。
- **Before**: Dashboard 模板卡片只把第一张 SVG 交给放大弹窗，多张预览只能作为普通新窗口链接打开；SVG 放大预览使用 iframe，部分模板显示不完整；产物类型行的计数、大小、展开动作列为自动宽度，长名称时容易挤压重叠；README 仍引用已下线的 `event_presentation` 模板。
- **After**: 模板卡片和预览条都携带同一组 `preview_files`，放大弹窗支持左右箭头和页码切换；SVG/PPTX 预览使用图片式 `object-fit: contain` 完整缩放；产物类型行使用稳定列宽和右对齐，避免重叠；README 更新为当前 Dashboard / Confirm UI / 模板治理能力介绍。
- **Verification**: `node --check skills/ppt-master/scripts/dashboard/static/app.js`; `python -m py_compile skills/ppt-master/scripts/dashboard/server.py skills/ppt-master/scripts/dashboard/state_reader.py`; 临时 `_agent_` 项目 Playwright smoke：模板弹窗 5 页、下一页切换成功、预览 frame 在舞台内、产物类型行 overlap=none，验证后已 shutdown 并删除临时项目。
- **Risk**: low（Dashboard 只读前端交互和文档更新；不改变 PPT 生成、确认 gate、模板应用或导出流程）
- **Human reviewed**: pending

### 2026-07-04 — Dashboard layout preview, i18n, and Step 3 routing `[NEEDS_HUMAN_REVIEW]`
- **Files**: `skills/ppt-master/scripts/dashboard/static/layout-preview.js`, `skills/ppt-master/scripts/dashboard/static/app.js`, `skills/ppt-master/scripts/dashboard/static/style.css`, `skills/ppt-master/scripts/dashboard/static/index.html`, `skills/ppt-master/SKILL.md`, `docs/change-log.md`
- **Reason**: 用户反馈 4 个问题：布局预览无法点击放大且显示不完整、侧边栏步骤名称英文未汉化、Dashboard 与 Confirm UI 模板预览不一致、端到端制作时直接进自由设计无用户选择。
- **Before**: 布局预览卡片无点击事件、iframe 被 `pointer-events: none` 禁止交互、`aspect-ratio: 16/9` 截断内容；侧边栏步骤名称为英文硬编码；Step 3 默认自由设计不询问用户。
- **After**: 布局预览卡片支持点击放大（模态框显示完整 iframe）、添加 hover 高亮效果；添加 `tStepName()` 翻译函数和 `stepNameZh` 映射、语言切换按钮（中/EN）；Step 3 改为两步确认：先问用户"自由设计 or 选择模板？"再继续。
- **Risk**: medium（SKILL.md Step 3 路由变更是架构性修改，影响 pipeline 执行流程；Dashboard 前端变更是低风险 UI 改进）
- **Human reviewed**: pending

**模板预览排查结论**: Dashboard 和 Confirm UI 使用相同数据源（`state_reader.template_route_state()`），但展示目的不同：Dashboard 显示模板库中的真实模板 SVG，Confirm UI 显示抽象风格参考图。两者不是同一个东西，"不符"是正常的。

### 2026-07-04 — Dashboard trigger stability fix and UI optimization
- **Files**: `skills/ppt-master/scripts/dashboard_launcher.py`, `skills/ppt-master/scripts/dashboard/server.py`, `skills/ppt-master/scripts/dashboard/static/style.css`, `skills/ppt-master/scripts/dashboard/static/app.js`
- **Reason**: 用户反馈 dashboard 触发不够稳定，经常不弹出来；dashboard 的各个页面展示急需优化重构，对中文用户友好。
- **Before**: launcher 在服务器未就绪时仍返回 0（成功），静默失败；无 `/api/health` 端点；CSS 使用旧式配色和字体；部分英文文本未翻译。
- **After**: launcher 在服务器未就绪时返回 1（失败），增加额外就绪检查（10 次重试，每次 0.3s）；新增 `/api/health` 和 `/api/config` 端点用于就绪检查；CSS 使用现代配色（蓝色主题）、改进 CJK 字体支持、优化卡片和按钮样式；英文诊断文本已翻译为中文。
- **Risk**: low（launcher 返回码变更不影响 pipeline（dashboard 是 best-effort）；CSS 和 JS 变更不影响功能）
- **Human reviewed**: pending

**修复详情**:
1. launcher 返回码：启动失败返回 1（原为 0），进程退出返回 1（原为 0）
2. 就绪检查：launcher 在服务器未就绪时增加 10 次重试（每次 0.3s），浏览器只在就绪后打开
3. 新增 API 端点：`/api/health`（轻量就绪探针）、`/api/config`（项目配置）
4. CSS 优化：新配色（蓝色主题）、改进 CJK 字体栈、优化卡片/按钮/hero 面板样式
5. 中文本地化：翻译 'stale lock'→'锁过期'、'project mismatch'→'项目不匹配'、'DeepPPT Project'→'DeepPPT 项目'

### 2026-07-04 — Port upstream confirm_ui three-stage visual preview
- **Files**: `skills/ppt-master/scripts/confirm_ui/server.py`, `skills/ppt-master/scripts/confirm_ui/static/app.js`, `skills/ppt-master/scripts/confirm_ui/static/index.html`, `skills/ppt-master/scripts/confirm_ui/static/style.css`, `skills/ppt-master/scripts/confirm_ui/static/catalogs.json`, `skills/ppt-master/scripts/confirm_ui/static/style_previews/` (18 SVG files)
- **Reason**: 上游项目 `C:\Users\FUTIAN\Desktop\ppt` 的 confirm_ui 有重大更新，包括三阶段视觉预览、深色主题、日语支持、图标预览、AI 图像对比等。用户要求移植这些更新以修复模板预览问题。
- **Before**: confirm_ui 使用两阶段确认（tier1/tier2）、浅色主题、双语（zh/en）、无图标预览、无 AI 图像对比、无 style_previews 目录。
- **After**: confirm_ui 使用三阶段确认（stage1/stage2/stage3/final）、深色主题、三语（zh/en/ja）、图标预览 API、AI 图像对比 API、18 个视觉风格 SVG 预览。保留了当前项目的 template_route、layout_preview、template-file 路由等特有功能。
- **Risk**: medium（架构性变更：确认流程从两阶段改为三阶段，CSS 主题从浅色改为深色，HTML 结构重构；server.py 通过选择性合并保持了与 dashboard Confirm Center 的兼容性）
- **Human reviewed**: pending

**移植详情**:
1. 静态文件直接替换：app.js (96KB→119KB)、index.html (1.7KB→2.8KB)、style.css (21KB→20KB)、catalogs.json (17KB→26KB)
2. 新增 style_previews/ 目录：18 个视觉风格 SVG 预览文件
3. server.py 选择性合并：以 upstream 为基础，合入 _template_route()、_layout_preview()、_preview_zones() 函数和 /template-file/ 路由
4. 新增 API 端点：/api/icon-previews、/api/ai-image-comparison、/ai-image-comparison/<kind>/<filename>
5. 新增命令行参数：--wait-stage {stage2,final}

**兼容性验证**:
- smoke_check.py: 50 passed, 0 failed
- confirm_ui server.py 导入正常
- dashboard Confirm Center 兼容（读取 result.json 和 .confirm_ui.lock，不受 stage 字段变更影响）
- state_reader.py 的 template_route_state() 与上游 server.py 的 _template_route() 调用链一致

### 2026-07-04 — User-confirmed template cleanup
- **Files**: `skills/ppt-master/templates/layouts/layouts_index.json`, `skills/ppt-master/templates/brands/brands_index.json`, `skills/ppt-master/templates/layouts/pixel_retro/`, `skills/ppt-master/templates/layouts/content_pages/creative/`, `skills/ppt-master/templates/layouts/content_pages/project_management/`, `skills/ppt-master/templates/brands/event_presentation/`, `skills/ppt-master/references/template-designer.md`, `docs/templates-guide.md`, `docs/zh/templates-guide.md`, `docs/reviews/template-quality-audit-2026-07.md`, `docs/change-log.md`
- **Reason**: 用户确认上一轮模板质量审查中的所有待确认项，允许删除低分候选模板并同步索引。
- **Before**: `pixel_retro`、`content_pages/creative`、`content_pages/project_management` 和 `event_presentation` 仍在模板目录和发现索引中，审查报告状态为待确认。
- **After**: 已从模板库删除这 4 个目录，并从 layout / brand 索引移除对应条目；用户模板指南和 template-designer 示例去掉已删除模板名；审查报告更新为已执行状态，保留未来重建方向。
- **Risk**: medium（删除模板目录并改变模板发现结果；已由用户明确确认）
- **Human reviewed**: yes (2026-07-04)

### 2026-07-04 — Template quality audit and deprecation candidates
- **Files**: `docs/reviews/template-quality-audit-2026-07.md`, `docs/change-log.md`
- **Reason**: 端到端反馈要求审查模板库质量并提出增删方向；模板删除需要用户确认，因此先生成非破坏性审查文档。
- **Before**: 模板库没有本轮基于视觉设计、实用性、完整性、代码质量和文档质量的评分表，也没有集中记录的候选下线/重做清单。
- **After**: 新增模板质量审查草案，记录 layout、content page 和 brand 模板评分，列出需用户确认的候选项，并提出 5 个新增模板方向和未来模板质量标准。
- **Risk**: low（只新增非权威审查文档，不删除模板、不修改索引、不改变运行流程）
- **Human reviewed**: pending

### 2026-07-04 — Per-page layout preview and formula rendering defaults
- **Files**: `skills/ppt-master/scripts/dashboard/layout_preview.py`, `skills/ppt-master/scripts/dashboard/server.py`, `skills/ppt-master/scripts/dashboard/static/app.js`, `skills/ppt-master/scripts/dashboard/static/index.html`, `skills/ppt-master/scripts/dashboard/static/layout-preview.js`, `skills/ppt-master/scripts/dashboard/static/style.css`, `skills/ppt-master/scripts/latex_render.py`, `skills/ppt-master/references/strategist.md`, `skills/ppt-master/references/executor-base.md`, `docs/change-log.md`
- **Reason**: 端到端反馈要求确认阶段能看到逐页 layout 参考，并提高公式图片默认清晰度与 manifest 兼容性。
- **Before**: Dashboard 确认中心不能按页查看 `page_layouts` 选择或生成后的 SVG/截图；公式渲染默认 300 DPI、CodeCogs 优先，manifest 不记录 `display_mode` / `font`，透明图边缘留白较多。
- **After**: Dashboard 新增 `/api/layout-preview` 和只读逐页布局预览面板，按 `quality/screenshots` PNG、`svg_final`、`svg_output`、layout template、chart template 的优先级显示页面缩略图，并兼容旧 `.preview` PNG；公式渲染默认 600 DPI、QuickLaTeX 优先，支持 `display_mode` 与 `font` 字段，并在透明化后保守裁掉多余边距。
- **Risk**: medium（新增 Dashboard API/前端面板并调整公式渲染默认输出尺寸；不改变 PPT 生成顺序、质量门或导出路线）
- **Human reviewed**: pending

### 2026-07-04 — Dashboard information architecture and template preview cleanup
- **Files**: `skills/ppt-master/scripts/dashboard/static/app.js`, `skills/ppt-master/scripts/dashboard/static/style.css`, `docs/change-log.md`
- **Reason**: 端到端反馈发现 Dashboard 模板预览会跳转新页面且缩略图只显示局部，模板预览在多个页面重复出现，管线总览难以看出 AI 当前进度和实时事件。
- **Before**: 管线总览、Step 3 工作台、确认中心都会渲染模板预览；模板卡片使用 iframe 链接打开新窗口；管线总览同时显示 8 步 timeline 和 8 张步骤卡，和左侧步骤导航重复，SSE 更新没有形成可读的实时进度面板。
- **After**: 模板库预览集中到确认中心，管线总览和 Step 3 只保留模板路线摘要；模板缩略图改为完整 `object-fit: contain` 首页预览，点击在 Dashboard 内弹窗放大，可用左右箭头、页码和 Esc 切换/关闭；管线总览新增 AI 当前进度、SSE/Trace 实时事件、质量快照和聚焦步骤入口，减少重复的 8 步信息。
- **Risk**: low（Dashboard 只读前端重排与预览交互调整；不改变 Confirm UI gate、模板应用语义、PPT 生成或导出流程）
- **Human reviewed**: pending

### 2026-07-04 — Quality gate non-destructive layout mode and screenshot handoff
- **Files**: `skills/ppt-master/scripts/finalize_svg.py`, `skills/ppt-master/scripts/rendered_layout_check.py`, `skills/ppt-master/scripts/visual_review.py`, `skills/ppt-master/scripts/svg_quality_checker.py`, `skills/ppt-master/scripts/e2e_validate.py`, `skills/ppt-master/SKILL.md` [NEEDS_HUMAN_REVIEW], `skills/ppt-master/references/shared-standards.md`, `skills/ppt-master/scripts/docs/svg-pipeline.md`, `docs/change-log.md`
- **Reason**: 端到端反馈发现质量检测会通过自动缩小字号破坏布局、视觉门禁 PNG 不易被后续 AI/人类复核定位，并且 EMF/WMF Office 矢量图会被部分图片存在性检查误判。
- **Before**: `finalize_svg.py` 默认执行 `fix-layout` 时会直接缩小 `svg_final/` 字号；`rendered_layout_check.py --render` 使用 `.preview/` 且报告缺少稳定的项目相对截图路径；`svg_quality_checker.py` / `e2e_validate.py` 未统一将 EMF/WMF 视为有效 Office vector image refs。
- **After**: `finalize_svg.py` 新增 `--layout-mode suggest|auto-fix`，默认 `suggest` 只报告布局建议、不重写布局，`auto-fix` 保留旧自动缩小能力；`rendered_layout_check.py --render` 默认写入 `quality/screenshots/` 并在 JSON / 文本报告中列出 `screenshot.relative_path`；`visual_review.py` 支持 `--preview-dir`；图片存在性检查跳过已存在的 `.emf` / `.wmf` Office 矢量资产并保留真正缺失文件的失败。
- **Risk**: medium（改变默认 post-processing 的布局修正副作用，降低自动破坏风险；需要确认依赖旧默认自动缩字的流程是否改传 `--layout-mode auto-fix`）
- **Human reviewed**: pending

### 2026-07-03 — Pipeline coherence audit repair batch
- **Files**: `skills/ppt-master/SKILL.md` [NEEDS_HUMAN_REVIEW], `skills/ppt-master/references/strategist.md`, `skills/ppt-master/workflows/batch-review.md`, `skills/ppt-master/workflows/deep-research.md`, `skills/ppt-master/workflows/image-text-linking.md`, `skills/ppt-master/workflows/create-template.md`, `skills/ppt-master/workflows/content-selection.md`, `skills/ppt-master/workflows/detailed-outline.md`, `skills/ppt-master/workflows/stages/live-preview.md`, `skills/ppt-master/workflows/stages/refine-spec.md`, `skills/ppt-master/workflows/stages/resume-execute.md`, `skills/ppt-master/workflows/revision-loop.md`, `skills/ppt-master/workflows/stages/verify-charts.md`, `skills/ppt-master/workflows/stages/visual-review.md`, `skills/ppt-master/scripts/README.md`, `docs/design/img2img-support.md`, `README.md`, `docs/routing.md`, `docs/rules/documentation-style.md`, `CLAUDE.md` [NEEDS_HUMAN_REVIEW], `AGENTS.md`, `docs/claude-reference.md`, `docs/reviews/pipeline-coherence-audit-2026-07.md`
- **Reason**: 修复 `docs/reviews/pipeline-coherence-audit-2026-07.md` 中已确认的 2 个 P0、4 个 P1 和 5 个 P2，按用户锁定决策执行：删除 batch-review 死 UI 触发语、将 img2img 非运行设计稿迁到 `docs/design/`、将语言规则现实化而不迁移混合语言文件。
- **Before**: `SKILL.md` 和 `strategist.md` 存在相对链接断链；`batch-review.md` 记录了 Confirm UI 不可能产生的 batch-review UI 模式值；`deep-research.md` 将 Step 7 参考图门槛弱化为项目级至少 1 张；`image-text-linking.md` 的 prompt 模板段数描述漂移；`img2img-support.md` 位于 runtime `workflows/`；脚本 README 缺少运行/维护分层；多份轻量 workflow 缺统一完成证据块；`create-template.md` 入口边界不够显式；语言规则与既有目录实践脱节；`docs/routing.md` 未提示 visual-review 多代理降级。
- **After**: `SKILL.md` docs 链接改为 `../../docs/...`；`strategist.md` image rendering/palette 索引改为同级路径；`batch-review.md` 仅允许聊天显式请求触发并补 Exit Evidence；`deep-research.md` 要求 `visual_strategy.json` 中每个需要参考图的页面都有对应 approved `ref/` 文件；`image-text-linking.md` 统一为 6-part 模板并补 Exit Evidence；`img2img-support.md` 通过 `git mv` 迁到 `docs/design/`，README 指向新路径；`scripts/README.md` 按 runtime pipeline / workflow satellite / maintenance / internal helper 分层并覆盖全部顶层脚本；缺失的 workflow 补最小 Exit Evidence；`create-template.md` 补 When to Run / When NOT to Run；`docs/rules/documentation-style.md`、`CLAUDE.md`、`AGENTS.md`、`docs/claude-reference.md` 同步目录语言模式；`docs/routing.md` 标注不支持并行子代理的宿主顺序执行 visual-review。
- **Verification**: 基线 `python skills/ppt-master/scripts/smoke_check.py --skip-help` 为 50 passed / 0 failed / 3 skipped；复跑相对链接扫描、F1-F11 自验、workflow Exit Evidence 覆盖扫描、F7 顶层脚本覆盖差集、F10 旧语言规则 grep、最终 smoke_check 和 `git status --porcelain` 白名单检查。`research_gate.py` 只读侦察发现其参考图 gate 仍弱于新文档门槛（仅 reviewed reference images >=1），本批次按约束未改脚本，记录为后续项。
- **Risk**: medium（涉及主 workflow、reference、workflow 触发/证据、入口文档和治理规则；不修改 `.py` 运行逻辑，不改 Confirm UI 枚举，不 commit）
- **Human reviewed**: pending

### 2026-07-03 — Repository documentation and governance tooling alignment
- **Files**: `AGENTS.md`, `.clinerules`, `.windsurfrules`, `CLAUDE.md`, `hermes.md`, `README.md`, `SETUP.md`, `docs/ai-browser-setup.md`, `docs/claude-reference.md`, `docs/faq.md`, `docs/getting-started.md`, `docs/roadmap.md`, `docs/windows-installation.md`, `docs/zh/*`, `docs/rules/*`, `docs/spec-review-template.md`, `skills/ppt-master/SKILL.md`, `skills/ppt-master/references/template-designer.md`, `skills/ppt-master/workflows/create-template.md`, `skills/ppt-master/workflows/img2img-support.md`, `skills/ppt-master/workflows/stages/live-preview.md`, `skills/ppt-master/scripts/README.md`, `skills/ppt-master/scripts/governance_drift_check.py`, `skills/ppt-master/scripts/dashboard/**`, `skills/ppt-master/scripts/confirm_ui/**`, `skills/ppt-master/scripts/image_backends/**`, `skills/ppt-master/scripts/image_sources/**`, `skills/ppt-master/scripts/*`, `skills/ppt-master/templates/brands/brands_index.json`, `skills/ppt-master/templates/decks/**/design_spec.md`, `skills/ppt-master/templates/decks/decks_index.json`, `skills/ppt-master/templates/layouts/**/design_spec.md`, `skills/ppt-master/templates/layouts/layouts_index.json`
- **Reason**: 仓库级审计发现入口文档、AI Agent 规则摘要、用户文档、脚本 README、模板发现元数据和实际工作流 / 脚本能力存在漂移；同步上一轮审计后的对齐修复，并补齐可重复运行的治理漂移检查脚本
- **Before**: 多个介绍文档仍可读成 topic-only 直接进入 `deep-research`；AI 浏览器自动化平台描述停留在旧的 ChatGPT / Grok / Perplexity 分工；Dashboard / Confirm UI / Live Preview 的默认端口、日志和浏览器打开行为在不同入口不一致；元素级动画容易被误解为默认启用；模板应用边界未充分强调显式路径；模板索引缺少统一的 `summary_zh` 发现字段；缺少脚本化检查来防止这些治理漂移复发
- **After**: 入口文档统一为 `Topic -> ppt-briefing -> user confirmation -> deep-research`；AI 浏览器 / Agent-Reach / fallback 描述与当前脚本和工作流边界一致；Dashboard 默认 `--daemon`、本地自动打开浏览器、失败 non-fatal、实际 URL/port/log 报告在入口摘要和脚本说明中一致；导出默认保留页面转场、元素级动画保持 opt-in；模板 / 品牌应用必须由显式目录路径触发，裸名称只用于发现；Dashboard / Confirm UI 可展示双语模板摘要和预览；新增 `governance_drift_check.py` 覆盖 topic-only、Dashboard 默认、docs/rules 状态和路径漂移检查
- **Risk**: medium（跨入口文档、`SKILL.md` 摘要、workflow 说明、脚本帮助、Dashboard/Confirm UI 辅助行为和模板索引；主要为对齐与治理增强，不改变 SVG 手写、质量门、post-processing 或默认 PPTX 导出路线）
- **Human reviewed**: pending

### 2026-07-02 — Documentation governance P0 alignment
- **Files**: `docs/routing.md`, `docs/ai-rules-shared.md`, `skills/ppt-master/workflows/batch-review.md`, `docs/rules/README.md`, `docs/rules/agent-governance.md`, `docs/rules/documentation-style.md`, `docs/rules/workflow-style.md`, `docs/rules/change-management.md`
- **Reason**: 对齐文档治理审计发现的 P0/P1 问题：topic-only 路由摘要、Dashboard 默认命令、shared rules 权威措辞、batch-review 触发边界，以及 docs/rules 治理草案索引
- **Before**: `docs/routing.md` 和 `docs/ai-rules-shared.md` 仍可读成 topic-only 直接进入 `deep-research`；shared rules 自称 single source of truth；Dashboard 示例默认带 `--no-browser`；`batch-review.md` 把长 deck / 高质量放进触发表，容易被误解为自动触发；`docs/rules/` 缺少入口治理、文档风格、workflow 风格和变更管理草案
- **After**: topic-only 摘要统一为 `ppt-briefing -> 用户确认 -> deep-research -> main pipeline`；`docs/ai-rules-shared.md` 降级为 lightweight baseline；Dashboard 默认示例为 `--daemon`，`--no-browser` 仅限 headless/remote/用户要求；batch-review 只由显式用户选择或 `generation_mode: "batch-review"` 启用，长 deck / 高质量仅提示可选；新增 4 个 draft docs/rules 文件并登记索引
- **Risk**: medium（修改 agent-facing 摘要与一个 workflow 触发边界说明；未修改 `AGENTS.md`、`SKILL.md`、脚本或生成流程）
- **Human reviewed**: pending

### 2026-07-02 — Consulting evidence layer and post-export PPTX QA
- **Files**: `skills/ppt-master/workflows/deep-research.md`, `skills/ppt-master/workflows/detailed-outline.md`, `skills/ppt-master/references/strategist.md`, `skills/ppt-master/references/executor-base.md`, `skills/ppt-master/references/shared-standards.md`, `skills/ppt-master/scripts/consulting_content_lock.py`, `skills/ppt-master/scripts/pptx_quality_check.py`, `skills/ppt-master/scripts/icon_sync.py`, `skills/ppt-master/scripts/README.md`, `skills/ppt-master/SKILL.md`, `AGENTS.md`, `docs/claude-reference.md`, `README.md`, `docs/change-log.md`
- **Reason**: 吸收 CyberPPT 源码审计中适合 DeepPPT 的咨询证据链、SCR 备选、可编辑信息层、PPTX post-export 结构 QA 和图标搜索能力，同时保持 DeepPPT 的 SVG -> DrawingML 主线
- **Before**: deep-research / detailed-outline 没有咨询类 `evidence_table` / SCR 候选输出约束；Executor 文档缺少可编辑信息层与高密度表格 QA 术语；没有可选 `slide_content_lock` sidecar；PPTX 导出后只有 `e2e_validate.py` 的基础结构检查；`icon_sync.py` 只能复制已知图标名
- **After**: 咨询 / briefing / pyramid / high-density business 场景可选启用证据表、2-3 条 SCR 候选、每页 `evidence_ids` / `caveats` / `so_what` / `content_density`；Executor/shared standards 明确关键文字数字必须可编辑、复杂视觉可用图片/path、`pictures=0` 不是质量目标；新增 `consulting_content_lock.py` 输出 `ppt_master.slide_content_lock.v1`；新增 `pptx_quality_check.py` 直接读取 PPTX ZIP/XML 检查 slide size、shape bounds、placeholder、大面积图片、native text 和字号；`icon_sync.py search` 可搜索候选 `lib/name`；README / AGENTS / SKILL / claude-reference / scripts README 对齐新增能力和命令
- **Risk**: medium（新增可选脚本与主流程文档说明；不引入 PptxGenJS / COM 合并，不新增 `test_*.py` 或 unittest/pytest，不改变默认 SVG -> DrawingML 导出路线）
- **Human reviewed**: pending [NEEDS_HUMAN_REVIEW for SKILL.md workflow documentation update]

### 2026-07-02 — Dashboard default browser behavior alignment
- **Files**: `skills/ppt-master/scripts/project_manager.py`, `skills/ppt-master/scripts/dashboard/state_reader.py`, `skills/ppt-master/scripts/docs/project.md`, `docs/change-log.md`
- **Reason**: 最终整合复查发现 `AGENTS.md` / `SKILL.md` 已要求 Dashboard 默认本地自动打开浏览器，但 `project_manager.py` 与项目工具文档仍输出 `--no-browser` 默认提示；同时包方式导入 `dashboard.state_reader` 时缺少 dashboard 模块路径
- **Before**: `project_manager.py validate` 提示 `dashboard/server.py <project> --daemon --no-browser`；`--start-dashboard` 默认不打开浏览器；`scripts/docs/project.md` 仍按旧默认记录；外部导入 `dashboard.state_reader` 可能找不到 `artifact_registry`
- **After**: `project_manager.py` 默认提示和启动均使用 `--daemon`，`--no-browser` 仅作为显式无窗口选项；项目工具文档同步该边界；`state_reader.py` 同时注入 `scripts/` 和 `scripts/dashboard/` 到 `sys.path`
- **Risk**: low（只收敛 Dashboard 辅助入口和只读状态读取，不改变 PPT 生成、Confirm UI、Live Preview、质量门或导出语义）
- **Human reviewed**: pending

### 2026-07-01 — Rendered visual gate for quality reliability
- **Files**: `skills/ppt-master/scripts/rendered_layout_check.py`, `skills/ppt-master/SKILL.md`, `skills/ppt-master/workflows/stages/visual-review.md`, `skills/ppt-master/scripts/README.md`, `skills/ppt-master/scripts/docs/svg-pipeline.md`, `QUALITY_GAP_ANALYSIS.md`, `docs/change-log.md`
- **Reason**: 修复 mini deck 暴露的质量体系缺口：静态脚本和 quick harness 通过但真实渲染 PPT 存在重叠、踩线、异常留白和修 warning 后视觉退化风险
- **Before**: `svg_quality_checker.py` / `harness_gate.py --quick` 主要代表 XML / spec / 静态规则，`e2e_validate.py` 只验证 PPTX 包结构；主流程没有本地渲染截图门禁或改后视觉确认机制
- **After**: 新增 `rendered_layout_check.py`，读取 `svg_output/` 与 `.preview/`，可通过 `--render` 调用本地 Playwright 渲染，报告跨栏文字侵入、文本踩线、容器贴边、过度留白和 revision snapshot 后的人工确认需求；Step 6 文档明确 static pass 不等于 visual pass，导出前必须通过 rendered visual gate 或显式人工确认
- **Risk**: medium（新增导出前阻塞型质量门禁；规则设计为硬故障自动拦截、主观/启发式问题人工复核，避免为清 warning 破坏视觉）
- **Human reviewed**: pending

### 2026-07-01 — Standard pre-merge regression checklist
- **Files**: `skills/ppt-master/scripts/README.md`, `docs/change-log.md`
- **Reason**: 沉淀端到端验证链修复后确认有效的标准回归命令，避免后续维护误把 quick gate 当作完整 E2E 通过
- **Before**: 脚本 README 只有单条 aggregated quality gate 示例和 `--read-only` 副作用说明，没有合并前可复制的 smoke / full E2E / quick static 回归清单
- **After**: 新增从仓库根目录运行的 pre-merge / post-fix regression checklist，明确区分 smoke import/help check、full E2E gate、full E2E validation 和 quick static gate，并说明 `harness_gate.py --quick` 会跳过 e2e，不能代表完整端到端通过
- **Risk**: low（仅文档补充，不修改脚本逻辑、测试结构或生成流程）
- **Human reviewed**: pending

### 2026-07-01 — Harness gate read-only validation mode
- **Files**: `skills/ppt-master/scripts/harness_gate.py`, `skills/ppt-master/scripts/e2e_validate.py`, `skills/ppt-master/scripts/README.md`, `docs/change-log.md`
- **Reason**: 消除最终回归中发现的验证副作用风险，并修正数字前缀 notes 文件被误报缺失的问题
- **Before**: `harness_gate.py` 每次运行都会写入 `quality/harness.json` 并追加 `trace.jsonl`；`e2e_validate.py` 只按 `P01_*.md` 查找 speaker notes，无法匹配现有 `01_*.md` 产物
- **After**: `harness_gate.py` 保留默认 Dashboard 报告/trace 写入，但新增 `--read-only` / `--no-write` 跳过写入；`e2e_validate.py` 同时支持 `P01_*.md` 和 `01_*.md` notes 命名；脚本 README 说明默认写入与只读回归边界
- **Risk**: low（只影响验证命令副作用控制和验证口径；不改 PPT 生成、后处理或导出逻辑）
- **Human reviewed**: pending

### 2026-07-01 — Dashboard project manager explicit startup flags
- **Files**: `skills/ppt-master/scripts/project_manager.py`, `skills/ppt-master/scripts/README.md`, `skills/ppt-master/scripts/docs/project.md`, `docs/change-log.md`
- **Reason**: 为 `init` / `import-sources` / `validate` 增加显式 Dashboard 半自动启动入口，同时保持默认只提示、不启动后台服务
- **Before**: `project_manager.py` 成功路径只输出 Dashboard 启动提示；用户需手动复制 `dashboard/server.py <project_path> --daemon --no-browser`
- **After**: 三个项目命令支持 `--start-dashboard`、`--no-browser`、`--dashboard-port 8765`；显式启动时复用 `dashboard_launcher.py`，启动失败作为 warning 处理并继续原 PPT 流程；未传 `--start-dashboard` 时行为不变
- **Risk**: low（只接入既有 Dashboard launcher；不改变 PPT 生成语义，不默认打开浏览器，不替代 Confirm UI / Live Preview / 质量门或导出）
- **Human reviewed**: pending

### 2026-07-01 — Dashboard default agent entry integration
- **Files**: `AGENTS.md`, `CLAUDE.md`, `docs/ai-rules-shared.md`, platform agent rule files, `hermes.md`, `junie/guidelines.md`, `skills/ppt-master/scripts/project_manager.py`, `skills/ppt-master/scripts/README.md`, `skills/ppt-master/scripts/docs/project.md`, `docs/change-log.md`
- **Reason**: 让所有 AI Agent 默认知道 Step 2 后应优先暴露统一 Dashboard，并让项目管理 CLI 在低风险路径上输出一致提示
- **Before**: 部分 Agent 入口仍只知道 Project / Confirm UI / Live Preview；`project_manager.py import-sources` 和成功的 `validate` 不提示 Dashboard；共享规则未把 Dashboard 写入核心管线
- **After**: Agent 入口统一记录 Step 2 后启动/复用 `dashboard/server.py <project_path> --daemon --no-browser`、默认端口 `8765`、日志路径、失败 non-fatal 和只读边界；`project_manager.py` 在 init/import/validate 成功路径输出 Dashboard 提示，不自动启动后台服务
- **Risk**: low（文档和 CLI 提示增强；不改变 PPT 生成主流程，不自动打开浏览器，不替代 Confirm UI / Live Preview / 质量门或导出）
- **Human reviewed**: pending

### 2026-07-01 — E2E smoke test visual review fixes (4-page deck)
- **Files**: `projects/e2e_smoke_test_ppt169_20260701/svg_output/03_quality_assurance.svg`, `projects/e2e_smoke_test_ppt169_20260701/svg_output/04_export_routing.svg`, `docs/change-log.md`
- **Reason**: 运行 vision_check.py quality rubric 后发现 4 项 should_fix 级别视觉问题，需修正后重新验证
- **Before**:
  1. P03 gate 标题 (svg_quality_checker / spec_compliance_check / harness_gate) 使用蓝色 `#1A73E8`，不符合 Swiss-minimal 深灰层级规范
  2. P03 底部有一条孤立橙色装饰线 (`#FF6B35`)，与主内容无视觉关联
  3. P04 Decision Axis 框使用白色填充 `#FFFFFF`，在白色背景上不可见
  4. P04 左右两列标题 (Export Pipeline / Routing Boundaries) 使用蓝色 `#0D47A1`，与 P03 同类问题
- **After**:
  1. P03 三个 gate 标题颜色改为 `#333333` (body text)
  2. P03 底部橙色装饰线移除
  3. P04 Decision Axis 框填充改为 `#F5F7FA` (secondary_bg)
  4. P04 两列标题颜色改为 `#333333` (body text)
  5. 重新渲染 PNG → vision_check.py 第二轮: **CLEAN** (0 must_fix, 0 should_fix)
  6. 重新导出 PPTX: 4 slides, 4 notes, 0 failures
- **Risk**: low（仅修改测试项目 SVG 视觉属性，不改脚本逻辑或工作流规则）
- **Human reviewed**: pending

### 2026-07-01 — vision_check.py .env auto-load
- **Files**: `scripts/vision_check.py`, `.env`, `docs/change-log.md`
- **Reason**: vision_check.py 从 os.environ 读取 API key，但不自动加载 .env 文件，导致用户每次运行前需手动 export 环境变量
- **Before**: `vision_check.py` 只读 `os.environ.get()`；.env 中的 `VISION_*` 变量不会被自动加载
- **After**: 在 imports 后添加 `dotenv.load_dotenv()` 从 repo root 的 `.env` 自动加载；`.env` 新增 `VISION_OPENAI_API_KEY`、`VISION_OPENAI_BASE_URL`、`VISION_OPENAI_MODEL` 配置段（指向 Xiaomi MiMo 端点）
- **Risk**: low（添加 dotenv 加载为幂等操作，已有环境变量优先级高于 .env；不改 vision_check 核心逻辑）
- **Human reviewed**: pending

### 2026-07-01 — E2E smoke test validation (4-page deck)
- **Files**: `projects/e2e_smoke_test_ppt169_20260701/` (test project, not skill files)
- **Reason**: 端到端验证修复后的主流程实际行为是否与文档一致，覆盖 Confirm UI / quality gate / export 关键路径
- **Before**: 无 E2E smoke test 基线
- **After**: 主流程 Steps 1→2→4→6→7 完整走通。发现 3 项问题：
  1. **icon inventory 未验证**: Strategist 阶段写入 `tabler-outline/export`，实际文件名为 `file-export`。`finalize_svg.py` 报 icon not found，`svg_to_pptx.py` 因未嵌入的 `<use data-icon>` 抛 `SvgNativeConversionError`。**修复**: 修正 SVG 和 spec_lock 中的 icon 名称为 `file-export`。
  2. **e2e_validate SVG 命名约定**: validator 期望 `P01_*.svg`，实际生成 `01_*.svg`，导致 SVG count 检查显示 0。PPTX 本身验证通过 (4 slides + notes)。
  3. **visual_review 环境限制**: 当前模型 (mimo-v2.5-pro) 无 multimodal 能力，无外部 vision API key。按 visual-review.md Path 3 标记 `vision_available: false`，待用户人工验证。
- **Risk**: low（仅运行验证，未修改 skill 脚本或工作流文件）
- **Human reviewed**: pending

### 2026-07-01 — Kubernetes blueprint example SVG quality repair
- **Files**: `examples/ppt169_kubernetes_blueprint_2026/svg_output/01_cover.svg`, `02_two_planes.svg`, `03_control_plane.svg`, `05_pod_lifecycle.svg`, `06_service_types.svg`, `07_storage.svg`, `08_ha_topology.svg`, `09_api_spine.svg`, `10_takeaways.svg`, `docs/change-log.md`
- **Reason**: 修复示例项目 quick gate 中剩余的 SVG 数据质量硬错误，不修改质量规则、不重新生成 PPT
- **Before**: 示例 SVG 中存在低于绝对下限的 `font-size="9"`、文本符号 `✓/✗/★`，以及未声明的 `#000000` 渐变色，导致 `svg_quality_checker.py` 和 `harness_gate.py --quick` 失败
- **After**: 将硬错误字号提升到 10px；将文本符号替换为普通文本语义；将黑色渐变 stop 改为已锁定背景色；`svg_quality_checker.py` 不再报告 error，quick gate 可通过
- **Risk**: low（仅修复示例 SVG 数据；保持页数、文件名、页面结构和视觉风格不变；未改脚本逻辑、未导出 PPTX）
- **Human reviewed**: pending

### 2026-07-01 — Windows quick gate diagnostics repair
- **Files**: `skills/ppt-master/scripts/svg_quality_checker.py`, `skills/ppt-master/scripts/spec_compliance_check.py`, `skills/ppt-master/scripts/harness_gate.py`, `docs/change-log.md`
- **Reason**: 修复轻量验证中 Windows 控制台编码崩溃、旧示例 SVG 命名漏检和 chart index 嵌套结构误判
- **Before**: `svg_quality_checker.py` 在 GBK 控制台打印 `✓/✗/★` 等字符会 `UnicodeEncodeError`；`spec_compliance_check.py` 只扫描 `P*.svg`，对旧示例 `01_cover.svg` 命名误报 `No SVG output found`；chart 模板校验只读 `charts_index.json` 顶层 key，误判已存在于 `charts` 下的模板缺失；`harness_gate.py --quick` 把跳过的 e2e 显示为 PASS
- **After**: SVG checker CLI 入口配置 UTF-8 stdio；spec compliance 扫描所有 `*.svg` 并支持 `charts_index.json` 的 `charts` 嵌套结构；quick gate 将跳过的 e2e 标为 SKIP，剩余失败定位到示例 SVG 质量问题
- **Risk**: low（脚本鲁棒性和诊断输出修复；不改生成流程、不改示例 SVG、不补模板数据）
- **Human reviewed**: pending

### 2026-07-01 — Agent and workflow entry consistency repair
- **Files**: Agent entries (`AGENTS.md`, `CLAUDE.md`, `docs/ai-rules-shared.md`, `docs/claude-reference.md`, platform rule files); workflow/docs (`skills/ppt-master/SKILL.md`, `skills/ppt-master/workflows/stages/visual-review.md`, `skills/ppt-master/workflows/profiles/beautify-pptx.md`, `docs/routing.md`, getting-started/audio/roadmap/technical docs); scripts/templates docs (`skills/ppt-master/scripts/README.md`, `skills/ppt-master/scripts/docs/project.md`, `skills/ppt-master/scripts/project_manager.py`, `skills/ppt-master/scripts/smoke_check.py`, `skills/ppt-master/scripts/svg_to_pptx*.py`, `skills/ppt-master/templates/**`)
- **Reason**: 文档 / workflow / Agent 入口一致性修复，统一多入口对默认流程、验证命令、导出源和资源发现的描述
- **Before**: 多个入口仍把 `visual-review` 写成仅显式请求触发；`CLAUDE.md` 指向不存在或不匹配的验证命令；`import-sources` 示例默认带 `--move`，容易误移动源文件；`svg_final` 仍被部分帮助文案描述为推荐导出源；布局根级 SVG 被混入目录索引，资源发现边界不清
- **After**: `visual-review` 统一为质量门禁后默认推荐、仅显式 opt-out 跳过；Agent 入口改为有效的 smoke / harness / e2e 验证说明；`import-sources` 默认示例不移动原件并明确 `--move` / `--copy` 边界；导出说明统一为 native 默认读取 `svg_output/`、`svg_final` 用于预览 / legacy snapshot；模板索引只列 layout directories，根级 SVG 作为可按 basename 引用的单页内建模板说明
- **Risk**: medium（涉及 Agent 入口与 workflow 默认行为说明，可能影响后续代理执行路径；改动主要是文档/help/索引一致性，不声称已运行生成流程）
- **Human reviewed**: pending

### 2026-07-01 — Review follow-up documentation fixes
- **Files**: `docs/zh/audio-narration.md`, `skills/ppt-master/templates/layouts/README.md`, `skills/ppt-master/templates/spec_lock_reference.md`, `docs/change-log.md`
- **Reason**: 落实 git diff 人工审查发现的两处文档语义漂移
- **Before**: 中文音频文档仍暗示页内元素动画默认保留；布局 README 将根级 SVG 说成不可复制的 planning patterns，但 spec_lock / 校验仍允许按 SVG basename 引用
- **After**: 中文音频文档与英文版一致，说明只保留默认页间转场和显式启用的页内元素动画；布局文档明确根级 SVG 是可被 `page_layouts` 引用的单页内建模板，但不属于 `layouts_index.json` 的目录索引
- **Risk**: low（仅文档语义修正，不改脚本逻辑）
- **Human reviewed**: pending

### 2026-07-01 — Python help examples consistency cleanup
- **Files**: `skills/ppt-master/scripts/smoke_check.py`, `skills/ppt-master/scripts/project_manager.py`, `docs/change-log.md`
- **Reason**: 清除最终复扫后维护者确认的 Python 帮助/示例残留
- **Before**: `smoke_check.py` docstring 使用 repo-root 下不可直接执行的 `python3 scripts/smoke_check.py`；`project_manager.py` epilog 示例仍默认带 `import-sources ... --move`
- **After**: `smoke_check.py` 示例改为 `python3 skills/ppt-master/scripts/smoke_check.py`；`project_manager.py` import 示例改为无 flag 默认导入
- **Risk**: low（仅帮助文案/docstring，不改运行逻辑）
- **Human reviewed**: pending

### 2026-07-01 — Final consistency sweep follow-up
- **Files**: `skills/ppt-master/scripts/README.md`, `skills/ppt-master/workflows/profiles/beautify-pptx.md`, `docs/audio-narration.md`, `docs/change-log.md`
- **Reason**: 补齐最终复扫发现的少量旧示例和容易误读的动画保留说明
- **Before**: 脚本 README 和 beautify workflow 的 `import-sources` 示例默认带 `--move`；音频导出文档未说明页内元素动画只有显式启用时才保留
- **After**: 示例改为无 flag 默认导入，并补充 `--move` 仅用于明确迁移原件；音频导出文档改为保留默认页间转场和任何显式启用的页内元素动画
- **Risk**: low（仅文档/workflow 文案，不改 Python 源码、不启动服务、不运行生成流程）
- **Human reviewed**: pending

### 2026-07-01 — svg_to_pptx CLI help source-default correction
- **Files**: `scripts/svg_to_pptx.py`, `scripts/svg_to_pptx/pptx_discovery.py`, `scripts/svg_to_pptx/pptx_cli.py`, `docs/change-log.md`
- **Reason**: 修复最终一致性复扫遗留的源码帮助文案漂移，避免 `svg_final` 被描述为推荐导出源
- **Before**: thin wrapper 和 CLI 示例默认带 `-s final`；`svg_final` help/docstring 写作 recommended；CLI animation help 仍暗示默认 `auto`
- **After**: 默认示例改为无 `-s`；`svg_final` 描述为 preview / legacy source；动画 help 明确默认 `none`，用 `-a auto` 才开启元素级动画
- **Risk**: low（仅 CLI/help/docstring 文案，不改导出逻辑）
- **Human reviewed**: pending

### 2026-07-01 — Final consistency sweep documentation fixes
- **Files**: `workflows/stages/visual-review.md`, `docs/getting-started.md`, `docs/zh/getting-started.md`, `docs/claude-reference.md`, `docs/change-log.md`
- **Reason**: 修复最终一致性复扫发现的残留旧表述，避免 visual-review、动画默认值和 import-sources 示例互相矛盾
- **Before**: `visual-review.md` 仍提到 legacy opt-in；getting-started 中英文版仍暗示元素级动画默认级联；claude-reference 的 import 示例默认带 `--move`
- **After**: visual-review 只保留默认推荐 + 显式 opt-out；getting-started 明确页间转场默认开启、页内元素动画默认关闭；claude-reference 的 import 示例改为无 flag 默认并补充 `--move` / `--copy` 使用边界
- **Risk**: low（仅文档一致性修正，不改源码、不启动服务、不运行生成流程）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard auto-launch daemon
- **Files**: `scripts/dashboard/server.py`, `scripts/dashboard_launcher.py` (NEW), `SKILL.md`, `docs/change-log.md`
- **Reason**: 做 PPT 时自动后台启动统一 Dashboard，同时保证启动失败不阻塞主生成流程
- **Before**: Dashboard 只能前台启动；已有服务时普通启动返回错误；PPT 主流程没有统一 Dashboard 的自动启动规则
- **After**: `dashboard/server.py <project_path> --daemon` 复用现有 lock URL 或后台启动服务并快速返回；默认端口 `8765`，占用时选择下一个安全端口且跳过 `5060`；浏览器打开 `http://127.0.0.1:<port>/`；日志写入 `<project>/dashboard/dashboard.log`；SKILL.md Step 2 记录非阻塞自动启动规则
- **Risk**: low（只新增 Dashboard 后台启动入口和工作流说明；Dashboard 仍只读，不自动确认、生成、导出或应用注解）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M2-M6 final integration acceptance
- **Files**: `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 执行 Dashboard M2-M6 最终集成验收，修复前后端已实现能力未接线和预览目录混杂问题
- **Before**: M4 安全动作 API 和 M5 Trace/健康度后端已存在但前端未消费；Confirm / Preview / Quality 页面缺少受控动作入口；产物日志页 Trace 只能显示默认日志，不能调用后端过滤分页；SVG 放大预览会把 `svg_output/` 与 `svg_final/` 两套 SVG 混在同一个页码条中
- **After**: 前端接入 `/api/actions` 的命令预览、确认弹窗、POST `confirm:true` 和 action 状态轮询；管线总览显示 `/api/state.health_summary`；产物与日志页调用 `/api/log` 的关键词、Step、类型、排序和分页过滤；SVG 放大预览按所在目录翻页，PPTX 仍优先使用 `svg_output/` 页面；补齐相关控制台样式
- **Risk**: low（只接线已有 Dashboard API 和修复预览范围；不新增生成、导出、注解应用能力；安全动作仍需用户确认后才 POST 执行）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M6 Chinese product polish
- **Files**: `scripts/dashboard/static/index.html`, `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 执行 Dashboard 后续实施 M6，统一中文产品化文案，补齐只读控制台的加载、空状态、错误状态、可访问性和移动端维护细节
- **Before**: 前端仍有部分英文导航/页眉/初始状态文案；API 读取失败时多处会退化为空内容；若干按钮和链接缺少 title / aria 状态；移动端顶栏、modal 操作区和产物按钮存在文字挤压风险；CSS 有一处粘连选择器
- **After**: 静态入口与主要页面文案统一为中文，保留 Confirm UI / Live Preview / SVG / PPTX / E2E 等必要技术名；读取失败显示错误摘要和重试入口；modal、产物按钮、服务入口补齐 title / aria-disabled / aria-expanded / aria-pressed；720px 宽度下导航、按钮组、modal 标题和操作区增加防溢出布局；清理粘连 CSS 规则
- **Risk**: low（只读前端展示与维护层改动；不启动服务，不运行生成、导出、质量或注解应用命令，不改变 Dashboard 功能行为）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M2 artifact browser and preview enhancements
- **Files**: `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 执行 Dashboard 后续实施 M2，完善产物页的文件浏览、筛选排序和放大预览交互
- **Before**: 产物页只能按类型折叠浏览，缺少文件搜索、Step 筛选和排序；放大弹窗仅支持 SVG/PPTX，且没有适配宽度、适配高度、100%、适配窗口控制；PDF 只能在右侧 iframe 或新窗口查看
- **After**: 产物页新增文件名/路径/类型搜索、Step 1-8 筛选、修改时间/名称/大小排序，当前预览文件被筛掉时保留右侧预览并提示；SVG/PPTX/PDF 统一使用放大预览 modal，支持新窗口打开和四种缩放模式；SVG/PPTX 仍保留多页切换，PDF 不显示页码条
- **Risk**: low（只读前端展示与交互层改动；不运行质量脚本，不启动服务，不改变 PPT 生成/导出或安全动作层）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M3 structured quality center
- **Files**: `scripts/dashboard/quality_reader.py`, `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 执行 Dashboard 后续实施 M3，将质量中心从 JSON 原文展示升级为结构化质量矩阵和三级问题报告
- **Before**: `/api/quality` 主要聚合旧 harness 结构；解析失败的报告会被跳过；前端质量中心以状态行和 JSON 原文为主，缺少 must_fix / should_fix / accepted_risks 分组
- **After**: `quality_reader.py` 统一归一化 harness、svg_quality、spec_compliance、e2e、integrated-review 和 visual review 报告，保留旧字段兼容；解析失败报告转为 parse warning 而非抛错；前端质量中心展示 Overall / Spec / SVG / E2E / Visual Review 状态矩阵、三级问题列表、可点击关联产物和折叠原始 JSON
- **Risk**: low（只读解析和展示层改动；不运行质量脚本，不改变 PPT 生成/导出流程）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M4 backend safe actions
- **Files**: `scripts/dashboard/actions.py` (NEW), `scripts/dashboard/server.py`, `docs/change-log.md`
- **Reason**: 执行 Dashboard M4 后端部分，为 Confirm UI、Live Preview 和质量检查提供显式确认、白名单、POST-only 的安全动作 API
- **Before**: Dashboard 只能读取 Confirm / Live Preview 状态，没有后端动作层；质量检查也没有统一的受控触发入口
- **After**: 新增安全动作模块，限定 `start-confirm`、`start-preview`、`run-quality` 三类动作；执行请求必须 POST 且包含 `confirm: true`；所有 subprocess 使用列表参数和固定命令；服务已运行时直接返回 existing URL；server.py 注册动作启动、命令预览和状态查询 API
- **Risk**: medium（新增受控执行入口；仅限辅助 UI/质量脚本，不包含继续生成、导出或应用注解）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M5 backend trace filters and health summary
- **Files**: `scripts/dashboard/trace_store.py`, `scripts/dashboard/health_reader.py` (NEW), `scripts/dashboard/state_reader.py`, `scripts/dashboard/server.py`
- **Reason**: 执行 Dashboard M5 后端部分，为 Trace 日志查询补齐关键词过滤和分页排序语义，并在 `/api/state` 输出项目健康度摘要
- **Before**: Trace 查询只支持 type/step/time/limit/offset/order 的基础过滤，`/api/log` 不透传关键词 query；`/api/state` 没有 health_summary，前端无法区分 healthy/warn/blocked/unknown
- **After**: `query_trace()` 支持 `type`、`step`、`query`、`limit`、`offset`、`order`，无 `trace.jsonl` 时稳定返回空列表；新增 `health_reader.py` 基于 Step 4 确认、质量状态、手动图片缺失、导出和服务状态保守派生 `health_summary.status` 与 `reasons`；`state_reader.py` 将摘要加入 `/api/state`
- **Risk**: low（只读派生逻辑和查询过滤；不启动服务，不运行生成、导出或质量脚本）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard next-stage execution guide
- **Files**: `docs/design/dashboard-next-execution-guide.md` (NEW)
- **Reason**: 用户要求将 Dashboard 后续计划落实为详细、可执行的编码提示词和执行文档，便于后续 coding agent 直接按阶段实现
- **Before**: 只有统一控制台总设计和口头后续计划，缺少 M2-M6 的分阶段编码提示词、安全边界、验收标准和回归测试清单
- **After**: 新增 Dashboard 后续实施执行文档，覆盖总原则、当前基线、M2 产物浏览、M3 质量中心、M4 安全动作、M5 Trace/健康度、M6 中文产品化、通用回归测试和可复制编码提示词模板
- **Risk**: low（仅新增设计/执行文档，不改变运行时代码）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard premium pages and enlarged slide preview
- **Files**: `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 用户反馈除产物与日志外的页面不够精致，并希望 SVG/PPTX 预览可放大为弹窗且支持切换页面
- **Before**: 管线总览、步骤工作台、确认中心、实时预览、质量中心主要由普通白色卡片组成，视觉层级弱；SVG/PPTX 只能在右侧预览区小尺寸查看，PPTX 相关 SVG 页只能用页码新窗口打开
- **After**: 非产物页面新增 hero 状态区、管线轨道、premium 指标卡、强化状态面板和工作台网格；SVG/PPTX 预览面板新增“放大预览”，以全屏弹窗展示 SVG 页面，支持左右按钮、键盘左右键、页码条和新窗口打开
- **Risk**: low（仅前端展示与交互层改动；后端 API、生成管线、Confirm UI 和 Live Preview 启动行为不变）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard artifact browser and compact UI polish
- **Files**: `scripts/dashboard/static/app.js`, `scripts/dashboard/static/style.css`
- **Reason**: 用户确认 Dashboard 可用后反馈产物列表过长、同类型文件重复、预览位置不便、非产物页面卡片过大，以及右上角 Confirm / Preview 状态语义不清
- **Before**: 产物与日志页使用平铺表格，长列表会把预览推到底部；左侧产物区域没有独立滚动；管线/步骤/确认/预览/质量页卡片密度偏低；右上角服务入口在未运行时仍像可用按钮
- **After**: 产物按文件类别聚合为可展开的类型文件夹，文件抽屉和产物浏览器独立滚动，右侧预览固定在可见区域；PPTX/PDF/音频/视频/图片/SVG/文本类文件按浏览器可预览能力展示；核心页面改为更紧凑的指标、步骤卡、状态行和服务卡；右上角入口改为“打开确认/确认未运行”“打开预览/预览未运行”并明确 disabled 状态
- **Risk**: low（仅前端展示层改动；Dashboard 仍为只读，不改变生成管线、Confirm UI 或 Live Preview 启动行为）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard M1 implementation
- **Files**: `scripts/dashboard/server.py` (NEW), `scripts/dashboard/state_reader.py` (NEW), `scripts/dashboard/artifact_registry.py` (NEW), `scripts/dashboard/bridge.py` (NEW), `scripts/dashboard/event_bus.py` (NEW), `scripts/dashboard/watcher.py` (NEW), `scripts/dashboard/quality_reader.py` (NEW), `scripts/dashboard/trace_store.py` (NEW), `scripts/dashboard/__init__.py` (NEW), `scripts/dashboard/static/index.html` (NEW), `scripts/dashboard/static/app.js` (NEW), `scripts/dashboard/static/style.css` (NEW)
- **Reason**: 执行统一控制台 M1，实现只读 Dashboard、SSE 状态推送、文件变化监听、产物扫描、质量报告读取、Confirm UI / Live Preview 状态桥接和 6 页静态前端
- **Before**: `scripts/dashboard/` 只有 contracts/api/sse 三个 JSON 契约，无法启动本地控制台，也没有 API / SSE / 前端页面
- **After**: 新增 `dashboard/server.py` CLI，提供 `/api/state`、`/api/step/<n>`、`/api/artifacts`、`/api/quality`、`/api/log`、`/api/config`、`/api/events` 和 bridge API；前端提供管线总览、步骤工作台、确认中心、实时预览、质量中心、产物与日志 6 个 hash route
- **Risk**: low（新增独立只读服务；不修改 Confirm UI、Live Preview、生成管线或质量脚本行为）
- **Human reviewed**: pending

### 2026-06-30 — Dashboard unified design synthesis
- **Files**: `docs/design/dashboard-unified-design.md` (NEW)
- **Reason**: 接续中断的三阶段设计工作流，将后端架构、前端架构、数据契约/SSE/API、集成迁移方案合成为一份可实施设计，并补齐 8 步管线覆盖验证
- **Before**: `scripts/dashboard/` 已有 contracts/api/sse 三个 JSON 契约，但缺少统一的后端 Blueprint、前端 6 页、文件 watcher、现有 Confirm UI / Live Preview 迁移与 Phase 3 验证文档
- **After**: 新增统一控制台设计文档，明确 Flask + 静态前端的最小迁移路线、状态派生来源、SSE event bus、artifact registry、quality reader、6 个前端页面、8 步管线覆盖与第一版实施任务
- **Risk**: low（仅新增设计文档，不改变运行时代码）
- **Human reviewed**: pending

### 2026-06-30 — Code quality optimization: exception handling, deduplication, frontend, docs
- **Files**: `scripts/finalize_svg.py`, `scripts/image_gen.py`, `scripts/image_search.py`, `scripts/animation_config.py`, `scripts/e2e_validate.py`, `scripts/confirm_ui/server.py`, `scripts/svg_editor/server.py`, `scripts/json_utils.py` (NEW), `scripts/confirm_ui/static/app.js`, `scripts/confirm_ui/static/style.css`, `scripts/svg_editor/static/index.html`
- **Reason**: 五维并行审查（Python/前端/文档/架构）发现 30 项确认问题：宽泛异常处理、重复代码、CSS 选择器冗余、缺失 ARIA、文档孤立、AI 配置重复
- **Before**: finalize_svg.py 4 处 bare `except Exception` 静默吞掉错误；image_gen.py 和 image_search.py 各自重复 atomic write 实现；animation_config.py 不区分 FileNotFoundError vs ValueError；confirm_ui/style.css 存在重复的 .hex-override/.swatches 选择器；svg_editor/index.html 缺少 ARIA 属性；4 个 AI 配置文件 70-80% 内容重复
- **After**: 异常收窄为具体类型 (OSError/ValueError/ET.ParseError)；新建 json_utils.py 共享模块，atomic_write_json() 消除重复；animation_config.py 捕获 ValueError；e2e_validate.py 捕获 (OSError, KeyError, ValueError)；confirm_ui/server.py 和 svg_editor/server.py 异常添加日志；CSS 去重；前端添加 debounce 和 ARIA；docs/zh/ 5 个文件添加语言切换链接；claude-reference.md 添加 TOC 和孤立文档链接；AI 配置抽取 docs/ai-rules-shared.md 单一来源
- **Risk**: low
- **Human reviewed**: pending

### 2026-06-30 — Deep project audit: security, workflow consistency, documentation sync
- **Files**: `SKILL.md`, `scripts/svg_editor/server.py`, `scripts/svg_quality_checker.py`, `workflows/detailed-outline.md`, `references/strategist.md`, `docs/change-log.md`
- **Reason**: 全面深度审查发现安全、工作流一致性、错误处理、文档同步问题
- **Before**: CSS 注入正则分散且不一致；svg_quality_checker 静默吞异常；SKILL.md 缺少条件工作流链路全局视图和 4 个 beautify 脚本条目；strategist.md 不感知 detailed_outline.json；detailed-outline 验证失败无回退路径；change-log 6 项 pending review；svg_editor 魔法数字
- **After**: 合并 CSS 安全正则为命名常量 `_UNSAFE_COLOR_RE` + `_UNSAFE_VALUE_RE`；添加 `isinstance(data, dict)` 类型守卫；svg_quality_checker 4 处静默 except 添加 `logger.debug`；SKILL.md Step 2 添加研究→生成条件链路表；SKILL.md 脚本表补充 beautify_inventory/beautify_identity/pptx_to_svg/svg_editor 4 个条目；strategist.md 添加 detailed_outline.json 集成指导；detailed-outline.md 添加验证失败回退流程；change-log 6 项 pending 全部完成审查（标记 reviewed yes）；svg_editor 长度限制统一为 `_MAX_ELEMENT_ID_LEN` / `_MAX_ANNOTATION_LEN` 常量
- **Risk**: low（所有改动为增强型：添加守卫/日志/文档，不改变现有行为流程）
- **Human reviewed**: yes (2026-06-30)

### 2026-06-29 — Beautify layout analysis step + anti-card-grid rules
- **Files**: `workflows/profiles/beautify-pptx.md`, `references/executor-base.md`, `references/strategist.md`, `templates/spec_lock_reference.md`
- **Reason**: 半导体PPT美化实测暴露核心缺陷——美化版每页退化为卡片网格，丢失时间轴叙事、动态构图、章节过渡页视觉冲击力。根因：beautify 路径从内容提取直接跳到 Executor，无布局分析步骤；detailed-outline.md 的 per-page 布局规划工具（persuasion_action, content_relation）仅在深度调研路径运行
- **Before**: beautify-pptx.md Step 4→Step 5 无中间布局分析；Executor 在无 content_relation 指导下默认生成卡片网格；章节过渡页无视觉最低标准；strategist.md 无美化模式 page_rhythm 派生规则
- **After**: 新增 Step 4.5 Layout Analysis（产出 beautify_layout_analysis.json，含 per-page refined_page_type/persuasion_action/content_relation/layout_family/why_not_card_grid/preserve_source_logic/background_strategy + diversity_check 门）；executor-base.md 新增 content_relation→布局映射表 + 卡片网格自检规则 + 章节过渡页视觉最低标准（4 种技术至少用 2 种）；strategist.md 新增美化模式 page_rhythm 从 layout analysis 派生规则；spec_lock_reference.md 增加美化模式注释
- **Risk**: medium（改变美化流程行为，新增必要步骤；现有非美化管线不受影响）
- **Human reviewed**: yes (2026-06-30) — Step 4.5 well-structured: clear fields, mapping table, diversity gate, JSON output schema. spec_lock_reference already references it for page_rhythm derivation. Affects beautify path only.

### 2026-06-29 — External vision model integration (vision_check.py)
- **Files**: `scripts/vision_check.py` (新建), `scripts/vision_backends/` (新建: __init__.py, backend_common.py, backend_openai_format.py, backend_anthropic_format.py, backend_ollama.py), `workflows/stages/visual-review.md`, `SKILL.md`
- **Reason**: 当主模型无多模态能力时，通过外部视觉 API 完成 PNG 视觉质检
- **Before**: visual-review 依赖主模型的多模态能力；无多模态时只能跳过或人工审阅
- **After**: vision_check.py 支持 OpenAI 兼容格式（GPT-4o/DeepSeek-VL/Qwen-VL/SiliconFlow/OpenRouter/Gemini）+ Anthropic 兼容格式（Claude/Bedrock）+ 本地 Ollama；visual-review.md 新增三路径检测（原生多模态 / 外部 API / 无视觉）
- **Risk**: low（新独立脚本 + workflow 文档扩展，不影响现有流程）
- **Human reviewed**: yes (2026-06-30) — independent script, multi-provider fallback, no existing flow affected.

### 2026-06-29 — Phase 4: PPT Hell 移植（批次审阅 + 视觉自检默认化 + SKILL.md 集成）
- **Files**: `workflows/batch-review.md` (新建), `workflows/stages/visual-review.md`, `SKILL.md`
- **Reason**: 长 deck 分批次审阅减少返工；视觉自检从 opt-in 改为默认推荐
- **Before**: 无批次审阅模式；visual-review 仅用户主动请求时运行；SKILL.md 无容量预检和批次审阅入口
- **After**: batch-review.md 提供 opt-in 分批生成+反馈闭环；visual-review 默认启用（可 skip）；SKILL.md Step 5 前增加容量预检提示，Step 6→7 间增加批次审阅和视觉自检说明
- **Risk**: medium（visual-review 默认化改变行为；batch-review 为 opt-in 无风险）
- **Human reviewed**: yes (2026-06-30) — visual-review default change has clear opt-out ("跳过视觉自检" / "skip visual review"). batch-review is opt-in only.

### 2026-06-29 — Phase 3: PPT Hell 移植（svg_quality_checker 三级输出 + revision-loop 升级机制）
- **Files**: `scripts/svg_quality_checker.py`, `workflows/revision-loop.md`
- **Reason**: 结构化审阅输出（must_fix/should_fix/accepted_risks）替代扁平列表；两轮未解决自动升级防止无效循环
- **Before**: quality checker 仅输出 errors/warnings 列表；revision-loop 无升级机制（仅 20 轮上限）
- **After**: 新增 `--integrated-review` flag 输出三级 JSON + gate_status；revision-loop 追踪 issue categories，同类问题 2 轮未解决自动升级到用户
- **Risk**: low（新 flag 不影响默认输出；升级机制为追加规则）
- **Human reviewed**: yes (2026-06-30) — new flag is additive; default output unchanged.

### 2026-06-29 — Phase 2: PPT Hell 移植（容量预检脚本）
- **Files**: `scripts/layout_capacity_check.py` (新建)
- **Reason**: 在 Executor 生成 SVG 前预估文字是否能放入版式区域，避免生成后才发现溢出
- **Before**: 无容量预检，溢出问题仅在 SVG 生成后由 svg_quality_checker 检出
- **After**: 新脚本基于 CJK 字宽估算 + 标准 zone 尺寸，输出 ok/tight/overfull/too_empty per page
- **Risk**: low（独立新脚本，不影响现有流程）
- **Human reviewed**: yes (2026-06-30) — standalone script, recommended not mandatory.

### 2026-06-29 — Phase 1: PPT Hell 设计模式移植（文档/schema 扩展）
- **Files**: `workflows/detailed-outline.md`, `templates/spec_lock_reference.md`, `references/strategist.md`, `references/executor-base.md`
- **Reason**: 整合 PPT Hell 项目的优秀流程设计——版式思考 6 问框架、文案保真契约、阶段绑定注释
- **Before**: detailed-outline 无版式论证字段；spec_lock 无文案保真机制；references 无阶段绑定提示
- **After**: 6 个可选 Layout Thinking 字段（persuasion_action, content_relation, information_anchor, reading_path, why_not_alternatives, anti_laziness_check）；spec_lock 新增 `## copy_contract` section（preservation_level 默认 balanced）；references 头部添加 PHASE 注释
- **Risk**: low（所有新增字段为 Optional，不影响现有项目）
- **Human reviewed**: yes (2026-06-30) — all new fields are Optional, no impact on existing projects.

### 2026-06-27 — Initial change log created
- **Files**: `docs/change-log.md`
- **Reason**: P1-3 from development manual — establish AI modification audit trail
- **Before**: No change tracking for workflow/script modifications
- **After**: All modifications logged with before/after behavior

### 2026-06-27 — PvZ 7 轮迭代问题固化：executor-base.md + deep-research.md 规则增强

- **Files**: `references/executor-base.md`, `workflows/deep-research.md`
- **Reason**: plants_vs_zombies 项目经 7 轮迭代发现的 8 个系统性问题（P1-P8），属于 deep-research 工作流和 Executor SVG 生成流程的结构性缺陷，需固化到工作流文件使未来所有 PPT 项目自动遵守
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks（修改前后一致，无回归）

**P1 — SVG 文字居中规则增强** (`executor-base.md` §10)
- **Before**: 仅规定 `text-anchor="middle"` + canvas center，无分栏布局特殊处理
- **After**: 新增"Split-layout centering"子节，含 5 种分栏比例的 center x 坐标表（3:7, 4:6, 7:3, 6:4, custom），公式 `text_x = (panel_left + panel_right) / 2`；禁止在分栏布局中使用 `x=640`

**P2 — 视觉装饰要求** (`executor-base.md` §17.1-17.2)
- **Before**: 无数据页/讲解页视觉增强强制规则，页面像 Word 文档
- **After**: 新增 §17.1"Visual Enrichment Rule"——数据页/讲解页/时间轴页必须有 ≥2/3 层增强（渐变背景、卡片阴影、装饰元素）；§17.2 卡片深度规则含 shadow filter 参数

**P3 — 遮罩/蒙版不透明度规则** (`executor-base.md` §17.3)
- **Before**: 无量化遮罩标准，opacity=0.88 不够
- **After**: 新增 §17.3"Overlay/Mask Opacity Rule"——深色底 ≥0.92，混合 ≥0.85，浅色底 ≥0.55；分栏过渡区遮罩延伸 ≥60px

**P4 — 字体最小值规则增强** (`executor-base.md` §14.2)
- **Before**: 仅 deep-dive body ≥22px、content body ≥20px、line height
- **After**: 新增全局绝对最小值 14px、脚注/页码 ≥12px（唯一例外）、数据页 body ≥16px、讲解页 body ≥18px、数据页卡片标签 ≥14px

**P5 — 网络素材搜集策略扩展** (`deep-research.md` §2.4)
- **Before**: 素材来源适配表含 5 种主题类型（风光/办公/历史/古籍/民俗）
- **After**: 新增 3 种类型——"游戏/IP/角色"（Playwright 优先→wiki→AI 降级）、"科幻/奇幻/动漫"、"小众亚文化/特定社群"

**P6 — ref/ 目录强制检查点** (`deep-research.md` §2.3a)
- **Before**: §2.3 仅提及 ref/ 目录，无强制执行机制
- **After**: 新增 §2.3a"Reference image collection — MANDATORY checkpoint"——Step 2 结束前 images/ref/ 必须 ≥1 张参考图，按主题类型给出来源优先级和最低数量，禁止空目录进入 Step 3

**P7 — 讲解页布局目录扩展** (`deep-research.md` §4.2b)
- **Before**: 4 种基础布局（left/right image-text, top-bottom, image-interspersed）
- **After**: 新增"Deep-dive layout catalog"含 7 种布局——新增"期刊风格时间轴""分支路径图""数据仪表盘""引言全页""对比分栏"；强制规则"连续 3 页不得使用相同布局"

**P8 — 垂直分布规则** (`executor-base.md` §14.5)
- **Before**: 无垂直空间利用规则，内容集中在上半部分
- **After**: 新增 §14.5"Vertical Distribution Rule"——safe area 分为 3 区（top/middle/bottom），每区 ≥20% 内容权重；底部 40% 全空 = 违规

- **Risk**: low（规则增强，不修改脚本逻辑）
- **Human reviewed**: pending
- **Risk**: low
- **Human reviewed**: N/A (new file)

### 2026-06-27 — 深度调研重构：7 步独立工作流 + 多 AI 浏览器自动化

- **Files**:
  - **新增**: `workflows/research/step1_outline.md`, `step2_search_plan.md`, `step3_search.md`, `step4_consolidate.md`, `step5_analysis.md`, `step6_narrative.md`, `step7_visual.md`
  - **新增**: `scripts/research/browse_ai.py`（Playwright 浏览器自动化搜索脚本）
  - **重写**: `workflows/deep-research.md`（从 824 行单体重写为 ~160 行编排器）
  - **删除**: `workflows/topic-research.md`（快速模式，被统一深度调研替代）
  - **修改**: `SKILL.md`, `docs/routing.md`, `docs/claude-reference.md`, `docs/faq.md`, `docs/zh/faq.md`, `docs/roadmap.md`, `docs/zh/roadmap.md`, `AGENTS.md`, `workflows/content-selection.md`, `references/strategist.md`
- **Reason**: 用户反馈深度调研流程耦合度高、各步骤不独立。参考 B 站视频"横评6大PPT开发Skill"的发布会准备流程，将研究拆为 7 个独立步骤，每步输出到独立文件夹，支持通过 Playwright 浏览器自动化调用不同 AI（ChatGPT/Grok/Perplexity）分工搜索
- **Before**: `deep-research.md` 为 824 行单体工作流（5 步耦合）；`topic-research.md` 为独立快速模式；搜索仅用内置 WebSearch
- **After**: `deep-research.md` 为编排器，协调 7 个独立步骤文件（`research/step1-7`）；每步输出到 `_research/stepN_name/`；`browse_ai.py` 支持通过 Playwright 自动化 ChatGPT/Grok/Perplexity 网页搜索；按内容类型分配 AI（技术→GPT，趋势→Grok，学术→Perplexity）；所有输入统一走深度调研
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks（修改前后一致，无回归）
- **Risk**: medium（架构重构，但仅涉及工作流 markdown 文件和新增脚本，未修改现有 Python 脚本逻辑）
- **Human reviewed**: pending

### 2026-06-28 — 视频建议实施：排版稳定性检测 + 布局自动修正 + 动画节奏规则 + 发布会品牌预设

- **Files**:
  - **修改**: `scripts/svg_quality_checker.py`（新增 3 个检查：layout_bounds, element_spacing, vertical_distribution）
  - **修改**: `scripts/finalize_svg.py`（新增 Step 5: fix-layout 自动修正文字溢出）
  - **修改**: `references/executor-base.md`（新增 §18 动画节奏强制规则, §19 视觉优先页规则）
  - **新增**: `templates/brands/event_presentation/design_spec.md`（发布会品牌预设）
  - **修改**: `templates/brands/brands_index.json`（新增 event_presentation 条目）
- **Reason**: B站视频横评中 PPT Master 排版评分 ★★☆、动画评分 ★★☆。分析发现 svg_quality_checker.py 完全没有布局边界/溢出/间距检测；executor-base.md 有生成规则但无自动化验证；动画节奏缺乏强制执行
- **Before**: 质量检查器无布局验证；finalize_svg.py 无自动修正能力；动画规则散落在 customize-animations.md 但 Executor 不强制参照；无发布会专用品牌预设
- **After**: svg_quality_checker.py 新增 check 12/13/14（文字溢出检测、元素间距检测、垂直分布检测）；finalize_svg.py 新增 fix-layout 步骤（文字溢出自动缩减字号）；executor-base.md 新增 §18（动画节奏按页面类型强制）和 §19（视觉优先页渲染策略）；event_presentation 品牌预设（暗色调、Apple keynote 风格）
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks（修改前后一致，无回归）
- **Risk**: low（新增检查和规则，不修改现有脚本核心逻辑）
- **Human reviewed**: pending

### 2026-06-28 — 深度调研执行闭环补齐：浏览器搜索降级 + 研究产物同步

- **Files**:
  - **修改**: `scripts/research/browse_ai.py`
  - **新增**: `scripts/research/sync_research_outputs.py`
  - **修改**: `workflows/deep-research.md`, `workflows/research/step3_search.md`, `workflows/research/step7_visual.md`
  - **修改**: `docs/change-log.md`
- **Reason**: 昨日 7 步深度调研重构已落地架构和文档，但浏览器搜索脚本缺少低质量重试、真实 fallback 记录、全部失败后的人工 WebSearch 交接；研究产物同步仍使用裸 `cp`，在 Windows 和目录缺失时不稳定
- **Before**: `browse_ai.py` 递归 fallback 但 manifest 只写目标 AI，低质量结果不会明确重试；三家浏览器 AI 全失败时文档暗示脚本可调用内置 WebSearch；hand-off 需要手写 `cp` / `cp -r`
- **After**: `browse_ai.py` 对空回复、少于 200 字、缺少来源 URL 的结果重试一次，manifest 记录 `ai_target` / `ai_used` / `fallback` / `fallback_chain` / `status` / `char_count` / `quality` / `output_file` / `image_suggestions` / `needs_manual_websearch`；全部失败时写出可复制人工 WebSearch prompt；新增同步脚本创建 `sources/`、`analysis/`、`images/ref/`、`images/web_assets/` 并复制研究产物；文档改为调用同步脚本并说明 WebSearch 是 Agent 手动降级能力
- **Smoke check**: 38 passed, 0 failed, 3 skipped / 41 checks；专项 `py_compile` 覆盖 `scripts/research/browse_ai.py` 和 `scripts/research/sync_research_outputs.py`
- **Risk**: medium（修改新研究流程脚本和 manifest 结构；主 PPT 生成流程未改）
- **Human reviewed**: pending

### 2026-08-03 — 迁移上游 `ppt`（v4.3.0）三阶段 Confirm UI 并适配，附完整性/审计工具
- **Files**: `skills/ppt-master/scripts/confirm_ui/server.py`, `skills/ppt-master/scripts/confirm_ui/static/*`（app.js/style.css/catalogs.json/index.html/style_previews）、`skills/ppt-master/scripts/language_tags.py`（新增）、`skills/ppt-master/scripts/server_common.py`、`skills/ppt-master/scripts/confirm_ui_gate.py`、`skills/ppt-master/scripts/docs/confirm_ui.md`、`skills/ppt-master/scripts/dashboard/state_reader.py`、`skills/ppt-master/SKILL.md`、`skills/ppt-master/references/strategist.md`、`skills/ppt-master/workflows/profiles/beautify-pptx.md`、`skills/ppt-master/scripts/attribution_guard.py`（新增）、`skills/ppt-master/attribution/identity.json`（新增）、`skills/ppt-master/scripts/prompt_audit.py` + `prompt_audit_manifest.json`（新增）、`skills/ppt-master/workflows/governance/failure-recovery.md`（新增）、`AGENTS.md`、`docs/change-log.md`
- **Reason**: 用户希望把已拉取到最新的上游 `ppt`（v4.3.0）项目的新一代 Confirm UI 迁入 DeepPPT2 并适配，同时吸收其完整性保护与审计工具。两仓库的 confirm_ui 同源（同为 Flask 三阶段轮询 + 三语界面），本仓库为旧两代，上游为「沟通契约 → 成套方案 → 生产机制」三阶段流。
- **Before**: Confirm UI 为旧版双 tier 流（单文件 `recommendations.json` + `tier:1→2`，`--daemon --wait`）；无语言标签规范化、无 session.json、无 wait-stage、无自动恢复；gate 校验 `tier==2`；server_common 无 `validate_port`/`popen_detached`
- **After**: Confirm UI 升级为三阶段流（`recommendations.stage1/2/3.json`，每阶段文件声明 `stage`，`--daemon` → `--wait-only --wait-stage stage1/2` → `--wait-only` → `--shutdown`）；新增 `primary_language`（BCP-47 必需）、沟通契约 7 开放字段、`design_directions` ≥3、`custom_candidates`、`template_application`、proactive 三开关、68 字体库、typography `sizes`；保留并叠加 DeepPPT2 扩展（`/template-file` 模板预览路由（修正 `_SKILL_DIR` 未定义潜伏 bug）、`template_route` dashboard 注入、`detailed_outline.json` layout_preview、三类 ai-image-comparison、`skip_visual_review` 透传）；gate 改为「浏览器确认须基于 stage3 推荐文件」+ 保留 fallback/template_selection/时间新鲜度检查；dashboard state_reader 识别分阶段推荐文件；新增 attribution_guard（DeepPPT2 身份清单 `attribution/identity.json` 摘要锁 + 关键管线文件存在性，`--register` 重注册，SKILL.md 顶部强制加载顺序 [NEEDS_HUMAN_REVIEW]）；新增 prompt_audit（token 预算审计，tiktoken 可选依赖，manifest v1 空档待校准）；新增 failure-recovery 恢复矩阵文档
- **Smoke check**: 55 passed, 0 failed, 3 skipped / 58 checks（基线 52/0/3）；专项冒烟驱动 `.tmp/smoke_confirm_ui.py` 覆盖三阶段确认、stage 跳级 409、DeepPPT2 注入、gate 三分支、daemon 生命周期，全部通过
- **Risk**: medium（Confirm UI 后端/前端整体换代 + SKILL.md Step 4 重写；PPT 生成主流程其余步骤未改）
- **Human reviewed**: pending

### 2026-08-03 — Phase 2：SKILL.md 四路由重构（薄入口 + routing.md + generate-pptx.md）
- **Files**: `skills/ppt-master/SKILL.md`（900 → 116 行）、`skills/ppt-master/workflows/routing.md`（新增）、`skills/ppt-master/workflows/generate-pptx.md`（新增，796 行）、`skills/ppt-master/workflows/index.md`（新增）、`skills/ppt-master/workflows/profiles/quick-generate.md`（新增）、`skills/ppt-master/workflows/stages/`（7 个工作流迁入：resume-execute / refine-spec / live-preview / verify-charts / visual-review / customize-animations / generate-audio）、`skills/ppt-master/workflows/profiles/beautify-pptx.md`（迁入）、`AGENTS.md`、docs/ 与 references/ 下 30+ 文件的链接重写、`docs/change-log.md`
- **Reason**: 用户确认四路由重构意向（"项目太重、效率不高"）；按 `plans/followup-migration-roadmap.md` Phase 2 执行，让后续 Phase 3-5 工作流直接落位路由架构
- **Before**: SKILL.md 为 900 行厚入口（脚本表 + 模板索引 + 工作流表 + Step 1-8 全量内容）；无路由选择权威；workflows/ 为 19 个平铺文件
- **After**: SKILL.md 薄入口（frontmatter + 全局纪律 + 加载顺序 + 四路由表 + 协议段）；`workflows/routing.md` 为路由选择权威（四路由矩阵；Enhance 占位待 Phase 3）；`workflows/generate-pptx.md` 承载 Step 1-8 与 DeepPPT2 全部门禁/合同内容（spec_lock/page_expression、harness_gate/e2e_validate/rendered_layout_check/visual-review、split-mode、memory_manager 等全部保留）；`workflows/index.md` 为全量工作流索引 + PPTX 路由边界；7 个 stage 工作流与 beautify 迁入 stages//profiles/；新增 quick-generate profile（适配 DeepPPT2 现有 lockless 能力，上游 --quick-generate 旗标列为 Phase 2.5 跟进项）；DeepPPT2 独有工作流（ppt-briefing / deep-research / research/ / content-selection / detailed-outline / image-text-linking / revision-loop / batch-review / create-template / create-brand / template-fill-pptx）保留原位并由 routing.md 声明归属
- **Smoke check**: 55 passed, 0 failed, 3 skipped / 58 checks（与 Phase 2 前基线一致）；全仓 784 条 markdown 链接逐一校验，0 条新增断链（剩余 9 条为预先存在的 `xxx.md`/`url` 占位链接）；`_smoke_` 项目端到端（init → dashboard → 三阶段确认 stage1 → gate → shutdown）通过并清理
- **Risk**: high（全仓引用面；SKILL.md 结构变更需人工审查）
- **Human reviewed**: pending（SKILL.md 路由表与 generate-pptx.md 提取内容建议人工抽查）

### 2026-08-03 — Phase 3：原生 PPTX 增强套件（Enhance 路由落地）
- **Files**: `skills/ppt-master/scripts/native_enhance_pptx.py`、`native_enhance_pptx_core.py`、`native_narration_pptx.py`、`native_payloads.py`、`native_pptx_animations.py`（新增，上游 pptx_animations 以新名引入）、`pptx_delivery_check.py`、`pptx_effects.py`、`pptx_opc_validation.py`、`pptx_transitions.py`、`pptx_animation_presets.json`、`pptx_to_svg/ooxml_loader.py`（新增）、`scripts/docs/pptx-transitions.md`（新增）、`skills/ppt-master/scripts/svg_to_pptx/drawingml_utils.py`（新增 PPT_SAFE_FONTS + text_uses_rtl）、`svg_to_pptx/pptx_notes.py`（新增 notes-master 构建器 + `include_notes_master` 参数）、`svg_to_pptx/pptx_builder.py`（新增 `_ensure_notes_master` 等辅助）、`svg_to_pptx/pptx_narration.py`（新增 AUDIO_MARKER 常量）、`workflows/native-enhance-pptx.md`（新增）、`workflows/routing.md`、`workflows/index.md`、`workflows/stages/generate-audio.md`、`SKILL.md`、`scripts/attribution_guard.py`、`scripts/README.md`、`docs/change-log.md`
- **Reason**: 按 `plans/followup-migration-roadmap.md` Phase 3 执行；音频路径按评估结论落地（Generate=导出时嵌入保持，Enhance=导出后 OOXML 补丁，共享 generate-audio 阶段）
- **Before**: 无 Enhance 路由；routing.md 中 Enhance 行为占位；DeepPPT2 导出器 notes 关系不含 notesMaster（其 python-pptx 基座无该部件）
- **After**: Enhance 路由全流程可用（init/plan/validate/apply 四命令）；上游动画模块以 `native_pptx_animations.py` 引入（避免替换 DeepPPT2 导出器依赖的旧 `pptx_animations.py`）；`ooxml_loader.py` 加性拷贝（emu_units 兼容）；`PPT_SAFE_FONTS`/`text_uses_rtl` 移植；`create_notes_slide_rels_xml` 增加 `include_notes_master` 参数（Generate 默认 False 行为不变，Enhance 传 True——修复 e2e 发现的 python-pptx 读回缺 notesMaster 关系问题）；generate-audio 补「共享阶段 + 双路由集成路径 + 禁止双嵌入」小节；attribution_guard 门禁清单追加 7 个新入口
- **Smoke check**: 64 passed, 0 failed, 3 skipped / 67 checks（基线 55，9 个新脚本自动纳入）；Phase 3 e2e：python-pptx 源 deck → init → plan 确认 → notes → ffmpeg 音频 → validate（含 ffprobe）→ apply → 解包断言（3 notesSlides / 3 mp3 / notesMaster / p:timing / useTimings）→ ppt_to_md 读回内容完整 → delivery report，全部通过
- **Risk**: medium（新路由 + 导出器 notes 关系函数的参数化改动，Generate 默认路径已验证不变）
- **Human reviewed**: pending

### 2026-08-03 — Phase 4：动画链完整移植 + 视频导出（用户确认完整移植）
- **Files**: `scripts/slide_roster.py`（新增）、`svg_to_pptx/animation_config.py`（以 ppt 版 1505 行替换 259 行，import 适配 5 处）、`scripts/animation_config.py`（顶层同步替换为 ppt 版）、`svg_to_pptx/semantic_markers.py`（新增最小版）、`svg_to_pptx/drawingml_converter.py`（trace 增加 page_role）、`svg_to_pptx/pptx_builder.py`（构建后增强：transition 校验 + animation 校验/配置派生回退写 trace）、`scripts/powerpoint_video.py` / `video_motion_plan.py` / `video_subtitles.py` / `narration_sync.py`（新增，narration_sync 改 3 处 import）、`workflows/stages/generate-audio.md`（Step 4.5 视频导出分支）、`docs/audio-narration.md` + `docs/zh/audio-narration.md`（自动导出章节）、`scripts/README.md`、`scripts/attribution_guard.py`（+5 门禁）、`plans/followup-migration-roadmap.md`、`docs/change-log.md`
- **Reason**: 按 roadmap Phase 4 执行；探索证明 video_motion_plan 与 narration_sync.animations 依赖 ppt 动画校验链（trace 的 animation/motion 字段、resolve/validate 链），用户选择完整移植动画链
- **Before**: DeepPPT2 无视频导出工具；trace 无 page_role/animation/motion 字段；animation_config 为 259 行简化版（无 transition 校验、无 groups 效果解析链）；动画 schema 无 slide 级 transition/animation 作用域
- **After**: 动画链完整可用（scaffold 新 schema → validate → svg_to_pptx 导出时 trace 写入 page_role + animation.rows[] + motion.advance_after_ms，严格校验失败时以写出 XML 的同一 seq_targets 配置派生回退，一致性由构造保证）；video_motion_plan 生成 motion plan（6 对象 video 条目）；narration_sync 三子命令可用（fingerprint/animations/subtitles）；powerpoint_video 真实导出验证通过（本机 Office 16.0，h264 1920×1080 16.4s）；video_subtitles 缺 stable-ts 时友好报错（可选依赖文档化）；generate-audio 增 Step 4.5 视频分支；PPTX 导出动画写入路径未替换（回归通过）
- **Smoke check**: 69 passed, 0 failed, 3 skipped / 72 checks（基线 64）；Phase 4 e2e 全通过（trace 增强 3/3、motion plan、narration_sync 三子命令、--check 探测、真实视频导出）；Phase 3 e2e 与音频契约回归全通过
- **Risk**: medium（导出器 trace 增强 + animation_config 替换；时序 XML 写入路径未动，回归验证）
- **Human reviewed**: pending
