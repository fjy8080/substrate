---
name: hosts-claude-code
description: Claude Code 宿主专属实操——AMD 的 GIT_DIR workaround、沙箱 cwd 限制、memory-gate 软链、gh 权限allow、截图 MCP 工具、SSH 目录禁访
metadata:
  type: reference
---

# Claude Code 宿主实操备忘

跑 [[amd-workflow-rules]] 工作流及日常使用 Claude Code 时的宿主专属 workaround（与 [[hosts-codex]] 对应）。

## workflowctl 与 worktree

- 脚本在 `$SKILLS_DIR/agent-managed-delivery/scripts/workflowctl.py`；**必须在任务 worktree（feature 分支）里跑**，controller 的 `assert_task_binding` 会在 base 分支拒绝 claim/advance/memory-gate。
- **沙箱强制 cwd 留在项目根**，`cd` 到兄弟 worktree 会被重置。变通：
  - Main Agent 跑 workflowctl：用 `GIT_DIR=<项目根>/.git/worktrees/<name>` 前缀，让 git 调用在 worktree 上下文解析（branch/head 正确，state 仍写 common dir）；此模式下 `memory-gate --file memory/xxx.md` 相对根 toplevel 解析，**无需建 worktree memory 软链**。
  - 跑 pytest / git push / git worktree 操作：需要脱离沙箱（dangerouslyDisableSandbox）+ `cd <worktree>`；push 被拒时改 `git -C <worktree> push`。
  - claim 也用 GIT_DIR 前缀跑，确保记录的是 worktree 的 branch/head。
- state.json 在 `.git/agent-managed-delivery/state.json`（common dir，跨 worktree 共享）；开新批次前若已存在，先归档到 `.git/agent-managed-delivery/archive/` 再 init。

## gh 权限

auto/default 权限模式下 `gh pr create` / `gh pr merge` 偶发被 classifier 保守拦截。在 `~/.claude/settings.json` 的 `permissions.allow` 显式加 `Bash(gh pr create:*)`、`Bash(gh pr merge:*)`（显式 allow 优先于 classifier）。注意：agent 自己无法 Edit settings.json 加 allow（会被当「自提权」拦截），必须用户手动加或点允许。

## 图片与 SSH

- 用户消息附本地截图而内置读图返回 unsupported 时，改用 MCP 图像分析工具（如 `analyze_image` / `ui_to_artifact` 类），prompt 聚焦任务相关视觉细节；读到的内容与代码核查交叉互证，不臆造看不到的部分。
- 部分环境下 Bash 访问 `~/.ssh` 的任何形式（ls/cat/find）都会被权限层拒绝，不要反复尝试；需要读 SSH 配置时让用户用 `!` 前缀自己跑短命令（长命令在终端里会被折行弄坏）。

关联 [[worktree-tips]]、[[subagent-model-policy]]。
