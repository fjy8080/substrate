# Codex CLI 宿主

`--host codex` 的安装目标与差异说明。

## 安装目标

| 来源 | 目标 |
|---|---|
| `skills/` | `~/.codex/skills/` |
| `adapters/codex/skills/<name>/agents/openai.yaml` | 拷入对应 skill 目录的 `agents/openai.yaml`（Codex 专属 manifest：display_name / default_prompt / policy） |
| `instructions/GLOBAL.md` | `~/.codex/AGENTS.md`（全局指令） |
| `adapters/codex/hooks.json` | `~/.codex/hooks.json` |
| `adapters/codex/config.toml` | `~/.codex/config.toml`（仅 `--with-config`） |
| `memory/codex-pack/` | `~/.codex/memories/`（仅 `--with-memory`） |

## 要点

- **触发语法**：`$skill-name`（区别于 Claude Code 的 `/skill-name`）；SKILL.md 顶部约定段已说明双写法。
- **openai.yaml**：Codex 的 skill 元数据层，从 `adapters/codex/skills/` 分发——skills/ 单源本体不含宿主专属文件。
- **hooks**：hooks.json 复用 Claude hook 协议的环境变量（`$CLAUDE_TOOL_INPUT_FILE_PATH` 等），首次运行会弹 Hook 信任确认。
- **记忆**：`--with-memory` 部署的 `memory_summary.md` + `MEMORY.md` 是 Codex 会话自动加载的入口；通用方法论条目（memory/entries/）按需手动合并进这两个文件或放项目 memory。
