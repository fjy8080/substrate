#!/usr/bin/env bash
# ============================================================================
# substrate —— 多 agent 技能与记忆包安装脚本
#
# 用法：
#   bash install.sh                 # 只装无损项：skills / 全局必读指令 / hook 脚本 / OMP 配置
#   bash install.sh --merge-mcp     # 额外把 MCP 模板合并进 ~/.claude.json（需 jq，先填占位符）
#   bash install.sh --with-memory   # 额外部署 codex 记忆到 ~/.codex/memories/
#   bash install.sh --with-config   # 额外覆盖 ~/.claude/settings.json 与 ~/.codex/config.toml
#   以上参数可组合；任意组合再加 --dry-run 只打印动作不执行
#
# 任何被覆盖的文件都会先备份为 <原名>.bak-substrate-<时间戳>。
# Claude 侧通用记忆（memory/claude/）不自动安装，按需手动放置，见 memory/README.md。
# ============================================================================
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
DRY=0; MERGE_MCP=0; WITH_MEMORY=0; WITH_CONFIG=0

for a in "$@"; do
  case "$a" in
    --merge-mcp)   MERGE_MCP=1 ;;
    --with-memory) WITH_MEMORY=1 ;;
    --with-config) WITH_CONFIG=1 ;;
    --dry-run)     DRY=1 ;;
    -h|--help)     sed -n '3,12p' "$0"; exit 0 ;;
    *) echo "未知参数: $a（用 --help 查看用法）" >&2; exit 1 ;;
  esac
done

stamp() { date +%Y%m%d%H%M%S; }

act() { # act "描述" 命令...
  local desc="$1"; shift
  if [ "$DRY" = 1 ]; then
    echo "[dry-run] $desc"
  else
    echo "→ $desc"
    "$@"
  fi
}

backup_and_cp_file() { # 备份已存在的目标文件后覆盖
  local src="$1" dst="$2"
  if [ -f "$dst" ] && [ "$DRY" = 0 ]; then cp -a "$dst" "$dst.bak-substrate-$(stamp)"; echo "  已备份原文件 → ${dst}.bak-substrate-*"; fi
  act "安装 $src → $dst" cp "$src" "$dst"
}

backup_and_cp_dir() { # 备份同名子项后合并目录；备份集中放 ~/.cache/substrate-backups/，避免 .bak 后缀目录被 skill 扫描器误识别
  local src="$1" dst="$2"
  local bdir="$HOME/.cache/substrate-backups/$(stamp)/$(printf '%s' "$dst" | tr '/ ' '__')"
  if [ -d "$dst" ] && [ "$DRY" = 0 ]; then
    for item in "$src"/* "$src"/.[!.]*; do
      [ -e "$item" ] || continue
      local name="${item##*/}"
      if [ -e "$dst/$name" ]; then
        mkdir -p "$bdir"
        cp -a "$dst/$name" "$bdir/$name"
        echo "  已备份 $dst/$name → $bdir/$name"
      fi
    done
  fi
  mkdir -p "$dst"
  act "合并目录 $src/ → $dst/" cp -a "$src/." "$dst/"
}

echo "== substrate 恢复脚本（repo: $REPO）=="

# ---------- 1. Claude Code：skills + hook 脚本 ----------
backup_and_cp_dir "$REPO/agents/claude-code/skills" "$HOME/.claude/skills"
mkdir -p "$HOME/.claude/scripts"
for f in notification.js check-memory-links.sh; do
  backup_and_cp_file "$REPO/agents/claude-code/scripts/$f" "$HOME/.claude/scripts/$f"
  [ "$DRY" = 0 ] && chmod +x "$HOME/.claude/scripts/$f" 2>/dev/null || true
done

# 全局必读指令（目标已存在会先备份，请按需与原内容合并）
[ -f "$REPO/agents/claude-code/CLAUDE.md" ] && backup_and_cp_file "$REPO/agents/claude-code/CLAUDE.md" "$HOME/.claude/CLAUDE.md"

