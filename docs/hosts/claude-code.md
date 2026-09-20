# Claude Code 宿主

`--host claude-code` 的安装目标与差异说明。

## 安装目标

| 来源 | 目标 |
|---|---|
| `skills/` | `~/.claude/skills/`（skill 目录整体拷入） |
| `instructions/GLOBAL.md` | `~/.claude/CLAUDE.md`（全局指令，每次会话自动加载；已有则先备份） |
| `adapters/claude-code/scripts/{notification.js,check-memory-links.sh}` | `~/.claude/scripts/` |
| `adapters/claude-code/settings.json` | `~/.claude/settings.json`（仅 `--with-config`） |
| `adapters/claude-code/mcp-servers.json.tpl` | 合并进 `~/.claude.json`（仅 `--merge-mcp`，需 jq） |

## 要点

- **触发语法**：`/skill-name` 斜杠命令，或按 SKILL.md description 自动触发。
- **skills 规范**：Claude Code 原生支持 Agent Skills 格式（SKILL.md frontmatter 的 `name`/`description`），本仓库 skills 无需改造即插即用。
- **全局指令**：`GLOBAL.md` 部署为 `CLAUDE.md` 后，lean-mode 与 stop-that-shit 两个必读判据每次会话强制加载。
- **hook 脚本**：`notification.js`（通知）与 `check-memory-links.sh`（记忆断链检查）需在 settings.json 的 hooks 配置里引用（`--with-config` 模板已配好，手动安装者按需自配）。
- **subagent**：`agent-managed-delivery` 在有 subagent 能力的宿主上按角色并行调度；OMP 格式的 6 个角色定义随仓库分发于 `adapters/omp/agents/`（可作其他宿主编写角色定义的参考），模型档位建议见 `memory/entries/subagent-model-policy.md`。
- **已知宿主特性**：Bash 沙箱 cwd 限制、`~/.ssh` 禁访、截图 MCP 工具等实操备忘见 `memory/hosts/claude-code.md`。
