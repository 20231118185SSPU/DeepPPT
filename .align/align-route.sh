#!/usr/bin/env bash
# .align/align-route.sh — Alignment Protocol signal-scoring router
# 由 align-init skill 生成（hook 源文件未随 skill 分发时按 SKILL.md 行为规范重建）。
#
# 用法：
#   hook 模式（默认）：从 stdin 读取 UserPromptSubmit 输入，输出路由提示
#   --classify "文本"：输出 VAGUE | CLEAR | HIGHRISK
set -u

if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
  ALIGN_DIR="$CLAUDE_PROJECT_DIR/.align"
else
  ALIGN_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
fi
ALIGN_DIR="${ALIGN_DIR:-.align}"

# 高风险信号：破坏性 / 不可逆 / 影响外部状态
HR_PATTERN='rm[[:space:]]+-rf|rm[[:space:]]+-r[[:space:]]+[^-]|git[[:space:]]+reset[[:space:]]+--hard|git[[:space:]]+push[[:space:]]+(-f|--force)|git[[:space:]]+push[[:space:]]+.*--no-verify|git[[:space:]]+commit[[:space:]]+.*--no-verify|git[[:space:]]+clean[[:space:]]+-fd|git[[:space:]]+checkout[[:space:]]+--[[:space:]]+\.|force[[:space:]]*-?[[:space:]]*push|--no-verify|deploy|生产环境|生产部署|DROP[[:space:]]+TABLE|删库|truncate[[:space:]]+table|\.env[[:space:]"]|credentials'

# 模糊信号：仅有动作动词、无具体目标
VAGUE_PATTERN='优化|改进|完善|整理|看看|检查一下|弄一下|搞一下|美化|调整一下|改改|review$|review[[:space:]]+it|improve$|improve[[:space:]]+it|make[[:space:]]+it[[:space:]]+better|look[[:space:]]+at[[:space:]]+it|check[[:space:]]+it'

# 具体目标信号：文件路径 / 行号 / 符号 / 引用
TARGET_PATTERN='\.[a-z0-9]+\b|:[0-9]|第[0-9]+行|line[[:space:]]+[0-9]|def[[:space:]]|class[[:space:]]|function[[:space:]]|`[^`]+`|"[^"]+"'

classify() {
  local p="$1"
  # 1. 高风险优先
  if printf '%s' "$p" | grep -qiE "$HR_PATTERN"; then
    printf 'HIGHRISK'; return
  fi
  # 2. 有具体目标 → 非模糊
  if printf '%s' "$p" | grep -qiE "$TARGET_PATTERN"; then
    printf 'CLEAR'; return
  fi
  # 3. 短且仅动作动词 → 模糊
  local len=${#p}
  if [ "$len" -lt 40 ] && printf '%s' "$p" | grep -qiE "$VAGUE_PATTERN"; then
    printf 'VAGUE'; return
  fi
  printf 'CLEAR'
}

# --- classify 模式 ---
if [ "${1:-}" = "--classify" ] && [ $# -ge 2 ]; then
  classify "$2"
  printf '\n'
  exit 0
fi

# --- hook 模式：读取 stdin，分类，输出路由提示 ---
raw="$(cat 2>/dev/null || true)"
label="$(classify "$raw")"

case "$label" in
  VAGUE)
    echo "[Alignment Route=VAGUE] 需求模糊。先读 .align/lessons.md → spec.md → context.md，一次只问一个问题（附推荐答案），勿直接执行。"
    ;;
  HIGHRISK)
    echo "[Alignment Route=HIGHRISK] 命中高风险信号。先输出方案 + 影响面，等用户确认；禁止静默假设。红线：高风险静默假设 = 无效输出。"
    ;;
  CLEAR)
    echo "[Alignment Route=CLEAR] 可直接执行。交付前必须自验证（bash .align/align-check.sh / .align/check-commands.txt）。"
    ;;
esac
exit 0
