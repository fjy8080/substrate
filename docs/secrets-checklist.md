# 密钥恢复清单（Secrets Checklist）

本仓库所有配置已脱敏，真实凭据**永不入库**。新机器恢复时按下表逐项填入（`<...>` 为占位符）。
占位符未填时 `install.sh --merge-mcp` / `--with-config` 会主动拒绝执行。

| # | 占位符 | 出现位置 | 对应服务 | 获取方式 |
|---|---|---|---|---|
| 1 | `<ZAI_BEARER_TOKEN>` | `agents/claude-code/mcp-servers.json.tpl`、`agents/codex/config.toml` | z.ai 平台（web-reader / web-search-prime / zread 三个 MCP 的 Bearer） | z.ai 控制台 API Keys（与 #2 是同平台不同 key 形态） |
| 2 | `<ZAI_API_KEY>` | 同上两处（zai-mcp-server 的 `Z_AI_API_KEY`） | 智谱 Z_AI（zai-mcp-server） | 智谱开放平台 API Key（`xxxxxxxx.yyyyyyyy` 形态） |

## 需要重新登录/授权（无法搬文件）

| 工具 | 项目 | 说明 |
|---|---|---|
| Codex | `~/.codex/auth.json` | 凭据文件未入库，新机器重新 `codex` 登录 |
| OMP | oauth | `~/.omp/agent/` 走 oauth 授权（`auth: oauth`），首次使用重新授权 |
| Claude Code | 代理 token | settings.json 里 `ANTHROPIC_AUTH_TOKEN=PROXY_MANAGED` 由本地代理（OMP, 127.0.0.1:15721）管理，OMP 授权后自动生效 |
| gh CLI | GitHub | `gh auth login`；`~/.gitconfig` credential helper 指向 gh（见 `docs/misc/gitconfig.template`） |

## 未入库（含真实密钥的原文件，仅留在本机）

- `~/.claude.json`（mcpServers 节含真实 key）
- `~/.codex/config.toml`（本机版含真实 token）
- `~/.config/opencode/opencode.json`（5 个 provider 的明文 apiKey，opencode 未列入本仓库管理范围）

## 防误提交提醒

- 绝不把上面这些原文件 `git add` 进来；`.gitignore` 已排除 `*.key`、`secrets/**`、`.env*`
- 若将来把仓库转 public，先跑一遍密钥模式扫描确认历史提交干净
