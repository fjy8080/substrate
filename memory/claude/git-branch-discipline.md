---
name: git-branch-discipline
description: Git 关键纪律——根工作区可能长期落后、必须从最新 origin 基线建独立 worktree、remote 名以 remote -v 为准、不自行合并
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-03T16:06:21.051Z
---

Git 工作流的关键、易踩坑点（各项目以自己的 AGENTS.md 与 memory 为权威，此处只记 agent 视角下最易出错的稳定约束；具体状态请实时核对，不在此维护）。

- **remote 实际名为 `origin`**（不是旧历史记录里的 `upstream`）；开工前 `git remote -v` 复核。
- **本地根工作区可能长期落后**：根工作区常停在旧的本地基线、落后 `origin` 基线多个提交、且未快进。**下一项实际开发必须从最新 `origin/develop` 创建独立 worktree；不得在根目录快进、也不得从旧本地基线开工。** 落后数使用前必须重新核对。
- 分支命名 `feature/i{迭代号}-{描述性英文名}`；**一任务一分支一 PR**；多任务并行用独立 worktree，禁止跨分支夹带改动。
- 不直接在 `main`/`develop` 上开发或推送。
- 实现者**不自行合并 PR**：普通任务至少 1 名未参与实现者审查；鉴权/合规/迁移/文件安全/AI 真值/恢复等高风险任务需 2 名独立审查人。
- 禁止未经确认的 `reset --hard`、强推、清空卷等高风险操作。

具体当前 PR/Gate 状态请查项目 `memory/01`。关联 [[shared-memory-location]]。
