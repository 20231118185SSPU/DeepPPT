# DeepPPT2 性能基线与 CI 风险报告（2026-08）

> 状态：Phase 3 基线报告（只读测量产物，2026-08-03 实测）。  
> 权威性：非运行规则；基线数字仅用于后续优化对比，优化目标阈值待用户确认后写入。  
> 配套：原始数据 `.tmp/perf_baseline.json`、`.tmp/smoke_timing.json`（gitignored，测量脚本 `.tmp/perf_baseline.py` 可复跑）。

---

## 0. 一句话结论

性能侧全部处于健康区间（smoke 完整 26.1s、单页示例导出 p50 3.7s、质量检查冷启动 p50 1.33s）；**真正的风险是质量门侧**：29/29 公开示例 `svg_quality_checker` 全部 rc=1（共因 = legacy `spec_lock.md` 缺 `pptx_structure.mode`），且迁移提交（`31298372`）尚未 push（`main` 领先 `origin/main` 1 个提交）——**一旦 push，CI svg-quality job 必然失败**（§3）。

## 1. 环境与方法

| 项 | 值 |
|---|---|
| OS | Windows 10.0.26200 x64（Git Bash） |
| Python | 3.12.13（uv 托管 cpython-3.12-windows-x86_64） |
| 日期 | 2026-08-03 |
| 方法 | `time.perf_counter()`；冷 = 每采样独立子进程；暖 = 同进程重复调用；p50/p95 = nearest-rank |
| Fixture | `examples/ppt169_kubernetes_blueprint_2026`（10 页，复制至 `.tmp/`，用于质量/dashboard/finalize）；`examples/ppt169_swiss_grid_systems`（用于导出，rc=0 可用） |

## 2. 性能基线（p50 / p95）

| 测量项 | n | p50 | p95 | 备注 |
|---|---|---|---|---|
| 解释器冷启动（`python -c pass`） | 10 | 56.8 ms | 81.8 ms | |
| 冷导入 `svg_quality` | 10 | 61.6 ms | 77.6 ms | |
| 冷导入 `svg_to_pptx` | 10 | 98.5 ms | 116.8 ms | 重构版导出器包 |
| 冷导入 `dashboard.server` | 10 | 473.2 ms | 556.0 ms | |
| 冷导入 `confirm_ui.server` | 10 | 445.9 ms | 480.7 ms | |
| `os.walk` 全仓（冷） | 10 | 369.4 ms | 424.9 ms | 24,203 文件 |
| `svg_quality_checker` 冷（完整 CLI） | 10 | 1,333.9 ms | 1,433.2 ms | fixture rc=1（既有 ERROR，见 §3） |
| `svg_quality_checker` 暖（同进程） | 5 | 374.4 ms | 386.1 ms | 暖/冷 ≈ 3.6×；说明冷启动大头是 import 链 |
| `dashboard/server.py --daemon` + 首次 HTTP | 10 | 1,861.8 ms | 2,106.8 ms | 0 失败 |
| `svg_to_pptx` 导出（swiss，10 页） | 3 | 3,724 ms | 4,052 ms | rc=0 ×3 |
| `finalize_svg`（冷） | 3 | 482.2 ms | 516.2 ms | rc=0 ×3 |
| `smoke_check --skip-help` | 3 | 2.3 s | 2.3 s | rc=0 |
| `smoke_check` 完整（162 checks） | 1 | 26.1 s | — | rc=0（勘误：盘点报告 §7 曾记「≈3 分钟」，系后台任务观测误判，实测 26.1s） |

