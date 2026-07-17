#!/usr/bin/env bash
# .align/align-check.sh — 一键交付验证 + 债务台账
# 读取 .align/check-commands.txt，逐行执行，报告通过/失败。
set -u

if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
  ALIGN_DIR="$CLAUDE_PROJECT_DIR/.align"
else
  ALIGN_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
fi
ALIGN_DIR="${ALIGN_DIR:-.align}"
cmdfile="$ALIGN_DIR/check-commands.txt"

if [ ! -f "$cmdfile" ]; then
  echo "[align-check] 未找到 check-commands.txt — 跳过验证（待补）。"
  exit 0
fi

# 临时输出文件
out="$(mktemp 2>/dev/null || echo "/tmp/align-check.$$")"
trap 'rm -f "$out" 2>/dev/null' EXIT

pass=0; fail=0; skip=0; total=0

while IFS= read -r line || [ -n "$line" ]; do
  # 跳过空行与注释
  case "$line" in
    ''|\#*) continue ;;
  esac
  total=$((total+1))
  printf '▶ %s\n' "$line"
  # 切换到仓库根，使相对路径命令可用
  if ( cd "$ALIGN_DIR/.." && eval "$line" ) >"$out" 2>&1; then
    printf '  ✓ PASS\n'; pass=$((pass+1))
  else
    printf '  ✗ FAIL\n'; fail=$((fail+1))
    # 打印输出尾部摘要
    tail -n 8 "$out" 2>/dev/null | sed 's/^/    | /'
  fi
done < "$cmdfile"

echo "---"
echo "总计 $total / 通过 $pass / 失败 $fail"
if [ "$fail" -gt 0 ]; then
  echo "[align-check] 存在失败项 — 交付前必须修复或显式标注债务。"
  exit 1
fi
exit 0
