# MEMORY

通用记忆包全量索引。使用方式见 [README.md](README.md)。

## entries/ —— 通用方法论

- [AMD 工作流核心规则](entries/amd-workflow-rules.md) — 状态机、角色分工、scope 管理与合并门禁
- [Git 分支纪律](entries/git-branch-discipline.md) — 一任务一分支一 PR、实现者不自行合并、禁高风险操作
- [Git 实战坑合集](entries/git-pitfalls.md) — squash 假象、冲突取侧、gh api 应急推送、ls-remote 权威校验
- [Shell 与 CI 实战坑](entries/shell-and-ci-pitfalls.md) — 管道吞退出码、CI 磁盘守卫绝对量、解释器一致、对照实验
- [GitHub Projects API 硬规则](entries/github-projects-api.md) — 限流退避、单写队列、禁并发 mutation
- [多 agent 任务认领协议](entries/multi-agent-task-claiming.md) — 认领前五查、领取即占坑、归属只认 commit author
- [项目记忆协议](entries/project-memory-protocol.md) — 六类分类、写入时机触发器、记忆与代码冲突以代码为准
- [项目记忆的单一真相源](entries/shared-memory-location.md) — AGENTS.md + memory/ 工具无关，多工具共用不复制
- [会话交接纪律](entries/session-handoff-discipline.md) — 开了 PR/推分支必须立即留痕，盘点三件套核对断层
- [worktree 实操技巧](entries/worktree-tips.md) — 软链共享依赖与 memory、.gitignore 斜杠坑
- [LLM 产出验收口径](entries/llm-output-acceptance.md) — mock 默认真模型手动、绝对要素清单、tolerate-drop
- [Subagent 模型档位策略](entries/subagent-model-policy.md) — subagent 统一最强档位，质量优先

## hosts/ —— 宿主专属实操

- [Claude Code 宿主备忘](hosts/claude-code.md) — GIT_DIR workaround、沙箱 cwd、gh 权限 allow、截图 MCP、SSH 禁访
- [Codex CLI 宿主备忘](hosts/codex.md) — tmpfs review 目录风险、旧平台路径残留警惕

## codex-pack/ —— Codex 原生格式

- `memory_summary.md` — 用户偏好与交付技巧精华（`--with-memory` 部署）
- `extensions/` — ad-hoc 记忆扩展机制