**候选优化点（仅列为假设，未做任何优化；需 profiling 证明后单变量验证）**：
1. ~~quality checker 冷启动 import 链懒加载~~ **已实验并回退（2026-08-03）**：将 `svg_to_pptx.drawingml.converter` + `native_objects` 模块级 try/except import 改为函数内懒加载后，完整运行 p50 从 1334ms 升至 1664ms（**负优化 +25%**）——检查函数每次运行必达（每页都执行），openpyxl ~600ms 只是从启动移到检查时。已 `git checkout` 回退（smoke 156/0/4、guard、checker spot 均复验）。该方向关闭；如需继续，须改 `svg_to_pptx/native_objects` 包内部 import 结构（openpyxl 懒加载，波及导出器，风险高）。
2. dashboard daemon 启动 1.86s（含 import ~0.5s + 健康检查 + 首请求）——未实验。
3. 其余项均在合理区间，无优化必要。

**目标阈值**：按契约 §6，不在基线前臆定；待用户审阅本报告后单独确认（例如：「quality 冷启动 p50 降到 1.0s 以内」等）。

## 3. CI 风险发现（优先级高于性能）

### 3.1 事实链

| # | 事实 | 证据 |
|---|---|---|
| 1 | 29/29 `examples/*/` 的 `svg_quality_checker.py <dir>` 全部 rc=1 | 全量实测（修正版扫描，含被 `$(basename)` 命令替换吞 rc 的初扫纠错） |
| 2 | 全量共因：`spec_lock.md` 缺 `pptx_structure.mode: flat/structured`（v4.3.0 迁移后 release 契约） | swiss/attention/kubernetes 等抽查输出一致 |
| 3 | 部分示例另有内容级 ERROR（marker 颜色 2 例、emoji 文本、零宽 stroke 渐变等） | kubernetes（05/09 页）、attention（15 页）、building_effective_agents（03 页） |
| 4 | `kubernetes_blueprint` 导出在新导出器下 traceback（`drawingml/converter.py:1529`） | 实测；swiss/brutalist 导出 rc=0（非全量故障） |
| 5 | 迁移提交 `31298372`（2026-08-03 18:50）未 push：`main...origin/main [ahead 1]` | `git status -sb`、`git log` |
| 6 | CI svg-quality job：对每个有 `svg_output/` 的 examples 跑 checker，`|| status=1` | `.github/workflows/ci.yml:64-75`；checker 任何 ERROR → exit 1（`svg_quality/cli.py`） |

### 3.2 推断与影响

- **一旦 push，CI 三个 job 中 svg-quality 必红（29/29 示例失败）**；e2e job 视各示例导出成功率（至少 kubernetes 这类会失败）[推断，待 CI 实测]。smoke job 正常（本地 156/0/4 通过）。
- 原因链：v4.3.0 迁移升级了 checker 契约（spec_lock `pptx_structure.mode` 必填 + 新语法 ERROR 类），但 29 个 legacy 示例未回填，且迁移后本地/CI 均未对 examples 做过全量回归（CI 未触发 = 未 push）。
- 盘点报告 §6 曾记「CI 契约面：29 个示例全部具备 spec_lock + exports」——那是**结构存在性**，不是**质量通过性**；本报告补充通过性事实。

### 3.3 处置记录（2026-08-03，选项 A 已执行）

1. ✅ **模板 bug 修复**：`templates/spec_lock_reference.md` 的 `pptx_structure` 节原写 `- pptx_structure.mode: flat`，而解析器（`svg_quality/checker.py _PPTX_STRUCTURE_MODE_RE`）只匹配 `- mode: flat`——按模板回填会失败；已修为 `- mode: flat` 并更正「Remove the section for legacy decks」注释（checker 对 missing mode 报 ERROR，与注释矛盾）。
2. ✅ **29 个 legacy examples 回填**：`spec_lock.md` 追加 `## pptx_structure` + `- mode: flat`（按各文件行尾，CRLF×22 / LF×7；脚本 `.tmp/backfill_structure_mode.py`）。结果：**5/29 变绿**（brutalist / cangzhuo / global_ai_capital / lin_huiyin_architect_revised / swiss_grid）。
3. ⏳ **24 个仍红示例分类清单**（回填后）：

