# .align/context.md — 项目上下文契约

> 由 `align-init` skill 扫描生成。

---

## 项目目标与当前阶段

- 项目目标：AI 驱动的演示文稿生成系统，将源文档（PDF/DOCX/URL/Markdown）转换为可原生编辑的 PPTX，使用真实 PowerPoint 形状（DrawingML）`[原文]`
- 当前阶段：活跃开发中，核心流水线已稳定（Source → Project → Template → Strategist → Image_Generator → Executor → Quality Check → Post-process → Export）`[推断]`
- 多角色协作：Strategist → Image_Generator → Executor `[原文]`

---

## 共享术语

- "Project"：一个 PPT 生成项目，包含 sources/、images/、svg_output/、exports/ 等目录 `[原文]`
- "spec_lock.md"：机器可读的执行契约，Executor 每页生成前必须重新读取 `[原文]`
- "design_spec.md"：人类可读的设计规范，包含八项确认结果 `[原文]`
- "Eight Confirmations"：Step 4 的核心确认点（画布、页数、受众、风格、配色、图标、排版、图片）`[原文]`
- "Quality Gate"：质量门，包括 svg_quality_checker、spec_compliance_check、harness_gate、rendered_layout_check `[原文]`
- "Dashboard"：只读统一仪表盘，提供项目状态、预览、确认桥接 `[原文]`
- "Confirm UI"：Step 4 八项确认的交互式可视化页面 `[原文]`
- "Live Preview"：Step 6 浏览器内实时预览编辑器 `[原文]`

---

## 架构关键决策

- SVG 必须手写，禁止脚本批量生成
  原因：跨页视觉一致性依赖逐页创作时的完整上游上下文
  影响：Executor Step 6 逐页顺序生成，禁止子代理委托 `[原文]`

- 仓库不包含自动化测试
  原因：项目性质为工作流/技能包，非应用脚手架
  影响：验证通过 smoke_check、harness_gate、e2e_validate 完成 `[原文]`

- scripts/ 不是 Python 包
  原因：扁平脚本目录结构，每个入口脚本自行注入 sys.path
  影响：新脚本需在入口处 `sys.path.insert(0, ...)` 并用 `# noqa: E402` 标注 `[原文]`

- 临时文件使用 gitignored 目录
  原因：projects/ 是用户工作区，非通用临时目录
  影响：开发实验用 `.tmp/` 或 `projects/_smoke_*` 前缀 `[原文]`
