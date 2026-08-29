# substrate

> 基于 GitHub 协作流程的 AI 编程 agent **技能包** 与跨项目**通用记忆包**。
> 一套在 Claude Code 与 Codex 上长期实战打磨的交付纪律：Issue 全生命周期、exact-HEAD PR 审查与修复、多 agent 受控交付，以及防止 agent 越界与过度防御工程的行为判据。

## 这是什么

两个核心资产，全部即取即用：

1. **开发技能包（`agents/*/skills/`）** —— 围绕 GitHub 协作流程（Issue → 分支/worktree → PR → CI → 审查 → 合并 → 记忆沉淀）构建的一组 skill。每个 skill 都有明确的触发条件与权限边界（只读 / 显式授权后才写 / 三轮收敛后停），核心脚本自带测试。
2. **通用记忆包（`memory/`）** —— 从多个真实项目沉淀的跨项目方法论：多 agent 并行开发纪律、Git 分支纪律、双工具单一真相源约定、GitHub API 硬规则、平台差异 workaround。已脱敏，可直接并入你自己的 agent 记忆体系。

适用 agent：**Claude Code** 与 **Codex**（两边各一份、同源维护）；`agents/omp/` 附带 OMP 配置示例。

## 技能清单

### GitHub 协作流程技能

| Skill | 触发方式 | 作用 |
|---|---|---|
| `github-issue-create` | `/github-issue-create` 或「创建issue + 文本」 | 把文本变成经代码核验、严重度分级、任务边界的 Issue 草稿；仅在用户批准后发布 |
| `github-issue-review` | `/github-issue-review` 或「审查issue + 编号」 | 只读分诊/审计：真实性、严重度、任务归属、契约影响、重复项、可复现性；评论发布需用户确认 |
| `github-issue-debug` | `/github-issue-debug` 或「修复issue + 编号」 | 在隔离分支/worktree 上按锁定 Issue 范围实现修复并开发 PR |
| `github-pr-review` | `/github-pr-review` 或「审查#N」 | exact-HEAD 只读 PR 审查：PR 作者身份、贡献者独立性、任务边界分类、P0/P1-only 三轮收敛；未经确认不发布 |
| `github-pr-fix` | `/github-pr-fix` 或「修复#N」 | 验证并修复活跃 PR 上可行动的反馈，维护完整身份/生命周期台账，回复前先汇报 |
| `agent-managed-delivery` | 仅显式 `/agent-managed-delivery` | 锁定 WBS 范围的多 agent 交付工作流：状态机（18 态）+ `workflowctl.py` 持久状态 + exact-HEAD/CI/审查 gate；绝不从普通开发请求推断触发 |

### ★ 必读技能（全局指令强制加载，见下节）

