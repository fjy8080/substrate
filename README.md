# substrate

> 面向**任意 AI 编程 agent** 的**技能包**与**通用记忆包**。
> 一套在多个真实项目、多个 agent 宿主上长期实战打磨的交付纪律：Issue 全生命周期、exact-HEAD PR 审查与修复、多 agent 受控交付、AI 产出验收，以及防止 agent 越界与过度防御工程的行为判据。

## 这是什么

三个核心资产，全部即取即用、**宿主中立**（Claude Code、Codex CLI 均一等支持，其他 agent 走 generic 模式）：

1. **开发技能包（`skills/`，单源）** —— 围绕 GitHub 协作流程（Issue → 分支/worktree → PR → CI → 审查 → 合并 → 记忆沉淀）构建的 9 个 skill，外加治理模板与 DoD 清单。每个 skill 都有明确的触发条件与权限边界（只读 / 显式授权后才写 / 三轮收敛后停），核心脚本自带测试。
2. **通用记忆包（`memory/`）** —— 从多个真实项目沉淀的跨项目方法论：多 agent 并行开发纪律、Git 分支纪律与实战坑、任务认领协议、项目记忆协议、GitHub API 硬规则、LLM 产出验收口径、平台差异 workaround。可直接并入你自己的 agent 记忆体系。
3. **治理模板（`templates/`）** —— 无分支保护仓库的人工合并控制：13 节 PR 模板、Issue 模板、PR 元数据 CI 校验脚本、DoD 11 条与禁止绕过门禁清单。

## 技能清单

### GitHub 协作流程技能

| Skill | 触发方式 | 作用 |
|---|---|---|
| `github-issue-create` | 显式调用或「创建issue + 文本」 | 把文本变成经代码核验、严重度分级、任务边界的 Issue 草稿；仅在用户批准后发布 |
| `github-issue-review` | 显式调用或「审查issue + 编号」 | 只读分诊/审计：真实性、严重度、任务归属、契约影响、重复项、可复现性；评论发布需用户确认 |
| `github-issue-debug` | 显式调用或「修复issue + 编号」 | 在隔离分支/worktree 上按锁定 Issue 范围实现修复并开发 PR |
| `github-pr-review` | 显式调用或「审查#N」 | exact-HEAD 只读 PR 审查：PR 作者身份、贡献者独立性、任务边界分类、P0/P1-only 三轮收敛；未经确认不发布 |
| `github-pr-fix` | 显式调用或「修复#N」 | 验证并修复活跃 PR 上可行动的反馈，维护完整身份/生命周期台账，回复前先汇报 |
| `agent-managed-delivery` | 仅显式调用 | 锁定任务范围的多 agent 交付工作流：状态机（18 态）+ `workflowctl.py` 持久状态 + exact-HEAD/CI/审查 gate；绝不从普通开发请求推断触发 |
| `ai-output-review` | 「验收 AI 产出」等 | LLM 输出质量验收：盲评双评规程、绝对要素清单、严重事实错误率阈值、证据脱敏 |

### ★ 必读技能（全局指令强制加载）

