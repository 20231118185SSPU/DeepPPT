# .align/lessons.md — 经验规则

> 初始为空。由沉淀门（门 5）在踩坑/纠正/新约定/推翻假设时自动追加。
> 格式：`- [场景/触发条件] 规则：xxx → 下次执行：xxx`
> 每条 ≤2 行，超 50 条归档。

---

## 经验规则

- [SVG → PPTX 文本边界] 规则：Chromium/SVG 渲染通过不代表 DrawingML 字宽不越界 → 下次执行：导出后运行 `pptx_quality_check.py`，按 DrawingML 实测微调短句或坐标并重新导出。
- [跨 `tspan` 的逐字 assertion] 规则：可见换行可能让 XML 文本拼接丢失语义空格 → 下次执行：用 `&#32;` 保留空格，并用 XML 解析器对 JSON 原文做标准化精确比对。
- [Windows watcher 回归] 规则：文本写回可能把 `page_expression.json` 的 LF 转成 CRLF，造成真实 digest drift → 下次执行：watcher fixture 用字节级恢复，合同文件保持 UTF-8/LF 后再封存。
- [SVG assertion 可见性] 规则：隐藏 descendant、透明 paint 或 tspan 字号覆盖都不能算可见 assertion → 下次执行：按可见文本 run 解析 XML，并检查每个 run 的有效字号。
- [条件工作流合同] 规则：总编排器声明可选能力不等于执行步骤已落地 → 下次执行：统一 `enabled/reason/source` 路由回执，并在 owning step 中规定产出与验证。
- [新机器 sidecar 合同] 规则：新增必需产物不能只接入连续生成路径 → 下次执行：同步检查连续、split handoff、resume 与 refine 的全生命周期。
- [研究正文深度门] 规则：机器注释和结构化 sidecar 不能贡献可读正文字数 → 下次执行：计数前先剔除机器注释块，并用短正文反例验证。
