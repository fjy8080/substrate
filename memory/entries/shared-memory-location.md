---
name: shared-memory-location
description: 项目记忆的单一真相源——AGENTS.md 与项目内 memory/ 工具无关，多个 agent 工具共用、不各自维护副本
metadata:
  type: feedback
---

# 项目记忆的单一真相源

项目的工作规范与记忆应是**工具无关的单一真相源**，所有 agent 工具（Claude Code、Codex、OpenCode……）都直接读，不各自维护副本。

**Why:** 多个工具各自维护一份项目记忆，会随时间漂移、口径不一致，导致一边已更新而另一边基于过期信息操作。

**How to apply:**

- 项目工作规范和上下文只认项目根的 `AGENTS.md` 与 `memory/`（git 跟踪与否按项目约定，文件内不绑定特定模型/厂商工具/客户端专属格式）。
- 每次开工必读顺序：`AGENTS.md` → `memory/MEMORY.md`（或索引文件）→ 按索引读相关记忆条目（项目概览、已锁定决策、协作约定、风险与未完成项等）。
- **不要**把项目 `memory/` 的具体交付状态（PR 号、HEAD、Gate 结论、批次进度等）复制进 agent 工具自己的记忆目录；那些只由项目 `memory/` 维护。
- 工具侧记忆只放：指向项目记忆的指针、该工具特有的视角补充、跨工具的稳定约定。

## 优先级（冲突时）

1. 仓库正式权威文档与当前代码。
2. GitHub PR/CI、任务系统、运行环境的实时状态。
3. `memory/` 当前摘要。
4. 历史快照与聊天记录。

任何分支/PR/Gate/Provider 状态使用前必须重新验证。关联 [[git-branch-discipline]]、[[project-memory-protocol]]。
