#!/usr/bin/env bash
# ============================================================================
# substrate —— 面向任意 AI 编程 agent 的技能与记忆包安装脚本（宿主注册表驱动）
#
# 用法：
#   bash install.sh                              # 安装全部一等宿主（claude-code, codex, omp）
#   bash install.sh --host claude-code           # 只装指定宿主；--host 可重复或逗号分隔
#   bash install.sh --host generic --dest DIR    # 通用模式：skills 拷到任意目录 + 打印接线清单
#   bash install.sh --merge-mcp                  # (claude-code) MCP 模板合并进 ~/.claude.json，需 jq，先填占位符
#   bash install.sh --with-memory                # (codex) 部署通用记忆包到 ~/.codex/memories/
#   bash install.sh --with-config                # (claude-code/codex) 覆盖 settings.json / config.toml 模板
#   以上参数可组合；任意组合再加 --dry-run 只打印动作不执行
#
# 新增宿主：在下方注册表加一个 install_<name> 函数并加入 ALL_HOSTS 即可，
# 宿主的技能目录/指令文件/触发语法说明见 docs/hosts/。
#
# 任何被覆盖的文件都会先备份为 <原名>.bak-substrate-<时间戳>。
# 通用记忆（memory/entries/）不自动安装，按需手动放置，见 memory/README.md。
# ============================================================================
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
DRY=0; MERGE_MCP=0; WITH_MEMORY=0; WITH_CONFIG=0
ALL_HOSTS="claude-code codex omp generic"
SELECTED_HOSTS=""

while [ $# -gt 0 ]; do
  case "$1" in
    --merge-mcp)   MERGE_MCP=1 ;;
    --with-memory) WITH_MEMORY=1 ;;
    --with-config) WITH_CONFIG=1 ;;
    --dry-run)     DRY=1 ;;
    --host)        shift; SELECTED_HOSTS="${SELECTED_HOSTS:+$SELECTED_HOSTS,}$(printf '%s' "${1:?--host 需要宿主名}" | tr '_' '-')" ;;
    --dest)        shift; GENERIC_DEST="${1:?--dest 需要目录}" ;;
    -h|--help)     sed -n '3,16p' "$0"; exit 0 ;;
    *) echo "未知参数: $1（用 --help 查看用法）" >&2; exit 1 ;;
  esac
  shift
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

want_host() { # 当前宿主是否被选中；未指定 --host 时默认除 generic 外的全部一等宿主
  local h="$1"
  if [ -z "$SELECTED_HOSTS" ]; then
    [ "$h" = "generic" ] && return 1
    return 0
  fi
  case ",$SELECTED_HOSTS," in *",$h,"*) return 0 ;; esac
  return 1
}

# ---------------------------------------------------------------------------
# 宿主注册表：每个一等宿主一个 install_<name> 函数
# ---------------------------------------------------------------------------

install_claude_code() {
  echo "-- claude-code --"
  backup_and_cp_dir "$REPO/skills" "$HOME/.claude/skills"
  mkdir -p "$HOME/.claude/scripts"
  for f in notification.js check-memory-links.sh; do
    backup_and_cp_file "$REPO/adapters/claude-code/scripts/$f" "$HOME/.claude/scripts/$f"
    [ "$DRY" = 0 ] && chmod +x "$HOME/.claude/scripts/$f" 2>/dev/null || true
  done
  # 全局必读指令（目标已存在会先备份，请按需与原内容合并）
  backup_and_cp_file "$REPO/instructions/GLOBAL.md" "$HOME/.claude/CLAUDE.md"

  if [ "$MERGE_MCP" = 1 ]; then
    TPL="$REPO/adapters/claude-code/mcp-servers.json.tpl"
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
  if [ "$WITH_CONFIG" = 1 ]; then
    guard_placeholder "$REPO/adapters/claude-code/settings.json"
    backup_and_cp_file "$REPO/adapters/claude-code/settings.json" "$HOME/.claude/settings.json"
  fi
}

