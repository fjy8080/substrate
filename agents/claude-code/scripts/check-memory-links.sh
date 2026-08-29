#!/usr/bin/env bash
# 校验 Claude Code auto-memory 目录的链接完整性：
#   1) MEMORY.md 中 [text](file.md) 引用的文件必须存在
#   2) [[wiki-link]] 目标对应的 <name>.md 必须存在
# 用法：check-memory-links.sh [memory目录]
#   不传参数时，根据 $CLAUDE_PROJECT_DIR 推导当前项目的 memory 目录
#   （Claude Code 项目目录命名规则：绝对路径中的 / 全部替换为 -）。
# 有断链时以 hook additionalContext 形式输出提醒，否则静默退出。
# 安装位置：~/.claude/scripts/check-memory-links.sh
set -uo pipefail

DIR="${1:-}"
if [ -z "$DIR" ] && [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    DIR="$HOME/.claude/projects/$(printf '%s' "$CLAUDE_PROJECT_DIR" | tr '/' '-')/memory"
fi
[ -f "$DIR/MEMORY.md" ] || exit 0

missing=""

# markdown 链接: [text](file.md)
while IFS= read -r ref; do
    [ -e "$DIR/$ref" ] || missing="${missing}\\n- ${ref}（MEMORY.md 链接指向的文件不存在）"
done < <(grep -oE '\]\([^)#]+\.md' "$DIR/MEMORY.md" | sed -E 's/^\]\(//' | sort -u)

# wiki 链接: [[name]] → name.md
while IFS= read -r name; do
    [ -z "$name" ] && continue
    [ -e "$DIR/$name.md" ] || missing="${missing}\\n- ${name}.md（[[wiki链接]] 目标不存在）"
done < <(grep -oE '\[\[[^]]+\]\]' "$DIR/MEMORY.md" | sed -E 's/^\[\[//; s/\]\]$//' | sort -u)

if [ -n "$missing" ]; then
    printf -v msg "⚠ auto-memory 存在断链，请修复 MEMORY.md 或补齐缺失文件：%b" "$missing"
    jq -nc --arg m "$msg" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$m}}' 2>/dev/null || true
fi
exit 0