| `lean-mode`（节制工程） | [Timefiles404/lean-mode-skill](https://github.com/Timefiles404/lean-mode-skill)（MIT） | 防御性代码/校验/抽象的信任边界判据（校验只在四处信任边界做一次）；构建测试提速判据 |
| `stop-that-shit`（别再造史了） | [lennney/stop-that-shit](https://github.com/lennney/stop-that-shit)（MIT, v0.1.0） | Stop Ladder 四问拦截范围膨胀、顺手加固、无需求的哈希/依赖/兼容层；review/monitor 模式一律只读 |

## 通用记忆包

`memory/claude/` —— 13 条跨项目方法论（各条独立成文，frontmatter 标注 type）：

- **AMD 多 agent 交付**：工作流核心规则与状态机、Claude Code 实操 workaround（GIT_DIR、沙箱 cwd、venv 共享）、批次实操约定
- **Git 纪律**：一任务一分支一 PR、实现者不自行合并、禁高风险操作、分支命名约定
- **双工具协作**：codex 与 claude code 并用的单一真相源原则、双端 skill 同步的占位符回译规则
- **平台规则**：GitHub Projects API 硬规则（限流退避、单写队列、禁并发 mutation）、MCP 图像工具用法、subagent 模型约定

`memory/codex/` —— Codex 记忆精选：10 条用户工作偏好（原话级）+ 7 条通用交付技巧（脱敏版，项目快照已移除）。

使用方式：按需把记忆文件放入目标项目的 memory 目录（或 home 级记忆），并在对应 `MEMORY.md` 索引补一行；详见 `memory/README.md`。

## 快速开始

```bash
git clone https://github.com/HP26666/substrate
cd substrate

bash install.sh --dry-run     # 预览将执行的动作
bash install.sh               # 安装：skills + 全局必读指令 + hook 脚本 + OMP 配置示例（覆盖前自动备份）

# 可选开关（可组合）：
bash install.sh --merge-mcp   # 把 MCP 模板合并进 ~/.claude.json（需 jq；先填 <ZAI_*> 占位符）
bash install.sh --with-config # 覆盖 ~/.claude/settings.json 与 ~/.codex/config.toml（脱敏模板）
bash install.sh --with-memory # 部署 codex 记忆到 ~/.codex/memories/
```

- 配置模板（settings.json / config.toml / mcp-servers.json.tpl）**不含任何真实凭据**，需替换的占位符清单见 `docs/secrets-checklist.md`。
- 也可以不跑脚本，直接把想要的 skill 目录拷进 `~/.claude/skills/` 或 `~/.codex/skills/`——skill 均为自包含目录。

## 必读 skill 机制

`install.sh` 会把 `agents/claude-code/CLAUDE.md` 与 `agents/codex/AGENTS.md` 部署为**全局指令文件**（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`），使两个必读 skill 的核心判据在每次会话自动加载，正文细节在各自 `skills/<name>/SKILL.md`。

- lean-mode 与 stop-that-shit 以 **advisory 模式**收录（纯 SKILL.md，零依赖、零 hook）。
- 如需 stop-that-shit 的 **hook 强制模式**（运行时硬拦截越界写入），按 `agents/vendor/stop-that-shit/INSTALL.md` 经 plugin marketplace 安装；Hook 信任需使用者本人确认。

## 目录结构

```
substrate/
├── install.sh                 # 安装脚本（幂等，覆盖前备份，--dry-run 预演）
├── agents/
│   ├── claude-code/           # skills/（8 个）+ CLAUDE.md（全局必读指令）+ settings.json
│   │                          # + mcp-servers.json.tpl + scripts/（通知/记忆断链检查 hook 脚本）
│   ├── codex/                 # skills/（8 个）+ AGENTS.md + hooks.json + config.toml 模板
│   ├── omp/                   # OMP 配置示例（模型角色/任务并发/approval 模式）
│   └── vendor/                # 第三方必读 skill 的上游完整副本（源码+测试+LICENSE，升级 diff 用）
├── memory/                    # 通用记忆包（claude 方法论 13 条 + codex 精选），详见 memory/README.md
└── docs/
    ├── secrets-checklist.md   # 需自行填入的凭据占位符清单
    ├── ccb-workflow-kit/      # CCB 多 Agent 协作工作流搭建包（教程/排障/安全脱敏说明）
    ├── OMP项目级AMD并行工作区改造复用手册.md
    └── misc/gitconfig.template
```

## 质量与测试

- skills 核心脚本自带测试（`test_*.py` / 上游 `node --test` 套件），收录时全部验证。
- stop-that-shit 上游套件 181/182 通过（唯一失败的 `opencode-smoke` 需要 OpenCode 运行时环境，与 claude/codex 路径无关）。
- 已知失败（预先存在）：claude 侧 `agent-managed-delivery` 的 `test_workflowctl.py` 32 用例中 1 个 scope-drift 用例失败；codex 侧同款全绿。

## License 与致谢

本项目以 [MIT License](LICENSE) 开源（© HP26666），覆盖自建 skills、memory、docs 与脚本。

内置的第三方项目保留各自许可（原样存于对应目录）：

- `agents/vendor/lean-mode-skill/` — MIT © Timefiles
- `agents/vendor/stop-that-shit/` — MIT © Stop That Shit contributors
