# .align/lessons.md — 经验规则

> 初始为空。由沉淀门（门 5）在踩坑/纠正/新约定/推翻假设时自动追加。
> 格式：`- [场景/触发条件] 规则：xxx → 下次执行：xxx`
> 每条 ≤2 行，超 50 条归档。

---

## 经验规则

- [研究正文深度门] 规则：机器注释和结构化 sidecar 不能贡献可读正文字数 → 下次执行：计数前先剔除机器注释块，并用短正文反例验证。
- [上游同源 UI 迁移] 规则：确认目标文件与上游同源时，整份替换新代实现后必须重新叠加本仓库独有扩展，并逐项核对扩展的潜伏缺陷 → 下次执行：替换前先 grep 扩展依赖的常量/路由是否在新文件中有定义（如 `_SKILL_DIR` 未定义）。
- [跨仓库文件拷贝] 规则：`cp` 整目录后 diff 校验 + 运行 smoke 建立新基线 → 下次执行：先基线后改、改后对比通过数（52→55 确认新增脚本被覆盖）。
- [同秒写入的门禁新鲜度] 规则：`confirmed_at` 为秒级精度而文件 mtime 含亚秒，同秒写入会被误判为过期 → 下次执行：测试驱动在关键写入间留 ≥1.1s，或比对时先截断 mtime 到秒。
- [uv 托管 Python 禁 pip] 规则：uv 管理的解释器是 externally-managed，`pip install`/`uv pip install` 均拒绝（需 venv）→ 下次执行：可选依赖不硬装，按上游同样处理（可选标注），不要在用户环境强装。
- [文档搬迁链接失效] 规则：把 SKILL.md 的段落搬入 workflows/ 子目录时，裸 `references/`、`scripts/`、`templates/`、`../../docs/` 相对链接全部失效 → 下次执行：搬迁后立即跑全仓 markdown 链接解析校验（正则提取 `](...)` 逐一 resolve），先修再收工。
- [sed 链接重写顺序] 规则：先改目标文档自身的链接（如 generate-pptx.md 内 workflows/→stages/），再做全仓 sed，避免双重替换 → 下次执行：重写规则按「自内向外」排序，并 grep 校验 `stages/stages` 之类双前缀。
- [Windows 日志锁] 规则：dashboard 守护进程持有 dashboard.log，--shutdown 后需等待 1-2s 才能删除项目目录 → 下次执行：_smoke_ 清理前先 /api/shutdown + sleep + 再 rmtree。
- [Windows 目录句柄] 规则：Bash 会话 cwd 停留在目标目录（或 ffmpeg/ffprobe 子进程句柄）会让 rmtree 报 WinError 32 → 下次执行：先 cd 离开 + taskkill 媒体进程，仍锁则用 PowerShell Remove-Item -Force。
- [哑音频会误导导出验证] 规则：`--recorded-narration` 会用 ffprobe 校验 MPEG 帧，伪造字节音频被正确拦截（校验本身有效）→ 下次执行：音频契约测试必须用 `ffmpeg -f lavfi -i anullsrc...` 生成合法静音 mp3。
- [notes 命名宽度继承 SVG 文件名] 规则：total_md_split 按 SVG stem 命名（01.svg→01.md，001.svg→001.md），非固定三位 → 下次执行：断言前先确认 fixture 的 SVG 命名宽度；native_enhance `_audio_path` 接受 001/01/1/slide001 全部宽度。
- [同血缘模块替换判断] 规则：上游重构模块（如 pptx_animations 3932 行新版）与被本仓导出器消费的旧版 API 不兼容时，不可整体替换 → 下次执行：以新模块名引入（native_pptx_animations.py）+ 改导入点，导出器零改动。
- [函数参数化路由差异] 规则：同一 XML 生成函数被两条路由消费但契约不同（Generate 无 notesMaster 部件 vs Enhance 有）→ 下次执行：加默认 False 的参数而非复制函数，Generate 默认路径输出保持不变（用断言验证两模式）。
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
