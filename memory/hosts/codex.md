---
name: hosts-codex
description: Codex CLI 宿主专属实操——review 临时目录的 tmpfs 容量风险与清理、复用配置时警惕旧平台绝对路径残留
metadata:
  type: reference
---

# Codex CLI 宿主实操备忘

与 [[hosts-claude-code]] 对应。

- **临时目录容量风险**：把 PR-review 工作流的 repo checkout + venv 建在 `/tmp` 类 tmpfs 时，多个 PR/项目的目录一天能堆数 G，塞满后触发系统「配额满」类弹窗。排查手法：`df -h /tmp` 看 tmpfs 用量、按 PR/项目名模式找出陈旧 checkout/venv 目录清理；工作流设计上应把重目录放到持久盘并在任务结束即清理。
- **配置迁移/复用警惕旧平台路径残留**：从旧机器/旧平台迁移配置（config、脚本、shell rc）后行为异常时，先 grep 是否残留旧平台风格的绝对路径（`C:\Users\...`、`/c/Users/...`、旧家目录等）。
- 记忆机制：`~/.codex/memories/` 下的 `memory_summary.md` + `MEMORY.md` 是会话自动加载的记忆入口，格式见 memory/codex-pack/；与本仓库 `memory/entries/` 的关系见 [[shared-memory-location]]。
