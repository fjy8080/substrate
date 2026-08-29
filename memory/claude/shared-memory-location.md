---
name: shared-memory-location
description: 项目共享记忆位置——codex 与 claude code 共用的单一真相源在哪、读取顺序与优先级
metadata: 
  node_type: memory
  type: reference
  modified: 2026-08-03T16:06:14.112Z
---

项目的记忆与工作规范应是**工具无关的单一真相源**，Codex 和 Claude Code 都直接读，不各自维护副本。

## 权威文件（在项目工作目录根，每次开工必读）

1. **`AGENTS.md`**（项目根，git 跟踪）= Agent 工作规范权威：当前协作对象、技术基线、开工/上下文恢复流程、Git 与任务工作流、工程与契约规则、已知高风险约束、验证命令、任务报告格式、必读文档路由。
2. **`memory/MEMORY.md`** → 再按其建议顺序读 `memory/` 各编号文件（含 GitHub API 硬规则）：项目概览、当前状态、已锁定决策、协作约定、风险与未完成项、任务与交付基线等；`memory/CHANGELOG.md` 是变更历史。

`memory/` 是 git-ignored 的本地共享目录，明确写明"不使用特定模型、厂商工具或客户端专属格式"，因此天然适合两个工具共用。

## 优先级（冲突时）

1. 仓库正式权威文档与当前代码。
2. GitHub PR/CI、任务系统、运行环境的实时状态。
3. `memory/` 当前摘要。
4. 历史快照与聊天记录。

任何分支/PR/Gate/Provider 状态使用前必须重新验证。关联 [[dev-tooling-dual-agent]]、[[git-branch-discipline]]。