# ---------- 2. Codex：skills + hooks.json ----------
backup_and_cp_dir "$REPO/agents/codex/skills" "$HOME/.codex/skills"
backup_and_cp_file "$REPO/agents/codex/hooks.json" "$HOME/.codex/hooks.json"
[ -f "$REPO/agents/codex/AGENTS.md" ] && backup_and_cp_file "$REPO/agents/codex/AGENTS.md" "$HOME/.codex/AGENTS.md"

# ---------- 3. OMP：配置（无密钥，原样可用） ----------
mkdir -p "$HOME/.omp/agent"
backup_and_cp_file "$REPO/agents/omp/config.yml" "$HOME/.omp/agent/config.yml"
backup_and_cp_file "$REPO/agents/omp/models.yml" "$HOME/.omp/agent/models.yml"

# ---------- 4. 可选：合并 MCP 到 ~/.claude.json ----------
if [ "$MERGE_MCP" = 1 ]; then
  TPL="$REPO/agents/claude-code/mcp-servers.json.tpl"
  if grep -q '<ZAI_' "$TPL"; then
    echo "✗ $TPL 仍含 <ZAI_*> 占位符——请先按 docs/secrets-checklist.md 填入真实凭据再合并。" >&2
    exit 1
  fi
  command -v jq >/dev/null || { echo "✗ 需要 jq 来合并 MCP 配置"; exit 1; }
  if [ -f "$HOME/.claude.json" ]; then
    if [ "$DRY" = 0 ]; then
      cp -a "$HOME/.claude.json" "$HOME/.claude.json.bak-substrate-$(stamp)"
      echo "  已备份 ~/.claude.json"
    fi
    act "合并 mcpServers 到 ~/.claude.json" bash -c \
      "jq --slurpfile tpl '$TPL' '.mcpServers = ((.mcpServers // {}) * \$tpl[0].mcpServers)' '$HOME/.claude.json' > '$HOME/.claude.json.tmp' && mv '$HOME/.claude.json.tmp' '$HOME/.claude.json'"
  else
    echo "  ~/.claude.json 不存在（Claude Code 尚未首次运行）；请先启动一次 claude 再执行 --merge-mcp"
  fi
fi

# ---------- 5. 可选：codex 记忆 ----------
if [ "$WITH_MEMORY" = 1 ]; then
  mkdir -p "$HOME/.codex/memories"
  for f in MEMORY.md memory_summary.md; do
    [ -f "$REPO/memory/codex/$f" ] && backup_and_cp_file "$REPO/memory/codex/$f" "$HOME/.codex/memories/$f"
  done
  [ -d "$REPO/memory/codex/extensions" ] && backup_and_cp_dir "$REPO/memory/codex/extensions" "$HOME/.codex/memories/extensions"
fi

# ---------- 6. 可选：覆盖主配置 ----------
if [ "$WITH_CONFIG" = 1 ]; then
  for f in "$REPO/agents/claude-code/settings.json" "$REPO/agents/codex/config.toml"; do
    if grep -q '<ZAI_' "$f"; then
      echo "✗ $f 仍含 <ZAI_*> 占位符，为防误用未覆盖。请先填写凭据（docs/secrets-checklist.md）。" >&2
      exit 1
    fi
  done
  backup_and_cp_file "$REPO/agents/claude-code/settings.json" "$HOME/.claude/settings.json"
  backup_and_cp_file "$REPO/agents/codex/config.toml" "$HOME/.codex/config.toml"
fi

echo
echo "== 完成。剩余手动项 =="
echo "  1. 密钥/登录：见 docs/secrets-checklist.md（z.ai MCP token、Z_AI_API_KEY、Codex 登录、OMP oauth）"
echo "  2. Claude 插件 marketplace：若用了 --with-config：settings.json 启用的官方插件需重新经 marketplace 安装"
echo "  4. Claude 通用记忆 memory/claude/：手动放置到目标项目 memory 目录，见 memory/README.md"
echo "  5. stop-that-shit hook 强制模式（可选）：见 agents/vendor/stop-that-shit/INSTALL.md，经 plugin marketplace 安装并由本人确认 Hook 信任"
