# 凭据清单（Secrets Checklist）

本仓库所有配置已脱敏，**不含任何真实凭据**。使用时按下表把占位符替换为你自己的凭据：
占位符未填时 `install.sh --merge-mcp` / `--with-config` 会主动拒绝执行。

| # | 占位符 | 出现位置 | 对应服务 | 说明 |
|---|---|---|---|---|
| 1 | `<ZAI_BEARER_TOKEN>` | `agents/claude-code/mcp-servers.json.tpl`、`agents/codex/config.toml` | z.ai 平台 MCP（web-reader / web-search-prime / zread） | z.ai 控制台 API Keys |
| 2 | `<ZAI_API_KEY>` | 同上两处（zai-mcp-server 的 `Z_AI_API_KEY`） | 智谱 Z_AI（zai-mcp-server） | 智谱开放平台 API Key |

不需要这些 MCP 的话，直接删掉对应配置即可，不影响 skills 使用。

## 首次使用需自行登录/授权（无法随仓库分发）

| 工具 | 项目 | 说明 |
|---|---|---|
| Codex | `~/.codex/auth.json` | 重新 `codex` 登录；hooks.json 首次运行会弹 Hook 信任确认 |
| OMP | oauth | `~/.omp/agent/` 配置走 oauth 授权（`auth: oauth`），首次使用重新授权 |
| Claude Code | 代理 token | settings.json 的 `ANTHROPIC_AUTH_TOKEN=PROXY_MANAGED` 面向本地代理（如 OMP）；无代理环境可删掉这两个 env 改用官方登录 |
| gh CLI | GitHub | `gh auth login`；`~/.gitconfig` credential helper 指向 gh（见 `docs/misc/gitconfig.template`） |

## 这类文件永远不要 commit 进任何 git 仓库

- `~/.claude.json`（全局 MCP 节点含真实 key）、`~/.codex/auth.json`
- 任何含 `apiKey` / `Bearer` 真实值的 provider 配置（如 opencode.json 这类多 provider 配置文件是明文密钥重灾区）
- `.ssh/`、`.env*`、`*.pem`、`*.key`、凭据数据库

本仓库 `.gitignore` 已排除 `*.key`、`secrets/**`、`.env*`；若你 fork 后自行扩充内容，提交前建议跑一遍密钥模式扫描（token / key / private key 指纹）。
