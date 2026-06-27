# 视频建议实施计划：排版稳定性 + 动画质量 + 场景适配

## Context

B站视频"横评6大PPT开发Skill"中，PPT Master 排版评分 ★★☆、动画评分 ★★☆、发布会场景适配 ★★☆。深入分析发现：

- **svg_quality_checker.py** 有 11+ 项检查，但**完全没有**布局边界检测、文字溢出检测、元素间距检测
- **executor-base.md** 有详细的生成规则（安全边距 50px/40px、垂直分布 3 区域、居中公式），但**没有被自动化验证**
- **customize-animations.md** 已有节奏规划表（anchor/breathing/dense），但 Executor 生成时未强制参照
- **finalize_svg.py** 纯格式兼容管线，**无自动修正**能力

---

## P1: 排版稳定性（最高优先级）

### 1.1 新增 `_check_layout_bounds` 检查（svg_quality_checker.py）

为每个可见元素检查是否超出 viewBox 边界：

```
检查项:
- text 元素: x + 估算文字宽度 > viewBox_width - margin_right → ERROR
- text 元素: x - 估算文字宽度 < margin_left → ERROR
- text 元素: y > viewBox_height - margin_bottom → ERROR
- text 元素: y < margin_top → ERROR
- image 元素: x + width > viewBox_width → ERROR
- rect/g 元素: 超出 viewBox → WARNING
- 所有元素: 右边缘 > viewBox_width + tolerance → WARNING
```

**估算文字宽度方法**: `len(text) * font_size * 0.55`（中文字符 `* 1.0`，拉丁字符 `* 0.55`）
**安全边距**: 从 executor-base.md §14.1 取值（left/right 50px, top/bottom 40px）
**tolerance**: 10px（避免误报）

### 1.2 新增 `_check_element_spacing` 检查（svg_quality_checker.py）

检查相邻元素间最小间距：

```
检查项:
- 同一 y 坐标（±20px）的 text 元素: 水平间距 < 15px → WARNING
- 同一 x 坐标（±20px）的 text 元素: 垂直间距 < font_size * 0.3 → WARNING
- text 与 image 重叠: text 的 bounding box 与 image 的 bounding box 有 >30% 交集 → WARNING
- 卡片/rect 内的 text: text 超出 rect 边界 → ERROR
```

### 1.3 新增 `_check_vertical_distribution` 检查（svg_quality_checker.py）

自动验证 executor-base.md §14.5 的垂直分布规则：

```
- 将 viewBox 高度分为 3 区（top/middle/bottom，各 33%）
- 统计每个区域的可见元素数量/权重
- 任何区域权重 < 15% → WARNING（低于 §14.5 的 20% 要求，留余量）
- 底部 40% 完全空白 → ERROR
```

### 1.4 executor-base.md 新增 §14.6 "Layout Violation Auto-Fix Rules"

在 finalize_svg.py 的 post-processing 中增加自动修正步骤（Step 5）：

```
自动修正规则:
1. 文字溢出: 如果 text x + 估算宽度 > viewBox_width - 50:
   → 将 font-size 缩减 10%（最多缩减 2 次）
   → 如果仍溢出，将 x 向左微调
2. 元素越界: 如果任何元素 y > viewBox_height - 40:
   → 将 y 调整为 viewBox_height - 40
3. 垂直分布失衡: 如果底部 40% 无内容:
   → WARNING（不自动修正，但标记给 Executor）
```

### 文件变更

| 文件 | 变更 |
|------|------|
| `scripts/svg_quality_checker.py` | 新增 3 个检查方法: `_check_layout_bounds`, `_check_element_spacing`, `_check_vertical_distribution` |
| `scripts/finalize_svg.py` | 新增 Step 5: layout auto-fix（文字溢出缩减、元素越界修正） |
| `references/executor-base.md` | 新增 §14.6: Layout Violation Auto-Fix Rules |

---

## P2: 动画质量

### 2.1 executor-base.md 新增 §18 "Animation Rhythm Enforcement"

将 customize-animations.md 的节奏表提升为 Executor 生成时的强制参照：

```
§18.1 — 动画选择规则
- 封面页/结尾页: transition=fade(0.5s), 对象动画=fade(0.6s)
- 目录页: transition=none, 对象动画=fly(0.4s) 逐项进入
- 内容页 (dense): transition=fade(0.25s), 对象动画=auto(0.35s)
- 内容页 (breathing): transition=fade(0.35s), 对象动画=fade(0.5s)
- 深度分析页: transition=fade(0.3s), 对象动画根据布局类型选择:
  - 数据仪表板: wipe(0.4s) 逐组进入
  - 对比分栏: fly(0.4s) 左右分入
  - 时间轴: fly(0.35s) 逐节点进入
  - 全页引述: fade(0.6s) 整体淡入
- 过渡页: transition=fade(0.4s), 对象动画=fade(0.5s)

§18.2 — 禁止规则
- 禁止所有页面使用同一动画方案（"为动画而动画"）
- 禁止内容页使用 zoom/swivel/blinds 等花哨效果
- 禁止动画时长 < 0.15s（太快不可见）
- 禁止动画时长 > 1.0s（太慢拖沓）

§18.3 — 关键数据强调
- 包含数字/KPI 的文本组: 使用 appear(0.3s) 或 fade(0.4s)
- 图表: 使用 wipe(0.5s) 从左到右
- 对比数据: 使用 fly(0.4s) 从两侧进入
```