install_codex() {
  echo "-- codex --"
  backup_and_cp_dir "$REPO/skills" "$HOME/.codex/skills"
  # 宿主专属 manifest（agents/openai.yaml）从适配层拷入各 skill
  if [ "$DRY" = 0 ]; then
    find "$REPO/adapters/codex/skills" -name openai.yaml | while read -r y; do
      rel="${y#"$REPO/adapters/codex/skills/"}"
      mkdir -p "$HOME/.codex/skills/$(dirname "$rel")"
      act "安装 $rel → ~/.codex/skills/$rel" cp "$y" "$HOME/.codex/skills/$rel"
    done
  else
    act "安装 adapters/codex/skills/*/agents/openai.yaml → ~/.codex/skills/ 各 skill" echo
  fi
  backup_and_cp_file "$REPO/adapters/codex/hooks.json" "$HOME/.codex/hooks.json"
  backup_and_cp_file "$REPO/instructions/GLOBAL.md" "$HOME/.codex/AGENTS.md"
  if [ "$WITH_MEMORY" = 1 ]; then
    mkdir -p "$HOME/.codex/memories"
    for f in "$REPO"/memory/codex-pack/*; do
      [ -e "$f" ] || continue
      case "$(basename "$f")" in
        extensions) backup_and_cp_dir "$f" "$HOME/.codex/memories/extensions" ;;
        *) backup_and_cp_file "$f" "$HOME/.codex/memories/$(basename "$f")" ;;
      esac
    done
  fi
  if [ "$WITH_CONFIG" = 1 ]; then
    guard_placeholder "$REPO/adapters/codex/config.toml"
    backup_and_cp_file "$REPO/adapters/codex/config.toml" "$HOME/.codex/config.toml"
  fi
}

install_omp() {
  echo "-- omp --"
  mkdir -p "$HOME/.omp/agent"
  backup_and_cp_file "$REPO/adapters/omp/config.yml" "$HOME/.omp/agent/config.yml"
  backup_and_cp_file "$REPO/adapters/omp/models.yml" "$HOME/.omp/agent/models.yml"
  backup_and_cp_dir "$REPO/adapters/omp/agents" "$HOME/.omp/agent/agents"
}

install_generic() {
  echo "-- generic --"
  if [ -z "${GENERIC_DEST:-}" ]; then
    echo "✗ generic 模式需要 --dest DIR（skills 将拷贝到 DIR/skills）" >&2
    exit 1
  fi
  backup_and_cp_dir "$REPO/skills" "$GENERIC_DEST/skills"
  mkdir -p "$GENERIC_DEST"
  backup_and_cp_file "$REPO/instructions/GLOBAL.md" "$GENERIC_DEST/GLOBAL.md"
  echo
  echo "  generic 手动接线清单（按你的 agent 文档完成）："
  echo "  1. 把 \$DEST/skills 下需要的 skill 目录登记/拷贝到 agent 的技能加载目录"
  echo "  2. 把 GLOBAL.md 内容并入 agent 的全局指令文件（CLAUDE.md / AGENTS.md / 系统提示）"
  echo "  3. 触发语法按宿主替换：SKILL.md 内 /name 在 Codex 为 \$name，其他宿主按其规则"
  echo "  4. 各宿主细节见 docs/hosts/；新宿主可在 install.sh 注册表加一个 install_<name>"
}

guard_placeholder() { # 含未填占位符的配置模板禁止覆盖真实配置
  if grep -q '<ZAI_' "$1"; then
    echo "✗ $1 仍含 <ZAI_*> 占位符，为防误用未覆盖。请先填写凭据（docs/secrets-checklist.md）。" >&2
    exit 1
  fi
}

# ---------------------------------------------------------------------------
echo "== substrate 安装脚本（repo: $REPO）=="

# 校验 --host 取值
if [ -n "$SELECTED_HOSTS" ]; then
  IFS=',' read -r -a REQUESTED_HOSTS <<< "$SELECTED_HOSTS"
  for r in "${REQUESTED_HOSTS[@]}"; do
    case " $ALL_HOSTS " in *" $r "*) ;; *) echo "未知宿主: $r（可选：$ALL_HOSTS）" >&2; exit 1 ;; esac
  done
fi

for h in $ALL_HOSTS; do
  want_host "$h" || continue
  "install_`printf '%s' "$h" | tr - '_'`"
done

echo
echo "== 完成。剩余手动项 =="
echo "  1. 密钥/登录：见 docs/secrets-checklist.md（z.ai MCP token、Z_AI_API_KEY、Codex 登录、OMP oauth）"
echo "  2. Claude 插件 marketplace：若用了 --with-config：settings.json 启用的官方插件需重新经 marketplace 安装"
echo "  3. 通用记忆 memory/entries/：手动放置到目标项目 memory 目录，见 memory/README.md"
echo "  4. stop-that-shit hook 强制模式（可选）：见 vendor/stop-that-shit/INSTALL.md，经 plugin marketplace 安装并由用户确认 Hook 信任"
