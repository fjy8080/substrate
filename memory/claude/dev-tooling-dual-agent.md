---
name: dev-tooling-dual-agent
description: 用户同时用 codex 和 claude code 开发本项目，两边记忆必须共用同一套真相源
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-03T16:06:16.996Z
---

用户（HP26666）在本项目**同时使用 Codex 和 Claude Code** 开发。

**Why:** 若两个工具各自维护一份项目记忆，会随时间漂移、口径不一致，导致一边已更新而另一边基于过期信息操作。

**How to apply:**
- 项目工作规范和上下文只认 `AGENTS.md` 与 `memory/`，见 [[shared-memory-location]]。
- **不要**在 Claude Code 的 memory 目录里复制项目 `memory/` 的具体交付状态（PR 号、HEAD、Gate 结论、批次进度等），那些只由项目 `memory/` 维护。
- Claude Code 这侧只放：指向项目记忆的指针、Claude Code 特定视角补充、跨工具的稳定约定。
- 环境为 Linux/bash；个人 Skill（`agent-managed-delivery`、`github-pr-review`、`github-pr-fix`）是 Codex 本机配置，需显式触发，不进入项目分支。