| 类别 | 示例 | 修复性质 |
|---|---|---|
| A. SVG root 缺 width/height | ai_image_guide、deepseek_evolution、march7th_hsr、meditation、arknights_amiya、doctor、fashion_weekly、kaltsit（8 个） | 机械（批量加属性，可脚本化） |
| B. 零宽 stroke 渐变 | attention、glassmorphism、high_rise_renewal、image_text_showcase、lin_huiyin_architect、lora_hu（6 个） | 页面级设计修改 |
| C. emoji 文本 | kalsit（★）、building_effective_agents（✓）、general_dark_tech（⚠）、indie_bookstore（★）、sugar_rush（✓）（5 个） | 内容级（换图标） |
| D. `<g>` 上 filter | home_design_trends、liziqi（2 个） | 页面级 |
| E. 其他 | kimsoong（clip-path `inset(...)`）、kubernetes（marker 颜色）、lin_huiyin_architect（theme 契约缺 font_family 等）、pritzker（**回填 flat 后 page_layouts 节与 flat 冲突**——此例应为 structured 或删节，特例待决） | 各例单独处理 |

**决策遗留**：B-F 类需逐个修复（选项 B），或调整 CI 门禁（选项 C，不推荐），或暂缓（push 前必须解决）。pritzker 特例需单独判断（回填 flat 是否语义正确）。

5. ✅ **L1 机械层修复执行（2026-08-03 晚）**：A 类 162 SVG 补 width/height（8 示例）+ 4 个 spec_lock 契约行（typography title/body、font_family 族，映射自 legacy 行名）+ doctor 2 个 WEBP 伪装图片转真格式 + kubernetes marker 按色拆分。**绿数 0 → 10/29**。
6. ✅ **L2/L3 修复执行（2026-08-03 晚）**：L3 语义层删 4 个 legacy `page_layouts` 节（structured 专属契约，消费方有容错）；L2 设计层——B 类 6 示例 line→rect 等值转换（userSpaceOnUse 被 checker 明令禁止）、C 类 emoji 合法 Unicode 替换（✓→√ 等 7 映射）、D 类 `<g>` filter 移背景 rect/单图内层 g、E 类 kimsoong `inset()` → 本地 clipPath；补 liziqi/lin_huiyin typography title 行与 page_rhythm 节。**最终：checker 29/29 全绿**；导出抽查 5 个重度修改示例 rc=0；e2e 全量 24/29。
7. ✅ **e2e 5 个既有资产缺口 — 已修复（2026-08-03，用户批准「删声明」）**：deepseek/doctor/kaltsit 删 spec_lock `images` 过期声明（7+20+6 条）；arknights/kaltsit 按 design_spec 页序重编号 15 个 svg（`02_chapter_*`/`03_content_*`/`03a_content_*` → 唯一数字前缀，03a 前缀原不被 `normalize_svg_page_id` 识别）；kimsoong 10 个 `slide_NN` → `NN` 数字前缀。**最终：checker 29/29 + e2e 29/29 双门全绿**；改名示例导出 rc=0 抽查通过。

4. ✅ **连带缺陷修复（spec_lock_validate mode 跨节误读）**：回填暴露 `spec_lock_validate.py` 全局搜索 `- mode:` 行，把 `## pptx_structure` 的 `- mode: flat` 误读为叙事模式（模板顺序 pptx_structure 在 mode 之前，所有新项目均受影响，系统性 `Unusual mode value: flat` WARN）——已修复为限定 `## mode` 节内读取；smoke 156/0/4 回归通过；legacy 示例的「缺必需节 FAIL」为既有状态（迁移后新契约，非本批引入）。

## 4. 附注

- `.tmp/` 存在既往会话残留目录 `_agent_page_expression_ab_20260718`、`_agent_page_expression_phase2_20260719`（非本会话创建，未动；按 agent-governance §5 报告，待用户确认后清理）。
- 本报告测量过程在 `examples/` 产生的临时导出文件已删除；`examples/` 未被修改。