| Skill | 来源 | 作用 |
|---|---|---|
| `lean-mode`（节制工程） | [Timefiles404/lean-mode-skill](https://github.com/Timefiles404/lean-mode-skill)（MIT） | 防御性代码/校验/抽象的信任边界判据（校验只在四处信任边界做一次）；构建测试提速判据 |
| `stop-that-shit`（别再造史了） | [lennney/stop-that-shit](https://github.com/lennney/stop-that-shit)（MIT, v0.1.0） | Stop Ladder 四问拦截范围膨胀、顺手加固、无需求的哈希/依赖/兼容层；review/monitor 模式一律只读 |

## 通用记忆包

`memory/entries/` —— 12 条跨项目方法论（各条独立成文，frontmatter 标注 type）：

- **多 agent 交付**：AMD 工作流核心规则（状态机/角色/scope/门禁）、多 agent 任务认领协议（五查/占坑/author 归属）、会话交接纪律
- **Git 纪律**：一任务一分支一 PR、实现者不自行合并、禁高风险操作、Git 实战坑合集（squash 假象/冲突取侧/gh api 应急推送）
- **Shell 与 CI**：管道吞退出码、CI 磁盘守卫绝对量、解释器一致性、环境对照实验
- **协作机制**：项目记忆协议（六类分类+写入时机触发器）、单一真相源约定、worktree 实操技巧
- **AI 工程**：LLM 产出验收口径、subagent 模型档位策略
- **平台规则**：GitHub Projects API 硬规则（限流退避、单写队列、禁并发 mutation）

`memory/hosts/` —— 宿主专属实操备忘（Claude Code / Codex 各一份）；`memory/codex-pack/` —— Codex 原生格式可部署包。

使用方式：按需把记忆条目放入目标项目的 memory 目录（或 home 级记忆），并在对应 `MEMORY.md` 索引补一行；详见 `memory/README.md`。

## 快速开始

```bash
git clone https://github.com/fjy8080/substrate
cd substrate

bash install.sh --dry-run                          # 预览将执行的动作
bash install.sh                                    # 安装全部一等宿主：claude-code + codex + omp
bash install.sh --host claude-code                 # 只装一个宿主
bash install.sh --host generic --dest ~/my-agents  # 任意其他 agent：拷贝 skills + 接线清单

# 可选开关（可组合）：
bash install.sh --merge-mcp     # 把 MCP 模板合并进 ~/.claude.json（需 jq；先填 <ZAI_*> 占位符）
bash install.sh --with-config   # 覆盖 ~/.claude/settings.json 与 ~/.codex/config.toml（模板）
bash install.sh --with-memory   # 部署 codex 记忆到 ~/.codex/memories/
```

- 配置模板（settings.json / config.toml / mcp-servers.json.tpl）**不含任何真实凭据**，需替换的占位符清单见 `docs/secrets-checklist.md`。
- 也可以不跑脚本，直接把想要的 skill 目录拷进你的 agent 技能目录——skill 均为自包含目录（`skills/<name>/`）。
- 各宿主的安装目标、触发语法与差异说明见 `docs/hosts/`。

## 必读 skill 机制

`install.sh` 会把 `instructions/GLOBAL.md` 部署为各宿主的**全局指令文件**（Claude Code：`~/.claude/CLAUDE.md`；Codex：`~/.codex/AGENTS.md`），使两个必读 skill 的核心判据在每次会话自动加载，正文细节在各自 `skills/<name>/SKILL.md`。

- lean-mode 与 stop-that-shit 以 **advisory 模式**收录（纯 SKILL.md，零依赖、零 hook）。
- 如需 stop-that-shit 的 **hook 强制模式**（运行时硬拦截越界写入），按 `vendor/stop-that-shit/INSTALL.md` 经 plugin marketplace 安装；Hook 信任需使用者本人确认。

## 目录结构

```
substrate/
├── install.sh                 # 安装脚本（宿主注册表驱动，幂等，覆盖前备份，--dry-run 预演）
├── skills/                    # 9 个 skill 的唯一实体（宿主中立写法，Agent Skills 规范 frontmatter）
├── adapters/                  # 宿主专属配置：claude-code/（settings、MCP 模板、hook 脚本）
│                              #   codex/（hooks.json、config.toml、openai.yaml manifest）omp/
├── instructions/GLOBAL.md     # 全局必读指令单源（部署为 CLAUDE.md / AGENTS.md）
├── memory/                    # 通用记忆包（entries/ + hosts/ + codex-pack/），详见 memory/README.md
├── templates/                 # GitHub 治理模板（PR/Issue 模板、元数据 CI 脚本、DoD 清单）
├── docs/
│   ├── hosts/                 # 各宿主安装说明（claude-code / codex / generic）
│   ├── security-gates.md      # 供应链固定 / 漏洞豁免到期制 / 审计基线门禁模式
│   ├── secrets-checklist.md   # 需自行填入的凭据占位符清单
│   ├── ccb-workflow-kit/      # CCB 多 Agent 协作工作流搭建包（教程/排障/安全脱敏说明）
│   ├── OMP项目级AMD并行工作区改造复用手册.md
│   └── misc/gitconfig.template
└── vendor/                    # 第三方必读 skill 的上游完整副本（源码+测试+LICENSE，升级 diff 用）
```

## 设计原则

- **单源分发**：skills/ 是唯一实体；宿主差异（触发前缀 `/` vs `$`、安装路径、专属 manifest）收敛到安装脚本与 adapters/ 层。SKILL.md 顶部一段约定写明 `$SKILL_DIR` 与触发语法替换规则。
- **新增宿主零成本**：在 install.sh 注册表加一个函数即可；不支持技能机制的宿主把 SKILL.md 当 runbook 注入上下文也能用。
- **权限边界**：每个 skill 声明只读 / 需用户显式授权 / 三轮收敛后停；行为判据类记忆（lean-mode / stop-that-shit）全局强制加载。

## 质量与测试

- skills 核心脚本自带测试（`test_*.py` / 上游 `node --test` 套件），收录时全部验证：`workflowctl` 32 用例、issue/pr evidence 快照套件、sync_pr_metadata 套件全绿。
- stop-that-shit 上游套件 181/182 通过（唯一失败的 `opencode-smoke` 需要 OpenCode 运行时环境，与本仓库技能路径无关）。
- 运行方式：`cd skills/<name>/scripts && python3 -m unittest discover`（需 Python ≥3.11）。

## License 与致谢

本项目以 [MIT License](LICENSE) 开源（© fjy8080），覆盖自建 skills、memory、docs、templates 与脚本。

内置的第三方项目保留各自许可（原样存于对应目录）：

- `vendor/lean-mode-skill/` — MIT © Timefiles
- `vendor/stop-that-shit/` — MIT © Stop That Shit contributors
