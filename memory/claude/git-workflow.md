---
name: git-workflow
description: "Git branching model, commit conventions, and branch management practices"
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-18T14:36:04.048Z
---

# Git 工作流

- **主分支** `develop`，PR 目标分支均为 develop
- Feature 分支命名: `feature/<scope>` 或 `feature/i<number>-<desc>`
- Fix 分支命名: `fix/issue-<number>-<short-desc>`
- 有过 PR 合并后删除远程分支的习惯（定期 prune）
- ~~CCB 流程用于变更控制~~ → **已弃用**，当前使用 AMD（Agent Managed Delivery）工作流
