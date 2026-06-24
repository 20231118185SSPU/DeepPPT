# Skill 对齐审计报告

**日期**: 2026-06-25
**审计对象**: `~/.claude/skills/ppt-deep-research/SKILL.md`（545 行 → 修补后 ~600 行）
**权威源基准**: 8 个文件（SKILL.md, deep-research.md, strategist.md, executor-base.md, image-generator.md, image-searcher.md, design_spec_reference.md, .env.example）

## 差异摘要

| 级别 | 数量 |
|------|------|
| 关键（流程断裂） | 3 |
| 重要（规则缺失） | 5 |
| 轻微（措辞/格式） | 2 |
| **总差异** | **10** |
| 一致（无需修改） | 2（保存路径、八项确认） |

## 决策：结构保留 + 大段重写（6 处编辑）

skill 的 8 步骨架、视觉身份提取（Step 5）、双轨图片策略（Step 7）、讲解页排版规范、story_driven 模板页面类型库等核心差异化内容与权威源一致，无需重写。

## 变更清单

| # | 维度 | 差异描述 | 权威源 | 类型 | 处理方式 |
|---|------|---------|--------|------|---------|
| 1 | 保存路径 | `sources/research_report.md` — 一致 | deep-research.md §4.6 | ✅ 一致 | 无需修改 |
| 2 | 显式 init | Step 1 无 `project_manager.py init` 命令 | deep-research.md §1.1 | **缺失/关键** | ✅ 新增 §1.1 段落 |
| 3 | Agent-Reach | 无 B站/V2EX/RSS/YouTube/Jina 采集 | deep-research.md §2.2a | **缺失/重要** | ✅ 新增到 Step 2 |
| 4 | 素材来源适配 | 无按主题类型选源表 + 无 svg-native | deep-research.md §2.4 | **缺失/重要** | ✅ 新增到 Step 2 降级策略 |
| 5 | 降级链 | 三轨制缺第④级 svg-native | deep-research.md §4.3 | **过时/重要** | ✅ 更新为四轨制 |
| 6 | 质量门控 | 无叙事深度自检报告 checklist | deep-research.md §4.7 | **缺失/重要** | ✅ 新增 §4.7 |
| 7 | 亮色适配 | 无亮色主题适配清单 | deep-research.md §4.3 | **缺失/重要** | ✅ 新增到 Step 8.1 |
| 8 | 僵尸清理 | 无导出后清理规则 | deep-research.md §4.3 | **缺失/轻微** | ✅ 新增到 Step 8.4 |
| 9 | §3 最低产出 | 已包含全部 5 项 — 与 deep-research.md §3.4 一致 | deep-research.md §3.4 | ✅ 一致 | 无需修改 |
| 10 | 八项确认 | 完整 Confirm UI 流程 — 与 SKILL.md Step 4 一致 | SKILL.md Step 4 | ✅ 一致 | 无需修改 |

## 验证

- [x] 每条编辑可追溯到 deep-research.md 具体章节
- [x] 新增段落均标记 `> **2026-06-24 同步更新** — 来源：...`
- [x] 未删除任何现有内容
- [x] skill 现有的差异化内容（视觉身份提取、双轨图片、讲解页排版、模板页面类型库）未被覆盖