### 文件变更

| 文件 | 变更 |
|------|------|
| `references/executor-base.md` | 新增 §18: Animation Rhythm Enforcement |

---

## P3: 发布会场景适配

### 3.1 新增发布会品牌预设

创建 `templates/brands/event_presentation/brand_preset.json`：

```json
{
  "name": "Event Presentation",
  "palette": {
    "background": ["#0d1117", "#161b22", "#1c1c2e"],
    "primary": ["#58a6ff", "#388bfd"],
    "accent": ["#f78166", "#d29922"],
    "body_text": ["#c9d1d9", "#8b949e"]
  },
  "typography": {
    "heading": "bold, large (48-72px for titles)",
    "body": "clean, 20-24px"
  },
  "density": "sparse",
  "mood": "dramatic, product-focused, Apple-style"
}
```

### 3.2 Strategist 场景识别规则（SKILL.md Step 4 增强）

在 Eight Confirmations 中增加场景类型判断：

```
当 scenario = "发布会" / "产品发布" / "launch event":
  - 自动推荐 event_presentation 品牌预设
  - page_rhythm: anchor 页面 ≥ 40%, dense ≤ 20%
  - 推荐全屏背景图 + 少量文字的布局模板
  - 图片使用策略: ai 为主（需要高质量产品渲染图）
  - 每页文字量: ≤ 80 字（减少信息密度）
```

### 文件变更

| 文件 | 变更 |
|------|------|
| `templates/brands/event_presentation/brand_preset.json` | 新建发布会品牌预设 |
| `SKILL.md` Step 4 | Strategist 增加场景类型判断规则 |

---

## P4: 视觉关键页混合渲染

### 4.1 Strategist 标记视觉优先页

在 design_spec.md 的 Page Roster 中增加 `visual_priority` 字段：

```
| Page | Type | Visual Priority | Image Source |
|------|------|----------------|-------------|
| P01  | cover | HIGH | ai |
| P04  | content | HIGH | ai |
| P06  | content | normal | web |
| P09  | deep_dive | LOW | none |
```

### 4.2 Executor 视觉优先页规则

在 executor-base.md 新增 §19 "Visual Priority Page Rules":

```
当 visual_priority = HIGH:
  - 必须使用 AI 生成的全屏背景图（通过 image_gen.py）
  - 文字叠加在背景图上，使用半透明遮罩（opacity ≥ 0.85）
  - 文字颜色必须与背景图形成 WCAG 4.5:1 对比度
  - 文字量 ≤ 60 字
  - 动画: fade(0.6s) 整体淡入

当 visual_priority = normal:
  - 标准内容页规则

当 visual_priority = LOW:
  - 可以使用纯色背景 + 文字/数据
  - 动画可以更简洁
```

### 文件变更

| 文件 | 变更 |
|------|------|
| `references/executor-base.md` | 新增 §19: Visual Priority Page Rules |
| `workflows/deep-research.md` Step 7 | visual_strategy.json 增加 visual_priority per page |

---

## 实施顺序

| 阶段 | 内容 | 影响范围 |
|------|------|---------|
| **Phase 1** | P1 排版稳定性（svg_quality_checker.py 新增 3 个检查） | 质量检测脚本 |
| **Phase 2** | P1 自动修正（finalize_svg.py Step 5） | 后处理脚本 |
| **Phase 3** | P2 动画质量（executor-base.md §18） | 参考文档 |
| **Phase 4** | P3 发布会场景（品牌预设 + Strategist 规则） | 模板 + SKILL.md |
| **Phase 5** | P4 视觉关键页（executor-base.md §19） | 参考文档 |

---

## 验证方案

1. **P1 单元测试**: 用一个已知有溢出问题的 SVG 文件运行 `svg_quality_checker.py`，确认新检查能捕获问题
2. **P1 自动修正测试**: 用一个有文字溢出的 SVG 运行 `finalize_svg.py`，确认修正后文字不再溢出
3. **P2 文档验证**: 确认 §18 的节奏表与 customize-animations.md 一致
4. **P3 端到端**: 用发布会场景跑一次完整流程，对比改进前后的排版/动画效果
5. **Smoke check**: `python scripts/smoke_check.py` 无回归
6. **变更日志**: 所有变更记录到 `docs/change-log.md`
