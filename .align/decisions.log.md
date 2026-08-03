# .align/decisions.log.md — 重大决策日志

> 初始为空。由沉淀门（门 5）在高风险决策确认/架构决策/权限决策时自动追加。
> 格式：`- [决策类型] 决策内容：xxx / 影响：xxx / 依据：xxx / 日期：yyyy-mm-dd`
> 每条 ≤5 行，超 100 条归档。

---

## 决策记录

- [架构决策] 动画双文件合并方案 A：删 `native_pptx_animations.py`（与 `pptx_animations.py` md5 相同 145,406B），native 侧 3 处 import 切 `from pptx_animations import`，attribution_guard 清单与 README/文档同步 / 影响：smoke -2 checks（被删脚本的 import+help），导出器侧零改动 / 依据：消费者×符号矩阵 15 符号全兼容、用户批准 / 日期：2026-08-03
- [架构决策] `.align/spec.md` + `context.md` 事实刷新：CI 存在性、smoke 基线 78/0/3 + 158/0/4、Python 3.12.13 实测 / 影响：后续模型不再误判「无 CI/无测试」 / 依据：盘点报告 §5 漂移清单、align-check.sh 一键验证通过 / 日期：2026-08-03
- [架构决策] examples 质量门修复（CI 风险处置）：模板 `- mode: flat` bug 修复 + 29 个 legacy spec_lock 回填 + L1-L3 机械/语义层修复 + e2e 声明删除与 svg 重编号 / 影响：checker 29/29 + e2e 29/29 双门全绿，CI #12/#13 全绿 / 依据：perf-baseline §3 事实链、用户批准（「继续，删申明」）/ 日期：2026-08-03
- [权限决策] Phase 4 产物治理：`projects/README.md` Lifecycle Governance（active/archive/disposable）+ 清理 34 个旧 backup 快照（~0.9GB，project_manager.py:299 官方标注 safe to delete）+ `.codex` dashboard 缓存（256MB→5KB） / 影响：projects/ 5.73GB→4.8GB、.codex 261MB→5KB / 依据：用户批准、官方标注 + 清单 + 回滚边界 / 日期：2026-08-03
- [架构决策] Dashboard 重定位为产物展台：默认路由产物、四阶段导航（制作思路/设计契约/生成页面/导出成品）、research 类型、`artifacts_index.json` 落盘 / 影响：Dashboard = 在线观看平台（思路+产物），Confirm UI 与质量门不动 / 依据：用户指示定位、浏览器实测 + smoke 77/0/3 / 日期：2026-08-03
- [权限决策] GitHub Pages workflow 精简：删除 `static.yml` + `jekyll-gh-pages.yml`，仅保留 `deploy-pages.yml` / 影响：Pages 部署单一入口，站点生效 / 依据：用户批准删除 / 日期：2026-08-03
- [权限决策] README 全面刷新并 push 同步远程：CI badge、v4.3.0 迁移完成内容、Dashboard 展示定位、结构树、changelog 条目 / 影响：仓库介绍与远程同步 / 依据：用户要求 / 日期：2026-08-03
- [契约决策] prompt audit manifest 重写：7 个真实 load_sets（按 SKILL.md 加载纪律与四路由归属 + glob `select` 按需语义）、1 个 exempt（NOTICE.md）、22 个 exact 重复 accepted（模板族共享契约/自动生成头）、corpus max_tokens 400k→430k、generate 预算 190k / 影响：audit rc=0 / errors=0 / coverage 172 闭合（171 covered + 1 exempt）；未 commit（待用户批准） / 依据：BUDGET_CORPUS 无法经 exempt 降低，提 max_tokens 为真实 load-set 设计配套而非掩盖 / 日期：2026-08-03
