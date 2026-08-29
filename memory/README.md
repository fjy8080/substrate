# 通用记忆包（memory/）

跨项目沉淀的 agent 工作方法论，全部从真实项目实战中提炼。每条独立成文、frontmatter 标注 type（feedback / project / reference），可按需并入你自己的记忆体系。

## claude/ —— 13 条跨项目方法论

| 文件 | 类型 | 内容 |
|---|---|---|
| `amd-workflow-rules.md` | project | AMD 多 agent 交付：核心原则、18 态状态机、角色分工（Scout / Explorer / Developer / Knowledge Keeper / Reviewer）与调度约束 |
| `amd-cc-workarounds.md` | reference | Claude Code 下跑 AMD 的实操 workaround：GIT_DIR 前缀、沙箱 cwd 限制、venv 共享、GitHub 限流处理 |
| `amd-workflow-claude-code.md` | reference | AMD 批次实操约定：workflowctl 调用位置、memory-gate `--file` 陷阱、gh 权限预检、git diff 预检 |
| `git-branch-discipline.md` | project | Git 纪律：一任务一分支一 PR、实现者不自行合并（高风险任务双独立审查）、禁 `reset --hard` / 强推 |
| `git-workflow.md` | project | 分支命名约定（feature / fix 前缀、develop 主干、合并后清理远程分支） |
| `dev-tooling-dual-agent.md` | feedback | 双 agent（Codex + Claude Code）并用时共用单一真相源，不各自维护会漂移的副本 |
| `shared-memory-location.md` | reference | `AGENTS.md` + `memory/` 作为跨工具真相源的读取顺序与冲突优先级 |
| `sync-codex-skill-to-claude.md` | feedback | 双端 skill 同步规则：占位符回译（`$skill` → `/skill`、路径与展开差异）与平台特有跳过项 |
| `github-projects-api.md` | reference | GitHub Projects API 硬规则：单写队列、mutation 间隔 ≥1s、指数退避、禁并发 mutation、禁止无限重试 |
| `subagent-model-opus-only.md` | feedback | 自定义 subagent 一律用最强模型档位，不按原档位降级 |
| `mcp-image-tool-for-screenshots.md` | feedback | 用户附带截图时用 MCP 图像工具读取，内置 Read 返回 unsupported 时不要放弃 |
| `ssh-access-workflow.md` | project | agent 禁访 `~/.ssh` 的环境约定：让用户用 `!` 前缀自跑短命令 |
| `codex-tmpfs-review-dirs.md` | project | `/tmp`（tmpfs）被 review checkout 塞满的排查手法；迁移配置中路径残留的警惕 |

**使用方式**：放入目标项目的 memory 目录（Claude Code 的 auto-memory 按项目路径组织），并在该目录的 `MEMORY.md` 索引里补一行条目；环境类记忆放 home 级记忆目录可全局生效。文件间 `[[互链]]` 在本包内闭合。

## codex/ —— Codex 记忆

- `memory_summary.md`：**精华** —— 10 条用户工作偏好（原话级：「直接问，不要自己猜」「先修 CI，再审查」「不要合并」等）+ 7 条通用交付技巧（exact-HEAD 证据链、未验证 gate 独立呈报、Flyway 全树扫描断言、批量 API 串行化等）
- `extensions/ad_hoc/instructions.md`：ad-hoc 记忆扩展的机制说明

按 `bash install.sh --with-memory` 部署到 `~/.codex/memories/`（同名旧文件自动备份），或手动复制。
