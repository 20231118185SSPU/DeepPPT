# .align/lessons.md — 经验规则

> 初始为空。由沉淀门（门 5）在踩坑/纠正/新约定/推翻假设时自动追加。
> 格式：`- [场景/触发条件] 规则：xxx → 下次执行：xxx`
> 每条 ≤2 行，超 50 条归档。

---

## 经验规则

- [heredoc 写 Python 源码] 规则：bash heredoc 内嵌 Python 字符串拼接写文件时 `\n` 转义链易碎（实际写入换行导致 SyntaxError）→ 下次执行：改用 Write/Edit 工具写代码文件，或写入后用 py_compile 立即验证。
- [上游严格校验器 vs 本仓导出器契约] 规则：ppt 的 validate_generated_animation_xml 要求动画目标为文本承载 p:sp 且 effect options 可解析，DeepPPT2 的组动画（grpSp）必然触发 ValueError → 下次执行：先探测校验器对真实产物的行为，再决定 trace 数据来源；配置派生回退（同源 seq_targets）保证一致性。
- [trace 路径与旗标] 规则：DeepPPT2 的 conversion trace 需 `--conversion-trace` 旗标且路径为 `<输出>.pptx.trace.json`（非 validation/）→ 下次执行：断言前先核对 CLI 旗标与输出位置。
- [motion plan 结构] 规则：video_motion_plan 的产物是 `slides[].objects[].video`，不是 `slides[].video` → 下次执行：断言前先 dump 实际结构。
- [PowerPoint COM 真实可用] 规则：本机 Office 16.0 存在，powerpoint_video --check 返回可用、真实导出成功 → 下次执行：视频相关验证可直接在本机做真实编码，不限于静态检查。
- [拷贝丢装饰器] 规则：整文件拷贝可能丢装饰器行（template_preview_pptx 的 `_review_svg_sources` 缺 `@contextlib.contextmanager`，import 通过但 `with` 崩）→ 下次执行：工具迁移后跑真实 e2e 而非只 import，或 diff 时核对 def 上方装饰器。
- [工具脚本 import 闭包含包内新模块] 规则：工具脚本（shape_boolean_svg）依赖 `svg_to_pptx.shape_boolean`——ppt 重构包 drawingml 的模块，DeepPPT2 只有 pre-refactor flat 版，ast 符号面 diff 显示 102/14 个缺失符号 → 下次执行：迁移评估先跑 ast 符号面 diff（几秒出结论）；拖入重构的按回退条款：优雅降级信息 + 文档标注，不强行改装导出器。
- [compact 工具属性集] 规则：compact_svg_coordinates 只压缩 `data-pptx-frame`/`data-pptx-bounds`/`transform` 属性，不碰 x/y/width/height 与 path data → 下次执行：fixture 按工具契约构造，别用通用坐标。
- [selector 元素类型与资源存在性] 规则：extract_svg_pictures 的 `--select` 必须命中 `<g>` 元素（非 `<image>`），且引用的图片文件必须真实存在 → 下次执行：先建真实资源再跑工具，报错先看 stderr 的语义提示。
- [入口吞退出码] 规则：CLI 包装脚本若 `main()` 裸调用（不 `raise SystemExit(main())`），所有错误路径静默 rc=0，CI/调用方无法感知失败 → 下次执行：复盘时对每个入口脚本做「错误路径 rc 探测」（传坏参数断言 rc≠0），比读代码快。
- [路由先行文件后补] 规则：Phase 2 重构时 routing.md 已写入 quick-generate 触发行但 profile 文件与 CLI flag 从未迁移——悬空引用在链接检查里不报（文件级检查只查 `](...)` 目标存在性）→ 下次执行：路由表每行的目标文件逐一 `ls` 核验存在，不能只跑链接解析。
- [链接检查的排除分类] 规则：全仓链接扫描的 broken 需按「真断链 / 代码块示例（xxx.md、url）/ 用户项目导入材料（projects/*/sources/）」三分类，直接改会误伤示例与用户内容 → 下次执行：扫描结果先分类再动手；fenced code block 内的链接不算。
- [gate 清单按入口补] 规则：attribution_guard 的 _REQUIRED_GATE_FILES 每阶段按「关键入口脚本」追加（Phase 5 补 preset_shape_svg/template_preview_pptx），工具类脚本不进清单 → 下次执行：阶段收尾时对照新增脚本清单与 gate 清单。
- [整套导出器替换的调用面清单] 规则：包整体替换时，真实 import 消费者比想象少（DeepPPT2 仅 9 个顶层脚本），但每个的符号面要逐一核对（20 个符号全在新包后适配退化为纯路径替换）→ 下次执行：先跑「消费者 × 符号」矩阵核对，再决定改 import 还是改实现。
- [新契约测试项目要补全] 规则：重构版导出器要求 spec_lock 完整主题契约（canvas/typography/colors/pptx_structure.mode），verify 脚本的 _smoke_ 项目没有 → 报错信息本身就是契约清单（"missing: typography font_family/title_family/body_family, colors"）→ 下次执行：脚本项目创建时直接写完整 lock 模板。
- [trace 路径契约变化] 规则：新 CLI 的 --conversion-trace 纯 flag 写 validation/<stem>.trace.json（旧版写 pptx 旁 <pptx>.trace.json）→ 下次执行：断言 trace 前先看 CLI 的默认路径分支，或显式传路径。
- [--recorded-narration 依赖 narration_animations.json] 规则：新 CLI 的二次导出默认期望项目根 narration_animation.sjson（narration_sync animations 产物）→ 下次执行：narration_sync animations 输出到项目根（新 CLI 默认查找位置）。
- [checker 横幅文本差异] 规则：新 checker 的 --quick-generate 是行为式（无"Quick Generate"横幅），verify 断言 stdout 文本会脆 → 下次执行：断言用产物文件存在性（validation/svg_quality_report.json）而非横幅。
- [preview 工具是 structured 导向] 规则：template_preview_pptx（ppt 原版）要求 SVG 根 data-pptx-master（structured 预览），普通 fixture 需 --visual-only → 下次执行：模板预览验证用 --visual-only 或构造 structured fixture。
- [svg_finalize 与导出器配套升级] 规则：新导出器的 tspan_flattener 调用 svg_finalize.flatten_text_with_tspans(preserve_line_breaks=...)——包替换牵出 svg_finalize 全套（7 模块全 DIFFER）→ 下次执行：替换包后先跑真实导出（TypeError 会暴露配套模块），再逐模块核对调用面。
- [spec_lock 主题契约是新导出器硬门] 规则：flat 导出也要求 spec_lock 的 font_family/title_family/body_family + colors + pptx_structure.mode（DeepPPT2 模板恰好都有）→ 下次执行：手写测试 lock 用模板字段，别写最小子集。
- [git quotepath 与路径集合比对] 规则：`git ls-files` 默认把非 ASCII 路径转义为八进制（core.quotepath=true，336 个中文名文件），与 os.walk 的 Unicode 路径比对全部失配 → 下次执行：路径集合比对统一用 `git ls-files -z`（NUL 分隔、不转义）。
- [Windows Git Bash 无 /usr/bin/time] 规则：Git Bash 缺 `/usr/bin/time`，`time -f` 不可用 → 下次执行：计时用 Python `time.perf_counter()` 包 subprocess，或直接 python -c 内计时。
- [盘点/审计/契约文档惯例] 规则：`plans/` 与 `docs/reviews/` 新增文档不进 `docs/change-log.md`（change-log 只记脚本/工作流/路由变更，既有两篇审计均无条目）→ 下次执行：新增计划/审计/契约文档按 documentation-style.md 声明状态与权威性即可，变更记录留给脚本/工作流改动。
- [双名副本合并方向] 规则：同内容双名副本（md5 相同）合并时保留与上游同名文件、改少侧消费点 import（native 侧 3 处）、同步 attribution_guard 清单与文档提及，导出器侧零改动 → 下次执行：合并前出消费者×符号矩阵，执行后 smoke（预期 checks -2/文件）+ guard 双验证，change-log 记录「-2 checks 为被删脚本的 import+help」。另注：docs/change-log.md 现为顶部倒序插入（Phase 6/quick/Phase 5 均在 Log 区顶部）。
- [shell 命令替换吞退出码] 规则：`echo "$(basename $d): rc=$?"` 中 `$?` 在命令替换求值之后才取，反映的是 basename 的 rc（恒 0），循环扫描全变全绿假象 → 下次执行：先 `rc=$?` 存入变量，再拼 echo。
- [warm 调用 CLI main 需捕获 SystemExit] 规则：入口脚本 main() 会 `sys.exit(N)`（如 svg_quality/cli 任何 ERROR → exit 1），同进程 warm 测量/调用不 catch 会中断测量脚本 → 下次执行：性能 warm 测量统一 `try: main() except SystemExit: pass`，只计时。
- [行插入式修复的死循环] 规则：遍历 lines 时 `insert` 新行（如内层 `<g filter>`）会被 while/for 后续迭代再次匹配正则，无限嵌套直到超时 → 下次执行：批量修复用「单遍收集 + 重建列表」（while + 显式 i 步进），插入内容显式跳过；写完先跑 dry-run 验证幂等。
- [emoji 禁区合法替代] 规则：checker `_EMOJI_RE` 禁 2600-26FF / 2700-27BF / 1Fxxx / FE00-FE0F → 下次执行：✓→√、✕→×、✦→◇、★→◆、⚠→!、⚡→▶、💡→!（U+221A/00D7/25C6/25C7/0021/25B6 均合法）。
- [checker 与 e2e 契约面不同] 规则：checker 查 spec_lock mode + SVG 语法；e2e 查 page_rhythm 页数、images 声明存在性、svg 命名模式（P NN）→ legacy 示例可能 checker 全绿但 e2e 红（声明与磁盘漂移、命名不兼容）→ 下次执行：示例全量验收同时跑 checker + e2e 双门。
- [懒加载负优化陷阱] 规则：把模块级 eager import 改函数内懒加载，若使用函数每次运行必达（checker 每页都跑检查），重依赖（openpyxl ~600ms）只是从启动移到检查时，总耗时不变甚至更差（实测 +25%）→ 下次执行：懒加载前先确认使用路径是否每次必达；用「完整运行 p50」而非「import 耗时」做前后对比。
- [性能对比的 fixture 一致性] 规则：前后 p50 对比必须同一 fixture（kubernetes 副本 vs swiss 原位检查内容不同，差 ~300ms）→ 下次执行：基线 fixture 保留到优化批次结束，不要中途清理。
- [prompt_audit load-set selector 契约] 规则：manifest 的 load_sets.files 里 glob 条目必须带 `select`（1..N 的按需加载模型，缺 select 报 `AUDIT_SETUP_ERROR: invalid select=None`）→ 下次执行：glob 条目一律补 select（字符串路径是固定加载，无需 select）。
- [BUDGET_CORPUS 不受 exempt 影响] 规则：coverage.exempt 只豁免「覆盖率」要求，豁免文档仍计入 corpus tokens，压不动 BUDGET_CORPUS → 下次执行：corpus 超预算只能提高 max_tokens（须配真实 load-set 设计）或收窄 documents.include，别指望 exempt。
- [prompt_audit --json 输出键名] 规则：duplicates 输出键是 exact/exact_accepted/near/near_accepted（非 open/accepted），load_sets 是数组非字典 → 下次执行：解析输出先看顶层键再写解析器。
- [管道吞退出码] 规则：`cmd | tail; echo EXIT=$?` 取到的是 tail 的退出码，误记门禁 PASS/FAIL → 下次执行：重定向到文件（`cmd > f; echo $?`）再取退出码。
- [双门禁对同一字段语义冲突] 规则：spec_lock_validate 与 svg_quality_checker 对 flat 模式 `page_layouts` 一强制存在一禁止存在 → 下次执行：改共享契约前先 grep 所有消费方对同一字段的断言方向，修成模式感知而非单侧让步。
- [子串匹配误伤] 规则：拉丁词条子串匹配会命中普通单词（"ip" ⊂ "discipline"），CJK 多字符词无此问题 → 下次执行：拉丁词条一律 `\b…\b` 词边界，CJK 保持子串。
- [全局 font-size 串扰] 规则：宽度估计取页面首个 font-size，150px 装饰数字污染所有估计 → 下次执行：估计宽度用元素自身 font-size。
- [docx 摊平表格不可作权威] 规则：mammoth 摊平合并单元格表格（vMerge 全续行成幻影行、gridSpan 列丢失），且圈号码位是 `<w:sym>`（Wingdings 2 F06A–F073 / Wingdings F081–F08A 双字体）非 w:t → 下次执行：表格链路以 docx XML 直接解析为权威，摊平文本仅辅助；复核对账在图表完成后必须做一次。
- [vMerge 语义] 规则：vMerge 重启格（无 w:vMerge 属性）拥有内容；续行（val=continue）为幻影行跳过，部分续列才重复重启格文本 → 下次执行：恢复合并单元格表格时先列语义分支再实现。
- [断言契约精确 id] 规则：检查器认顶层组 id 精确 `lead`/`subtitle`，变体（lead-assertion）报 role-missing；断言必须等于单个 `<text>` 整句，跨兄弟元素报 not-editable → 下次执行：先读 spec_compliance_check.py 的检查名再写 executor 文档，别凭示意图命名。
- [字形盒 vs 行盒] 规则：getBoundingClientRect/行盒会高估文字范围（含行距），字形交叠判定须用 baseline±(0.78,0.22)×fs 的字形盒交集 → 下次执行：几何审计用字形盒模型，检测器报警默认信真、用源码坐标二次验证而非视觉模型否决。
- [tspan dy 累积语义] 规则：SVG tspan 的 dy 相对上一行 baseline（累积），非相对 text 根；行解析错误会把整组行误算到同一 y 产生假交叠 → 下次执行：解析 tspan 行时维护游标 y += dy。
- [后绘 rect 覆盖先绘文字] 规则：文档顺序即 z-order；填充 rect 出现在 text 之后且相交 = 遮挡（P11 卡片遮断言、P13 断言条切面板）→ 下次执行：审计工具检查"rect.doc_order > text.doc_order 且相交"。
- [PowerPoint 渲染是最终真相] 规则：Chromium 与 PowerPoint 字体度量不同（雅黑行高/字宽 headroom），浏览器预览差 2px 的地方 PowerPoint 可能肉眼可见重叠 → 下次执行：版式复核以 pptx_render_export.py 的 Slide.Export PNG 为基准，几何审计只作第一道防线。
- [视觉模型 OCR 连读掩盖遮挡] 规则：两行文字重叠时视觉模型常 OCR 成一行（P07 下一步×来源重叠 34.5px 被连读）→ 下次执行：把视觉模型 OCR 与源码 text 内容 diff，缺失/合并行本身就是遮挡信号。
- [新顶层脚本自动进 smoke] 规则：smoke_check 自动 glob scripts/*.py 做 import+--help 覆盖，新 CLI 只需满足"模块级 import 无副作用 + --help 15s 内 exit 0" → 下次执行：新增工具后跑 smoke 确认 checks 数 +2/脚本。
- [PowerShell 字符串勿用 .format] 规则：PowerShell 脚本含 {0:D2} 等格式符，与 str.format 冲突且反斜杠不需转义 → 下次执行：COM 自动化脚本用占位符 replace 而非 format，路径直接传原样。
- [native_enhance init 项目落点] 规则：`native_enhance_pptx.py init` 默认把项目建到 `projects/`（非临时区），需 `--project-dir` 显式指到 .tmp → 下次执行：fixture/临时验证一律传 `--project-dir`，误建即删（`projects/` 只留真实用户项目）。
- [enhance plan JSON 是字典] 规则：enhancement_plan.json 的 `modules` 是 dict 非 list，`modules.audio.enabled=false` 才是关闭键位；用 list 遍历关闭会静默无效 → 下次执行：改 plan 前先 dump 顶层键结构。
- [fixture 网格合法性] 规则：DOCX tblGrid 列数必须 ≥ 行内全部 tc 的 gridSpan 之和（3 列 + span2 + 1 tc = 4 列不合法）；恢复逻辑对超宽行截断是正确行为，先验 fixture 再判工具缺陷 → 下次执行：构造合并表格 fixture 时先算列账，把超宽当"修复"前先自查 fixture。
- [finally 内 import 的函数级作用域] 规则：函数内 `finally: import shutil` 会把 shutil 提升为整个函数的局部名，函数体任何提前引用都 UnboundLocalError → 下次执行：函数内 import 前先确认作用域，或提到函数顶部/模块顶部。
- [普通字符串的 {{ 转义] 规则：非 f-string 模板字符串里写 `{{` 会原样保留，拼出的源码 `{{...}}` 解析成「dict 作 key」→ TypeError: unhashable type: 'dict'（Test 7 用 f-string 风格所以 OK）→ 下次执行：.replace 式模板用单括号，只有 f-string 才需要双括号。
- [手写 trace 事件须带 schema_version] 规则：fixture 手造事件缺 schema_version 会被聚合器全量计为 legacy（10/10 误报）；trace_writer 写入时自动补，手写必须显式 → 下次执行：非 legacy 事件一律显式 `"schema_version": 1`，只留目标事件当 legacy 样本。
- [gate_result 重试归组键] 规则：gate_result 事件无 operation 时按 type 归组会让全部 gate 共享 "gate_result" 键、重试计数虚高 → 下次执行：操作键回退顺序 operation → gate → type。
- [step 配对不是重试] 规则：step_start+step_complete 是单次运行两事件，重试统计只数 start 类事件（step_start/gate_result/*attempt*）的重复 → 下次执行：重试指标按 start 类事件计数。
- [duration_ms 0 是实测] 规则：写入方带 duration_ms: 0 的完成事件是真实 0ms 测量，不能被「无 start 无法计算→null」吞掉 → 下次执行：stage 聚合优先保留写入方实测值，null 只表示未测量。
- [spec_lock_digest 消息走 stderr] 规则：verify_digest 的 OK/MISMATCH 输出用 `file=sys.stderr`，只 redirect_stdout 拦不住，CLI JSON 输出被污染 → 下次执行：调用 digest 校验时同时 redirect stdout+stderr（`contextlib.redirect_stderr`）。
- [诊断 fixture 需完整合法上下文] 规则：诊断场景 fixture 必须带合法 spec_lock+digest，否则 SPEC_LOCK_MISSING/DIGEST_MISMATCH 无关 blocker 叠加污染目标场景 → 下次执行：每场景 fixture 只留目标缺陷，其余契约完整（digest 用 generate 生成）。
- [中间态不是 blocker] 规则：svg_final 已存在未导出是正常中间态（status=partial + next=EXPORT_PENDING），不是错误 blocker；blocker 只用于真正卡住/损坏的状态 → 下次执行：诊断 status 语义 = ok/partial/blocked 三档，EXPORT 类下一步归 partial。
- [真实项目 digest 过期是真发现] 规则：gan_hemt 的 spec_lock 在 digest 生成后被修改（verify rc≠0），诊断正确暴露 SPEC_LOCK_DIGEST_MISMATCH——说明 spec_lock 改动后未重跑 digest generate → 下次执行：任何 spec_lock 修改后必须 regenerate digest（.align/spec.md 高风险清单已列，实际又踩一次）。
- [空间分类按文件级规则] 规则：`live_preview/server.log` 等任何 `.log` 文件按后缀归可再生（日志可重生成），与所在目录无关；归档计划 item.class 显示顶层目录名可能误导 → 下次执行：分类标注区分「目录类」与「后缀类」规则来源，或接受日志可再生语义并在文档写明。
- [可再生 ≠ 可删] 规则：space_report 只列可再生候选（backup 309.8 MiB 主导），dry-run 计划仅供用户确认；任何清理命令必须精确路径 + 恢复方式 + 再次确认，禁止 bulk-clean → 下次执行：治理类工具只报告，删除动作永远留给显式授权。
