# CCB 多 Agent 协作工作流搭建包

制作日期：2026-08-08；参考环境：Linux / macOS / WSL、Node.js 24、CCB 8.5.7、Codex CLI、Claude Code、OpenCode。

本包把一套可见、可接管的多 Agent 开发流程整理为可复现模板：两个 Codex 把关角色、五个 Claude 工作角色，以及一个可选 OpenCode 窗口。它不包含任何账号凭据、API Key、Cookie、SSH 私钥、项目源码、历史会话、数据库或日志。

## 先看这里

新手请按以下顺序执行：

1. 阅读 [01-完整搭建教程.md](01-完整搭建教程.md)，先完成环境和各 CLI 的独立登录。
2. 将本包解压到本机任意位置，运行 `scripts/preflight.sh`，所有“必需项”通过后再继续。
3. 进入要协作的 Git 项目，运行 `scripts/bootstrap-ccb-project.sh /你的/项目路径`。
4. 打开新生成的 `.ccb/ccb.config`，按实际账号能力调整模型名，然后在项目根目录运行 `ccb`。
5. 用 [03-排障与验收.md](03-排障与验收.md) 的冒烟任务验证 main → task_scout → developer → reviewer。

日常使用查 [02-日常操作手册.md](02-日常操作手册.md)。安全边界和脱敏规则查 [04-安全脱敏说明.md](04-安全脱敏说明.md)。

## 包内目录

| 路径 | 用途 |
| --- | --- |
| `templates/ccb/` | CCB 项目拓扑、共享记忆、Git 忽略模板 |
| `templates/codex/` | Codex 安全默认值示例 |
| `templates/claude/` | Claude Code 项目规则和权限示例 |
| `templates/opencode/` | OpenCode 最小无凭据配置示例 |
| `templates/cc-switch/` | cc-switch 的安全使用说明 |
| `templates/project/` | 项目级 `AGENTS.md` 约束模板 |
| `skills/` | `ask`、上下文清理和诊断技能参考实现 |
| `scripts/` | 只读前检、无覆盖的项目初始化和脱敏审计 |

## 这套流程的职责边界

```text
负责人/主操作者
        │
      main (Codex：状态机、授权、结论)
   ┌────┼──────────────────┐
task_scout / explorer / utility  developer (Claude：唯一代码写者)
                                      │
                                reviewer (Codex：每轮全新只读审查)
                                      │
                         knowledge_keeper (Claude：开发停止后写知识)
```

关键规则：同一任务只有 `developer` 可以写代码；`reviewer` 每轮审查前清上下文；任务结束才清复用 Agent 的上下文；不把密钥或登录状态放入 Git 或共享压缩包。

## 版本与来源

- CCB：`npm install -g @seemseam/ccb@latest`，项目页：https://github.com/SeemSeam/claude_codex_bridge
- Codex：遵循官方 CLI 文档和自己的账号登录流程；项目级配置放 `.codex/config.toml`，用户级配置放 `~/.codex/config.toml`。
- Claude Code、OpenCode、cc-switch 均必须由用户用其本人账号完成登录或授权；不要复制另一台机器的隐藏目录。

版本会变化。开始部署前先执行 `ccb version`、`codex --version`、`claude --version`、`opencode --version`，并以各工具当日官方说明为准。
