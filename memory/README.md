# 通用记忆（memory/）

从各项目的 auto-memory 与 Codex 记忆中**精选的跨项目通用部分**（敏感信息已按用户 2026-08-30 的决定脱敏）。项目特定记忆（HXCQ 部署流程、shenxue 交付状态等）不属于本仓库——那部分由各项目自己的 `memory/` 目录和上一次的 workspace-migration tar 包负责。

## claude/ —— 13 条通用方法论记忆

| 文件 | 内容 | 原位置（来源项目 memory） |
|---|---|---|
| `subagent-model-opus-only.md` | 用户偏好：自定义 subagent 一律用 opus，不降级 | HXCQ-Sport |
| `sync-codex-skill-to-claude.md` | codex↔claude 双端 skill 同步的占位符回译规则与跳过项 | HXCQ-Sport |
| `mcp-image-tool-for-screenshots.md` | 用户附截图时用 MCP 图像工具读取，Read 失败别放弃 | HXCQ-Sport |
| `amd-workflow-rules.md` | AMD（Agent Managed Delivery）工作流核心规则、状态机、角色分工 | shenxue-ai |
| `amd-cc-workarounds.md` | Claude Code 下跑 AMD 的实操 workaround（GIT_DIR、沙箱 cwd、venv 共享） | shenxue-ai |
| `amd-workflow-claude-code.md` | AMD 批次实操约定（workflowctl 路径、memory-gate 陷阱、gh 权限） | shenxue-ai |
| `dev-tooling-dual-agent.md` | codex 与 claude code 并用时的单一真相源原则 | shenxue-ai |
| `git-branch-discipline.md` | Git 纪律：一任务一分支一 PR、不自行合并、禁高风险操作 | shenxue-ai |
| `git-workflow.md` | 分支命名约定（feature/fix 前缀、develop 主干） | shenxue-ai |
| `github-projects-api.md` | GitHub Projects API 硬规则（限流退避、单写队列、禁止并发 mutation） | shenxue-ai |
| `shared-memory-location.md` | AGENTS.md+memory/ 作为跨工具单一真相源的读取顺序与优先级 | shenxue-ai |
| `ssh-access-workflow.md` | 本机 ~/.ssh 对 agent 禁访，让用户用 `!` 前缀自跑短命令 | home 级 |
| `codex-tmpfs-review-dirs.md` | /tmp tmpfs 会被 review checkout 塞满；codex 配置有 Windows 迁移残留要警惕 | home 级 |

**恢复方式**：这些文件原本分散在不同项目的 auto-memory 目录。建议恢复时：
- 环境类（`ssh-access-workflow.md`、`codex-tmpfs-review-dirs.md`）放 home 级 memory：`~/.claude/projects/<home 目录转义>/memory/`
- 方法论类按需放入常用项目对应的 memory 目录，或同样放 home 级
- 放置后记得在目标 `MEMORY.md` 索引里补一行条目（auto-memory 按 `MEMORY.md` 索引加载）

## codex/ —— Codex 记忆脱敏精选版

原机 `~/.codex/memories/` 共 19 个 Task Group（91KB）。按用户决定的脱敏策略，本仓库只保留：

| 文件 | 内容 |
|---|---|
| `MEMORY.md` | 仅保留无敏感项的 PDF answer highlighting 任务组 + 脱敏说明头 |
| `memory_summary.md` | **精华**：用户偏好原话（“直接问不要自己猜”、“先修CI再审查”等 10 条）+ 通用工作技巧 |
| `extensions/ad_hoc/instructions.md` | ad-hoc 记忆系统的说明文件 |

已移除（完整版仅存原机，不入库）：
- 16 个项目交付快照 Task Group（shenxue-ai ×8、HXCQ-Sport ×4、xingyan ×1、KDE/SSH ×1、版权纠纷 ×1、代理排障 ×1）——含 VPS/服务器标识、私钥操作记录、代理工具链、法律事务、业务实现细节
- `extensions/ad_hoc/notes/`（xingyan 项目交接记录）
- `raw_memories.md`（378KB 原始滚存，本就未收录）

**恢复方式**：`bash install.sh --with-memory`（自动备份同名旧文件）。
